#!/usr/bin/env python3
"""
gemini-filter — hourly v2ray config checker
============================================
Fetches configs from sources.json, tests each one for:
  1. Alive (proxy connects)
  2. Opens gemini.google.com (HARD REQUIREMENT — fails = dropped)
  3. Exit IP country (USA = 30 pts, etc.)
  4. Latency (<150ms = 25 pts, 150-300 = 18, 300-600 = 10, >600 = DROPPED)
  5. Stability (min(days^2, 100) — capped at day 10)

Top 30 by score saved to top30.txt with names like:
  1 | US | 10d | 130ms
  2 | DE | 21d | 240ms
"""

import base64
import concurrent.futures
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_FILE = os.path.join(ROOT, "sources.json")
HISTORY_FILE = os.path.join(ROOT, "history.json")
TOP30_FILE = os.path.join(ROOT, "top30.txt")
ALL_OK_FILE = os.path.join(ROOT, "all_ok.txt")
STATS_FILE = os.path.join(ROOT, "stats.md")
XRAY_BIN = os.path.join(ROOT, "bin", "xray")
XRAY_VERSION = "v26.10.21"
# Fallback versions if the primary fails (older releases that definitely exist)
XRAY_FALLBACK_VERSIONS = ["v25.10.7", "v25.1.30", "v24.12.18"]

GEMINI_URL = "https://gemini.google.com/"
LATENCY_URL = "https://www.google.com/generate_204"
IP_LOOKUP_URL = "https://ipinfo.io/json"

COUNTRY_SCORES = {
    "US": 30, "CA": 18, "MX": 18,
    "DE": 12, "NL": 12, "FI": 12, "FR": 12, "GB": 12,
    "SE": 12, "CH": 12, "AT": 12, "IE": 12, "BE": 12, "DK": 12, "NO": 12,
    "TR": 10, "AE": 8, "JP": 8, "KR": 8, "SG": 8, "HK": 6,
}
DEFAULT_COUNTRY_SCORE = 5

FLAG_BASE = {
    "US": "US", "CA": "CA", "MX": "MX",
    "DE": "DE", "NL": "NL", "FI": "FI", "FR": "FR", "GB": "UK",
    "SE": "SE", "CH": "CH", "AT": "AT", "IE": "IE", "BE": "BE",
    "DK": "DK", "NO": "NO", "TR": "TR", "AE": "AE",
    "JP": "JP", "KR": "KR", "SG": "SG", "HK": "HK",
}


# ---------------------------------------------------------------------------
# Config parsing — vmess://, vless://, trojan://, ss://
# ---------------------------------------------------------------------------

