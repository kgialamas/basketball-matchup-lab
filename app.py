from __future__ import annotations

import streamlit as st

from analytics.matchup import build_matchup, list_seasons, list_teams

st.set_page_config(page_title="Basketball Matchup Lab", layout="wide")
st.title("Basketball Matchup Lab")
st.caption("Personal matchup explorer — current season first, interpretation left to you.")

seasons = list_seasons()
if seasons.empty:
    st.warning("No data yet. Run: python scripts/sync.py --season U2026")
    st.stop()

season_code = st.selectbox("Season", seasons["season_code"].tolist())
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
    st.session_state["matchup"] = build_matchup(team_options[team_a_label], team_options[team_b_label], season_code)

m = st.session_state.get("matchup")
if not m or m["season_code"] != season_code:
    st.stop()

a, b = m["team_a"], m["team_b"]
st.subheader(f"{a['name']} vs {b['name']}")
st.caption(f"League average estimated possessions: {m['league_pace']:.1f}")

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

import pandas as pd
summary_df = pd.DataFrame(summary_rows)

t1, t2, t3, t4, t5 = st.tabs(["Overview", "Team Stats", "Players", "Opponent Allowed", "Pace"])

with t1:
    x1, x2 = st.columns(2)
    with x1:
        st.metric(a["name"], f"{a['summary']['points']:.1f} PPG")
        st.write(f"Pace: **{a['summary']['pace_label'].upper()}**")
        st.write(f"Sample: {a['summary']['games']} games")
    with x2:
        st.metric(b["name"], f"{b['summary']['points']:.1f} PPG")
        st.write(f"Pace: **{b['summary']['pace_label'].upper()}**")
        st.write(f"Sample: {b['summary']['games']} games")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

with t2:
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

with t3:
    p1, p2 = st.columns(2)
    display_cols = ["player_name", "position_name", "minutes", "points", "rebounds", "assists", "fg2m", "fg2a", "fg3m", "fg3a", "ftm", "fta", "blocks", "fouls_committed", "fouls_received"]
    with p1:
        st.markdown(f"### {a['name']}")
        st.dataframe(a["players"][display_cols], use_container_width=True, hide_index=True)
    with p2:
        st.markdown(f"### {b['name']}")
        st.dataframe(b["players"][display_cols], use_container_width=True, hide_index=True)

with t4:
    st.markdown(f"### What opponents have done vs {a['name']}")
    st.dataframe(a["opponents"][display_cols], use_container_width=True, hide_index=True)
    st.markdown(f"### What opponents have done vs {b['name']}")
    st.dataframe(b["opponents"][display_cols], use_container_width=True, hide_index=True)

with t5:
    pace_df = pd.DataFrame([
        {"Team": a["name"], "Estimated possessions": a["summary"].get("possessions_est"), "Label": a["summary"]["pace_label"]},
        {"Team": b["name"], "Estimated possessions": b["summary"].get("possessions_est"), "Label": b["summary"]["pace_label"]},
        {"Team": "League average", "Estimated possessions": m["league_pace"], "Label": "reference"},
    ])
    st.dataframe(pace_df, use_container_width=True, hide_index=True)
    st.caption("Possessions are estimated as FGA − OREB + TO + 0.44 × FTA. Shot-clock timing will be added later from play-by-play where reliable.")
