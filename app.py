from __future__ import annotations

import pandas as pd
import streamlit as st

from analytics.matchup import build_matchup, list_seasons, list_teams
from analytics.schedule import list_upcoming_games

st.set_page_config(page_title="Basketball Matchup Lab", layout="wide")
st.title("Basketball Matchup Lab")
st.caption("Upcoming games, team profiles, player production, opponent allowed and pace — all in one place.")

seasons = list_seasons()
if seasons.empty:
    st.warning("No data available yet. Run the season sync first.")
    st.stop()

season_options = seasons["season_code"].tolist()
season_code = st.sidebar.selectbox("Season", season_options)
filter_mode = st.sidebar.selectbox("Sample", ["All games", "Last 5", "Last 10", "Home", "Away"])
mode = st.sidebar.radio("Mode", ["Upcoming Games", "Manual Matchup"])

selected_a = None
selected_b = None

if mode == "Upcoming Games":
    upcoming = list_upcoming_games(season_code=season_code)
    st.subheader("Upcoming Games")
    if upcoming.empty:
        st.info("No upcoming games are stored for this season yet. Use Manual Matchup or run the schedule sync.")
    else:
        competition_options = ["All"] + sorted(upcoming["competition"].dropna().unique().tolist())
        competition = st.selectbox("Competition", competition_options)
        view = upcoming if competition == "All" else upcoming[upcoming["competition"] == competition]
        labels = {
            f"{r.matchup} · {r.game_date}": (r.home_team_code, r.away_team_code)
            for _, r in view.iterrows()
        }
        chosen = st.selectbox("Game", list(labels.keys()))
        selected_a, selected_b = labels[chosen]
        if st.button("Open Matchup", type="primary", use_container_width=True):
            st.session_state["selected_matchup"] = (selected_a, selected_b, season_code, filter_mode)
else:
    st.subheader("Manual Matchup")
    teams = list_teams(season_code)
    team_options = {f"{r.team_name} ({r.team_code})": r.team_code for _, r in teams.iterrows()}
    labels = list(team_options.keys())
    if len(labels) < 2:
        st.info("Not enough teams are available in this season yet.")
        st.stop()
    c1, c2 = st.columns(2)
    with c1:
        a_label = st.selectbox("Team A", labels, index=0)
    with c2:
        b_label = st.selectbox("Team B", labels, index=1)
    selected_a, selected_b = team_options[a_label], team_options[b_label]
    if selected_a == selected_b:
        st.info("Choose two different teams.")
        st.stop()
    if st.button("Build Matchup", type="primary", use_container_width=True):
        st.session_state["selected_matchup"] = (selected_a, selected_b, season_code, filter_mode)

selection = st.session_state.get("selected_matchup")
if not selection:
    st.stop()
team_a, team_b, selected_season, selected_filter = selection
if selected_season != season_code or selected_filter != filter_mode:
    st.stop()

try:
    m = build_matchup(team_a, team_b, season_code, filter_mode=filter_mode)
except ValueError as exc:
    st.warning(str(exc))
    st.stop()

a, b = m["team_a"], m["team_b"]
st.divider()
st.header(f"{a['name']} vs {b['name']}")
st.caption(f"{season_code} · {filter_mode} · League average estimated possessions: {m['league_pace']:.1f}")

metric_labels = [
    ("points", "PTS"), ("opponent_points", "PTS Allowed"), ("rebounds", "REB"),
    ("assists", "AST"), ("fg2m", "2PM"), ("fg2a", "2PA"), ("fg3m", "3PM"),
    ("fg3a", "3PA"), ("ftm", "FTM"), ("fta", "FTA"), ("blocks", "BLK"),
    ("fouls_committed", "Fouls Committed"), ("fouls_received", "Fouls Drawn"),
    ("turnovers", "TO"), ("possessions_est", "Estimated Possessions"),
]
summary_df = pd.DataFrame([
    {"Metric": label, a["name"]: a["summary"].get(key), b["name"]: b["summary"].get(key)}
    for key, label in metric_labels
])

allowed_labels = [
    ("points", "PTS Allowed"), ("rebounds", "REB Allowed"), ("assists", "AST Allowed"),
    ("fg2m", "2PM Allowed"), ("fg2a", "2PA Allowed"), ("fg3m", "3PM Allowed"),
    ("fg3a", "3PA Allowed"), ("ftm", "FTM Allowed"), ("fta", "FTA Allowed"),
    ("blocks", "BLK Allowed"), ("fouls_received", "Fouls Drawn Allowed"), ("turnovers", "TO Allowed"),
]
allowed_df = pd.DataFrame([
    {"Metric": label, a["name"]: a["allowed"].get(key), b["name"]: b["allowed"].get(key)}
    for key, label in allowed_labels
])

player_cols = [
    "player_name", "position_name", "minutes", "points", "rebounds", "assists",
    "fg2m", "fg2a", "fg3m", "fg3a", "ftm", "fta", "blocks",
    "fouls_committed", "fouls_received", "turnovers",
]

ov, team_tab, players_tab, allowed_tab, position_tab, pace_tab = st.tabs([
    "Overview", "Team Stats", "Players", "Opponent Allowed", "By Position", "Pace"
])

with ov:
    c1, c2 = st.columns(2)
    for col, team in [(c1, a), (c2, b)]:
        with col:
            pts = team["summary"].get("points")
            st.metric(team["name"], f"{pts:.1f} PPG" if pts is not None else "—")
            st.write(f"Pace: **{team['summary']['pace_label'].title()}**")
            st.write(f"Sample size: **{team['summary']['games']} games**")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

with team_tab:
    st.markdown("### Team Production")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    st.markdown("### What Each Team Allows")
    st.dataframe(allowed_df, use_container_width=True, hide_index=True)

with players_tab:
    p1, p2 = st.columns(2)
    with p1:
        st.markdown(f"### {a['name']}")
        st.dataframe(a["players"][[c for c in player_cols if c in a["players"].columns]], use_container_width=True, hide_index=True)
    with p2:
        st.markdown(f"### {b['name']}")
        st.dataframe(b["players"][[c for c in player_cols if c in b["players"].columns]], use_container_width=True, hide_index=True)

with allowed_tab:
    st.markdown(f"### Opponents vs {a['name']}")
    st.dataframe(a["opponents"], use_container_width=True, hide_index=True)
    st.markdown(f"### Opponents vs {b['name']}")
    st.dataframe(b["opponents"], use_container_width=True, hide_index=True)

with position_tab:
    target = st.radio("Defense to Inspect", [a["name"], b["name"]], horizontal=True)
    selected = a if target == a["name"] else b
    groups = selected["opponents_by_position"]
    if not groups:
        st.info("No opponent position data is available for this sample yet.")
    else:
        group = st.selectbox("Position Group", list(groups.keys()))
        st.caption(f"Opponent {group.lower()} vs {selected['name']} · {filter_mode}")
        st.dataframe(groups[group], use_container_width=True, hide_index=True)

with pace_tab:
    pace_df = pd.DataFrame([
        {"Team": a["name"], "Estimated Possessions": a["summary"].get("possessions_est"), "Pace": a["summary"]["pace_label"].title()},
        {"Team": b["name"], "Estimated Possessions": b["summary"].get("possessions_est"), "Pace": b["summary"]["pace_label"].title()},
        {"Team": "League Average", "Estimated Possessions": m["league_pace"], "Pace": "Reference"},
    ])
    st.dataframe(pace_df, use_container_width=True, hide_index=True)
    st.caption("Estimated possessions = FGA − OREB + TO + 0.44 × FTA. Shot-clock timing will be added from play-by-play where reliable.")
