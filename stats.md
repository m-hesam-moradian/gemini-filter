# gemini-filter stats

- **Last run:** 2026-10-26T02:46:22.895104+00:00
- **Total runs:** 14
- **Configs gathered (raw, all sources):** 2607
- **Configs tested (after balanced cap to 5000):** 1062
- **Per-source cap:** 1000 (each source contributes at most 1000 unique configs)
- **Passed latency (< 600ms) + real Gemini check:** 20
- **Drop reasons:** {'latency_fail': 159, 'gemini_fail': 16, 'xray_fail': 0, 'xray_died': 760, 'latency_high': 107}
- **History retention:** 30 days

## Source breakdown (this run)

| Source | Type | Status | Raw | Unique |
|--------|------|--------|-----|--------|
| 0xRadikal | subscription | ok | 100 | 47 |
| Farid-Karimi | subscription | ok | 716 | 500 |
| Kwinshadow-TVC | subscription | ok | 71 | 67 |
| MahanKenway | subscription | ok | 1522 | 15 |
| V2RayRoot | subscription | ok | 287 | 224 |
| __history_survivors__ | (history) | ok | 12 | 0 |
| barry-far | subscription | ok | 444 | 172 |
| iboxz | subscription | ok | 356 | 302 |
| ircfspace-tvc | subscription | ok | 50 | 46 |
| mahdibland | subscription | ok | 4060 | 1000 |
| miladtahanian | subscription | ok | 364 | 246 |

## Protocol breakdown (passed filters)

| Protocol | Count |
|----------|-------|
| shadowsocks | 16 |
| vmess | 4 |

Shadowsocks-only file: **16 configs** in `shadowsocks.txt`

## Top 20 (ranked by download speed)

| # | Country | City | Streak | Latency | Speed |
|---|---------|------|---------|---------|-------|
| 1 | 🇺🇸 US | Miami Florida | 2d | 598ms | 9.93 MB/s |
| 2 | 🇺🇸 US | Phoenix Arizona | 2d | 479ms | 5.68 MB/s |
| 3 | 🇨🇦 CA | Beauharnois-Salaberry Quebec | 1d | 578ms | 5.15 MB/s |
| 4 | 🇺🇸 US | Phoenix Arizona | 2d | 517ms | 5.04 MB/s |
| 5 | 🇨🇦 CA | Beauharnois-Salaberry Quebec | 2d | 104ms | 4.65 MB/s |
| 6 | 🇬🇧 GB | London England | 1d | 575ms | 4.0 MB/s |
| 7 | 🇺🇸 US | Washington District of Columbia | 1d | 486ms | 3.85 MB/s |
| 8 | 🇬🇧 GB | Manchester England | 1d | 287ms | 3.83 MB/s |
| 9 | 🇮🇹 IT | Milan Lombardia | 1d | 453ms | 3.31 MB/s |
| 10 | 🇮🇹 IT | Milan Lombardia | 1d | 334ms | 3.22 MB/s |
| 11 | 🇮🇹 IT | Milan Lombardia | 1d | 548ms | 3.16 MB/s |
| 12 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 2d | 322ms | 3.1 MB/s |
| 13 | 🇮🇹 IT | Milan Lombardia | 2d | 347ms | 3.1 MB/s |
| 14 | 🇩🇪 DE | Frankfurt am Main Hessen | 2d | 580ms | 2.92 MB/s |
| 15 | 🇺🇸 US | Los Angeles California | 2d | 376ms | 2.63 MB/s |
| 16 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 2d | 371ms | 2.63 MB/s |
| 17 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 416ms | 1.26 MB/s |
| 18 | 🇵🇱 PL | Wroclaw Lower Silesian Voivodeship | 1d | 599ms | 1.21 MB/s |
| 19 | 🇺🇸 US | Washington District of Columbia | 1d | 520ms | 0.86 MB/s |
| 20 | 🇳🇱 NL | Amsterdam Provincie Noord-Holland | 1d | 313ms | 0.0 MB/s |
