# gemini-filter stats

- **Last run:** 2026-10-29T12:08:37.359184+00:00
- **Total runs:** 23
- **Configs gathered (raw, all sources):** 3690
- **Configs tested (after balanced cap to 5000):** 1816
- **Per-source cap:** 1000 (each source contributes at most 1000 unique configs)
- **Passed latency (< 600ms) + real Gemini check:** 30
- **Drop reasons:** {'latency_fail': 449, 'gemini_fail': 34, 'xray_fail': 0, 'xray_died': 1240, 'latency_high': 63}
- **History retention:** 30 days

## Source breakdown (this run)

| Source | Type | Status | Raw | Unique |
|--------|------|--------|-----|--------|
| 0xRadikal | subscription | ok | 100 | 60 |
| Farid-Karimi | subscription | ok | 812 | 546 |
| Kwinshadow-TVC | subscription | ok | 71 | 68 |
| MahanKenway | subscription | ok | 1651 | 1001 |
| V2RayRoot | subscription | ok | 287 | 218 |
| __history_survivors__ | (history) | ok | 9 | 0 |
| barry-far | subscription | ok | 459 | 212 |
| iboxz | subscription | ok | 366 | 290 |
| ircfspace-tvc | subscription | ok | 50 | 46 |
| mahdibland | subscription | ok | 4312 | 1000 |
| miladtahanian | subscription | ok | 364 | 258 |

## Protocol breakdown (passed filters)

| Protocol | Count |
|----------|-------|
| shadowsocks | 26 |
| vmess | 4 |

Shadowsocks-only file: **26 configs** in `shadowsocks.txt`

## Top 30 (ranked by download speed)

| # | Country | City | Streak | Latency | Speed |
|---|---------|------|---------|---------|-------|
| 1 | 🇺🇸 US | Washington District of Columbia | 2d | 215ms | 51.19 MB/s |
| 2 | 🇺🇸 US | Washington District of Columbia | 1d | 233ms | 42.62 MB/s |
| 3 | 🇺🇸 US | Newark New Jersey | 2d | 157ms | 23.43 MB/s |
| 4 | 🇺🇸 US | Miami Florida | 2d | 355ms | 14.35 MB/s |
| 5 | 🇺🇸 US | Miami Florida | 5d | 371ms | 13.88 MB/s |
| 6 | 🇺🇸 US | Atlanta Georgia | 3d | 494ms | 12.26 MB/s |
| 7 | 🇺🇸 US | Atlanta Georgia | 3d | 199ms | 12.12 MB/s |
| 8 | 🇺🇸 US | Dallas Texas | 5d | 112ms | 11.73 MB/s |
| 9 | 🇺🇸 US | Dallas Texas | 4d | 569ms | 11.24 MB/s |
| 10 | 🇺🇸 US | Dallas Texas | 2d | 597ms | 10.9 MB/s |
| 11 | 🇺🇸 US | New York City New York | 5d | 317ms | 10.27 MB/s |
| 12 | 🇺🇸 US | New York City New York | 4d | 221ms | 10.04 MB/s |
| 13 | 🇺🇸 US | New York City New York | 5d | 279ms | 9.78 MB/s |
| 14 | 🇺🇸 US | New York City New York | 4d | 283ms | 9.58 MB/s |
| 15 | 🇺🇸 US | Phoenix Arizona | 2d | 182ms | 7.46 MB/s |
| 16 | 🇺🇸 US | Phoenix Arizona | 2d | 194ms | 7.35 MB/s |
| 17 | 🇨🇦 CA | Vancouver British Columbia | 2d | 595ms | 6.35 MB/s |
| 18 | 🇺🇸 US | Seattle Washington | 2d | 577ms | 6.29 MB/s |
| 19 | 🇬🇧 GB | London England | 2d | 427ms | 5.56 MB/s |
| 20 | 🇬🇧 GB | Manchester England | 2d | 282ms | 4.92 MB/s |
| 21 | 🇮🇹 IT | Milan Lombardia | 1d | 435ms | 4.75 MB/s |
| 22 | 🇺🇸 US | Miami Florida | 2d | 486ms | 4.57 MB/s |
| 23 | 🇩🇪 DE | Frankfurt am Main Hessen | 1d | 455ms | 4.51 MB/s |
| 24 | 🇺🇸 US | Phoenix Arizona | 2d | 456ms | 4.34 MB/s |
| 25 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 2d | 477ms | 4.24 MB/s |
| 26 | 🇦🇹 AT | Vienna Vienna | 1d | 355ms | 4.12 MB/s |
| 27 | 🏳️ ?? | | 1d | 367ms | 3.48 MB/s |
| 28 | 🇯🇵 JP | Tokyo Tokyo | 2d | 493ms | 2.85 MB/s |
| 29 | 🇯🇵 JP | Tokyo Tokyo | 2d | 496ms | 2.84 MB/s |
| 30 | 🇯🇵 JP | Tokyo Tokyo | 3d | 492ms | 2.83 MB/s |
