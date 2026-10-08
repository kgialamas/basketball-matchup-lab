const competition = document.querySelector('#competition');
const season = document.querySelector('#season');
const search = document.querySelector('#search');
const results = document.querySelector('#results');
const profile = document.querySelector('#profile');
const tabs = [...document.querySelectorAll('.tab')];

let dataset = null;
let mode = 'team';

function metric(label,val){return `<div class="metric"><span>${label}</span><strong>${val}</strong></div>`}
function pctText(value){return `${Number(value || 0).toFixed(1)}%`}
function currentSeason(){
  if(!dataset) return null;
  return dataset.seasons.find(s => s.competition === competition.value && s.season === season.value) || null;
}
function allPlayers(s){
  if(!s) return [];
  return s.teams.flatMap(t => t.players.map(p => ({...p, team:t.name, teamCode:t.code})));
}
function fillSeasonOptions(){
  if(!dataset) return;
  const comps=[...new Set(dataset.seasons.map(s=>s.competition))];
  competition.innerHTML=comps.map(c=>`<option>${c}</option>`).join('');
  if(comps.includes('EuroCup')) competition.value='EuroCup';
  refreshSeasonOptions();
}
function refreshSeasonOptions(){
  const seasons=dataset.seasons.filter(s=>s.competition===competition.value).map(s=>s.season);
  season.innerHTML=[...new Set(seasons)].map(s=>`<option>${s}</option>`).join('');
  renderResults();
  const s=currentSeason();
  if(s?.teams?.length){
    const aris=s.teams.find(t=>t.name.toLowerCase().includes('aris'));
    renderTeam(aris || s.teams[0]);
  } else profile.innerHTML='';
}

function renderTeam(t){
 const s=t.summary;
 profile.innerHTML = `<div class="card"><div class="profile-head"><div><div class="eyebrow">${currentSeason().competition} · ${currentSeason().season}</div><h2>${t.name}</h2><p>Official-source season data · ${s.gp} games</p></div></div>
 <div class="metrics">${metric('PTS',s.pts.toFixed(1))}${metric('PTS Allowed',s.opp.toFixed(1))}${metric('REB',s.reb.toFixed(1))}${metric('AST',s.ast.toFixed(1))}${metric('PIR',s.pir.toFixed(1))}${metric('Poss.',s.poss.toFixed(1))}</div>
 <h3>Shooting</h3><div class="shooting"><div><b>2FG</b><span>${s.fg2} — ${pctText(s.fg2pct)}</span></div><div><b>3FG</b><span>${s.fg3} — ${pctText(s.fg3pct)}</span></div><div><b>FT</b><span>${s.ft} — ${pctText(s.ftpct)}</span></div></div>
 <h3>Roster — Season Statistics</h3><div class="table-wrap"><table><thead><tr><th>Player</th><th>Pos</th><th>GP</th><th>GS</th><th>MIN</th><th>PTS</th><th>2FG</th><th>3FG</th><th>FT</th><th>OREB</th><th>DREB</th><th>REB</th><th>AST</th><th>STL</th><th>TO</th><th>BLK</th><th>FC</th><th>FD</th><th>+/-</th><th>PIR</th></tr></thead><tbody>${t.players.map(p=>`<tr data-player="${p.code}"><td>${p.name}</td><td>${p.pos}</td><td>${p.gp}</td><td>${p.gs}</td><td>${p.min}</td><td>${p.pts.toFixed(1)}</td><td>${p.fg2} — ${pctText(p.fg2pct)}</td><td>${p.fg3} — ${pctText(p.fg3pct)}</td><td>${p.ft} — ${pctText(p.ftpct)}</td><td>${p.oreb.toFixed(1)}</td><td>${p.dreb.toFixed(1)}</td><td>${p.reb.toFixed(1)}</td><td>${p.ast.toFixed(1)}</td><td>${p.stl.toFixed(1)}</td><td>${p.tov.toFixed(1)}</td><td>${p.blk.toFixed(1)}</td><td>${p.fc.toFixed(1)}</td><td>${p.fd.toFixed(1)}</td><td>${p.plus_minus.toFixed(1)}</td><td>${p.pir.toFixed(1)}</td></tr>`).join('')}</tbody></table></div></div>`;
 document.querySelectorAll('[data-player]').forEach(r=>r.onclick=()=>renderPlayer(r.dataset.player));
}

function renderPlayer(code){
 const s=currentSeason();
 const hit=allPlayers(s).find(p=>p.code===code); if(!hit)return;
 profile.innerHTML=`<div class="card"><div class="eyebrow">PLAYER PROFILE · ${s.competition} ${s.season}</div><h2>${hit.name}</h2><p>${hit.team} · ${hit.pos} · ${hit.gp} games</p><div class="metrics">${metric('MIN',hit.min)}${metric('PTS',hit.pts.toFixed(1))}${metric('REB',hit.reb.toFixed(1))}${metric('AST',hit.ast.toFixed(1))}${metric('STL',hit.stl.toFixed(1))}${metric('PIR',hit.pir.toFixed(1))}</div><h3>Shooting</h3><div class="shooting"><div><b>2FG</b><span>${hit.fg2} — ${pctText(hit.fg2pct)}</span></div><div><b>3FG</b><span>${hit.fg3} — ${pctText(hit.fg3pct)}</span></div><div><b>FT</b><span>${hit.ft} — ${pctText(hit.ftpct)}</span></div></div></div>`;
}

function renderResults(){
 const s=currentSeason();
 if(!s){results.innerHTML='';return;}
 const q=search.value.trim().toLowerCase();
 if(mode==='team'){
  const hits=s.teams.filter(t=>t.name.toLowerCase().includes(q));
  results.innerHTML=hits.map(t=>`<button class="result" data-team="${t.code}"><b>${t.name}</b><span>${s.competition} · ${s.season} · ${t.summary.gp} GP</span></button>`).join('');
  document.querySelectorAll('[data-team]').forEach(b=>b.onclick=()=>renderTeam(s.teams.find(t=>t.code===b.dataset.team)));
 }else{
  const players=allPlayers(s).filter(p=>p.name.toLowerCase().includes(q));
  results.innerHTML=players.map(p=>`<button class="result" data-p="${p.code}"><b>${p.name}</b><span>${p.team} · ${p.pos}</span></button>`).join('');
  document.querySelectorAll('[data-p]').forEach(b=>b.onclick=()=>renderPlayer(b.dataset.p));
 }
}

tabs.forEach(t=>t.onclick=()=>{tabs.forEach(x=>x.classList.remove('active'));t.classList.add('active');mode=t.dataset.mode;search.placeholder=mode==='team'?'Search team...':'Search player...';search.value='';profile.innerHTML='';renderResults();});
search.addEventListener('input',renderResults);
competition.addEventListener('change',refreshSeasonOptions);
season.addEventListener('change',()=>{renderResults(); const s=currentSeason(); if(s?.teams?.length) renderTeam(s.teams[0]);});

async function init(){
  results.innerHTML='<div class="muted">Loading official-source dataset…</div>';
  try{
    const response=await fetch(`data/site-data.json?v=${Date.now()}`);
    if(!response.ok) throw new Error(`HTTP ${response.status}`);
    dataset=await response.json();
    fillSeasonOptions();
  }catch(err){
    results.innerHTML='<div class="muted">Dataset refresh is still running. Please reload in a few minutes.</div>';
    console.error(err);
  }
}

init();
