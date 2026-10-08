# GBL Validation Report — Καρδίτσα Ιαπωνική vs Άρης

**Season:** 2026-27  
**Competition:** Greek Basket League  
**Official source:** ESAKE game `A7698911`  
**Result:** Καρδίτσα Ιαπωνική 74–68 Άρης

This is the first live validation of the ESAKE/GBL scraper into the common Matchup Lab schema.

## Team box score

| Metric | Καρδίτσα | Άρης |
|---|---:|---:|
| Points | 74 | 68 |
| Rebounds | 38 | 39 |
| Defensive rebounds | 27 | 27 |
| Offensive rebounds | 11 | 12 |
| Assists | 20 | 19 |
| 2PM-A | 19-44 | 16-36 |
| 3PM-A | 7-21 | 5-22 |
| FTM-A | 15-21 | 21-28 |
| Blocks | 5 | 5 |
| Steals | 13 | 6 |
| Turnovers | 18 | 21 |
| Fouls committed | 28 | 20 |
| Fouls received | 20 | 26 |
| Estimated possessions | 81.24 | 79.32 |
| ESAKE Rank | 83 | 65 |

## Άρης — player box score sample

| Player | MIN | PTS | REB | AST | 2PM-A | 3PM-A | FTM-A | FC | FR | RANK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Jeremiah Robinson-Earl | 28:58 | 25 | 8 | 2 | 6-10 | 1-5 | 10-11 | 1 | 6 | 26 |
| E.J. Liddell | 20:12 | 14 | 3 | 1 | 5-8 | 0-3 | 4-4 | 5 | 2 | 13 |
| Matt Morgan | 23:10 | 7 | 0 | 2 | 2-4 | 1-4 | 0-0 | 1 | 0 | 2 |
| Khem Birch | 15:09 | 6 | 7 | 2 | 2-5 | 0-0 | 2-2 | 1 | 1 | 12 |
| Adam Mokoka | 23:07 | 6 | 3 | 1 | 0-3 | 1-2 | 3-6 | 2 | 7 | 3 |
| Vasilis Toliopoulos | 20:01 | 5 | 1 | 2 | 0-1 | 1-4 | 2-3 | 0 | 4 | 0 |

## Καρδίτσα — leading scorers sample

| Player | MIN | PTS | REB | AST | 2PM-A | 3PM-A | FTM-A | FC | FR | RANK |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ja'Vier Francis | 24:55 | 19 | 9 | 0 | 7-8 | 0-0 | 5-6 | 2 | 5 | 29 |
| Jordan McRae | 28:17 | 17 | 3 | 1 | 6-16 | 1-3 | 2-3 | 3 | 3 | 7 |
| Justin Turner | 24:11 | 11 | 0 | 4 | 1-5 | 2-3 | 3-4 | 3 | 4 | 6 |
| Chris Smith | 21:59 | 8 | 8 | 2 | 3-6 | 0-2 | 2-2 | 4 | 1 | 12 |

## Scraper validation

- 1 official GBL game ingested
- 2 normalized team rows
- 24 normalized player rows
- 0 ingestion errors
- Team totals match the official ESAKE boxscore
- Player scoring/rebounding/assist/shooting/foul fields parsed successfully
- Estimated possessions calculated with `FGA - OREB + TO + 0.44 × FTA`

## Still to enrich

- Game date metadata
- Player position from ESAKE player profiles
- Starter flag
- Play-by-play events
- Full current-season GBL discovery/backfill

The report is intentionally descriptive. Matchup interpretation remains in the Streamlit/analytics layer.
