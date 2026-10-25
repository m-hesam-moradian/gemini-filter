# gemini-filter stats

- **Last run:** 2026-10-25T10:41:27.947013+00:00
- **Total runs:** 10
- **Configs gathered (raw, all sources):** 1185
- **Configs tested (after balanced cap to 5000):** 497
- **Per-source cap:** 1000 (each source contributes at most 1000 unique configs)
- **Passed latency (< 600ms) + real Gemini check:** 10
- **Drop reasons:** {'latency_fail': 93, 'gemini_fail': 27, 'xray_fail': 0, 'xray_died': 334, 'latency_high': 33}
- **History retention:** 30 days

## Source breakdown (this run)

| Source | Type | Status | Raw | Unique |
|--------|------|--------|-----|--------|
| __history_survivors__ | (history) | ok | 33 | 0 |
| mahdibland | subscription | ok | 4048 | 1000 |
| mifa-world | subscription | ok | 200 | 179 |
| v2rayng_free | telegram | ok | 12 | 6 |

## Protocol breakdown (passed filters)

| Protocol | Count |
|----------|-------|
| shadowsocks | 9 |
| vmess | 1 |

Shadowsocks-only file: **9 configs** in `shadowsocks.txt`

## Top 10 (ranked by download speed)

| # | Country | City | Streak | Latency | Speed |
|---|---------|------|---------|---------|-------|
| 1 | 🇺🇸 US | Dallas Texas | 1d | 156ms | 10.44 MB/s |
| 2 | 🇺🇸 US | Phoenix Arizona | 1d | 116ms | 5.74 MB/s |
| 3 | 🇺🇸 US | New York City New York | 1d | 188ms | 5.74 MB/s |
| 4 | 🇺🇸 US | New York City New York | 1d | 392ms | 5.38 MB/s |
| 5 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 504ms | 2.18 MB/s |
| 6 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 488ms | 2.14 MB/s |
| 7 | 🇦🇹 AT | Vienna Vienna | 1d | 531ms | 2.12 MB/s |
| 8 | 🇰🇷 KR | Seoul Seoul | 1d | 510ms | 2.09 MB/s |
| 9 | 🇮🇹 IT | Milan Lombardia | 1d | 513ms | 2.09 MB/s |
| 10 | 🇺🇸 US | New York City New York | 1d | 354ms | 0.0 MB/s |
