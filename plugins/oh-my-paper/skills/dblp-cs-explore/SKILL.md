---
name: dblp-cs-explore
description: 用于英文 P0 期刊调研中计算机科学 / 软件工程 / AI / CS venue 专项探索。触发关键词：dblp / CS venue / computer science journal / TPAMI / transactions pattern analysis / 计算机期刊。不用于跨学科默认探索（→openalex-explore）、OA-only 推荐（→bison-oa-explore）、已知 ISSN 校验（→crossref-validator）。
---

# dblp-cs-explore

## Method-call

`/dblp-cs-explore(query, limit=10, include_conference=false)`

定位：CS 专项 venue adapter。先用 dblp venue search 找候选，再用 OpenAlex Sources 反查 ISSN 和 publisher。

## 执行流程

1. 调 `https://dblp.org/search/venue/api?q=<query>&format=json`。
2. 默认只保留 `type=Journal`；用户明确需要会议路线时加 `--include-conference`。
3. 对每个 venue display name 调 OpenAlex `/sources?search=<venue>`，补 ISSN、OA、publisher、summary_stats。
4. 输出 CandidateJournal-compatible JSON；OpenAlex 未命中时保留 dblp venue，ISSN 置 `null` 并写 warning。

## 脚本

```bash
python3 scripts/dblp_search.py "transactions pattern analysis"
python3 scripts/test_search.py "transactions pattern analysis"
```

## 输出 Schema

- `identity.title`
- `identity.issn`
- `authority_metrics.dblp_url`
- `authority_metrics.dblp_type`
- `authority_metrics.openalex_id`
- `evidence[].source = dblp-venue-search`

## 本 skill 的 deletion-spec

- **触发删除条件**：dblp venue API 停用，或 OpenAlex / Semantic Scholar 已能稳定覆盖 CS venue + ISSN 映射。
- **禁用方式**：删除 `plugins/journal-research-en/skills/dblp-cs-explore/`，bump plugin minor，刷新 marketplace/cache。
- **卸载清单**：更新 orchestrator 工程/计算机路由、README、PLAN verifier，以及任何将 CS 查询委托给本 skill 的说明。
