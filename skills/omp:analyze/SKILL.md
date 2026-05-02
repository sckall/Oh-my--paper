---
id: omp:analyze
name: omp:analyze
version: 1.0.0
description: B14 Result Analysis - Independent LLM analysis of experimental results
stages: [B14]
tools: [read_file, write_file, Bash]
tracker: writes to .workflow/experiment-log.yaml; reads .workflow/experiment-log.yaml
---

# omp:analyze - Result Analysis

Use this skill for independent analysis of experimental results.

## Invocation

```
/omp:analyze
```

## Stage

B14 - RESULT_ANALYSIS

## Tasks

1. Read experiment data from ledger
2. Independent LLM analysis with separate context
3. Evaluate against hypotheses
4. Provide PROCEED/REFINE/PIVOT recommendations

## Tracker Integration

### 读
- `.workflow/experiment-log.yaml` — 读取 hypothesis 列表和 success criteria
- `.workflow/paper-issues.yaml` — 了解是否有相关的已知问题

### 写
- `.workflow/experiment-log.yaml` — 分析完成后更新对应 run 的 result、evidence、decision 字段

### 分析结果记录
```yaml
runs:
  - id: EXP-{N}
    result: "{客观描述实验结果}"
    evidence: "{具体数值，引用 results/ 文件}"
    decision: PROCEED|REFINE|PIVOT
    analyzed_at: "{YYYY-MM-DD}"
    analysis_notes: "{独立分析结论}"
```

### 约束
- MUST NOT modify: 原始实验数据文件
- decision 必须基于 evidence 中的实际数值，不得引用未记录的数据
- PROCEED 条件：hypothesis 验证成立 + 无 NaN/Inf
- PIVOT 条件：假设被数据证伪
