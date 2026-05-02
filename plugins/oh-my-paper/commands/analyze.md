---
description: F14 独立 LLM 分析：调用独立上下文客观分析实验结果
---

你是 Oh My Paper Orchestrator。此命令实现 F14 Result Analysis。

## 🚀 一键执行

当用户说"开始分析"、"运行 analyze"或直接调用此命令时，自动执行：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🤖 F14 独立分析 — B14 结果分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  📊 正在读取实验数据...
  📊 正在构建独立上下文...
  📊 正在调用分析模型...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 自动执行流程

### 1. 准备数据（自动）

```bash
# 准备独立分析上下文（不读取 project_truth 等）
mkdir -p .pipeline/parallel/analysis

# 合并实验数据
cat .pipeline/memory/experiment_ledger.md .pipeline/docs/result_summary.md \
    .pipeline/docs/research_brief.json > .pipeline/parallel/analysis/raw_data.md 2>/dev/null
```

### 2. 执行分析（自动）

调用独立 LLM 分析（使用 inno-experiment-analysis skill）：

```
基于以下实验数据进行客观分析：

[读取 raw_data.md 内容]

分析维度：
1. 指标分析（达标/未达标）
2. 收敛性检查
3. 统计显著性
4. 与假设一致性
5. 最严厉改进建议

输出：JSON 格式决策建议
```

### 3. 展示结果（渐进式披露）

**概要展示**：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🤖 F14 分析完成
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  📊 核心指标: {metric} = {value} ({status})

  🤖 决策建议: {PROCEED/REFINE/PIVOT}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [查看详情]  [接受建议]  [手动决策]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**详情展示**（用户选择时）：

| 维度 | 评估 | 说明 |
|------|------|------|
| 指标分析 | {status} | {details} |
| 收敛性 | {status} | {details} |
| 统计显著性 | {status} | {details} |
| 假设一致性 | {status} | {details} |

## 决策建议格式

```json
{
  "decision": "PROCEED|REFINE|PIVOT",
  "confidence": 0.9,
  "reasoning": "...",
  "required_actions": ["..."],
  "critical_issues": ["..."]
}
```

## 决策规则

| 决策 | 条件 |
|------|------|
| PROCEED | 指标达标 + 统计显著 + 假设一致 + 无 CRITICAL |
| REFINE | 指标接近达标 + 可修复问题 |
| PIVOT | 假设被证伪 + 问题无法修复 |

## 独立隔离机制

```
┌─────────────────────────────────────────┐
│  F14 独立分析（隔离上下文）              │
├─────────────────────────────────────────┤
│  ❌ project_truth.md                     │
│  ❌ orchestrator_state.md               │
│  ❌ decision_log.md                     │
├─────────────────────────────────────────┤
│  ✅ 读取                                │
├─────────────────────────────────────────┤
│  ✅ experiment_ledger.md（原始数据）      │
│  ✅ result_summary.md（结果摘要）         │
│  ✅ research_brief.json（配置）         │
└─────────────────────────────────────────┘
```

## 自动衔接

分析完成后：
- 如果 PROCEED → 自动推进到 B15 决策
- 如果 REFINE → 暂停，等待确认
- 如果 PIVOT → 暂停，等待确认