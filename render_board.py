#!/usr/bin/env python3
# render_board.py — 从 board.json 渲染公网版看板 dist/index.html
# 用法: python3 render_board.py [board.json 路径] [输出路径]
import json, sys, pathlib

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
  --bg:#f6f7f9; --card:#ffffff; --line:#e7e9ee; --line2:#dde0e7;
  --tx:#16181d; --tx2:#5f6673; --tx3:#9aa1ad;
  --blue:#2563eb; --green:#059669; --red:#dc2626; --amber:#d97706; --violet:#7c6cf0; --indigo:#4f46e5;
  --mono:"SF Mono",ui-monospace,Menlo,Consolas,monospace;
  --shadow:0 1px 2px rgba(16,24,40,.04),0 1px 3px rgba(16,24,40,.03);
}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--tx);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;line-height:1.6}
.wrap{max-width:1060px;margin:0 auto;padding:48px 28px 96px}

/* header */
header{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-end;justify-content:space-between;padding-bottom:32px}
h1{font-size:26px;font-weight:650;letter-spacing:.01em}
h1 .sub{display:block;font-size:13px;font-weight:400;color:var(--tx3);margin-top:6px}
.hmeta{font-size:12px;color:var(--tx3);text-align:right;line-height:2}
.hmeta b{color:var(--tx2);font-weight:500}

