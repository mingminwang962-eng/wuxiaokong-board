# 悟小空作战看板 · Agent 交接文档

> 给负责「看板自动同步」的 agent：看完这份文档即可独立接手，不需要问人。
> 看板仓库：`mingminwang962-eng/wuxiaokong-board`（公开，GitHub Pages 站点）
> 源仓库：`mingminwang962-eng/ip-system-runtime`（私有，任务事实都在这里）

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

## 你要做的事：让同步跑起来

任选一种方式，目标是「GitHub 上的任务事实变化后，看板 20 分钟内自动刷新」：

### 方式 A：任何机器上定时跑（最简单，推荐先跑通）

```bash
git clone git@github.com:mingminwang962-eng/wuxiaokong-board.git
cd wuxiaokong-board
# 需要 gh CLI 已登录且能读 ip-system-runtime
python3 sync_board.py --publish
```

挂 cron / launchd / 你所在的 agent 调度器，每 20 分钟跑一次即可。同步失败脚本会 exit 2 且**不覆盖旧页面**，你需要做的是告警（比如开一个 `board-alert` Issue）。

### 方式 B：GitHub Actions（不依赖任何本机）

在看板仓库建 `.github/workflows/sync.yml`：

```yaml
name: board-sync
on:
  schedule: [{ cron: "*/20 * * * *" }]
  workflow_dispatch:
concurrency: { group: board-sync, cancel-in-progress: false }
permissions: { contents: write, issues: write }
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - env: { GH_TOKEN: ${{ secrets.SOURCE_REPO_TOKEN }} }
        run: python3 sync_board.py --ci --apply-labels
      - run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add board.json index.html dist/index.html
          git diff --cached --quiet || { git commit -m "sync: 看板自动同步"; git push; }
      - if: failure()
        env: { GH_TOKEN: ${{ secrets.GITHUB_TOKEN }} }
        run: gh issue create --title "⚠️ 看板同步失败" --body "线上看板保留上一版本，请查 Actions 日志与 SOURCE_REPO_TOKEN。" --label "board-alert" || true
```

前提：看板仓库 Secrets 里配 `SOURCE_REPO_TOKEN`（能读私有源仓库的 PAT）。**没配好之前不要启用 schedule，否则每 20 分钟失败+告警刷屏。**

### 方式 C（可选增强）：事件驱动

在源仓库 `ip-system-runtime` 加一个 workflow，监听 issues/pull_request 事件后 `repository_dispatch` 到看板仓库触发方式 B。需要 PAT。可选，定时轮询已经够用。

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
- 自动贴签需要 `sync_board.py --apply-labels`（方式 B 已带）

### 人员

`people.json` 已登记：`mingminwang962-eng`=敏敏、`lyx680805-first`=夏天。负责人=复核人会被标红；未登记账号不会直接显示用户名。

### 依赖解锁

前置任务 DONE / Gate PASS 后，下游 BLOCKED 自动转 READY，由 sync 完成，不用人管。

## GitHub 协作约定（源仓库这边怎么操作）

- Issue 标题 `[T00.1] xxx`；assignee=认领人；label `reviewer:敏敏`/`reviewer:夏天` 标复核人
- 状态 label：`state:blocked` / `state:in-review` / `state:ready-for-gate` / `state:observing`
- 证据确认 label：`evidence:ok`
- Gate：`[GATE-WG0]`…`[GATE-WG7]` 标题的 Issue
- PR 标题必须含 `[Txx.x]`

## 改完同步器必须过自检

```bash
python3 sync_board.py --selftest   # 8 项伪造攻击测试，全过才允许交付
```

## 公网地址

- https://mingminwang962-eng.github.io/wuxiaokong-board/
- https://raw.githack.com/mingminwang962-eng/wuxiaokong-board/main/index.html （国内推荐）

两个地址都随 push 自动刷新，无需额外发布动作。

## 生产边界

R10、R11 与一切生产动作永远 HOLD；看板不接受「生产已发布」类状态。
