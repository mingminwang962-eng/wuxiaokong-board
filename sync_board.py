#!/usr/bin/env python3
# sync_board.py — 看板可信化同步器 v2
#
# 原则（可信化补丁）：
#   - board.json 是纯生成物：plan.json（静态计划）+ GitHub 事实 → board.json，每次整体重建
#   - 关闭 Issue ≠ 完成。DONE 需同时满足：合并的 PR + 自动测试全绿 + 非实施者审核批准 + evidence:ok 标签
#   - Gate 只认机器标签 gate:pass，且候选 SHA 必须与当前候选一致；候选变化 → 旧 PASS 自动失效（HOLD）
#   - 人员显示名只来自 people.json；未登记账号不直接显示 GitHub 用户名；负责人=复核人 → 标红
#
# 用法：
#   python3 sync_board.py                 # 拉取 + 重建 board.json + 渲染页面
#   python3 sync_board.py --publish       # 额外 git push 刷新公网看板（本地）
#   python3 sync_board.py --apply-labels  # 机器评估 Gate 条件并写回 gate:pass 标签（需写权限）
#   python3 sync_board.py --ci            # CI 模式：不碰本机 Widget 路径，不 push
#   python3 sync_board.py --dry-run       # 只打印变化
#   python3 sync_board.py --selftest      # 七项伪造攻击自检，不接触网络
import json, re, subprocess, sys, pathlib, datetime, shutil, os, fcntl, base64
from preparation import WORK_REPO, project_preparation

ROOT = pathlib.Path(__file__).parent
PLAN = ROOT / "plan.json"
PEOPLE = ROOT / "people.json"
BOARD = ROOT / "board.json"
SOURCE_REPO = os.environ.get("BOARD_SOURCE_REPO", "lyx680805-first/ip-system-runtime")
SOURCE_BRANCH = os.environ.get("BOARD_SOURCE_BRANCH", "main")
WIDGET_BOARD = pathlib.Path(os.environ.get("WIDGET_BOARD_PATH",
    "/Users/minmin/Library/Application Support/kimi-desktop/daimon-share/daimon/agents/main/blueprint/widgets/widget_c4d64365-1961-474e-ade1-617a82e3cbfb/workspace/board.json"))
TASK_RE = re.compile(r"\[(T\d{2}\.\d)\]")
GATE_RE = re.compile(r"\[GATE-(WG\d)\]")
CANDIDATE_RE = re.compile(r"candidate:([0-9a-f]{7,40})")

STATUS_ORDER = ["READY", "IN_PROGRESS", "READY_FOR_REVIEW", "READY_FOR_GATE", "OBSERVING", "DONE"]

def gh(*args, check=True):
    r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=90)
    if check and r.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:2])} 失败: {r.stderr.strip()[:300]}")
    return r.stdout

def day(iso):
    return iso[:10] if iso else None

# ---------- 核心裁决逻辑（纯函数，可自检） ----------

