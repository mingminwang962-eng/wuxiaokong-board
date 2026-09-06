#!/usr/bin/env python3
# sync_board.py — 从 GitHub 拉取真实进度，更新 board.json 并重建公网看板
#
# 事实源：GitHub Issue / PR / Milestone（不是任何人的口头汇报）
# 用法：
#   python3 sync_board.py              # 拉取 + 更新 + 重新渲染
#   python3 sync_board.py --publish    # 额外重新发布到妙搭（需 lark-cli 已认证）
#   python3 sync_board.py --dry-run    # 只打印将要发生什么，不写文件
#
# GitHub 协作约定（任何 agent / 人都按这个来）：
#   - Issue 标题以 [T00.1] 这样的任务号开头
#   - assignee = 认领人；reviewer 用 label `reviewer:敏敏` / `reviewer:夏天`
#   - 状态 label：state:blocked / state:in-review / state:ready-for-gate / state:observing
#     无 label：open+有assignee=进行中；open+无assignee=可认领；closed=已完成
#   - Gate 用标题 [GATE-WG0]…[GATE-WG7] 的 Issue 表示，closed=PASS
#   - 认领时间 = issue 的 assigned 事件时间；完成时间 = closedAt
import json, re, subprocess, sys, pathlib, datetime

ROOT = pathlib.Path(__file__).parent
BOARD = ROOT / "board.json"
REPO = "mingminwang962-eng/ip-system-runtime"
WIDGET_BOARD = pathlib.Path("/Users/minmin/Library/Application Support/kimi-desktop/daimon-share/daimon/agents/main/blueprint/widgets/widget_c4d64365-1961-474e-ade1-617a82e3cbfb/workspace/board.json")

# GitHub 登录名 -> 看板显示名。夏天的 GitHub 用户名确定后填到这里。
ASSIGNEE_MAP = {
    "mingminwang962-eng": "敏敏",
    # "夏天的GitHub用户名": "夏天",
}
TASK_RE = re.compile(r"\[(T\d{2}\.\d)\]")
GATE_RE = re.compile(r"\[GATE-(WG\d)\]")

def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:2])} 失败: {r.stderr.strip()[:300]}")
    return r.stdout

def day(iso):
    return iso[:10] if iso else None

