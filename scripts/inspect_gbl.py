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

    # Probe the first completed-looking game link, printing table headers and nearby structure.
    candidate = None
    for text, href in links:
        if "mode=1" in href or "mode=2" in href:
            candidate = href
            break
    if candidate is None and links:
        candidate = links[0][1]

    if candidate:
        print("PROBE_GAME", candidate)
        game_html = fetch(candidate)
        gsoup = BeautifulSoup(game_html, "html.parser")
        print("TITLE", gsoup.title.get_text(" ", strip=True) if gsoup.title else "")
        tables = gsoup.find_all("table")
        print("TABLE_COUNT", len(tables))
        for i, table in enumerate(tables[:12]):
            headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
            rows = table.find_all("tr")
            first_rows = []
            for row in rows[:3]:
                first_rows.append([cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])])
            print("TABLE", i, "HEADERS", headers)
            print("TABLE", i, "ROWS", first_rows)

        for a in gsoup.find_all("a", href=True):
            href = a["href"]
            text = " ".join(a.stripped_strings)
            if "EsakegameView" in href or "play" in text.lower() or "στατισ" in text.lower() or "stats" in text.lower():
                print("GAME_NAV", repr(text), urljoin(BASE, href))


if __name__ == "__main__":
    main()
