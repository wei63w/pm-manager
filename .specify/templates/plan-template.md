# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

**语言**: 填写后的 `plan.md` 正文必须为中文（章节标题可保留本模板英文结构名，便于 `/speckit-*` 识别）。代码标识符、路径、命令名保持英文。

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]

**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]

**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]

**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]

**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]

**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]

**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]

**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

对照 `.specify/memory/constitution.md` v1.1.1 逐条判定。FAIL 且未在
Complexity Tracking 记录豁免的，必须阻断本计划。

- **I. 本地优先的持久资产**：治理数据（地图、索引、评审、日志、规范）必须落入
  `.pm/`（或已文档化的元数据目录），禁止污染业务源码。`.pm/` 必须经
  `.git/info/exclude` 排除。变更类操作必须有跨会话复用与审计记录（操作人、时间、
  输入、输出）。
- **II. 先确认后写入**：写入应用代码、SQL、云资源或生成文档/规范前，必须等待用户
  明确确认。未确认的 PRD/宪章禁止当作基线。默认只报告。
- **III. 地图优先协作**：Agent I/O 必须优先导航地图与文档索引，而非递归遍历。扫描
  必须遵守忽略清单。必须提供增量扫描。单文件失败禁止中断整批。
- **IV. 有证据的质量闭环**：评审/质量输出必须含推理链与引用片段。已确认问题必须能
  沉淀进规范库。P0 打断；P1/P2 只进报告。V1.1 项（全量体检、Git 钩子、单测辅助、
  风险标记）禁止混入 V1.0 计划。
- **粘贴即证据与脱敏**：对话粘贴必须作为 `/pm-fix` 一等证据。证据落盘前必须脱敏。
  日常状态不得以「最多三条」截断未关闭的阻断或高优先级待办。
- **文档中文优先**：本计划与对应 spec/tasks 正文必须为中文。
- **NFR**：全量扫描 ≤30s，增量 ≤5s，Diff 评审 ≤15s，地图/资产加载秒级（中小型项目）。
  元数据必须在异常退出后可恢复。

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
