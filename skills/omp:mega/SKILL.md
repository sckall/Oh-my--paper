---
id: omp:mega
name: omp:mega
version: 1.0.0
description: 25-stage pipeline autopilot - fully autonomous research pipeline with progressive disclosure
stages: [all]
tools: [read_file, write_file, Bash]
---

# omp:mega - 25-Stage Pipeline Autopilot

Use this skill to start the fully autonomous research pipeline.

## Invocation

```
/omp:mega
```

## Stages Covered

> ⚠️ **C17 降重** 是写完初稿后的必经步骤。在 Review 之后、Archive 之前执行。

| Stage | Name | Command |
|-------|------|---------|
| A1 | Topic Init | /omp:setup |
| A+ | Hardware | /omp:hardware |
| A2 | Decompose | /omp:decompose |
| A3-A4 | Survey | /omp:survey |
| A5 | Gate | /omp:gate |
| A6 | Ideate | /omp:ideate |
| A7 | Debate | /omp:debate |
| 8.5 | Theory | /omp:theory |
| B9-B13 | Experiment | /omp:experiment |
| B13 | Repair | /omp:repair |
| B14 | Analyze | /omp:analyze |
| C16-C19 | Write | /omp:write |
| C18 | Review | /omp:review |
| **C17** | **降重 (AIGC)** | `baibaiAIGC` 技能 — 两轮降重流水线 CLI |
| C21 | Archive | /omp:archive |
| C22 | Export | /omp:export |
| D24 | 3rd Party | /omp:3rdparty |
| I25 | Rebuttal | /omp:rebuttal |

## Autopilot Mode

Select "🚀 自动驾驶" to begin fully autonomous execution. The system will:
1. Execute each stage automatically
2. Pause only at decision points (A5, B10, B15, C17, C20)
3. Display progress with progressive disclosure (overview → details → raw)
4. Apply PROCEED/REFINE/PIVOT decisions automatically

## Progressive Disclosure

Three layers of detail:
1. **Overview**: Stage name, progress bar, key metrics
2. **Details**: Subtask status, intermediate results
3. **Raw**: Full logs, configs, code
