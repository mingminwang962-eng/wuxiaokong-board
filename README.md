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
| `board.json` | **纯生成物**，sync 每次整体重建 | ❌ 手改会被 PR 守护拦截 |
| `index.html` / `dist/index.html` | 生成的看板页面 | ❌ 同上 |
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

## 自动同步（GitHub Actions）

`.github/workflows/sync.yml`：每 20 分钟 + 手动触发；单并发防覆盖；失败保留旧页面并自动开告警 Issue。

**首次启用需要一次性配置**：仓库 Settings → Secrets 添加 `SOURCE_REPO_TOKEN`（一个能读取私有源仓库 `ip-system-runtime` 的 PAT），否则 Actions 无法读取任务 Issue。

`.github/workflows/guard.yml`：PR 中手改 `board.json` / 页面文件直接失败——状态只能从 GitHub 事实生成。

本地手动同步仍然可用：`python3 sync_board.py --publish`（用本机 gh 登录态）。

## 状态机纪律（计划 v1.2 §11.3）

自测最高到「待审查」，不得自批完成；Gate 未通过不得推进下游；R10/R11 与生产动作永远 HOLD。

## 自检

`python3 sync_board.py --selftest`：八项伪造攻击测试（手工关单、测试失败、自我审核、缺证据、人工关 Gate、候选变化失效等），全过才允许交付同步器改动。
