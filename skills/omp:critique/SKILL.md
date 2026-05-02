---
name: omp:critique
description: 论文审查 — 只找问题，写入 .workflow/paper-issues.yaml。不读代码判断要不要修。
stages: [review]
tools: [read_file, write_file, Bash]
---

# omp:critique — 审查（只找问题）

## 约束（必须遵守）
- MUST NOT modify: 任何 .tex / .md 论文原文
- MUST NOT decide: 不判断问题是否值得修，那是 triage 的职责
- MUST use tracker: 所有问题必须写入 .workflow/paper-issues.yaml

## 工作流程
1. 读取论文文件和上下文
2. 对照文献找 claim-facto 不一致
3. 找逻辑漏洞、引用缺失、格式问题
4. 写入 paper-issues.yaml，状态全部标记为 open

## 输出格式
每条 issue 必须包含：
- id: {paper}-{brief-id}
- entity: 论文相关部分
- rule: 违反的规则类型（citation/method/logic/format）
- status: open
- category: missing-reference/logic-flaw/factual-error/format-issue
- summary: 1-2句话描述问题
- detail: 详细说明
- created: {YYYY-MM-DD}
- resolved: null

## Invocation

```
/omp:critique
```