def main():
    dry = "--dry-run" in sys.argv
    board = json.loads(BOARD.read_text(encoding="utf-8"))
    tasks = {t["id"]: t for t in board["tasks"]}
    gates = {g["id"]: g for g in board["gates"]}
    changes = []

    raw = gh("issue", "list", "-R", REPO, "--state", "all", "--limit", "300",
             "--json", "number,title,state,assignees,labels,createdAt,closedAt")
    issues = json.loads(raw)

    for it in issues:
        m = TASK_RE.search(it["title"])
        gm = GATE_RE.search(it["title"])
        if gm and gm.group(1) in gates:
            g = gates[gm.group(1)]
            new = "PASS" if it["state"] == "CLOSED" else "PENDING"
            if g["status"] != new:
                changes.append(f"Gate {g['id']}: {g['status']} → {new}（issue #{it['number']}）")
                g["status"] = new
            continue
        if not m or m.group(1) not in tasks:
            continue
        t = tasks[m.group(1)]
        labels = {l["name"] for l in it.get("labels", [])}
        assignees = [a["login"] for a in it.get("assignees", [])]
        owner = next((ASSIGNEE_MAP[a] for a in assignees if a in ASSIGNEE_MAP), None)
        if not owner and assignees:
            owner = assignees[0]  # 未登记的 GitHub 用户名原样显示，提醒补 ASSIGNEE_MAP
        reviewer = next((l.split(":", 1)[1] for l in labels if l.startswith("reviewer:")), t.get("reviewer"))

        if it["state"] == "CLOSED":
            status = "DONE"
        elif "state:blocked" in labels:
            status = "BLOCKED"
        elif "state:in-review" in labels:
            status = "READY_FOR_REVIEW"
        elif "state:ready-for-gate" in labels:
            status = "READY_FOR_GATE"
        elif "state:observing" in labels:
            status = "OBSERVING"
        elif assignees:
            status = "IN_PROGRESS"
        else:
            status = "READY"

        done_at = day(it.get("closedAt")) if it["state"] == "CLOSED" else None
        claimed_at = t.get("claimedAt")
        if assignees and not claimed_at:
            try:
                tl = json.loads(gh("api", f"repos/{REPO}/issues/{it['number']}/timeline",
                                   "--jq", '[.[] | select(.event=="assigned") | .created_at] | .[0] // empty'))
                claimed_at = day(tl.strip('"')) if tl else day(it.get("createdAt"))
            except Exception:
                claimed_at = day(it.get("createdAt"))

        diff = []
        if t["status"] != status: diff.append(f"状态 {t['status']}→{status}")
        if owner and t.get("owner") != owner: diff.append(f"认领人→{owner}")
        if reviewer and t.get("reviewer") != reviewer: diff.append(f"复核→{reviewer}")
        if done_at and t.get("doneAt") != done_at: diff.append(f"完成 {done_at}")
        if claimed_at and t.get("claimedAt") != claimed_at: diff.append(f"认领 {claimed_at}")
        if not diff:
            continue

        t["status"] = status
        if owner: t["owner"] = owner
        if reviewer: t["reviewer"] = reviewer
        if claimed_at: t["claimedAt"] = claimed_at
        t["doneAt"] = done_at
        t["ghIssue"] = it["number"]
        today = datetime.date.today().isoformat()
        if status == "BLOCKED" and not t.get("blockedAt"):
            t["blockedAt"] = today
        if status != "BLOCKED":
            t["blockedAt"] = None
        t["updatedAt"] = today
        changes.append(f"{t['id']}: {'，'.join(diff)}（issue #{it['number']}）")

    # 依赖解锁：前置全部 DONE / Gate PASS 的 BLOCKED 任务 → READY
    for t in board["tasks"]:
        if t["status"] != "BLOCKED" or not t.get("deps"):
            continue
        ok = all(
            (tasks[d]["status"] == "DONE") if d in tasks else (gates.get(d, {}).get("status") == "PASS")
            for d in t["deps"]
        )
        if ok:
            t["status"] = "READY"; t["blocker"] = ""; t["blockedAt"] = None
            t["updatedAt"] = datetime.date.today().isoformat()
            changes.append(f"{t['id']}: 前置已满足，BLOCKED → READY（自动解锁）")

    # currentWave = 第一个存在未完成任务的 wave
    for w in board["waves"]:
        if any(t["wave"] == w["id"] and t["status"] != "DONE" for t in board["tasks"]):
            if board["meta"]["currentWave"] != w["id"]:
                changes.append(f"当前波次 → Wave {w['id']}")
                board["meta"]["currentWave"] = w["id"]
            break

    if not changes and not issues:
        print(f"仓库 {REPO} 暂无任务 Issue，看板保持计划初始状态。先在 GitHub 建 [Txx.x] Issue 后再同步。")
        return
    if not changes:
        print("无变化，GitHub 与看板一致。")
        return

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    board["meta"]["syncedAt"] = now
    board["meta"]["updatedAt"] = now[:10]
    board["meta"]["updatedBy"] = "sync_board.py（GitHub 同步）"
    board["log"].append({"at": now, "by": "GitHub 同步", "what": "；".join(changes)})

    print("变更：")
    for c in changes: print(" -", c)
    if dry:
        print("--dry-run，未写文件"); return

    payload = json.dumps(board, ensure_ascii=False, indent=2)
    BOARD.write_text(payload, encoding="utf-8")
    if WIDGET_BOARD.exists():
        WIDGET_BOARD.write_text(payload, encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "render_board.py")], check=True)
    print("board.json 已更新，公网页面已重建。")

    if "--publish" in sys.argv:
        # 公网看板 = 本目录的 GitHub Pages（仓库根 index.html），push 即刷新
        import shutil
        shutil.copy(ROOT / "dist" / "index.html", ROOT / "index.html")
        subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
        r = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
        if r.returncode != 0:
            subprocess.run(["git", "-c", "user.name=minmin", "-c",
                            "user.email=mingminwang962-eng@users.noreply.github.com",
                            "commit", "-qm", f"sync: {now} 看板同步"], cwd=ROOT, check=True)
            subprocess.run(["git", "push", "-q"], cwd=ROOT, check=True)
            print("已发布 → https://mingminwang962-eng.github.io/wuxiaokong-board/")
        else:
            print("页面无变化，跳过发布。")

if __name__ == "__main__":
    main()
