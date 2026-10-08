from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "basketball.db"

TEAM_METRICS = [
    "points", "rebounds", "assists", "fg2m", "fg2a", "fg3m", "fg3a",
    "ftm", "fta", "blocks", "fouls_committed", "fouls_received",
    "turnovers", "possessions_est", "opponent_points",
]

PLAYER_METRICS = [
    "minutes", "points", "rebounds", "assists", "fg2m", "fg2a", "fg3m", "fg3a",
    "ftm", "fta", "blocks", "fouls_committed", "fouls_received", "turnovers",
]


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _avg_dict(df: pd.DataFrame, cols: list[str]) -> dict:
    return {c: float(df[c].mean()) if c in df and not df[c].dropna().empty else None for c in cols}


def _pace_label(value: float | None, league_avg: float | None) -> str:
    if value is None or league_avg in (None, 0):
        return "unknown"
    ratio = value / league_avg
    if ratio > 1.05:
        return "fast"
    if ratio < 0.95:
        return "slow"
    return "average"


def list_teams(season_code: str) -> pd.DataFrame:
    with _conn() as conn:
        return pd.read_sql_query(
            "SELECT team_code, MAX(team_name) team_name, COUNT(*) games FROM team_games WHERE season_code=? GROUP BY team_code ORDER BY team_name",
            conn,
            params=[season_code],
        )


def list_seasons() -> pd.DataFrame:
    with _conn() as conn:
        return pd.read_sql_query(
            "SELECT season_code, competition_code, COUNT(DISTINCT game_code) games, MIN(game_date) first_game, MAX(game_date) last_game FROM games GROUP BY season_code, competition_code ORDER BY season_code DESC",
            conn,
        )


def build_matchup(team_a: str, team_b: str, season_code: str) -> dict:
    with _conn() as conn:
        teams = pd.read_sql_query("SELECT * FROM team_games WHERE season_code=?", conn, params=[season_code])
        players = pd.read_sql_query("SELECT * FROM player_games WHERE season_code=?", conn, params=[season_code])

    if teams.empty:
        raise ValueError(f"No data for season {season_code}")

    league_pace = float(teams["possessions_est"].mean()) if "possessions_est" in teams else None

    def one_team(code: str) -> dict:
        tg = teams[teams.team_code == code].copy()
        if tg.empty:
            raise ValueError(f"Team {code} not found in {season_code}")
        own_players = players[players.team_code == code].copy()
        opp_players = players[players.opponent_code == code].copy()
        summary = _avg_dict(tg, TEAM_METRICS)
        summary["games"] = int(len(tg))
        summary["pace_label"] = _pace_label(summary.get("possessions_est"), league_pace)

        player_summary = (
            own_players.groupby(["player_code", "player_name", "position_name"], dropna=False)[PLAYER_METRICS]
            .mean(numeric_only=True)
            .reset_index()
            .sort_values(["minutes", "points"], ascending=False)
        )
        opponent_summary = (
            opp_players.groupby(["player_code", "player_name", "position_name"], dropna=False)[PLAYER_METRICS]
            .mean(numeric_only=True)
            .reset_index()
            .sort_values(["minutes", "points"], ascending=False)
        )

        return {
            "code": code,
            "name": tg.iloc[0]["team_name"],
            "summary": summary,
            "players": player_summary,
            "opponents": opponent_summary,
            "games": tg.sort_values("game_date", ascending=False),
        }

    return {
        "season_code": season_code,
        "league_pace": league_pace,
        "team_a": one_team(team_a),
        "team_b": one_team(team_b),
    }
