---
description: 实验循环：展示实验方案后确认，每轮结果回来后再决定继续/停止
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Oh My Paper Orchestrator。实验不能盲目启动，每轮都需要确认。

## 第一步：读取当前状态 + 硬件检测

```bash
cat .pipeline/memory/project_truth.md
cat .pipeline/memory/experiment_ledger.md
cat .pipeline/docs/research_brief.json

# Mega 模式：运行硬件检测
node "${CLAUDE_PLUGIN_ROOT}/scripts/hardware-detect.mjs"
cat .pipeline/mega/hardware_status.md
```

### 模型使用策略（根据任务类型选择）

| 任务类型 | 推荐模型 | 切换方式 |
|---------|---------|---------|
| 复杂实验设计/多步推理 | 模型1（综合最强） | `export OPENAI_MODEL_NAME="模型1"` |
| Pilot 调试/简单代码 | 模型2（稍弱但快） | `export OPENAI_MODEL_NAME="模型2"` |
| 大量重复简单生成 | 模型3（便宜快） | `export OPENAI_MODEL_NAME="模型3"` |
| 收敛性分析/数学计算 | 模型4（可能适合代码） | `export OPENAI_MODEL_NAME="模型4"` |

**注意**：通过 `/codex:rescue` 执行时，默认使用模型1。如需切换，在 prompt 开头指定 `MODEL: 模型2`。

用 `AskUserQuestion` 展示当前实验背景：

> **选定方向**：[project_truth 中的创新点]
> **已有实验**：[experiment_ledger 条数，或"尚无"]
> **成功标准**：[successThreshold]
>
> **硬件状态**：
> - 类型：[cuda/mps/cpu]
> - 设备：[device_name]
> - 内存：[memory MB]
>
> 准备进入实验循环。

选项：
- `继续，先设计方案`
- `我先描述一下我想要的实验配置`
- `取消`

如果用户有自己的配置描述，先记录下来再进入设计。

## 第二步：设计实验方案

```
/codex:rescue 阅读 .pipeline/memory/project_truth.md 和 .pipeline/memory/experiment_ledger.md（避免重复失败配置），使用 .claude/skills/inno-experiment-dev/SKILL.md 设计实验方案，写入 .pipeline/docs/experiment_plan.md，不要写代码
```

读取 `experiment_plan.md`，用 `AskUserQuestion` 展示方案摘要，等确认：

> **实验方案**：
> - 数据集：...
> - 基线：...
> - 超参：...
> - 评估指标：...
>
> 确认后开始实现和运行。

选项：
- `方案可以，开始实现`
- `调整某个配置`
- `重新设计方案`

## 第三步（新）：实验设计门控 B10（仅 Mega 模式）

如果 research_brief.json 中 mode 为 "Mega"，在实现前执行门控检查：

```bash
# 检查实验设计文档
cat .pipeline/docs/experiment_plan.md 2>/dev/null || echo "NOT_FOUND"
# 检查基线数量
grep -c "baseline" .pipeline/docs/experiment_plan.md 2>/dev/null || echo "0"
# 检查消融实验规划
grep -c "ablation" .pipeline/docs/experiment_plan.md 2>/dev/null || echo "0"
```

用 `AskUserQuestion` 展示：

> **门控 B10：实验设计**
>
> **检查项**：
> - [ ] 实验设计文档完整（目标、数据集、基线、方法、消融、指标、风险、预算）
> - [ ] 基线模型 ≥ 3 个（当前：{baseline_count}）
> - [ ] 消融实验规划完整
> - [ ] Pilot 运行完成（TIME_ESTIMATE: {estimate}）
>
> **通过条件**：设计文档完整且 Pilot 已运行

选项：
- `通过` — 实验设计批准，进入代码实现
- `修改设计` — 返回修改实验设计
- `重新假设` — 返回假设生成，重新思考方向

如果用户选择"通过"，更新 `.pipeline/mega/PROGRESS.md` 中 B10 为 "passed"。

## 第四步（新）：Pilot 运行 + 时间估算

**仅在 Mega 模式下执行。** Pilot 运行用于估算总时间，避免盲目投入大量计算资源。

### 4.1 设计 Pilot 实验

从完整实验配置中提取最小条件子集：
- 1 个数据集（而非全部）
- 1-2 个基线（而非全部）
- 1 epoch / 少量 iterations
- 小 batch size

用 `AskUserQuestion` 确认 Pilot 配置：

> **Pilot 实验配置**（用于时间估算）
> - 数据集：{pilot_dataset}
> - 基线：{pilot_baseline}
> - 训练：{pilot_epochs} epoch(s)
> - Batch size：{pilot_batch}
>
> Pilot 预计耗时：{estimated_time}
>
> 选项：
> - `运行 Pilot` — 开始小规模测试
> - `调整 Pilot 配置` — 减少 epochs 或 batch size
> - `跳过 Pilot，直接全量运行` — 不推荐

### 4.2 执行 Pilot

```bash
# 在 experiments/ 下创建 pilot_run.py
# 记录开始时间
date +%s

# 运行 Pilot
cd experiments/
python pilot_run.py

# 记录结束时间，计算 TIME_ESTIMATE
date +%s
```

### 4.3 计算 TIME_ESTIMATE

Pilot 完成后，分析日志：

```
Pilot 完成！
- Pilot 耗时：{pilot_time} 秒
- 外推总实验条件数：{total_conditions}
- 估算总时间：{total_estimated_time}

公式：
TIME_ESTIMATE = pilot_time × (total_conditions / pilot_conditions)
```

### 4.4 动态种子缩放

根据实验规模自动调整随机种子次数：

