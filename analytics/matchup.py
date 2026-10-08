from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "basketball.db"

TEAM_METRICS = [
    "points", "rebounds", "offensive_rebounds", "defensive_rebounds", "assists", "steals",
    "fg2m", "fg2a", "fg3m", "fg3a", "ftm", "fta", "blocks", "fouls_committed",
    "fouls_received", "turnovers", "valuation", "possessions_est", "opponent_points",
]

PLAYER_METRICS = [
    "minutes", "points", "rebounds", "offensive_rebounds", "defensive_rebounds", "assists",
    "steals", "turnovers", "blocks", "fouls_committed", "fouls_received", "plus_minus",
    "fg2m", "fg2a", "fg3m", "fg3a", "ftm", "fta", "valuation",
]

ALLOWED_TEAM_METRICS = [
    "points", "rebounds", "assists", "fg2m", "fg2a", "fg3m", "fg3a",
    "ftm", "fta", "blocks", "fouls_committed", "fouls_received", "turnovers",
]


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _avg_dict(df: pd.DataFrame, cols: list[str]) -> dict:
    return {c: float(df[c].mean()) if c in df and not df[c].dropna().empty else None for c in cols}


def _sum_dict(df: pd.DataFrame, cols: list[str]) -> dict:
    return {c: float(df[c].sum()) if c in df and not df[c].dropna().empty else None for c in cols}


def _pace_label(value: float | None, league_avg: float | None) -> str:
    if value is None or league_avg in (None, 0):
        return "unknown"
    ratio = value / league_avg
    if ratio > 1.05:
        return "fast"
    if ratio < 0.95:
        return "slow"
    return "average"


def _position_group(value: str | None) -> str:
    text = (value or "").strip().lower()
    if text in {"g", "pg", "sg"} or "guard" in text:
        return "Guards"
    if text in {"c"} or "center" in text:
        return "Centers"
    if text in {"f", "sf", "pf"} or "forward" in text:
        return "Forwards"
    return "Other"


def _apply_team_filter(df: pd.DataFrame, filter_mode: str) -> pd.DataFrame:
    out = df.sort_values("game_date", ascending=False).copy()
    if filter_mode == "Last 5":
        return out.head(5)
    if filter_mode == "Last 10":
        return out.head(10)
    if filter_mode == "Home":
        return out[out.home_away == "home"]
    if filter_mode == "Away":
        return out[out.home_away == "away"]
    return out


def _filter_player_rows(players: pd.DataFrame, selected_games: pd.DataFrame) -> pd.DataFrame:
    if players.empty or selected_games.empty:
        return players.iloc[0:0].copy()
    keys = selected_games[["source", "season_code", "game_code"]].drop_duplicates()
    return players.merge(keys, on=["source", "season_code", "game_code"], how="inner")


def list_teams(season_code: str) -> pd.DataFrame:
    with _conn() as conn:
        return pd.read_sql_query(
            "SELECT team_code, MAX(team_name) team_name, COUNT(*) games FROM team_games WHERE season_code=? GROUP BY team_code ORDER BY team_name",
            conn,
            params=[season_code],
        )


def list_players(season_code: str) -> pd.DataFrame:
    with _conn() as conn:
        return pd.read_sql_query(
            """
            SELECT player_code, MAX(player_name) player_name, MAX(team_code) team_code,
                   MAX(team_name) team_name, MAX(position_name) position_name, COUNT(*) games
            FROM player_games
            WHERE season_code=?
            GROUP BY player_code
            ORDER BY player_name
            """,
            conn,
            params=[season_code],
        )


def list_seasons() -> pd.DataFrame:
    with _conn() as conn:
        return pd.read_sql_query(
            "SELECT season_code, competition_code, COUNT(DISTINCT game_code) games, MIN(game_date) first_game, MAX(game_date) last_game FROM games GROUP BY season_code, competition_code ORDER BY season_code DESC",
            conn,
        )


def _player_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["player_code", "player_name", "position_name", "games", "starts", *PLAYER_METRICS])

    keys = ["player_code", "player_name", "position_name"]
    avg = df.groupby(keys, dropna=False)[PLAYER_METRICS].mean(numeric_only=True).reset_index()
    counts = df.groupby(keys, dropna=False).agg(games=("game_code", "nunique"), starts=("starter", "sum")).reset_index()
    out = counts.merge(avg, on=keys, how="left")
    return out.sort_values(["minutes", "points"], ascending=False)


