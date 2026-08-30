# Quickstart: 按宪章交付治理技能

用于验收本功能是否端到端可用。实现细节见 [tasks.md](./tasks.md) 与 [data-model.md](./data-model.md)、[contracts/](./contracts/)。

## 前置

- Python 3.11+，仓库根目录可执行 `pytest` 与 `pm`（`uv tool install --editable .` 或等价）
- 编码助手已能加载 `skills/pm-manager`（或项目内适配器）
- 准备一个**空的临时 git 仓库**作为目标项目（不要用本技能源码仓当唯一验收对象）

## 1. 脚手架（CLI）

```bash
cd /path/to/empty-app
git init
pm init .
```

**期望**: 出现 `.pm/config/project.yaml`；`.git/info/exclude` 含 `.pm/`；共享 `.gitignore` **没有**新增 `.pm/`；业务目录无新文件。

## 2. 确认门（Agent）

在目标仓库打开助手，执行 `/pm-init`。

**期望**: 得到 PRD/宪章**草稿**并等待确认；此时 `/pm-status` 不得把草稿当「需求基线」。回复 `confirm` 后再视为基线。

拒绝一份文档草稿时，正式文档路径不得被覆盖。

## 3. 跨会话

关闭对话，新开对话，再执行 `/pm-status`。

**期望**: 仍能看到治理台待办/配置，且未做一次全库重扫（有地图或有效元数据时）。

## 4. 状态条数

在 `.pm/state/todo.md` 放入 10 条 open 的 blocking/high 待办，执行 `/pm-status`。

**期望**: 10 条都能看到，不被截成 3 条。

## 5. 粘贴分诊与脱敏

`/pm-fix` 并粘贴含 `AKIAIOSFODNN7EXAMPLE` 或 `-----BEGIN PRIVATE KEY-----` 的伪堆栈。

**期望**: 产生待办；`.pm/evidence/` 与回复中无该秘密原文；业务源码未改。

## 6. 地图优先

```bash
pm arch .
```

**期望**: `.pm/architecture/` 下有图、`map.json` 与 `tree.md`；`node_modules` 等不在地图/目录树中。再改一个业务文件后重复 `pm arch`，应走增量（体感短于首次全量）。

助手在已有地图时定位模块，不得先无过滤遍历依赖目录。

## 6b. 文档索引与审计导出（CLI）

```bash
pm docs .
pm status .
pm export . --from 2026-01-01
```

**期望**: `doc-index.md` 标出缺失的核心文档；`pm status` 列出全部 blocking/high（无 3 条上限）；导出 Markdown 无秘密原文。

## 7. 评审契约

制造一处故意缺陷的本地改动，请助手做变更评审。

**期望**: 每条有效结论含推理与片段；无改动时明确「没有可评的变更」。确认一条后，规范库出现对应 Rule。

## 8. 审计导出

执行若干 `/pm-*` 后 `/pm-export`（或等价导出审计）。

**期望**: 能按时间看到命令摘要；无未脱敏秘密。

## 9. 回归（本仓库）

```bash
cd /path/to/pm-manager
pytest
```

**期望**: 现有 `tests/` 加本功能新增用例全部通过（exclude、脱敏、增量路径、Spec Kit 探测）。

## 非目标（本版本不要拿来挡验收）

定期全量体检、Git 提交钩子、单测自动补全、高危文件徽标。

## Walkthrough notes (2026-08-30)

CLI 部分已在临时 git 仓库走通：`scaffold` 写入 `.pm/` 且只追加 `.git/info/exclude`（共享 `.gitignore` 不含 `.pm/`）；`write_architecture` 产出 `map.json`、忽略 `node_modules`、二次扫描走增量；脱敏与 `audit.jsonl` 追加通过。`pytest` 22 项全绿。

Agent 部分（`/pm-init` 确认门、跨会话不重扫、10 条 blocking/high 全列出、粘贴 `/pm-fix`、评审契约、`/pm-export`）由命令模板与适配器契约覆盖，本会话未在独立目标仓里再跑一遍助手对话。
