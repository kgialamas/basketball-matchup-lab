from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = "https://www.esake.gr"
HEADERS = {"User-Agent": "Mozilla/5.0 BasketballMatchupLab/1.0"}
MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _query_id(href: str, key: str) -> str | None:
    try:
        return parse_qs(urlparse(href).query).get(key, [None])[0]
    except Exception:
        return None


def _season_year(month: int, season_code: str) -> int:
    start = int(season_code[-4:])
    return start if month >= 7 else start + 1


def _parse_date(text: str, season_code: str) -> str | None:
    full = re.search(
        r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(20\d{2})\s*-\s*(\d{1,2}:\d{2})",
        text,
        flags=re.I,
    )
    if full:
        dt = datetime.strptime(" ".join(full.groups()), "%d %B %Y %H:%M")
        return dt.isoformat()

    short = re.search(r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)?\s*(\d{1,2})\s+([A-Za-z]{3})\s*-\s*(\d{1,2}:\d{2})", text, flags=re.I)
    if short:
        day, mon, time = short.groups()
        month = MONTHS.get(mon.lower())
        if month:
            year = _season_year(month, season_code)
            dt = datetime.strptime(f"{day} {month} {year} {time}", "%d %m %Y %H:%M")
            return dt.isoformat()
    return None


def _game_container(link) -> object:
    node = link
    for _ in range(8):
        node = getattr(node, "parent", None)
        if node is None:
            break
        team_links = node.find_all("a", href=lambda h: h and "EsaketeamView" in h)
        if len(team_links) >= 2:
            return node
    return link.parent


def discover_team_schedule(team_id: str = "00000005", season_code: str = "G2026") -> list[dict]:
    url = f"{BASE}/en/action/EsaketeamView?idteam={team_id}&mode=3"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, "html.parser")

    rows: list[dict] = []
    seen: set[str] = set()
    for link in soup.find_all("a", href=True):
        href = urljoin(BASE, link["href"])
        if "EsakegameView" not in href or "mode=3" not in href:
            continue
        game_id = _query_id(href, "idgame")
        if not game_id or game_id in seen:
            continue
        seen.add(game_id)

        container = _game_container(link)
        text = " ".join(container.stripped_strings)
        team_links = container.find_all("a", href=lambda h: h and "EsaketeamView" in h)
        teams: list[tuple[str, str]] = []
        team_seen: set[str] = set()
        for t in team_links:
            code = _query_id(t.get("href", ""), "idteam")
            name = " ".join(t.stripped_strings).strip()
            if code and name and code not in team_seen:
                team_seen.add(code)
                teams.append((code, name))
        if len(teams) < 2:
            continue

        score_match = re.search(r"\b(\d{1,3})\s*-\s*(\d{1,3})\b", text)
        played = bool(score_match)
        home_score = float(score_match.group(1)) if score_match else None
        away_score = float(score_match.group(2)) if score_match else None
        rows.append({
            "source": "esake",
            "competition_code": "GBL",
            "season_code": season_code,
            "game_code": game_id,
            "game_date": _parse_date(text, season_code),
            "played": 1 if played else 0,
            "home_team_code": teams[0][0],
            "home_team_name": teams[0][1],
            "away_team_code": teams[1][0],
            "away_team_name": teams[1][1],
            "home_score": home_score,
            "away_score": away_score,
            "raw_json": "{}",
        })
    return rows
