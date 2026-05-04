---
id: ompdebate
name: debate
version: 1.0.0
description: A7 Multi-Agent Debate - Proponent/Opponent/Synthesizer debate for hypothesis validation
stages: [A7]
tools: [read_file, write_file, Bash]
---

# omp:debate - Multi-Agent Debate

Use this skill for hypothesis validation through debate.

## Invocation

```
/omp:debate
```

## Stage

A7 - HYPOTHESIS_GEN +辩论

## Debate Structure

### Round 1: Proponent
- Support hypothesis with evidence
- Find 3 strongest arguments
- Prepare for opponent attacks

### Round 2: Opponent
- Challenge with 3 biggest flaws
- Find contradictions
- Attack weakest points

### Round 3: Synthesizer
- Evaluate argument strength
- Determine hypothesis robustness
- Output: PASS/MODIFY/REJECT