def decide_task(issue, pr, people):
    """根据 Issue + 关联 PR 裁决任务状态。返回 (status, owner, reviewer, flags, times)"""
    flags, times = [], {}
    if issue is None:
        return None, None, None, flags, times  # 无 Issue：保持计划态
    labels = {l["name"] for l in issue.get("labels", [])}
    assignees = [a["login"] for a in issue.get("assignees", [])]
    owner_login = assignees[0] if assignees else None
    if owner_login and owner_login not in people:
        flags.append(f"未登记账号 {owner_login}（请补 people.json）")
    owner = people.get(owner_login, {}).get("display_name") if owner_login else None
    reviewer = next((l.split(":", 1)[1] for l in labels if l.startswith("reviewer:")), None)
    if owner and reviewer and owner == reviewer:
        flags.append("负责人与复核人是同一人，违反交叉复核")

    times["claimedAt"] = day(issue.get("claimedAt") or issue.get("createdAt")) if assignees else None
    times["doneAt"] = None

    if issue["state"] != "CLOSED":
        if "state:blocked" in labels: st = "BLOCKED"
        elif "state:in-review" in labels: st = "READY_FOR_REVIEW"
        elif "state:ready-for-gate" in labels: st = "READY_FOR_GATE"
        elif "state:observing" in labels: st = "OBSERVING"
        elif assignees: st = "IN_PROGRESS"
        elif "status:ready" in labels: st = "READY"
        else: st = "TRIAGED"
        return st, owner, reviewer, flags, times

    # Issue 已关闭 ≠ 完成：进入四级裁决
    times["doneAt"] = None
    if pr is None or not pr.get("mergedAt"):
        flags.append("Issue 已关闭但无已合并 PR，最多记为待审查")
        return "READY_FOR_REVIEW", owner, reviewer, flags, times

    checks = [c for c in (pr.get("statusCheckRollup") or []) if c.get("__typename") == "CheckRun"]
    if not checks:
        flags.append("合并 PR 无自动测试记录")
        return "READY_FOR_REVIEW", owner, reviewer, flags, times
    bad = [c for c in checks if c.get("conclusion") not in ("SUCCESS", "NEUTRAL", "SKIPPED")]
    if bad:
        flags.append(f"{len(bad)} 项自动测试未通过")
        return "READY_FOR_REVIEW", owner, reviewer, flags, times

    pr_author = (pr.get("author") or {}).get("login")
    approvals = [r for r in (pr.get("reviews") or [])
                 if r.get("state") == "APPROVED"
                 and r.get("author", {}).get("login") not in (pr_author, owner_login)]
    if not approvals:
        flags.append("缺少非实施者的审核批准")
        return "READY_FOR_REVIEW", owner, reviewer, flags, times

    if "evidence:ok" not in labels:
        flags.append("证据清单未确认（缺 evidence:ok 标签）")
        return "READY_FOR_GATE", owner, reviewer, flags, times

    times["doneAt"] = day(issue.get("closedAt"))
    return "DONE", owner, reviewer, flags, times

def decide_gate(issue, current_sha):
    """Gate 只认机器标签 gate:pass 且候选 SHA 匹配。返回 (status, note)"""
    if issue is None:
        return "PENDING", ""
    labels = {l["name"] for l in issue.get("labels", [])}
    if "gate:pass" not in labels:
        if issue["state"] == "CLOSED":
            return "HOLD", "人工关闭不产生 PASS：需机器核对后加 gate:pass 标签"
        return "PENDING", ""
    m = CANDIDATE_RE.search(issue.get("candidateComment") or "")
    if not m:
        return "HOLD", "gate:pass 缺少候选身份记录"
    if current_sha and not current_sha.startswith(m.group(1)) and not m.group(1).startswith(current_sha[:7]):
        return "HOLD", f"候选已变化（记录 {m.group(1)[:7]} ≠ 当前 {current_sha[:7]}），旧 PASS 自动失效"
    return "PASS", ""

# ---------- GitHub 拉取 ----------

def fetch_all():
    branch = SOURCE_BRANCH
    if branch == "main":
        branch = gh("api", f"repos/{SOURCE_REPO}", "--jq", ".default_branch").strip() or "main"
    issues = json.loads(gh("issue", "list", "-R", SOURCE_REPO, "--state", "all", "--limit", "300",
                           "--json", "number,title,state,assignees,labels,createdAt,closedAt"))
    prs = json.loads(gh("pr", "list", "-R", SOURCE_REPO, "--state", "all", "--limit", "300",
                        "--json", "number,title,state,mergedAt,author,statusCheckRollup,reviews"))
    head_sha = gh("api", f"repos/{SOURCE_REPO}/commits/{branch}", "--jq", ".sha").strip()
    # Gate 候选记录：读 gate:pass 评论
    gate_comments = {}
    for it in issues:
        gm = GATE_RE.search(it["title"])
        if gm:
            body = gh("api", f"repos/{SOURCE_REPO}/issues/{it['number']}/comments",
                      "--jq", '[.[] | .body] | join("\\n")', check=False)
            it["candidateComment"] = body
            gate_comments[gm.group(1)] = it
    return issues, prs, head_sha, branch

