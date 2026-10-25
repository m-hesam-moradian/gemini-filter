#!/usr/bin/env python3
"""
gemini-filter — hourly v2ray config checker (v2)
================================================

Pipeline (waterfall — each stage drops the failures):

  Stage 1: Gather        — fetch configs from sources.json
                            (subscriptions + telegram + raw .txt URLs)
  Stage 2: Cap           — if total > 5000, do per-source balanced random sampling
                            so each source contributes equally (no single source dominates)
  Stage 3: Latency test  — keep only configs with latency < 600ms
  Stage 4: Real Gemini   — fetch gemini.google.com, parse page HTML,
                            drop configs where Gemini shows the geo-block page
                            ("Gemini is not supported in your country")
  Stage 5: Top 50        — take top 50 candidates by (country + stability + latency) score
  Stage 6: Speed test    — download 5MB through each of the top 50, re-rank by download speed
  Stage 7: Output        — write top50.txt, shadowsocks.txt, all_ok.txt, stats.md
                            commit back to repo

Final ranking is by download speed (MB/s) — fastest config first.

Config names look like:
  1 | 🇺🇸 Ashburn VA | 7d | 23ms | 19.7 MB/s
"""

import base64
import concurrent.futures
import json
import os
import random
import re
import socket
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_FILE = os.path.join(ROOT, "sources.json")
HISTORY_FILE = os.path.join(ROOT, "history.json")
TOP_FILE = os.path.join(ROOT, "top50.txt")
SS_FILE = os.path.join(ROOT, "shadowsocks.txt")
ALL_OK_FILE = os.path.join(ROOT, "all_ok.txt")
STATS_FILE = os.path.join(ROOT, "stats.md")
XRAY_BIN = os.path.join(ROOT, "bin", "xray")
XRAY_VERSION = "v26.10.21"
XRAY_FALLBACK_VERSIONS = ["v25.10.7", "v25.1.30", "v24.12.18"]

GEMINI_URL = "https://gemini.google.com/"
LATENCY_URL = "https://www.google.com/generate_204"
SPEED_TEST_URL = "https://speed.cloudflare.com/__down?bytes=5000000"  # 5 MB

MAX_CONFIGS = 5000           # hard fallback cap; actual cap comes from sources.json
TOP_N = 50                   # final size of top50.txt
LATENCY_CUTOFF_MS = 600      # drop configs slower than this
GEMINI_TIMEOUT_S = 10        # the real Gemini page is ~800KB — needs longer than 4s on slow proxies
GEMINI_MIN_PAGE_SIZE = 100_000  # real app page is ~800KB; 403/error stubs are <2KB

# Countries where Gemini is NOT available. Even if the IP passes the page check,
# a login-time region check can still block the user, so we drop these outright.
GEMINI_BLOCKED_COUNTRIES = {
    "IR", "RU", "BY", "CN", "HK", "MO", "CU", "KP", "SY", "VE", "AF", "MM",
}

# Phrases Gemini shows when geo-blocked (case-insensitive substring match)
GEMINI_BLOCK_PHRASES = [
    "is not supported in your country",
    "not available in your country",
    "isn't available in your country",
    "is not available in your region",
    "isn't supported in your country",
    "not supported in your region",
    "isn't supported in your country/region",
    "not supported in your country/region",
]

COUNTRY_SCORES = {
    "US": 30, "CA": 18, "MX": 18,
    "DE": 12, "NL": 12, "FI": 12, "FR": 12, "GB": 12,
    "SE": 12, "CH": 12, "AT": 12, "IE": 12, "BE": 12, "DK": 12, "NO": 12,
    "TR": 10, "AE": 8, "JP": 8, "KR": 8, "SG": 8, "HK": 6,
}
DEFAULT_COUNTRY_SCORE = 5


# ---------------------------------------------------------------------------
# Country code -> flag emoji (regional indicator pairs)
# ---------------------------------------------------------------------------

def country_flag(cc: str) -> str:
    """Convert ISO-2 country code to flag emoji."""
    if not cc or len(cc) != 2 or not cc.isalpha():
        return "🏳️"
    cc = cc.upper()
    try:
        return chr(0x1F1E6 + ord(cc[0]) - ord("A")) + chr(0x1F1E6 + ord(cc[1]) - ord("A"))
    except Exception:
        return "🏳️"


# ---------------------------------------------------------------------------
# Config parsing — vmess://, vless://, trojan://, ss://
# ---------------------------------------------------------------------------

def parse_vmess(uri: str) -> dict:
    try:
        b64 = uri[len("vmess://"):]
        b64 += "=" * (-len(b64) % 4)
        data = json.loads(base64.b64decode(b64).decode("utf-8", errors="ignore"))
        return {
            "protocol": "vmess",
            "address": data.get("add", ""),
            "port": int(data.get("port", 0)),
            "id": data.get("id", ""),
            "alterId": int(data.get("aid", 0)),
            "network": data.get("net", "tcp"),
            "tls": data.get("tls", ""),
            "sni": data.get("sni", "") or data.get("host", ""),
            "path": data.get("path", "/"),
            "host": data.get("host", ""),
            "remark": data.get("ps", ""),
        }
    except Exception:
        return None


