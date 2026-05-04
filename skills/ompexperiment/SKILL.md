---
id: ompexperiment
name: experiment
version: 1.0.0
description: B9-B13 Experiment Loop - Design, run, and iterate experiments
stages: [B9, B10, B11, B12, B13]
pipeline:
  # B9 EXPERIMENT_DESIGN → B10 Gate 必须串行
  # B11 CODE_GENERATION 可以并行（多个实验条件同时跑）
  # B12 EXPERIMENT_RUN 可以并行（多个实验独立时）
  # B13 ITERATIVE_REFINE 必须串行（依赖 B12 结果）
  sequential: ["B9", "B10", "B13"]
  parallel: ["B11", "B12"]
  max_parallel_agents: 3
tools: [read_file, write_file, Bash]
---

# omp:experiment - Experiment Loop

Use this skill for the experiment pipeline.

## Invocation

```
/omp:experiment
```

## Stages

- B9: EXPERIMENT_DESIGN
- B10: Gate checkpoint
- B11: CODE_GENERATION
- B12: EXPERIMENT_RUN
- B13: ITERATIVE_REFINE

## Tasks

1. Design experiments with success criteria
2. Resource planning and allocation
3. Code generation and validation
4. Experiment execution with monitoring
5. Self-repair for NaN/Inf issues

## 约束

- MUST NOT modify: 论文正文 .tex 文件
- MUST NOT modify: .workflow/paper-issues.yaml（那是 critique/triage 的职责）
- MUST write to: .workflow/experiment-log.yaml（每次实验必须记录）
- 每个 experiment run 之前必须先运行 pilot 估算时间

## B9 前置检查

- [ ] hypothesis 已在 .workflow/ 中注册
- [ ] 数据集/环境已在 resource skill 中确认可用
- [ ] success criteria 已量化（不能是"效果好"这种模糊描述）
- [ ] pilot run 完成并记录了 TIME_ESTIMATE

## 反幻觉约束

- 严禁使用 random.uniform() / random.random() 伪造数据曲线
- 实验必须记录实际指标值，不得事后填写估算值
- NaN/Inf 必须触发 self-repair，不得忽略
