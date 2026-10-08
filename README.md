# Basketball Matchup Lab

Personal basketball research toolkit for EuroLeague, EuroCup, Basketball Champions League and Greek GBL.

The repo now has two layers:

1. The original general matchup toolkit (boxscores, team/player stats, pace estimates, Streamlit UI).
2. A dedicated ARIS 2026-27 play-by-play pipeline that reconstructs five-man lineups and produces ON/OFF, pair and lineup analytics.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# General EuroCup/EuroLeague dataset
python -m scripts.sync --season U2026

# ARIS-only validated lineup dataset (EuroCup + GBL)
python -m scripts.sync_aris --season U2026

# Optional UI
streamlit run app.py
```

The ARIS snapshot is written to `data/aris_2026_27.json`.

## ARIS pipeline

### Sources

- EuroCup: official EuroLeague live JSON play-by-play + boxscore feeds.
- GBL: ESAKE game pages, using the embedded Genius/BasketHotel play-by-play rows.

### Validation gates

A game is accepted only when the reconstructed data passes the checks available for that source, including:

- exactly five ARIS players in every stint;
- 40:00 regulation duration (plus overtime where applicable);
- reconstructed scoring margin equals the official final margin;
- substitution groups do not create impossible lineups;
- starter inference must resolve cleanly.

Bad/uncertain scrapes are rejected or listed under `errors`; they are not silently included in analytics.

### Analytics generated

- player ON vs OFF minutes and +/- per 40;
- ON/OFF swing;
- two-player shared-minute combinations;
- five-man lineup performance;
- points for / against per 40 as an interim pace-normalized view.

Possession-level ORtg/DRtg and Four Factors are the next analytical layer; they should only be added once possession boundaries are reconstructed reliably from play-by-play.

## Automation

`.github/workflows/aris-refresh.yml` runs every day and can also be triggered manually from GitHub Actions. It rebuilds the season snapshot, validates it, and commits `data/aris_2026_27.json` only when the underlying dataset has actually changed.

## Existing general architecture

```text
sources/      source-specific ingestion adapters
pipeline/     play-by-play normalization / lineup reconstruction
scripts/      sync jobs
analytics/    matchup, pace and lineup calculations
data/         generated ARIS season snapshot
db/           normalized SQLite schema for the general toolkit
app.py        Streamlit UI
```