def parse_url_scheme(uri: str, scheme: str) -> dict:
    try:
        if not uri.startswith(scheme + "://"):
            return None
        body = uri[len(scheme) + 3:]
        if "#" in body:
            body, frag = body.split("#", 1)
            remark = urllib.parse.unquote(frag)
        else:
            remark = ""
        if "?" in body:
            main, query = body.split("?", 1)
        else:
            main, query = body, ""
        if "@" not in main:
            return None
        userinfo, hostport = main.rsplit("@", 1)
        if ":" not in hostport:
            return None
        host, port = hostport.rsplit(":", 1)
        port = int(port)
        params = dict(urllib.parse.parse_qsl(query))

        if scheme == "ss":
            try:
                dec = base64.urlsafe_b64decode(userinfo + "=" * (-len(userinfo) % 4)).decode("utf-8")
                method, password = dec.split(":", 1)
            except Exception:
                method, password = (userinfo.split(":", 1) + [None])[:2] if ":" in userinfo else ("none", userinfo)
            return {
                "protocol": "shadowsocks",
                "address": host, "port": port,
                "method": method, "password": password or "",
                "network": "tcp", "tls": "", "sni": "", "path": "/", "host": "",
                "remark": remark,
            }
        if scheme == "vless":
            return {
                "protocol": "vless",
                "address": host, "port": port,
                "id": userinfo,
                "network": params.get("type", "tcp"),
                "tls": params.get("security", "none"),
                "sni": params.get("sni", "") or params.get("host", ""),
                "path": params.get("path", "/"),
                "host": params.get("host", ""),
                "flow": params.get("flow", ""),
                "remark": remark,
            }
        if scheme == "trojan":
            return {
                "protocol": "trojan",
                "address": host, "port": port,
                "password": userinfo,
                "network": params.get("type", "tcp"),
                "tls": params.get("security", "tls"),
                "sni": params.get("sni", "") or params.get("peer", "") or host,
                "path": params.get("path", "/"),
                "host": params.get("host", "") or params.get("sni", ""),
                "remark": remark,
            }
    except Exception:
        return None
    return None


def parse_config(uri: str) -> dict:
    uri = uri.strip()
    if not uri or uri.startswith("#"):
        return None
    if uri.startswith("vmess://"):
        return parse_vmess(uri)
    if uri.startswith("vless://"):
        return parse_url_scheme(uri, "vless")
    if uri.startswith("trojan://"):
        return parse_url_scheme(uri, "trojan")
    if uri.startswith("ss://"):
        return parse_url_scheme(uri, "ss")
    return None


def config_signature(c: dict) -> str:
    return f"{c['protocol']}|{c['address']}|{c['port']}|{c.get('id', c.get('password', ''))}"


def config_to_uri(c: dict) -> str:
    if c["protocol"] == "vmess":
        payload = {
            "v": "2", "ps": c.get("remark", ""),
            "add": c["address"], "port": str(c["port"]),
            "id": c["id"], "aid": str(c.get("alterId", 0)),
            "net": c.get("network", "tcp"), "type": "none",
            "tls": c.get("tls", "") or "", "sni": c.get("sni", ""),
            "host": c.get("host", ""), "path": c.get("path", "/"),
        }
        b = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
        return f"vmess://{b}"
    if c["protocol"] == "vless":
        q = urllib.parse.urlencode({
            "type": c.get("network", "tcp"),
            "security": c.get("tls", "none"),
            "sni": c.get("sni", ""), "host": c.get("host", ""),
            "path": c.get("path", "/"), "flow": c.get("flow", ""),
        })
        return f"vless://{c['id']}@{c['address']}:{c['port']}?{q}#{urllib.parse.quote(c.get('remark', ''))}"
    if c["protocol"] == "trojan":
        q = urllib.parse.urlencode({
            "type": c.get("network", "tcp"),
            "security": c.get("tls", "tls"),
            "sni": c.get("sni", ""), "host": c.get("host", ""),
            "path": c.get("path", "/"),
        })
        return f"trojan://{urllib.parse.quote(c['password'])}@{c['address']}:{c['port']}?{q}#{urllib.parse.quote(c.get('remark', ''))}"
    if c["protocol"] == "shadowsocks":
        cred = base64.urlsafe_b64encode(f"{c['method']}:{c['password']}".encode()).decode().rstrip("=")
        return f"ss://{cred}@{c['address']}:{c['port']}#{urllib.parse.quote(c.get('remark', ''))}"
    return ""


# ---------------------------------------------------------------------------
# Xray binary setup
# ---------------------------------------------------------------------------

def ensure_xray():
    if os.path.isfile(XRAY_BIN) and os.access(XRAY_BIN, os.X_OK):
        return XRAY_BIN
    bin_dir = os.path.dirname(XRAY_BIN)
    os.makedirs(bin_dir, exist_ok=True)
    arch = "64" if os.uname().machine in ("x86_64", "amd64") else "arm64-v8a"
    for ver in [XRAY_VERSION] + XRAY_FALLBACK_VERSIONS:
        url = f"https://github.com/XTLS/Xray-core/releases/download/{ver}/Xray-linux-{arch}.zip"
        print(f"setup: trying xray {ver}")
        zip_path = XRAY_BIN + ".zip"
        rc = subprocess.run(["wget", "-qL", "-O", zip_path, url]).returncode
        if rc != 0 or not os.path.exists(zip_path) or os.path.getsize(zip_path) < 1000:
            continue
        try:
            subprocess.run(["unzip", "-o", zip_path, "-d", bin_dir], check=True, capture_output=True)
            os.chmod(XRAY_BIN, 0o755)
            os.remove(zip_path)
            print(f"setup: xray {ver} ready")
            return XRAY_BIN
        except Exception as e:
            print(f"setup: unzip failed for {ver}: {e}")
            continue
    raise RuntimeError("could not download xray-core")


