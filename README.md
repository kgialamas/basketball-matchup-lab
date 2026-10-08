# Basketball Matchup Lab

Personal basketball research toolkit for EuroLeague, EuroCup, Basketball Champions League and Greek GBL.

Current milestone: EuroLeague/EuroCup ingestion, SQLite storage, pace/possessions analytics, matchup explorer, current/previous season support, filters, and opponent breakdowns by position.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.sync --season U2026
streamlit run app.py
```

Use `E2026` for EuroLeague 2026-27 and `U2026` for EuroCup 2026-27.

### Current + previous season in one run

```bash
python -m scripts.sync --season U2026 --season U2025
python -m scripts.sync --season E2026 --season E2025
```

For a small validation run:

```bash
python -m scripts.sync --season U2026 --season U2025 --max-games 2
```

## Current V1 scope

- Game-by-game team and player stats
- Points, rebounds, assists
- 2PT, 3PT and FT makes/attempts
- Blocks
- Fouls committed / received
- Turnovers, steals and minutes retained for future analysis
- Estimated possessions: `FGA - OREB + TO + 0.44 * FTA`
- Competition-relative fast / average / slow pace label
- Matchup comparison between two teams
- Player averages and opponent-allowed player tables
- Sample filters: All games / Last 5 / Last 10 / Home / Away
- Team allowed profile: PTS, REB, AST, shooting volume, FT, blocks, fouls and turnovers
- Opponent player breakdown: Guards / Forwards / Centers
- Multiple seasons can coexist in the same database without mixing by default

## Architecture

```text
sources/      source-specific ingestion adapters
scripts/      sync jobs
analytics/    matchup and pace calculations
db/           normalized SQLite schema
app.py        Streamlit UI
```

SQLite is intentionally used for local development and validation. Before unattended online scheduled sync is enabled, the persistence layer should move to a hosted database (for example Postgres) so the Streamlit process is not responsible for durable storage.

## Next milestone

1. Validate full 2025-26 EuroCup + EuroLeague backfill
2. Build Basketball Champions League adapter into the same normalized schema
3. Build Greek GBL adapter
4. Move persistence to hosted Postgres for unattended sync
5. Add play-by-play enrichment for possession timing where source quality supports it
