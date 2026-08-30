---
description: "按宪章交付治理技能的实现任务清单"
---

# Tasks: 按宪章交付治理技能

**Input**: Design documents from `/specs/001-constitution-skill/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: 宪章要求 CLI / 脚手架 / 持久化必须有 pytest（成功路径 + 至少一条失败/隔离）。技能模板行为用契约 Done When，不为本功能上 Agent 集成测试框架。

**Organization**: 按用户故事分组，便于独立实现与验收。

**语言**: 任务描述、Goal、Independent Test 为中文。文件路径、符号名、命令保持英文。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、无未完成依赖）
- **[Story]**: 用户故事标签（仅故事阶段）
- 每条必须含确切文件路径

## Path Conventions

- CLI: `src/pm_manager_cli/`、`tests/`
- 技能源: `skills/pm-manager/templates/commands/`、`skills/pm-manager/templates/pm/`
- 适配器必须与源模板同步: `adapters/cursor/skills/pm-*/SKILL.md`、`adapters/claude-code/commands/pm-*.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 确认沿用现有单包，不新增运行时依赖

- [X] T001 核对 `pyproject.toml` 保持 Python ≥3.11 且不新增运行时依赖（仅现有 typer/rich + 开发 pytest）
- [X] T002 [P] 在 `skills/pm-manager/AGENTS.md` 增加本功能实现备忘：确认门、地图优先、脱敏、状态不截断为三条、禁止 V1.1 范围

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 所有故事共用的治理台规则、脱敏、审计骨架、去掉 Top3 配置

**⚠️ CRITICAL**: 本阶段完成前不得开始用户故事实现

- [X] T003 从 `skills/pm-manager/templates/pm/project.yaml` 删除 `rules.top_n`，保留 `default_noise_filter: high`
- [X] T004 扩展 `src/pm_manager_cli/scaffold.py`：只经 `.git/info/exclude` 排除 `.pm/`，禁止改共享 `.gitignore`；不覆盖已有 `.pm/` 文件
- [X] T005 新增 `tests/test_scaffold.py`：exclude 写入、二次 scaffold 不覆盖用户文件、不改 `.gitignore`
- [X] T006 [P] 新增 `src/pm_manager_cli/redact.py`：密钥/PEM/token 形态替换为 `***`（见 research.md）
- [X] T007 新增 `tests/test_redact.py`：伪秘密被替换 + 无秘密文本保持原样
- [X] T008 [P] 新增 `src/pm_manager_cli/audit.py`：向 `.pm/state/audit.jsonl` 追加一行（ts、command、input_summary、output_summary）
- [X] T009 新增 `tests/test_audit.py`：写入一行可再读出；目录缺失时创建
- [X] T010 改 `skills/pm-manager/templates/commands/_closing.md`：去掉 Top3 用语，改为打开 overview/dashboard
- [X] T011 改各命令共享段（`skills/pm-manager/templates/commands/*.md` 的 Shared Workflow）：脱敏 → 审计 → 确认后才写业务树 → 状态不截断 blocking/high

**Checkpoint**: 脚手架可测、脱敏/审计模块可测、模板不再把 Top3 当硬门禁

---

## Phase 3: User Story 1 - 治理台一次建好、换会话还能用 (Priority: P1) 🎯 MVP

**Goal**: 目标仓库出现仅本地的 `.pm/`，二次会话加载已有资产，不强制全量重扫，不污染业务树

**Independent Test**: `pm init` 空 git 仓库 → `.pm/` 出现且 `.gitignore` 未改 → 再 `pm init` 不丢用户改过的文件 → 新对话 `/pm-status` 能读到配置

- [X] T012 [US1] 扩展 `src/pm_manager_cli/scaffold.py` 按 data-model 补齐 `architecture/`、`evidence/scans/`、`state/` 占位（含 `audit.jsonl` 空文件可选）
- [X] T013 [US1] 改 `skills/pm-manager/templates/commands/init.md`：元数据有效时禁止强制全量重扫；损坏则提示修复/增量
- [X] T014 [P] [US1] 将 init 行为同步到 `adapters/cursor/skills/pm-init/SKILL.md` 与 `adapters/claude-code/commands/pm-init.md`
- [X] T015 [US1] 在 `tests/test_scaffold.py` 增加：无 git 时 exclude 跳过；有 `.pm/config/project.yaml` 时不重置

**Checkpoint**: US1 可单独演示跨会话治理台

---

## Phase 4: User Story 2 - 先确认基线，再允许写东西 (Priority: P1)

**Goal**: 初始化三分支（Spec Kit / 已有 PRD / 起草）均在确认前停下；未确认不当基线

**Independent Test**: 三类仓库走 `/pm-init` 均等待 confirm；拒绝文档草稿后正式路径未被覆盖

