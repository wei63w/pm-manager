# CLI 契约: `pm` / `pm-manager`

确定性引擎。命令名保持英文。确认门、评审推理、粘贴分诊仍走 `/pm-*`。

变异 `.pm/` 的命令（`init` / `arch` / `docs` / `dashboard` / `export`）结束后必须向 `.pm/state/audit.jsonl` 追加一行（command、input/output 摘要）。`status` / `check` / `version` 只读，不写审计。

## `pm init [path]`

- **作用**: 创建 `.pm/` 骨架；`.git/info/exclude` 追加 `.pm/`；默认安装适配器
- **禁止**: 覆盖用户已编辑的 `.pm/` 文件；把 `.pm/` 写入共享 `.gitignore`
- **成功**: 退出码 0；目标出现 `.pm/config/project.yaml`；`audit.jsonl` 有 `pm-init` 行
- **失败**: 模板缺失 → 非 0，不半写业务源码

## `pm arch [path]`

- **作用**: 忽略清单扫描 → 写 `.pm/architecture/` Mermaid、`map.json` **与** 带注解目录树 `tree.md`
- **增量**: 若地图已存在，只重算变更文件（`mtime_hash`）
- **隔离**: 单文件读失败跳过并记入 notes，整命令仍 0（除非根目录不可读）
- **超时预期**: 中小型（忽略后 ≤5000 文件）全量 ≤30s、增量 ≤5s
- **禁止**: 未经确认把图写进业务树

## `pm docs [path]`

- **作用**: 扫描根目录约定核心文档（AGENTS.md/agent.md、prd、design、api、deploy、trouble-shoot）；更新 `.pm/state/doc-index.md`；stdout 打印缺失清单
- **禁止**: 生成或覆盖文档正文（起草 + 确认仍是 `/pm-init`）
- **失败**: 无 `.pm/` → 退出码 2

## `pm status [path]`

- **作用**: 只读列出 `.pm/state/todo.md`（及模块待办合并后）全部 open/in_progress 的 blocking/high（P0/P1），无 3 条上限；附带缺失核心文档计数与 `prd.status`
- **禁止**: LLM 评语；改 `.pm/` 或业务树
- **失败**: 无 `.pm/` → 退出码 2

## `pm export [path]`

- **作用**: 按 `--from` / `--to`（默认全部）读 `audit.jsonl`，脱敏后写 Markdown；默认 `.pm/exports/pm-export-YYYYMMDD.md`，或 `--out`
- **禁止**: 导出文件含秘密原文（AKIA、PEM、token 等须为 `***`）
- **失败**: 时间格式错误 → 退出码 1；无 `.pm/` → 退出码 2

## `pm check [path]`

- **作用**: 报告 `.pm/`、适配器、`map.json`、`audit.jsonl`、`doc-index.md`、`prd.status` 是否存在（只读）

## `pm dashboard [path]`

- **作用**: 从 findings/todos 重建 `.pm/dashboard/`（只写治理台）

## `pm install` / `pm version`

- 刷新适配器 / 打印版本。不要求写审计。

## 退出码

| 码 | 含义 |
|----|------|
| 0 | 成功（含部分文件跳过） |
| 1 | 用法或路径错误 |
| 2 | 模板/权限导致无法写 `.pm/`，或缺少 `.pm/` |
