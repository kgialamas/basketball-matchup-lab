from __future__ import annotations

import pandas as pd
import streamlit as st

from analytics.matchup import build_matchup, list_seasons, list_teams

st.set_page_config(page_title="Basketball Matchup Lab", layout="wide")
st.title("Basketball Matchup Lab")
st.caption("Personal matchup explorer — current season first, interpretation left to you.")

seasons = list_seasons()
if seasons.empty:
    st.warning("No data yet. Run: python -m scripts.sync --season U2026")
    st.stop()

season_code = st.selectbox("Season", seasons["season_code"].tolist())
filter_mode = st.selectbox("Sample", ["All games", "Last 5", "Last 10", "Home", "Away"], index=0)

teams = list_teams(season_code)
team_options = {f"{r.team_name} ({r.team_code})": r.team_code for _, r in teams.iterrows()}
labels = list(team_options.keys())

c1, c2 = st.columns(2)
with c1:
    team_a_label = st.selectbox("Team A", labels, index=0)
with c2:
    default_b = 1 if len(labels) > 1 else 0
    team_b_label = st.selectbox("Team B", labels, index=default_b)

if team_a_label == team_b_label:
    st.info("Choose two different teams.")
    st.stop()

if st.button("Build matchup", type="primary", use_container_width=True):
    st.session_state["matchup"] = build_matchup(
        team_options[team_a_label],
        team_options[team_b_label],
        season_code,
        filter_mode=filter_mode,
    )

m = st.session_state.get("matchup")
if not m or m["season_code"] != season_code or m.get("filter_mode") != filter_mode:
    st.stop()

a, b = m["team_a"], m["team_b"]
st.subheader(f"{a['name']} vs {b['name']}")
st.caption(f"Sample: {filter_mode} · League average estimated possessions: {m['league_pace']:.1f}")

metric_labels = [
    ("points", "PTS"), ("opponent_points", "PTS Allowed"), ("rebounds", "REB"),
    ("assists", "AST"), ("fg2m", "2PM"), ("fg2a", "2PA"), ("fg3m", "3PM"),
    ("fg3a", "3PA"), ("ftm", "FTM"), ("fta", "FTA"), ("blocks", "BLK"),
    ("fouls_committed", "Fouls committed"), ("fouls_received", "Fouls received"),
    ("turnovers", "TO"), ("possessions_est", "Possessions")
]

summary_rows = []
for key, label in metric_labels:
    summary_rows.append({
        "Metric": label,
        a["name"]: a["summary"].get(key),
        b["name"]: b["summary"].get(key),
    })
summary_df = pd.DataFrame(summary_rows)

allowed_labels = [
    ("points", "PTS allowed"), ("rebounds", "REB allowed"), ("assists", "AST allowed"),
    ("fg2m", "2PM allowed"), ("fg2a", "2PA allowed"), ("fg3m", "3PM allowed"),
    ("fg3a", "3PA allowed"), ("ftm", "FTM allowed"), ("fta", "FTA allowed"),
    ("blocks", "BLK allowed"), ("fouls_received", "Fouls drawn allowed"),
    ("turnovers", "TO allowed"),
]
allowed_rows = []
for key, label in allowed_labels:
    allowed_rows.append({
        "Metric": label,
        a["name"]: a["allowed"].get(key),
        b["name"]: b["allowed"].get(key),
    })
allowed_df = pd.DataFrame(allowed_rows)

player_cols = [
    "player_name", "position_name", "minutes", "points", "rebounds", "assists",
    "fg2m", "fg2a", "fg3m", "fg3a", "ftm", "fta", "blocks",
    "fouls_committed", "fouls_received", "turnovers"
]

t1, t2, t3, t4, t5, t6 = st.tabs([
    "Overview", "Team Stats", "Players", "Opponent Allowed", "By Position", "Pace"
])

with t1:
    x1, x2 = st.columns(2)
    with x1:
        pts = a["summary"].get("points")
        st.metric(a["name"], f"{pts:.1f} PPG" if pts is not None else "—")
        st.write(f"Pace: **{a['summary']['pace_label'].upper()}**")
        st.write(f"Sample: {a['summary']['games']} games")
    with x2:
        pts = b["summary"].get("points")
        st.metric(b["name"], f"{pts:.1f} PPG" if pts is not None else "—")
        st.write(f"Pace: **{b['summary']['pace_label'].upper()}**")
        st.write(f"Sample: {b['summary']['games']} games")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

with t2:
    st.markdown("### Team production")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    st.markdown("### What each team allows")
    st.dataframe(allowed_df, use_container_width=True, hide_index=True)

with t3:
    p1, p2 = st.columns(2)
    with p1:
        st.markdown(f"### {a['name']}")
        st.dataframe(a["players"][player_cols], use_container_width=True, hide_index=True)
    with p2:
        st.markdown(f"### {b['name']}")
        st.dataframe(b["players"][player_cols], use_container_width=True, hide_index=True)

with t4:
    st.markdown(f"### What opponents have done vs {a['name']}")
    cols_a = [c for c in [*player_cols, "position_group"] if c in a["opponents"].columns]
    st.dataframe(a["opponents"][cols_a], use_container_width=True, hide_index=True)
    st.markdown(f"### What opponents have done vs {b['name']}")
    cols_b = [c for c in [*player_cols, "position_group"] if c in b["opponents"].columns]
    st.dataframe(b["opponents"][cols_b], use_container_width=True, hide_index=True)

with t5:
    target = st.radio("Defense to inspect", [a["name"], b["name"]], horizontal=True)
    selected = a if target == a["name"] else b
    groups = selected["opponents_by_position"]
    if not groups:
        st.info("No opponent position data in this sample.")
    else:
        group_name = st.selectbox("Position group", list(groups.keys()))
        st.caption(f"Opponent {group_name.lower()} vs {selected['name']} · {filter_mode}")
        frame = groups[group_name]
        cols = [c for c in player_cols if c in frame.columns]
        st.dataframe(frame[cols], use_container_width=True, hide_index=True)

with t6:
    pace_df = pd.DataFrame([
        {"Team": a["name"], "Estimated possessions": a["summary"].get("possessions_est"), "Label": a["summary"]["pace_label"]},
        {"Team": b["name"], "Estimated possessions": b["summary"].get("possessions_est"), "Label": b["summary"]["pace_label"]},
        {"Team": "League average", "Estimated possessions": m["league_pace"], "Label": "reference"},
    ])
    st.dataframe(pace_df, use_container_width=True, hide_index=True)
    st.caption("Possessions are estimated as FGA − OREB + TO + 0.44 × FTA. Shot-clock timing will be added later from play-by-play where reliable.")