# ---------- 主流程 ----------

def fetch_preparation():
    record_sha = gh("api", f"repos/{WORK_REPO}/commits/main", "--jq", ".sha").strip()
    content = json.loads(gh("api", f"repos/{WORK_REPO}/contents/status/board-preparation.json?ref={record_sha}"))
    record = json.loads(base64.b64decode(content["content"]))
    return project_preparation(record, record_sha)

def build_board(plan, people, issues, prs, head_sha, today, now, src_branch="main"):
    tasks_out, gates_out, changes = [], [], []
    issue_by_task, gate_issue = {}, {}
    for it in issues:
        m = TASK_RE.search(it["title"])
        if m: issue_by_task[m.group(1)] = it
        gm = GATE_RE.search(it["title"])
        if gm: gate_issue[gm.group(1)] = it
    pr_by_task = {}
    for p in prs:
        m = TASK_RE.search(p["title"])
        if m and m.group(1) not in pr_by_task:
            pr_by_task[m.group(1)] = p  # 同一任务多 PR 时取第一个（标题约定唯一）

    for pt in plan["tasks"]:
        t = dict(pt)
        t.update({"owner": None, "reviewer": None, "status": None, "blocker": "",
                  "note": "", "claimedAt": None, "doneAt": None, "blockedAt": None,
                  "ghIssue": None, "flags": [], "updatedAt": today})
        it = issue_by_task.get(t["id"])
        pr = pr_by_task.get(t["id"])
        if it:
            t["ghIssue"] = it["number"]
            st, owner, reviewer, flags, times = decide_task(it, pr, people)
            t["status"], t["owner"], t["reviewer"] = st, owner, reviewer
            t["flags"] = flags
            t.update(times)
            if st == "BLOCKED": t["blockedAt"] = today
        else:
            t["status"] = "PLANNED"
            t["note"] = "父工作包尚未建单；草稿审核进度见上方，不代表可认领施工。"
        tasks_out.append(t)

    # 依赖与 Gate 裁决
    tmap = {t["id"]: t for t in tasks_out}
    gmap = {}
    for pg in plan["gates"]:
        gi = gate_issue.get(pg["id"])
        st, note = decide_gate(gi, head_sha)
        gmap[pg["id"]] = st
        g = dict(pg); g["status"] = st; g["note"] = note
        if gi: g["ghIssue"] = gi["number"]
        gates_out.append(g)

    for t in tasks_out:
        if t["status"] is not None and t["status"] != "BLOCKED":
            continue
        deps = t.get("deps") or []
        if not deps:
            t["status"] = t["status"] or "READY"
            continue
        ok = all((tmap[d]["status"] == "DONE") if d in tmap else (gmap.get(d) == "PASS") for d in deps)
        if t["status"] is None:
            t["status"] = "READY" if ok else "BLOCKED"
            if not ok:
                waiting = [d for d in deps if not ((tmap[d]["status"] == "DONE") if d in tmap else (gmap.get(d) == "PASS"))]
                t["blocker"] = "等 " + "、".join(waiting)

    cur = 0
    for w in plan["waves"]:
        if any(t["wave"] == w["id"] and t["status"] != "DONE" for t in tasks_out):
            cur = w["id"]; break
    else:
        cur = plan["waves"][-1]["id"]

    return {
        "meta": {**plan["meta"],
                 "updatedAt": today, "updatedBy": "sync_board v2（GitHub 事实重建）",
                 "syncedAt": now, "currentWave": cur,
                 "generatedFrom": {"repo": SOURCE_REPO, "branch": src_branch,
                                   "headSha": head_sha, "issues": len(issues), "prs": len(prs)}},
        "owners": plan["owners"], "statusFlow": plan["statusFlow"],
        "waves": plan["waves"], "gates": gates_out, "tasks": tasks_out,
        "log": [], "_changes": changes,
    }

