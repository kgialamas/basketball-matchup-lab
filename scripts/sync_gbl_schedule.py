from __future__ import annotations

import argparse

from scripts.sync import connect, upsert
from sources.gbl_schedule import discover_team_schedule


def sync_gbl_schedule(team_id: str = "00000005", season_code: str = "G2026") -> dict:
    rows = discover_team_schedule(team_id=team_id, season_code=season_code)
    conn = connect()
    try:
        upsert(conn, "games", rows)
        conn.commit()
    finally:
        conn.close()
    return {
        "season": season_code,
        "games": len(rows),
        "upcoming": sum(1 for row in rows if not row["played"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync GBL schedule from official ESAKE team page")
    parser.add_argument("--team-id", default="00000005")
    parser.add_argument("--season", default="G2026")
    args = parser.parse_args()
    print(sync_gbl_schedule(args.team_id, args.season))


if __name__ == "__main__":
    main()
