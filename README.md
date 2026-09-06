# 悟小空作战看板 · 公网版

任何 agent（Kimi / Claude Code / Codex）都可以维护这个看板。**看板只是投影，GitHub 才是事实源。**

## 文件

| 文件 | 作用 |
|-|-|
| `board.json` | 看板数据正本（48 任务 / 8 Wave / WG0–WG7）。**不要手改状态**，由 sync 脚本从 GitHub 同步 |
| `sync_board.py` | 从 GitHub 拉取 Issue/PR 真实状态 → 更新 board.json → 重建页面 → 可选重新发布 |
| `render_board.py` | 把 board.json 渲染成 `dist/index.html`（公网页面） |
| `dist/index.html` | 生成的公网看板（自包含单文件，无外部依赖） |
| `publish.json` | 妙搭发布配置（app_id），首次部署后生成 |

## 日常工作流

1. 在 GitHub 仓库 `mingminwang962-eng/ip-system-runtime` 上操作任务（见下方约定）
2. 任何 agent 运行 `python3 sync_board.py --publish`
3. 看板自动更新，公网链接内容自动刷新

## GitHub 协作约定（认领、状态全靠它）

- Issue 标题以任务号开头：`[T00.1] 冻结候选与机器清单`
- **认领人 = Issue assignee**。GitHub 用户名映射在 `sync_board.py` 顶部 `ASSIGNEE_MAP`（敏敏已配置；夏天的用户名确定后补一行）
- 复核人用 label：`reviewer:敏敏` / `reviewer:夏天`
- 状态 label：`state:blocked` / `state:in-review` / `state:ready-for-gate` / `state:observing`；无 label 时：open+有 assignee=进行中，open+无 assignee=可认领，closed=已完成
- Gate 用 `[GATE-WG0]` … `[GATE-WG7]` 标题的 Issue，closed 即 PASS
- 时间自动提取：认领时间=assigned 事件，完成时间=closedAt，阻塞起始=进入 blocked 当天，耗时自动计算

## 状态机纪律（计划 v1.2 §11.3）

自测最高到「待审查」，不得自批完成；Gate 未通过不得推进下游；R10/R11 与生产动作永远 HOLD。
