from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from pipeline.lineups import reconstruct_eurocup_stints, reconstruct_gbl_stints, validate_stints
from sources.eurocup_pbp import aris_box, fetch_game, starters
from sources.euroleague import game, season_games
from sources.gbl import discover_aris_game_ids, parse_game

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DEFAULT_OUT = DATA_DIR / "aris_2026_27.json"
ARIS_CODE = "ARI"


def _club_code(side: dict) -> str:
    return str(side.get("club", {}).get("code") or "").strip().upper()


def _club_name(side: dict) -> str:
    return str(side.get("club", {}).get("name") or "").strip()


def _score(side: dict) -> int:
    return int(float(side.get("score") or 0))


def sync_eurocup(season_code: str = "U2026") -> list[dict]:
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

        local = header.get("local", {})
        road = header.get("road", {})
        home_is_aris = _club_code(local) == ARIS_CODE
        aris_score = _score(local if home_is_aris else road)
        opp_score = _score(road if home_is_aris else local)
        opponent = _club_name(road if home_is_aris else local)

        stints = reconstruct_eurocup_stints(
            events,
            starting_five,
            aris_is_team_a=aris_idx == 0,
            aris_code=ARIS_CODE,
        )
        validation = validate_stints(stints, expected_margin=aris_score - opp_score)
        if not validation["ok"]:
            raise RuntimeError(f"EuroCup validation failed for {season_code}/{code}: {validation}")

        aris_games.append({
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
        })

    return aris_games


def sync_gbl() -> tuple[list[dict], list[dict]]:
    games = []
    errors = []
    for game_id in discover_aris_game_ids():
        try:
            parsed = parse_game(game_id)
            aris_index = int(parsed["aris_index"])
            score_a, score_b = int(parsed["score_a"]), int(parsed["score_b"])
            aris_score, opp_score = (score_a, score_b) if aris_index == 0 else (score_b, score_a)
            opponent = parsed["team_b"] if aris_index == 0 else parsed["team_a"]
            stints = reconstruct_gbl_stints(parsed)
            validation = validate_stints(stints, expected_margin=aris_score - opp_score)
            if not validation["ok"]:
                raise RuntimeError(f"validation failed: {validation}")
            games.append({
                "competition": "GBL",
                "season_code": "GBL2026",
                "game_code": game_id,
                "game_date": None,
                "venue": "home" if aris_index == 0 else "away",
                "opponent": opponent,
                "aris_score": aris_score,
                "opponent_score": opp_score,
                "starters": parsed["starters"],
                "source_url": parsed["source_url"],
                "validation": validation,
                "stints": [s.as_dict() for s in stints],
            })
        except Exception as exc:
            errors.append({"game_id": game_id, "error": str(exc)})
    return games, errors


def build_snapshot(season_code: str = "U2026", include_gbl: bool = True) -> dict:
    games = sync_eurocup(season_code)
    errors: list[dict] = []
    competitions = ["EuroCup"]
    if include_gbl:
        gbl_games, gbl_errors = sync_gbl()
        games.extend(gbl_games)
        errors.extend(gbl_errors)
        competitions.append("GBL")
    games.sort(key=lambda x: (x.get("game_date") or "9999", str(x.get("game_code"))))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "team": "ARIS Thessaloniki",
        "season": "2026-27",
        "competitions": competitions,
        "games": games,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build validated ARIS lineup dataset from official sources")
    parser.add_argument("--season", default="U2026")
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    parser.add_argument("--no-gbl", action="store_true")
    args = parser.parse_args()

    snapshot = build_snapshot(args.season.upper(), include_gbl=not args.no_gbl)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "games": len(snapshot["games"]),
        "errors": len(snapshot["errors"]),
        "output": str(out),
        "validated": all(g["validation"]["ok"] for g in snapshot["games"]),
    }))


if __name__ == "__main__":
    main()
