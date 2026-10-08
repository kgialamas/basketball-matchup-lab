from __future__ import annotations

from typing import Any
import requests

PBP_URL = "https://live.euroleague.net/api/PlayByPlay"
BOX_URL = "https://live.euroleague.net/api/Boxscore"


def _get(url: str, **params: Any) -> Any:
    r = requests.get(url, params=params, headers={"accept": "application/json", "user-agent": "basketball-matchup-lab/1.0"}, timeout=30)
    r.raise_for_status()
    return r.json()


def _find_event_list(node: Any) -> list[dict[str, Any]]:
    if isinstance(node, list) and node and isinstance(node[0], dict) and "PLAYTYPE" in node[0]:
        return node
    if isinstance(node, dict):
        for value in node.values():
            found = _find_event_list(value)
            if found:
                return found
    if isinstance(node, list):
        for value in node:
            found = _find_event_list(value)
            if found:
                return found
    return []


def _find_stats(node: Any) -> list[dict[str, Any]]:
    if isinstance(node, dict) and isinstance(node.get("Stats"), list):
        return node["Stats"]
    if isinstance(node, dict):
        for value in node.values():
            found = _find_stats(value)
            if found:
                return found
    if isinstance(node, list):
        for value in node:
            found = _find_stats(value)
            if found:
                return found
    return []


def fetch_game(season_code: str, game_code: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pbp = _get(PBP_URL, seasoncode=season_code, gamecode=game_code)
    box = _get(BOX_URL, seasoncode=season_code, gamecode=game_code)
    events = _find_event_list(pbp)
    teams = _find_stats(box)
    if not events:
        raise ValueError(f"No play-by-play events found for {season_code}/{game_code}")
    if not teams:
        raise ValueError(f"No boxscore team blocks found for {season_code}/{game_code}")
    return events, teams


def aris_box(teams: list[dict[str, Any]]) -> dict[str, Any]:
    for team in teams:
        name = str(team.get("Team", ""))
        players = team.get("PlayersStats") or []
        codes = {str(p.get("Team", "")).strip().upper() for p in players}
        if "ARIS" in name.upper() or "ARI" in codes:
            return team
    raise ValueError("ARIS boxscore block not found")


def starters(team: dict[str, Any]) -> list[str]:
    out = []
    for p in team.get("PlayersStats") or []:
        if int(p.get("IsStarter") or 0) == 1:
            out.append(str(p.get("Player") or "").strip())
    if len(out) != 5:
        raise ValueError(f"Expected 5 ARIS starters, found {len(out)}")
    return out


def normalize_name(name: str | None) -> str:
    if not name:
        return ""
    s = " ".join(name.replace(" - ", "-").split()).strip()
    if "," in s:
        last, first = [x.strip().title() for x in s.split(",", 1)]
        return f"{first} {last}".strip()
    return s.title()
