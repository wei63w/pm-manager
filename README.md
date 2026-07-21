# PM Manager

本地项目治理工作台（参考 [github/spec-kit](https://github.com/github/spec-kit) 的命令模板 + 脚手架脚本 + 多 Agent 适配模式）。

设计基线文档（`pm-manager-v*.md`）不纳入本仓库，仅在本地维护。

## 黄金路径

```text
/pm-init → /pm-status → /pm-done
出事粘贴日志 → /pm-fix
发版前 → /pm-all
```

## 安装

### Cursor

将本目录（或 `adapters/cursor/skills/*`）复制到项目 `.cursor/skills/` 或个人 `~/.cursor/skills/`：

```powershell
# 从本仓库根目录
.\pm-manager\scripts\powershell\install-cursor.ps1 -TargetProject "D:\your\app"
```

或手动：复制 `pm-manager/SKILL.md` 到 `.cursor/skills/pm-manager/SKILL.md`，并保证 `templates/`、`scripts/` 相对路径可访问（推荐整个 `pm-manager` 作为 skill 目录）。

### Claude Code

```powershell
.\pm-manager\scripts\powershell\install-claude.ps1 -TargetProject "D:\your\app"
```

会将 `adapters/claude-code/commands/*.md` 安装到目标项目的 `.claude/commands/`（命令名 `pm-init` 等，对话中用 `/pm-init`）。

### 仅脚手架（无 Agent）

```bash
python pm-manager/scripts/python/create_pm_scaffold.py /path/to/project
```

## 与 Spec Kit 的关系

| Spec Kit | PM Manager |
|----------|------------|
| `.specify/` | `.pm/`（治理状态，本地不提交） |
| `constitution` | `/pm-charter` + 自动发现 `.specify/memory/constitution.md` |
| `templates/commands` | `templates/commands` |
| `specify` CLI 脚手架 | `scripts/*/create_pm_scaffold*` |
| 功能规格驱动开发 | 项目健康度 / 待办 / 事故 / 发版门禁 |

二者可并存：Spec Kit 管「功能怎么做」，PM Manager 管「项目是否健康、今天做什么」。

## 目录

```text
pm-manager/
  SKILL.md
  AGENTS.md
  templates/commands/     # 命令提示词（spec-kit 风格 frontmatter + handoffs）
  templates/pm/           # 写入目标仓库 .pm/ 的模板
  scripts/python|powershell
  adapters/cursor|claude-code
  memory/ROUTING.md
```
