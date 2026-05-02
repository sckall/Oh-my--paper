---
description: 查看研究项目进度（支持 Legacy 和 Mega 双模式）
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Oh My Paper Progress Manager。

## 第一步：检测项目模式

```bash
# 读取研究简介，判断模式
cat .pipeline/docs/research_brief.json 2>/dev/null || echo "NOT_FOUND"
```

从 `research_brief.json` 中读取 `mode` 字段：
- `"mode": "Mega"` → 进入 **Mega 模式**
- 其他 / 不存在 → 进入 **Legacy 模式**

同时检查 `.pipeline/mega/PROGRESS.md` 是否存在作为备用判断。

---

## 模式 A：Mega 模式

（此部分逻辑保持不变，与原有 progress.md 一致）

### 第二步：检查 Mega 模式状态

```bash
ls .pipeline/mega/PROGRESS.md 2>/dev/null || echo "NOT_INITIALIZED"
```

如果 `NOT_INITIALIZED`：

> Mega 模式未启用。先运行 `/omp:mega` 初始化，或确认 `research_brief.json` 中 mode 字段是否为 `"Mega"`。

### 第三步：读取当前进度

```bash
cat .pipeline/mega/PROGRESS.md
```

### 第四步：解析并展示

提取以下信息：
- 当前版本
- 当前阶段和名称
- 各 Group 的完成状态
- 最近决策记录
- 下一门控

用 `AskUserQuestion` 展示：

```
┌──────────────────────────────────────────────────────┐
│  🚀 Oh My Paper — Mega 模式                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                      │
│  主题：[研究主题，截断到30字...]                      │
│  版本：v{version}  |  阶段：{stage}  |  进度：{progress}%│
│                                                      │
│  ████████████░░░░░░░░░░░░░░░░░░  {progress}%    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

选项：
- `查看详情` — 展示各 Group 详细状态
- `更新阶段` — 手动更新当前阶段
- `添加决策` — 记录新的决策点到 PROGRESS.md
- `返回` — 退出

（后续逻辑与原 progress.md 相同，此处省略重复内容）

---

## 模式 B：Legacy 模式（默认）

### 第二步：读取项目状态

```bash
# 读取研究简介
cat .pipeline/docs/research_brief.json 2>/dev/null || echo "NOT_FOUND"

# 读取任务列表
cat .pipeline/tasks/tasks.json 2>/dev/null || echo "NOT_FOUND"

# 读取项目真相文档
cat .pipeline/memory/project_truth.md 2>/dev/null || echo "NOT_FOUND"
```

### 第三步：计算各阶段进度

Legacy 模式包含 5 个阶段：`survey` → `ideation` → `experiment` → `publication` → `promotion`

进度计算规则：
- 从 `tasks.json` 中统计每个阶段相关任务的完成度
- 如果 `research_brief.json` 中有 `currentStage`，标记当前所在阶段
- 每个阶段进度 = 该阶段已完成任务数 / 该阶段总任务数

如果 `tasks.json` 为空或不存在，则从 `project_truth.md` 的内容推断进度（关键词匹配）。

### 第四步：ASCII 进度展示

用以下格式展示：

```
═════════════════════════════════════════════════════════
  📊 Oh My Paper — 进度总览
═════════════════════════════════════════════════════════
  主题：{topic}
  模式：Legacy  |  当前阶段：{current_stage}

  Survey      ████████████████████░░  90%  ✅
  Ideation    ████████████████████░░  85%  ✅
  Experiment  ████████░░░░░░░░░░░░  40%  🔄
  Publication ░░░░░░░░░░░░░░░░░░░░   0%  ⏳
  Promotion   ░░░░░░░░░░░░░░░░░░░░   0%  ⏳

  进行中任务：{in_progress_count}  |  已完成：{done_count}  |  待开始：{pending_count}
═════════════════════════════════════════════════════════
```

图例：
- `█` = 已完成
- `░` = 未完成
- `✅` = 阶段已完成
- `🔄` = 阶段进行中
- `⏳` = 阶段待开始

### 第五步：展示可操作选项

用 `AskUserQuestion` 提供：

> **进度总览**
>
> 选项：
> - `查看任务详情` — 展示 tasks.json 中各任务的详细状态
> - `切换到 Mega 模式` — 运行 `/omp:mega` 启用 25 阶段系统
> - `运行下一阶段` — 根据 current_stage 推荐下一步命令
> - `返回` — 退出

### 查看任务详情

读取 `.pipeline/tasks/tasks.json`，以表格形式展示：

```
## 任务详情

| 阶段        | 任务名         | 状态    |
|------------|---------------|--------|
| survey     | 搜索论文      | ✅ 完成 |
| survey     | 整理文献库    | ✅ 完成 |
| ideation   | 生成创新点    | 🔄 进行中 |
| experiment | 设计实验      | ⏳ 待开始 |
```

### 切换到 Mega 模式

提示用户：

> 切换到 Mega 模式将启用 25 阶段流水线，包含门控检查和决策循环。
> 当前进度可以保留，但建议先运行 `/omp:mega` 初始化 Mega 目录结构。
>
> 是否现在初始化 Mega 模式？

选项：`是，初始化 Mega 模式` / `暂不切换`

---

## 通用：快照历史（两种模式均显示）

在展示进度后，检查是否有快照：

```bash
ls .pipeline/memory/snapshots/ 2>/dev/null || echo "NO_SNAPSHOTS"
```

如果有快照，在进度展示末尾附加：

> 📸 发现 {n} 个快照，运行 `/omp:recover` 可恢复到任意快照。

---

## 错误处理

- 如果 `.pipeline/` 目录不存在：提示用户先运行 `/omp:setup` 初始化项目
- 如果 `research_brief.json` 不存在：提示用户检查项目初始化是否完整
- 如果 `tasks.json` 格式错误：提示用户手动检查该文件，不要静默忽略
