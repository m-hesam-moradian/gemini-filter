# gemini-filter stats

- **Last run:** 2026-10-25T20:18:41.128499+00:00
- **Total runs:** 13
- **Configs gathered (raw, all sources):** 3621
- **Configs tested (after balanced cap to 5000):** 1766
- **Per-source cap:** 1000 (each source contributes at most 1000 unique configs)
- **Passed latency (< 600ms) + real Gemini check:** 40
- **Drop reasons:** {'latency_fail': 405, 'gemini_fail': 40, 'xray_fail': 0, 'xray_died': 1225, 'latency_high': 56}
- **History retention:** 30 days

## Source breakdown (this run)

| Source | Type | Status | Raw | Unique |
|--------|------|--------|-----|--------|
| 0xRadikal | subscription | ok | 100 | 56 |
| Farid-Karimi | subscription | ok | 716 | 495 |
| Kwinshadow-TVC | subscription | ok | 71 | 67 |
| MahanKenway | subscription | ok | 1507 | 1000 |
| V2RayRoot | subscription | ok | 287 | 221 |
| barry-far | subscription | ok | 448 | 182 |
| iboxz | subscription | ok | 357 | 296 |
| ircfspace-tvc | subscription | ok | 50 | 46 |
| mahdibland | subscription | ok | 4060 | 1000 |
| miladtahanian | subscription | ok | 364 | 258 |

## Protocol breakdown (passed filters)

| Protocol | Count |
|----------|-------|
| shadowsocks | 32 |
| vmess | 8 |

Shadowsocks-only file: **32 configs** in `shadowsocks.txt`

## Top 40 (ranked by download speed)

| # | Country | City | Streak | Latency | Speed |
|---|---------|------|---------|---------|-------|
| 1 | 🇺🇸 US | Phoenix Arizona | 1d | 550ms | 27.47 MB/s |
| 2 | 🇺🇸 US | Phoenix Arizona | 1d | 87ms | 20.14 MB/s |
| 3 | 🇺🇸 US | Dallas Texas | 1d | 573ms | 11.79 MB/s |
| 4 | 🇺🇸 US | Dallas Texas | 1d | 550ms | 10.47 MB/s |
| 5 | 🇺🇸 US | Phoenix Arizona | 1d | 233ms | 7.57 MB/s |
| 6 | 🇺🇸 US | Salt Lake City Utah | 1d | 260ms | 7.28 MB/s |
| 7 | 🏳️ ?? | | 1d | 558ms | 6.08 MB/s |
| 8 | 🇺🇸 US | Atlanta Georgia | 1d | 578ms | 6.02 MB/s |
| 9 | 🇺🇸 US | New York City New York | 1d | 447ms | 5.63 MB/s |
| 10 | 🇺🇸 US | New York City New York | 1d | 547ms | 5.59 MB/s |
| 11 | 🇺🇸 US | Miami Florida | 1d | 481ms | 4.43 MB/s |
| 12 | 🇺🇸 US | San Jose California | 1d | 526ms | 3.67 MB/s |
| 13 | 🇺🇸 US | Miami Florida | 1d | 566ms | 3.67 MB/s |
| 14 | 🇨🇦 CA | Beauharnois-Salaberry Quebec | 1d | 394ms | 3.67 MB/s |
| 15 | 🇺🇸 US | Washington District of Columbia | 1d | 598ms | 3.64 MB/s |
| 16 | 🇺🇸 US | Miami Florida | 1d | 406ms | 3.49 MB/s |
| 17 | 🇯🇵 JP | Tokyo Tokyo | 1d | 336ms | 3.16 MB/s |
| 18 | 🇨🇦 CA | Beauharnois-Salaberry Quebec | 1d | 398ms | 3.09 MB/s |
| 19 | 🇯🇵 JP | Tokyo Tokyo | 1d | 343ms | 2.9 MB/s |
| 20 | 🇯🇵 JP | Tokyo Tokyo | 1d | 335ms | 2.84 MB/s |
| 21 | 🇯🇵 JP | Ibaraki Osaka | 1d | 498ms | 2.48 MB/s |
| 22 | 🇳🇱 NL | Kerkrade Provincie Limburg | 1d | 551ms | 2.35 MB/s |
| 23 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 478ms | 2.25 MB/s |
| 24 | 🇩🇪 DE | Frankfurt am Main Hessen | 1d | 422ms | 2.24 MB/s |
| 25 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 446ms | 2.21 MB/s |
| 26 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 453ms | 2.19 MB/s |
| 27 | 🇮🇹 IT | Milan Lombardia | 1d | 494ms | 2.11 MB/s |
| 28 | 🇮🇹 IT | Milan Lombardia | 1d | 512ms | 2.09 MB/s |
| 29 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 458ms | 2.07 MB/s |
| 30 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 494ms | 2.06 MB/s |
| 31 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 543ms | 2.02 MB/s |
| 32 | 🇺🇸 US | Phoenix Arizona | 1d | 69ms | 1.94 MB/s |
| 33 | 🇦🇹 AT | Vienna Vienna | 1d | 525ms | 1.89 MB/s |
| 34 | 🇸🇬 SG | Singapore South West | 1d | 564ms | 1.76 MB/s |
| 35 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 484ms | 1.52 MB/s |
| 36 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 575ms | 1.41 MB/s |
| 37 | 🇵🇱 PL | Wroclaw Lower Silesian Voivodeship | 1d | 588ms | 1.41 MB/s |
| 38 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 452ms | 1.28 MB/s |
| 39 | 🇳🇱 NL | Kerkrade Provincie Limburg | 1d | 572ms | 1.09 MB/s |
| 40 | 🇺🇸 US | Los Angeles California | 1d | 94ms | 0.0 MB/s |
