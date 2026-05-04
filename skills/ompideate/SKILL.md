---
id: ompideate
name: ideate
version: 1.0.0
description: A6 Hypothesis Generation - Generate and refine research hypotheses
stages: [A6]
tools: [read_file, write_file, Bash]
tracker: reads .workflow/literature-bank.yaml; writes hypotheses to .workflow/experiment-log.yaml
---

# omp:ideate - Hypothesis Generation

Use this skill to generate research hypotheses.

## Invocation

```
/omp:ideate
```

## Stage

A6 - KNOWLEDGE_EXTRACT

## Tasks

1. Extract knowledge from literature
2. Generate candidate hypotheses
3. Evaluate with multi-persona analysis
4. Select promising directions

## Tracker Integration

### 读
- `.workflow/literature-bank.yaml` — 读取已有文献，寻找研究空白
- `.workflow/paper-issues.yaml` — 了解已知问题，避免重复假设

### 写
- `.workflow/experiment-log.yaml` — 将候选假设注册为 hypothesis，status: proposed
- `.workflow/decision-log.yaml` — Ideation→Experiment gate 决策

### 工作流程
1. 读 .workflow/literature-bank.yaml 分析研究空白
2. 生成候选假设（至少 3 个）
3. 假设写入 .workflow/experiment-log.yaml，decision 留空
4. 调用 omp:debate 验证假设
5. debate 结束后记录最终 hypothesis 到 experiment-log.yaml
6. 调用 omp:gate 记录 PROCEED/REFINE/PIVOT 决策

### 约束
- MUST NOT modify: 论文正文 .tex 文件
- 假设必须可证伪（必须有明确的验证指标）
- 每个 hypothesis 必须引用 1+ 篇文献作为支撑
