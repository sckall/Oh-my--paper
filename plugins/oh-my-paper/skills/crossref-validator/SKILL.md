---
name: crossref-validator
description: 用于英文期刊 P0 调研中校验已知 ISSN 或 DOI 的 Crossref 元数据。触发关键词：Crossref / ISSN 校验 / DOI 校验 / journal metadata / publisher check / 0028-0836。不用于第一层候选生成（→openalex-explore）、CS venue 搜索（→dblp-cs-explore）、OA-only 推荐（→bison-oa-explore）。
---

# crossref-validator

## Method-call

`/crossref-validator(identifier, mailto?)`

定位：第二层轻量校验 adapter。输入 ISSN 或 DOI，调用 Crossref polite pool，确认期刊名、publisher、ISSN 组和 DOI 覆盖量。

## 执行流程

1. 判定 identifier：ISSN 走 `/journals/{issn}`，DOI 走 `/works/{doi}`。
2. `mailto` 优先读 `CROSSREF_MAILTO`，其次读 `JOURNAL_RESEARCH_MAILTO`；没有则不发送 maintainer mailto，客户可自行配置。
3. 输出 CandidateJournal-compatible JSON；ISSN 路径填 `identity`，DOI 路径填 `work` + `identity`。
4. 若 Crossref 无记录，返回非零并保留 HTTP 错误，不用模型猜字段。

## 脚本

```bash
python3 scripts/crossref_validate.py 0028-0836
python3 scripts/test_validate.py 0028-0836
```

`scripts/doi_to_bibtex.py` 从 `academic-suite:scholar-search` 物理复制，只作为 DOI 兜底工具，不改源。

## 输出 Schema

- `identifier_type`: `issn | doi`
- `candidate.identity.title`
- `candidate.identity.issn`
- `candidate.identity.publisher`
- `authority_metrics.crossref_counts`
- `evidence[].source = crossref-journal | crossref-work`

## 本 skill 的 deletion-spec

- **触发删除条件**：Crossref polite API 不再可用，或 authority-check 已内置稳定 ISSN/DOI 校验并覆盖本 skill 的全部输出字段。
- **禁用方式**：删除 `plugins/journal-research-en/skills/crossref-validator/`，bump plugin minor，刷新 marketplace/cache。
- **卸载清单**：更新 orchestrator 第二层校验表、README skills 表、PLAN verifier 命令、以及任何引用 `crossref-validator` 的 sibling skill。
