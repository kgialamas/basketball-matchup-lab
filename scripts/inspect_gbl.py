from __future__ import annotations

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://www.esake.gr"
TEAM_URL = f"{BASE}/gr/action/EsaketeamView?idteam=00000005&mode=3"


def fetch(url: str) -> str:
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0 BasketballMatchupLab/1.0"})
    r.raise_for_status()
    print("FETCH", r.status_code, r.url, "bytes", len(r.text))
    return r.text


def dump_page(label: str, url: str) -> None:
    print("PROBE", label, url)
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    print("TITLE", soup.title.get_text(" ", strip=True) if soup.title else "")
    tables = soup.find_all("table")
    print("TABLE_COUNT", len(tables))
    for i, table in enumerate(tables[:20]):
        print("TABLE_CLASS", i, table.get("class"), "ID", table.get("id"))
        headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
        rows = table.find_all("tr")
        first_rows = []
        for row in rows[:5]:
            first_rows.append([cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])])
        print("TABLE", i, "HEADERS", headers)
        print("TABLE", i, "ROWS", first_rows)

    # Print compact text around likely statistical labels to expose non-table layouts.
    for needle in ["2PM", "3PM", "FTM", "REB", "AST", "RANK", "FOULS", "MIN"]:
        node = soup.find(string=lambda s: s and needle.lower() in s.lower())
        if node:
            parent = node.parent
            print("NEEDLE", needle, "PARENT", parent.name, parent.get("class"), parent.get_text(" | ", strip=True)[:1200])


def main() -> None:
    html = fetch(TEAM_URL)
    soup = BeautifulSoup(html, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = " ".join(a.stripped_strings)
        if "EsakegameView" in href:
            links.append((text, urljoin(BASE, href)))

    print("GAME_LINK_COUNT", len(links))
    seen = set()
    for text, href in links:
        if href in seen:
            continue
        seen.add(href)
        print("GAME_LINK", repr(text), href)

    stats_url = None
    pbp_url = None
    for text, href in links:
        if stats_url is None and "mode=3" in href:
            stats_url = href
        if pbp_url is None and "mode=2" in href:
            pbp_url = href
        if stats_url and pbp_url:
            break

    if stats_url:
        dump_page("STATS", stats_url)
    if pbp_url:
        dump_page("PBP", pbp_url)


if __name__ == "__main__":
    main()
