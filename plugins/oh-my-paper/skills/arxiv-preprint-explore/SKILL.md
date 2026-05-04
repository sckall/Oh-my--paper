---
name: arxiv-preprint-explore
description: 用于英文 P0 期刊调研中从 arXiv preprint 反推投稿 venue。触发关键词：arXiv / preprint / cs.LG / physics preprint / math preprint / 预印本反推期刊。不用于已知 ISSN 校验（→crossref-validator）、CS venue 直接查找（→dblp-cs-explore）、OA-only 推荐（→bison-oa-explore）。
---

# arxiv-preprint-explore

## Method-call

`/arxiv-preprint-explore(query_or_category, max_results=5)`

定位：preprint 反推 adapter。先从 arXiv category / author / free text 抽样 preprint，再尝试用 OpenAlex 反查这些 preprint 的正式出版 source，最后聚合 venue 频次。

## 执行流程

1. 调 arXiv Atom API：category 输入转 `cat:<category>`，自由文本转 `all:<query>`。
2. 抽取 arXiv id、title、authors。
3. 对每条 entry 先尝试 OpenAlex `/works/arxiv:{id}`；如果当前 OpenAlex 不支持该 resolver，则降级为 title search 并扫描非 repository 的 `primary_location` / `locations`。
4. arXiv API 429 或无结果时，降级到 OpenAlex category query 聚合，并在 `warnings` 明确标记。
5. 输出 CandidateJournal-compatible JSON；CS 类 preprint 可能返回 conference venue，`authority_metrics.source_type` 会如实记录。

## 脚本

```bash
python3 scripts/arxiv_explore.py cs.LG 5
python3 scripts/test_explore.py cs.LG 5
```

`scripts/extract_metadata.py` 从 `academic-suite:scholar-search` 物理复制，用于 arXiv ID 解析兜底，不改源。

## 输出 Schema

- `identity.title`
- `authority_metrics.source_type`
- `authority_metrics.preprint_count`
- `authority_metrics.arxiv_ids`
- `evidence[].source = arxiv-openalex-resolver | arxiv-openalex-fallback`

## 本 skill 的 deletion-spec

- **触发删除条件**：OpenAlex 不再能通过 title/location 反查 preprint 出版 source，或 arXiv / OpenAlex 官方提供稳定的 preprint-to-venue endpoint。
- **禁用方式**：删除 `plugins/journal-research-en/skills/arxiv-preprint-explore/`，bump plugin minor，刷新 marketplace/cache。
- **卸载清单**：更新 orchestrator 数学/物理/CS preprint 路由、README、PLAN verifier，以及复用 `extract_metadata.py` 的说明。