/* preparation + freshness */
.preparation{background:#fff;border:1px solid #dcd8f6;border-radius:16px;padding:24px;margin-bottom:28px;box-shadow:var(--shadow)}
.preparation h2{margin-bottom:8px;color:var(--indigo)}
.preparation h3{font-size:21px;font-weight:600;margin-bottom:12px}
.prep-counts{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}
.prep-counts span{background:#f4f3fc;border-radius:8px;padding:8px 12px;font-size:13px;color:var(--tx2)}
.prep-counts b{color:var(--indigo);font-size:20px;margin-right:5px}
.prep-detail{font-size:12px;color:var(--tx2);line-height:1.9}
.prep-detail a{color:var(--blue);text-decoration:none;margin-right:14px}
.steps{display:flex;gap:8px;flex-wrap:wrap;font-size:12px;color:var(--tx3);margin:14px 0}.steps b{color:var(--indigo)}
.freshness{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:-12px 0 24px;font-size:12px;color:var(--tx2)}
.freshness.warn{color:var(--amber)}.freshness button{border:1px solid var(--line2);background:white;border-radius:8px;padding:6px 12px;cursor:pointer}
.pill.PLANNED{color:var(--tx2);background:#f1f2f5}
/* metrics */
.metrics{display:flex;gap:0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);margin-bottom:40px}
.metric{flex:1;padding:20px 8px;text-align:center}
.metric+.metric{border-left:1px solid var(--line)}
.metric .v{font-size:28px;font-weight:650;font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.metric .k{font-size:12px;color:var(--tx3);margin-top:2px}

/* timeline */
.timeline-note{font-size:12px;color:var(--tx2);margin:-8px 0 14px}
.timeline{display:flex;gap:0;margin-bottom:20px;overflow-x:auto;padding:4px 2px 12px}
.tl-node{flex:1;min-width:150px;position:relative;padding:0 8px}
.tl-node::before{content:"";position:absolute;top:14px;left:0;right:0;height:2px;background:var(--line2)}
.tl-node:first-child::before{left:50%}.tl-node:last-child::before{right:50%}
.tl-dot{position:relative;z-index:1;width:28px;height:28px;margin:0 auto;border-radius:50%;background:#fff;border:2px solid var(--line2);display:flex;align-items:center;justify-content:center;font-size:11px;font-family:var(--mono);color:var(--tx3)}
.tl-node.active .tl-dot{border-color:var(--indigo);color:var(--indigo);box-shadow:0 0 0 4px rgba(79,70,229,.1)}
.tl-node.done .tl-dot{border-color:var(--green);background:var(--green);color:#fff}
.tl-node.done::before{background:var(--green)}
.tl-name{text-align:center;font-size:11px;color:var(--tx2);margin-top:8px;line-height:1.5}
.tl-count{text-align:center;font-size:10px;color:var(--tx3);margin-top:5px;line-height:1.5}
.tl-node.active .tl-count{color:var(--indigo)}
.tl-gate{text-align:center;margin-top:4px}
.gate{display:inline-block;font-size:10px;font-family:var(--mono);padding:2px 9px;border-radius:99px;border:1px solid var(--line2);color:var(--tx3);background:#fff}
.gate.PASS{color:var(--green);border-color:#bbe5d2;background:#f0faf5}
.gate.FAIL{color:var(--red);border-color:#f3c2bf;background:#fef3f2}
.gate.HOLD{color:var(--amber);border-color:#f0dcb4;background:#fffaf0}

/* sections */
section{margin-bottom:48px}
h2{font-size:13px;font-weight:600;color:var(--tx3);letter-spacing:.12em;margin-bottom:16px;text-transform:uppercase}

/* battle map */
.legend{display:flex;flex-wrap:wrap;gap:16px;font-size:11px;color:var(--tx3);margin-bottom:16px}
.legend i{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;vertical-align:0}
.map{display:flex;gap:14px;overflow-x:auto;padding:2px 2px 14px}
.mwave{flex:none;width:288px;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px;box-shadow:var(--shadow)}
.mwave.active{border-color:#c7c3f5;box-shadow:0 0 0 3px rgba(79,70,229,.07),var(--shadow)}
.mw-head{display:flex;align-items:baseline;gap:8px;margin-bottom:14px}
.mw-head .wn2{font-family:var(--mono);font-size:11px;color:var(--indigo);font-weight:700}
.mw-head .wt2{font-size:13px;font-weight:600;flex:1;line-height:1.5}
.lanes{display:flex;gap:8px;align-items:flex-start}
.lane{flex:1;min-width:0;display:flex;flex-direction:column;gap:6px}
.lane-tag{font-size:10px;color:var(--tx3);font-family:var(--mono);text-align:center;padding-bottom:6px;border-bottom:1px dashed var(--line)}
.node{display:block;background:#fafbfc;border:1px solid var(--line);border-radius:10px;padding:8px 9px;text-decoration:none;color:var(--tx);transition:.15s;cursor:pointer}
.node:hover{border-color:#b6bee0;background:#fff;transform:translateY(-1px);box-shadow:var(--shadow)}
.node .nid{font-family:var(--mono);font-size:10px;color:var(--tx3);display:flex;align-items:center;gap:6px}
.node .nid::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--tx3);flex:none}
.node.DONE .nid::before{background:var(--green)}
.node.IN_PROGRESS .nid::before,.node.CLAIMED .nid::before,.node.READY .nid::before{background:var(--blue)}
.node.BLOCKED .nid::before{background:var(--red)}
.node.READY_FOR_REVIEW .nid::before,.node.READY_FOR_GATE .nid::before,.node.OBSERVING .nid::before{background:var(--amber)}
.node .nti{font-size:11.5px;line-height:1.5;display:block;margin-top:3px;color:var(--tx)}
.node .ndep{font-size:9px;color:var(--tx3);font-family:var(--mono);display:block;margin-top:3px}
.node.crit .nti::after{content:" ◆";color:var(--amber);font-size:9px}
.node .own{float:right;font-size:10px;font-weight:600;width:18px;height:18px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center}
.own.m{background:#e8f0fe;color:var(--blue)}
.own.x{background:#f0edfd;color:var(--violet)}
.mw-gate{margin-top:12px;text-align:center}

/* delivery policy + professional lanes */
.policy{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;margin-bottom:36px;box-shadow:var(--shadow)}
.policy-head{display:flex;gap:12px;align-items:center;justify-content:space-between;margin-bottom:12px}
.policy-head strong{font-size:15px}.policy ol{padding-left:20px;color:var(--tx2);font-size:12px;line-height:1.9}
.policy-note{font-size:12px;color:var(--tx2);margin-top:12px;padding:10px 12px;border-radius:9px;background:#fff8eb;border:1px solid #f0dcb4}
.lane-table-wrap{overflow-x:auto;padding-bottom:10px}
.lane-table{min-width:1120px;display:grid;grid-template-columns:170px repeat(8,1fr);border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff}
.lane-cell{min-height:66px;padding:9px;border-right:1px solid var(--line);border-bottom:1px solid var(--line);font-size:10px;color:var(--tx2)}
.lane-cell:nth-child(9n){border-right:0}.lane-cell.head{min-height:auto;background:#f7f8fa;font-family:var(--mono);font-weight:600;color:var(--tx3);text-align:center}
.lane-cell.lname{font-size:11px;font-weight:600;color:var(--tx);background:#fbfbfc}.lane-cell.lname b{font-family:var(--mono);color:var(--indigo);margin-right:6px}
.lane-task{display:block;color:var(--tx2);text-decoration:none;padding:2px 0;line-height:1.35;cursor:pointer}.lane-task:hover{color:var(--indigo)}
.lane-task::before{content:"";display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--tx3);margin-right:5px}.lane-task.DONE::before{background:var(--green)}.lane-task.IN_PROGRESS::before,.lane-task.READY::before{background:var(--blue)}.lane-task.READY_FOR_REVIEW::before,.lane-task.READY_FOR_GATE::before{background:var(--amber)}.lane-task.BLOCKED::before{background:var(--red)}

/* filters */
.filters{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px}
.chip{border:1px solid var(--line2);background:#fff;color:var(--tx2);font-size:12px;padding:6px 15px;border-radius:99px;cursor:pointer;transition:.15s}
.chip:hover{border-color:var(--tx3)}
.chip.on{background:var(--tx);color:#fff;border-color:var(--tx)}

/* waves + tasks */
.wave{margin-bottom:32px}
.wave-head{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.wave-head .wn{font-family:var(--mono);font-size:11px;color:var(--indigo);font-weight:700;letter-spacing:.05em}
.wave-head .wt{font-size:15px;font-weight:600}
.wave-head .wp{margin-left:auto;font-family:var(--mono);font-size:11px;color:var(--tx3)}
.wave-bar{height:3px;background:var(--line);border-radius:99px;margin-bottom:14px;overflow:hidden}
.wave-bar i{display:block;height:100%;background:var(--green);border-radius:99px}
.task{display:flex;gap:14px;align-items:flex-start;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:10px;box-shadow:var(--shadow);scroll-margin-top:20px;transition:.15s}
.task:hover{border-color:var(--line2)}
.task.flash{border-color:var(--amber);box-shadow:0 0 0 3px rgba(217,119,6,.15)}
.task.crit{border-left:3px solid #f0c87e}
.tid{font-family:var(--mono);font-size:12px;color:var(--tx3);padding-top:2px;width:50px;flex:none}
.tbody{flex:1;min-width:0}
.ttitle{font-size:14.5px;font-weight:550;line-height:1.5}
.ttitle .crit-tag{font-size:10px;color:var(--amber);font-weight:500;margin-left:6px}
.tmeta{font-size:11.5px;color:var(--tx3);margin-top:4px}
.tmeta .gh{color:var(--blue)}
.ttime{font-size:11.5px;color:var(--tx2);margin-top:3px;font-variant-numeric:tabular-nums}
.tblock{font-size:11.5px;color:var(--red);margin-top:4px}
.tnote{font-size:11.5px;color:var(--tx2);margin-top:3px}
.tright{display:flex;flex-direction:column;align-items:flex-end;gap:8px;flex:none}
.pill{font-size:11px;padding:3px 11px;border-radius:99px;white-space:nowrap;font-weight:500}
.pill.READY{color:var(--blue);background:#eef4ff}
.pill.CLAIMED,.pill.IN_PROGRESS{color:var(--blue);background:#e8f0fe}
.pill.READY_FOR_REVIEW,.pill.READY_FOR_GATE,.pill.OBSERVING{color:var(--amber);background:#fdf6e9}
.pill.DONE{color:var(--green);background:#eafaf3}
.pill.BLOCKED{color:var(--red);background:#fdf1f0}
.pill.INTAKE,.pill.TRIAGED{color:var(--tx3);background:#f1f2f5}
.avatars{display:flex;gap:4px;align-items:center;font-size:10px;color:var(--tx3)}

/* log */
.log li{list-style:none;font-size:12.5px;color:var(--tx2);padding:10px 2px;border-bottom:1px solid var(--line);line-height:1.7}
.log li b{color:var(--tx3);font-family:var(--mono);font-weight:500;margin-right:10px;font-size:11px}

footer{margin-top:56px;padding-top:24px;border-top:1px solid var(--line);font-size:11.5px;color:var(--tx3);line-height:2.1}
footer code{font-family:var(--mono);color:var(--tx2);font-size:11px}
@media(max-width:640px){.wrap{padding:32px 16px 64px}h1{font-size:21px}.hmeta{text-align:left}.metric .v{font-size:22px}.tl-name{display:none}}
</style>
</head>
<body>
<div class="wrap" id="app"></div>
<script id="d" type="application/json">__DATA__</script>
<script>
let D=JSON.parse(document.getElementById('d').textContent);
const SNAME={PLANNED:'待建单',INTAKE:'待登记',TRIAGED:'已初判',READY:'可认领',CLAIMED:'已认领',IN_PROGRESS:'进行中',READY_FOR_REVIEW:'待审查',READY_FOR_GATE:'待过门',OBSERVING:'观察中',DONE:'已完成',BLOCKED:'阻塞'};
const GNAME={PENDING:'待评审',PASS:'PASS',FAIL:'FAIL',HOLD:'HOLD'};
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let filter='all',refreshState='';
const formatTime=s=>s?new Date(s).toLocaleString('zh-CN',{hour12:false}):'未记录';
function preparationPanel(){
 const p=D.preparation;
 if(!p)return '<section class="preparation"><h2>准备与审核</h2><p>准备状态尚未接入，请查看最近同步时间。</p></section>';
 const n=p.counts,active={drafting:0,revising:0,awaiting_review:1,template_approved:1,issuing:2}[p.phase]??0;
 const stages=['草稿整理','审核与准入','正式建单','认领施工'];
 return `<section class="preparation"><h2>准备与审核 · Wave 0</h2><h3>${esc(p.title)}</h3>
 <div class="steps">${stages.map((x,i)=>(i===active?`<b>${x} · 当前</b>`:esc(x))).join('<span>→</span>')}</div>
 <div class="prep-counts"><span><b>${n.parentDrafts}</b>父任务草稿</span><span><b>${n.atomicDrafts}</b>原子草稿</span><span><b>${n.detailedSamples}</b>详细规格样例</span><span><b>${n.selfCheckGroups}</b>组草稿自检记录</span></div>
 <p class="prep-detail">下一步：${esc(p.nextStep)}<br>草稿自检不等于独立审核、任务准入或产品验收；下方单独统计父工作包收口。</p>
 <p class="prep-detail">本轮事件 ${esc(formatTime(p.updatedAt))} · 样例版本 ${esc(p.sampleCommit.slice(0,7))}<br>
 <a href="${esc(p.sampleUrl)}" target="_blank" rel="noopener noreferrer">查看本轮修订 ↗（需私有仓权限）</a><a href="${esc(p.recordUrl)}" target="_blank" rel="noopener noreferrer">准备状态记录 ↗</a></p>
 </section>`;
}
async function refreshBoard(){
 try{
  const path=location.pathname.includes('/dist/')?'../board.json':'board.json';
  const response=await fetch(new URL(path,location.href).href+'?t='+Date.now(),{cache:'no-store'});
  if(!response.ok)throw new Error('unavailable');
  const next=await response.json();
  if(!next.meta||!Array.isArray(next.tasks)||!Array.isArray(next.gates))throw new Error('invalid');
  D=next;refreshState='页面已检查 '+new Date().toLocaleTimeString('zh-CN',{hour12:false});
 }catch(e){refreshState='暂时无法获取更新，保留当前快照；请留意上次同步时间';}
 const y=window.scrollY;render();window.scrollTo(0,y);
}

function av(o){if(o==='敏敏')return '<span class="own m" title="敏敏">敏</span>';if(o==='夏天')return '<span class="own x" title="夏天">夏</span>';return ''}
function render(){
const T=D.tasks,G={};(D.gates||[]).forEach(g=>G[g.id]=g);
const c={};T.forEach(t=>c[t.status]=(c[t.status]||0)+1);
const done=c.DONE||0,ready=c.READY||0,wip=(c.CLAIMED||0)+(c.IN_PROGRESS||0),blocked=c.BLOCKED||0,review=(c.READY_FOR_REVIEW||0)+(c.READY_FOR_GATE||0);
const gp=(D.gates||[]).filter(g=>g.status==='PASS').length;
const pct=T.length?Math.round(done/T.length*100):0;
const stale=!D.meta.syncedAtISO||Date.now()-Date.parse(D.meta.syncedAtISO)>45*60*1000;
let h=`<header><div><h1>悟小空作战指挥室<span class="sub">系统修复实施计划 v1.2 · 夏天确认版 · 数据以 GitHub 为准</span></h1></div>
<div class="hmeta">当前波次 <b>Wave ${D.meta.currentWave}</b> · 基线 <b>${esc((D.meta.baselineSha||'').slice(0,7))}</b><br>更新 <b>${esc(D.meta.syncedAt||D.meta.updatedAt)}</b> · ${esc(D.meta.updatedBy)}</div></header>`;
h+=`<div class="freshness ${stale?'warn':''}"><button id="refresh-board" type="button">刷新看板</button><span>${esc(refreshState||'页面每60秒检查已发布快照；本机同步任务负责拉取GitHub并发布')}</span>${stale?'<span>同步快照已超过45分钟或缺少时间标识</span>':''}</div>`;
h+=preparationPanel();
if(D.atomicIssues?.length){h+='<section class="preparation"><h2>已转出原子任务 · GitHub 实际状态</h2>';D.atomicIssues.forEach(t=>{h+=`<p class="prep-detail"><b>${esc(t.id)}</b> · ${esc(SNAME[t.status]||t.status)} · ${esc(t.owner||'未分配')} <a href="${esc(t.issueUrl)}" target="_blank" rel="noopener noreferrer">任务 Issue ↗</a>${t.prUrl?`<a href="${esc(t.prUrl)}" target="_blank" rel="noopener noreferrer">交付 PR ↗</a>`:''}</p>`});h+='<p class="prep-detail">原子任务与父工作包分开显示；待审查不代表独立验收或合并门已通过。</p></section>';}
const policy=D.deliveryPolicy||{};
if(policy.standardFlow?.length){h+=`<section class="policy"><div class="policy-head"><strong>交付、复核与合并路径</strong><span class="gate ${policy.remotePushStatus==='HOLD'?'HOLD':'PASS'}">远端推送 ${esc(policy.remotePushStatus||'—')}</span></div><ol>${policy.standardFlow.map(x=>`<li>${esc(x)}</li>`).join('')}</ol><p class="prep-detail">统一接收分支：<b>${esc(policy.targetBranch||'未定')}</b></p>${policy.temporaryException?`<p class="policy-note"><b>当前例外：</b>${esc(policy.temporaryException)}</p>`:''}${policy.protectionNote?`<p class="prep-detail" style="margin-top:9px">${esc(policy.protectionNote)}</p>`:''}</section>`;}

h+=`<h2>正式施工 · 父工作包收口</h2><p class="prep-detail" style="margin-bottom:12px">草稿准备另列上方；未建单的父工作包不计为可认领。完成比例只代表已验收收口，不表示准备工作量。</p>`;
h+=`<div class="metrics">
<div class="metric"><div class="v">${pct}<span style="font-size:15px;color:var(--tx3)">%</span></div><div class="k">父工作包 ${done}/${T.length}</div></div>
<div class="metric"><div class="v" style="color:var(--blue)">${c.PLANNED||0}</div><div class="k">待建单</div></div>
<div class="metric"><div class="v" style="color:var(--blue)">${wip}</div><div class="k">在制</div></div>
<div class="metric"><div class="v" style="color:var(--amber)">${review}</div><div class="k">待审查 / 过门</div></div>
<div class="metric"><div class="v" style="color:var(--red)">${blocked}</div><div class="k">阻塞</div></div>
<div class="metric"><div class="v" style="color:var(--green)">${gp}<span style="font-size:14px;color:var(--tx3)">/8</span></div><div class="k">Gate 通过</div></div></div>`;
h+=`<section><h2>波次时间线 · 按门禁推进</h2><p class="timeline-note">未批准日历工期，因此不编造日期。当前波次完成出口 Gate 后进入下一波；无依赖项可以提前准备，不能越过合并门。</p><div class="timeline">`;
(D.waves||[]).forEach(w=>{const g=G[w.gate]||{status:'PENDING'};const cls=g.status==='PASS'?'done':(w.id===D.meta.currentWave?'active':'');const wt=T.filter(t=>t.wave===w.id);const wc={};wt.forEach(t=>wc[t.status]=(wc[t.status]||0)+1);let summary=`父包 ${wc.DONE||0}/${wt.length}`;if(w.id===0&&D.atomicIssues?.length){const ac={};D.atomicIssues.forEach(t=>ac[t.status]=(ac[t.status]||0)+1);summary+=` · 原子 在制 ${(ac.IN_PROGRESS||0)+(ac.CLAIMED||0)} / 待审 ${(ac.READY_FOR_REVIEW||0)+(ac.READY_FOR_GATE||0)}`;}
h+=`<div class="tl-node ${cls}" title="${esc(w.goal||'')}"><div class="tl-dot">W${w.id}</div><div class="tl-name">${esc(w.name)}</div><div class="tl-count">${esc(summary)}</div><div class="tl-gate"><span class="gate ${g.status}">${w.gate} ${GNAME[g.status]||g.status}</span></div></div>`});
h+=`</div></section>`;
const BYID={};T.forEach(t=>BYID[t.id]=t);
if(D.professionalLanes?.length){h+=`<section><h2>A–F 专业甬道 · 跨波工作面</h2><p class="timeline-note">纵向是六类专业写面，横向是 W0–W7。圆点颜色来自 GitHub 状态；点击任务可跳到工作包。</p><div class="lane-table-wrap"><div class="lane-table"><div class="lane-cell head">甬道 / 波次</div>${(D.waves||[]).map(w=>`<div class="lane-cell head">W${w.id}</div>`).join('')}`;D.professionalLanes.forEach(l=>{h+=`<div class="lane-cell lname"><b>${esc(l.id)}</b>${esc(l.name)}</div>`;(D.waves||[]).forEach(w=>{const items=(l.taskIds||[]).map(id=>BYID[id]).filter(t=>t&&t.wave===w.id);h+=`<div class="lane-cell">${items.map(t=>`<a class="lane-task ${t.status}" data-jump="${t.id}" title="${esc(t.title)}">${t.id} ${esc(t.title)}</a>`).join('')}</div>`});});h+=`</div></div></section>`;}
h+=`<section><h2>波次作战图 · 波内并行组与依赖</h2><div class="legend"><span><i style="background:var(--blue)"></i>可认领/进行中</span><span><i style="background:var(--amber)"></i>待审查/过门</span><span><i style="background:var(--red)"></i>阻塞</span><span><i style="background:var(--green)"></i>已完成</span><span>◆ 关键路径 · ⟵ 波内前置 · ⤺ 跨波前置 · 点节点跳转任务卡</span></div><div class="map">`;
(D.waves||[]).forEach(w=>{
const wt=T.filter(t=>t.wave===w.id);const g=G[w.gate]||{status:'PENDING'};
const lanes={};wt.forEach(t=>{const L=(t.group||'?').replace(/[0-9]+$/,'');(lanes[L]=lanes[L]||[]).push(t)});
h+=`<div class="mwave ${w.id===D.meta.currentWave?'active':''}"><div class="mw-head"><span class="wn2">W${w.id}</span><span class="wt2">${esc(w.name)}</span></div><div class="lanes">`;
Object.keys(lanes).sort().forEach(L=>{
h+=`<div class="lane"><div class="lane-tag">${L} 组</div>`;
lanes[L].forEach(t=>{
const inw=(t.deps||[]).filter(d=>BYID[d]&&BYID[d].wave===w.id);
const cross=(t.deps||[]).filter(d=>!BYID[d]||BYID[d].wave!==w.id);
h+=`<a class="node ${t.status} ${t.critical?'crit':''}" data-jump="${t.id}"><span class="nid">${t.id}${av(t.owner)}</span><span class="nti">${esc(t.title)}</span>${inw.length?`<span class="ndep">⟵ ${inw.join(' ')}</span>`:''}${cross.length?`<span class="ndep">⤺ ${cross.join(' ')}</span>`:''}</a>`});
h+=`</div>`});
h+=`</div><div class="mw-gate"><span class="gate ${g.status}" title="${esc(g.rule||'')}">出口 ${w.gate} · ${GNAME[g.status]||g.status}</span></div></div>`});
h+=`</div></section>`;
h+=`<section><h2>工作包</h2><div class="filters">`;
[['all','全部'],['敏敏','敏敏'],['夏天','夏天'],['none','未分配'],['crit','关键路径'],['active','在制 / 待审'],['blocked','阻塞']].forEach(f=>{h+=`<button class="chip ${filter===f[0]?'on':''}" data-f="${f[0]}">${f[1]}</button>`});
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
h+=`<div class="wave"><div class="wave-head"><span class="wn">WAVE ${w.id}</span><span class="wt">${esc(w.name)}</span><span class="gate ${g.status}" title="${esc(g.rule||'')}${g.note?' — '+esc(g.note):''}">${w.gate} · ${GNAME[g.status]||g.status}</span><span class="wp">${wd}/${wt.length}</span></div><div class="wave-bar"><i style="width:${wp}%"></i></div>`;
wt.forEach(t=>{
const dur=t.claimedAt&&t.doneAt?Math.max(0,Math.round((new Date(t.doneAt)-new Date(t.claimedAt))/86400000)):null;
const times=[t.claimedAt?`认领 ${t.claimedAt}`:'',t.doneAt?`完成 ${t.doneAt}`:'',dur!==null?`耗时 ${dur} 天`:'',t.status==='BLOCKED'&&t.blockedAt?`阻塞自 ${t.blockedAt}`:''].filter(Boolean).join(' · ');
h+=`<div class="task ${t.critical?'crit':''}" id="task-${t.id}"><span class="tid">${esc(t.id)}</span><span class="tbody"><div class="ttitle">${esc(t.title)}${t.critical?'<span class="crit-tag">◆ 关键路径</span>':''}</div><div class="tmeta">${esc(t.s)} · ${esc(t.p)}${t.deps&&t.deps.length?' · 前置 '+esc(t.deps.join(' ')):""}${t.ghIssue?` · <span class="gh">#${t.ghIssue}</span>`:''}</div>${times?`<div class="ttime">${esc(times)}</div>`:''}${t.status==='BLOCKED'&&t.blocker?`<div class="tblock">⊘ ${esc(t.blocker)}</div>`:''}${(t.flags||[]).map(f=>`<div class="tblock">⚠ ${esc(f)}</div>`).join('')}${t.note?`<div class="tnote">✎ ${esc(t.note)}</div>`:''}</span><span class="tright"><span class="pill ${t.status}">${SNAME[t.status]||t.status}</span><span class="avatars">${av(t.owner)}${t.reviewer?'审 '+av(t.reviewer):''}${!t.owner?(t.status==='PLANNED'?'未建单':'未分配'):''}</span></span></div>`});
h+=`</div>`});
h+=`</section>`;
if(D.log&&D.log.length){h+=`<section><h2>变更记录</h2><ul class="log">`;D.log.slice(-10).reverse().forEach(l=>{h+=`<li><b>${esc(l.at)}</b>${esc(l.by)} · ${esc(l.what)}</li>`});h+=`</ul></section>`}
h+=`<footer>只读看板 · 事实源 <code>github.com/${esc(D.meta.generatedFrom?.repo||'lyx680805-first/ip-system-runtime')}</code> 的 Issue / PR / Milestone<br>${esc(D.meta.productionBoundary)}<br>准备状态来自私有工作仓的最小状态记录；正式施工来自上方施工仓。页面自动读取公开快照，不持有私有仓凭据。</footer>`;
document.getElementById('app').innerHTML=h;
document.getElementById('refresh-board').onclick=refreshBoard;
document.querySelectorAll('[data-f]').forEach(b=>b.onclick=()=>{filter=b.dataset.f;render()});
document.querySelectorAll('[data-jump]').forEach(n=>n.onclick=e=>{e.preventDefault();const el=document.getElementById('task-'+n.dataset.jump);if(!el)return;el.scrollIntoView({behavior:'smooth',block:'center'});el.classList.add('flash');setTimeout(()=>el.classList.remove('flash'),1600)});
}
render();
setInterval(()=>{if(!document.hidden)refreshBoard()},60000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshBoard()});
refreshBoard();
</script>
</body>
</html>
"""

out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(TEMPLATE.replace("__DATA__", payload), encoding="utf-8")
print(f"rendered -> {out_path} ({out_path.stat().st_size} bytes, {len(data['tasks'])} tasks)")
