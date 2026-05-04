---
name: bison-oa-explore
description: 用于英文 P0 期刊调研中 OA-only / 必须开放获取 / Plan-S 兼容的期刊探索。触发关键词：B!SON / BISON / OA-only / open access journal / Plan-S / DOAJ seal / APC。不用于通用跨学科探索（→openalex-explore）、CS venue（→dblp-cs-explore）、ISSN 校验（→crossref-validator）。
---

# bison-oa-explore

## Method-call

`/bison-oa-explore(title, abstract?, keywords=[])`

定位：OA 特化 adapter。调用 TIB B!SON public API，用标题/摘要/关键词推荐开放获取期刊，并保留 APC、license、Plan-S、DOAJ Seal 等 OA 决策字段。

## 执行流程

1. POST `https://service.tib.eu/bison/api/public/v1/search`。
2. body: `{"title": str, "abstract": str, "keywords": list[str]}`。
3. 解析 `journals[]`，映射 `title/eissn/pissn/publisher_name/apc_max/licenses/publication_time_weeks/doaj_seal/plan_s_compliance/subjects`。
4. 输出 CandidateJournal-compatible JSON，`trust_level=oa-bison`。

## 脚本

```bash
python3 scripts/bison_search.py "transformer attention is all you need"
python3 scripts/test_search.py "transformer attention is all you need"
```

## 输出 Schema

- `identity.title`
- `identity.issn` / `identity.eissn`
- `identity.publisher`
- `fit_score`
- `cost_intel.apc_max`
- `authority_metrics.plan_s_compliance`
- `authority_metrics.doaj_seal`
- `speed_intel.publication_time_weeks`

## 本 skill 的 deletion-spec

- **触发删除条件**：B!SON public API 停止开放，或 DOAJ/OpenAlex 组合已能提供更稳定的 OA-only 推荐排序和同等字段。
- **禁用方式**：删除 `plugins/journal-research-en/skills/bison-oa-explore/`，bump plugin minor，刷新 marketplace/cache。
- **卸载清单**：更新 orchestrator OA 偏好路由、README、PLAN verifier，以及任何引用 B!SON 字段的文档。
