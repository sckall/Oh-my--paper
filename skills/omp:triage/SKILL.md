---
name: omp:triage
description: 论文问题分流 — 读取 .workflow/paper-issues.yaml，对每个 open issue 判定 actionable/wont-do。不读论文原文。
stages: [review]
tools: [read_file, write_file]
---

# omp:triage — 问题分流（只做决策）

## 约束（必须遵守）
- MUST NOT read: 论文 .tex / .md 原文（那是 critique 的职责）
- MUST NOT modify: 论文原文
- 只处理 status: open 的 issue

## 决策规则
- actionable: 问题真实存在，需要修复，有明确修复方向
- wont-do: 问题可以忽略（微小影响/修复成本过高/原文其实没问题）

## 输出
更新 paper-issues.yaml 中对应 issue 的 status 字段为 actionable 或 wont-do，并填写 detail（决策原因）。

## Invocation

```
/omp:triage
```