def build_xray_config(c: dict, socks_port: int) -> dict:
    inbound = {
        "port": socks_port, "listen": "127.0.0.1",
        "protocol": "socks", "settings": {"auth": "noauth", "udp": False},
    }
    stream = {"network": c.get("network", "tcp")}
    net = stream["network"]
    if net == "ws":
        stream["wsSettings"] = {"path": c.get("path", "/"),
                                "headers": {"Host": c.get("host", "") or c.get("sni", "")}}
    elif net == "grpc":
        stream["grpcSettings"] = {"serviceName": c.get("path", "") or c.get("host", "")}
    elif net == "h2":
        stream["httpSettings"] = {"path": c.get("path", "/"),
                                  "host": [c.get("host", "")] if c.get("host") else []}

    sec = c.get("tls", "")
    if sec in ("tls", "reality") or (c["protocol"] in ("trojan", "vless") and sec != "none"):
        stream["security"] = "tls"
        stream["tlsSettings"] = {"serverName": c.get("sni", "") or c["address"], "allowInsecure": True}
    else:
        stream["security"] = "none"

    if c["protocol"] == "vmess":
        outbound = {"protocol": "vmess",
                    "settings": {"vnext": [{"address": c["address"], "port": c["port"],
                                            "users": [{"id": c["id"], "alterId": c.get("alterId", 0),
                                                       "security": "auto"}]}]},
                    "streamSettings": stream}
    elif c["protocol"] == "vless":
        users = {"id": c["id"], "encryption": "none"}
        if c.get("flow"):
            users["flow"] = c["flow"]
        outbound = {"protocol": "vless",
                    "settings": {"vnext": [{"address": c["address"], "port": c["port"],
                                            "users": [users]}]},
                    "streamSettings": stream}
    elif c["protocol"] == "trojan":
        outbound = {"protocol": "trojan",
                    "settings": {"servers": [{"address": c["address"], "port": c["port"],
                                              "password": c["password"]}]},
                    "streamSettings": stream}
    elif c["protocol"] == "shadowsocks":
        outbound = {"protocol": "shadowsocks",
                    "settings": {"servers": [{"address": c["address"], "port": c["port"],
                                              "method": c["method"], "password": c["password"]}]},
                    "streamSettings": stream}
    else:
        return None
    return {"log": {"loglevel": "warning"}, "inbounds": [inbound], "outbounds": [outbound]}


# ---------------------------------------------------------------------------
# Source fetching (with per-source tracking for stats)
# ---------------------------------------------------------------------------

