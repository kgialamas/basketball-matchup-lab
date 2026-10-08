from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Iterable

from sources.euroleague import game, game_stats, normalize, season_games

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "basketball.db"
SCHEMA_PATH = ROOT / "db" / "schema.sql"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn


def upsert(conn: sqlite3.Connection, table: str, rows: Iterable[dict]) -> int:
    rows = list(rows)
    if not rows:
        return 0
    cols = list(rows[0].keys())
    placeholders = ",".join("?" for _ in cols)
    updates = ",".join(f"{c}=excluded.{c}" for c in cols if c not in {"source", "season_code", "game_code", "team_code", "player_code"})
    conflict = {
        "games": "source,season_code,game_code",
        "team_games": "source,season_code,game_code,team_code",
        "player_games": "source,season_code,game_code,player_code",
    }[table]
    sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders}) ON CONFLICT({conflict}) DO UPDATE SET {updates}"
    conn.executemany(sql, [[row.get(c) for c in cols] for row in rows])
    return len(rows)


def sync_season(season_code: str, max_games: int | None = None) -> dict:
    competition_code = season_code[0].upper()
    games = [g for g in season_games(competition_code, season_code) if g.get("played")]
    games.sort(key=lambda g: g.get("utcDate") or g.get("date") or "")
    if max_games:
        games = games[-max_games:]

    totals = {"season": season_code, "games": 0, "team_rows": 0, "player_rows": 0, "errors": []}
    conn = connect()
    try:
        for item in games:
            code = int(item["gameCode"])
            try:
                header = game(competition_code, season_code, code)
                stats = game_stats(competition_code, season_code, code)
                game_row, teams, players = normalize(header, stats)
                upsert(conn, "games", [game_row])
                upsert(conn, "team_games", teams)
                upsert(conn, "player_games", players)
                conn.commit()
                totals["games"] += 1
                totals["team_rows"] += len(teams)
                totals["player_rows"] += len(players)
                print(f"Synced {season_code} game {code}: {game_row['home_team_name']} vs {game_row['away_team_name']}")
            except Exception as exc:
                conn.rollback()
                totals["errors"].append({"game_code": code, "error": str(exc)})
                print(f"ERROR {season_code} game {code}: {exc}")
    finally:
        conn.close()
    return totals


def sync_many(seasons: list[str], max_games: int | None = None) -> list[dict]:
    results = []
    for season in seasons:
        results.append(sync_season(season.upper(), max_games))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync EuroLeague/EuroCup season data into SQLite")
    parser.add_argument("--season", action="append", dest="seasons", help="Season code; repeat flag for multiple seasons, e.g. --season U2026 --season U2025")
    parser.add_argument("--max-games", type=int, default=None)
    args = parser.parse_args()
    seasons = [s.upper() for s in (args.seasons or ["U2026"])]
    for result in sync_many(seasons, args.max_games):
        print(result)


if __name__ == "__main__":
    main()