def parse_vmess(uri: str) -> dict:
    """vmess://base64json"""
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
    """vless://, trojan://, ss://"""
    try:
        if not uri.startswith(scheme + "://"):
            return None
        body = uri[len(scheme) + 3:]
        # split off fragment (remark)
        if "#" in body:
            body, frag = body.split("#", 1)
            remark = urllib.parse.unquote(frag)
        else:
            remark = ""
        # split off query
        if "?" in body:
            main, query = body.split("?", 1)
        else:
            main, query = body, ""
        # userinfo@host:port
        if "@" not in main:
            return None
        userinfo, hostport = main.rsplit("@", 1)
        if ":" not in hostport:
            return None
        host, port = hostport.rsplit(":", 1)
        port = int(port)
        params = dict(urllib.parse.parse_qsl(query))

        if scheme == "ss":
            # userinfo may be base64(method:password)
            try:
                dec = base64.urlsafe_b64decode(userinfo + "=" * (-len(userinfo) % 4)).decode("utf-8")
                method, password = dec.split(":", 1)
            except Exception:
                method, password = userinfo.split(":", 1) if ":" in userinfo else ("none", userinfo)
            return {
                "protocol": "shadowsocks",
                "address": host, "port": port,
                "method": method, "password": password,
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
    """Stable identity of a config (ignoring remark)."""
    return f"{c['protocol']}|{c['address']}|{c['port']}|{c.get('id', c.get('password', ''))}"


def config_to_uri(c: dict) -> str:
    """Re-serialize so Hiddify/v2rayNG can import."""
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
    versions_to_try = [XRAY_VERSION] + XRAY_FALLBACK_VERSIONS
    for ver in versions_to_try:
        url = f"https://github.com/XTLS/Xray-core/releases/download/{ver}/Xray-linux-{arch}.zip"
        print(f"[setup] trying xray {ver} from {url}")
        zip_path = XRAY_BIN + ".zip"
        # -L follows redirects, -f fails on 4xx/5xx silently
        rc = subprocess.run(["wget", "-qL", "-O", zip_path, url]).returncode
        if rc != 0 or not os.path.exists(zip_path) or os.path.getsize(zip_path) < 1000:
            print(f"[setup] failed {ver}")
            continue
        try:
            subprocess.run(["unzip", "-o", zip_path, "-d", bin_dir], check=True,
                           capture_output=True)
            os.chmod(XRAY_BIN, 0o755)
            os.remove(zip_path)
            print(f"[setup] xray {ver} ready")
            return XRAY_BIN
        except Exception as e:
            print(f"[setup] unzip failed for {ver}: {e}")
            continue
    raise RuntimeError("could not download xray-core from any version")


def build_xray_config(c: dict, socks_port: int) -> dict:
    """Translate parsed config into xray-core JSON."""
    inbound = {
        "port": socks_port,
        "listen": "127.0.0.1",
        "protocol": "socks",
        "settings": {"auth": "noauth", "udp": False},
    }

    stream = {"network": c.get("network", "tcp")}
    net = stream["network"]
    if net == "ws":
        stream["wsSettings"] = {"path": c.get("path", "/"), "headers": {"Host": c.get("host", "") or c.get("sni", "")}}
    elif net == "grpc":
        stream["grpcSettings"] = {"serviceName": c.get("path", "") or c.get("host", "")}
    elif net == "h2":
        stream["httpSettings"] = {"path": c.get("path", "/"), "host": [c.get("host", "")] if c.get("host") else []}

    sec = c.get("tls", "")
    if sec in ("tls", "reality") or (c["protocol"] in ("trojan", "vless") and sec != "none"):
        stream["security"] = "tls"
        stream["tlsSettings"] = {
            "serverName": c.get("sni", "") or c["address"],
            "allowInsecure": True,
        }
    else:
        stream["security"] = "none"

    if c["protocol"] == "vmess":
        outbound = {
            "protocol": "vmess",
            "settings": {"vnext": [{
                "address": c["address"], "port": c["port"],
                "users": [{"id": c["id"], "alterId": c.get("alterId", 0), "security": "auto"}],
            }]},
            "streamSettings": stream,
        }
    elif c["protocol"] == "vless":
        users = {"id": c["id"], "encryption": "none"}
        if c.get("flow"):
            users["flow"] = c["flow"]
        outbound = {
            "protocol": "vless",
            "settings": {"vnext": [{
                "address": c["address"], "port": c["port"],
                "users": [users],
            }]},
            "streamSettings": stream,
        }
    elif c["protocol"] == "trojan":
        outbound = {
            "protocol": "trojan",
            "settings": {"servers": [{
                "address": c["address"], "port": c["port"],
                "password": c["password"],
            }]},
            "streamSettings": stream,
        }
    elif c["protocol"] == "shadowsocks":
        outbound = {
            "protocol": "shadowsocks",
            "settings": {"servers": [{
                "address": c["address"], "port": c["port"],
                "method": c["method"], "password": c["password"],
            }]},
            "streamSettings": stream,
        }
    else:
        return None

    return {
        "log": {"loglevel": "warning"},
        "inbounds": [inbound],
        "outbounds": [outbound],
    }


# ---------------------------------------------------------------------------
# Source fetching
# ---------------------------------------------------------------------------

def fetch_subscription(url: str, timeout: int = 30) -> list:
    """A subscription URL returns either a raw list of v2ray links or base64 of them."""
    req = urllib.request.Request(url, headers={"User-Agent": "v2rayNG/1.8.5"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", errors="ignore").strip()
    lines = []
    # try base64 decode
    try:
        dec = base64.b64decode(body + "=" * (-len(body) % 4)).decode("utf-8", errors="ignore")
        if any(s + "://" in dec for s in ("vmess", "vless", "trojan", "ss")):
            body = dec
    except Exception:
        pass
    for line in body.splitlines():
        line = line.strip()
        if line and any(line.startswith(s + "://") for s in ("vmess", "vless", "trojan", "ss")):
            lines.append(line)
    return lines


def fetch_telegram(username: str, timeout: int = 30) -> list:
    """Pull recent messages from a public Telegram channel via t.me/s/CHANNEL."""
    url = f"https://t.me/s/{username.lstrip('@')}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            html = r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[warn] telegram {username}: {e}")
        return []
    # telegram wraps links in href="..."
    return list(set(re.findall(r'(?:vmess|vless|trojan|ss)://[^\s"\'<>]+', html)))


def gather_configs(sources: dict) -> list:
    seen = set()
    out = []
    for sub in sources.get("subscriptions", []):
        if not sub.get("enabled", True):
            continue
        try:
            print(f"[fetch] subscription {sub['name']}")
            for line in fetch_subscription(sub["url"]):
                c = parse_config(line)
                if c:
                    sig = config_signature(c)
                    if sig not in seen:
                        seen.add(sig)
                        out.append(c)
        except Exception as e:
            print(f"[warn] sub {sub['name']}: {e}")
    for tg in sources.get("telegram_channels", []):
        if not tg.get("enabled", True):
            continue
        try:
            print(f"[fetch] telegram {tg['username']}")
            for line in fetch_telegram(tg["username"]):
                c = parse_config(line)
                if c:
                    sig = config_signature(c)
                    if sig not in seen:
                        seen.add(sig)
                        out.append(c)
        except Exception as e:
            print(f"[warn] tg {tg['username']}: {e}")
    return out


# ---------------------------------------------------------------------------
# Testing one config
# ---------------------------------------------------------------------------

def free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def test_one_config(xray_bin: str, c: dict, settings: dict) -> dict:
    """
    Returns dict with keys: alive(bool), gemini_ok(bool), latency_ms(int|None),
    country(str|None), country_code(str|None), error(str|None)
    """
    port = free_port()
    xray_cfg = build_xray_config(c, port)
    if not xray_cfg:
        return {"alive": False, "gemini_ok": False, "latency_ms": None,
                "country": None, "country_code": None, "error": "bad_config"}

    cfg_path = f"/tmp/xray_{port}.json"
    with open(cfg_path, "w") as f:
        json.dump(xray_cfg, f)

    proc = None
    try:
        proc = subprocess.Popen([xray_bin, "run", "-c", cfg_path],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)
        if proc.poll() is not None:
            return {"alive": False, "gemini_ok": False, "latency_ms": None,
                    "country": None, "country_code": None, "error": "xray_died"}

        proxies = {"http": f"socks5h://127.0.0.1:{port}",
                   "https": f"socks5h://127.0.0.1:{port}"}
        timeout = settings.get("test_timeout_seconds", 8)

        # 1) latency test
        t0 = time.time()
        req = urllib.request.Request(LATENCY_URL, headers={"User-Agent": "curl/8"})
        try:
            # use curl through SOCKS for speed
            r = subprocess.run(
                ["curl", "-sS", "-x", f"socks5h://127.0.0.1:{port}", "-o", "/dev/null",
                 "-w", "%{http_code} %{time_total}", "--max-time", str(timeout),
                 LATENCY_URL],
                capture_output=True, text=True, timeout=timeout + 2)
            if r.returncode != 0 or not r.stdout.strip():
                return {"alive": False, "gemini_ok": False, "latency_ms": None,
                        "country": None, "country_code": None, "error": "latency_fail"}
            parts = r.stdout.strip().split()
            http_code = int(parts[0]) if parts and parts[0].isdigit() else 0
            if http_code not in (200, 204):
                return {"alive": False, "gemini_ok": False, "latency_ms": None,
                        "country": None, "country_code": None, "error": f"http_{http_code}"}
            latency_ms = int(float(parts[1]) * 1000)
        except Exception:
            return {"alive": False, "gemini_ok": False, "latency_ms": None,
                    "country": None, "country_code": None, "error": "latency_exception"}

        # 2) Gemini test (HARD requirement)
        r = subprocess.run(
            ["curl", "-sS", "-x", f"socks5h://127.0.0.1:{port}", "-o", "/dev/null",
             "-w", "%{http_code}", "--max-time", str(timeout), "-L", GEMINI_URL],
            capture_output=True, text=True, timeout=timeout + 2)
        gemini_ok = r.returncode == 0 and r.stdout.strip() in ("200", "302", "301", "303")

        # 3) Exit IP location
        country_code = None
        country_name = None
        try:
            r = subprocess.run(
                ["curl", "-sS", "-x", f"socks5h://127.0.0.1:{port}", "--max-time", str(timeout),
                 IP_LOOKUP_URL],
                capture_output=True, text=True, timeout=timeout + 2)
            if r.returncode == 0 and r.stdout.strip().startswith("{"):
                info = json.loads(r.stdout)
                country_code = (info.get("country") or "").upper() or None
                country_name = info.get("country") or country_code
        except Exception:
            pass

        return {
            "alive": True,
            "gemini_ok": gemini_ok,
            "latency_ms": latency_ms,
            "country_code": country_code,
            "country": country_name,
            "error": None,
        }
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except Exception:
                proc.kill()
        try:
            os.remove(cfg_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_country(cc: str) -> int:
    return COUNTRY_SCORES.get(cc, DEFAULT_COUNTRY_SCORE) if cc else 0


def score_latency(ms: int) -> int:
    if ms is None:
        return 0
    if ms < 150:
        return 25
    if ms < 300:
        return 18
    if ms < 600:
        return 10
    return -1  # dropped


def score_stability(days: int) -> int:
    if days <= 0:
        return 0
    return min(days * days, 100)


def country_flag(cc: str) -> str:
    if not cc:
        return "??"
    return FLAG_BASE.get(cc.upper(), cc.upper())


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

def today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_history() -> dict:
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except Exception:
        return {"configs": {}, "last_updated": None, "stats": {}}


def save_history(h: dict):
    h["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(HISTORY_FILE, "w") as f:
        json.dump(h, f, indent=2)


def update_history(h: dict, sig: str, today_ok: bool, retention_days: int) -> dict:
    """Returns the entry with computed streak_days and first_seen."""
    cfgs = h.setdefault("configs", {})
    e = cfgs.get(sig, {"first_seen": today_utc(), "history": []})

    today = today_utc()
    # dedupe today's entry — keep last
    if e["history"] and e["history"][-1].get("date") == today:
        e["history"][-1] = {"date": today, "ok": today_ok}
    else:
        e["history"].append({"date": today, "ok": today_ok})

    # trim
    cutoff = (datetime.now(timezone.utc).timestamp()) - retention_days * 86400
    e["history"] = [x for x in e["history"]
                    if datetime.fromisoformat(x["date"]).timestamp() >= cutoff][-retention_days:]

    # streak = consecutive ok days ending today (or last seen)
    streak = 0
    for entry in reversed(e["history"]):
        if entry["ok"]:
            streak += 1
        else:
            break

    cfgs[sig] = e
    return {"first_seen": e["first_seen"], "streak_days": streak,
            "history_len": len(e["history"])}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print(f"gemini-filter run — {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    with open(SOURCES_FILE) as f:
        sources = json.load(f)
    settings = sources.get("test_settings", {})
    retention_days = int(settings.get("history_retention_days", 100))

    xray_bin = ensure_xray()
    configs = gather_configs(sources)
    max_n = int(settings.get("max_configs_per_run", 500))
    if len(configs) > max_n:
        print(f"[main] truncating {len(configs)} -> {max_n}")
        configs = configs[:max_n]
    print(f"[main] testing {len(configs)} unique configs")

    history = load_history()

    results = []
    workers = int(settings.get("concurrent_workers", 8))

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(test_one_config, xray_bin, c, settings): c for c in configs}
        for i, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            c = futs[fut]
            try:
                t = fut.result()
            except Exception as e:
                t = {"alive": False, "gemini_ok": False, "latency_ms": None,
                     "country_code": None, "country": None, "error": str(e)}

            sig = config_signature(c)
            hinfo = update_history(history, sig, t["alive"] and t["gemini_ok"], retention_days)
            if not t["alive"] or not t["gemini_ok"]:
                continue
            lat_score = score_latency(t["latency_ms"])
            if lat_score < 0:
                continue  # >600ms dropped
            score = (score_country(t["country_code"])
                     + score_stability(hinfo["streak_days"])
                     + lat_score)
            results.append({
                "config": c,
                "country_code": t["country_code"],
                "latency_ms": t["latency_ms"],
                "streak_days": hinfo["streak_days"],
                "first_seen": hinfo["first_seen"],
                "score": score,
            })
            if i % 25 == 0:
                print(f"[main] tested {i}/{len(configs)}  kept={len(results)}")

    results.sort(key=lambda r: (-r["score"], r["latency_ms"] or 9999))
    top30 = results[:30]

    # Write top30.txt
    lines = []
    for i, r in enumerate(top30, 1):
        cc = r["country_code"] or "??"
        flag = country_flag(cc)
        name = f"{i} | {flag} | {r['streak_days']}d | {r['latency_ms']}ms"
        # update remark so Hiddify shows the same name
        r["config"]["remark"] = name
        lines.append(config_to_uri(r["config"]))
    with open(TOP30_FILE, "w") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    print(f"[main] wrote {len(top30)} configs to top30.txt")

    # Write all_ok.txt (everything that passed, up to 200)
    with open(ALL_OK_FILE, "w") as f:
        f.write("\n".join(config_to_uri(r["config"]) for r in results[:200]) + ("\n" if results else ""))

    # Write stats.md
    history["stats"] = {
        "total_runs": history.get("stats", {}).get("total_runs", 0) + 1,
        "last_run_at": datetime.now(timezone.utc).isoformat(),
        "last_run_configs_checked": len(configs),
        "last_run_alive": sum(1 for r in results if r),
        "last_run_gemini_ok": len(results),
    }
    save_history(history)
    write_stats_md(history, top30, configs)
    print("[main] done")


def write_stats_md(history: dict, top30: list, all_configs: list):
    s = history.get("stats", {})
    md = ["# gemini-filter stats", ""]
    md.append(f"- **Last run:** {s.get('last_run_at', '?')}")
    md.append(f"- **Total runs:** {s.get('total_runs', 0)}")
    md.append(f"- **Configs checked:** {s.get('last_run_configs_checked', 0)}")
    md.append(f"- **Passed (alive + Gemini + <600ms):** {s.get('last_run_gemini_ok', 0)}")
    md.append(f"- **Tracked in history:** {len(history.get('configs', {}))}")
    md.append("")
    md.append("## Top 30")
    md.append("")
    md.append("| # | Country | Streak | Latency | Score |")
    md.append("|---|---------|--------|---------|-------|")
    for i, r in enumerate(top30, 1):
        md.append(f"| {i} | {r['country_code'] or '??'} | {r['streak_days']}d | {r['latency_ms']}ms | {r['score']} |")
    md.append("")
    with open(STATS_FILE, "w") as f:
        f.write("\n".join(md))


if __name__ == "__main__":
    main()
