---
id: omp:write
name: omp:write
version: 1.0.0
description: C16-C19 Paper Writing - Draft, revise, and polish paper
stages: [C16, C17, C18, C19]
tools: [read_file, write_file, Bash]
tracker: reads .workflow/paper-issues.yaml (actionable items); writes to .workflow/paper-issues.yaml (completed items)
---

# omp:write - Paper Writing

Use this skill for paper writing and revision.

## Invocation

```
/omp:write [--match-style {journal-id}]
```

### 可选参数
| 参数 | 说明 | 示例 |
|------|------|------|
| `--match-style` | 模仿期刊的写作风格 | `--match-style computer-science-china` |

## Stages

- C16: PAPER_OUTLINE
- C17: PAPER_DRAFT
- C18: PEER_REVIEW
- C19: PAPER_REVISION

## Tasks

1. （可选）读取期刊风格指南（`.pipeline/memory/style_guide.md`）
2. Generate paper outline
3. Write initial draft sections (matching journal style if specified)
4. Internal peer review
5. Revision based on feedback
6. Citation verification
7. Generate pre-submission checklist based on journal profile

### 期刊风格模仿
- 如果指定了 `--match-style` 参数，参考 `.pipeline/memory/style_guide.md`
- 标题风格：参考 `title_style` 部分
- 行文风格：参考 `writing_style` 部分
- 引用格式：使用 `citation_style` 指定的格式

## Tracker Integration

### 读
- `.workflow/paper-issues.yaml` — C16 前调用 omp:critique 扫描问题，读取 status: actionable 的 issue
- `.workflow/decision-log.yaml` — 确认当前 gate 已通过

### 写
- `.workflow/paper-issues.yaml` — 每修复一个 issue，记录 resolved 时间和 completed 状态
- `.workflow/decision-log.yaml` — Write→Review gate 记录

### 写作前置检查（C16 开始前）
- [ ] omp:triage 已完成，所有 open issue 已有 actionable/wont-do 判定
- [ ] decision-log 记录了 Write 阶段开始的 PROCEED 决策
- [ ] citation 缺失问题已通过 omp:critique 全部处理

### 约束
- MUST NOT modify: 已被 omp:triage 判定为 wont-do 的 issue
- citation 问题必须先调用 omp:critique 确认为 open，再修复
- 每完成一个 section，更新 paper-issues.yaml 对应 issue 的 resolved 字段

### 流程
C16 outline → C17 draft → C18 peer_review（调用 omp:critique 扫描）→ C19 revision（处理 critique 结果）
