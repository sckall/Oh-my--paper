---
description: 查看或更新 Mega 模式进度
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Oh My Paper Progress Manager。

## 第一步：检查 Mega 模式状态

```bash
ls .pipeline/mega/PROGRESS.md 2>/dev/null || echo "NOT_INITIALIZED"
```

如果 NOT_INITIALIZED：

> Mega 模式未启用。先运行 `/omp:mega` 初始化。

## 第二步：读取当前进度

```bash
cat .pipeline/mega/PROGRESS.md
```

## 第三步：解析并展示

提取以下信息：
- 当前版本
- 当前阶段和名称
- 各 Group 的完成状态
- 最近决策记录
- 下一门控

用 `AskUserQuestion` 展示：

> **Mega 模式进度**
>
> **版本**: v{version}
> **当前阶段**: {stage_name} ({stage_id})
>
> **阶段进度**：
> - Group A (定义): {A_status} ████████░░ 80%
>   - A1 Topic: ✅
>   - A2 Hardware: ✅
>   - A3 Search: ✅
>   - A4 Screen: ✅
>   - A5 Gateway: 🔄
>   - A6 Hypothesis: ⏳
>   - A7 Debate: ⏳
>   - A8 Decision: ⏳
>
> - Group B (实验): {B_status} ░░░░░░░░░░ 0%
>   - B9-B15: ⏳ pending
>
> - Group C (论文): {C_status} ░░░░░░░░░░ 0%
>   - C16-C23: ⏳ pending
>
> **最近决策**：
> - {date}: {decision} @ {stage_id} → {new_stage_id}
> - {date}: {decision} @ {stage_id} → {new_stage_id}
>
> **下一门控**: {next_gate} ({gate_id})

选项：
- `查看详情` — 展示当前阶段的详细状态
- `更新阶段` — 手动更新当前阶段
- `添加决策` — 记录新的决策点到 PROGRESS.md
- `返回` — 退出

## 第四步：处理用户选择

### 查看详情

读取并展示：
```bash
cat .pipeline/mega/plans/plan_{current_stage}.md 2>/dev/null
cat .pipeline/docs/research_brief.json
```

### 更新阶段

用 `AskUserQuestion` 询问：

> **选择要更新的阶段**：
> - A1-A8（Group A 阶段）
> - B9-B15（Group B 阶段）
> - C16-C23（Group C 阶段）

选择后，用 `AskUserQuestion` 询问新状态：

> **{stage_name} 的新状态**：
> - `pending` — 未开始
> - `in_progress` — 进行中
> - `done` — 已完成
> - `blocked` — 被阻塞

更新 PROGRESS.md 中对应阶段的状态。

### 添加决策

用 `AskUserQuestion` 询问：

> **记录新决策**
>
> 决策类型：
> - `PROCEED` — 继续下一阶段
> - `REFINE` — 细化调整（版本+0.1）
> - `PIVOT` — 换方向（版本+1.0）

> 触发阶段：{current_stage}
> 目标阶段：{next_stage}
> 原因：{请描述}

更新 PROGRESS.md：
1. 在版本历史添加新条目
2. 在决策日志添加详情
3. 如果是 REFINE/PIVOT，更新版本号