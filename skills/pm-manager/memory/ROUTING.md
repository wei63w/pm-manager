# Command routing

对外只强调日常 5 个口令 + 发布前 1 个。其余为规划 / 诊断。

| User phrase | Command |
|-------------|---------|
| initialize / start governing / 初始化治理 | `/pm-init` |
| confirm PRD / 确认草稿 | `/pm-init` |
| how are we doing / 现在做什么 / 今日状态 | `/pm-status` |
| what's next / 认领下一条 | `/pm-next` |
| this is done / 关闭 TODO-xxx | `/pm-done` |
| help me with this error + paste / 贴报错 | `/pm-fix` |
| 白屏 / Vite 报错 / Vue warn / Pinia / 路由失败 | `/pm-fix` |
| full check / 发布前扫描 / health scan | `/pm-all` |
| review this diff / 评审改动 / 确认误报 | `/pm-review` |
| checkup / 体检 / 全量质量 / 分级建议 | `/pm-checkup` |
| diagnose .pm / 治理台坏了 / 修复元数据 | `/pm-check` |
| generate outline / 空仓规划 | `/pm-outline` |
| charter / constitution / 导入宪章 | `/pm-charter` |
| export governance summary | `/pm-export` |
| missing docs / 补文档 / 文档过期 | `/pm-docs` |
| architecture diagram / 架构图 / 地图 | `/pm-arch` |
| journal / timeline / 开发记录 / 意图 / 时间线 / 优化建议 | `/pm-journal` |
| missing tests / 单测缺口 / 补测试 | `/pm-tests` |

Do **not** route users to `/pm-discover`. Deep scan is `/pm-all`.

Daily essentials: `init` → `status` → `next` → `done`; `fix` for incidents; `review` for local diffs; `all` before release; `check` when `.pm/` looks broken.
