"""私有工作仓 → 公开看板的最小状态投影；不传递任意正文。"""
import datetime
import re

WORK_REPO = "mingminwang962-eng/wuxiaokong-work"
PHASES = {
    "drafting": ("任务草稿整理中", "补齐本批草稿和准入字段"),
    "revising": ("按审核意见修订中", "提交新固定版本，交叉复核差异"),
    "awaiting_review": ("本轮草稿已修订，等待差异复核", "夏天复核新版本；通过后再按条件转正式任务"),
    "template_approved": ("模板已通过，继续分批整理", "优先补齐首张任务准入；条件齐即开工，不等待全部草稿"),
    "issuing": ("正在转出正式任务", "核对Issue内容和链接，原草稿停止维护任务状态"),
}
EVENTS = {
    "draft_created": "首批草稿已提交",
    "revision_submitted": "草稿修订和自检记录已提交",
    "review_received": "已记录新一轮审核意见",
    "template_approved": "已记录模板复核通过",
    "issue_transfer_started": "开始按准入条件转出任务",
}


def sha(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("准备进度必须绑定完整Git提交")
    return value


def timestamp(value):
    parsed = datetime.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("准备事件时间必须包含时区")
    return parsed.isoformat()


def project_preparation(record, record_sha):
    if record.get("schemaVersion") != 1 or record.get("phase") not in PHASES:
        raise ValueError("不支持的准备进度版本或阶段")
    counts = {}
    for key in ("parentDrafts", "atomicDrafts", "detailedSamples", "selfCheckGroups"):
        value = record.get("counts", {}).get(key)
        if type(value) is not int or not 0 <= value <= 10000:
            raise ValueError("准备数量无效")
        counts[key] = value
    if counts["detailedSamples"] > counts["atomicDrafts"]:
        raise ValueError("详细样例数大于原子草稿数")
    phase = record["phase"]
    title, next_step = PHASES[phase]
    sample_sha = sha(record["sampleCommit"])
    events = []
    for event in record.get("events", [])[-20:]:
        if event.get("kind") not in EVENTS:
            raise ValueError("未知准备事件")
        commit = sha(event["commit"])
        events.append({"at": timestamp(event["at"]), "title": EVENTS[event["kind"]],
                       "url": f"https://github.com/{WORK_REPO}/commit/{commit}"})
    # 明确列举字段，不spread输入；任意额外正文/链接不会进入公开产物。
    return {"phase": phase, "title": title, "nextStep": next_step,
            "counts": counts, "updatedAt": timestamp(record["updatedAt"]),
            "sampleCommit": sample_sha, "recordCommit": sha(record_sha),
            "sampleUrl": f"https://github.com/{WORK_REPO}/commit/{sample_sha}",
            "recordUrl": f"https://github.com/{WORK_REPO}/blob/{record_sha}/status/board-preparation.json",
            "events": events}
