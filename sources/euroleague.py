from __future__ import annotations

import json
from typing import Any

import requests

BASE = "https://api-live.euroleague.net/v2"


def _get_json(url: str) -> dict[str, Any]:
    r = requests.get(url, headers={"accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()


def season_games(competition_code: str, season_code: str) -> list[dict[str, Any]]:
    data = _get_json(f"{BASE}/competitions/{competition_code}/seasons/{season_code}/games")
    return data.get("data", [])


def game(competition_code: str, season_code: str, game_code: int) -> dict[str, Any]:
    return _get_json(f"{BASE}/competitions/{competition_code}/seasons/{season_code}/games/{game_code}")


def game_stats(competition_code: str, season_code: str, game_code: int) -> dict[str, Any]:
    return _get_json(f"{BASE}/competitions/{competition_code}/seasons/{season_code}/games/{game_code}/stats")


def _num(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stat(stats: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        if key in stats:
            return _num(stats.get(key))
    return None


def normalize(header: dict[str, Any], stats: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    local = header.get("local", {}).get("club", {})
    road = header.get("road", {}).get("club", {})
    season = header.get("season", {})
    season_code = season.get("code")
    competition_code = season.get("competitionCode") or (season_code[0] if season_code else None)
    base = {
        "source": "euroleague",
        "competition_code": competition_code,
        "season_code": season_code,
        "game_code": int(header["gameCode"]),
        "game_date": header.get("utcDate") or header.get("date"),
        "played": 1 if header.get("played") else 0,
        "home_team_code": local.get("code"),
        "home_team_name": local.get("name"),
        "away_team_code": road.get("code"),
        "away_team_name": road.get("name"),
        "home_score": _num(header.get("local", {}).get("score")),
        "away_score": _num(header.get("road", {}).get("score")),
        "raw_json": json.dumps(header, ensure_ascii=False),
    }

    team_rows: list[dict[str, Any]] = []
    player_rows: list[dict[str, Any]] = []

    for home_away, side_key, opp_key in (("home", "local", "road"), ("away", "road", "local")):
        side = stats.get(side_key, {})
        opp = stats.get(opp_key, {})
        team = header.get(side_key, {}).get("club", {})
        opponent = header.get(opp_key, {}).get("club", {})
        ts = side.get("total", {}).get("stats") or side.get("total") or {}

        fg2a = _stat(ts, "fieldGoalsAttempted2") or 0
        fg3a = _stat(ts, "fieldGoalsAttempted3") or 0
        fga = fg2a + fg3a
        oreb = _stat(ts, "offensiveRebounds") or 0
        tov = _stat(ts, "turnovers") or 0
        fta = _stat(ts, "freeThrowsAttempted") or 0
        possessions = fga - oreb + tov + 0.44 * fta

        team_rows.append({
            "source": "euroleague",
            "competition_code": competition_code,
            "season_code": season_code,
            "game_code": base["game_code"],
            "game_date": base["game_date"],
            "team_code": team.get("code"),
            "team_name": team.get("name"),
            "opponent_code": opponent.get("code"),
            "opponent_name": opponent.get("name"),
            "home_away": home_away,
            "points": base["home_score"] if home_away == "home" else base["away_score"],
            "opponent_points": base["away_score"] if home_away == "home" else base["home_score"],
            "rebounds": _stat(ts, "totalRebounds"),
            "offensive_rebounds": _stat(ts, "offensiveRebounds"),
            "defensive_rebounds": _stat(ts, "defensiveRebounds"),
            "assists": _stat(ts, "assistances", "assists"),
            "steals": _stat(ts, "steals"),
            "turnovers": _stat(ts, "turnovers"),
            "blocks": _stat(ts, "blocksFavour", "blocks"),
            "fouls_committed": _stat(ts, "foulsCommited", "foulsCommitted"),
            "fouls_received": _stat(ts, "foulsReceived"),
            "fg2m": _stat(ts, "fieldGoalsMade2"),
            "fg2a": _stat(ts, "fieldGoalsAttempted2"),
            "fg3m": _stat(ts, "fieldGoalsMade3"),
            "fg3a": _stat(ts, "fieldGoalsAttempted3"),
            "ftm": _stat(ts, "freeThrowsMade"),
            "fta": _stat(ts, "freeThrowsAttempted"),
            "valuation": _stat(ts, "valuation"),
            "possessions_est": possessions,
            "raw_json": json.dumps(side, ensure_ascii=False),
        })

        for row in side.get("players", []):
            p = row.get("player", {})
            person = p.get("person", {})
            st = row.get("stats", {})
            player_rows.append({
                "source": "euroleague",
                "competition_code": competition_code,
                "season_code": season_code,
                "game_code": base["game_code"],
                "game_date": base["game_date"],
                "team_code": team.get("code") or p.get("club", {}).get("code"),
                "team_name": team.get("name") or p.get("club", {}).get("name"),
                "opponent_code": opponent.get("code"),
                "opponent_name": opponent.get("name"),
                "home_away": home_away,
                "team_score": base["home_score"] if home_away == "home" else base["away_score"],
                "opponent_score": base["away_score"] if home_away == "home" else base["home_score"],
                "player_code": person.get("code"),
                "player_name": person.get("name") or person.get("alias") or p.get("name"),
                "position_name": p.get("positionName"),
                "starter": 1 if st.get("startFive") else 0,
                "minutes": (_num(st.get("timePlayed")) or 0) / 60,
                "points": _stat(st, "points"),
                "rebounds": _stat(st, "totalRebounds"),
                "offensive_rebounds": _stat(st, "offensiveRebounds"),
                "defensive_rebounds": _stat(st, "defensiveRebounds"),
                "assists": _stat(st, "assistances", "assists"),
                "steals": _stat(st, "steals"),
                "turnovers": _stat(st, "turnovers"),
                "blocks": _stat(st, "blocksFavour", "blocks"),
                "fouls_committed": _stat(st, "foulsCommited", "foulsCommitted"),
                "fouls_received": _stat(st, "foulsReceived"),
                "plus_minus": _stat(st, "plusMinus"),
                "fg2m": _stat(st, "fieldGoalsMade2"),
                "fg2a": _stat(st, "fieldGoalsAttempted2"),
                "fg3m": _stat(st, "fieldGoalsMade3"),
                "fg3a": _stat(st, "fieldGoalsAttempted3"),
                "ftm": _stat(st, "freeThrowsMade"),
                "fta": _stat(st, "freeThrowsAttempted"),
                "valuation": _stat(st, "valuation"),
                "raw_json": json.dumps(row, ensure_ascii=False),
            })

    return base, team_rows, [r for r in player_rows if r.get("player_code")]
