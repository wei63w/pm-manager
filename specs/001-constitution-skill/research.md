# Research: 按宪章交付治理技能

**Date**: 2026-08-30  
**Feature**: `001-constitution-skill`

Phase 0 将 Technical Context 中的选择固化。无残留 `NEEDS CLARIFICATION`。

## 行为落点：技能模板 vs CLI

- **Decision**: 确认门、基线导入、评审推理链、粘贴分诊、中文报告由 Agent 技能模板执行；脚手架、git exclude、忽略清单扫描、Mermaid/地图 JSON、增量文件集合由 CLI 执行。
- **Rationale**: 评审与确认是对话行为，CLI 无法代用户点头；扫描与排除规则必须确定性且可测（宪章要求 pytest 覆盖 CLI/持久化）。
- **Alternatives considered**: 全部做成 CLI 子命令（无法承载确认对话）；全部做成纯 Prompt（扫描性能与排除规则不可回归）。

## 存储：文件系统治理台

- **Decision**: 继续用目标仓库 `.pm/` 目录（YAML/Markdown/JSON），不引入数据库或云同步。
- **Rationale**: 宪章原则 I 与产品边界（本地工作台、非 Jira 替代）。
- **Alternatives considered**: SQLite（增加迁移与崩溃面，无多人需求）；把地图写进业务 `docs/`（污染源码，违反原则 I，除非用户确认）。

## 增量更新：按需而非守护进程

- **Decision**: 各 `/pm-*` 与 `pm arch` 启动时按 `mtime_hash` 做增量；不安装文件监视守护进程。宪章「应当静默增量」解释为**命令触发时静默补齐**，不是后台常驻。
- **Rationale**: 研发流程第 6 条禁止默认后台常驻；按需增量仍满足「禁止无条件全量重扫」。
- **Alternatives considered**: watchdog 守护进程（违反宪章）；每次全量扫描（违反 NFR 与原则 III）。

## 脱敏

- **Decision**: 落盘前对证据/对话摘录做规则脱敏：密钥/口令/私钥 PEM/`AKIA…` 类云密钥/常见 token 形态替换为 `***`。不引入外部密钥扫描服务。
- **Rationale**: 宪章安全条款；可在 pytest 中用伪秘密回归。
- **Alternatives considered**: 仅靠模型「不要打印密钥」（不可测）；调用商业 secret scanner（新依赖、需网络）。

## 评审输出形态

- **Decision**: 规定 Agent 评审记录的 Markdown 字段：结论、推理、引用片段、严重度、用户处置。无推理或无片段的条目视为不合格，不得写入规范库。
- **Rationale**: 原则 IV；Agent 产出无法用编译器强制，用契约 + 模板 Done When 约束。
- **Alternatives considered**: 结构化 JSON Schema 校验每条评审（V1.0 过重，可在 V1.1 加）；LLM-as-judge 交叉复核（PRD 有、宪章划为 V1.1 幻觉升级）。

## 去掉 Top3 上限

- **Decision**: `project.yaml` 删除或忽略 `rules.top_n: 3`。`/pm-status` 列出全部未关闭阻断/高优先级待办，低优先级默认可折叠。适配器与 `_closing.md` 同步删「最多三条」。
- **Rationale**: 规格 FR-011 / GC-005；用户已从宪章移除日常 Top3。
- **Alternatives considered**: 保留 top_n 可配置（本规格明确禁止三条硬门禁，配置成 3 会再踩雷）；分页（非本版本必须）。

## 地图格式

- **Decision**: `.pm/architecture/map.json`（模块、关键文件、能力入口）供 Agent 先读；Mermaid 仍写在 `.pm/architecture/`。忽略目录沿用并扩展 `architecture.py` 的 `SKIP_DIRS` + `project.yaml` `scan.exclude_dirs`。
- **Rationale**: 原则 III；现有 `pm arch` 已会写图，缺的是给 Agent 的结构化地图。
- **Alternatives considered**: 仅 Markdown 树（Agent 定位差）；写入仓库根 `ARCHITECTURE.md`（默认污染业务树）。

## 适配器同步

- **Decision**: `skills/pm-manager/templates/commands/` 为单一行为源；`adapters/cursor` 与 `adapters/claude-code` 必须同内容更新（现有发布方式）。
- **Rationale**: 用户在两种助手上行为必须一致。
- **Alternatives considered**: 运行时从源模板生成适配器（本版本不改发布管道）；只改 Cursor（违反「技能」多宿主假设）。

## 测试策略

- **Decision**: pytest 覆盖：git exclude、不覆盖已有 `.pm/` 文件、Spec Kit 探测、脱敏、忽略目录、增量「只返回变更路径」。技能侧用命令契约的 Done When，不在本版本上 Agent 集成测试框架。
- **Rationale**: 宪章要求 CLI/脚手架/持久化有成功+失败用例。
- **Alternatives considered**: Playwright 测助手（无稳定宿主 API）；对 Markdown 模板做快照（脆弱）。

## 中小型仓库

- **Decision**: 计划内「中小型」指扫描文件数（应用 `max_file_size_kb` 与忽略后）不超过约 5000 个文件。超出时 CLI/技能必须声明「全量会更慢」，禁止假装增量完成。
- **Rationale**: 规格假设需要可测边界；不把数字写进对外命令名。
- **Alternatives considered**: 按仓库字节数（含依赖则失真）；不定义（NFR 无法验收）。
