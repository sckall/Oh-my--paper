---
description: 并行执行：同时启动多个 Agent 并行工作，结果汇总
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Oh My Paper Orchestrator。此命令支持并行执行多个 Agent 任务，实现真正的多智能体协作。

## 使用场景

`/omp:parallel` 适用于以下场景：

1. **文献调研 + gap 分析 + 初步写作**：同时进行多个相关任务
2. **实验设计 + 基线实现 + 评估脚本**：并行准备实验环境
3. **论文各章节并行撰写**：不同章节同时起草

## 第一步：定义并行任务组

```bash
# 创建并行任务目录
mkdir -p .pipeline/parallel/tasks

# 读取项目状态，确定可用任务
cat .pipeline/memory/project_truth.md
cat .pipeline/memory/orchestrator_state.md
cat .pipeline/tasks/tasks.json
```

用 `AskUserQuestion` 展示可用的并行任务组合：

> **并行执行模式**
>
> 请选择并行任务组合：
>
> **选项 A: 文献调研组合**
> - Task A1: 文献搜索（/omp:survey）
> - Task A2: Gap 分析（生成 gap_matrix.md）
> - Task A3: 引用核查（检查相关性）
>
> **选项 B: 实验准备组合**
> - Task B1: 实验设计（生成 experiment_plan.md）
> - Task B2: 基线代码实现
> - Task B3: 评估脚本准备
>
> **选项 C: 论文写作组合**
> - Task C1: Introduction 撰写
> - Task C2: Related Work 撰写
> - Task C3: Methodology 撰写
>
> **选项 D: 自定义组合**
> - 用户自定义任务组合

## 第二步：创建独立任务上下文

选择任务组合后，为每个任务创建独立上下文：

```bash
# 创建任务上下文
cat > .pipeline/parallel/tasks/task_A1_context.md << 'EOF'
# Task A1: 文献调研

## 任务目标
[具体任务描述]

## 独立上下文
[不给定主项目上下文，避免偏见]

## 输出要求
结果写入: .pipeline/parallel/tasks/task_A1_result.md
EOF

cat > .pipeline/parallel/tasks/task_A2_context.md << 'EOF'
# Task A2: Gap 分析

## 任务目标
[具体任务描述]

## 独立上下文
[不给定主项目上下文，避免偏见]

## 输出要求
结果写入: .pipeline/parallel/tasks/task_A2_result.md
EOF

cat > .pipeline/parallel/tasks/task_A3_context.md << 'EOF'
# Task A3: 引用核查

## 任务目标
[具体任务描述]

## 独立上下文
[不给定主项目上下文，避免偏见]

## 输出要求
结果写入: .pipeline/parallel/tasks/task_A3_result.md
EOF

echo "任务上下文已创建"
ls -la .pipeline/parallel/tasks/
```

用 `AskUserQuestion` 确认：

> **并行任务配置**
>
> | 任务 | 目标 | 输出文件 |
> |------|------|---------|
> | Task A1 | 文献调研 | task_A1_result.md |
> | Task A2 | Gap 分析 | task_A2_result.md |
> | Task A3 | 引用核查 | task_A3_result.md |
>
> 选项：
> - `确认，启动并行执行`
> - `修改任务配置`
> - `取消`

## 第三步：并行执行任务

### 执行方式 1: Codex 并行委派（推荐）

同时向用户展示三个 Codex 命令，用户在新终端并行执行：

```
# 在三个新终端中同时执行以下命令：

# Terminal 1 - Task A1
codex "[Task A1 完整 prompt]"

# Terminal 2 - Task A2
codex "[Task A2 完整 prompt]"

# Terminal 3 - Task A3
codex "[Task A3 完整 prompt]"
```

用 `AskUserQuestion` 引导：

> **启动并行执行**
>
> 请在三个**新终端**中分别执行以下命令：
>
> **Terminal 1 - Task A1: 文献调研**
> ```
> codex "[完整 prompt...]"
> ```
>
> **Terminal 2 - Task A2: Gap 分析**
> ```
> codex "[完整 prompt...]"
> ```
>
> **Terminal 3 - Task A3: 引用核查**
> ```
> codex "[完整 prompt...]"
> ```
>
> 三个任务将并行执行，互不干扰。
>
> 选项：
> - `我已启动三个终端`
> - `先执行一个试试`
> - `取消`

