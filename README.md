# Basketball Matchup Lab

Personal basketball research toolkit for EuroLeague, EuroCup, Basketball Champions League and Greek GBL.

Current milestone: EuroLeague/EuroCup ingestion, SQLite storage, pace/possessions analytics, matchup explorer, and a lightweight Streamlit interface.

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

## Architecture

```text
sources/      source-specific ingestion adapters
scripts/      sync jobs
analytics/    matchup and pace calculations
db/           normalized SQLite schema
app.py        Streamlit UI
```

SQLite is intentionally used for local development and validation. Before unattended online scheduled sync is enabled, the persistence layer should move to a hosted database (for example Postgres) so the Streamlit process is not responsible for durable storage.

## Next adapters

1. Basketball Champions League
2. Greek GBL
3. Play-by-play enrichment for possession timing where the source quality supports it
