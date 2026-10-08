from __future__ import annotations

from dataclasses import dataclass, asdict
from math import ceil
from typing import Any

from sources.eurocup_pbp import normalize_name


@dataclass
class Stint:
    start_second: int
    end_second: int
    duration_seconds: int
    lineup: list[str]
    aris_points: int
    opp_points: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _period_from_event(event: dict[str, Any]) -> int:
    minute = int(event.get("MINUTE") or 1)
    if minute <= 40:
        return max(1, ceil(minute / 10))
    return 4 + ceil((minute - 40) / 5)


def _remaining_seconds(clock: str | None, period: int) -> int:
    if not clock:
        return 600 if period <= 4 else 300
    m, s = [int(x) for x in str(clock).split(":")[:2]]
    return m * 60 + s


def event_elapsed_seconds(event: dict[str, Any]) -> int:
    period = _period_from_event(event)
    period_len = 600 if period <= 4 else 300
    previous = 2400 + max(0, period - 5) * 300 if period > 4 else (period - 1) * 600
    return previous + (period_len - _remaining_seconds(event.get("MARKERTIME"), period))


def reconstruct_eurocup_stints(events: list[dict[str, Any]], starters: list[str], aris_code: str = "ARI") -> list[Stint]:
    lineup = {normalize_name(x) for x in starters}
    if len(lineup) != 5:
        raise ValueError("Starter normalization did not yield exactly five players")

    ordered = sorted(events, key=lambda e: (event_elapsed_seconds(e), int(e.get("NUMBEROFPLAY") or 0)))
    stints: list[Stint] = []
    start = 0
    start_aris = start_opp = 0
    score_aris = score_opp = 0
    i = 0

    def close(at: int) -> None:
        nonlocal start, start_aris, start_opp
        if at > start:
            if len(lineup) != 5:
                raise ValueError(f"Invalid lineup size {len(lineup)} at {start}-{at}: {sorted(lineup)}")
            stints.append(Stint(start, at, at - start, sorted(lineup), score_aris - start_aris, score_opp - start_opp))
            start = at
            start_aris = score_aris
            start_opp = score_opp

    while i < len(ordered):
        t = event_elapsed_seconds(ordered[i])
        same_time = []
        while i < len(ordered) and event_elapsed_seconds(ordered[i]) == t:
            same_time.append(ordered[i])
            i += 1

        for e in same_time:
            a = e.get("POINTS_A")
            b = e.get("POINTS_B")
            if a is not None or b is not None:
                a = int(a or 0)
                b = int(b or 0)
                if str(e.get("CODETEAM", "")).strip().upper() == aris_code:
                    pass
                score_aris, score_opp = (a, b) if any(str(x.get("CODETEAM", "")).strip().upper() == aris_code and x.get("POINTS_A") is not None for x in ordered[: min(i, len(ordered))]) else (b, a)

        subs = [e for e in same_time if str(e.get("CODETEAM", "")).strip().upper() == aris_code and e.get("PLAYTYPE") in {"IN", "OUT"}]
        if subs:
            close(t)
            for e in subs:
                name = normalize_name(e.get("PLAYER"))
                if e.get("PLAYTYPE") == "OUT":
                    lineup.discard(name)
            for e in subs:
                name = normalize_name(e.get("PLAYER"))
                if e.get("PLAYTYPE") == "IN":
                    lineup.add(name)
            if len(lineup) != 5:
                raise ValueError(f"Substitution group at {t}s produced {len(lineup)} players: {sorted(lineup)}")

    game_end = max(2400, max((event_elapsed_seconds(e) for e in ordered), default=2400))
    close(game_end)
    return stints


def validate_stints(stints: list[Stint], expected_margin: int | None = None) -> dict[str, Any]:
    total_seconds = sum(s.duration_seconds for s in stints)
    all_five = all(len(s.lineup) == 5 and len(set(s.lineup)) == 5 for s in stints)
    margin = sum(s.aris_points - s.opp_points for s in stints)
    ok_time = total_seconds >= 2400 and total_seconds % 300 == 0
    ok_margin = expected_margin is None or margin == expected_margin
    return {
        "ok": bool(stints) and all_five and ok_time and ok_margin,
        "stints": len(stints),
        "seconds": total_seconds,
        "all_five": all_five,
        "margin": margin,
        "expected_margin": expected_margin,
        "margin_ok": ok_margin,
    }
