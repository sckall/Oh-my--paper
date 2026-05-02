---
description: D11 资源规划：估算实验所需 GPU/时间资源
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Oh My Paper Orchestrator。此命令实现 D11 资源规划，估算实验所需资源。

## 第一步：读取实验计划

```bash
cat .pipeline/docs/experiment_plan.md
cat .pipeline/mega/hardware_status.md
```

## 第二步：分析资源需求

根据实验计划，估算资源需求：

```json
{
  "tasks": [
    {
      "id": "task-001",
      "name": "基线实验",
      "depends_on": null,
      "gpu_count": 1,
      "estimated_minutes": 120,
      "priority": 1
    },
    {
      "id": "task-002",
      "name": "方法实验",
      "depends_on": ["task-001"],
      "gpu_count": 1,
      "estimated_minutes": 240,
      "priority": 2
    }
  ],
  "total_gpu_budget": 360,
  "generated": "[时间戳]"
}
```

## 第三步：展示资源估算

用 `AskUserQuestion` 展示：

> **资源规划**
>
> | 任务 | GPU | 预计时间 | 优先级 |
> |------|-----|---------|-------|
> | 基线实验 | 1 | 120 min | 1 |
> | 方法实验 | 1 | 240 min | 2 |
> | 消融实验 | 1 | 180 min | 3 |
> | **总计** | - | **540 min** | - |
>
> **可用硬件**：[根据 hardware_status.md]
>
> 选项：
> - `确认，开始执行`
> - `调整任务配置`
> - `减少资源预算`
> - `取消`

## 第四步：检查时间是否足够

如果估算时间超过可用时间：

> ⚠️ **资源不足警告**
>
> 估算需要：540 分钟
> 可用时间：300 分钟
> 缺口：240 分钟
>
> **建议优化方案**：
> 1. 减少随机种子次数（10 → 3）
> 2. 减少实验条件数
> 3. 降低 max iterations
>
> 选项：
> - `采纳建议，自动调整`
> - `手动调整配置`
> - `继续，但分批执行`

## 第五步：写入资源计划

```bash
cat > .pipeline/docs/resource_plan.json << 'EOF'
{
  "tasks": [...],
  "total_gpu_budget_minutes": 540,
  "gpu_type": "cuda/mps/cpu",
  "estimated_total_hours": 9,
  "optimization_applied": ["减少种子次数"],
  "generated": "[时间戳]"
}
EOF
```

## 资源优化规则

| 情况 | 优化措施 |
|------|---------|
| 实验条件 > 100 组 | 种子数降至 3-5 次 |
| 时间预算不足 | 每轮优化步数 ≤ 5000 |
| GPU 内存不足 | 降低 batch size |
| 时间超过 80% 预算 | 自动保存 checkpoint |

## 动态缩放规则

```
IF 实验条件数 > 100:
    seeds_per_condition = 3  # 严禁强跑 20 次
ELSE IF 实验条件数 > 50:
    seeds_per_condition = 5
ELSE:
    seeds_per_condition = 10
```

## 生成执行计划

根据资源计划，生成具体执行顺序：

```markdown
## 执行计划

### 阶段 1: 基线实验
- 任务: task-001
- GPU: 1
- 时间: 120 min
- 预计完成: [时间]

### 阶段 2: 方法实验
- 任务: task-002
- GPU: 1
- 时间: 240 min
- 预计完成: [时间]

### 阶段 3: 消融实验
- 任务: task-003
- GPU: 1
- 时间: 180 min
- 预计完成: [时间]

**总计**: 540 分钟 (9 小时)
```