---
id: ompplan
name: plan
version: 1.0.0
description: Review project status and decide next steps with user
stages: [A1, A2, A3, A4, A5, A6, A7, A8, B9, B10, B11, B12, B13, B14, B15, C16, C17, C18, C19, C20, C21, C22, C23]
tools: [read_file, AskUserQuestion]
tracker: reads project state files; writes to orchestrator_state.md and execution_context.md
---

# omp:plan - Project Planning & Direction

Use this skill to review project status and decide the next step with the user.

## Invocation

```
/omp:plan
```

## Stages

- All stages: A1 through C23

## Tasks

1. Read all project state files
2. Generate status summary
3. Present current status to user with suggested next action
4. Based on user input, execute the chosen action

### Smart Suggestions by Stage

| Current Stage | Suggested Next | Auto-execute Command |
|--------------|---------------|---------------------|
| ideation | Generate hypothesis → Debate | `/omp:ideate` → `/omp:debate` |
| hypothesis | Debate to validate hypothesis | `/omp:debate` |
| literature | Supplement literature → Design experiment | `/omp:survey` → `/omp:experiment` |
| experiment | Analyze experiment results | `/omp:analyze` |
| writing | Peer review | `/omp:review` |
| review | Revise based on review | `/omp:write` |

### User Choices

- `按建议继续：[具体下一步]` — Execute suggested next step
- `自动执行 /omp:mega` — Launch Mega mode auto pipeline
- `我有其他想法` — User has different idea
- `查看详细任务列表` — List detailed task list
- `推进到下一阶段` — Advance to next stage

## Tracker Integration

### 读
- `.pipeline/memory/project_truth.md`
- `.pipeline/memory/orchestrator_state.md`
- `.pipeline/tasks/tasks.json`
- `.pipeline/memory/review_log.md`
- `.pipeline/docs/research_brief.json`
- `.pipeline/memory/experiment_ledger.md`
- `.pipeline/memory/decision_log.md`

### 写
- `.pipeline/memory/orchestrator_state.md` — Updated status
- `.pipeline/memory/execution_context.md` — Task package for next step

## Constraints

- MUST use AskUserQuestion for all confirmation steps
- Never proceed without user input
- Follow the smart suggestions table unless user overrides
