---
id: omp:experiment
name: omp:experiment
version: 1.0.0
description: B9-B13 Experiment Loop - Design, run, and iterate experiments
stages: [B9, B10, B11, B12, B13]
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
