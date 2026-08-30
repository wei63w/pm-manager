# AGENTS.md — PM Manager

本仓库是面向本地项目治理（`.pm/`）的 **Spec Kit 风格**技能包。

治理正文以 [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) v1.1.2 为准（中文优先）。

## 布局（对照 Spec Kit）

| 路径 | 角色（类似 Spec Kit） |
|------|----------------------|
| `templates/commands/*.md` | 斜杠/技能命令提示（Spec Kit 的 `templates/commands`） |
| `templates/pm/*` | 复制进目标项目 `.pm/` 的产物 |
| `scripts/python\|powershell` | 确定性脚手架（仓库根目录） |
| `adapters/cursor` | Cursor Agent Skills 安装（仓库根目录） |
| `adapters/claude-code` | Claude Code 斜杠命令（仓库根目录） |
| `SKILL.md` | Cursor / 技能宿主的路由技能 |
| 设计文档 | 仅本地 `pm-manager-v*.md`（gitignore / 不发布） |

## Agent 规则

与宪章 v1.1.2 对齐：

1. 优先日常五条：`/pm-init` `/pm-status` `/pm-next` `/pm-done` `/pm-fix`；发布前 `/pm-all`。地图用 `pm map` / `/pm-arch`；文档用 `/pm-docs`；开发记录用 `pm log` / `/pm-journal`。不要让用户跑 `/pm-discover`。
2. 对话粘贴是 `/pm-fix` 的一等证据。先声明：本次只分诊，不改代码。
3. `/pm-init`：检测 Spec Kit。若无，则分析项目并起草 `.pm/prd/prd.md`，等待用户确认。确认或跳过之后做技术轻扫（文档索引 + 地图）。未确认的 PRD 禁止当作基线。
4. `.pm/` 仅本地 —— 写入 `.git/info/exclude`，禁止写入共享 `.gitignore`。地图、索引、评审、日志放在此处，禁止污染业务源码。
5. 先确认后写入：未经确认禁止自动修改应用代码/SQL/云资源，也禁止将生成文档/规范落盘。
6. 默认噪声过滤：blocking + high；`/pm-status` 列出未关闭的阻断与高优先级待办，**不以三条为上限**。有待处置评审时提示 `/pm-review`。
7. 优先读导航地图与文档索引，禁止默认全库递归。证据落盘前必须脱敏。
8. 评审走 `/pm-review` / `pm review`：推理链 + 片段；交叉复核 `--cross`；`confirm` / `false_positive` / `later`；仅 confirmed 进规范库。回填只写 `.pm/reviews/annotations/`。按需体检 `/pm-checkup`，不要默认绑进 `/pm-status` 或 `/pm-all`。
9. 宪章、规格、计划、任务、PRD 正文中文优先；命令名与路径保持英文。用户以中文交互时，报告与待办必须中文。
10. 元数据损坏用 `/pm-check`（可 `repair`）。增强能力可用：`pm tests` / `/pm-tests`、`pm gate`、可选 `pm hook`、`pm config apply`、地图 `risk_files`。日常不强制。周期性全量体检仍不做。
11. `/pm-all` 默认技术扫描，不因 `prd.status=draft` 拦截；对照基线才用 `--compare-baseline`。

## 快速验证

```bash
pm init /path/to/project
# then in agent: /pm-init  /pm-status
```