| 实验条件数 | 每条件种子数 |
|-----------|-------------|
| ≤ 20 | 10 次 |
| 21-50 | 5 次 |
| 51-100 | 3 次 |
| > 100 | 3 次（警告用户）|

用 `AskUserQuestion` 展示：

> **实验规模与资源估算**
>
> | 项目 | 值 |
> |------|-----|
> | 总实验条件数 | {total_conditions} |
> | 每条件种子数 | {seeds_per_condition} |
> | Pilot 耗时 | {pilot_time}s |
> | 估算总耗时 | {total_estimated_time} |
>
> 选项：
> - `确认，开始全量运行`
> - `减少实验条件` — 减少基线或数据集
> - `减少种子数` — 从 {seeds} 降至 3
> - `取消，先调整实验设计`

### 4.5 写入时间估算日志

将 Pilot 结果写入 `.pipeline/mega/logs/pilot_result.md`：

```markdown
# Pilot 运行结果
_Date: {datetime}_

## Pilot 配置
- 数据集：{dataset}
- 基线：{baseline}
- Epochs：{epochs}
- Batch size：{batch}

## 时间估算
- Pilot 耗时：{pilot_time}s
- 外推估算：{total_estimated_time}

## 种子缩放
- 总条件数：{total_conditions}
- 每条件种子：{seeds_per_condition}

## 用户决策
- 用户确认：{confirmed}
- 确认时间：{datetime}
```

### 4.6（新）：运行约束检查

在实现代码前，运行约束检查确保符合 HARD CONSTRAINTS：

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/constraints.mjs" experiment
```

用 `AskUserQuestion` 展示检查结果：

> **约束检查结果**
>
> ✅ 通过项：
> - [列出通过项]
>
> ⚠️ 警告项：
> - [列出警告项]
>
> ❌ 失败项：
> - [列出失败项]
>
> **注意**：❌ 项必须在继续前修复

选项（如果有失败项）：
- `修复问题` — 返回代码修改
- `忽略警告继续` — 不推荐
- `取消实验`

## 第五步：实现并运行（带 time_guard）

全量实验实现和运行：

```
/codex:rescue --background --resume 根据 .pipeline/docs/experiment_plan.md 实现实验代码到 experiments/ 目录并运行，将每次运行结果追加到 .pipeline/memory/experiment_ledger.md
```

### 5.1 time_guard 逻辑

在实验循环中加入 time_guard 检查：

```python
# 在训练循环中定期检查时间
import time

start_time = time.time()
max_time_budget = TOTAL_ESTIMATED_TIME * 1.2  # 120% 预算
checkpoint_interval = 100  # 每 100 步保存 checkpoint

for step in range(max_steps):
    # ... 训练代码 ...

    # time_guard 检查
    elapsed = time.time() - start_time
    if elapsed > max_time_budget:
        print(f"TIME_GUARD: 达到 {elapsed:.1f}s，超过预算 {max_time_budget:.1f}s")
        print("保存 checkpoint 并优雅停止...")
        save_checkpoint(step, model_state)
        break

    # 定期保存
    if step % checkpoint_interval == 0:
        save_checkpoint(step, model_state)
```

用 `AskUserQuestion` 确认：

> **全量实验启动**
>
> - 实验条件数：{total_conditions}
> - 估算总耗时：{total_estimated_time}
> - time_guard：80% 预算时自动停止
> - Checkpoint：每 100 步保存
>
> 选项：
> - `开始全量实验`
> - `调整超时阈值`
> - `取消`

### 5.2（新）：代码实现后约束复查

代码实现完成后，再次运行约束检查：

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/constraints.mjs" experiment
```

检查项：
- 是否使用了 NumPy 2.x 兼容的 API
- 是否包含收敛检查
- 是否包含 time_guard
- 是否有 NaN/Inf 掩盖

如果检查失败，用 `AskUserQuestion` 询问：
> ❌ 约束检查未通过
>
> 选项：
> - `修复代码` — 返回修改
> - `忽略继续` — 不推荐

## 第六步：结果回来后，由你决定下一步

读取 `experiment_ledger.md` 最新行，向用户展示结果，用 `AskUserQuestion` 询问：

> **最新实验结果**：[指标] = [值]
> **成功标准**：[threshold]
> **状态**：达标 ✅ / 未达标 ❌

选项（未达标时）：
- `调整超参，再跑一轮`
- `修改实验设计，重新来`
- `这个方向有问题，返回 /omp:ideate`
- `结果够用了，进入写作`

选项（达标时）：
- `很好，进入 /omp:write`
- `还想多跑几组对比实验`

## 实验完成后的智能建议

根据实验结果情况，自动建议下一步：

| 结果情况 | 建议的下一步 |
|---------|------------|
| 结果达标 + 证据充分 | 自动建议：`/omp:analyze` 进行独立 LLM 分析 |
| 结果达标 + 想快速推进 | 直接进入 `/omp:write` |
| 结果接近达标 | 建议 `REFINE` 调整后重新实验 |
| 结果完全不达标 | 建议 `PIVOT` 返回 `/omp:ideate` |

### 自动进入 B14 分析（推荐）

用 `AskUserQuestion` 展示：

> **实验结果评估**
>
> | 指标 | 值 | 成功标准 |
> |------|-----|---------|
> | [metric] | [value] | [threshold] |
>
> 建议：先进行 B14 独立 LLM 分析，获得客观评价后再决定下一步。
>
> 选项：
> - `进入 B14 分析` — 启动 /omp:analyze（推荐）
> - `直接进入写作` — 跳过独立分析
> - `继续调参` — 返回实验调整

这样就实现了 **experiment → analyze → decision** 的自动衔接。