- [X] T016 [US2] 改 `skills/pm-manager/templates/commands/init.md`：Spec Kit 导入、已有 `docs/prd.md` 导入、否则起草；`confirm`/`revise`/`skip`；确认前禁止深潜
- [X] T017 [US2] 改 `skills/pm-manager/templates/commands/charter.md`：`approve` 才把宪章当基线；`skip` 不得用草稿做「需求是否合理」
- [X] T018 [P] [US2] 同步 `adapters/cursor/skills/pm-init/SKILL.md`、`adapters/cursor/skills/pm-charter/SKILL.md`、`adapters/claude-code/commands/pm-init.md`、`adapters/claude-code/commands/pm-charter.md`
- [X] T019 [US2] 确认 `src/pm_manager_cli/speckit.py` 与 `tests/test_speckit.py` 仍覆盖空 `.specify/`、宪章、规格、短 stub PRD

**Checkpoint**: US2 可单独演示确认门

---

## Phase 5: User Story 3 - 查看状态、推进待办，贴报错就能分诊 (Priority: P1)

**Goal**: 日常状态列出全部未关闭 blocking/high；粘贴即证据；脱敏；不改业务代码

**Independent Test**: 10 条 blocking/high 在 `/pm-status` 全部可见；`/pm-fix` 伪密钥不入盘且源码未改

- [X] T020 [US3] 改 `skills/pm-manager/templates/commands/status.md`：删除 Top3 上限与 Done When「Top3 <= 3」；列出全部 open/in_progress 的 blocking/high
- [X] T021 [P] [US3] 改 `skills/pm-manager/templates/commands/next.md` 与 `skills/pm-manager/templates/commands/done.md`：按优先级认领/关闭，不提 Top3
- [X] T022 [US3] 改 `skills/pm-manager/templates/commands/fix.md`：对话粘贴为一等证据；落盘前脱敏；默认不写业务代码
- [X] T023 [US3] 改 `skills/pm-manager/templates/pm/overview.md`：用「未关闭阻断/高优先级待办」替换「Today's Top3」三条列表
- [X] T024 [P] [US3] 同步 status/next/done/fix 到 `adapters/cursor/skills/pm-status/SKILL.md`、`pm-next/SKILL.md`、`pm-done/SKILL.md`、`pm-fix/SKILL.md` 以及 `adapters/claude-code/commands/pm-status.md`、`pm-next.md`、`pm-done.md`、`pm-fix.md`
- [X] T025 [US3] 改 `skills/pm-manager/SKILL.md`：description 与 How to execute 去掉「只给 Top3」，改为列出 blocking/high 且不截断

**Checkpoint**: US3 可单独演示状态与分诊

---

## Phase 6: User Story 4 - 先看地图，再打开文件 (Priority: P2)

**Goal**: `pm arch` / `/pm-arch` 写 `map.json` + Mermaid 到 `.pm/architecture/`；增量；忽略依赖目录

**Independent Test**: 含 `node_modules` 的仓库生成地图不含该目录；改一文件后再 arch 走增量；助手先读地图

- [X] T026 [US4] 扩展 `src/pm_manager_cli/architecture.py`：写出 `.pm/architecture/map.json`（modules/key_files/capabilities）；沿用 `SKIP_DIRS` + `scan.exclude_dirs`
- [X] T027 [US4] 在 `src/pm_manager_cli/architecture.py` 实现增量：已有地图时按 `mtime_hash` 只重算变更路径；单文件失败记 notes 不失败整批
- [X] T028 [US4] 新增 `tests/test_architecture.py`：忽略 `node_modules`；增量只触及变更文件；单文件失败不抛整批
- [X] T029 [US4] 改 `skills/pm-manager/templates/commands/arch.md`：先读 `map.json`；默认只写治理台；写入业务树必须确认
- [X] T030 [P] [US4] 同步 `adapters/cursor/skills/pm-arch/SKILL.md` 与 `adapters/claude-code/commands/pm-arch.md`

**Checkpoint**: US4 可单独演示地图优先

---

## Phase 7: User Story 5 - 缺的说明可补，改动可评，踩过的坑能留下 (Priority: P2)

**Goal**: 核心说明缺失清单 + 起草确认落盘；变更评审必须有推理与片段；确认问题沉淀规范

**Independent Test**: 缺文档走起草且未确认不覆盖；故意缺陷评审含推理+片段；确认后 rules 被后续加载

- [X] T031 [US5] 在 `skills/pm-manager/templates/commands/init.md`（及需要时 `all.md`）加入核心说明检测与双模式补齐（自备 / 起草后确认），索引写入 `.pm/state/doc-index.md`
- [X] T032 [US5] 新增 `skills/pm-manager/templates/pm/engineering/reviews.md` 评审条目模板（summary/reasoning/snippet/severity/disposition）
- [X] T033 [US5] 改 `skills/pm-manager/templates/commands/all.md` 与 `discover.md`：合格评审必须含推理与片段；无本地变更则明示无可评；P0 打断
- [X] T034 [US5] 新增 `skills/pm-manager/templates/pm/engineering/rules.md` 并在 all/init 流程中：仅 confirmed 写入；后续评审必须加载 enabled 规则
- [X] T035 [P] [US5] 同步 `adapters/cursor/skills/pm-all/SKILL.md`、`pm-discover/SKILL.md` 与 `adapters/claude-code/commands/pm-all.md`、`pm-discover.md`

