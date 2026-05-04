---
id: omp:parallel
name: omp:parallel
version: 1.0.0
description: Parallel Execution - Run multiple agents in parallel
stages: []
tools: [read_file, write_file, Bash, Agent]
---

# omp:parallel - Parallel Execution

Use this skill for parallel multi-agent execution.

## Invocation

```
/omp:parallel
```

## Use Case

Run multiple research tasks concurrently:
- Task A: Literature survey + gap analysis
- Task B: Experiment results analysis
- Task C: Paper draft review

## Tasks

1. Define parallel task groups
2. Create independent contexts
3. Launch agents in parallel
4. Aggregate results