def gate_eligibility(board):
    """机器 Gate 评估：本 Wave 任务全部 DONE 且无旗标 → 可贴 gate:pass"""
    eligible = {}
    for w in board["waves"]:
        gid = w["gate"]
        wt = [t for t in board["tasks"] if t["wave"] == w["id"]]
        ok = all(t["status"] == "DONE" and not t["flags"] for t in wt)
        eligible[gid] = ok
    return eligible

def run_sync():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest()
    dry, ci = "--dry-run" in argv, "--ci" in argv
    apply_labels = "--apply-labels" in argv

    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    people = json.loads(PEOPLE.read_text(encoding="utf-8"))
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    today = now[:10]

    try:
        issues, prs, head_sha, src_branch = fetch_all()
        preparation = fetch_preparation()
    except Exception as e:
        # 同步失败：保留旧页面，不覆盖（补丁第三项）
        print(f"同步失败：{e}\n旧看板保持不变。")
        sys.exit(2)

    board = build_board(plan, people, issues, prs, head_sha, today, now, src_branch)
    board["preparation"] = preparation
    board["meta"]["syncedAtISO"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    board["meta"]["updatedBy"] = "GitHub 同步（施工记录＋准备状态）"

    # 与上一版对比生成变更日志
    old = json.loads(BOARD.read_text(encoding="utf-8")) if BOARD.exists() else None
    log = (old or {}).get("log", [])
    if old:
        oldprep = old.get("preparation") or {}
        if any(oldprep.get(k) != preparation.get(k) for k in ("phase", "sampleCommit", "counts")):
            board["_changes"].append(preparation["title"] + "（准备进度，不计入施工完成）")
        oldt = {t["id"]: t for t in old.get("tasks", [])}
        for t in board["tasks"]:
            o = oldt.get(t["id"], {})
            diff = []
            if o.get("status") != t["status"]: diff.append(f"状态 {o.get('status','—')}→{t['status']}")
            if o.get("owner") != t["owner"] and t["owner"]: diff.append(f"认领人→{t['owner']}")
            if diff: changes = f"{t['id']}: {'，'.join(diff)}"; board["_changes"].append(changes)
        oldg = {g["id"]: g for g in old.get("gates", [])}
        for g in board["gates"]:
            if oldg.get(g["id"], {}).get("status") != g["status"]:
                board["_changes"].append(f"{g['id']}: {oldg.get(g['id'],{}).get('status','—')}→{g['status']}")
    if board["_changes"]:
        log.append({"at": now, "by": "GitHub 同步", "what": "；".join(board["_changes"])})
    board["log"] = log[-200:]
    del board["_changes"]

    if not issues:
        print(f"源仓库 {SOURCE_REPO} 暂无任务 Issue，看板为计划初始态（全部待建单）。")

    # 机器 Gate 标签写回
    if apply_labels:
        elig = gate_eligibility(board)
        for g in board["gates"]:
            if "ghIssue" not in g: continue
            want = elig.get(g["id"], False)
            has = g["status"] == "PASS"
            if want and not has:
                gh("issue", "edit", str(g["ghIssue"]), "-R", SOURCE_REPO, "--add-label", "gate:pass", check=False)
                gh("issue", "comment", str(g["ghIssue"]), "-R", SOURCE_REPO,
                   "--body", f"candidate:{head_sha}\n机器核对：本 Wave 任务全部 DONE 且无旗标。", check=False)
                print(f"机器加签 {g['id']} gate:pass (candidate {head_sha[:7]})")
            elif not want and has:
                gh("issue", "edit", str(g["ghIssue"]), "-R", SOURCE_REPO, "--remove-label", "gate:pass", check=False)
                print(f"机器摘除 {g['id']} gate:pass（条件不再满足）")

    print("变更：" if board["log"] and board["log"][-1]["by"] == "GitHub 同步" else "无状态变化。")
    if board["log"] and board["log"][-1]["by"] == "GitHub 同步":
        print(" - " + board["log"][-1]["what"])
    if dry:
        print("--dry-run，未写文件"); return

    BOARD.write_text(json.dumps(board, ensure_ascii=False, indent=2), encoding="utf-8")
    if not ci and WIDGET_BOARD.exists():
        WIDGET_BOARD.write_text(BOARD.read_text(encoding="utf-8"), encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "render_board.py")], check=True)
    print("board.json 已重建（plan + GitHub 事实），页面已渲染。")

    if "--publish" in argv and not ci:
        shutil.copy(ROOT / "dist" / "index.html", ROOT / "index.html")
        generated = ["board.json", "dist/index.html", "index.html"]
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()
        if set(staged) - set(generated):
            raise RuntimeError("暂存区有非看板生成文件，停止自动提交，请先处理人工改动")
        subprocess.run(["git", "add", "--", *generated], cwd=ROOT, check=True)
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode != 0:
            subprocess.run(["git", "-c", "user.name=github-actions[bot]",
                            "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
                            "commit", "-qm", f"sync: {now} 看板同步"], cwd=ROOT, check=True)
            subprocess.run(["git", "push", "-q"], cwd=ROOT, check=True)
            print("已发布。")
        else:
            print("页面无变化，跳过发布。")

