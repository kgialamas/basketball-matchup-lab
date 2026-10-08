from __future__ import annotations

import argparse
import json

from scripts.sync import connect, upsert
from sources.euroleague import season_games


def _num(value):
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def normalize_schedule_game(item: dict, season_code: str) -> dict:
    competition_code = season_code[0].upper()
    local = item.get("local", {}).get("club", {})
    road = item.get("road", {}).get("club", {})
    return {
        "source": "euroleague",
        "competition_code": competition_code,
        "season_code": season_code,
        "game_code": int(item["gameCode"]),
        "game_date": item.get("utcDate") or item.get("date"),
        "played": 1 if item.get("played") else 0,
        "home_team_code": local.get("code"),
        "home_team_name": local.get("name"),
        "away_team_code": road.get("code"),
        "away_team_name": road.get("name"),
        "home_score": _num(item.get("local", {}).get("score")),
        "away_score": _num(item.get("road", {}).get("score")),
        "raw_json": json.dumps(item, ensure_ascii=False),
    }


def sync_schedule(season_code: str) -> dict:
    competition_code = season_code[0].upper()
    items = season_games(competition_code, season_code)
    rows = [normalize_schedule_game(item, season_code) for item in items]
    conn = connect()
    try:
        upsert(conn, "games", rows)
        conn.commit()
    finally:
        conn.close()
    upcoming = sum(1 for row in rows if not row["played"])
    return {"season": season_code, "games": len(rows), "upcoming": upcoming}


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync full EuroLeague/EuroCup schedule into SQLite")
    parser.add_argument("--season", action="append", dest="seasons")
    args = parser.parse_args()
    for season in args.seasons or ["E2026", "U2026"]:
        print(sync_schedule(season.upper()))


if __name__ == "__main__":
    main()
