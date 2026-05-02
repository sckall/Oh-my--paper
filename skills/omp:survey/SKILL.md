---
id: omp:survey
name: omp:survey
version: 1.0.0
description: A3-A4 Literature Survey - Multi-source search and gap analysis. tracker: write to .workflow/literature-bank.yaml
stages: [A3, A4]
tools: [read_file, write_file, Bash, WebSearch]
---

# omp:survey - Literature Survey

Use this skill for comprehensive literature review.

## Invocation

```
/omp:survey [--journal {journal-id}]
```

### 可选参数
| 参数 | 说明 | 示例 |
|------|------|------|
| `--journal` | 目标期刊 ID，根据期刊偏好过滤文献 | `--journal computer-science-china` |

## Stages

- A3: SEARCH_STRATEGY
- A4: LITERATURE_COLLECT

## Tasks

1. （可选）读取期刊画像（`.pipeline/memory/journal_profile.md`）
2. Multi-source paper search (arXiv, Semantic Scholar, etc.)
3. Gap analysis and comparison
4. Literature bank creation
5. Quality gate at A5

### 期刊偏好过滤
- 如果指定了 `--journal` 参数，优先推荐符合期刊偏好的文献
- 参考 `.my-paper/journals/{journal-id}/analysis/topic-distribution.yaml`
- 优先选择期刊常用数据集和评估指标相关的文献

## Tracker Integration

### 读
- `.workflow/literature-bank.yaml` — 了解已有文献，避免重复收录

### 写
- `.workflow/literature-bank.yaml` — 每篇新文献追加到 `papers` 数组，id 自增
- `.workflow/decision-log.yaml` — Survey→Ideation gate 决策记录（格式见 schema.md）

### 工作流程
1. 读 .workflow/literature-bank.yaml 查重
2. 多源搜索论文（arXiv, Semantic Scholar 等）
3. 相关性 ≥ 0.7 的文献写入 literature-bank.yaml，status: screened
4. 筛选完成后，调用 omp:gate 记录 LITERATURE_SCREEN gate 决策
5. 高质量 accepted 文献更新 status: accepted

### 约束
- MUST write to: .workflow/literature-bank.yaml（新增文献不得跳过 tracker）
- MUST NOT overwrite: 已有记录只追加不覆盖
- 每次 gate 必须写 .workflow/decision-log.yaml
