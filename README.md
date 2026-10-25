# gemini-filter

Hourly-checked v2ray configs filtered by **Gemini access** (hard requirement),
scored by **USA priority + stability (days²) + latency**, top 30 saved.

## How it works

```
every hour (GitHub Actions):
 1. fetch configs  ←  sources.json (subscriptions + telegram channels)
 2. test each one with xray-core:
       ✓ alive?           ✓ opens gemini.google.com?  (HARD requirement)
       ✓ exit IP country  ✓ latency
 3. update history.json  (100-day memory per config)
 4. score & rank  →  top30.txt  ←  paste this URL into Hiddify
```

## Scoring (max 155 pts)

| Category | Rule | Points |
|----------|------|--------|
| **Location** | USA | 30 |
| | Canada / Mexico | 18 |
| | EU (DE, NL, FI, FR, GB, …) | 12 |
| | Other | 5 |
| **Stability** | `min(days², 100)` — capped at day 10 | 0 → 100 |
| **Speed** | < 150 ms | 25 |
| | 150–300 ms | 18 |
| | 300–600 ms | 10 |
| | > 600 ms | **DROPPED** |
| **Gemini** | opens gemini.google.com | **required** (filter, no points) |

A 10-day-stable USA server at 130ms = `30 + 100 + 25 = 155` 👑
A 30-day-stable German server at 240ms = `12 + 100 + 18 = 130`
A 1-day USA server at 290ms = `30 + 1 + 18 = 49` (low — must prove itself)

## Top 30

```
1 | US | 10d | 130ms
2 | US | 21d | 180ms
3 | DE | 30d | 240ms
```

## Subscribe in Hiddify / v2rayNG

Use this raw URL (updates automatically every hour):

```
https://raw.githubusercontent.com/m-hesam-moradian/gemini-filter/main/top30.txt
```

## Where to add your sources

Edit **[`sources.json`](sources.json)** — three sections:

```jsonc
{
  "subscriptions": [
    { "name": "my-sub", "url": "https://...", "enabled": true }
  ],
  "telegram_channels": [
    { "name": "my-channel", "username": "channel_without_at", "enabled": true }
  ],
  "test_settings": { ... }   // optional tuning
}
```

After editing → commit / push. Next hourly run picks it up. **No secrets, no CI config changes needed.**

## Files

| File | Purpose |
|------|---------|
| `sources.json` | ← edit this: subscriptions + telegram channels |
| `top30.txt` | the only file Hiddify needs — auto-updated hourly |
| `all_ok.txt` | everything that passed (up to 200) — for fallback use |
| `history.json` | 100-day memory: per-config first_seen, streak, history |
| `stats.md` | human-readable run summary + top 30 table |
| `scripts/checker.py` | the engine |
| `.github/workflows/checker.yml` | hourly run (public repo = unlimited minutes) |

## Notes

- **Public repo is required** for unlimited free Actions minutes (hourly runs × ~10 min each = ~240 min/day, private would burn the 2000 min/month quota in 8 days).
- Tests run from GitHub's servers, so the checker verifies "does the proxy itself open Gemini". In practice this matches what works from Iran because TLS/CDN-based configs survive the GFW best.
- `allowInsecure: true` is used during testing because many free configs have stale certs — without it, half would fail TLS handshake.

