---
id: omp:gate
name: omp:gate
version: 1.0.0
description: Gate Checkpoint - Quality gate at A5, B10, C20
stages: [A5, B10, C20]
tools: [read_file, write_file, Bash]
---

# omp:gate - Quality Gate

Use this skill for quality checkpoints.

## Invocation

```
/omp:gate
```

## Gates

- A5: LITERATURE_SCREEN
- B10: EXPERIMENT_DESIGN
- C20: QUALITY_GATE

## Decision Criteria

| Decision | Condition |
|----------|-----------|
| PROCEED | All criteria met |
| REFINE | Minor issues |
| PIVOT | Major blockers |