def build_team_profile(team_code: str, season_code: str, filter_mode: str = "All games") -> dict:
    with _conn() as conn:
        team_games = pd.read_sql_query("SELECT * FROM team_games WHERE season_code=? AND team_code=?", conn, params=[season_code, team_code])
        players = pd.read_sql_query("SELECT * FROM player_games WHERE season_code=? AND team_code=?", conn, params=[season_code, team_code])
        league = pd.read_sql_query("SELECT possessions_est FROM team_games WHERE season_code=?", conn, params=[season_code])

    if team_games.empty:
        raise ValueError(f"Team {team_code} not found in {season_code}")

    selected = _apply_team_filter(team_games, filter_mode)
    selected_players = _filter_player_rows(players, selected)
    league_pace = float(league["possessions_est"].mean()) if not league.empty else None
    averages = _avg_dict(selected, TEAM_METRICS)
    totals = _sum_dict(selected, TEAM_METRICS)
    averages["games"] = int(len(selected))
    averages["pace_label"] = _pace_label(averages.get("possessions_est"), league_pace)

    return {
        "code": team_code,
        "name": team_games.iloc[0]["team_name"],
        "season_code": season_code,
        "filter_mode": filter_mode,
        "averages": averages,
        "totals": totals,
        "roster": _player_summary(selected_players),
        "games": selected.sort_values("game_date", ascending=False),
        "league_pace": league_pace,
    }


def build_player_profile(player_code: str, season_code: str, filter_mode: str = "All games") -> dict:
    with _conn() as conn:
        rows = pd.read_sql_query("SELECT * FROM player_games WHERE season_code=? AND player_code=?", conn, params=[season_code, player_code])
        team_games = pd.read_sql_query("SELECT * FROM team_games WHERE season_code=?", conn, params=[season_code])

    if rows.empty:
        raise ValueError(f"Player {player_code} not found in {season_code}")

    team_code = rows.iloc[-1]["team_code"]
    tg = team_games[team_games.team_code == team_code].copy()
    selected_games = _apply_team_filter(tg, filter_mode)
    selected = _filter_player_rows(rows, selected_games)
    summary = _player_summary(selected)
    season_line = summary.iloc[0].to_dict() if not summary.empty else {}

    return {
        "player_code": player_code,
        "player_name": rows.iloc[0]["player_name"],
        "team_code": team_code,
        "team_name": rows.iloc[0]["team_name"],
        "position_name": rows.iloc[0]["position_name"],
        "season_code": season_code,
        "filter_mode": filter_mode,
        "summary": season_line,
        "game_log": selected.sort_values("game_date", ascending=False),
    }


def build_matchup(team_a: str, team_b: str, season_code: str, filter_mode: str = "All games") -> dict:
    with _conn() as conn:
        teams = pd.read_sql_query("SELECT * FROM team_games WHERE season_code=?", conn, params=[season_code])
        players = pd.read_sql_query("SELECT * FROM player_games WHERE season_code=?", conn, params=[season_code])

    if teams.empty:
        raise ValueError(f"No data for season {season_code}")

    league_pace = float(teams["possessions_est"].mean()) if "possessions_est" in teams else None

    def one_team(code: str) -> dict:
        tg_all = teams[teams.team_code == code].copy()
        if tg_all.empty:
            raise ValueError(f"Team {code} not found in {season_code}")

        tg = _apply_team_filter(tg_all, filter_mode)
        own_players_all = players[players.team_code == code].copy()
        opp_players_all = players[players.opponent_code == code].copy()
        own_players = _filter_player_rows(own_players_all, tg)

        if tg.empty:
            opp_players = opp_players_all.iloc[0:0].copy()
        else:
            game_codes = set(tg.game_code.tolist())
            opp_players = opp_players_all[opp_players_all.game_code.isin(game_codes)].copy()

        summary = _avg_dict(tg, TEAM_METRICS)
        summary["games"] = int(len(tg))
        summary["pace_label"] = _pace_label(summary.get("possessions_est"), league_pace)

        opp_team_rows = teams[(teams.opponent_code == code) & (teams.game_code.isin(tg.game_code.tolist()))].copy()
        allowed = _avg_dict(opp_team_rows, ALLOWED_TEAM_METRICS)
        allowed["games"] = int(len(opp_team_rows))

        opponent_summary = _player_summary(opp_players)
        if not opponent_summary.empty:
            opponent_summary["position_group"] = opponent_summary["position_name"].map(_position_group)

        position_splits = {}
        if not opponent_summary.empty:
            for group in ["Guards", "Forwards", "Centers", "Other"]:
                subset = opponent_summary[opponent_summary.position_group == group].copy()
                if not subset.empty:
                    position_splits[group] = subset

        return {
            "code": code,
            "name": tg_all.iloc[0]["team_name"],
            "summary": summary,
            "allowed": allowed,
            "players": _player_summary(own_players),
            "opponents": opponent_summary,
            "opponents_by_position": position_splits,
            "games": tg.sort_values("game_date", ascending=False),
        }

    return {
        "season_code": season_code,
        "filter_mode": filter_mode,
        "league_pace": league_pace,
        "team_a": one_team(team_a),
        "team_b": one_team(team_b),
    }
