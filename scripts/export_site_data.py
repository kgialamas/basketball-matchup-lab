from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "basketball.db"
OUT_PATH = ROOT / "docs" / "data" / "site-data.json"

SEASON_LABELS = {"E2026":"2026-27","U2026":"2026-27","E2025":"2025-26","U2025":"2025-26","E2024":"2024-25","U2024":"2024-25"}
COMP_LABELS = {"E":"EuroLeague","U":"EuroCup"}

def pct(m,a): return round(m/a*100,1) if a else 0.0
def r1(v): return round(float(v or 0),1)
def mmss(v):
    sec=int(round(float(v or 0)*60)); m,s=divmod(sec,60); return f"{m}:{s:02d}"
def shooting(m,a):
    m,a=int(m or 0),int(a or 0); return {"line":f"{m}/{a}","pct":pct(m,a)}

def game_log(conn, season_code, player_code=None, team_code=None):
    if player_code:
        rows=conn.execute("""SELECT * FROM player_games WHERE source='euroleague' AND season_code=? AND player_code=? ORDER BY game_date DESC,game_code DESC""",(season_code,player_code)).fetchall()
        out=[]
        for g in rows:
            out.append({
                "date":g["game_date"],"opponent":g["opponent_name"],"ha":g["home_away"],
                "result":f"{int(g['team_score'] or 0)}-{int(g['opponent_score'] or 0)}",
                "min":mmss(g["minutes"]),"pts":r1(g["points"]),"oreb":r1(g["offensive_rebounds"]),"dreb":r1(g["defensive_rebounds"]),"reb":r1(g["rebounds"]),
                "ast":r1(g["assists"]),"stl":r1(g["steals"]),"tov":r1(g["turnovers"]),"blk":r1(g["blocks"]),"fc":r1(g["fouls_committed"]),"fd":r1(g["fouls_received"]),
                "plus_minus":r1(g["plus_minus"]),"pir":r1(g["valuation"]),
                "fg2":shooting(g["fg2m"],g["fg2a"]),"fg3":shooting(g["fg3m"],g["fg3a"]),"ft":shooting(g["ftm"],g["fta"])
            })
        return out
    rows=conn.execute("""SELECT * FROM team_games WHERE source='euroleague' AND season_code=? AND team_code=? ORDER BY game_date DESC,game_code DESC""",(season_code,team_code)).fetchall()
    return [{"date":g["game_date"],"opponent":g["opponent_name"],"ha":g["home_away"],"result":f"{int(g['points'] or 0)}-{int(g['opponent_points'] or 0)}","pts":r1(g["points"]),"reb":r1(g["rebounds"]),"ast":r1(g["assists"]),"stl":r1(g["steals"]),"tov":r1(g["turnovers"]),"blk":r1(g["blocks"]),"pir":r1(g["valuation"]),"poss":r1(g["possessions_est"])} for g in rows]

def main():
    if not DB_PATH.exists(): raise SystemExit(f"Database not found: {DB_PATH}")
    conn=sqlite3.connect(DB_PATH); conn.row_factory=sqlite3.Row
    seasons=[r["season_code"] for r in conn.execute("SELECT DISTINCT season_code FROM team_games WHERE source='euroleague' ORDER BY season_code DESC")]
    payload={"generated_from":"official EuroLeague Basketball live API","seasons":[]}
    for season_code in seasons:
        teams=conn.execute("""SELECT team_code,MAX(team_name) team_name,COUNT(*) gp,AVG(points) pts,AVG(opponent_points) opp,AVG(rebounds) reb,AVG(offensive_rebounds) oreb,AVG(defensive_rebounds) dreb,AVG(assists) ast,AVG(steals) stl,AVG(turnovers) tov,AVG(blocks) blk,AVG(fouls_committed) fc,AVG(fouls_received) fd,AVG(valuation) pir,AVG(possessions_est) poss,SUM(fg2m) fg2m,SUM(fg2a) fg2a,SUM(fg3m) fg3m,SUM(fg3a) fg3a,SUM(ftm) ftm,SUM(fta) fta FROM team_games WHERE source='euroleague' AND season_code=? GROUP BY team_code ORDER BY team_name""",(season_code,)).fetchall()
        sobj={"competition":COMP_LABELS.get(season_code[0],season_code[0]),"competition_code":season_code[0],"season":SEASON_LABELS.get(season_code,season_code),"season_code":season_code,"teams":[]}
        for t in teams:
            players=conn.execute("""SELECT player_code,MAX(player_name) player_name,MAX(position_name) position_name,COUNT(*) gp,SUM(CASE WHEN starter=1 THEN 1 ELSE 0 END) gs,AVG(minutes) min,AVG(points) pts,AVG(rebounds) reb,AVG(offensive_rebounds) oreb,AVG(defensive_rebounds) dreb,AVG(assists) ast,AVG(steals) stl,AVG(turnovers) tov,AVG(blocks) blk,AVG(fouls_committed) fc,AVG(fouls_received) fd,AVG(plus_minus) plus_minus,AVG(valuation) pir,SUM(fg2m) fg2m,SUM(fg2a) fg2a,SUM(fg3m) fg3m,SUM(fg3a) fg3a,SUM(ftm) ftm,SUM(fta) fta FROM player_games WHERE source='euroleague' AND season_code=? AND team_code=? GROUP BY player_code ORDER BY AVG(minutes) DESC,AVG(points) DESC""",(season_code,t["team_code"])).fetchall()
            plist=[]
            for p in players:
                plist.append({"code":p["player_code"],"name":p["player_name"],"pos":p["position_name"] or "—","gp":int(p["gp"] or 0),"gs":int(p["gs"] or 0),"min":mmss(p["min"]),"pts":r1(p["pts"]),"oreb":r1(p["oreb"]),"dreb":r1(p["dreb"]),"reb":r1(p["reb"]),"ast":r1(p["ast"]),"stl":r1(p["stl"]),"tov":r1(p["tov"]),"blk":r1(p["blk"]),"fc":r1(p["fc"]),"fd":r1(p["fd"]),"plus_minus":r1(p["plus_minus"]),"pir":r1(p["pir"]),"fg2":shooting(p["fg2m"],p["fg2a"]),"fg3":shooting(p["fg3m"],p["fg3a"]),"ft":shooting(p["ftm"],p["fta"]),"games":game_log(conn,season_code,player_code=p["player_code"])})
            sobj["teams"].append({"code":t["team_code"],"name":t["team_name"],"summary":{"gp":int(t["gp"] or 0),"pts":r1(t["pts"]),"opp":r1(t["opp"]),"reb":r1(t["reb"]),"oreb":r1(t["oreb"]),"dreb":r1(t["dreb"]),"ast":r1(t["ast"]),"stl":r1(t["stl"]),"tov":r1(t["tov"]),"blk":r1(t["blk"]),"fc":r1(t["fc"]),"fd":r1(t["fd"]),"pir":r1(t["pir"]),"poss":r1(t["poss"]),"fg2":shooting(t["fg2m"],t["fg2a"]),"fg3":shooting(t["fg3m"],t["fg3a"]),"ft":shooting(t["ftm"],t["fta"])},"players":plist,"games":game_log(conn,season_code,team_code=t["team_code"])})
        payload["seasons"].append(sobj)
    OUT_PATH.parent.mkdir(parents=True,exist_ok=True); OUT_PATH.write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print(f"Wrote {OUT_PATH}"); conn.close()

if __name__=="__main__": main()
