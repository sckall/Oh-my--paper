---
id: omp:resource
name: omp:resource
version: 1.0.0
description: B11 Resource Planning - Plan compute and time resources for experiments
stages: [B11]
tools: [read_file, write_file, Bash]
---

# omp:resource - Resource Planning

Use this skill for experiment resource planning.

## Invocation

```
/omp:resource
```

## Stage

B11 - CODE_GENERATION

## Tasks

1. Estimate experiment runtime
2. Plan compute allocation
3. Set time guards
4. Define budget limits (80% stop)
