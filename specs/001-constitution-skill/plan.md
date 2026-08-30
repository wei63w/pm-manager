# Implementation Plan: 按宪章交付治理技能

**Branch**: `001-constitution-skill` | **Date**: 2026-08-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-constitution-skill/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

**语言**: 填写后的 `plan.md` 正文必须为中文（章节标题可保留本模板英文结构名，便于 `/speckit-*` 识别）。代码标识符、路径、命令名保持英文。

## Summary

把宪章 v1.1.1 的四条原则落实到现有 PM Manager：**Agent 技能模板**负责确认门、评审证据、状态展示与中文输出；**CLI** 负责确定性脚手架、`.pm/` 排除、增量扫描与导航地图。不新起云端服务、不引入后台守护进程。V1.1（全量体检、Git 钩子、单测助手、高危徽标）不进入本计划。

技术路径：在 `skills/pm-manager/templates/commands/` 按契约改命令行为；在 `src/pm_manager_cli/` 补审计、脱敏、地图 JSON、增量扫描；`project.yaml` 去掉 `top_n: 3`；Cursor / Claude 适配器与源模板保持同步。

## Technical Context

**Language/Version**: Python 3.11+（CLI / pytest）；Agent 命令为 Markdown 技能模板

**Primary Dependencies**: 现有 `typer`、`rich`；不新增运行时依赖。开发依赖 `pytest>=7`

**Storage**: 目标仓库本地 `.pm/` 文件树（Markdown / YAML / JSON），无数据库

**Testing**: pytest（CLI、脚手架、脱敏、扫描、Spec Kit 探测）；技能行为用契约清单 + 手工走查

**Target Platform**: Windows / macOS / Linux 本地；Cursor 与 Claude Code 编码助手

**Project Type**: CLI + 可安装 Agent Skill 包（非 Web、非移动）

**Performance Goals**: 中小型仓库全量扫描 ≤30s，增量 ≤5s，地图/资产加载秒级；单次变更评审（Agent）≤15s 体感

**Constraints**: 默认只报告；写入业务代码/正式文档必须用户确认；`.pm/` 仅经 `.git/info/exclude` 排除；按需扫描，禁止后台常驻；用户中文交互时待办/评审/报告中文

**Scale/Scope**: 单人本地、单仓库治理台；V1.0 技能行为对齐宪章，不覆盖多人同步

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

对照 `.specify/memory/constitution.md` v1.1.1。本计划 **全部 PASS**，Complexity Tracking 为空。

| 门禁 | 判定 | 本计划如何满足 |
|------|------|----------------|
| I. 本地优先的持久资产 | PASS | 资产只写 `.pm/`；`pm init` 继续写 `.git/info/exclude`；审计落 `.pm/evidence` 与 `.pm/state` |
| II. 先确认后写入 | PASS | 命令模板强制草案 → 确认；未确认 PRD/宪章不得当基线 |
| III. 地图优先协作 | PASS | CLI 生成地图 JSON + Mermaid 到 `.pm/`；技能要求先读地图/索引 |
| IV. 有证据的质量闭环 | PASS | 评审契约强制推理链 + 片段；规范库沉淀；不含 V1.1 体检/钩子 |
| 粘贴即证据与脱敏 | PASS | `/pm-fix` 以对话粘贴为一等证据；落盘前脱敏；状态不截断为三条 |
| 文档中文优先 | PASS | 本计划与后续 tasks 正文中文；命令名保持英文 |
| NFR | PASS | 扫描走增量 + 忽略清单；无守护进程；单文件失败隔离 |

**Phase 1 复检**：契约与数据模型仍只扩展 `.pm/` 内实体，无业务树默认写入，无 V1.1 范围渗入。判定保持 PASS。

## Project Structure

### Documentation (this feature)

```text
specs/001-constitution-skill/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md             # /speckit-tasks 生成，本命令不创建
```

### Source Code (repository root)

```text
src/pm_manager_cli/
├── cli.py                 # pm init / arch / dashboard / check
├── scaffold.py            # .pm/ 骨架 + git exclude
├── speckit.py             # Spec Kit / PRD 探测
├── architecture.py        # 扫描 + Mermaid（将扩展地图 JSON / 增量）
├── dashboard.py
├── agents.py              # 适配器安装
└── paths.py

skills/pm-manager/
├── SKILL.md
├── AGENTS.md
├── templates/commands/    # /pm-* 行为源（本功能主改）
└── templates/pm/          # 复制进目标 .pm/

adapters/cursor/skills/
adapters/claude-code/commands/

tests/
└── test_speckit.py        # 将扩展 scaffold / 脱敏 / 扫描
```

**Structure Decision**: 沿用现有单包布局。不新增 apps/frontend。确定性能力放 CLI；需推理的确认流、评审、分诊放技能模板。适配器从 `templates/commands/` 同步，禁止只改一侧。

## Complexity Tracking

> 无宪章违规，本表留空。

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
