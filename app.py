from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from analytics.matchup import (
    build_matchup,
    build_player_profile,
    build_team_profile,
    list_players,
    list_seasons,
    list_teams,
)

st.set_page_config(page_title="Basketball Matchup Lab", layout="wide")
st.title("Basketball Matchup Lab")
st.caption("Official-source basketball research. Search by team or player first; matchup analysis comes second.")


def fmt_minutes(value) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    total_seconds = int(round(float(value) * 60))
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


def fmt_num(value, digits=1):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    return f"{float(value):.{digits}f}"


def shot_pair(made, attempted):
    if made is None or attempted is None:
        return "—"
    return f"{float(made):.1f}-{float(attempted):.1f}"


def roster_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "Player": r.get("player_name"),
            "Pos": r.get("position_name") or "—",
            "GP": int(r.get("games", 0)),
            "GS": int(r.get("starts", 0) or 0),
            "MIN": fmt_minutes(r.get("minutes")),
            "PTS": fmt_num(r.get("points")),
            "2FG": shot_pair(r.get("fg2m"), r.get("fg2a")),
            "3FG": shot_pair(r.get("fg3m"), r.get("fg3a")),
            "FT": shot_pair(r.get("ftm"), r.get("fta")),
            "OREB": fmt_num(r.get("offensive_rebounds")),
            "DREB": fmt_num(r.get("defensive_rebounds")),
            "REB": fmt_num(r.get("rebounds")),
            "AST": fmt_num(r.get("assists")),
            "STL": fmt_num(r.get("steals")),
            "TO": fmt_num(r.get("turnovers")),
            "BLK": fmt_num(r.get("blocks")),
            "FC": fmt_num(r.get("fouls_committed")),
            "FD": fmt_num(r.get("fouls_received")),
            "+/-": fmt_num(r.get("plus_minus")),
            "PIR": fmt_num(r.get("valuation")),
        })
    return pd.DataFrame(rows)


def team_stats_table(avg: dict, total: dict) -> pd.DataFrame:
    metrics = [
        ("Points", "points"),
        ("Points Allowed", "opponent_points"),
        ("2FG Made", "fg2m"), ("2FG Attempted", "fg2a"),
        ("3FG Made", "fg3m"), ("3FG Attempted", "fg3a"),
        ("FT Made", "ftm"), ("FT Attempted", "fta"),
        ("Offensive Rebounds", "offensive_rebounds"),
        ("Defensive Rebounds", "defensive_rebounds"),
        ("Rebounds", "rebounds"),
        ("Assists", "assists"),
        ("Steals", "steals"),
        ("Turnovers", "turnovers"),
        ("Blocks", "blocks"),
        ("Fouls Committed", "fouls_committed"),
        ("Fouls Drawn", "fouls_received"),
        ("PIR", "valuation"),
        ("Estimated Possessions", "possessions_est"),
    ]
    return pd.DataFrame([
        {"Metric": label, "Per Game": fmt_num(avg.get(key)), "Season Total": fmt_num(total.get(key), 0)}
        for label, key in metrics
    ])


seasons = list_seasons()
if seasons.empty:
    st.warning("No data available yet. Run the season sync first.")
    st.stop()

season_code = st.sidebar.selectbox("Season", seasons["season_code"].tolist())
filter_mode = st.sidebar.selectbox("Sample", ["All games", "Last 5", "Last 10", "Home", "Away"])
search_mode = st.radio("Search", ["Team", "Player", "Matchup"], horizontal=True)

if search_mode == "Team":
    teams = list_teams(season_code)
    if teams.empty:
        st.info("No team data is available for this season yet.")
        st.stop()

    options = {f"{r.team_name} ({r.team_code})": r.team_code for _, r in teams.iterrows()}
    selected_label = st.selectbox("Select Team", list(options.keys()))
    profile = build_team_profile(options[selected_label], season_code, filter_mode)

    st.divider()
    st.header(profile["name"])
    st.caption(f"{season_code} · {filter_mode} · {profile['averages']['games']} games")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PPG", fmt_num(profile["averages"].get("points")))
    c2.metric("Points Allowed", fmt_num(profile["averages"].get("opponent_points")))
    c3.metric("Rebounds", fmt_num(profile["averages"].get("rebounds")))
    c4.metric("Assists", fmt_num(profile["averages"].get("assists")))

    roster_tab, team_tab, games_tab = st.tabs(["Roster & Player Stats", "Team Stats", "Game Log"])

    with roster_tab:
        st.subheader("Current Season Roster")
        st.caption("Per-game averages from official box scores. Minutes are shown as MM:SS.")
        st.dataframe(roster_table(profile["roster"]), use_container_width=True, hide_index=True)

    with team_tab:
        st.subheader("Team Statistics")
        st.dataframe(team_stats_table(profile["averages"], profile["totals"]), use_container_width=True, hide_index=True)
        st.write(f"Pace: **{profile['averages']['pace_label'].title()}**")

    with games_tab:
        cols = ["game_date", "home_away", "opponent_name", "points", "opponent_points", "rebounds", "assists", "turnovers", "possessions_est"]
        frame = profile["games"][[c for c in cols if c in profile["games"].columns]].copy()
        frame.columns = [c.replace("_", " ").title() for c in frame.columns]
        st.dataframe(frame, use_container_width=True, hide_index=True)

