# Agent 斜杠命令契约: `/pm-*`

命令名保持英文。源文件：`skills/pm-manager/templates/commands/<name>.md`。  
Cursor / Claude 适配器必须与源模板行为一致。

所有会改 `.pm/` 的命令共享：读配置 → 按需增量扫描 → 脱敏后写证据 → 合并待办 → 追加审计 → 中文回复（用户以中文交互时）。**禁止**自动写业务代码/SQL/云。**禁止**把日常阻断/高优先级待办截成三条。

## `/pm-init`

- **输入**: 空 | `confirm` | `approve` | `revise: …` | `skip` | 一句话意图
- **必须**: 探测 Spec Kit 宪章/规格并导入草稿；否则导入或起草 PRD 草稿；**停下等确认**
- **禁止**: 未确认把草稿当基线；确认前全模块深潜；覆盖用户已改治理文件
- **输出**: 中文摘要 + 确认/修订/跳过选项；治理台已建

## `/pm-status`

- **必须**: 健康一句 + 全部未关闭 blocking/high 待办（可排序/折叠低优先级，**无条数上限**）
- **禁止**: Done When 再写「Top3 <= 3」
- **输出**: 认领/关闭指引；链接 overview/dashboard

## `/pm-next` / `/pm-done`

- **必须**: 认领第一条合适的 open 项 / 关闭指定 TODO-xxx 并刷新权威 `state/todo.md`

## `/pm-fix`

- **必须**: 对话粘贴为一等证据（不必先存文件）；脱敏后落盘；只建问题与待办
- **禁止**: 未确认改业务代码

## `/pm-arch`

- **必须**: 先读已有 `map.json`；生成/增量更新地图与 Mermaid 到 `.pm/architecture/`
- **禁止**: 默认写入业务树；无过滤递归依赖目录

## `/pm-all` / `/pm-discover`

- **必须**: 模块深潜走此路径，不是 `/pm-status` 默认
- **禁止**: 把 V1.1 全量体检当作本版本必做；评审条目无推理/片段

## `/pm-charter`

- **必须**: discover/import/create/approve/skip 状态机；approve 才把宪章当基线

## `/pm-export`

- **必须**: 按时间窗导出审计（脱敏 Markdown）；不得含秘密原文

## `/pm-outline`

- **必须**: 未确认基线时只出提纲草稿，不当验收标准

## 评审写入契约（任意产生 ReviewFinding 的命令）

每条合格条目必须含：`summary`、`reasoning`、`snippet`、`severity`。缺一则不合格，不得沉淀 Rule。无本地变更时必须明示「没有可评的变更」。
