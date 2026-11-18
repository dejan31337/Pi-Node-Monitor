import os
import json
import base64
import hmac
import uuid
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote

PORT = int(os.getenv("PORT", "8080"))
STATUS_URL = os.getenv("NODE_STATUS_URL", "http://host.docker.internal:18765/status")
HELPER = STATUS_URL.rsplit("/", 1)[0]
TOKEN = os.getenv("NODE_STATUS_TOKEN", "")
DASH_USER = os.getenv("DASHBOARD_USER", "")
DASH_PASS = os.getenv("DASHBOARD_PASSWORD", "")

AVAILABILITY_URL = "https://sync.minepi.com/node-selection-stats?uuid="

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pi Network Node Monitor · 1.0.9</title>
<style>
*{box-sizing:border-box}
:root{color-scheme:dark;--bg:#071126;--panel:#0d1a33;--panel2:#111f3b;--line:#263b60;--text:#edf3ff;--muted:#a9bad9;--blue:#1677ff;--cyan:#20b9f3;--green:#19d58b;--purple:#8138d6;--orange:#f5a623;--red:#ff4561}
html{scroll-behavior:smooth;background:var(--bg)}
body{margin:0;min-height:100vh;background:radial-gradient(ellipse at 48% -20%,#1a3260 0,transparent 52%),var(--bg);color:var(--text);font:15px/1.5 Inter,Segoe UI,Arial,sans-serif}
header{display:flex;align-items:center;gap:22px;padding:22px max(18px,calc((100vw - 1540px)/2));border-bottom:1px solid var(--line);background:linear-gradient(105deg,#09152d,#0c1934 65%,#111b3c)}
.brand-mark{width:76px;height:76px;flex:0 0 76px;border:5px solid #f5b63e;border-radius:50%;display:grid;place-items:center;color:#f5b63e;font-size:43px;font-weight:800;box-shadow:0 0 22px #f5b63e22}
.brand-copy{min-width:240px;flex:1}
header h1{font-size:clamp(22px,2.4vw,34px);line-height:1.15;margin:0 0 6px;letter-spacing:-.6px;color:#f4f7ff}
header .small{color:#b8c8e7;font-size:16px}
.header-status{min-width:260px;border-left:1px solid #506080;padding:5px 22px}
#connection{font-weight:800;color:var(--green);font-size:17px}
#lastReport{margin-top:4px;color:#b8c8e7}
.header-actions{display:flex;gap:10px;flex-wrap:wrap}
main{max-width:1540px;margin:auto;padding:20px 22px 28px}
#message{padding:9px 13px;margin:0 0 13px;color:#b8d6ff;background:#10264a;border:1px solid #234575;border-radius:9px;font-size:13px}
.toolbar{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:0 0 14px}
.menu{display:flex;flex-wrap:wrap;justify-content:space-between;gap:4px;margin:0 0 20px;padding:7px;background:#0d1932;border:1px solid var(--line);border-radius:12px}
button{appearance:none;background:linear-gradient(135deg,#1265e8,#1553c6);color:white;border:1px solid #2678ff;border-radius:9px;padding:11px 16px;margin:2px;font:700 14px Inter,Segoe UI,Arial,sans-serif;cursor:pointer;box-shadow:0 4px 12px #0002;transition:filter .15s,transform .15s}
button:hover{filter:brightness(1.14);transform:translateY(-1px)}
button.active{background:linear-gradient(135deg,#145bd0,#087ee9);border-color:#25b6ff;box-shadow:inset 0 -3px #20baff,0 4px 12px #0002}
button.danger{background:linear-gradient(135deg,#a91642,#d52b51);border-color:#e34b69}
button.secondary{background:linear-gradient(135deg,#5422a3,#7029c2);border-color:#8e4ce2}
input,select{width:min(100%,460px);padding:11px 13px;border:1px solid #34496d;border-radius:8px;background:#09152c;color:var(--text);font-size:14px}
input:focus,select:focus{outline:2px solid #168bff66;border-color:#2d9aff}
.panel{background:linear-gradient(145deg,#101e39,#0b1730);border:1px solid var(--line);border-radius:12px;padding:19px;margin-bottom:15px;box-shadow:0 8px 25px #0003}
.panel h2{font-size:20px;line-height:1.25;margin:0 0 14px;color:#f0f5ff;letter-spacing:-.2px}
#dashboardView>.panel{padding:18px}
#viewTitle{font-size:24px;margin-bottom:16px}
.small{color:var(--muted);font-size:13px}
#connection{font-size:17px;color:var(--green)}
#lastReport{margin-top:3px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px}
.stat{padding:14px;background:#0a1730;border:1px solid #243858;border-top:2px solid #237cf2;border-radius:9px;min-width:0}
.stat-label{color:#aebfdf;font-size:12px;font-weight:650}
.stat-value{font-size:21px;font-weight:800;margin-top:7px;overflow-wrap:anywhere;color:#f1f5ff}
.stat-detail{color:#8fa5c9;font-size:12px;margin-top:5px;overflow-wrap:anywhere}
.stat.status-good{border-top-color:var(--green)}.stat.status-good .stat-value{color:#39e5a2}
.stat.status-bad{border-top-color:var(--red)}.stat.status-bad .stat-value{color:#ff6a7d}
.stat.status-warn{border-top-color:var(--orange)}.stat.status-warn .stat-value{color:#ffc15c}
.service{padding:13px;background:#0a1730;border:1px solid #243858;border-radius:9px;min-width:0}
.service b{display:block;margin-bottom:7px;color:#f0f5ff;font-size:15px;text-transform:capitalize}
.service-actions{display:flex;flex-wrap:wrap;gap:4px;margin-top:9px}.service-actions button{margin:0;padding:8px 10px;font-size:12px}
.service-actions button:disabled{opacity:.35;cursor:not-allowed;transform:none}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#071126;padding:15px;border:1px solid #263b60;border-radius:8px;min-height:45px;color:#dce8ff;max-height:650px;overflow:auto}
.uuid-row{display:flex;flex-wrap:wrap;align-items:center;gap:8px}.hidden{display:none!important}.good{color:var(--green)}.bad{color:var(--red)}
.report-title{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:10px}
footer{color:#93a8ca;font-size:12px;padding:16px 2px 4px;border-top:1px solid var(--line)}
#dashboardContent{align-items:start}
.dashboard-card{background:linear-gradient(145deg,#101e39,#0b1730);border:1px solid var(--line);border-radius:12px;padding:17px;min-width:0;box-shadow:0 8px 25px #0003}
.dashboard-card h2{font-size:19px;margin:0 0 13px;color:#f1f5ff}
.dashboard-card.wide{grid-column:1/-1}
.dashboard-card .grid{grid-template-columns:repeat(auto-fit,minmax(130px,1fr))}
.dashboard-card .uuid-row{margin:8px 0}
#availabilityView .panel,#explorerView .panel,#dockerLogsView .panel,#fullReportSection{background:linear-gradient(145deg,#101e39,#0b1730)}
#availabilityView .stat{background:#0a1730}
@media(min-width:1050px){#dashboardContent{grid-template-columns:1fr 1fr}.dashboard-card.span-two{grid-column:1/-1}}
@media(max-width:900px){header{flex-wrap:wrap}.header-status{border-left:0;padding:0;min-width:0}.brand-copy{min-width:180px}}
@media(max-width:650px){header{padding:17px 14px;gap:12px}.brand-mark{width:54px;height:54px;flex-basis:54px;border-width:3px;font-size:31px}.brand-copy{min-width:0}header h1{font-size:22px}.header-status{width:100%}.header-actions{width:100%}.header-actions button{flex:1}main{padding:13px 10px 22px}.panel{padding:14px}.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.stat{padding:10px}.stat-value{font-size:17px}.menu{justify-content:flex-start;gap:3px}.menu button{flex:1 1 auto;padding:9px 10px;font-size:12px}.dashboard-card{padding:13px}.dashboard-card .grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:360px){.grid,.dashboard-card .grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<header>
<div class="brand-mark" aria-hidden="true">π</div>
<div class="brand-copy">
<h1>Pi Network Node Monitor</h1>
<div class="small">Pi Desktop 0.6.4 · SoloHost</div>
</div>
<div class="header-status">
<b id="connection">WAITING FOR NODE</b>
<div class="small" id="lastReport">No report loaded yet</div>
</div>
<div class="header-actions">
<button onclick="loadStatus()">↻ Refresh now</button>
<button class="secondary" onclick="toggleFullReport()">▤ Show full report</button>
</div>
</header>

<main>
<div id="message">Ready. Select a dashboard section.</div>

<nav class="menu" id="menu">
<button data-view="overview" onclick="showView('overview')">Overview</button>
<button data-view="protocol" onclick="showView('protocol')">Protocol</button>
<button data-view="peers" onclick="showView('peers')">Peers</button>
<button data-view="system" onclick="showView('system')">System</button>
<button data-view="explorer" onclick="showView('explorer')">Peers Explorer</button>
<button data-view="availability" onclick="showView('availability')">Availability</button>
<button data-view="logs" onclick="showView('logs')">Docker Logs</button>
</nav>

<section id="dashboardView">
<div class="panel">
<h2 id="viewTitle">Node Overview</h2>
<div id="dashboardContent" class="grid">
<div class="stat">
<div class="stat-label">Node status</div>
<div class="stat-value">Waiting</div>
</div>
</div>
</div>
</section>


<section id="explorerView" class="hidden">
<div class="panel">
<h2>Peers Explorer</h2>
<p class="small">Loads the full output of stellar-core http-command peers.</p>
<button onclick="loadPeers()">Load peers</button>
<button class="danger" onclick="closePeers()">Close peers</button>
<pre id="peers">Click Load peers to load peer information.</pre>
</div>
</section>

<section id="availabilityView" class="hidden">
<div class="panel">
<h2>Pi Network Availability</h2>
<p class="small">Enter your own Pi Network UUID. It is saved in this browser.</p>
<div class="uuid-row">
<input id="availabilityUuid" type="text" placeholder="Enter your UUID"
autocomplete="off" spellcheck="false">
<button onclick="saveUuid()">Save UUID</button>
<button onclick="loadAvailability()">Refresh availability</button>
</div>
<div id="availabilityMessage" class="small" style="margin-top:10px">
Enter and save your UUID, then refresh availability.
</div>
<div class="grid" style="margin-top:14px">
<div class="stat">
<div class="stat-label">Availability</div>
<div class="stat-value" id="availabilityValue">—</div>
</div>
<div class="stat">
<div class="stat-label">Node start date</div>
<div class="stat-value" id="startDate">—</div>
</div>
<div class="stat">
<div class="stat-label">Date added</div>
<div class="stat-value" id="dateAdded">—</div>
</div>
</div>
</div>
</section>

<section id="dockerLogsView" class="hidden">
<div class="panel">
<h2>Docker Logs · testnet2</h2>
<p class="small">Read-only Supervisor logs from the testnet2 container. Refresh manually to retrieve the latest output.</p>
<div class="uuid-row" style="margin-bottom:12px">
<label for="logService">Service</label>
<select id="logService" style="padding:11px;border:1px solid #cfc6bd;border-radius:7px;background:#fff;font-size:15px">
<option value="horizon">Horizon</option><option value="stellar-core">Stellar Core</option><option value="postgresql">PostgreSQL</option><option value="rpc">RPC</option>
</select>
<label for="logLines">Lines</label>
<select id="logLines" style="padding:11px;border:1px solid #cfc6bd;border-radius:7px;background:#fff;font-size:15px">
<option>100</option><option>250</option><option selected>500</option><option>1000</option>
</select>
<button onclick="loadLogs()">Refresh logs</button>
</div>
<input id="logSearch" type="text" placeholder="Filter logs (ERROR, WARN, INFO...)" oninput="filterLogs()" style="width:min(100%,520px);margin-bottom:10px">
<div id="logsMessage" class="small">Select a service and click Refresh logs.</div>
<pre id="logsOutput">No logs loaded.</pre>
</div>
</section>

<section id="fullReportSection" class="panel hidden">
<h2>Complete node-status report</h2>
<pre id="fullReport">No report loaded.</pre>
</section>

<footer>Pi Network Node Monitor · SoloHost · Community-built dashboard · Not affiliated with Pi Network.</footer>
</main>

<script>
const names=["horizon","postgresql","stellar-core","rpc"];
const UUID_KEY="pi-node-monitor-availability-uuid";
const LAST_VIEW_KEY="pi-node-monitor-last-view";

let lastView="overview";
let reportText="";
let reportSections={};
let reportTime="";
let availabilityStats={};
let availabilityUuid="";
let rawLogText="";

function msg(s){
 document.getElementById("message").textContent=s;
}

async function api(path,method="GET"){
 const r=await fetch(path,{
  method,
  headers:{"Content-Type":"application/json"}
 });
 let d={};
 try{d=await r.json()}catch(e){}
 if(!r.ok||d.ok===false){
  throw Error(d.error||("HTTP "+r.status));
 }
 return d;
}

function setLastView(view){
 lastView=view;
 localStorage.setItem(LAST_VIEW_KEY,view);
}

function showView(view){
  if(!["overview","protocol","peers","system","explorer","availability","logs"].includes(view))view="overview";
  setLastView(view);
  document.getElementById("dashboardView").classList.toggle(
   "hidden", !["overview","protocol","peers","system"].includes(view)
  );
  document.getElementById("explorerView").classList.toggle("hidden",view!=="explorer");
  document.getElementById("availabilityView").classList.toggle("hidden",view!=="availability");
  document.getElementById("dockerLogsView").classList.toggle("hidden",view!=="logs");
  document.querySelectorAll("#menu button").forEach(b=>{
   b.classList.toggle("active",b.dataset.view===view);
  });
  const titles={overview:"Node Overview",protocol:"Protocol & Horizon",peers:"Peer Connections",system:"System Resources"};
  if(titles[view]){
   document.getElementById("viewTitle").textContent=titles[view];
   renderDashboard(view);
  }
  if(view==="logs" && !rawLogText)document.getElementById("logsMessage").textContent="Select a service and click Refresh logs.";
}

function parseReport(text){
 const result={};
 let current="";

 text.split(/\r?\n/).forEach(line=>{
  const heading=line.match(/^\s*===\s*(.*?)\s*===\s*$/);
  if(heading){
   current=heading[1].trim();
   result[current]=[];
   return;
  }

  if(!current||!line.trim())return;

  const cleaned=line.trim();
  const match=cleaned.match(/^([^:]+):\s*(.*)$/);

  if(match){
   result[current].push({
    label:match[1].trim(),
    value:match[2].trim()
   });
  }else{
   result[current].push({
    label:"",
    value:cleaned
   });
  }
 });

 return result;
}

function findValue(section,label){
 const rows=reportSections[section]||[];
 const row=rows.find(x=>x.label.toLowerCase()===label.toLowerCase());
 return row?row.value:"—";
}

function addStat(root,label,value,detail=""){
 const card=document.createElement("div");
 card.className="stat";

 const l=document.createElement("div");
 l.className="stat-label";
 l.textContent=label;

 const v=document.createElement("div");
 v.className="stat-value";
 v.textContent=value||"—";

 const status=String(value||"").toLowerCase();
 const field=String(label||"").toLowerCase();

 if(
  status.includes("synced") ||
  status.includes("running") ||
  status.includes("connected") ||
  status==="healthy"
 ){
  card.classList.add("status-good");
 }else if(
  status.includes("stopped") ||
  status.includes("failed") ||
  status.includes("error") ||
  status.includes("disconnected") ||
  status.includes("not started")
 ){
  card.classList.add("status-bad");
 }else if(
  status.includes("pending") ||
  status.includes("warning") ||
  status.includes("catching up") ||
  field.includes("pending")
 ){
  card.classList.add("status-warn");
 }

 card.append(l,v);

 if(detail){
  const d=document.createElement("div");
  d.className="stat-detail";
  d.textContent=detail;
  card.append(d);
 }

 root.append(card);
}

function renderRows(root,section){
 const rows=reportSections[section]||[];

 if(!rows.length){
  addStat(root,"Report section","Not available");
  return;
 }

 rows.forEach(row=>{
  addStat(root,row.label||"Information",row.value||"—");
 });
}

function renderDashboard(view){
 const root=document.getElementById("dashboardContent");
 root.replaceChildren();
 root.style.display="grid";
 if(!reportText){
  const empty=document.createElement("div");empty.className="dashboard-card span-two";
  addStat(empty,"Node status","Waiting for node report");root.append(empty);return;
 }
 function addGroup(title,section,wide=false){
  const card=document.createElement("section");card.className="dashboard-card"+(wide?" wide":"");
  const heading=document.createElement("h2");heading.textContent=title;card.append(heading);
  const group=document.createElement("div");group.className="grid";renderRows(group,section);card.append(group);root.append(card);
 }
 if(view==="overview"){
  addGroup("Node Overview","Protocol");
  addOverviewAvailabilityGroup();
  addServiceOverviewGroup();
  addGroup("Peer Connections","Peers");
  addGroup("System Resources","System");
  addGroup("Horizon Details","Horizon",true);
 }else if(view==="protocol"){
  addGroup("Protocol","Protocol");addGroup("Horizon Details","Horizon",true);
 }else if(view==="peers"){
  addGroup("Peer Connections","Peers",true);
 }else if(view==="system"){
  addGroup("System Resources","System",true);
 }
}

function addOverviewAvailabilityGroup(){
 const root=document.getElementById("dashboardContent");
 const card=document.createElement("section");card.className="dashboard-card";
 const heading=document.createElement("h2");heading.textContent="Node Availability";card.append(heading);
 const tools=document.createElement("div");tools.className="uuid-row";
 const input=document.createElement("input");input.id="overviewUuid";input.type="text";input.placeholder="Pi Network UUID";input.autocomplete="off";input.spellcheck=false;input.value=availabilityUuid||document.getElementById("availabilityUuid").value;
 const save=document.createElement("button");save.textContent="Save UUID";save.onclick=()=>{document.getElementById("availabilityUuid").value=input.value;saveUuid();availabilityUuid=input.value.trim();hint.textContent="UUID saved in this browser";};
 const refresh=document.createElement("button");refresh.textContent="Refresh";refresh.onclick=()=>{document.getElementById("availabilityUuid").value=input.value;loadAvailability();};
 tools.append(input,save,refresh);card.append(tools);
 const hint=document.createElement("div");hint.className="small";hint.textContent=availabilityUuid?"UUID saved":"Enter your UUID to load Pi Network availability";card.append(hint);
 const cards=document.createElement("div");cards.className="grid";cards.style.marginTop="12px";
 addStat(cards,"Availability",availabilityStats.availability||"Not loaded");
 addStat(cards,"Node start date",availabilityStats.user_start_date||"—");
 addStat(cards,"Date added",availabilityStats.date_added||"—");
 card.append(cards);root.append(card);
}

function addServiceOverviewGroup(){
 const root=document.getElementById("dashboardContent");
 const card=document.createElement("section");card.className="dashboard-card";
 const heading=document.createElement("h2");heading.textContent="Service Manager";card.append(heading);
 const group=document.createElement("div");group.className="grid";
 const rows=reportSections["Services"]||[];
 for(const name of names){
  let statusText="Status unavailable";
  let row=rows.find(x=>String(x.label||"").toLowerCase()===name);
  if(row)statusText=row.value||"Status unavailable";
  else{
   const index=rows.findIndex(x=>String(x.value||"").trim().toLowerCase()===name);
   if(index>=0)statusText=rows[index+1]?.value||"Status unavailable";
   else{row=rows.find(x=>String(x.value||"").toLowerCase().startsWith(name+" "));if(row)statusText=row.value.substring(name.length).trim();}
  }
  const stateMatch=statusText.match(/\b(RUNNING|STOPPED|STARTING|STOPPING|FATAL|EXITED)\b/i);
  const state=stateMatch?stateMatch[1].toUpperCase():"UNKNOWN";
  const div=document.createElement("div");div.className="service";
  const title=document.createElement("b");title.textContent=name.replace("stellar-core","Stellar Core").replace("postgresql","PostgreSQL");div.append(title);
  const status=document.createElement("div");status.className="small";status.textContent=statusText;
  if(state==="RUNNING")status.classList.add("good");if(["STOPPED","FATAL","EXITED"].includes(state))status.classList.add("bad");div.append(status);
  const actions=document.createElement("div");actions.className="service-actions";
  for(const action of ["start","restart"]){
   const b=document.createElement("button");b.textContent=action==="start"?"▶ Start":"↻ Restart";
   if(state==="RUNNING"&&action==="start")b.disabled=true;
   b.onclick=()=>serviceOne(name,action);actions.append(b);
  }
  div.append(actions);group.append(div);
 }
 card.append(group);
 const all=document.createElement("div");all.className="service-actions";all.style.marginTop="12px";
 const start=document.createElement("button");start.textContent="▶ Start All";start.onclick=()=>serviceAll("start");
 const restart=document.createElement("button");restart.className="secondary";restart.textContent="↻ Restart All";restart.onclick=()=>serviceAll("restart");
 all.append(start,restart);card.append(all);root.append(card);
}

async function loadStatus(){
 msg("Loading complete node-status report...");

 try{
  const d=await api("/api/status");
  reportText=d.status||d.output||"";

  if(!reportText){
   throw Error("The helper returned an empty node-status report.");
  }

  reportSections=parseReport(reportText);
  reportTime=new Date().toLocaleString();

  document.getElementById("connection").textContent="Connected · testnet2";
  document.getElementById("lastReport").textContent="Last report: "+reportTime;
  document.getElementById("fullReport").textContent=reportText;

  if(["overview","protocol","peers","system"].includes(lastView))renderDashboard(lastView);
  msg("Node status updated.");
  return true;
 }catch(e){
  msg("Node status error: "+e.message);
  document.getElementById("connection").textContent="Connection or report error";
  return false;
 }
}

function toggleFullReport(){
 const el=document.getElementById("fullReportSection");
 el.classList.toggle("hidden");
 if(!el.classList.contains("hidden")){
  document.getElementById("fullReport").textContent=reportText||"No report loaded.";
 }
}

async function serviceOne(name,action){
 if(!confirm(action.toUpperCase()+" "+name+"?"))return;

 msg(action+" "+name+"...");

 try{
  const d=await api("/api/service/"+name+"/"+action,"POST");
  msg(d.output||"Command completed. Updating service status...");

  await loadStatus();

  msg(name+" "+action+" command completed. Status refreshed.");
 }catch(e){
  msg("Service action error: "+e.message);
 }
}

async function serviceAll(action){
 const warning=action==="restart"
  ?"Restart ALL Supervisor services? This may interrupt node services."
  :action==="stop"
  ?"STOP ALL Supervisor services? This will interrupt node operation."
  :"Start all Supervisor services?";

 if(!confirm(warning))return;
 msg(action+" all services...");
 try{
  const d=await api("/api/services/"+action,"POST");
  msg(d.output||"Command completed. Refreshing status...");
  await loadStatus();
 }catch(e){
  msg("Error: "+e.message);
 }
}

async function loadPeers(){
 setLastView("explorer");
 document.getElementById("explorerView").classList.remove("hidden");
 document.getElementById("dashboardView").classList.add("hidden");
 document.getElementById("availabilityView").classList.add("hidden");

 document.querySelectorAll("#menu button").forEach(b=>{
  b.classList.toggle("active",b.dataset.view==="explorer");
 });

 msg("Loading peer information...");
 document.getElementById("peers").textContent="Loading peers...";

 try{
  const d=await api("/api/peers");
  document.getElementById("peers").textContent=d.output||JSON.stringify(d,null,2);
  msg("Peer information loaded.");
 }catch(e){
  document.getElementById("peers").textContent="Unable to load peers: "+e.message;
  msg("Peers error: "+e.message);
 }
}

function closePeers(){
 document.getElementById("explorerView").classList.add("hidden");
 document.getElementById("peers").textContent="Click Load peers to load peer information.";
 showView("overview");
 msg("Peers Explorer closed.");
}

function isUuid(value){
 return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}

function saveUuid(){
 const input=document.getElementById("availabilityUuid");
 const value=input.value.trim();

 if(!isUuid(value)){
  document.getElementById("availabilityMessage").textContent="Please enter a valid UUID.";
  return;
 }

 input.value=value;
 localStorage.setItem(UUID_KEY,value);
 document.getElementById("availabilityMessage").textContent="UUID saved in this browser.";
 msg("Availability UUID saved.");
}

async function loadAvailability(){
 const uuidValue=document.getElementById("availabilityUuid").value.trim();

 if(!isUuid(uuidValue)){
  document.getElementById("availabilityMessage").textContent="Enter a valid UUID before refreshing availability.";
  return;
 }

 localStorage.setItem(UUID_KEY,uuidValue);
 document.getElementById("availabilityMessage").textContent="Loading Pi Network availability...";

 try{
  const d=await api("/api/availability?uuid="+encodeURIComponent(uuidValue));
  const stats=d.stats||{};
  const availability=Number(stats.availability);

  document.getElementById("availabilityValue").textContent=
   Number.isFinite(availability)?(availability*100).toFixed(2)+"%":"Unavailable";
  document.getElementById("startDate").textContent=stats.user_start_date||"—";
  document.getElementById("dateAdded").textContent=stats.date_added||"—";
  availabilityStats={
   availability:Number.isFinite(availability)?(availability*100).toFixed(2)+"%":"Unavailable",
   user_start_date:stats.user_start_date||"—",
   date_added:stats.date_added||"—"
  };
  availabilityUuid=uuidValue;
  if(lastView==="overview")renderDashboard("overview");
  document.getElementById("availabilityMessage").textContent="Pi Network availability data updated.";
  msg("Pi Network availability updated.");
 }catch(e){
  document.getElementById("availabilityMessage").textContent="Could not load availability: "+e.message;
  msg("Availability error: "+e.message);
 }
}

async function refreshLastView(){
  const view=localStorage.getItem(LAST_VIEW_KEY)||lastView;
  if(view==="explorer"){
   await loadPeers();
  }else if(view==="availability"){
   await loadAvailability();
  }else if(view==="logs"){
   await loadLogs();
  }else{
   await loadStatus();
   showView(view);
  }
}

function filterLogs(){
  const term=(document.getElementById("logSearch").value||"").toLowerCase();
  const filtered=term?rawLogText.split(/\r?\n/).filter(line=>line.toLowerCase().includes(term)).join("\n"):rawLogText;
  document.getElementById("logsOutput").textContent=filtered||"No matching log lines.";
}

async function loadLogs(){
  const service=document.getElementById("logService").value;
  const lines=document.getElementById("logLines").value;
  document.getElementById("logsMessage").textContent="Loading "+service+" logs...";
  document.getElementById("logsOutput").textContent="Loading...";
  try{
   const d=await api("/api/logs?service="+encodeURIComponent(service)+"&lines="+encodeURIComponent(lines));
   rawLogText=d.output||"";
   document.getElementById("logsMessage").textContent=d.message||("Loaded "+service+" logs · "+lines+" lines requested");
   filterLogs();
   msg("Docker logs updated for "+service+".");
  }catch(e){
   rawLogText="";
   document.getElementById("logsOutput").textContent="Unable to load logs: "+e.message;
   document.getElementById("logsMessage").textContent="Log request failed.";
   msg("Docker logs error: "+e.message);
  }
}

window.addEventListener("DOMContentLoaded",()=>{
 const saved=localStorage.getItem(UUID_KEY);
 if(saved){document.getElementById("availabilityUuid").value=saved;availabilityUuid=saved;}

 const savedView=localStorage.getItem(LAST_VIEW_KEY);
 if(savedView)lastView=savedView;

 showView(lastView);
 loadStatus();
});
</script>
</body>
</html>"""


def helper_request(path, method="GET"):
    req = urllib.request.Request(
        HELPER + path,
        method=method,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            data = json.loads(e.read().decode("utf-8"))
            return {"ok": False, "error": data.get("error", str(e))}
        except Exception:
            return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def fetch_availability(user_uuid):
    try:
        uuid.UUID(user_uuid)
    except (ValueError, AttributeError):
        return {"ok": False, "error": "Invalid UUID format"}

    url = AVAILABILITY_URL + quote(user_uuid, safe="")
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Pi-Node-Monitor"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        stats = data.get("stats")
        if not isinstance(stats, dict):
            return {"ok": False, "error": "Pi Network returned no availability stats"}
        return {"ok": True, "stats": stats}
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": "Pi Network HTTP " + str(e.code)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


class Handler(BaseHTTPRequestHandler):

    def authorized(self):
        if not DASH_USER and not DASH_PASS:
            return True

        supplied = self.headers.get("Authorization", "")
        if not supplied.startswith("Basic "):
            return False

        try:
            decoded = base64.b64decode(supplied.split(" ", 1)[1]).decode()
            user, password = decoded.split(":", 1)
            return (
                hmac.compare_digest(user, DASH_USER)
                and hmac.compare_digest(password, DASH_PASS)
            )
        except Exception:
            return False

    def send_data(self, code, data, content_type="application/json; charset=utf-8"):
        body = data if isinstance(data, bytes) else json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.authorized():
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="Pi Node Monitor"')
            self.end_headers()
            return

        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            return self.send_data(200, HTML.encode("utf-8"), "text/html; charset=utf-8")

        if path == "/health":
            return self.send_data(200, {"ok": True})

        if path == "/api/availability":
            values = parse_qs(parsed.query).get("uuid", [])
            if not values:
                return self.send_data(400, {"ok": False, "error": "UUID is required"})
            result = fetch_availability(values[0].strip())
            return self.send_data(200 if result.get("ok") else 502, result)

        if path == "/api/logs":
            params = parse_qs(parsed.query)
            service = (params.get("service", [""])[0] or "").strip()
            lines = (params.get("lines", ["500"])[0] or "500").strip()
            if service not in ("horizon", "stellar-core", "postgresql", "rpc"):
                return self.send_data(400, {"ok": False, "error": "Invalid service"})
            if lines not in ("100", "250", "500", "1000"):
                return self.send_data(400, {"ok": False, "error": "Invalid line count"})
            result = helper_request("/logs?service=" + quote(service) + "&lines=" + quote(lines))
            return self.send_data(200 if result.get("ok") else 502, result)

        routes = {
            "/api/status": "/status",
            "/api/services": "/services",
            "/api/peers": "/peers"
        }
        if path in routes:
            result = helper_request(routes[path])
            return self.send_data(200 if result.get("ok") else 502, result)

        return self.send_data(404, {"ok": False, "error": "Not found"})

    def do_POST(self):
        if not self.authorized():
            return self.send_data(401, {"ok": False, "error": "Unauthorized"})

        path = urlparse(self.path).path
        parts = path.strip("/").split("/")

        if len(parts) == 4 and parts[:2] == ["api", "service"]:
            service, action = parts[2], parts[3]

            if service not in ("horizon", "postgresql", "stellar-core", "rpc"):
                return self.send_data(400, {"ok": False, "error": "Invalid service"})

            if action not in ("start", "stop", "restart"):
                return self.send_data(400, {"ok": False, "error": "Invalid action"})

            result = helper_request("/service/" + service + "/" + action, "POST")
            return self.send_data(200 if result.get("ok") else 502, result)

        if path in (
            "/api/services/start",
            "/api/services/stop",
            "/api/services/restart"
        ):
            action = path.rsplit("/", 1)[1]
            result = helper_request("/services/" + action, "POST")
            return self.send_data(200 if result.get("ok") else 502, result)

        return self.send_data(404, {"ok": False, "error": "Not found"})

    def log_message(self, fmt, *args):
        print("[Pi Node Monitor] " + (fmt % args), flush=True)


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("NODE_STATUS_TOKEN is missing")

    print("Pi Node Monitor starting on port", PORT, flush=True)

    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
