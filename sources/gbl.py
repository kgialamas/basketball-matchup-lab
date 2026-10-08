from __future__ import annotations

import json
import re
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = "https://www.esake.gr"
RESULTS_URL = f"{BASE}/gr/action/EsakeResults"
HEADERS = {"User-Agent": "Mozilla/5.0 BasketballMatchupLab/1.0"}
SOURCE = "esake"
COMPETITION = "GBL"


def _get(url: str) -> tuple[str, BeautifulSoup]:
    r = requests.get(url, timeout=30, headers=HEADERS)
    r.raise_for_status()
    # ESAKE serves UTF-8 content but its headers can cause requests to guess latin-1,
    # producing mojibake for Greek team names. Decode the response bytes explicitly.
    text = r.content.decode("utf-8", errors="replace")
    return text, BeautifulSoup(text, "html.parser")


def _query_id(href: str, key: str) -> str | None:
    try:
        return parse_qs(urlparse(href).query).get(key, [None])[0]
    except Exception:
        return None


def _num(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip().replace(",", ".")
    if text in {"", "-", "--", "--:--:--"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _made_attempted(value: str | None) -> tuple[float | None, float | None]:
    if not value:
        return None, None
    m = re.search(r"(-?\d+)\s*-\s*(-?\d+)", value)
    if not m:
        return None, None
    return float(m.group(1)), float(m.group(2))


def _minutes(value: str | None) -> float | None:
    if not value:
        return None
    parts = value.strip().split(":")
    try:
        if len(parts) == 3:
            h, m, s = [int(x) for x in parts]
            return h * 60 + m + s / 60
        if len(parts) == 2:
            m, s = [int(x) for x in parts]
            return m + s / 60
    except ValueError:
        return None
    return None


def _clean_player_name(value: str) -> str:
    return re.sub(r"^#\d+\s*", "", value).strip()


def _slug_code(name: str) -> str:
    clean = re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_")
    return clean[:32] or "UNKNOWN"


def discover_games(results_url: str = RESULTS_URL) -> list[str]:
    """Return unique official GBL game IDs exposed on the results page."""
    _, soup = _get(results_url)
    ids: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(BASE, a["href"])
        if "EsakegameView" not in href or "mode=3" not in href:
            continue
        game_id = _query_id(href, "idgame")
        if game_id and game_id not in seen:
            seen.add(game_id)
            ids.append(game_id)
    return ids


def team_games_from_team_page(team_id: str = "00000005") -> list[str]:
    """Useful fallback/discovery path. Default team is Aris."""
    url = f"{BASE}/gr/action/EsaketeamView?idteam={team_id}&mode=3"
    _, soup = _get(url)
    ids: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(BASE, a["href"])
        if "EsakegameView" not in href or "mode=3" not in href:
            continue
        game_id = _query_id(href, "idgame")
        if game_id and game_id not in seen:
            seen.add(game_id)
            ids.append(game_id)
    return ids


def _participating_teams(soup: BeautifulSoup) -> list[tuple[str, str]]:
    teams: list[tuple[str, str]] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "EsaketeamView" not in href:
            continue
        team_id = _query_id(href, "idteam")
        name = " ".join(a.stripped_strings).strip()
        if not team_id or not name or team_id in seen:
            continue
        seen.add(team_id)
        teams.append((team_id, name))
    return teams[:2]


def _score_and_names(soup: BeautifulSoup, teams: list[tuple[str, str]]) -> tuple[str, str, float | None, float | None]:
    text = " ".join(soup.stripped_strings)
    m = re.search(r"Game:\s*(.+?)\s+(\d+)\s*-\s*(\d+)\s+(.+?)(?:\s+PLAYER|\s+SHOTS|$)", text, flags=re.I)
    if m:
        return m.group(1).strip(), m.group(4).strip(), float(m.group(2)), float(m.group(3))

    tables = soup.select("table.table-esake")
    totals: list[float | None] = []
    for table in tables[:2]:
        total = None
        for tr in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
            if cells and cells[0].upper() == "TOTAL" and len(cells) > 1:
                total = _num(cells[1])
                break
        totals.append(total)

    names = [t[1] for t in teams]
    while len(names) < 2:
        names.append(f"TEAM_{len(names)+1}")
    while len(totals) < 2:
        totals.append(None)
    return names[0], names[1], totals[0], totals[1]


def _player_rows(table, team_code: str, team_name: str, opponent_code: str, opponent_name: str,
                 team_score: float | None, opponent_score: float | None, game_id: str,
                 season_code: str, home_away: str) -> list[dict]:
    rows: list[dict] = []
    for tr in table.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
        if len(cells) < 17:
            continue
        first = cells[0].strip()
        if not first.startswith("#"):
            continue

        player_link = tr.find("a", href=lambda h: h and "EsakeplayerView" in h)
        player_code = _query_id(player_link["href"], "idplayer") if player_link else None
        player_name = _clean_player_name(first)
        fg2m, fg2a = _made_attempted(cells[2])
        fg3m, fg3a = _made_attempted(cells[3])
        ftm, fta = _made_attempted(cells[4])

        rows.append({
            "source": SOURCE,
            "competition_code": COMPETITION,
            "season_code": season_code,
            "game_code": game_id,
            "game_date": None,
            "team_code": team_code,
            "team_name": team_name,
            "opponent_code": opponent_code,
            "opponent_name": opponent_name,
            "home_away": home_away,
            "team_score": team_score,
            "opponent_score": opponent_score,
            "player_code": player_code or f"{team_code}:{_slug_code(player_name)}",
            "player_name": player_name,
            "position_name": None,
            "starter": None,
            "minutes": _minutes(cells[15]),
            "points": _num(cells[1]),
            "rebounds": _num(cells[5]),
            "offensive_rebounds": _num(cells[7]),
            "defensive_rebounds": _num(cells[6]),
            "assists": _num(cells[8]),
            "steals": _num(cells[13]),
            "turnovers": _num(cells[14]),
            "blocks": _num(cells[9]),
            "fouls_committed": _num(cells[12]),
            "fouls_received": _num(cells[11]),
            "plus_minus": None,
            "fg2m": fg2m,
            "fg2a": fg2a,
            "fg3m": fg3m,
            "fg3a": fg3a,
            "ftm": ftm,
            "fta": fta,
            "valuation": _num(cells[16]),
            "raw_json": json.dumps({"cells": cells}, ensure_ascii=False),
        })
    return rows


def _team_total(table) -> dict:
    for tr in table.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
        if not cells or cells[0].upper() != "TOTAL" or len(cells) < 17:
            continue
        fg2m, fg2a = _made_attempted(cells[2])
        fg3m, fg3a = _made_attempted(cells[3])
        ftm, fta = _made_attempted(cells[4])
        oreb = _num(cells[7])
        tov = _num(cells[14])
        fga = (fg2a or 0) + (fg3a or 0)
        possessions = None
        if oreb is not None and tov is not None and fta is not None:
            possessions = fga - oreb + tov + 0.44 * fta
        return {
            "points": _num(cells[1]),
            "fg2m": fg2m, "fg2a": fg2a,
            "fg3m": fg3m, "fg3a": fg3a,
            "ftm": ftm, "fta": fta,
            "rebounds": _num(cells[5]),
            "defensive_rebounds": _num(cells[6]),
            "offensive_rebounds": oreb,
            "assists": _num(cells[8]),
            "blocks": _num(cells[9]),
            "fouls_received": _num(cells[11]),
            "fouls_committed": _num(cells[12]),
            "steals": _num(cells[13]),
            "turnovers": tov,
            "valuation": _num(cells[16]),
            "possessions_est": possessions,
            "raw_json": json.dumps({"cells": cells}, ensure_ascii=False),
        }
    raise ValueError("TOTAL row not found in GBL stats table")


def parse_game(game_id: str, season_code: str = "G2026") -> tuple[dict, list[dict], list[dict]]:
    url = f"{BASE}/gr/action/EsakegameView?idgame={game_id}&mode=3"
    _, soup = _get(url)
    tables = soup.select("table.table-esake")
    if len(tables) < 2:
        raise ValueError(f"Expected two GBL boxscore tables for {game_id}, found {len(tables)}")

    teams = _participating_teams(soup)
    home_name, away_name, home_score, away_score = _score_and_names(soup, teams)

    if len(teams) >= 2:
        home_code, away_code = teams[0][0], teams[1][0]
        home_name = teams[0][1] or home_name
        away_name = teams[1][1] or away_name
    else:
        home_code, away_code = _slug_code(home_name), _slug_code(away_name)

    totals = [_team_total(tables[0]), _team_total(tables[1])]
    if home_score is None:
        home_score = totals[0]["points"]
    if away_score is None:
        away_score = totals[1]["points"]

    game_row = {
        "source": SOURCE,
        "competition_code": COMPETITION,
        "season_code": season_code,
        "game_code": game_id,
        "game_date": None,
        "played": 1 if home_score is not None and away_score is not None else 0,
        "home_team_code": home_code,
        "home_team_name": home_name,
        "away_team_code": away_code,
        "away_team_name": away_name,
        "home_score": home_score,
        "away_score": away_score,
        "raw_json": json.dumps({"url": url}, ensure_ascii=False),
    }

    team_rows = []
    for i, (code, name, opp_code, opp_name, hoa, score, opp_score) in enumerate([
        (home_code, home_name, away_code, away_name, "home", home_score, away_score),
        (away_code, away_name, home_code, home_name, "away", away_score, home_score),
    ]):
        total = totals[i]
        team_rows.append({
            "source": SOURCE,
            "competition_code": COMPETITION,
            "season_code": season_code,
            "game_code": game_id,
            "game_date": None,
            "team_code": code,
            "team_name": name,
            "opponent_code": opp_code,
            "opponent_name": opp_name,
            "home_away": hoa,
            "points": score,
            "opponent_points": opp_score,
            "rebounds": total["rebounds"],
            "offensive_rebounds": total["offensive_rebounds"],
            "defensive_rebounds": total["defensive_rebounds"],
            "assists": total["assists"],
            "steals": total["steals"],
            "turnovers": total["turnovers"],
            "blocks": total["blocks"],
            "fouls_committed": total["fouls_committed"],
            "fouls_received": total["fouls_received"],
            "fg2m": total["fg2m"], "fg2a": total["fg2a"],
            "fg3m": total["fg3m"], "fg3a": total["fg3a"],
            "ftm": total["ftm"], "fta": total["fta"],
            "valuation": total["valuation"],
            "possessions_est": total["possessions_est"],
            "raw_json": total["raw_json"],
        })

    player_rows = []
    player_rows.extend(_player_rows(tables[0], home_code, home_name, away_code, away_name, home_score, away_score, game_id, season_code, "home"))
    player_rows.extend(_player_rows(tables[1], away_code, away_name, home_code, home_name, away_score, home_score, game_id, season_code, "away"))

    return game_row, team_rows, player_rows


def pbp_url(game_id: str) -> str:
    return f"{BASE}/gr/action/EsakegameView?idgame={game_id}&mode=2"