def main():
    if "--selftest" in sys.argv:
        return selftest()
    # 自动同步与人工同步不能同时重建/提交同一工作树。
    with open(ROOT / ".git" / "board-sync.lock", "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("另一次看板同步正在执行，本轮跳过。")
            return
        return run_sync()

# ---------- 七项伪造攻击自检 ----------

def selftest():
    people = {"alice": {"display_name": "敏敏"}, "bob": {"display_name": "夏天"}}
    good_checks = [{"__typename": "CheckRun", "conclusion": "SUCCESS"}]
    ext_review = [{"state": "APPROVED", "author": {"login": "bob"}}]
    self_review = [{"state": "APPROVED", "author": {"login": "alice"}}]
    closed = lambda labels: {"state": "CLOSED", "labels": [{"name": l} for l in labels],
                             "assignees": [{"login": "alice"}], "createdAt": "2026-09-01", "closedAt": "2026-09-05"}
    pr = lambda checks, reviews: {"mergedAt": "x", "author": {"login": "alice"},
                                  "statusCheckRollup": checks, "reviews": reviews}
    cases = []
    s, *_ = decide_task(closed([]), None, people)
    cases.append(("手工关闭任务不能伪造完成", s == "READY_FOR_REVIEW"))
    s, *_ = decide_task(closed(["evidence:ok"]), pr([{"__typename": "CheckRun", "conclusion": "FAILURE"}], ext_review), people)
    cases.append(("测试失败不能显示 DONE", s == "READY_FOR_REVIEW"))
    s, _, _, fl, _ = decide_task(closed(["evidence:ok"]), pr(good_checks, self_review), people)
    cases.append(("实施者不能审核自己", s == "READY_FOR_REVIEW" and any("审核" in f for f in fl)))
    s, *_ = decide_task(closed([]), pr(good_checks, ext_review), people)
    cases.append(("缺证据清单最多到待过门", s == "READY_FOR_GATE"))
    s, *_ = decide_task(closed(["evidence:ok"]), pr(good_checks, ext_review), people)
    cases.append(("四级全过才 DONE", s == "DONE"))
    g, note = decide_gate({"state": "CLOSED", "labels": [], "candidateComment": ""}, "abc1234")
    cases.append(("人工关 Gate 不 PASS", g == "HOLD"))
    g, note = decide_gate({"state": "OPEN", "labels": [{"name": "gate:pass"}], "candidateComment": "candidate:aaa1111"}, "bbb2222")
    cases.append(("候选变化旧 PASS 自动失效", g == "HOLD"))
    g, _ = decide_gate({"state": "OPEN", "labels": [{"name": "gate:pass"}], "candidateComment": "candidate:abc1234"}, "abc1234def")
    cases.append(("机器标签+候选一致才 PASS", g == "PASS"))
    failed = [name for name, ok in cases if not ok]
    for name, ok in cases:
        print(("✓" if ok else "✗"), name)
    print(f"\n自检 {len(cases)-len(failed)}/{len(cases)} 通过")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
