from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "basketball.db"

COMPETITION_NAMES = {
    "E": "EuroLeague",
    "U": "EuroCup",
    "GBL": "Greek Basket League",
}


def list_upcoming_games(season_code: str | None = None, competition_code: str | None = None) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()

    where = ["played = 0", "home_team_code IS NOT NULL", "away_team_code IS NOT NULL"]
    params: list[str] = []
    if season_code:
        where.append("season_code = ?")
        params.append(season_code)
    if competition_code:
        where.append("competition_code = ?")
        params.append(competition_code)

    sql = f"""
        SELECT source, competition_code, season_code, game_code, game_date,
               home_team_code, home_team_name, away_team_code, away_team_name
        FROM games
        WHERE {' AND '.join(where)}
        ORDER BY game_date ASC
    """
    with sqlite3.connect(DB_PATH) as conn:
        frame = pd.read_sql_query(sql, conn, params=params)

    if not frame.empty:
        frame["competition"] = frame["competition_code"].map(COMPETITION_NAMES).fillna(frame["competition_code"])
        frame["matchup"] = frame["home_team_name"] + " vs " + frame["away_team_name"]
    return frame
