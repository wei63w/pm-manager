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

1. 优先日常命令；模块深潜走 `/pm-all` 或 `/pm-discover`。
2. 对话粘贴是 `/pm-fix` 的一等证据。
3. `/pm-init`：检测 Spec Kit。若无，则分析项目并起草 `.pm/prd/prd.md`，等待用户确认。未确认的 PRD 禁止当作基线。
4. `.pm/` 仅本地 —— 写入 `.git/info/exclude`，禁止写入共享 `.gitignore`。地图、索引、评审、日志放在此处，禁止污染业务源码。
5. 先确认后写入：未经确认禁止自动修改应用代码/SQL/云资源，也禁止将生成文档/规范落盘。
6. 默认噪声过滤：blocking + high；`/pm-status` 列出未关闭的阻断与高优先级待办，**不以三条为上限**。
7. 优先读导航地图与文档索引，禁止默认全库递归。证据落盘前必须脱敏。
8. 评审/质量输出必须含推理链与引用片段；已确认问题沉淀进规范库。
9. 宪章、规格、计划、任务、PRD 正文中文优先；命令名与路径保持英文。用户以中文交互时，报告与待办必须中文。
10. 本功能实现约束：确认门；地图优先读 `map.json`；证据脱敏；状态不截断为三条；不把 V1.1（全量体检、Git 钩子、单测助手、高危徽标）当成本版本必做。

## 快速验证

```bash
pm init /path/to/project
# then in agent: /pm-init  /pm-status
```
