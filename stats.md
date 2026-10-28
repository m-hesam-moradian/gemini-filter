# gemini-filter stats

- **Last run:** 2026-10-28T03:36:32.483633+00:00
- **Total runs:** 19
- **Configs gathered (raw, all sources):** 2549
- **Configs tested (after balanced cap to 5000):** 1048
- **Per-source cap:** 1000 (each source contributes at most 1000 unique configs)
- **Passed latency (< 600ms) + real Gemini check:** 44
- **Drop reasons:** {'latency_fail': 153, 'gemini_fail': 33, 'xray_fail': 0, 'xray_died': 806, 'latency_high': 12}
- **History retention:** 30 days

## Source breakdown (this run)

| Source | Type | Status | Raw | Unique |
|--------|------|--------|-----|--------|
| 0xRadikal | subscription | ok | 100 | 61 |
| Farid-Karimi | subscription | ok | 843 | 512 |
| Kwinshadow-TVC | subscription | ok | 71 | 67 |
| MahanKenway | subscription | ok | 1701 | 12 |
| V2RayRoot | subscription | ok | 287 | 214 |
| __history_survivors__ | (history) | ok | 23 | 0 |
| barry-far | subscription | ok | 451 | 170 |
| iboxz | subscription | ok | 360 | 242 |
| ircfspace-tvc | subscription | ok | 50 | 46 |
| mahdibland | subscription | ok | 4414 | 1002 |
| miladtahanian | subscription | ok | 364 | 246 |

## Protocol breakdown (passed filters)

| Protocol | Count |
|----------|-------|
| shadowsocks | 37 |
| vmess | 7 |

Shadowsocks-only file: **37 configs** in `shadowsocks.txt`

## Top 44 (ranked by download speed)

| # | Country | City | Streak | Latency | Speed |
|---|---------|------|---------|---------|-------|
| 1 | 🇺🇸 US | Dallas Texas | 3d | 286ms | 18.31 MB/s |
| 2 | 🇺🇸 US | Dallas Texas | 4d | 460ms | 17.43 MB/s |
| 3 | 🇺🇸 US | Dallas Texas | 2d | 449ms | 13.52 MB/s |
| 4 | 🇺🇸 US | Dallas Texas | 1d | 414ms | 11.19 MB/s |
| 5 | 🇺🇸 US | New York City New York | 4d | 340ms | 10.57 MB/s |
| 6 | 🇺🇸 US | New York City New York | 3d | 381ms | 9.82 MB/s |
| 7 | 🇺🇸 US | Atlanta Georgia | 2d | 382ms | 9.72 MB/s |
| 8 | 🇺🇸 US | New York City New York | 4d | 319ms | 9.68 MB/s |
| 9 | 🇺🇸 US | Washington District of Columbia | 1d | 419ms | 9.66 MB/s |
| 10 | 🇺🇸 US | Atlanta Georgia | 2d | 275ms | 9.34 MB/s |
| 11 | 🇺🇸 US | New York City New York | 3d | 410ms | 8.99 MB/s |
| 12 | 🇺🇸 US | Washington District of Columbia | 1d | 333ms | 8.63 MB/s |
| 13 | 🇺🇸 US | Newark New Jersey | 1d | 240ms | 7.7 MB/s |
| 14 | 🇺🇸 US | Miami Florida | 1d | 290ms | 7.65 MB/s |
| 15 | 🇺🇸 US | Phoenix Arizona | 1d | 311ms | 7.07 MB/s |
| 16 | 🇺🇸 US | Miami Florida | 4d | 227ms | 6.91 MB/s |
| 17 | 🇺🇸 US | Phoenix Arizona | 2d | 169ms | 6.62 MB/s |
| 18 | 🇺🇸 US | San Jose California | 1d | 218ms | 6.31 MB/s |
| 19 | 🇨🇦 CA | Toronto Ontario | 1d | 306ms | 6.24 MB/s |
| 20 | 🇺🇸 US | Seattle Washington | 1d | 326ms | 5.76 MB/s |
| 21 | 🇨🇦 CA | Vancouver British Columbia | 1d | 223ms | 5.19 MB/s |
| 22 | 🇺🇸 US | Los Angeles California | 1d | 136ms | 4.89 MB/s |
| 23 | 🇨🇦 CA | Beauharnois-Salaberry Quebec | 2d | 302ms | 4.35 MB/s |
| 24 | 🇺🇸 US | New York City New York | 1d | 316ms | 3.65 MB/s |
| 25 | 🇺🇸 US | Phoenix Arizona | 1d | 229ms | 3.43 MB/s |
| 26 | 🇺🇸 US | Phoenix Arizona | 1d | 225ms | 3.37 MB/s |
| 27 | 🇺🇸 US | Miami Florida | 1d | 299ms | 3.35 MB/s |
| 28 | 🇩🇪 DE | Frankfurt am Main Hessen | 1d | 404ms | 2.81 MB/s |
| 29 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 370ms | 2.71 MB/s |
| 30 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 4d | 365ms | 2.68 MB/s |
| 31 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 406ms | 2.67 MB/s |
| 32 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 2d | 354ms | 2.65 MB/s |
| 33 | 🇮🇹 IT | Milan Lombardia | 1d | 458ms | 2.65 MB/s |
| 34 | 🇮🇹 IT | Milan Lombardia | 1d | 438ms | 2.59 MB/s |
| 35 | 🇦🇹 AT | Vienna Vienna | 1d | 446ms | 2.47 MB/s |
| 36 | 🇯🇵 JP | Tokyo Tokyo | 2d | 444ms | 2.47 MB/s |
| 37 | 🇯🇵 JP | Tokyo Tokyo | 1d | 431ms | 2.45 MB/s |
| 38 | 🇵🇱 PL | Wroclaw Lower Silesian Voivodeship | 2d | 476ms | 2.45 MB/s |
| 39 | 🇮🇹 IT | Milan Lombardia | 1d | 424ms | 2.33 MB/s |
| 40 | 🇮🇹 IT | Milan Lombardia | 1d | 393ms | 2.31 MB/s |
| 41 | 🇮🇹 IT | Milan Lombardia | 1d | 463ms | 2.29 MB/s |
| 42 | 🇬🇧 GB | London England | 1d | 368ms | 1.33 MB/s |
| 43 | 🇳🇱 NL | Almere Stad Provincie Flevoland | 1d | 390ms | 0.89 MB/s |
| 44 | 🇺🇸 US | Los Angeles California | 1d | 531ms | 0.0 MB/s |
