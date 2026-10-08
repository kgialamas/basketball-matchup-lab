from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from pipeline.lineups import reconstruct_eurocup_stints, validate_stints
from sources.eurocup_pbp import aris_box, fetch_game, starters
from sources.euroleague import game, season_games

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DEFAULT_OUT = DATA_DIR / "aris_2026_27.json"
ARIS_CODE = "ARI"


def _club_code(side: dict) -> str:
    return str(side.get("club", {}).get("code") or "").strip().upper()


def _club_name(side: dict) -> str:
    return str(side.get("club", {}).get("name") or "").strip()


def _score(side: dict) -> int:
    value = side.get("score")
    return int(float(value or 0))


def sync_eurocup(season_code: str = "U2026") -> dict:
    competition_code = season_code[0].upper()
    schedule = season_games(competition_code, season_code)
    aris_games = []

    for item in schedule:
        if not item.get("played"):
            continue
        local_code = _club_code(item.get("local", {}))
        road_code = _club_code(item.get("road", {}))
        if ARIS_CODE not in {local_code, road_code}:
            continue

        code = int(item["gameCode"])
        header = game(competition_code, season_code, code)
        events, teams = fetch_game(season_code, code)
        team = aris_box(teams)
        starting_five = starters(team)
        aris_idx = next(i for i, t in enumerate(teams) if t is team)
        aris_is_team_a = aris_idx == 0

        local = header.get("local", {})
        road = header.get("road", {})
        home_is_aris = _club_code(local) == ARIS_CODE
        aris_score = _score(local if home_is_aris else road)
        opp_score = _score(road if home_is_aris else local)
        opponent = _club_name(road if home_is_aris else local)

        stints = reconstruct_eurocup_stints(
            events,
            starting_five,
            aris_is_team_a=aris_is_team_a,
            aris_code=ARIS_CODE,
        )
        validation = validate_stints(stints, expected_margin=aris_score - opp_score)
        if not validation["ok"]:
            raise RuntimeError(f"Validation failed for {season_code}/{code}: {validation}")

        aris_games.append(
            {
                "competition": "EuroCup",
                "season_code": season_code,
                "game_code": code,
                "game_date": header.get("utcDate") or header.get("date"),
                "venue": "home" if home_is_aris else "away",
                "opponent": opponent,
                "aris_score": aris_score,
                "opponent_score": opp_score,
                "starters": starting_five,
                "validation": validation,
                "stints": [s.as_dict() for s in stints],
            }
        )

    aris_games.sort(key=lambda x: x.get("game_date") or "")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "team": "ARIS Thessaloniki",
        "season": "2026-27",
        "competitions": ["EuroCup"],
        "games": aris_games,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build validated ARIS lineup dataset from official sources")
    parser.add_argument("--season", default="U2026")
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    snapshot = sync_eurocup(args.season.upper())
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "games": len(snapshot["games"]),
        "output": str(out),
        "validated": all(g["validation"]["ok"] for g in snapshot["games"]),
    }))


if __name__ == "__main__":
    main()