def fetch_subscription(url: str, timeout: int = 30) -> list:
    req = urllib.request.Request(url, headers={"User-Agent": "v2rayNG/1.8.5"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", errors="ignore").strip()
    try:
        dec = base64.b64decode(body + "=" * (-len(body) % 4)).decode("utf-8", errors="ignore")
        if any(s + "://" in dec for s in ("vmess", "vless", "trojan", "ss")):
            body = dec
    except Exception:
        pass
    return [l.strip() for l in body.splitlines()
            if l.strip() and any(l.strip().startswith(s + "://") for s in ("vmess", "vless", "trojan", "ss"))]


def fetch_telegram(username: str, timeout: int = 30) -> list:
    url = f"https://t.me/s/{username.lstrip('@')}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            html = r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"warn: telegram {username}: {e}")
        return []
    return list(set(re.findall(r'(?:vmess|vless|trojan|ss)://[^\s"\'<>]+', html)))


def gather_configs(sources: dict) -> list:
    """
    Returns list of dicts: {config, source_name, source_type}
    Dedup happens GLOBALLY but the first source to provide a config wins attribution.
    """
    seen = set()
    out = []
    per_source_raw = {}

    def add(c, source_name, source_type):
        sig = config_signature(c)
        per_source_raw[source_name] = per_source_raw.get(source_name, 0) + 1
        if sig in seen:
            return
        seen.add(sig)
        out.append({"config": c, "source_name": source_name, "source_type": source_type})

    # Fetch all sources in parallel — one slow Telegram channel can't stall the others.
    def fetch_one(source):
        """Returns (source_name, source_type, list_of_raw_lines)."""
        if "url" in source:  # subscription
            try:
                return source["name"], "subscription", fetch_subscription(source["url"])
            except Exception as e:
                print(f"warn: sub {source['name']}: {e}")
                return source["name"], "subscription", []
        else:  # telegram
            try:
                return source["username"], "telegram", fetch_telegram(source["username"])
            except Exception as e:
                print(f"warn: tg {source['username']}: {e}")
                return source["username"], "telegram", []

    active_sources = [s for s in sources.get("subscriptions", []) if s.get("enabled", True)] + \
                     [t for t in sources.get("telegram_channels", []) if t.get("enabled", True)]
    print(f"fetch: {len(active_sources)} sources in parallel")
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(16, len(active_sources) or 1)) as ex:
        futs = [ex.submit(fetch_one, s) for s in active_sources]
        for fut in concurrent.futures.as_completed(futs):
            src_name, src_type, lines = fut.result()
            print(f"fetch: {src_name} -> {len(lines)} raw lines")
            for line in lines:
                c = parse_config(line)
                if c:
                    add(c, src_name, src_type)

    return out, per_source_raw


def balanced_random_pull(items: list, max_n: int) -> list:
    """
    Each source contributes an EQUAL share of the cap.
    If source A has 100k configs and source B has 5k, both get max_n/n_sources slots.
    Sources smaller than their slot get fully included; the leftover is split among the bigger ones.
    """
    if len(items) <= max_n:
        return items
    by_source = {}
    for item in items:
        by_source.setdefault(item["source_name"], []).append(item)
    n_sources = len(by_source)
    base_quota = max_n // n_sources
    leftovers = max_n - base_quota * n_sources

    result = []
    leftover_pool = []
    for src, lst in by_source.items():
        random.shuffle(lst)
        if len(lst) <= base_quota:
            result.extend(lst)
            # Do NOT add lst to leftover_pool here — it's already in result.
            # Adding it again would cause duplicate testing of small-source configs.
        else:
            take = lst[:base_quota]
            result.extend(take)
            leftover_pool.extend(lst[base_quota:])  # only the EXTRAS go to redistribution

    # fill remaining slots from leftover_pool
    needed = max_n - len(result)
    if needed > 0 and leftover_pool:
        random.shuffle(leftover_pool)
        result.extend(leftover_pool[:needed])

    # final trim (in case rounding went over)
    random.shuffle(result)
    return result[:max_n]


# ---------------------------------------------------------------------------
# Test one config — multi-stage
# ---------------------------------------------------------------------------

def free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def spawn_xray(xray_bin: str, c: dict) -> tuple:
    """Returns (proc, port, cfg_path) or (None, None, None) on failure."""
    port = free_port()
    cfg = build_xray_config(c, port)
    if not cfg:
        return None, None, None
    cfg_path = f"/tmp/xray_{port}.json"
    with open(cfg_path, "w") as f:
        json.dump(cfg, f)
    proc = subprocess.Popen([xray_bin, "run", "-c", cfg_path],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Wait for xray to start listening — poll the port instead of fixed sleep.
    # Cap at 1.5s; if it doesn't open by then, give up (the config is broken).
    deadline = time.time() + 1.5
    while time.time() < deadline:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        try:
            s.connect(("127.0.0.1", port))
            s.close()
            return proc, port, cfg_path
        except Exception:
            pass
        if proc.poll() is not None:
            try: os.remove(cfg_path)
            except OSError: pass
            return None, None, None
        time.sleep(0.03)  # local xray starts in 15-30ms; polling faster doesn't waste time
    # timeout — port didn't open in 1.5s
    cleanup_xray(proc, cfg_path)
    return None, None, None


def cleanup_xray(proc, cfg_path):
    if proc and proc.poll() is None:
        proc.terminate()
        try: proc.wait(timeout=2)
        except Exception: proc.kill()
    if cfg_path and os.path.exists(cfg_path):
        try: os.remove(cfg_path)
        except OSError: pass


def curl_through_socks(port: int, url: str, timeout: int, extra_args: list = None) -> tuple:
    """Run curl through the SOCKS proxy, return (returncode, stdout, stderr).
    --connect-timeout is shorter than --max-time so dead proxies fail fast at the
    TCP layer instead of waiting the full timeout."""
    conn_timeout = min(3, max(1, timeout // 2))
    cmd = ["curl", "-sS", "-x", f"socks5h://127.0.0.1:{port}",
           "--connect-timeout", str(conn_timeout),
           "--max-time", str(timeout), "-L"]
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 3)
    return r.returncode, r.stdout, r.stderr


def test_latency(port: int, timeout: int) -> dict:
    """Stage 3: latency only. Returns {alive, latency_ms} or {alive: False}."""
    rc, out, _ = curl_through_socks(port, LATENCY_URL, timeout,
                                    extra_args=["-o", "/dev/null", "-w", "%{http_code} %{time_total}"])
    if rc != 0 or not out.strip():
        return {"alive": False}
    parts = out.strip().split()
    if not parts or not parts[0].isdigit() or int(parts[0]) not in (200, 204):
        return {"alive": False}
    return {"alive": True, "latency_ms": int(float(parts[1]) * 1000)}


_EXIT_IP_CACHE = {}  # exit_ip -> {country_code, city, region} — many configs share exits


def _geo_lookup_direct(ip: str) -> dict:
    """
    Look up geo info for an exit IP, querying DIRECTLY from the runner (not
    through the proxy). Going through the proxy exit burned ipinfo.io quotas
    (the shared datacenter exits are abused by thousands of other proxy users),
    which is why so many configs showed '??' country. Querying directly with a
    per-IP cache + provider fallback chain is reliable.
    """
    if ip in _EXIT_IP_CACHE:
        return _EXIT_IP_CACHE[ip]
    info = {"country_code": None, "city": "", "region": ""}
    # 1) ipwho.is — free, generous limits, returns country_code/city/region
    try:
        r = subprocess.run(["curl", "-sS", "--max-time", "5", f"https://ipwho.is/{ip}"],
                           capture_output=True, text=True, timeout=8)
        d = json.loads(r.stdout)
        if d.get("country_code"):
            info = {"country_code": d["country_code"].upper(),
                    "city": d.get("city") or "", "region": d.get("region") or ""}
    except Exception:
        pass
    # 2) ip-api.com fallback
    if not info["country_code"]:
        try:
            r = subprocess.run(
                ["curl", "-sS", "--max-time", "5",
                 f"http://ip-api.com/json/{ip}?fields=countryCode,city,regionName"],
                capture_output=True, text=True, timeout=8)
            d = json.loads(r.stdout)
            if d.get("countryCode"):
                info = {"country_code": d["countryCode"].upper(),
                        "city": d.get("city") or "", "region": d.get("regionName") or ""}
        except Exception:
            pass
    _EXIT_IP_CACHE[ip] = info
    return info


def test_country_info(port: int, timeout: int) -> dict:
    """
    Stage 4b: get the exit IP (through the proxy, via ipify — a tiny plain-text
    response with very high rate limits), then geo-lookup DIRECTLY from the runner.
    Only called for configs that already passed the Gemini check.
    """
    info = {}
    rc, out, _ = curl_through_socks(port, "https://api.ipify.org", timeout)
    exit_ip = out.strip() if rc == 0 and out.strip() else ""
    if exit_ip:
        info = _geo_lookup_direct(exit_ip)
        info["exit_ip"] = exit_ip
    return info


def test_gemini_real(port: int, timeout: int = GEMINI_TIMEOUT_S) -> bool:
    """
    Stage 4: verify the REAL Gemini app page loads — three-part check:

      1. HTTP status must be 200.
         (Google serves 403 Forbidden to flagged datacenter exit IPs — the page
         still contains "google" and "<html", so a content-only check passes it.
         This was the bug that let 403-blocked configs into top50.)
      2. Page body must be >= GEMINI_MIN_PAGE_SIZE bytes.
         (The real app page is ~800KB; 403/error stubs are <2KB.)
      3. Body must not contain geo-block phrases.
         ("isn't supported in your country/region" etc.)
    """
    rc, out, _ = curl_through_socks(
        port, GEMINI_URL, timeout,
        extra_args=["-w", "\n__META__%{http_code} %{size_download}"])
    if rc != 0 or not out:
        return False
    marker = "\n__META__"
    idx = out.rfind(marker)
    if idx < 0:
        return False
    body = out[:idx]
    meta = out[idx + len(marker):].strip().split()
    if len(meta) != 2:
        return False
    try:
        status = int(meta[0])
        size = int(float(meta[1]))
    except Exception:
        return False
    if status != 200:
        return False
    if size < GEMINI_MIN_PAGE_SIZE:
        return False
    body_lower = body.lower()
    for phrase in GEMINI_BLOCK_PHRASES:
        if phrase in body_lower:
            return False
    return True


def test_download_speed(port: int, timeout: int = 15) -> float:
    """
    Stage 6: download 5MB, return MB/s.
    Uses curl -w to get avg_speed in bytes/sec, converts to MB/s.
    """
    rc, out, _ = curl_through_socks(
        port, SPEED_TEST_URL, timeout,
        extra_args=["-o", "/dev/null", "-w", "%{speed_download}"])
    if rc != 0 or not out.strip():
        return 0.0
    try:
        bps = float(out.strip())
        return round(bps / 1_000_000, 2)  # bytes/sec -> MB/s
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Scoring (used to pick top 50 candidates BEFORE the speed test)
# ---------------------------------------------------------------------------

def score_country(cc: str) -> int:
    return COUNTRY_SCORES.get(cc, DEFAULT_COUNTRY_SCORE) if cc else 0


def score_stability(days: int) -> int:
    if days <= 0:
        return 0
    return min(days * days, 100)


def score_latency(ms: int) -> int:
    if ms is None:
        return 0
    if ms < 150: return 25
    if ms < 300: return 18
    if ms < 600: return 10
    return -1  # dropped


# ---------------------------------------------------------------------------
# History (30-day retention)
# ---------------------------------------------------------------------------

def today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_history() -> dict:
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except Exception:
        return {"configs": {}, "last_updated": None, "stats": {}, "sources_30d": {}}


def save_history(h: dict):
    h["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(HISTORY_FILE, "w") as f:
        json.dump(h, f, indent=2)


def update_history(h: dict, sig: str, today_ok: bool, retention_days: int,
                   uri: str = None, source_name: str = None) -> dict:
    cfgs = h.setdefault("configs", {})
    e = cfgs.get(sig, {"first_seen": today_utc(), "history": []})
    today = today_utc()
    if e["history"] and e["history"][-1].get("date") == today:
        e["history"][-1] = {"date": today, "ok": today_ok}
    else:
        e["history"].append({"date": today, "ok": today_ok})
    cutoff = datetime.now(timezone.utc).timestamp() - retention_days * 86400
    e["history"] = [x for x in e["history"]
                    if datetime.fromisoformat(x["date"]).timestamp() >= cutoff][-retention_days:]
    # Store the URI + source so we can re-test survivors next run even if they
    # disappear from the fresh fetch (otherwise their streak would silently reset).
    if uri:
        e["uri"] = uri
    if source_name:
        e["source_name"] = source_name
    streak = 0
    for entry in reversed(e["history"]):
        if entry["ok"]:
            streak += 1
        else:
            break
    cfgs[sig] = e
    return {"first_seen": e["first_seen"], "streak_days": streak}


def previously_alive_configs(h: dict, days_back: int = 3) -> list:
    """
    Returns a list of {config, source_name, source_type} dicts for configs that
    were marked OK in the last `days_back` days of history. We need these to be
    re-tested every run so their streak doesn't silently reset when the random
    pull happens to skip them.
    """
    out = []
    cutoff = datetime.now(timezone.utc).timestamp() - days_back * 86400
    for sig, e in h.get("configs", {}).items():
        if not e.get("uri"):
            continue
        # was OK in the last days_back days?
        recent_ok = any(x.get("ok") for x in e.get("history", [])
                        if datetime.fromisoformat(x["date"]).timestamp() >= cutoff)
        if not recent_ok:
            continue
        c = parse_config(e["uri"])
        if not c:
            continue
        out.append({
            "config": c,
            "source_name": e.get("source_name", "history"),
            "source_type": "history-survivor",
            "from_history": True,
        })
    return out


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print(f"gemini-filter v2 — {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    with open(SOURCES_FILE) as f:
        sources = json.load(f)
    settings = sources.get("test_settings", {})
    retention_days = int(settings.get("history_retention_days", 30))  # was 100, now 30
    workers = int(settings.get("concurrent_workers", 48))
    test_timeout = int(settings.get("test_timeout_seconds", 4))
    # Effective cap comes from sources.json (was previously ignored — bug)
    effective_cap = int(settings.get("max_configs_per_run", MAX_CONFIGS))

    history = load_history()

    # ---- Stage 1: gather fresh configs from all sources ----
    all_items, per_source_raw = gather_configs(sources)
    total_gathered = len(all_items)
    print(f"main: stage 1 — gathered {total_gathered} unique fresh configs from {len(per_source_raw)} sources")

    # ---- Stage 1b: inject previously-alive configs from history ----
    # These must be re-tested every run, otherwise their "days active" streak would
    # silently reset just because the random pull skipped them.
    survivors = previously_alive_configs(history, days_back=3)
    # Dedupe survivors against the fresh pool (if a config is in both, we don't need
    # to test it twice — its fresh fetch will be tested).
    fresh_sigs = {config_signature(it["config"]) for it in all_items}
    survivors_only = [s for s in survivors if config_signature(s["config"]) not in fresh_sigs]
    if survivors_only:
        print(f"main: stage 1b — injecting {len(survivors_only)} previously-alive configs from history "
              f"(survivors not in fresh fetch — must re-test to keep streak growing)")
        all_items = survivors_only + all_items
        per_source_raw["__history_survivors__"] = len(survivors_only)
    else:
        print(f"main: stage 1b — found {len(survivors)} survivors in history, all already in fresh fetch")

    # ---- Stage 2: balanced random pull if > effective_cap ----
    # Survivors are PRESERVED first (they take priority slots), then the remaining
    # slots are split equally across the fresh sources.
    if len(all_items) > effective_cap:
        print(f"main: stage 2 — capping to {effective_cap} (preserving {len(survivors_only)} survivors + balanced random for the rest)")
        survivors_budget = min(len(survivors_only), effective_cap // 4)  # cap survivors at 25% of total
        kept_survivors = survivors_only[:survivors_budget] if survivors_only else []
        remaining_budget = effective_cap - len(kept_survivors)
        # Remove survivors from the fresh pool before doing the balanced random pull,
        # so the pull only operates on fresh configs.
        fresh_items = [it for it in all_items if not it.get("from_history")]
        kept_fresh = balanced_random_pull(fresh_items, remaining_budget) if fresh_items else []
        items = kept_survivors + kept_fresh
        per_source_kept = {}
        for it in items:
            per_source_kept[it["source_name"]] = per_source_kept.get(it["source_name"], 0) + 1
        for src, n in sorted(per_source_kept.items(), key=lambda x: -x[1]):
            raw = per_source_raw.get(src, 0)
            print(f"         {src:30} raw={raw:6}  kept={n}")
    else:
        items = all_items
        print(f"main: stage 2 — no cap needed ({len(all_items)} <= {effective_cap})")

    xray_bin = ensure_xray()

    # ---- Stage 2.5: Fast TCP pre-filter ----
    # Most public proxy configs point at servers that aren't even listening on the
    # port. A raw TCP socket.connect() takes 0.5–1.5s on a dead host, vs 0.05s on
    # a live one. Spawning xray+curl on a dead host wastes 8s of worker time.
    # We can run 200 TCP probes in parallel and drop ~80% of bad configs in <15s.
    def tcp_ping(c: dict, timeout: float = 1.5) -> bool:
        try:
            with socket.create_connection((c["address"], int(c["port"])), timeout=timeout):
                return True
        except Exception:
            return False

    print(f"main: stage 2.5 — TCP pre-filter on {len(items)} configs (1.5s timeout, 200 workers)")
    pre_filter_alive = []
    pre_filter_dead = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=200) as ex:
        futs = {ex.submit(tcp_ping, it["config"]): it for it in items}
        for fut in concurrent.futures.as_completed(futs):
            if fut.result():
                pre_filter_alive.append(futs[fut])
            else:
                pre_filter_dead += 1
    items = pre_filter_alive
    print(f"main: stage 2.5 — {len(items)} alive, {pre_filter_dead} dropped (TCP closed)")

    # ---- Stage 3+4: latency test → drop >600ms → real Gemini test ----
    passed_stage34 = []
    stats_stage = {"latency_fail": 0, "gemini_fail": 0, "xray_fail": 0}

    def worker_stage34(item):
        c = item["config"]
        proc, port, cfg_path = spawn_xray(xray_bin, c)
        if not proc:
            return None, "xray_died", None
        try:
            # Stage 3: latency (cheap — drops most bad configs here)
            lat_info = test_latency(port, test_timeout)
            if not lat_info.get("alive"):
                return None, "latency_fail", None
            if lat_info["latency_ms"] > LATENCY_CUTOFF_MS:
                return None, "latency_high", lat_info
            # Stage 4: real Gemini check — status 200 + full-size page + no geo-block.
            # Dedicated 10s timeout: the page is ~800KB and 4s truncates it on slow proxies.
            if not test_gemini_real(port, GEMINI_TIMEOUT_S):
                return None, "gemini_fail", lat_info
            # Country lookup only for Gemini-passing configs (exit IP + direct lookup)
            country_info = test_country_info(port, test_timeout)
            lat_info.update(country_info)
            # Drop countries where Gemini is not available at all
            if lat_info.get("country_code") in GEMINI_BLOCKED_COUNTRIES:
                return None, "country_blocked", lat_info
            return lat_info, "ok", None
        except Exception:
            return None, "exception", None
        finally:
            cleanup_xray(proc, cfg_path)

    print(f"main: stage 3+4 — testing {len(items)} configs (latency < {LATENCY_CUTOFF_MS}ms + Gemini real)")
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(worker_stage34, it): it for it in items}
        for i, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            it = futs[fut]
            try:
                lat_info, status, _ = fut.result()
            except Exception:
                status, lat_info = "exception", None
            sig = config_signature(it["config"])
            ok_today = status == "ok"
            uri = config_to_uri(it["config"])
            hinfo = update_history(history, sig, ok_today, retention_days,
                                  uri=uri, source_name=it.get("source_name"))
            if ok_today and lat_info:
                lat_score = score_latency(lat_info["latency_ms"])
                candidate_score = (score_country(lat_info.get("country_code"))
                                   + score_stability(hinfo["streak_days"])
                                   + max(lat_score, 0))
                passed_stage34.append({
                    "config": it["config"],
                    "source_name": it["source_name"],
                    "source_type": it["source_type"],
                    "country_code": lat_info.get("country_code"),
                    "city": lat_info.get("city", ""),
                    "region": lat_info.get("region", ""),
                    "latency_ms": lat_info["latency_ms"],
                    "streak_days": hinfo["streak_days"],
                    "first_seen": hinfo["first_seen"],
                    "candidate_score": candidate_score,
                })
            else:
                stats_stage[status] = stats_stage.get(status, 0) + 1
            if i % 50 == 0:
                print(f"         tested {i}/{len(items)}  passed={len(passed_stage34)}")

    print(f"main: stage 3+4 — {len(passed_stage34)} configs passed latency + real-Gemini check")
    print(f"         drop reasons: {stats_stage}")

    # ---- Stage 5: pick top 50 candidates by composite score ----
    passed_stage34.sort(key=lambda r: (-r["candidate_score"], r["latency_ms"]))
    top_candidates = passed_stage34[:TOP_N]
    print(f"main: stage 5 — selected top {len(top_candidates)} candidates for speed test")

    # ---- Stage 6: download speed test, re-rank by MB/s ----
    def worker_speed(item):
        c = item["config"]
        proc, port, cfg_path = spawn_xray(xray_bin, c)
        if not proc:
            return 0.0
        try:
            return test_download_speed(port)
        except Exception:
            return 0.0
        finally:
            cleanup_xray(proc, cfg_path)

    print(f"main: stage 6 — speed-testing top {len(top_candidates)} candidates (5MB download each)")
    speed_workers = min(workers, 8)
    with concurrent.futures.ThreadPoolExecutor(max_workers=speed_workers) as ex:
        futs = {ex.submit(worker_speed, it): it for it in top_candidates}
        for i, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            futs[fut]["speed_mbps"] = fut.result()
            if i % 10 == 0:
                print(f"         speed-tested {i}/{len(top_candidates)}")

    # Re-rank by download speed (fastest first)
    top_candidates.sort(key=lambda r: -r["speed_mbps"])

    # ---- Stage 7: write output files ----
    write_outputs(top_candidates, passed_stage34, all_items,
                  per_source_raw, history, stats_stage,
                  total_gathered, len(items), retention_days, sources, effective_cap)

    # ---- Finalize history ----
    history["stats"] = {
        "total_runs": history.get("stats", {}).get("total_runs", 0) + 1,
        "last_run_at": datetime.now(timezone.utc).isoformat(),
        "last_run_configs_gathered": total_gathered,
        "last_run_configs_tested": len(items),
        "last_run_passed_latency": len(passed_stage34) + stats_stage.get("gemini_fail", 0),
        "last_run_passed_gemini": len(passed_stage34),
        "last_run_top_n": len(top_candidates),
        "drop_reasons": stats_stage,
        "per_source_raw": per_source_raw,
    }
    save_history(history)
    print("main: done")


def make_name(rank: int, r: dict) -> str:
    cc = r.get("country_code") or "??"
    flag = country_flag(cc)
    city = r.get("city") or ""
    region = r.get("region") or ""
    # Combine city + region but trim if too long
    loc_parts = [p for p in [city, region] if p]
    loc = " ".join(loc_parts)[:25] if loc_parts else cc
    # Source name (cleaned — strip "example-" prefix, cap length)
    src = (r.get("source_name") or "").replace("example-", "").replace("__history_survivors__", "history")[:18]
    return f"{rank} | {flag} {loc} | {r['streak_days']}d | {r['latency_ms']}ms | {r['speed_mbps']} MB/s | {src}"


def write_outputs(top_n, all_passed, all_items, per_source_raw,
                  history, stats_stage, total_gathered, total_tested,
                  retention_days, sources, effective_cap):
    # ---- top50.txt ----
    lines = []
    for i, r in enumerate(top_n, 1):
        name = make_name(i, r)
        r["config"]["remark"] = name
        lines.append(config_to_uri(r["config"]))
    with open(TOP_FILE, "w") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))

    # ---- shadowsocks.txt (all SS configs that passed stage 3+4) ----
    # Sort SS by speed descending so the fastest SS is at the top of the file too.
    # SS configs that weren't in the top-N speed-test batch will have speed_mbps=0;
    # fall back to candidate_score for ordering.
    ss_passed = sorted(
        [r for r in all_passed if r["config"]["protocol"] == "shadowsocks"],
        key=lambda r: (-r.get("speed_mbps", 0), -r.get("candidate_score", 0))
    ) if all_passed else []
    ss_lines = []
    for i, r in enumerate(ss_passed, 1):
        name = make_name(i, r)
        r["config"]["remark"] = name
        ss_lines.append(config_to_uri(r["config"]))
    with open(SS_FILE, "w") as f:
        f.write("\n".join(ss_lines) + ("\n" if ss_lines else ""))

    # ---- all_ok.txt (all passed, up to 200) ----
    with open(ALL_OK_FILE, "w") as f:
        f.write("\n".join(config_to_uri(r["config"]) for r in all_passed[:200])
                + ("\n" if all_passed else ""))

    # ---- stats.md ----
    s = history.get("stats", {})
    md = ["# gemini-filter stats", ""]
    md.append(f"- **Last run:** {datetime.now(timezone.utc).isoformat()}")
    md.append(f"- **Total runs:** {s.get('total_runs', 0) + 1}")
    md.append(f"- **Configs gathered (raw, all sources):** {total_gathered}")
    md.append(f"- **Configs tested (after balanced cap to {effective_cap}):** {total_tested}")
    md.append(f"- **Passed latency (< {LATENCY_CUTOFF_MS}ms) + real Gemini check:** {len(all_passed)}")
    md.append(f"- **Drop reasons:** {stats_stage}")
    md.append(f"- **History retention:** {retention_days} days")
    md.append("")

    # Per-source breakdown
    md.append("## Source breakdown (this run)")
    md.append("")
    md.append("| Source | Type | Raw configs | Unique after dedup |")
    md.append("|--------|------|-------------|---------------------|")
    per_source_unique = {}
    for it in all_items:
        per_source_unique[it["source_name"]] = per_source_unique.get(it["source_name"], 0) + 1
    for src in sorted(per_source_raw.keys()):
        raw = per_source_raw.get(src, 0)
        uniq = per_source_unique.get(src, 0)
        # determine type
        stype = "subscription" if any(s["name"] == src for s in sources.get("subscriptions", [])) else "telegram"
        md.append(f"| {src} | {stype} | {raw} | {uniq} |")
    md.append("")

    # Protocol breakdown
    proto_counts = {}
    for r in all_passed:
        proto_counts[r["config"]["protocol"]] = proto_counts.get(r["config"]["protocol"], 0) + 1
    md.append("## Protocol breakdown (passed filters)")
    md.append("")
    md.append("| Protocol | Count |")
    md.append("|----------|-------|")
    for p in sorted(proto_counts.keys()):
        md.append(f"| {p} | {proto_counts[p]} |")
    md.append("")
    md.append(f"Shadowsocks-only file: **{len(ss_lines)} configs** in `shadowsocks.txt`")
    md.append("")

    # Top 50 table
    md.append(f"## Top {len(top_n)} (ranked by download speed)")
    md.append("")
    md.append("| # | Country | City | Streak | Latency | Speed |")
    md.append("|---|---------|------|---------|---------|-------|")
    for i, r in enumerate(top_n, 1):
        md.append(f"| {i} | {country_flag(r.get('country_code') or '??')} {r.get('country_code') or '??'} | "
                 f"{(r.get('city') or '')} {(r.get('region') or '')}".strip() + " | "
                 f"{r['streak_days']}d | {r['latency_ms']}ms | {r['speed_mbps']} MB/s |")
    md.append("")

    with open(STATS_FILE, "w") as f:
        f.write("\n".join(md))


if __name__ == "__main__":
    main()
