const sample = {
  competition: 'EuroCup', season: '2026-27',
  teams: [
    {name:'Aris Thessaloniki', code:'ARI', summary:{gp:2, pts:90.0, opp:77.0, reb:45.0, ast:22.0, fg2:'42/71', fg2pct:'59.2%', fg3:'19/64', fg3pct:'29.7%', ft:'39/49', ftpct:'79.6%', blk:4.0, fc:23.0, fd:25.0, tov:15.5, poss:78.8}, players:[
      {name:'Jeremiah Robinson-Earl',pos:'F',min:'29:41',pts:12.0,reb:11.0,ast:2.5,fg3:'2/8'},
      {name:'Matthew Morgan',pos:'G',min:'24:35',pts:10.0,reb:3.5,ast:3.5,fg3:'4/17'},
      {name:'Neno Dimitrijevic',pos:'G',min:'22:13',pts:14.5,reb:3.0,ast:5.0,fg3:'2/5'},
      {name:'Adam Mokoka',pos:'F',min:'22:11',pts:8.5,reb:2.0,ast:0.5,fg3:'1/9'},
      {name:'Vassilis Toliopoulos',pos:'G',min:'18:20',pts:9.5,reb:2.5,ast:3.0,fg3:'5/13'}
    ]},
    {name:'Recoletas Salud San Pablo Burgos', code:'BUR', summary:{gp:2, pts:82.5, opp:87.0, reb:41.0, ast:19.5, fg2:'39/81', fg2pct:'48.1%', fg3:'20/50', fg3pct:'40.0%', ft:'27/43', ftpct:'62.8%', blk:3.0, fc:25.5, fd:22.5, tov:16.5, poss:74.5}, players:[
      {name:'Sekou Doumbouya',pos:'C',min:'24:13',pts:14.5,reb:9.0,ast:3.0,fg3:'1/3'},
      {name:'Chase Audige',pos:'G',min:'22:47',pts:17.5,reb:1.0,ast:1.5,fg3:'6/13'},
      {name:'DJ Steward',pos:'G',min:'21:39',pts:17.5,reb:2.5,ast:3.0,fg3:'6/8'},
      {name:'Ziga Samar',pos:'G',min:'21:37',pts:1.0,reb:3.5,ast:5.0,fg3:'0/0'},
      {name:'Daniel Diez',pos:'F',min:'19:55',pts:5.5,reb:4.0,ast:1.5,fg3:'1/8'}
    ]}
  ]
};

const competition = document.querySelector('#competition');
const season = document.querySelector('#season');
const search = document.querySelector('#search');
const results = document.querySelector('#results');
const profile = document.querySelector('#profile');
const tabs = [...document.querySelectorAll('.tab')];
let mode = 'team';
competition.innerHTML = `<option>${sample.competition}</option>`;
season.innerHTML = `<option>${sample.season}</option>`;

function metric(label,val){return `<div class="metric"><span>${label}</span><strong>${val}</strong></div>`}
function renderTeam(t){
 const s=t.summary;
 profile.innerHTML = `<div class="card"><div class="profile-head"><div><div class="eyebrow">${sample.competition} · ${sample.season}</div><h2>${t.name}</h2><p>Official-source sample · ${s.gp} games</p></div></div>
 <div class="metrics">${metric('PTS',s.pts.toFixed(1))}${metric('PTS Allowed',s.opp.toFixed(1))}${metric('REB',s.reb.toFixed(1))}${metric('AST',s.ast.toFixed(1))}${metric('Possessions',s.poss.toFixed(1))}</div>
 <h3>Shooting</h3><div class="shooting"><div><b>2FG</b><span>${s.fg2} — ${s.fg2pct}</span></div><div><b>3FG</b><span>${s.fg3} — ${s.fg3pct}</span></div><div><b>FT</b><span>${s.ft} — ${s.ftpct}</span></div></div>
 <h3>Roster — Season Averages</h3><div class="table-wrap"><table><thead><tr><th>Player</th><th>Pos</th><th>MIN</th><th>PTS</th><th>REB</th><th>AST</th><th>3FG</th></tr></thead><tbody>${t.players.map(p=>`<tr data-player="${p.name}"><td>${p.name}</td><td>${p.pos}</td><td>${p.min}</td><td>${p.pts.toFixed(1)}</td><td>${p.reb.toFixed(1)}</td><td>${p.ast.toFixed(1)}</td><td>${p.fg3}</td></tr>`).join('')}</tbody></table></div></div>`;
 document.querySelectorAll('[data-player]').forEach(r=>r.onclick=()=>renderPlayer(r.dataset.player));
}
function renderPlayer(name){
 const hit=sample.teams.flatMap(t=>t.players.map(p=>({...p,team:t.name}))).find(p=>p.name===name); if(!hit)return;
 profile.innerHTML=`<div class="card"><div class="eyebrow">PLAYER PROFILE · ${sample.competition} ${sample.season}</div><h2>${hit.name}</h2><p>${hit.team} · ${hit.pos}</p><div class="metrics">${metric('MIN',hit.min)}${metric('PTS',hit.pts.toFixed(1))}${metric('REB',hit.reb.toFixed(1))}${metric('AST',hit.ast.toFixed(1))}${metric('3FG',hit.fg3)}</div></div>`;
}
function renderResults(){
 const q=search.value.trim().toLowerCase();
 if(mode==='team'){
  const hits=sample.teams.filter(t=>t.name.toLowerCase().includes(q));
  results.innerHTML=hits.map(t=>`<button class="result" data-team="${t.code}"><b>${t.name}</b><span>${sample.competition} · ${sample.season}</span></button>`).join('');
  document.querySelectorAll('[data-team]').forEach(b=>b.onclick=()=>renderTeam(sample.teams.find(t=>t.code===b.dataset.team)));
 }else{
  const players=sample.teams.flatMap(t=>t.players.map(p=>({...p,team:t.name}))).filter(p=>p.name.toLowerCase().includes(q));
  results.innerHTML=players.map(p=>`<button class="result" data-p="${p.name}"><b>${p.name}</b><span>${p.team} · ${p.pos}</span></button>`).join('');
  document.querySelectorAll('[data-p]').forEach(b=>b.onclick=()=>renderPlayer(b.dataset.p));
 }
}
tabs.forEach(t=>t.onclick=()=>{tabs.forEach(x=>x.classList.remove('active'));t.classList.add('active');mode=t.dataset.mode;search.placeholder=mode==='team'?'Search team...':'Search player...';search.value='';profile.innerHTML='';renderResults();});
search.addEventListener('input',renderResults);
renderResults();
renderTeam(sample.teams[0]);