# gemini-filter stats

- **Last run:** 2026-10-25T15:26:00.659648+00:00
- **Total runs:** 12
- **Configs gathered (raw, all sources):** 3594
- **Configs tested (after balanced cap to 5000):** 1741
- **Per-source cap:** 1000 (each source contributes at most 1000 unique configs)
- **Passed latency (< 600ms) + real Gemini check:** 18
- **Drop reasons:** {'latency_fail': 398, 'gemini_fail': 40, 'xray_fail': 0, 'xray_died': 1209, 'latency_high': 76}
- **History retention:** 30 days

## Source breakdown (this run)

| Source | Type | Status | Raw | Unique |
|--------|------|--------|-----|--------|
| 0xRadikal | subscription | ok | 100 | 56 |
| Farid-Karimi | subscription | ok | 693 | 483 |
| Kwinshadow-TVC | subscription | ok | 71 | 68 |
| MahanKenway | subscription | ok | 1495 | 1000 |
| V2RayRoot | subscription | ok | 287 | 221 |
| __history_survivors__ | (history) | ok | 4 | 0 |
| barry-far | subscription | ok | 451 | 180 |
| iboxz | subscription | ok | 358 | 298 |
| ircfspace-tvc | subscription | ok | 50 | 46 |
| mahdibland | subscription | ok | 4048 | 1000 |
| miladtahanian | subscription | ok | 364 | 246 |

## Protocol breakdown (passed filters)

| Protocol | Count |
|----------|-------|
| shadowsocks | 17 |
| vmess | 1 |

Shadowsocks-only file: **17 configs** in `shadowsocks.txt`

## Top 18 (ranked by download speed)

| # | Country | City | Streak | Latency | Speed |
|---|---------|------|---------|---------|-------|
| 1 | 🇺🇸 US | Phoenix Arizona | 1d | 556ms | 13.42 MB/s |
| 2 | 🇨🇦 CA | Beauharnois-Salaberry Quebec | 1d | 289ms | 3.31 MB/s |
| 3 | 🇯🇵 JP | Tokyo Tokyo | 1d | 347ms | 3.03 MB/s |
| 4 | 🇯🇵 JP | Tokyo Tokyo | 1d | 356ms | 3.01 MB/s |
| 5 | 🇯🇵 JP | Tokyo Tokyo | 1d | 340ms | 2.86 MB/s |
| 6 | 🇬🇧 GB | Manchester England | 1d | 542ms | 2.05 MB/s |
| 7 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 501ms | 2.04 MB/s |
| 8 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 510ms | 2.03 MB/s |
| 9 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 522ms | 2.03 MB/s |
| 10 | 🇦🇹 AT | Vienna Vienna | 1d | 527ms | 2.03 MB/s |
| 11 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 514ms | 2.0 MB/s |
| 12 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 558ms | 1.99 MB/s |
| 13 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 496ms | 1.95 MB/s |
| 14 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 510ms | 1.94 MB/s |
| 15 | 🇮🇹 IT | Milan Lombardia | 1d | 508ms | 1.91 MB/s |
| 16 | 🇺🇸 US | Washington District of Columbia | 1d | 291ms | 1.72 MB/s |
| 17 | 🇺🇸 US | Phoenix Arizona | 1d | 406ms | 1.27 MB/s |
| 18 | 🇨🇦 CA | Montreal Quebec | 1d | 408ms | 0.87 MB/s |
