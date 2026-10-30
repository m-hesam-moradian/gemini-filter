# gemini-filter stats

- **Last run:** 2026-10-30T12:00:00.073961+00:00
- **Total runs:** 25
- **Configs gathered (raw, all sources):** 3719
- **Configs tested (after balanced cap to 5000):** 1866
- **Per-source cap:** 1000 (each source contributes at most 1000 unique configs)
- **Passed latency (< 600ms) + real Gemini check:** 27
- **Drop reasons:** {'latency_fail': 430, 'gemini_fail': 28, 'xray_fail': 0, 'xray_died': 1290, 'latency_high': 91}
- **History retention:** 30 days

## Source breakdown (this run)

| Source | Type | Status | Raw | Unique |
|--------|------|--------|-----|--------|
| 0xRadikal | subscription | ok | 100 | 42 |
| Farid-Karimi | subscription | ok | 891 | 613 |
| Kwinshadow-TVC | subscription | ok | 71 | 65 |
| MahanKenway | subscription | ok | 1623 | 1002 |
| V2RayRoot | subscription | ok | 287 | 224 |
| __history_survivors__ | (history) | ok | 10 | 0 |
| barry-far | subscription | ok | 460 | 169 |
| iboxz | subscription | ok | 364 | 310 |
| ircfspace-tvc | subscription | ok | 50 | 46 |
| mahdibland | subscription | ok | 4361 | 1000 |
| miladtahanian | subscription | ok | 364 | 258 |

## Protocol breakdown (passed filters)

| Protocol | Count |
|----------|-------|
| shadowsocks | 25 |
| vmess | 2 |

Shadowsocks-only file: **25 configs** in `shadowsocks.txt`

## Top 27 (ranked by download speed)

| # | Country | City | Streak | Latency | Speed |
|---|---------|------|---------|---------|-------|
| 1 | 🇺🇸 US | Phoenix Arizona | 3d | 128ms | 17.6 MB/s |
| 2 | 🇺🇸 US | Dallas Texas | 3d | 552ms | 10.6 MB/s |
| 3 | 🇺🇸 US | Dallas Texas | 6d | 140ms | 10.25 MB/s |
| 4 | 🇺🇸 US | Dallas Texas | 1d | 137ms | 10.05 MB/s |
| 5 | 🇺🇸 US | Dallas Texas | 5d | 422ms | 9.98 MB/s |
| 6 | 🇺🇸 US | Atlanta Georgia | 4d | 567ms | 7.23 MB/s |
| 7 | 🇺🇸 US | Phoenix Arizona | 3d | 574ms | 6.81 MB/s |
| 8 | 🇺🇸 US | Washington District of Columbia | 2d | 411ms | 6.52 MB/s |
| 9 | 🇺🇸 US | Newark New Jersey | 3d | 202ms | 6.35 MB/s |
| 10 | 🇺🇸 US | Miami Florida | 3d | 485ms | 6.33 MB/s |
| 11 | 🇺🇸 US | Miami Florida | 6d | 460ms | 6.25 MB/s |
| 12 | 🇺🇸 US | Washington District of Columbia | 1d | 339ms | 4.43 MB/s |
| 13 | 🇯🇵 JP | Tokyo Tokyo | 4d | 328ms | 4.21 MB/s |
| 14 | 🇯🇵 JP | Tokyo Tokyo | 3d | 332ms | 4.21 MB/s |
| 15 | 🇯🇵 JP | Tokyo Tokyo | 3d | 333ms | 4.12 MB/s |
| 16 | 🇨🇦 CA | Beauharnois-Salaberry Quebec | 1d | 339ms | 4.11 MB/s |
| 17 | 🇨🇦 CA | Toronto Ontario | 1d | 205ms | 3.29 MB/s |
| 18 | 🇬🇧 GB | Manchester England | 3d | 467ms | 3.0 MB/s |
| 19 | 🏳️ ?? | | 3d | 530ms | 2.79 MB/s |
| 20 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 487ms | 2.69 MB/s |
| 21 | 🇦🇹 AT | Vienna Vienna | 2d | 547ms | 2.59 MB/s |
| 22 | 🇮🇹 IT | Milan Lombardia | 1d | 525ms | 2.59 MB/s |
| 23 | 🇨🇦 CA | Beauharnois-Salaberry Quebec | 1d | 349ms | 2.1 MB/s |
| 24 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 593ms | 2.04 MB/s |
| 25 | 🇺🇸 US | New York City New York | 6d | 377ms | 2.03 MB/s |
| 26 | 🇺🇸 US | New York City New York | 5d | 443ms | 1.93 MB/s |
| 27 | 🇨🇦 CA | Beauharnois-Salaberry Quebec | 1d | 516ms | 1.15 MB/s |
