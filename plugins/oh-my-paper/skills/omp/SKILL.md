---
id: omp
name: Oh My Paper
version: 1.0.0
description: Research pipeline automation for paper writing - 25 stage pipeline with autopilot mode
stages: [A1, A+, A2, A3, A4, A5, A6, A7, 8.5, A8, B9, B10, B11, B12, B13, B14, B15, C16, C17, C18, C19, C20, C21, C22, C23, D24, I25]
tools: [read_file, write_file, Bash, Agent]
---

# Oh My Paper

Use this skill when working on academic research papers with the Oh My Paper pipeline.

## Available Commands

| Command | Description | Stage |
|---------|-------------|-------|
| `/omp:mega` | 25-stage pipeline autopilot | All |
| `/omp:setup` | Initialize project | A1 |
| `/omp:hardware` | Hardware detection | A+ |
| `/omp:decompose` | Problem decomposition | A2 |
| `/omp:survey` | Literature survey | A3-A4 |
| `/omp:gate` | Gate checkpoint | A5, B10, C20 |
| `/omp:ideate` | Hypothesis generation | A6 |
| `/omp:debate` | Multi-agent debate | A7 |
| `/omp:theory` | Theoretical bounds | 8.5 |
| `/omp:experiment` | Experiment loop | B9-B13 |
| `/omp:repair` | Self-repair code | B13 |
| `/omp:resource` | Resource planning | B11 |
| `/omp:analyze` | Result analysis | B14 |
| `/omp:write` | Paper writing | C16-C19 |
| `/omp:review` | Peer review | C18 |
| `/omp:archive` | Knowledge archive | C21 |
| `/omp:export` | Export to Overleaf | C22 |
| `/omp:3rdparty` | Third-party review | D24 |
| `/omp:rebuttal` | Rebuttal response | I25 |
| `/omp:parallel` | Parallel execution | - |
| `/omp:delegate` | Codex delegation | - |
| `/omp:progress` | View progress | - |
| `/omp:sync` | Sync status | - |

## Quick Start

To start the autopilot pipeline:
```
/omp:mega
```

Then select "🚀 自动驾驶" to begin autonomous execution.

## Project Structure

The pipeline creates:
- `.pipeline/memory/` - Shared state between agents
- `.pipeline/docs/` - Research documents
- `.pipeline/tasks/` - Task tracking
- `experiments/` - Experiment code
- `paper/` - Paper LaTeX files
- `results/` - Analysis results
