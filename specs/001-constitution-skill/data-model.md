# Data Model: 按宪章交付治理技能

**Date**: 2026-08-30  
**Storage**: 目标仓库 `.pm/`（本地文件）

所有实体默认只存在于治理台。写入业务树必须经用户确认（规格 FR-008）。

## 实体

### 治理台 (Workbench)

- **位置**: `<project>/.pm/`
- **字段**: 由子实体组成；无单独主键
- **规则**: 必须经 `.git/info/exclude` 排除 `.pm/`；禁止写入共享 `.gitignore`
- **关系**: 1 仓库 : 1 治理台

### 项目配置 (ProjectConfig)

- **位置**: `.pm/config/project.yaml`、`.pm/config/local.yaml`
- **关键字段**:
  - `charter.status`: `absent | draft | approved | skipped`
  - `prd.status`: `absent | draft | confirmed | skipped`
  - `prd.path`: 默认 `.pm/prd/prd.md`
  - `speckit.present` / `constitution` / `specs`
  - `rules.require_confirm_before_write`: 必须为 true
  - `rules.desensitize_evidence`: 必须为 true
  - `rules.default_noise_filter`: `high`（阻断+高优先展示）
  - **删除** `rules.top_n`（不得再作为三条上限）
  - `scan.exclude_dirs` / `scan.incremental_by`
- **校验**: `prd.status != confirmed` 时禁止把 PRD 当验收基线

### 基线草稿 (BaselineDraft)

- **位置**: `.pm/prd/prd.md`、`.pm/charter/charter.md`、`.pm/charter/requirements.md`、`.pm/charter/sources.md`
- **字段**: 正文、`source`（speckit | imported | drafted）、状态见配置
- **转换**: `draft --确认--> confirmed/approved`；`draft --跳过--> skipped`
- **规则**: 未确认不得用于「需求是否合理」判定

### 导航地图 (NavMap)

- **位置**: `.pm/architecture/map.json`（结构化）；同目录 Mermaid 给人读
- **字段**: `generated_at`、`modules[]`（name, path, responsibility）、`key_files[]`、`capabilities[]`、`hotspots[]`、`excludes_applied[]`
- **规则**: 生成时跳过 ignore 清单；增量时只重算变更文件对应节点

### 说明索引 (DocIndex)

- **位置**: `.pm/state/doc-index.md`（或 YAML）
- **字段**: 每条核心说明：`id`、`expected_name`、`status`（missing | present | possibly_stale）、`path`
- **核心说明集合（闭合）**: `AGENTS.md`/`agent.md`、产品说明、设计、接口、部署、排障（与规格 User Story 5 一致）

### 待办 (Todo)

- **位置**: `.pm/state/todo.md`（权威）；模块 `todo.md` 为来源
- **字段**: `id`（TODO-xxx）、`title`、`severity`（blocking | high | medium | low）、`status`（open | in_progress | done）、`source`
- **转换**: `open -> in_progress`（认领）；`in_progress|open -> done`（关闭）
- **规则**: 日常状态必须能列出全部 `open|in_progress` 且 severity 为 blocking/high 的项，禁止截成 3 条

### 评审条目 (ReviewFinding)

- **位置**: `.pm/` 下评审记录（建议 `.pm/engineering/reviews/<timestamp>.md`）
- **必填字段**: `summary`、`reasoning`、`snippet`、`severity`（P0/P1/P2）、`disposition`（unset | confirmed | false_positive | deferred）
- **可选**: `file`、`line`、`dimension`（security|quality|complete|docs|logic）、`cross`（unset|agree|new|reject）
- **校验**: 缺 `reasoning` 或 `snippet` → 不合格，不得沉淀规范
- **转换**: `unset -> confirmed | false_positive | deferred`

### 规范条目 (Rule)

- **位置**: `.pm/engineering/rules.md`（或 library 文件）
- **字段**: `id`、`text`、`source_finding`、`enabled`（true/false）
- **规则**: 仅 `disposition=confirmed` 可创建；后续评审/生成必须加载 `enabled=true` 的条目

### 证据 (Evidence)

- **位置**: `.pm/evidence/scans/{command}-{timestamp}.json`
- **字段**: `command`、`timestamp`、`raw_redacted`、`paths[]`
- **规则**: 写入前脱敏；原始秘密不得入盘

### 审计记录 (AuditEvent)

- **位置**: `.pm/state/audit.jsonl`（一行一事，异常退出不丢已 flush 行）
- **字段**: `ts`、`actor_or_session`、`command`、`input_summary`、`output_summary`、`reasoning?`
- **规则**: 扫描/生成/评审/分诊均须追加；支持按时间窗过滤导出为 Markdown

### 对话摘要 (DialogueNote)

- **位置**: `.pm/state/dialogue.md` + `.pm/state/dialogue.jsonl`
- **字段**: `ts`、`kind`（consult | code | fix | docs | refactor | other）、`intent?`、`files[]?`、`status`（parsed | unresolved）、`excerpt?`
- **规则**: 脱敏后落盘；不可判断时 `unresolved`，禁止编造文件列表

### 会话意图 (SessionIntent)

- **位置**: `.pm/state/session.json`
- **字段**: `generated_at`、`kind`、`goal`、`files[]`、`status`、`note_count`
- **规则**: 由最近对话摘要聚合；无摘要时 `goal=信息不足`

### 变更点 (ChangePoint)

- **位置**: `.pm/state/changes.md`
- **字段**: `path`、`source`（map | git）
- **规则**: 来自 `map.json` 的 `changed_paths` 与 git（失败忽略）；不含 `.pm/`

### 迭代时间线 (TimelineEvent)

- **位置**: `.pm/state/timeline.md`
- **字段**: `ts`、`kind`（audit | dialogue-kind | change）、`title`、`detail`

### 优化建议 (Suggestion)

- **位置**: `.pm/state/suggestions.md`
- **字段**: `id`（SUG-xxx）、`priority`（P0 | P1 | P2）、`title`、`reason`、`action`
- **规则**: 只提示，不自动改业务树，不自动建待办

### 高危文件 (RiskFile)

- **位置**: `.pm/architecture/map.json` 的 `risk_files[]`
- **字段**: `path`、`flags[]`（entry | hotspot | bulky | uncommented）、`reasons[]`

### 单测缺口 (TestGap)

- **位置**: `.pm/state/test-gaps.md`
- **字段**: `path`、`suggest`、`changed`
- **规则**: 不自动写业务树测试

### 幻觉防御 (GuardReport)

- **位置**: `.pm/state/guard.md`
- **字段**: 不合格评审、逻辑丢失嫌疑、本轮碰到的高危文件

## 关系

```text
Workbench
├── ProjectConfig 1—1 BaselineDrafts (prd/charter)
├── NavMap 1—1 DocIndex
├── Todo * — ReviewFinding * （待办可来自评审或分诊）
├── ReviewFinding * —0..1 Rule
├── Evidence *
├── AuditEvent *
├── DialogueNote *
├── SessionIntent 1
├── ChangePoint *
├── TimelineEvent *
└── Suggestion *
```

## 校验摘要

| 规则 | 来源 |
|------|------|
| 无 reasoning/snippet 不得入库为合格评审 | FR-017 / GC-004 |
| 无确认不得写业务树或正式文档 | FR-008 / GC-002 |
| 脱敏后再写 Evidence/Dialogue/导出 | FR-013 / GC-003 |
| 状态列表不得 top_n=3 截断 blocking/high | FR-011 / GC-005 |
