from __future__ import annotations

from dataclasses import dataclass, asdict
from math import ceil
from typing import Any

from sources.eurocup_pbp import normalize_name

@dataclass
class Stint:
    start_second: int
    end_second: int
    duration_seconds: int
    lineup: list[str]
    aris_points: int
    opp_points: int
    def as_dict(self) -> dict[str, Any]: return asdict(self)

def _period(e):
    minute=int(e.get('MINUTE') or 1)
    return max(1, ceil(minute/10)) if minute<=40 else 4+ceil((minute-40)/5)

def event_elapsed_seconds(e):
    p=_period(e); plen=600 if p<=4 else 300
    prev=(p-1)*600 if p<=4 else 2400+(p-5)*300
    clock=e.get('MARKERTIME') or ("10:00" if p<=4 else "05:00")
    m,s=map(int,str(clock).split(':')[:2])
    return prev+(plen-(m*60+s))

def _reconstruct(groups, starters, score_fn, sub_fn, end=2400):
    lineup={normalize_name(x) for x in starters}
    if len(lineup)!=5: raise ValueError('Expected five starters')
    out=[]; start=0; sf=sa=pf=pa=0
    def close(t):
        nonlocal start,sf,sa
        if t>start:
            if len(lineup)!=5: raise ValueError(f'Invalid lineup size {len(lineup)} at {start}-{t}: {sorted(lineup)}')
            out.append(Stint(start,t,t-start,sorted(lineup),pf-sf,pa-sa)); start=t; sf=pf; sa=pa
    for t, events in groups:
        score=score_fn(events)
        if score is not None: pf,pa=score
        subs=sub_fn(events)
        if subs:
            close(t)
            for action,name in subs:
                if action=='OUT': lineup.discard(normalize_name(name))
            for action,name in subs:
                if action=='IN': lineup.add(normalize_name(name))
            if len(lineup)!=5: raise ValueError(f'Substitution group at {t}s produced {len(lineup)} players: {sorted(lineup)}')
    close(end)
    return out

def reconstruct_eurocup_stints(events, starters, *, aris_is_team_a, aris_code='ARI'):
    ordered=sorted(events,key=lambda e:(event_elapsed_seconds(e),int(e.get('NUMBEROFPLAY') or 0)))
    grouped=[]; i=0
    while i<len(ordered):
        t=event_elapsed_seconds(ordered[i]); same=[]
        while i<len(ordered) and event_elapsed_seconds(ordered[i])==t: same.append(ordered[i]); i+=1
        grouped.append((t,same))
    running_for=0; running_against=0
    scoring={'FTM':1,'2FGM':2,'3FGM':3}
    def score(es):
        nonlocal running_for,running_against
        changed=False
        for e in es:
            pts=scoring.get(e.get('PLAYTYPE'))
            if not pts: continue
            changed=True
            if str(e.get('CODETEAM','')).strip().upper()==aris_code: running_for+=pts
            else: running_against+=pts
        return (running_for,running_against) if changed else None
    def subs(es):
        return [(e['PLAYTYPE'],e.get('PLAYER')) for e in es if str(e.get('CODETEAM','')).strip().upper()==aris_code and e.get('PLAYTYPE') in {'IN','OUT'}]
    end=max(2400,max((event_elapsed_seconds(e) for e in ordered),default=2400))
    return _reconstruct(grouped,starters,score,subs,end)

def reconstruct_gbl_stints(parsed):
    idx=int(parsed['aris_index']); events=sorted(parsed['events'],key=lambda e:int(e['elapsed']))
    grouped=[]; i=0
    while i<len(events):
        t=int(events[i]['elapsed']); same=[]
        while i<len(events) and int(events[i]['elapsed'])==t: same.append(events[i]); i+=1
        grouped.append((t,same))
    def score(es):
        vals=[e for e in es if e.get('score_a') is not None and e.get('score_b') is not None]
        if not vals: return None
        e=vals[-1]; a=int(e['score_a']); b=int(e['score_b'])
        return (a,b) if idx==0 else (b,a)
    def subs(es): return [(e['action'],e.get('player')) for e in es if e.get('team_index')==idx and e.get('action') in {'IN','OUT'}]
    return _reconstruct(grouped,parsed['starters'],score,subs,2400)

def validate_stints(stints, expected_margin=None):
    seconds=sum(s.duration_seconds for s in stints); margin=sum(s.aris_points-s.opp_points for s in stints)
    all_five=all(len(s.lineup)==5 and len(set(s.lineup))==5 for s in stints)
    return {'ok':bool(stints) and all_five and seconds>=2400 and seconds%300==0 and (expected_margin is None or margin==expected_margin),'stints':len(stints),'seconds':seconds,'all_five':all_five,'margin':margin,'expected_margin':expected_margin,'margin_ok':expected_margin is None or margin==expected_margin}
