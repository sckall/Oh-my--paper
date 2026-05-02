---
id: omp:gate
name: omp:gate
version: 1.0.0
description: Gate Checkpoint - Quality gate at A5, B10, C20
stages: [A5, B10, C20]
tools: [read_file, write_file, Bash]
tracker: writes to .workflow/decision-log.yaml; reads .workflow/experiment-log.yaml and .workflow/literature-bank.yaml
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

## Tracker Integration

### 读
- `.workflow/experiment-log.yaml` — 验证实验是否满足 hypothesis 的 success criteria
- `.workflow/literature-bank.yaml` — A5 gate 验证文献覆盖是否充分
- `.workflow/paper-issues.yaml` — C20 gate 验证问题是否已解决

### 写
- `.workflow/decision-log.yaml` — 必须写入每个 gate 的决策

### Decision Log 格式
```yaml
decisions:
  - id: DEC-{001}
    stage: "{A5|B10|C20}"
    decision: PROCEED|REFINE|PIVOT
    reason: "{具体原因}"
    confidence: 0.85
    evidence: "{引用 experiment-log 或 literature-bank 的 id}"
    timestamp: "{YYYY-MM-DDTHH:mm:ss+08:00}"
    next_step: "{下一个阶段}"
```

### 约束
- MUST write to: .workflow/decision-log.yaml（每个 gate 必须记录，无决策不推进）
- PROCEED 条件：所有 criteria 满足 + 证据链完整
- REFINE 条件：有可修复问题，预计 1 轮内解决
- PIVOT 条件：假设被证伪或根本性问题无法绕过
