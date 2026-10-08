const competition=document.querySelector('#competition');
const season=document.querySelector('#season');
const search=document.querySelector('#search');
const results=document.querySelector('#results');
const profile=document.querySelector('#profile');
const tabs=[...document.querySelectorAll('.tab')];
let dataset=null, mode='player';

const n=v=>Number(v||0).toFixed(1);
const shot=s=>`${s?.line||'0/0'} — ${Number(s?.pct||0).toFixed(1)}%`;
const metric=(label,val)=>`<div class="metric"><span>${label}</span><strong>${val}</strong></div>`;
const currentSeason=()=>dataset?.seasons.find(s=>s.competition===competition.value&&s.season===season.value)||null;
const allPlayers=s=>s?s.teams.flatMap(t=>t.players.map(p=>({...p,team:t.name,teamCode:t.code}))):[];

function fillFilters(){
 const comps=[...new Set(dataset.seasons.map(s=>s.competition))];
 competition.innerHTML=comps.map(c=>`<option>${c}</option>`).join('');
 if(comps.includes('EuroCup')) competition.value='EuroCup';
 refreshSeasons();
}
function refreshSeasons(){
 const ss=[...new Set(dataset.seasons.filter(s=>s.competition===competition.value).map(s=>s.season))];
 season.innerHTML=ss.map(x=>`<option>${x}</option>`).join('');
 renderResults();
 const s=currentSeason(); if(s){ const p=allPlayers(s)[0]; if(mode==='player'&&p) renderPlayer(p.code); else if(s.teams[0]) renderTeam(s.teams[0]); }
}

function renderPlayer(code){
 const s=currentSeason(); const p=allPlayers(s).find(x=>x.code===code); if(!p)return;
 profile.innerHTML=`
 <article class="profile-card">
  <header class="hero"><div><div class="eyebrow">PLAYER PROFILE · ${s.competition} · ${s.season}</div><h2>${p.name}</h2><p>${p.team} · ${p.pos}</p></div><div class="hero-badge">${p.gp}<span>GP</span></div></header>
  <section class="stat-strip">${metric('MIN',p.min)}${metric('PTS',n(p.pts))}${metric('REB',n(p.reb))}${metric('AST',n(p.ast))}${metric('STL',n(p.stl))}${metric('PIR',n(p.pir))}</section>
  <section class="profile-section"><div class="section-kicker">Season shooting</div><div class="shoot-grid"><div><span>2FG</span><strong>${shot(p.fg2)}</strong></div><div><span>3FG</span><strong>${shot(p.fg3)}</strong></div><div><span>FT</span><strong>${shot(p.ft)}</strong></div></div></section>
  <section class="profile-section"><div class="section-kicker">Full season profile</div><div class="detail-grid">${metric('GP',p.gp)}${metric('GS',p.gs)}${metric('OREB',n(p.oreb))}${metric('DREB',n(p.dreb))}${metric('TO',n(p.tov))}${metric('BLK',n(p.blk))}${metric('FC',n(p.fc))}${metric('FD',n(p.fd))}${metric('+/-',n(p.plus_minus))}</div></section>
  <section class="profile-section"><div class="section-head"><div><div class="section-kicker">Game log</div><h3>${s.season} ${s.competition}</h3></div><span>${p.games?.length||0} games</span></div>
   <div class="table-wrap"><table><thead><tr><th>Date</th><th>Opponent</th><th>H/A</th><th>Result</th><th>MIN</th><th>PTS</th><th>2FG</th><th>3FG</th><th>FT</th><th>OREB</th><th>DREB</th><th>REB</th><th>AST</th><th>STL</th><th>TO</th><th>BLK</th><th>FC</th><th>FD</th><th>+/-</th><th>PIR</th></tr></thead><tbody>${(p.games||[]).map(g=>`<tr><td>${g.date||'—'}</td><td>${g.opponent||'—'}</td><td>${g.ha||'—'}</td><td>${g.result}</td><td>${g.min}</td><td>${n(g.pts)}</td><td>${shot(g.fg2)}</td><td>${shot(g.fg3)}</td><td>${shot(g.ft)}</td><td>${n(g.oreb)}</td><td>${n(g.dreb)}</td><td>${n(g.reb)}</td><td>${n(g.ast)}</td><td>${n(g.stl)}</td><td>${n(g.tov)}</td><td>${n(g.blk)}</td><td>${n(g.fc)}</td><td>${n(g.fd)}</td><td>${n(g.plus_minus)}</td><td>${n(g.pir)}</td></tr>`).join('')}</tbody></table></div>
  </section>
 </article>`;
}

