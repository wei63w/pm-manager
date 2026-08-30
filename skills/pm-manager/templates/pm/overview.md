# 项目治理总览

> 更新时间: {ISO8601} | 触发: {command}
> 生命周期: {new|existing} | 过程: {process.mode} | 宪章: {absent|draft|approved} | 提纲: {absent|draft|approved} | PRD: {absent|draft|confirmed|skipped}

## 健康

| 模块 | 状态 | 阻断 | 高 | 中 | 低 | 上次扫描 |
|------|------|------|----|----|----|----------|
| — | 未扫描 | 0 | 0 | 0 | 0 | — |

## 扫描模式

- 本轮: 技术扫描 | 技术扫描 + 已确认基线对照
- 宪章需重比: 否

## 向导（有哪条做哪条）

按顺序只保留仍成立的一步：

1. **还没有治理台** → 运行 `/pm-init`
2. **PRD 仍是草稿** → 回复 `confirm` / `revise: …` / `skip`（跳过仍可做技术扫描）
3. **还没有导航地图** → 运行 `/pm-arch` 或等 `/pm-init` 确认/跳过后的轻扫
4. **看板尚未生成** → 运行 `/pm-all`（默认技术扫描，不要求已确认 PRD）
5. **有未关闭待办** → `/pm-status` 认领，或 `/pm-next`
6. **有待处置评审** → `/pm-review`（`confirm` / `false_positive` / `later`）

## 未关闭的阻断 / 高优先级待办

1. （还没有待办。若上面的向导已走完：贴报错用 `/pm-fix`，发布前用 `/pm-all`）

## 阻断项

- 无

## 建议下一步

1. 先完成上面的向导，不要空跑 `/pm-all` 等门禁
2. 日常：`/pm-status` → `/pm-next` → `/pm-done`
3. 贴报错：`/pm-fix`（只分诊，不改代码）
