[English](./README.md) | **简体中文**

**📋 PM Manager**  
*知道下一步该修什么 — 适配任意 AI 编程助手。*

[![Release](https://img.shields.io/github/v/release/wei63w/pm-manager?logo=github&label=release)](https://github.com/wei63w/pm-manager/releases/latest)
[![Version](https://img.shields.io/badge/version-alpha-orange)](https://github.com/wei63w/pm-manager)
[![Downloads](https://img.shields.io/github/downloads/wei63w/pm-manager/total?label=downloads&color=brightgreen)](https://github.com/wei63w/pm-manager/releases)
[![Commit activity](https://img.shields.io/github/commit-activity/m/wei63w/pm-manager)](https://github.com/wei63w/pm-manager/commits/main)
[![License](https://img.shields.io/github/license/wei63w/pm-manager)](https://github.com/wei63w/pm-manager/blob/main/LICENSE)
[![skills.sh](https://skills.sh/b/wei63w/pm-manager)](https://skills.sh/wei63w/pm-manager)

开源技能包，用于**本地项目治理**：初始化 `.pm/` 工作台、查看当日未关闭待办、分诊粘贴的日志，以及做发布前健康扫描。布局借鉴 [Spec Kit](https://github.com/github/spec-kit) 的命令模板 + 多 Agent 适配器。可与 Spec Kit 并存：Spec Kit 管「做什么」；PM Manager 管「项目健康、下一步做什么」。

---

## 目录

- [PM Manager 是什么](#pm-manager-是什么)
- [快速开始](#快速开始)
- [CLI 参考](#cli-参考)
- [支持的 AI 编程助手](#支持的-ai-编程助手)
- [斜杠命令](#斜杠命令)
- [与 Spec Kit 的关系](#与-spec-kit-的关系)
- [核心原则](#核心原则)
- [日常流程](#日常流程)
- [仓库布局](#仓库布局)
- [前置条件](#前置条件)
- [支持](#支持)
- [许可证](#许可证)

## PM Manager 是什么

多数 AI 编程会话会直接改代码。**PM Manager 把日常循环反过来**：在本地、可审计的 `.pm/` 里维护健康度、待办、事故与发布门禁，再让助手列出**当日未关闭的阻断与高优先级工作**。

它**不是**云端项目管理套件，也**不是** Jira / Linear 的替代品。它是**开发者侧治理工作台**，落在仓库本地的 `.pm/`（git 排除），用斜杠命令 / 技能驱动，用法类似 Spec Kit 的 `/speckit.*`。

## 快速开始

### 1. 安装 Agent Skill（skills.sh）

```bash
npx skills@latest add wei63w/pm-manager
```

或将 `skills/pm-manager` 复制到工具的技能目录：

| 工具 | 路径 |
|------|------|
| Cursor | `~/.cursor/skills/pm-manager/` |
| Claude Code | `~/.claude/skills/pm-manager/` |
| Codex | `~/.agents/skills/pm-manager/` |

### 2. 安装 CLI（可选，跨平台）

需要 **[uv](https://docs.astral.sh/uv/)** 与 **Python 3.11+**。CLI 负责搭建 `.pm/` 并安装各助手适配器。

```bash
# 从 GitHub 安装（推荐）
uv tool install pm-manager-cli --from git+https://github.com/wei63w/pm-manager.git

# 或从本地检出安装
uv tool install --editable .
```

验证：

```bash
pm version
# 或
pm-manager version
```

之后升级：

```bash
uv tool upgrade pm-manager-cli
# 或从 git 强制重装
uv tool install pm-manager-cli --force --from git+https://github.com/wei63w/pm-manager.git
```

### 3. 在目标项目里初始化

在你的**业务仓库**中执行（不必长期检出本技能包）：

```bash
cd /path/to/your-app

# 创建 .pm/ + 安装 Cursor 与 Claude 适配器（默认；不需要 Node.js）
# 可选 skills.sh 索引：pm init --skills-sh
pm init

# 仅 Cursor
pm init --agent cursor

# 仅 Claude Code
pm init --agent claude

# 只搭 .pm/（不装助手文件，也不走 skills.sh）
pm init --scaffold-only

# 同时走 skills.sh 索引（需要 Node.js / npx）
pm init --skills-sh
```

不重新搭脚手架、只刷新适配器：

```bash
pm install --agent all
pm check
```

> Windows / macOS / Linux 命令相同。`scripts/powershell/` 下的旧 PowerShell 脚本仍可用，但**优先用** `pm init`。

### 4. 在助手里初始化治理

在项目中打开 Cursor / Claude Code，执行：

```text
/pm-init
```

- 识别**新项目 vs 已有项目**
- 检测仓库是否已用 **Spec Kit**（`.specify/memory/constitution.md` 或 `.specify/specs/**/*.md`）
- 若有 Spec Kit：导入宪章/规格，并请你确认
- 若**没有** Spec Kit：分析仓库（空仓可用一句话意图），起草 `.pm/prd/prd.md`，**等你确认**
- 补全 `pm init` 已搭好的文件系统（由助手填写 PRD / 宪章）
- 你确认或跳过之后会做**技术轻扫**（文档索引 + 地图），不必先跑 `/pm-all`

### 5. 查看当日状态

```text
/pm-status
```

会给出一行健康摘要，以及全部未关闭的阻断/高优先级待办（无助手时也可运行 `pm status`）。用 `/pm-next` 认领一条，用 `/pm-done TODO-001` 关闭。

### 6. 分诊事故

把堆栈或日志贴进对话：

```text
/pm-fix
```

对话粘贴是一等证据来源（不必先存成文件）。**本次只分诊，不改代码**；要改仓库须再确认。

### 7. 发布前全量扫描

```text
/pm-all
```

默认做**技术债扫描**（`prd.status=draft` 不拦截）。对照已确认基线时加 `--compare-baseline`。摘要默认噪声过滤（blocking + high）。完整列表加 `--verbose`。

扫描后用浏览器打开 **`.pm/dashboard/index.html`** 看可视化看板（KPI、图表、模块风险）；或在 IDE 里读 **`overview.md`**。随时可用 `pm dashboard` 重建。

## CLI 参考

| 命令 | 说明 |
|------|------|
| `pm version` | 打印 CLI 版本 |
| `pm init [path]` | 创建 `.pm/` + 安装助手适配器（默认不跑 Node/skills.sh） |
| `pm init --agent cursor\|claude\|all\|none` | 选择要安装的适配器 |
| `pm init --scaffold-only` | 只创建 `.pm/` |
| `pm init --skills-sh` | 额外执行 `npx --yes skills@latest add wei63w/pm-manager -y`（需要 Node） |
| `pm install --agent …` | 刷新适配器，不重新搭脚手架 |
| `pm check [path]` | 诊断 `.pm/`、地图、审计、`prd.status`、待处置评审 |
| `pm docs [path]` | 检测缺失/过期核心文档；`--draft` 只写 `.pm/docs/drafts/` |
| `pm map [query]` | 查询 `map.json`（模块 / 能力 / 路径） |
| `pm status [path]` | 现状快照 + 待办 + 本轮意图 + 优化建议 |
| `pm log [text]` | 脱敏并分类一条对话（`--kind` / `--intent` / `--file`） |
| `pm journal [path]` | 刷新时间线、变更点、本轮意图、优化建议 |
| `pm dashboard [path]` | 按模块 findings/todos 重建 `.pm/dashboard/` |
| `pm arch [path]` | 扫描 → Mermaid、`map.json`、`layer.mmd`、带注解目录树 |
| `pm tests [path]` | 列出单测缺口（不写业务树测试） |
| `pm review` | Diff 草稿 + `--cross` + 处置 + 回填草稿 |
| `pm rules` | 列出 / 启用 / 禁用 / 新增规范 |
| `pm checkup` | 按需五维体检（无定时器） |
| `pm gate --path` | 提交前门禁：密钥、语法、规范、P0、高危 |
| `pm hook install\|status\|uninstall` | 可选安装本地 `.git/hooks/pre-commit`（init 不自动装） |
| `pm config apply <template>` | 按 frontend/backend/service/script/auto 只补缺失键 |
| `pm export [path]` | 批量导出：审计、对话、快照、评审、缺口、guard、架构路径 |

`pm-manager` 是 `pm` 的别名。

## 支持的 AI 编程助手

| 助手 | 安装路径 | 调用方式 |
|------|----------|----------|
| **Cursor** | `.cursor/skills/pm-manager`（可选：`adapters/cursor/skills` 下按命令拆分的技能） | `/pm-init`、`/pm-status` … 或自然语言（「今天该做什么」） |
| **Claude Code** | `.claude/commands/pm-*.md` | `/pm-init`、`/pm-status` … |
| **其他技能宿主** | 以 `skills/pm-manager/SKILL.md` 为路由，进入 `templates/commands/` | 遵循宿主技能约定 |

无斜杠命令时的自然语言路由见 [`skills/pm-manager/memory/ROUTING.md`](./skills/pm-manager/memory/ROUTING.md)。

## 斜杠命令

### 日常命令（优先记住这些）

| 命令 | Agent 技能 | 说明 |
|------|------------|------|
| `/pm-init` | `pm-init` | 搭治理台、起草 PRD；确认或跳过后做技术轻扫 |
| `/pm-status` | `pm-status` | 健康 + 向导 + 未关闭阻断/高优先级待办 + 待处置评审 |
| `/pm-next` | `pm-next` | 认领下一条待办（`in_progress`） |
| `/pm-done` | `pm-done` | 关闭 `TODO-xxx`，刷新总览 |
| `/pm-fix` | `pm-fix` | 把粘贴日志解析成待办（**不改业务代码**） |

### 发布 / 质量 / 恢复

| 命令 | Agent 技能 | 说明 |
|------|------------|------|
| `/pm-all` | `pm-all` | 全量**技术**扫描 + 看板（草稿 PRD 不拦截） |
| `/pm-review` | `pm-review` | Diff 评审 + 交叉复核 + 沉淀规范 |
| `/pm-checkup` | `pm-checkup` | 按需体检（P0/P1/P2）；不进日常 status |
| `/pm-check` | `pm-check` | 诊断/修复 `.pm/`，不覆盖已确认文件 |
| `/pm-arch` | `pm-arch` | 生成架构图、地图与带注解目录树 |
| `/pm-docs` | `pm-docs` | 缺失/过期文档；草稿只在 `.pm/`，确认后才落正式路径 |
| `/pm-journal` | `pm-journal` | 本轮意图、迭代时间线、变更点、优化建议 |
| `/pm-tests` | `pm-tests` | 单测缺口；确认前不写测试文件 |

### 规划与导出

| 命令 | Agent 技能 | 说明 |
|------|------------|------|
| `/pm-outline` | `pm-outline` | 按意图生成大纲与宪章草稿 |
| `/pm-charter` | `pm-charter` | 无参数时向导：create / import / discover / approve / skip |
| `/pm-export` | `pm-export` | 脱敏 Markdown 摘要，便于分享或换机 |

`/pm-discover` 是内部步骤（由 `/pm-all` 调用），不要让用户单独跑。

命令提示词在 [`skills/pm-manager/templates/commands/`](./skills/pm-manager/templates/commands/)，带 Spec Kit 风格 frontmatter 与 `handoffs`。

## 与 Spec Kit 的关系

| Spec Kit | PM Manager |
|----------|------------|
| `.specify/` | `.pm/`（仅本地，不提交） |
| `/speckit.constitution` | `/pm-charter` + 自动发现宪章 |
| 规格 → 计划 → 任务 → 实现 | 状态 → 下一条 → 完成 / 分诊 / 全扫 |
| 规格驱动的**功能**交付 | 治理驱动的**项目健康** |

二者可在**同一仓库**运行。PM Manager 在检测到 Spec Kit 产物时会读取它们；它不替代规格驱动开发。

## 核心原则

治理正文以中文为准，见 [`.specify/memory/constitution.md`](./.specify/memory/constitution.md)（v1.1.1）。仓库默认 README 为英文；本文是中文版。摘要如下：

- **本地优先的持久资产** — 地图、索引、评审、日志放在 `.pm/`（git 排除）；跨会话可复用、可审计
- **先确认后写入** — 先报告；未经确认禁止自动改应用代码/SQL/云资源，也禁止把生成文档落盘
- **地图优先协作** — 助手先读导航地图与文档索引，再决定是否遍历目录
- **有证据的质量闭环** — 评审结论带推理链；已确认问题沉淀进规范库
- **日常状态不截断为三条** — `/pm-status` 列出未关闭的阻断/高优先级待办（不以 Top3 为上限）；粘贴是 `/pm-fix` 的一等证据
- **文档中文优先** — 宪章、规格、计划、任务、PRD 用中文写；CLI / 命令名保持英文
- **按需扫描** — 无后台守护进程；来源为粘贴 / `--path` / 已登记路径
- **可选宪章对照** — 无宪章时做技术债扫描；有宪章时做带**置信度**的「需求是否合理」对照

## 日常流程

| 时机 | 命令 |
|------|------|
| 仓库第一次接入 | `/pm-init`（确认或跳过，然后轻扫） |
| 早上 /「现在做什么」 | `/pm-status` → `/pm-next` |
| 做完一条待办 | `/pm-done TODO-xxx` |
| 生产 / 本地报错 | 粘贴 + `/pm-fix`（只分诊） |
| 本地改动要评 | `/pm-review` |
| 治理台看起来坏了 | `/pm-check` |
| 发布前 | `/pm-all` → `.pm/dashboard/` |
| 需要架构图 | `/pm-arch` 或 `pm arch` |
| 交接 / 换电脑 | `/pm-export` |

```text
/pm-init → /pm-status → /pm-done
         ↘ /pm-fix（事故）
         ↘ /pm-all  → .pm/dashboard/  （发布门禁 + 总览）
```

### 目标产物 `.pm/dashboard/`（`/pm-all` 或 `pm dashboard` 之后）

```text
.pm/dashboard/
  index.html    # 可视化看板 — 用浏览器打开
  overview.md   # IDE 表格：KPI、进度条、模块风险排序、热点/待办
  findings.md   # 汇总未关闭发现
  todos.md      # 汇总未关闭待办
  stats.json    # 计数 + health_score + module_risk
  README.md     # 与 overview.md 相同（入口别名）
```

## 仓库布局

```text
pm-manager/
  pyproject.toml                 # uv/pip 包（pm / pm-manager 入口）
  src/pm_manager_cli/            # 跨平台 CLI（含 pm dashboard）
  skills/pm-manager/             # 可安装的 Agent Skill（skills.sh）
    SKILL.md                     # 路由技能
    AGENTS.md                    # 面向助手的说明
    templates/commands/          # 斜杠/技能命令提示
    templates/pm/                # 复制进目标项目 .pm/ 的文件
    memory/ROUTING.md            # 自然语言 → 命令映射
  scripts/python/                # 薄封装（优先用 pm init）
  scripts/powershell/            # 旧版 Windows 辅助脚本
  adapters/cursor/               # Cursor 技能变体
  adapters/claude-code/          # Claude Code 命令文件
  skills.sh.json                 # skills.sh 分组
```

## 前置条件

- **Windows / macOS / Linux**
- [uv](https://docs.astral.sh/uv/)（推荐）用于 `uv tool install`
- **Python 3.11+**
- **Git**（用于写入 exclude 规则）
- 支持技能或项目斜杠命令的 AI 编程助手（推荐 Cursor 或 Claude Code）
- 可选：[Spec Kit](https://github.com/github/spec-kit)，若你已在用宪章/规格

## 支持

问题与缺陷请开 [GitHub issue](https://github.com/wei63w/pm-manager/issues/new)。

## 许可证

本项目采用 [MIT License](./LICENSE)。
