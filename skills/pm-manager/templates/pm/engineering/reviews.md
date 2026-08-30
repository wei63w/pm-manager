# 评审记录

每条**合格**发现必须包含：摘要、推理、引用片段、严重级别。
缺推理或片段 = 不合格，不得写入规范库。

| id | summary | reasoning | snippet | severity | disposition | file | line | dimension | cross |
|----|---------|-----------|---------|----------|-------------|------|------|-----------|-------|
| — | — | — | — | P0/P1/P2 | unset | — | — | — | unset |

处置：

- `confirmed` → 写入 `rules.md`（enabled）
- `false_positive` → 后续评审不再当约束
- `deferred` / `later` → 只留在本表
- 空 / `unset` → 待处置；`/pm-status` 应提示条数
