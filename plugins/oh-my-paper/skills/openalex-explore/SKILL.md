---
name: openalex-explore
description: 用于英文 P0 期刊调研第一层跨学科探索时使用。触发关键词：OpenAlex / cross-disciplinary / 英文跨学科选刊 / 物理化学材料工程社科期刊探索 / journal source search。不用于已知 ISSN 校验（→crossref-validator）、CS 专项 venue（→dblp-cs-explore）、OA-only 推荐（→bison-oa-explore）、Google Scholar cross-check（→google-scholar-explore）。
---

# openalex-explore

## Method-call

`/openalex-explore(query, per_page=10, oa_only=false)`

定位：跨学科主源 adapter。输入研究方向、题目或摘要，调用 OpenAlex Works + Sources，把论文检索结果聚合成 CandidateJournal-compatible JSON。

## 执行流程

1. 读取 `OPENALEX_API_KEY`，没有则读 macOS Keychain service `openalex`，仍没有则匿名调用并写 warning。
2. 调 OpenAlex `/works`，使用 `search=<query>`、`group_by=primary_location.source.id`、`filter=primary_location.source.type:journal`。
3. 对 top source.id 调 `/sources/{id}` 补 ISSN、publisher、OA、DOAJ、summary_stats。
4. 输出 `list[CandidateJournal]` 兼容 JSON；`trust_level=openalex-explore`，只供第一层探索，不能直接当最终投稿决策。
5. 遇到 429/5xx 用 1s/2s/4s 退避重试；候选为空时返回非零，让 orchestrator 切副 adapter。

## 脚本

```bash
python3 scripts/openalex_search.py "quantum computing" --per-page 10
python3 scripts/test_explore.py "quantum computing"
```

## 输出 Schema

每个候选至少包含：

- `identity.title`
- `identity.issn` / `identity.eissn`
- `identity.publisher`
- `fit_score`
- `authority_metrics.openalex_id`
- `authority_metrics.source_type`
- `evidence[].source = openalex-grouped-works`

## Anti-pattern

- 不返回 repository / preprint server 作为期刊候选。
- 不把 OpenAlex fit_score 当作最终推荐，只用于候选池排序。
- 不在仓库写入 API key。

## 本 skill 的 deletion-spec

- **触发删除条件**：OpenAlex API 不再稳定提供 Works/Sources 聚合，或官方/本地 MCP 已提供等价 CandidateJournal 输出且覆盖跨学科探索。
- **禁用方式**：删除 `plugins/journal-research-en/skills/openalex-explore/`，bump `journal-research-en` minor，重生成 marketplace 并刷新 Claude/Codex cache。
- **卸载清单**：同步更新 `journal-research-orchestrator` 的学科路由、`README.md` 的 skill 表、`plugins/journal-research-en/.claude-plugin/plugin.json` 版本，以及依赖 OpenAlex fallback 的 sibling adapter 文档。