elif search_mode == "Player":
    players = list_players(season_code)
    if players.empty:
        st.info("No player data is available for this season yet.")
        st.stop()

    options = {
        f"{r.player_name} — {r.team_name}": r.player_code
        for _, r in players.iterrows()
    }
    selected_label = st.selectbox("Select Player", list(options.keys()))
    profile = build_player_profile(options[selected_label], season_code, filter_mode)
    s = profile["summary"]

    st.divider()
    st.header(profile["player_name"])
    st.caption(f"{profile['team_name']} · {profile['position_name'] or '—'} · {season_code} · {filter_mode}")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("MIN", fmt_minutes(s.get("minutes")))
    c2.metric("PTS", fmt_num(s.get("points")))
    c3.metric("REB", fmt_num(s.get("rebounds")))
    c4.metric("AST", fmt_num(s.get("assists")))
    c5.metric("PIR", fmt_num(s.get("valuation")))

    st.subheader("Season Line")
    st.dataframe(roster_table(pd.DataFrame([s])), use_container_width=True, hide_index=True)

    st.subheader("Game Log")
    game_cols = [
        "game_date", "opponent_name", "home_away", "minutes", "points", "fg2m", "fg2a", "fg3m", "fg3a",
        "ftm", "fta", "offensive_rebounds", "defensive_rebounds", "rebounds", "assists", "steals", "turnovers",
        "blocks", "fouls_committed", "fouls_received", "plus_minus", "valuation",
    ]
    log = profile["game_log"][[c for c in game_cols if c in profile["game_log"].columns]].copy()
    if "minutes" in log:
        log["minutes"] = log["minutes"].map(fmt_minutes)
    st.dataframe(log, use_container_width=True, hide_index=True)

else:
    teams = list_teams(season_code)
    team_options = {f"{r.team_name} ({r.team_code})": r.team_code for _, r in teams.iterrows()}
    labels = list(team_options.keys())
    if len(labels) < 2:
        st.info("Not enough teams are available for a matchup yet.")
        st.stop()

    c1, c2 = st.columns(2)
    with c1:
        a_label = st.selectbox("Team A", labels, index=0)
    with c2:
        b_label = st.selectbox("Team B", labels, index=1)

    if a_label == b_label:
        st.info("Choose two different teams.")
        st.stop()

    if st.button("Build Matchup", type="primary", use_container_width=True):
        m = build_matchup(team_options[a_label], team_options[b_label], season_code, filter_mode)
        st.session_state["matchup_result"] = m

    m = st.session_state.get("matchup_result")
    if not m or m["season_code"] != season_code or m["filter_mode"] != filter_mode:
        st.stop()

    a, b = m["team_a"], m["team_b"]
    st.divider()
    st.header(f"{a['name']} vs {b['name']}")
    st.caption(f"{season_code} · {filter_mode}")

    comparison = pd.DataFrame([
        {"Metric": "Points", a["name"]: fmt_num(a["summary"].get("points")), b["name"]: fmt_num(b["summary"].get("points"))},
        {"Metric": "Points Allowed", a["name"]: fmt_num(a["summary"].get("opponent_points")), b["name"]: fmt_num(b["summary"].get("opponent_points"))},
        {"Metric": "Rebounds", a["name"]: fmt_num(a["summary"].get("rebounds")), b["name"]: fmt_num(b["summary"].get("rebounds"))},
        {"Metric": "Assists", a["name"]: fmt_num(a["summary"].get("assists")), b["name"]: fmt_num(b["summary"].get("assists"))},
        {"Metric": "Estimated Possessions", a["name"]: fmt_num(a["summary"].get("possessions_est")), b["name"]: fmt_num(b["summary"].get("possessions_est"))},
    ])
    st.dataframe(comparison, use_container_width=True, hide_index=True)
