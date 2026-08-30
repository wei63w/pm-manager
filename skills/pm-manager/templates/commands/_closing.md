## 收尾输出（按命令分级）

会改 `.pm/` 的 `/pm-*` 回复必须有一句中文摘要。链接只列**已经存在**的文件，不要指向还没生成的路径。

用户以中文交互时，摘要、待办、评审、报告必须中文。命令名保持 `/pm-*`。

### 轻量（`/pm-status` / `/pm-next` / `/pm-done` / `/pm-fix` / `/pm-check`）

最多 1–2 个有效链接：

```text
## 摘要
- <一句健康 / 刚发生了什么>
- <未关闭阻断+高优先级待办条数；正文不用三条上限>

## 打开这些（若文件存在）
- 总览: `.pm/state/overview.md`
- 看板（仅当 `.pm/dashboard/index.html` 已存在）: `.pm/dashboard/index.html`
```

### 完整（`/pm-init` 确认或跳过之后 / `/pm-all` / `/pm-arch` / `/pm-export` / `/pm-review`）

```text
## 摘要
- <一句健康 / 本轮改了什么>
- <未关闭阻断+高优先级待办条数，正文列出，无三条上限>

## 打开这些（只列已生成的）
- 治理看板（浏览器）: `.pm/dashboard/index.html`
- 治理看板（IDE）: `.pm/dashboard/overview.md`
- 架构与地图: `.pm/architecture/overview.md`
- 总览 / 待办: `.pm/state/overview.md`
- PRD（草稿或已确认）: `.pm/prd/prd.md`
```

没有的文件不要列。明确请用户打开上面还在的链接。不要只写「完成」而不给路径。
