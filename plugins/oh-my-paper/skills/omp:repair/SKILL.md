---
id: omp:repair
name: omp:repair
version: 1.0.0
description: B13 Self-Repair - Trace and fix NaN/Inf issues in code
stages: [B13]
tools: [read_file, write_file, Bash]
---

# omp:repair - Self-Repair

Use this skill to fix code issues.

## Invocation

```
/omp:repair
```

## Stage

B13 - ITERATIVE_REFINE

## Self-Repair Principles

1. **No try-except masking** - Fix root cause
2. **No np.nan_to_num()** - Fix logic, not symptoms
3. **Trace to root cause** - Find the real issue
4. **Verify fix** - Test after repair

## Common Issues

| Issue | Fix |
|-------|-----|
| High learning rate | Reduce rate, add gradient clipping |
| Division by zero | Add eps or check denominator |
| Unnormalized values | Add normalization layer |
| Numerical overflow | Scale input, add stability checks |
