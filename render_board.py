#!/usr/bin/env python3
# render_board.py — 从 board.json 渲染公网版看板 dist/index.html
# 用法: python3 render_board.py [board.json 路径] [输出路径]
import json, sys, pathlib, html as H

ROOT = pathlib.Path(__file__).parent
data_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "board.json"
out_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "dist" / "index.html"

data = json.loads(data_path.read_text(encoding="utf-8"))
payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>悟小空作战指挥室</title>
<style>
:root{
  --bg:#0b0e14; --bg2:#11151f; --card:#151a26; --line:#232a3a; --line2:#2e3648;
  --tx:#e8ecf4; --tx2:#9aa4b8; --tx3:#5d6778;
  --amber:#f5a623; --cyan:#3ec6e0; --green:#34c98e; --red:#f0564d; --violet:#8b7cf6; --gray:#6b768c;
  --mono:"SF Mono",ui-monospace,Menlo,Consolas,monospace;
}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--tx);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;min-height:100vh;background-image:radial-gradient(ellipse 80% 50% at 50% -10%,rgba(62,198,224,.08),transparent),radial-gradient(ellipse 60% 40% at 90% 110%,rgba(245,166,35,.05),transparent)}
.wrap{max-width:1180px;margin:0 auto;padding:40px 24px 80px}
header{display:flex;flex-wrap:wrap;gap:24px;align-items:flex-end;justify-content:space-between;padding-bottom:28px;border-bottom:1px solid var(--line)}
h1{font-size:30px;font-weight:700;letter-spacing:.02em}
h1 .sub{display:block;font-size:13px;font-weight:400;color:var(--tx2);margin-top:6px;letter-spacing:.06em}
.hmeta{text-align:right;font-size:12px;color:var(--tx3);line-height:1.9;font-family:var(--mono)}
.hmeta b{color:var(--tx2);font-weight:500}
.ring-box{display:flex;align-items:center;gap:20px}
.ring{position:relative;width:96px;height:96px;flex:none}
.ring svg{transform:rotate(-90deg)}
.ring .pct{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.ring .pct b{font-size:22px;font-variant-numeric:tabular-nums}
.ring .pct span{font-size:10px;color:var(--tx3)}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;margin:28px 0}
.metric{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.metric .v{font-size:26px;font-weight:700;font-variant-numeric:tabular-nums}
.metric .k{font-size:12px;color:var(--tx3);margin-top:2px}
.timeline{display:flex;gap:0;margin:8px 0 32px;overflow-x:auto;padding-bottom:8px}
.tl-node{flex:1;min-width:120px;position:relative;padding:0 8px}
.tl-node::before{content:"";position:absolute;top:15px;left:0;right:0;height:2px;background:var(--line2)}
.tl-node:first-child::before{left:50%}.tl-node:last-child::before{right:50%}
.tl-dot{position:relative;z-index:1;width:32px;height:32px;margin:0 auto;border-radius:50%;background:var(--bg2);border:2px solid var(--line2);display:flex;align-items:center;justify-content:center;font-size:12px;font-family:var(--mono);color:var(--tx2)}
.tl-node.active .tl-dot{border-color:var(--amber);color:var(--amber);box-shadow:0 0 16px rgba(245,166,35,.35)}
.tl-node.done .tl-dot{border-color:var(--green);background:var(--green);color:#04120c}
.tl-node.done::before{background:var(--green)}
.tl-name{text-align:center;font-size:11px;color:var(--tx2);margin-top:8px;line-height:1.4}
.tl-gate{text-align:center;margin-top:4px}
.gate{display:inline-block;font-size:10px;font-family:var(--mono);padding:2px 8px;border-radius:99px;border:1px solid var(--line2);color:var(--tx3)}
.gate.PASS{color:var(--green);border-color:rgba(52,201,142,.4);background:rgba(52,201,142,.08)}
.gate.FAIL{color:var(--red);border-color:rgba(240,86,77,.4);background:rgba(240,86,77,.08)}
.gate.HOLD{color:var(--amber);border-color:rgba(245,166,35,.4);background:rgba(245,166,35,.08)}
section{margin-top:36px}
h2{font-size:15px;font-weight:600;color:var(--tx2);letter-spacing:.08em;margin-bottom:14px;display:flex;align-items:center;gap:10px}
h2::after{content:"";flex:1;height:1px;background:var(--line)}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}
.chip{border:1px solid var(--line2);background:transparent;color:var(--tx2);font-size:12px;padding:6px 14px;border-radius:99px;cursor:pointer;transition:.15s}
.chip:hover{border-color:var(--tx3);color:var(--tx)}
.chip.on{background:var(--tx);color:#0b0e14;border-color:var(--tx);font-weight:600}
.wave{margin-bottom:22px}
.wave-head{display:flex;align-items:center;gap:12px;margin-bottom:8px}
.wave-head .wn{font-family:var(--mono);font-size:12px;color:var(--amber);border:1px solid rgba(245,166,35,.35);padding:2px 10px;border-radius:8px;background:rgba(245,166,35,.06)}
.wave-head .wt{font-size:14px;font-weight:600}
.wave-head .wp{margin-left:auto;font-family:var(--mono);font-size:12px;color:var(--tx3)}
.wave-bar{height:3px;background:var(--line);border-radius:99px;margin-bottom:10px;overflow:hidden}
.wave-bar i{display:block;height:100%;background:linear-gradient(90deg,var(--green),var(--cyan));border-radius:99px}
.task{display:flex;gap:12px;align-items:flex-start;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin-bottom:8px;transition:.15s;scroll-margin-top:20px}
.task:hover{border-color:var(--line2)}
.task.flash{border-color:var(--amber);box-shadow:0 0 0 2px rgba(245,166,35,.35),0 0 24px rgba(245,166,35,.15)}
.map{display:flex;gap:14px;overflow-x:auto;padding-bottom:10px}
.mwave{flex:none;width:300px;background:var(--bg2);border:1px solid var(--line);border-radius:14px;padding:14px}
.mwave.active{border-color:rgba(245,166,35,.5);box-shadow:0 0 24px rgba(245,166,35,.08)}
.mw-head{display:flex;align-items:center;gap:8px;margin-bottom:12px}
.mw-head .wn2{font-family:var(--mono);font-size:11px;color:var(--amber);font-weight:700}
.mw-head .wt2{font-size:13px;font-weight:600;flex:1;line-height:1.4}
.lanes{display:flex;gap:8px;align-items:flex-start}
.lane{flex:1;min-width:0;display:flex;flex-direction:column;gap:6px}
.lane-tag{font-size:10px;color:var(--tx3);font-family:var(--mono);text-align:center;padding:2px 0;border-bottom:1px dashed var(--line2);margin-bottom:2px}
.lane-para{font-size:9px;color:var(--green);text-align:center;font-family:var(--mono)}
.node{display:block;background:var(--card);border:1px solid var(--line2);border-left-width:3px;border-radius:8px;padding:7px 8px;text-decoration:none;color:var(--tx);transition:.15s;cursor:pointer}
.node:hover{border-color:var(--cyan);transform:translateY(-1px)}
.node .nid{font-family:var(--mono);font-size:10px;color:var(--cyan);display:block}
.node .nti{font-size:11px;line-height:1.4;display:block;margin-top:1px}
.node .ndep{font-size:9px;color:var(--tx3);font-family:var(--mono);display:block;margin-top:2px}
.node.crit{border-left-color:var(--amber)}
.node .own{float:right;font-size:10px;font-weight:600}
.node.DONE{border-left-color:var(--green);opacity:.85}
.node.IN_PROGRESS,.node.CLAIMED{border-left-color:var(--cyan)}
.node.READY{border-left-color:var(--cyan);border-style:solid}
.node.BLOCKED{border-left-color:var(--red)}
.node.READY_FOR_REVIEW,.node.READY_FOR_GATE,.node.OBSERVING{border-left-color:var(--amber)}
.mw-gate{margin-top:10px;text-align:center}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:11px;color:var(--tx3);margin-bottom:14px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:-1px}
.task.crit{border-left:3px solid var(--amber)}
.tid{font-family:var(--mono);font-size:12px;color:var(--cyan);padding-top:3px;width:52px;flex:none}
.tbody{flex:1;min-width:0}
.ttitle{font-size:14px;line-height:1.5}
.tmeta{font-size:11px;color:var(--tx3);margin-top:3px;font-family:var(--mono)}
.tblock{font-size:11px;color:var(--red);margin-top:3px}
.tnote{font-size:11px;color:var(--tx2);margin-top:3px}
.tright{display:flex;flex-direction:column;align-items:flex-end;gap:6px;flex:none}
.pill{font-size:11px;padding:3px 10px;border-radius:99px;white-space:nowrap}
.pill.READY{color:var(--cyan);background:rgba(62,198,224,.1);border:1px solid rgba(62,198,224,.3)}
.pill.CLAIMED,.pill.IN_PROGRESS{color:var(--cyan);background:rgba(62,198,224,.12);border:1px solid rgba(62,198,224,.35)}
.pill.READY_FOR_REVIEW,.pill.READY_FOR_GATE,.pill.OBSERVING{color:var(--amber);background:rgba(245,166,35,.1);border:1px solid rgba(245,166,35,.3)}
.pill.DONE{color:var(--green);background:rgba(52,201,142,.1);border:1px solid rgba(52,201,142,.3)}
.pill.BLOCKED{color:var(--red);background:rgba(240,86,77,.08);border:1px solid rgba(240,86,77,.3)}
.pill.INTAKE,.pill.TRIAGED{color:var(--tx3);background:rgba(107,118,140,.1);border:1px solid var(--line2)}
.avatar{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600}
.avatar.m{background:rgba(62,198,224,.15);color:var(--cyan);border:1px solid rgba(62,198,224,.4)}
.avatar.x{background:rgba(139,124,246,.15);color:var(--violet);border:1px solid rgba(139,124,246,.4)}
.avatar.n{background:transparent;color:var(--tx3);border:1px dashed var(--line2);font-size:10px}
.log li{list-style:none;font-size:12px;color:var(--tx2);padding:8px 0;border-bottom:1px dashed var(--line);line-height:1.6}
.log li b{color:var(--tx3);font-family:var(--mono);font-weight:500;margin-right:8px}
footer{margin-top:48px;padding-top:20px;border-top:1px solid var(--line);font-size:11px;color:var(--tx3);line-height:2}
footer code{font-family:var(--mono);color:var(--tx2)}
@media(max-width:640px){h1{font-size:22px}.hmeta{text-align:left}.tl-name{display:none}}
</style>
</head>
<body>
<div class="wrap" id="app"></div>
<script id="d" type="application/json">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('d').textContent);
const SNAME={INTAKE:'待登记',TRIAGED:'已初判',READY:'可认领',CLAIMED:'已认领',IN_PROGRESS:'进行中',READY_FOR_REVIEW:'待审查',READY_FOR_GATE:'待过门',OBSERVING:'观察中',DONE:'已完成',BLOCKED:'阻塞'};
const GNAME={PENDING:'待评审',PASS:'PASS',FAIL:'FAIL',HOLD:'HOLD'};
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let filter='all';
function av(o){if(o==='敏敏')return '<span class="avatar m" title="敏敏">敏</span>';if(o==='夏天')return '<span class="avatar x" title="夏天">夏</span>';return '<span class="avatar n" title="待认领">—</span>'}
function render(){
const T=D.tasks,G={};(D.gates||[]).forEach(g=>G[g.id]=g);
const c={};T.forEach(t=>c[t.status]=(c[t.status]||0)+1);
const done=c.DONE||0,ready=c.READY||0,wip=(c.CLAIMED||0)+(c.IN_PROGRESS||0),blocked=c.BLOCKED||0,review=(c.READY_FOR_REVIEW||0)+(c.READY_FOR_GATE||0);
const gp=(D.gates||[]).filter(g=>g.status==='PASS').length;
const pct=T.length?Math.round(done/T.length*100):0;
const R=2*Math.PI*42;
let h=`<header><div class="ring-box"><div class="ring"><svg width="96" height="96"><circle cx="48" cy="48" r="42" fill="none" stroke="#232a3a" stroke-width="6"/><circle cx="48" cy="48" r="42" fill="none" stroke="#3ec6e0" stroke-width="6" stroke-linecap="round" stroke-dasharray="${R}" stroke-dashoffset="${R*(1-pct/100)}"/></svg><div class="pct"><b>${pct}%</b><span>${done}/${T.length} 任务</span></div></div>
<div><h1>悟小空作战指挥室<span class="sub">系统修复实施计划 v1.2 · 夏天确认版 · 数据以 GitHub 为准</span></h1></div></div>
<div class="hmeta">当前波次 <b>Wave ${D.meta.currentWave}</b><br>基线 <b>${esc((D.meta.baselineSha||'').slice(0,7))}</b> · 更新 <b>${esc(D.meta.updatedAt)}</b><br>同步 <b>${esc(D.meta.syncedAt||D.meta.updatedAt)}</b> by ${esc(D.meta.updatedBy)}</div></header>`;
h+=`<div class="metrics">
<div class="metric"><div class="v" style="color:var(--cyan)">${ready}</div><div class="k">READY 可认领</div></div>
<div class="metric"><div class="v" style="color:var(--cyan)">${wip}</div><div class="k">WIP 在制</div></div>
<div class="metric"><div class="v" style="color:var(--amber)">${review}</div><div class="k">待审查 / 过门</div></div>
<div class="metric"><div class="v" style="color:var(--red)">${blocked}</div><div class="k">阻塞</div></div>
<div class="metric"><div class="v" style="color:var(--green)">${gp}<span style="font-size:14px;color:var(--tx3)">/8</span></div><div class="k">Wave Gate 通过</div></div></div>`;
h+=`<section><h2>波次时间线</h2><div class="timeline">`;
(D.waves||[]).forEach(w=>{const g=G[w.gate]||{status:'PENDING'};const cls=g.status==='PASS'?'done':(w.id===D.meta.currentWave?'active':'');
h+=`<div class="tl-node ${cls}"><div class="tl-dot">W${w.id}</div><div class="tl-name">${esc(w.name)}</div><div class="tl-gate"><span class="gate ${g.status}">${w.gate} ${GNAME[g.status]||g.status}</span></div></div>`});
h+=`</div></section>`;
const BYID={};T.forEach(t=>BYID[t.id]=t);
h+=`<section><h2>波次作战图 · 并行泳道与依赖</h2><div class="legend"><span><i style="background:var(--cyan)"></i>可认领/进行中</span><span><i style="background:var(--amber)"></i>待审查/过门</span><span><i style="background:var(--red)"></i>阻塞</span><span><i style="background:var(--green)"></i>已完成</span><span><i style="background:transparent;border:2px solid var(--amber)"></i>左金条=关键路径</span><span>并排泳道=可并行 · ⟵=波内前置 · 点节点跳转任务卡</span></div><div class="map">`;
(D.waves||[]).forEach(w=>{
const wt=T.filter(t=>t.wave===w.id);const g=G[w.gate]||{status:'PENDING'};
const lanes={};wt.forEach(t=>{const L=(t.group||'?').replace(/[0-9]+$/,'');(lanes[L]=lanes[L]||[]).push(t)});
h+=`<div class="mwave ${w.id===D.meta.currentWave?'active':''}"><div class="mw-head"><span class="wn2">W${w.id}</span><span class="wt2">${esc(w.name)}</span></div><div class="lanes">`;
Object.keys(lanes).sort().forEach(L=>{
h+=`<div class="lane"><div class="lane-tag">${L} 组</div>${Object.keys(lanes).length>1?'<div class="lane-para">‖ 并行</div>':''}`;
lanes[L].forEach(t=>{
const inw=(t.deps||[]).filter(d=>BYID[d]&&BYID[d].wave===w.id);
const oc=t.owner==='敏敏'?'<span class="own" style="color:var(--cyan)">敏</span>':t.owner==='夏天'?'<span class="own" style="color:var(--violet)">夏</span>':'';
h+=`<a class="node ${t.status} ${t.critical?'crit':''}" data-jump="${t.id}">${oc}<span class="nid">${t.id}</span><span class="nti">${esc(t.title)}</span>${inw.length?`<span class="ndep">⟵ ${inw.join(' ')}</span>`:''}</a>`});
h+=`</div>`});
h+=`</div><div class="mw-gate"><span class="gate ${g.status}" title="${esc(g.rule||'')}">出口 ${w.gate} · ${GNAME[g.status]||g.status}</span></div></div>`});
h+=`</div></section>`;
h+=`<section><h2>工作包</h2><div class="filters">`;
[['all','全部'],['敏敏','敏敏'],['夏天','夏天'],['none','待认领'],['crit','关键路径'],['active','在制 / 待审'],['blocked','阻塞']].forEach(f=>{h+=`<button class="chip ${filter===f[0]?'on':''}" data-f="${f[0]}">${f[1]}</button>`});
h+=`</div>`;
(D.waves||[]).forEach(w=>{
const wt=T.filter(t=>{if(t.wave!==w.id)return false;
if(filter==='none')return !t.owner;if(filter==='crit')return t.critical;
if(filter==='active')return ['CLAIMED','IN_PROGRESS','READY_FOR_REVIEW','READY_FOR_GATE','OBSERVING'].includes(t.status);
if(filter==='blocked')return t.status==='BLOCKED';
if(filter==='all')return true;return t.owner===filter});
if(!wt.length)return;
const wd=wt.filter(t=>t.status==='DONE').length,wp=wt.length?Math.round(wd/wt.length*100):0;
const g=G[w.gate]||{status:'PENDING'};
h+=`<div class="wave"><div class="wave-head"><span class="wn">WAVE ${w.id}</span><span class="wt">${esc(w.name)}</span><span class="gate ${g.status}" title="${esc(g.rule||'')}">${w.gate} · ${GNAME[g.status]||g.status}</span><span class="wp">${wd}/${wt.length}</span></div><div class="wave-bar"><i style="width:${wp}%"></i></div>`;
wt.forEach(t=>{
const dur=t.claimedAt&&t.doneAt?Math.max(0,Math.round((new Date(t.doneAt)-new Date(t.claimedAt))/86400000)):null;
const times=[t.claimedAt?`认领 ${t.claimedAt}`:'',t.doneAt?`完成 ${t.doneAt}`:'',dur!==null?`耗时 ${dur}d`:'',t.status==='BLOCKED'&&t.blockedAt?`阻塞自 ${t.blockedAt}`:''].filter(Boolean).join(' · ');
h+=`<div class="task ${t.critical?'crit':''}" id="task-${t.id}"><span class="tid">${esc(t.id)}</span><span class="tbody"><div class="ttitle">${esc(t.title)}${t.critical?' <span style="font-size:10px;color:var(--amber)">◆ 关键路径</span>':''}</div><div class="tmeta">${esc(t.s)} · ${esc(t.p)}${t.deps&&t.deps.length?' · 前置 '+esc(t.deps.join(' ')):""}${t.ghIssue?` · <span style="color:var(--cyan)">#${t.ghIssue}</span>`:''}</div>${times?`<div class="tmeta" style="color:var(--tx2)">⏱ ${esc(times)}</div>`:''}${t.status==='BLOCKED'&&t.blocker?`<div class="tblock">⊘ ${esc(t.blocker)}</div>`:''}${t.note?`<div class="tnote">✎ ${esc(t.note)}</div>`:''}</span><span class="tright"><span class="pill ${t.status}">${SNAME[t.status]||t.status}</span><span style="display:flex;gap:4px;align-items:center">${av(t.owner)}${t.reviewer?`<span style="font-size:10px;color:var(--tx3)">审</span>`+av(t.reviewer):''}</span></span></div>`});
h+=`</div>`});
h+=`</section>`;
if(D.log&&D.log.length){h+=`<section><h2>变更记录</h2><ul class="log">`;D.log.slice(-10).reverse().forEach(l=>{h+=`<li><b>${esc(l.at)}</b>${esc(l.by)} · ${esc(l.what)}</li>`});h+=`</ul></section>`}
h+=`<footer>只读看板 · 事实源：<code>github.com/mingminwang962-eng/ip-system-runtime</code> 的 Issue / PR / Milestone<br>${esc(D.meta.productionBoundary)}<br>修改请通过 GitHub 任务流进行，本页由同步脚本自动重建</footer>`;
document.getElementById('app').innerHTML=h;
document.querySelectorAll('[data-f]').forEach(b=>b.onclick=()=>{filter=b.dataset.f;render()});
document.querySelectorAll('[data-jump]').forEach(n=>n.onclick=e=>{e.preventDefault();const el=document.getElementById('task-'+n.dataset.jump);if(!el)return;el.scrollIntoView({behavior:'smooth',block:'center'});el.classList.add('flash');setTimeout(()=>el.classList.remove('flash'),1600)});
}
render();
</script>
</body>
</html>
"""

out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(TEMPLATE.replace("__DATA__", payload), encoding="utf-8")
print(f"rendered -> {out_path} ({out_path.stat().st_size} bytes, {len(data['tasks'])} tasks)")
