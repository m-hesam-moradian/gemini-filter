# gemini-filter

Hourly-checked v2ray configs filtered through a **waterfall pipeline** — each stage
drops the failures — and finally re-ranked by **download speed**. Top 50 saved,
with country flag + city name in each config name.

## Pipeline (waterfall)

```
every hour (GitHub Actions):

  Stage 1  gather          ←  sources.json (subscriptions + telegram)
  Stage 2  balanced cap    ←  if > 5000, random pull with per-source equal share
  Stage 3  latency test    ←  drop > 600 ms
  Stage 4  real Gemini     ←  fetch gemini.google.com, drop geo-blocked pages
  Stage 5  top 50          ←  by (country + stability + latency) score
  Stage 6  speed test      ←  download 5MB through each, re-rank by MB/s
  Stage 7  output          ←  top50.txt, shadowsocks.txt, stats.md
```

Stage 4 is the key fix — Gemini returns HTTP 200 even when geo-blocking you.
The checker parses the page body and drops configs that show
"Gemini is not supported in your country".

## Final ranking — by download speed

After 50 candidates pass all filters, each downloads a 5 MB file through
Cloudflare's speed test endpoint. The final sort is by **MB/s descending** —
fastest first. Latency still matters (it gates stage 3) but the final ordering
is purely speed-based.

## Scoring (used only to pick the 50 candidates — final ranking is by speed)

| Category | Rule | Points |
|----------|------|--------|
| **Location** | USA | 30 |
| | Canada / Mexico | 18 |
| | EU (DE, NL, FI, FR, GB, …) | 12 |
| | Other | 5 |
| **Stability** | `min(days², 100)` — capped at day 10 | 0 → 100 |
| **Latency** | < 150 ms | 25 |
| | 150–300 ms | 18 |
| | 300–600 ms | 10 |
| | > 600 ms | **DROPPED** |
| **Gemini** | opens gemini.google.com (page-content check) | **required** (filter, no points) |

## Top 50 — config name format

```
1 | 🇺🇸 Ashburn VA | 7d | 23ms | 19.7 MB/s
2 | 🇺🇸 Frankfurt HE | 21d | 180ms | 12.5 MB/s
3 | 🇩🇪 Munich BY | 30d | 240ms | 7.2 MB/s
```

## Subscribe in Hiddify / v2rayNG

```
https://raw.githubusercontent.com/m-hesam-moradian/gemini-filter/main/top50.txt
```

Shadowsocks-only (for clients that want SS only):

```
https://raw.githubusercontent.com/m-hesam-moradian/gemini-filter/main/shadowsocks.txt
```

## Where to add your sources

Edit **[`sources.json`](sources.json)**:

```jsonc
{
  "subscriptions": [
    { "name": "my-sub", "url": "https://...", "enabled": true }
  ],
  "telegram_channels": [
    { "name": "my-channel", "username": "channel_without_at", "enabled": true }
  ],
  "test_settings": {
    "max_configs_per_run": 5000,
    "history_retention_days": 30,
    "concurrent_workers": 8
  }
}
```

After editing → commit / push. Next hourly run picks it up.

## Files

| File | Purpose |
|------|---------|
| `sources.json` | ← edit this: subscriptions + telegram channels |
| `top50.txt` | the only file Hiddify needs — top 50 ranked by speed, auto-updated hourly |
| `shadowsocks.txt` | all shadowsocks configs that passed filters |
| `all_ok.txt` | everything that passed (up to 200) — for fallback use |
| `history.json` | 30-day memory: per-config first_seen, streak, history |
| `stats.md` | run summary + per-source breakdown + protocol counts + top 50 table |
| `scripts/checker.py` | the engine |
| `.github/workflows/checker.yml` | hourly run (public repo = unlimited minutes) |

## How to verify a run worked

1. Open https://github.com/m-hesam-moradian/gemini-filter/actions
2. Click the latest "hourly-checker" run
3. Step "run checker" shows the waterfall:
   - `gather: ...` — fetched each source OK?
   - `stage 3+4 — testing N configs` — pipeline running
   - `drop reasons: {...}` — how many failed latency / Gemini
   - `selected top 50 candidates for speed test`
   - `done`
4. Step "commit results" should end with `main -> main` (success)
5. `stats.md` shows: per-source raw counts, protocol breakdown, top 50 table with speed

## Notes

- **Public repo** = unlimited free GitHub Actions minutes (hourly × ~10 min = ~240 min/day).
- Tests run from GitHub's servers; we verify "does the proxy itself open Gemini". TLS/CDN-based configs survive the GFW best, so this matches Iran's reality well.
- `allowInsecure: true` is used during testing because many free configs have stale certs — without it, half would fail TLS handshake.
- 30-day history (was 100) keeps `history.json` lighter.
- If a source has 100k configs and another has 5k, the balanced random pull gives each source an equal share of the 5000-slot cap — no source can dominate.
