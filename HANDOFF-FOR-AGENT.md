# 悟小空作战看板 · Agent 交接文档

> 给负责「看板自动同步」的 agent：看完这份文档即可独立接手，不需要问人。
> 看板仓库：`mingminwang962-eng/wuxiaokong-board`（公开，GitHub Pages 站点）
> 源仓库：`lyx680805-first/ip-system-runtime`（夏天账号，私有，任务事实都在这里）
> ⚠️ 2026-09-07 系统所有者（敏敏）拍板：施工仓库=夏天仓 `lyx680805-first/ip-system-runtime`。`mingminwang962-eng/ip-system-runtime` 是敏敏账号下的旧副本（仅剩 6 月旧 minmin 分支），**不是施工仓库，别去那边开 Issue/PR**。看板同步默认仓库已随之改指夏天仓。

## 这个系统是什么

悟小空系统修复项目（计划 v1.2）的进度看板。48 个父工作包 T00.1–T07.6、8 个 Wave、8 个出口门 WG0–WG7。执行人：敏敏、夏天。

**核心原则：GitHub 是唯一事实源，看板只是机器生成的投影。** 任何人说「我做完了」都不算数，只有 GitHub 上的 Issue/PR/测试/审核记录算数。

## 看板仓库文件

| 文件 | 作用 | 手改？ |
|-|-|-|
| `plan.json` | 静态计划：Wave/Gate/任务骨架（标题、依赖、关键路径） | ✅ 唯一可手改的计划数据 |
| `people.json` | GitHub 账号 → 显示名（敏敏/夏天） | ✅ 可手改 |
| `sync_board.py` | 同步器：拉 GitHub → 重建 board.json → 渲染页面 → 发布 | 改逻辑 |
| `render_board.py` | board.json → 页面 | 改样式 |
| `board.json` / `index.html` / `dist/index.html` | **纯生成物** | ❌ 禁止手改 |

## 当前同步方式

已使用本机 Codex 当前任务的心跳调度，每 20 分钟同步一次。不要重复建立 cron、launchd 或 GitHub Actions。需要本机 Codex 和网络可用；页面每 60 秒检查发布快照，超过 45 分钟未同步会提示。

执行目录 `/Users/minmin/Documents/wuxiaokong-board`。先检查工作树；干净时 `git pull --ff-only`，再运行 `python3 -B sync_board.py --publish`。有人工改动或分支分歧先保留现场，不强制覆盖。脚本只提交 `board.json`、`dist/index.html`、`index.html`；读取失败保留旧快照。定时任务不使用 `--apply-labels`，不写 Issue 评论，不进行施工操作。

准备进度来自私有工作仓 `mingminwang962-eng/wuxiaokong-work` 的 `status/board-preparation.json`。经办人在真实修订、审核事件后更新该记录并提交。同步器固定提交读取，只公开白名单字段。具体字段与阶段见工作仓 `status/README.md` 和本仓 `preparation.py`。

准备数量不计入正式完成率；尚未建单显示 `PLANNED`。当前施工判定仍是旧父工作包关联规则，正式原子任务转出前还需实现子任务/Gate/证据汇总，不能将本次动态展示更新当作该项已完成。

## 同步器的裁决规则（改逻辑前先读懂）

### 任务 DONE 的四级条件（缺一不算完成）

1. Issue 已关闭
2. 存在已合并的关联 PR（PR 标题含 `[Txx.x]`）
3. PR 的自动测试（statusCheckRollup）全部通过
4. 有**非实施者**的 APPROVED 审核（自批无效）
5. Issue 带 `evidence:ok` 标签（证据清单：候选 commit、测试结果、回滚方式）

缺哪级降级到哪级：`READY_FOR_REVIEW`（缺 PR/测试/审核）或 `READY_FOR_GATE`（只缺证据），页面 ⚠ 旗标说明缺什么。

### Gate 只认机器

- 人工关闭 Gate Issue = HOLD，不是 PASS
- 机器核对「本 Wave 任务全部 DONE 且无旗标」后贴 `gate:pass` 标签并评论 `candidate:<sha>`
- 候选 SHA 变化 → 旧 PASS 自动失效为 HOLD
- 自动贴签需要 `sync_board.py --apply-labels`（当前心跳不使用此选项）

### 人员

`people.json` 已登记：`mingminwang962-eng`=敏敏、`lyx680805-first`=夏天。负责人=复核人会被标红；未登记账号不会直接显示用户名。

### 依赖解锁

未建单的工作包不会因依赖为空而变成可认领；正式准入需要任务记录。现有依赖裁决与父子汇总仍需在正式建单前按新规则完善。

## GitHub 协作约定（源仓库这边怎么操作）

- Issue 标题 `[T00.1] xxx`；assignee=认领人；label `reviewer:敏敏`/`reviewer:夏天` 标复核人
- 状态 label：`state:blocked` / `state:in-review` / `state:ready-for-gate` / `state:observing`
- 证据确认 label：`evidence:ok`
- Gate：`[GATE-WG0]`…`[GATE-WG7]` 标题的 Issue
- PR 标题必须含 `[Txx.x]`

## 改完同步器必须过自检

```bash
python3 -B sync_board.py --selftest
python3 -B -m unittest test_preparation.py
```

## 公网地址

- https://mingminwang962-eng.github.io/wuxiaokong-board/
- https://raw.githack.com/mingminwang962-eng/wuxiaokong-board/main/index.html （国内推荐）

两个地址都随 push 自动刷新，无需额外发布动作。

## 生产边界

R10、R11 与一切生产动作永远 HOLD；看板不接受「生产已发布」类状态。

## 首卡转出后的显示

`plan.json`的atomicTaskIds登记执行版原子ID。公开投影只显示已建Issue的ID、状态、登记负责人和Issue/PR链接，不公开私有正文。原子待审不推进父Epic或Gate；父子收口聚合仍待适配。当前候选分支改为已从8acd建立的`codex/wave0-integration`，旧main和原staging基线不移动。首卡#4/PR#5处于待独立审核；适用保护与有效检查是合并门，不是要求实施前已有测试结果。
