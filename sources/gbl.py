from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import requests
from bs4 import BeautifulSoup

BASE = "https://www.esake.gr"
TEAM_URL = f"{BASE}/el/action/EsaketeamView?idteam=00000005&mode=3"
GAME_URL = f"{BASE}/el/action/EsakegameView?idgame={{game_id}}&mode=2"
UA = {"user-agent": "basketball-matchup-lab/1.0"}


@dataclass
class GBLEvent:
    elapsed: int
    score_a: int | None
    score_b: int | None
    team_index: int | None
    text: str
    player: str | None
    action: str | None


def _html(url: str) -> str:
    r = requests.get(url, headers=UA, timeout=30)
    r.raise_for_status()
    return r.text


def discover_aris_game_ids() -> list[str]:
    soup = BeautifulSoup(_html(TEAM_URL), "html.parser")
    ids = set()
    for a in soup.select('a[href*="EsakegameView?idgame="]'):
        m = re.search(r"idgame=([A-Za-z0-9]+)", a.get("href", ""))
        if m:
            ids.add(m.group(1))
    return sorted(ids)


def _player(text: str) -> str | None:
    m = re.search(r"\(\d+\)\s+(.+?)(?:\s+(?:commited|committed|made|performed|perfomed|missed|passed|left|entered)\b)", text, re.I)
    return " ".join(m.group(1).split()).title() if m else None


def _action(text: str) -> str | None:
    t = text.lower()
    if "entered" in t and "court" in t:
        return "IN"
    if "left" in t and "court" in t:
        return "OUT"
    return None


def parse_game(game_id: str) -> dict[str, Any]:
    url = GAME_URL.format(game_id=game_id)
    soup = BeautifulSoup(_html(url), "html.parser")
    headline = soup.select_one(".mbt-headline .mbt-text")
    if not headline:
        raise ValueError(f"GBL game {game_id}: play-by-play headline not found")
    headline_text = " ".join(headline.stripped_strings)
    m = re.search(r"Game:\s*(.*?)\s+(\d+)\s*-\s*(\d+)\s+(.*)$", headline_text)
    if not m:
        raise ValueError(f"GBL game {game_id}: cannot parse headline {headline_text!r}")
    team_a, score_a, score_b, team_b = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
    aris_index = 0 if "aris" in team_a.lower() else 1 if "aris" in team_b.lower() else None
    if aris_index is None:
        raise ValueError(f"GBL game {game_id}: ARIS not present in headline")

    holder = soup.select_one(".mbt-actions-holder table")
    if not holder:
        raise ValueError(f"GBL game {game_id}: actions table not found")
    events: list[GBLEvent] = []
    for tr in holder.select("tr"):
        cells = tr.find_all("td")
        if len(cells) < 2:
            continue
        clock = cells[0].get_text(" ", strip=True)
        if not re.fullmatch(r"\d{1,2}:\d{2}", clock):
            continue
        mm, ss = map(int, clock.split(":"))
        elapsed = mm * 60 + ss
        sm = re.search(r"(\d+)\s*:\s*(\d+)", cells[1].get_text(" ", strip=True))
        sa, sb = (int(sm.group(1)), int(sm.group(2))) if sm else (None, None)
        for idx, cell in enumerate(cells[2:4]):
            text = " ".join(cell.stripped_strings)
            if text:
                events.append(GBLEvent(elapsed, sa, sb, idx, text, _player(text), _action(text)))

    sub_times = [e.elapsed for e in events if e.team_index == aris_index and e.action in {"IN", "OUT"}]
    if not sub_times:
        raise ValueError(f"GBL game {game_id}: no ARIS substitutions parsed")
    first_sub = min(sub_times)
    starters = sorted({e.player for e in events if e.team_index == aris_index and e.player and e.elapsed <= first_sub and e.action != "IN"})
    if len(starters) != 5:
        raise ValueError(f"GBL game {game_id}: starter inference produced {len(starters)} players: {starters}")
    return {"game_id": game_id, "source_url": url, "team_a": team_a, "team_b": team_b, "score_a": score_a, "score_b": score_b, "aris_index": aris_index, "starters": starters, "events": [e.__dict__ for e in events]}