**Checkpoint**: US5 可单独演示文档确认与有证据评审

---

## Phase 8: User Story 6 - 做过什么能查、能按时间段交出去 (Priority: P3)

**Goal**: 治理命令追加审计；对话摘要脱敏落盘；按时间导出

**Independent Test**: 连续 init/status/fix 后 `audit.jsonl` 有对应行；导出窗内可读且无秘密

- [X] T036 [US6] 在 Shared Workflow（`skills/pm-manager/templates/commands/*.md`）要求每次变更 `.pm/` 调用审计字段（命令名、输入/输出摘要；有推理则写上）
- [X] T037 [US6] 改 `skills/pm-manager/templates/commands/export.md`：按时间窗导出脱敏 Markdown，禁止秘密原文
- [X] T038 [US6] 在 `skills/pm-manager/templates/commands/fix.md` 与 `init.md` 增加对话摘要落盘到 `.pm/state/dialogue.md`（不可判断标 unresolved，禁止编造文件列表）
- [X] T039 [P] [US6] 同步 `adapters/cursor/skills/pm-export/SKILL.md` 与 `adapters/claude-code/commands/pm-export.md`

**Checkpoint**: US6 可单独演示审计导出

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: 文档、适配器一致性、quickstart、全量测试

- [X] T040 [P] 更新 `README.md` 与 `skills/pm-manager/AGENTS.md`，与宪章 v1.1.1（无 Top3 上限）保持一致
- [X] T041 [P] 改 `skills/pm-manager/templates/commands/outline.md` 共享段：去掉 Top3，未确认基线不当验收
- [X] T042 同步 `adapters/cursor/skills/pm-outline/SKILL.md` 与 `adapters/claude-code/commands/pm-outline.md`
- [X] T043 按 `specs/001-constitution-skill/quickstart.md` 走查一遍并记下缺口
- [X] T044 运行 `pytest` 确保 `tests/test_speckit.py`、`tests/test_scaffold.py`、`tests/test_redact.py`、`tests/test_audit.py`、`tests/test_architecture.py` 全绿
- [X] T045 抽查源模板与 Cursor/Claude 适配器无 Top3 残留、无「未确认当基线」

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖
- **Foundational (Phase 2)**: 依赖 Setup；**阻塞全部用户故事**
- **US1 (Phase 3)**: 依赖 Foundational — MVP
- **US2 (Phase 4)**: 依赖 Foundational；建议在 US1 之后（共用 init.md）
- **US3 (Phase 5)**: 依赖 Foundational；与 US2 文件不同可并行，但 status 依赖治理台存在（US1）
- **US4 (Phase 6)**: 依赖 Foundational；与 US3 可并行
- **US5 (Phase 7)**: 依赖 Foundational；文档补齐挂在 init，建议 US2 之后
- **US6 (Phase 8)**: 依赖 Foundational 的 audit 模块；建议各命令共享段稳定后做
- **Polish (Phase 9)**: 依赖计划交付的故事

### User Story Dependencies

- **US1**: 不依赖其他故事
- **US2**: 实现上改同一 `init.md`，接在 US1 后
- **US3**: 逻辑独立，验收需已有 `.pm/`（US1）
- **US4**: 独立（CLI architecture）
- **US5**: 评审可独立；文档双模式接 init（US2）
- **US6**: 独立审计导出，接共享工作流

### Parallel Opportunities

- T006 与 T008（redact.py / audit.py）
- T014 适配器同步（init 两侧）
- T021 next.md 与 done.md
- T024 四套 status/next/done/fix 适配器
- T030 arch 适配器两侧
- T035 all/discover 适配器
- T040 与 T041 文档类

---

## Parallel Example: User Story 3

```bash
# 模板侧可并行改不同文件：
Task: "改 next.md 与 done.md 去掉 Top3 in skills/pm-manager/templates/commands/"
Task: "改 fix.md 粘贴+脱敏 in skills/pm-manager/templates/commands/fix.md"

# 适配器在模板完成后再并行复制
Task: "同步 pm-status/pm-fix 到 adapters/cursor 与 adapters/claude-code"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 Setup
2. Phase 2 Foundational（脱敏、审计、去掉 top_n、exclude）
3. Phase 3 US1（scaffold + init 不重扫）
4. **STOP**：按 US1 Independent Test 验收后再继续

### Incremental Delivery

1. US1 治理台 → US2 确认门 → US3 状态/分诊 → US4 地图 → US5 文档+评审 → US6 审计导出 → Polish
2. 每故事独立可演示，不把 V1.1 体检/钩子/单测助手拉进来

### Parallel Team Strategy

- Foundational 完成后：一人 CLI（US4 architecture + tests），一人技能模板（US2/US3/US5）
- 适配器同步始终在对应源模板完成之后

---

## Notes

- [P] = 不同文件、无未完成依赖
- 改 `templates/commands/*.md` 后必须同步对应 adapters，禁止只改一侧
- 提交按任务或逻辑组；在 checkpoint 停下来验收故事
- 避免：无路径的空泛任务、同一文件多人并行、把 Top3 加回去
