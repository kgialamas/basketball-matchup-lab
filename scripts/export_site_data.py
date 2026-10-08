from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "basketball.db"
OUT_PATH = ROOT / "docs" / "data" / "site-data.json"

SEASON_LABELS = {
    "E2026": "2026-27",
    "U2026": "2026-27",
    "E2025": "2025-26",
    "U2025": "2025-26",
    "E2024": "2024-25",
    "U2024": "2024-25",
}
COMP_LABELS = {"E": "EuroLeague", "U": "EuroCup"}


def pct(made: float, att: float) -> float:
    return round((made / att * 100.0), 1) if att else 0.0


def mmss(decimal_minutes: float | None) -> str:
    total_seconds = int(round((decimal_minutes or 0) * 60))
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


def r1(value: float | None) -> float:
    return round(float(value or 0), 1)


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    seasons = [
        row["season_code"]
        for row in conn.execute(
            "SELECT DISTINCT season_code FROM team_games WHERE source='euroleague' ORDER BY season_code DESC"
        )
    ]

    payload = {"generated_from": "official EuroLeague Basketball live API", "seasons": []}

    for season_code in seasons:
        competition_code = season_code[0]
        teams = conn.execute(
            """
            SELECT
              team_code,
              MAX(team_name) AS team_name,
              COUNT(*) AS gp,
              AVG(points) AS pts,
              AVG(opponent_points) AS opp,
              AVG(rebounds) AS reb,
              AVG(offensive_rebounds) AS oreb,
              AVG(defensive_rebounds) AS dreb,
              AVG(assists) AS ast,
              AVG(steals) AS stl,
              AVG(turnovers) AS tov,
              AVG(blocks) AS blk,
              AVG(fouls_committed) AS fc,
              AVG(fouls_received) AS fd,
              AVG(valuation) AS pir,
              AVG(possessions_est) AS poss,
              SUM(fg2m) AS fg2m, SUM(fg2a) AS fg2a,
              SUM(fg3m) AS fg3m, SUM(fg3a) AS fg3a,
              SUM(ftm) AS ftm, SUM(fta) AS fta
            FROM team_games
            WHERE source='euroleague' AND season_code=?
            GROUP BY team_code
            ORDER BY team_name
            """,
            (season_code,),
        ).fetchall()

        season_obj = {
            "competition": COMP_LABELS.get(competition_code, competition_code),
            "competition_code": competition_code,
            "season": SEASON_LABELS.get(season_code, season_code),
            "season_code": season_code,
            "teams": [],
        }

        for t in teams:
            players = conn.execute(
                """
                SELECT
                  player_code,
                  MAX(player_name) AS player_name,
                  MAX(position_name) AS position_name,
                  COUNT(*) AS gp,
                  SUM(CASE WHEN starter=1 THEN 1 ELSE 0 END) AS gs,
                  AVG(minutes) AS min,
                  AVG(points) AS pts,
                  AVG(rebounds) AS reb,
                  AVG(offensive_rebounds) AS oreb,
                  AVG(defensive_rebounds) AS dreb,
                  AVG(assists) AS ast,
                  AVG(steals) AS stl,
                  AVG(turnovers) AS tov,
                  AVG(blocks) AS blk,
                  AVG(fouls_committed) AS fc,
                  AVG(fouls_received) AS fd,
                  AVG(plus_minus) AS plus_minus,
                  AVG(valuation) AS pir,
                  SUM(fg2m) AS fg2m, SUM(fg2a) AS fg2a,
                  SUM(fg3m) AS fg3m, SUM(fg3a) AS fg3a,
                  SUM(ftm) AS ftm, SUM(fta) AS fta
                FROM player_games
                WHERE source='euroleague' AND season_code=? AND team_code=?
                GROUP BY player_code
                ORDER BY AVG(minutes) DESC, AVG(points) DESC
                """,
                (season_code, t["team_code"]),
            ).fetchall()

            player_items = []
            for p in players:
                fg2m, fg2a = int(p["fg2m"] or 0), int(p["fg2a"] or 0)
                fg3m, fg3a = int(p["fg3m"] or 0), int(p["fg3a"] or 0)
                ftm, fta = int(p["ftm"] or 0), int(p["fta"] or 0)
                player_items.append({
                    "code": p["player_code"],
                    "name": p["player_name"],
                    "pos": p["position_name"] or "—",
                    "gp": int(p["gp"] or 0),
                    "gs": int(p["gs"] or 0),
                    "min": mmss(p["min"]),
                    "pts": r1(p["pts"]),
                    "oreb": r1(p["oreb"]),
                    "dreb": r1(p["dreb"]),
                    "reb": r1(p["reb"]),
                    "ast": r1(p["ast"]),
                    "stl": r1(p["stl"]),
                    "tov": r1(p["tov"]),
                    "blk": r1(p["blk"]),
                    "fc": r1(p["fc"]),
                    "fd": r1(p["fd"]),
                    "plus_minus": r1(p["plus_minus"]),
                    "pir": r1(p["pir"]),
                    "fg2": f"{fg2m}/{fg2a}", "fg2pct": pct(fg2m, fg2a),
                    "fg3": f"{fg3m}/{fg3a}", "fg3pct": pct(fg3m, fg3a),
                    "ft": f"{ftm}/{fta}", "ftpct": pct(ftm, fta),
                })

            fg2m, fg2a = int(t["fg2m"] or 0), int(t["fg2a"] or 0)
            fg3m, fg3a = int(t["fg3m"] or 0), int(t["fg3a"] or 0)
            ftm, fta = int(t["ftm"] or 0), int(t["fta"] or 0)
            season_obj["teams"].append({
                "code": t["team_code"],
                "name": t["team_name"],
                "summary": {
                    "gp": int(t["gp"] or 0), "pts": r1(t["pts"]), "opp": r1(t["opp"]),
                    "reb": r1(t["reb"]), "oreb": r1(t["oreb"]), "dreb": r1(t["dreb"]),
                    "ast": r1(t["ast"]), "stl": r1(t["stl"]), "tov": r1(t["tov"]),
                    "blk": r1(t["blk"]), "fc": r1(t["fc"]), "fd": r1(t["fd"]),
                    "pir": r1(t["pir"]), "poss": r1(t["poss"]),
                    "fg2": f"{fg2m}/{fg2a}", "fg2pct": pct(fg2m, fg2a),
                    "fg3": f"{fg3m}/{fg3a}", "fg3pct": pct(fg3m, fg3a),
                    "ft": f"{ftm}/{fta}", "ftpct": pct(ftm, fta),
                },
                "players": player_items,
            })

        payload["seasons"].append(season_obj)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    for s in payload["seasons"]:
        players = sum(len(t["players"]) for t in s["teams"])
        print(f"{s['competition']} {s['season']}: {len(s['teams'])} teams, {players} player-team rows")

    conn.close()


if __name__ == "__main__":
    main()
