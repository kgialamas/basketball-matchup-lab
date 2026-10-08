from __future__ import annotations

import argparse

from scripts.sync import connect, upsert
from sources.gbl import discover_games, parse_game, team_games_from_team_page


def sync_gbl(season_code: str = "G2026", max_games: int | None = None, aris_only: bool = False) -> dict:
    game_ids = team_games_from_team_page() if aris_only else discover_games()
    if max_games:
        game_ids = game_ids[:max_games]

    totals = {"season": season_code, "games": 0, "team_rows": 0, "player_rows": 0, "errors": []}
    conn = connect()
    try:
        for game_id in game_ids:
            try:
                game_row, teams, players = parse_game(game_id, season_code=season_code)
                if not game_row.get("played"):
                    continue
                upsert(conn, "games", [game_row])
                upsert(conn, "team_games", teams)
                upsert(conn, "player_games", players)
                conn.commit()
                totals["games"] += 1
                totals["team_rows"] += len(teams)
                totals["player_rows"] += len(players)
                print(f"Synced GBL {game_id}: {game_row['home_team_name']} {game_row['home_score']} - {game_row['away_score']} {game_row['away_team_name']}")
            except Exception as exc:
                conn.rollback()
                totals["errors"].append({"game_id": game_id, "error": str(exc)})
                print(f"ERROR GBL {game_id}: {exc}")
    finally:
        conn.close()
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync official ESAKE/GBL box scores into SQLite")
    parser.add_argument("--season", default="G2026", help="Internal season code, e.g. G2026")
    parser.add_argument("--max-games", type=int, default=None)
    parser.add_argument("--aris-only", action="store_true", help="Discover games from the Aris team page only")
    args = parser.parse_args()
    result = sync_gbl(args.season, args.max_games, args.aris_only)
    print(result)


if __name__ == "__main__":
    main()
