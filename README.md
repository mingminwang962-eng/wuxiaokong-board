# 悟小空作战看板 · 公网版（可信化 v2）

任何 agent（Kimi / Claude Code / Codex）都可以维护这个看板。**GitHub 是唯一事实源，看板只是它的机器生成投影。**

公网地址：
- https://mingminwang962-eng.github.io/wuxiaokong-board/
- https://raw.githack.com/mingminwang962-eng/wuxiaokong-board/main/index.html （国内推荐）

## 文件

| 文件 | 作用 | 能否手改 |
|-|-|-|
| `plan.json` | 静态计划：Wave / Gate / 48 任务骨架（标题、依赖、关键路径） | ✅ 只能改这里 |
| `people.json` | GitHub 账号 → 显示名 / 角色映射 | ✅ 只能改这里 |
| `board.json` | **纯生成物**，sync 每次整体重建 | ❌ 必须由同步脚本生成 |
| `index.html` / `dist/index.html` | 生成的看板页面 | ❌ 必须由同步脚本生成 |
| `sync_board.py` | 同步器：GitHub 事实 → board.json → 页面 → 发布 | 改逻辑 |
| `render_board.py` | 页面渲染 | 改样式 |

## 可信化规则（核心）

### 任务 DONE 的四级条件

关闭 Issue 只代表「施工结束」。DONE 必须同时满足：

1. 存在已合并的关联 PR（PR 标题含 `[Txx.x]`）
2. 该 PR 的自动测试全部通过
3. 有**非实施者**的 APPROVED 审核（实施者自批无效）
4. Issue 带 `evidence:ok` 标签（证据清单：候选 commit、测试结果、回滚方式）

缺哪一级，看板最多显示到「待审查」或「待过门」，并以 ⚠ 旗标说明缺什么。

### Gate 只认机器

- 人工关闭 Gate Issue **不产生 PASS**（显示 HOLD）
- 机器（sync --apply-labels / Actions）核对「本 Wave 任务全部 DONE 且无旗标」后才贴 `gate:pass` 标签，并评论记录 `candidate:<sha>`
- 候选代码变化（SHA 不匹配）→ 旧 PASS 自动失效为 HOLD

### 人员

- 显示名只来自 `people.json`；未登记账号不会把 GitHub 用户名直接显示出来
- 负责人 = 复核人 → 看板标红

## GitHub 协作约定

- Issue 标题 `[T00.1] xxx`；assignee = 认领人；`reviewer:敏敏` / `reviewer:夏天` 标复核人
- 状态 label：`state:blocked` / `state:in-review` / `state:ready-for-gate` / `state:observing`
- 证据确认 label：`evidence:ok`
- Gate：`[GATE-WG0]` … `[GATE-WG7]` 标题的 Issue；PASS 只能由机器贴 `gate:pass`
- PR 标题必须含 `[Txx.x]`（同步器据此关联任务）

## 准备进度与动态更新

看板分开显示「准备与审核」和「正式施工」。未建 Issue 的父工作包显示待建单；草稿数量不计入施工完成率。

- 准备事实源：私有仓 `mingminwang962-eng/wuxiaokong-work` 的 `status/board-preparation.json`。完成修订、收到审核或转出任务时，由经办人按实际记录更新并提交；同步器不会猜测审核结论。
- `preparation.py` 只公开固定阶段、数量、时间、提交链接；私有文档正文和任意附加字段不会进入公开页面。
- 正式施工事实源：`lyx680805-first/ip-system-runtime` 的 Issue/PR。无 Issue 显示 `PLANNED`，未分配 Issue 没有 `status:ready` 时显示 `TRIAGED`。
- 本机 Codex 心跳任务每 20 分钟运行 `python3 -B sync_board.py --publish`，使用已有 gh 登录态。需要本机 Codex 可运行且网络正常；这不是云端常驻服务。
- 页面每 60 秒读取最新已发布 `board.json`；返回前台或点击「刷新看板」也会检查。GitHub Pages 发布可能另有短暂延迟。
- 显示同步时间，超过 45 分钟提示过期。拉取失败保留旧页面；网页读取失败保留当前快照。
- 同步有本机文件锁；自动提交只允许三个生成文件，不顺带提交人工修改。

当前没有安装 GitHub Actions 同步或 PR 守护工作流；此前文档对此的描述已纠正。若以后改为云端运行，需要另行配置能读两个私有仓的凭据。

**当前限制：** 施工统计仍沿用旧父工作包 Issue/PR 关联规则。正式原子任务转出前，需按修订后的规则补上子任务、Gate 与证据汇总；不能把本轮展示改造当作该聚合规则已完成。

## 状态机纪律（计划 v1.2 §11.3）

自测最高到「待审查」，不得自批完成；Gate 未通过不得推进下游；R10/R11 与生产动作永远 HOLD。

## 自检

`python3 sync_board.py --selftest`：八项伪造攻击测试（手工关单、测试失败、自我审核、缺证据、人工关 Gate、候选变化失效等），全过才允许交付同步器改动。

准备状态与失败保留测试：`python3 -B -m unittest test_preparation.py`。
