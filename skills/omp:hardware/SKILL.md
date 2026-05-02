---
id: omp:hardware
name: omp:hardware
version: 1.0.0
description: A+ Hardware Detection - Detect and report hardware capabilities
stages: [A+]
tools: [read_file, write_file, Bash]
---

# omp:hardware - Hardware Detection

Use this skill to detect hardware capabilities.

## Invocation

```
/omp:hardware
```

## Stage

A+ - Hardware Detection

## Tasks

1. Detect CPU, GPU, memory
2. Estimate compute budget
3. Generate hardware report
4. Store in hardware_status.md
