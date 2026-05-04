---
name: google-scholar-explore
description: 用于英文 P0 期刊调研中做 Google Scholar cross-check、找具体论文并反推 venue 频次。触发关键词：Google Scholar / scholar cross-check / 具体论文反推期刊 / venue frequency / 引文检索。不用于通用主源探索（→openalex-explore）、CS venue 专项（→dblp-cs-explore）、ISSN 校验（→crossref-validator）。
---

# google-scholar-explore

## Method-call

`/google-scholar-explore(query, limit=30)`

定位：cross-check adapter。优先调用物理复制的 `search_google_scholar.py`，聚合返回结果中的 `venue` 字段，再用 OpenAlex Sources 反查 ISSN；Google Scholar 反爬失败时降级 OpenAlex search 并输出求救卡 warning。

## 执行流程

1. 调 `scripts/search_google_scholar.py "<query>" --limit <N> --output <tmp.json>`。
2. 读取 `results[].venue` 做频次聚合。
3. 对 top venue 调 OpenAlex `/sources?search=<venue>` 补 ISSN/publisher/OA。
4. 若 scholarly 缺失、Google 拒绝或返回空，降级 OpenAlex works source 聚合，`warnings` 写明 fallback。
5. 输出 CandidateJournal-compatible JSON；本 skill 是 cross-check，不替代主探索。

## 脚本

```bash
python3 scripts/gs_explore.py "diffusion model image generation"
python3 scripts/test_explore.py "diffusion model image generation"
```

`scripts/search_google_scholar.py` 从 `academic-suite:scholar-search` 物理复制，不改源。

## 输出 Schema

- `identity.title`
- `identity.issn`
- `fit_score`
- `authority_metrics.venue_count`
- `authority_metrics.google_scholar_fallback`
- `evidence[].source = google-scholar-venue-frequency | google-scholar-openalex-fallback`

## 本 skill 的 deletion-spec

- **触发删除条件**：Google Scholar 访问持续被反爬阻断且 fallback 成为唯一实际路径，或官方/第三方合规 Scholar API 替代当前 `scholarly` 脚本。
- **禁用方式**：删除 `plugins/journal-research-en/skills/google-scholar-explore/`，bump plugin minor，刷新 marketplace/cache。
- **卸载清单**：更新 orchestrator cross-check 路由、README、PLAN verifier、以及对物理复制脚本的说明。
