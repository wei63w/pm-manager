# Agent 斜杠命令契约: `/pm-*`

命令名保持英文。源文件：`skills/pm-manager/templates/commands/<name>.md`。  
Cursor / Claude 适配器必须与源模板行为一致。

所有会改 `.pm/` 的命令共享：读配置 → 按需增量扫描 → 脱敏后写证据 → 合并待办 → 追加审计 → 中文回复（用户以中文交互时）。**禁止**自动写业务代码/SQL/云。**禁止**把日常阻断/高优先级待办截成三条。

## `/pm-init`

- **输入**: 空 | `confirm` | `approve` | `revise: …` | `skip` | 一句话意图
- **必须**: 探测 Spec Kit 宪章/规格并导入草稿；否则导入或起草 PRD 草稿；**停下等确认**；确认或跳过之后做技术轻扫（文档索引 + 地图），不要求先跑 `/pm-all`
- **禁止**: 未确认把草稿当基线；确认前全模块深潜；覆盖用户已改治理文件
- **输出**: 中文摘要 + 确认/修订/跳过选项；治理台已建；向导式下一步

## `/pm-status`

- **必须**: 健康一句 + 全部未关闭 blocking/high 待办（可排序/折叠低优先级，**无条数上限**）；有待处置评审时提示条数
- **禁止**: Done When 再写「Top3 <= 3」；默认深潜
- **输出**: 向导或认领/关闭指引；只链已存在的 overview/dashboard

## `/pm-next` / `/pm-done`

- **必须**: 认领第一条合适的 open 项 / 关闭指定 TODO-xxx 并刷新权威 `state/todo.md`

## `/pm-fix`

- **必须**: 对话粘贴为一等证据（不必先存文件）；脱敏后落盘；只建问题与待办；回复置顶「本次只分诊，不改代码」
- **禁止**: 未确认改业务代码

## `/pm-arch`

- **必须**: 先读已有 `map.json`；生成/增量更新地图与 Mermaid 到 `.pm/architecture/`
- **禁止**: 默认写入业务树；无过滤递归依赖目录

## `/pm-all`

- **必须**: 模块深潜走此路径，不是 `/pm-status` 默认；**默认技术扫描**，不因 `prd.status=draft` 拦截
- **禁止**: 把 V1.1 全量体检当作本版本必做；评审条目无推理/片段；把未确认 PRD 当基线对照
- **对照基线**: 仅 `--compare-baseline` 且 PRD 已确认或宪章已批准

## `/pm-discover`

- **内部**: 由 `/pm-all` 调用。用户输入此命令时改走 `/pm-all` 并说明。

## `/pm-review`

- **必须**: 对本地 diff 做带推理+片段的评审；无 diff 明示没有可评的；`confirm` / `false_positive` / `later`；仅 confirmed 进规范库
- **禁止**: 未确认改业务代码；无证据结论

## `/pm-check`

- **必须**: 诊断缺失文件、损坏 audit、过期/缺失地图、未确认 PRD、待处置评审；`repair` 只补骨架不覆盖已确认内容

## `/pm-charter`

- **必须**: 无参数时给出 create/import/discover/approve/skip 向导；approve 才把宪章当基线；技术扫描不要求 approve

## `/pm-export`

- **必须**: 按时间窗导出审计（**先脱敏再落盘**）；不得含秘密原文；若仍有残留则删除文件并失败

## `/pm-outline`

- **必须**: 未确认基线时只出提纲草稿，不当验收标准

## 评审写入契约（任意产生 ReviewFinding 的命令）

每条合格条目必须含：`summary`、`reasoning`、`snippet`、`severity`。缺一则不合格，不得沉淀 Rule。无本地变更时必须明示「没有可评的变更」。