### 执行方式 2: 后台任务模式

如果系统支持后台任务：

```bash
# 并行启动三个后台任务
(codex "[Task A1 prompt]" &)
(codex "[Task A2 prompt]" &)
(codex "[Task A3 prompt]" &)

# 等待所有任务完成
wait

echo "所有并行任务完成"
```

## 第四步：轮询等待结果

用户启动后，轮询检查完成信号：

```bash
# 检查各任务完成状态
for task in A1 A2 A3; do
  if grep -q "CODEX_DONE" .pipeline/parallel/tasks/task_${task}_result.md 2>/dev/null; then
    echo "Task ${task}: ✅ 完成"
  else
    echo "Task ${task}: ⏳ 进行中"
  fi
done
```

用 `AskUserQuestion` 询问：

> **任务状态**
>
> - Task A1: [完成/进行中]
> - Task A2: [完成/进行中]
> - Task A3: [完成/进行中]
>
> 选项：
> - `继续等待`
> - `检查当前结果`

## 第五步：汇总结果

所有任务完成后，汇总到主上下文：

```bash
# 汇总各任务结果
cat > .pipeline/memory/parallel_summary.md << 'EOF'
# 并行执行结果汇总

## 执行时间
[时间戳]

## 任务结果摘要

### Task A1: 文献调研
[task_A1_result.md 摘要]

### Task A2: Gap 分析
[task_A2_result.md 摘要]

### Task A3: 引用核查
[task_A3_result.md 摘要]

## 汇总结论
[综合各任务结果，给出整体结论]
EOF

cat .pipeline/memory/parallel_summary.md
```

用 `AskUserQuestion` 展示：

> **并行执行完成**
>
> **汇总结论**：[整体结论]
>
> | 任务 | 状态 | 关键产出 |
> |------|------|---------|
> | Task A1 | ✅ | [产出摘要] |
> | Task A2 | ✅ | [产出摘要] |
> | Task A3 | ✅ | [产出摘要] |
>
> 选项：
> - `接受结果，继续`
> - `某个任务需要重做`
> - `全部重新执行`

## 并行执行架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator (总指挥)                      │
│   - 定义任务组  - 汇总结果  - 决策推进                        │
└─────────────────────────────────────────────────────────────┘
                    │           │           │
           ┌───────▼─┐   ┌───────▼─┐   ┌───────▼─┐
           │ Task A1 │ //│ Task A2 │ //│ Task A3 │
           │ (Codex) │ //│ (Codex) │ //│ (Codex) │
           └─────┬───┘   └─────┬───┘   └─────┬───┘
                 │             │             │
                 └──────────────┼─────────────┘
                                │
                    .pipeline/parallel/tasks/
                    (独立上下文，独立执行)
                                │
                    ┌───────────┴───────────┐
                    │  汇总到 main context │
                    └───────────────────────┘
```

## 独立上下文隔离机制

每个并行任务使用独立上下文文件：

```
.pipeline/parallel/tasks/
├── task_A1_context.md     # Task A1 输入上下文（隔离）
├── task_A1_result.md      # Task A1 输出结果
├── task_A2_context.md     # Task A2 输入上下文（隔离）
├── task_A2_result.md      # Task A2 输出结果
├── task_A3_context.md     # Task A3 输入上下文（隔离）
└── task_A3_result.md      # Task A3 输出结果
```

**隔离原则**：
- 各任务不看其他任务的输出
- 不读取项目主上下文（避免偏见）
- 只基于任务描述执行
- 结果汇总后才进行综合判断

## 冲突解决机制

如果多个任务结果存在冲突：

```
冲突检测：
  └─ 如果 task_A1 和 task_A2 结果矛盾

解决方式：
  1. 记录冲突到 parallel_summary.md
  2. 交给用户决策
  3. 或交给独立 Agent（如 F14 分析）判断
```