---
id: omp:analyze
name: omp:analyze
version: 1.0.0
description: B14 Result Analysis - Independent LLM analysis of experimental results
stages: [B14]
tools: [read_file, write_file, Bash]
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