function renderTeam(t){
 const s=currentSeason(),x=t.summary;
 profile.innerHTML=`<article class="profile-card"><header class="hero"><div><div class="eyebrow">TEAM PROFILE · ${s.competition} · ${s.season}</div><h2>${t.name}</h2><p>Official-source season profile</p></div><div class="hero-badge">${x.gp}<span>GP</span></div></header>
 <section class="stat-strip">${metric('PTS',n(x.pts))}${metric('PTS ALLOWED',n(x.opp))}${metric('REB',n(x.reb))}${metric('AST',n(x.ast))}${metric('PIR',n(x.pir))}${metric('POSS',n(x.poss))}</section>
 <section class="profile-section"><div class="section-kicker">Season shooting</div><div class="shoot-grid"><div><span>2FG</span><strong>${shot(x.fg2)}</strong></div><div><span>3FG</span><strong>${shot(x.fg3)}</strong></div><div><span>FT</span><strong>${shot(x.ft)}</strong></div></div></section>
 <section class="profile-section"><div class="section-head"><div><div class="section-kicker">Roster</div><h3>Season statistics</h3></div><span>${t.players.length} players</span></div><div class="table-wrap"><table><thead><tr><th>Player</th><th>Pos</th><th>GP</th><th>GS</th><th>MIN</th><th>PTS</th><th>2FG</th><th>3FG</th><th>FT</th><th>REB</th><th>AST</th><th>STL</th><th>TO</th><th>BLK</th><th>+/-</th><th>PIR</th></tr></thead><tbody>${t.players.map(p=>`<tr class="clickable" data-player="${p.code}"><td>${p.name}</td><td>${p.pos}</td><td>${p.gp}</td><td>${p.gs}</td><td>${p.min}</td><td>${n(p.pts)}</td><td>${shot(p.fg2)}</td><td>${shot(p.fg3)}</td><td>${shot(p.ft)}</td><td>${n(p.reb)}</td><td>${n(p.ast)}</td><td>${n(p.stl)}</td><td>${n(p.tov)}</td><td>${n(p.blk)}</td><td>${n(p.plus_minus)}</td><td>${n(p.pir)}</td></tr>`).join('')}</tbody></table></div></section>
 <section class="profile-section"><div class="section-head"><div><div class="section-kicker">Team game log</div><h3>${s.season} ${s.competition}</h3></div><span>${t.games?.length||0} games</span></div><div class="table-wrap"><table><thead><tr><th>Date</th><th>Opponent</th><th>H/A</th><th>Result</th><th>PTS</th><th>REB</th><th>AST</th><th>STL</th><th>TO</th><th>BLK</th><th>PIR</th><th>Poss.</th></tr></thead><tbody>${(t.games||[]).map(g=>`<tr><td>${g.date||'—'}</td><td>${g.opponent||'—'}</td><td>${g.ha||'—'}</td><td>${g.result}</td><td>${n(g.pts)}</td><td>${n(g.reb)}</td><td>${n(g.ast)}</td><td>${n(g.stl)}</td><td>${n(g.tov)}</td><td>${n(g.blk)}</td><td>${n(g.pir)}</td><td>${n(g.poss)}</td></tr>`).join('')}</tbody></table></div></section></article>`;
 document.querySelectorAll('[data-player]').forEach(r=>r.onclick=()=>{mode='player';syncTabs();renderPlayer(r.dataset.player)});
}

function renderResults(){
 const s=currentSeason(); if(!s){results.innerHTML='';return;}
 const q=search.value.trim().toLowerCase();
 if(!q){results.innerHTML='';return;}
 if(mode==='player'){
  const hits=allPlayers(s).filter(p=>p.name.toLowerCase().includes(q)).slice(0,12);
  results.innerHTML=hits.map(p=>`<button class="result" data-p="${p.code}"><b>${p.name}</b><span>${p.team} · ${p.pos}</span></button>`).join('');
  document.querySelectorAll('[data-p]').forEach(b=>b.onclick=()=>renderPlayer(b.dataset.p));
 }else{
  const hits=s.teams.filter(t=>t.name.toLowerCase().includes(q)).slice(0,12);
  results.innerHTML=hits.map(t=>`<button class="result" data-team="${t.code}"><b>${t.name}</b><span>${s.competition} · ${s.season} · ${t.summary.gp} GP</span></button>`).join('');
  document.querySelectorAll('[data-team]').forEach(b=>b.onclick=()=>renderTeam(s.teams.find(t=>t.code===b.dataset.team)));
 }
}
function syncTabs(){tabs.forEach(t=>t.classList.toggle('active',t.dataset.mode===mode));search.placeholder=mode==='player'?'Search player...':'Search team...';}
tabs.forEach(t=>t.onclick=()=>{mode=t.dataset.mode;syncTabs();search.value='';results.innerHTML='';const s=currentSeason();if(mode==='player'){const p=allPlayers(s)[0];if(p)renderPlayer(p.code)}else if(s?.teams[0])renderTeam(s.teams[0])});
search.addEventListener('input',renderResults); competition.addEventListener('change',refreshSeasons); season.addEventListener('change',refreshSeasons);

async function init(){
 results.innerHTML='<div class="muted">Loading official-source dataset…</div>';
 try{const r=await fetch(`data/site-data.json?v=${Date.now()}`);if(!r.ok)throw new Error(`HTTP ${r.status}`);dataset=await r.json();fillFilters();mode='player';syncTabs();const s=currentSeason(),p=allPlayers(s)[0];if(p)renderPlayer(p.code)}catch(e){results.innerHTML='<div class="muted">Dataset refresh is still running. Please reload shortly.</div>';console.error(e)}
}
init();
