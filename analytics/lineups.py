from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Any


def _finish(row: dict[str, Any]) -> dict[str, Any]:
    seconds = row.pop("seconds", 0)
    minutes = seconds / 60
    row["minutes"] = round(minutes, 2)
    row["plus_minus"] = int(row.get("points_for", 0) - row.get("points_against", 0))
    row["plus_minus_per_40"] = round(row["plus_minus"] * 40 / minutes, 2) if minutes else None
    row["points_for_per_40"] = round(row.get("points_for", 0) * 40 / minutes, 2) if minutes else None
    row["points_against_per_40"] = round(row.get("points_against", 0) * 40 / minutes, 2) if minutes else None
    return row


def summarize(games: list[dict[str, Any]]) -> dict[str, Any]:
    player = defaultdict(lambda: {"seconds": 0, "points_for": 0, "points_against": 0})
    pair = defaultdict(lambda: {"seconds": 0, "points_for": 0, "points_against": 0})
    lineup = defaultdict(lambda: {"seconds": 0, "points_for": 0, "points_against": 0})
    total_seconds = total_for = total_against = 0

    for game in games:
        for stint in game.get("stints", []):
            secs = int(stint["duration_seconds"])
            pf = int(stint["aris_points"])
            pa = int(stint["opp_points"])
            players = tuple(sorted(stint["lineup"]))
            total_seconds += secs
            total_for += pf
            total_against += pa
            for name in players:
                player[name]["seconds"] += secs
                player[name]["points_for"] += pf
                player[name]["points_against"] += pa
            for combo in combinations(players, 2):
                pair[combo]["seconds"] += secs
                pair[combo]["points_for"] += pf
                pair[combo]["points_against"] += pa
            lineup[players]["seconds"] += secs
            lineup[players]["points_for"] += pf
            lineup[players]["points_against"] += pa

    players_out = []
    for name, values in player.items():
        on = _finish(dict(values))
        off_seconds = total_seconds - values["seconds"]
        off = _finish({
            "seconds": off_seconds,
            "points_for": total_for - values["points_for"],
            "points_against": total_against - values["points_against"],
        })
        swing = None
        if on["plus_minus_per_40"] is not None and off["plus_minus_per_40"] is not None:
            swing = round(on["plus_minus_per_40"] - off["plus_minus_per_40"], 2)
        players_out.append({"name": name, "on": on, "off": off, "swing_per_40": swing})

    pairs_out = [
        {"players": list(names), **_finish(dict(values))}
        for names, values in pair.items()
    ]
    lineups_out = [
        {"players": list(names), **_finish(dict(values))}
        for names, values in lineup.items()
    ]
    players_out.sort(key=lambda x: x["on"]["minutes"], reverse=True)
    pairs_out.sort(key=lambda x: x["minutes"], reverse=True)
    lineups_out.sort(key=lambda x: x["minutes"], reverse=True)
    return {"players": players_out, "pairs": pairs_out, "lineups": lineups_out}
