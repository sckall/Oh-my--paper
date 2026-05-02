---
id: omp:review
name: omp:review
version: 1.0.0
description: C18/D24 Peer Review - Internal and external paper review. DEPRECATED for problem-finding: use omp:critique + omp:triage instead. This skill now handles Final Review only (publish recommendation).
stages: [C18, D24]
tools: [read_file, write_file, Bash]
---

# omp:review - Peer Review

Use this skill for paper review.

## Invocation

```
/omp:review [--check-journal {journal-id}]
```

### 可选参数
| 参数 | 说明 | 示例 |
|------|------|------|
| `--check-journal` | 检查论文是否符合期刊偏好 | `--check-journal computer-science-china` |

## Stages

- C18: PEER_REVIEW (internal)
- D24: 3RD_PARTY_REVIEW (external)

## Tasks

1. （可选）读取期刊画像（`.pipeline/memory/journal_profile.md`）
2. Methodology-Evidence consistency check
3. Trial count verification
4. Statistical significance validation
5. CRITICAL fabrication detection
6. Citation verification
7. Journal match check (if `--check-journal` specified)

### 期刊匹配度检查
- 检查论文标题是否符合期刊风格（参考 `title_style`）
- 检查论文章节结构是否符合期刊常用章节（参考 `writing_style.common_sections`）
- 检查论文是否有足够的实验结果（参考 `empirical_tendency`）
- 检查论文创新点是否明确（参考 `innovation_metrics`）
- 生成期刊匹配度报告（0-10 分）
