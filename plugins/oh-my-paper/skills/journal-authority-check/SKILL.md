---
name: journal-authority-check
description: 用于英文 / SCI 路线 P0 期刊调研第二层「验证」的二级权威源交叉核验：当 letpub-sci-journal-review 拿不到 / 不全 / 数据可疑时，调本 skill 跑 SJR (Scimago) + DOAJ + Scopus CiteScore 公开数据做交叉验证。被 journal-research-orchestrator 第二层并发调用，也可单独触发（"这数字 letpub 准吗" / "这刊有没有被 SCIE 收录"）。SJR + DOAJ v0.1 实装，CiteScore 部分实装，MJL 留 stub。触发关键词：SJR / Scimago / DOAJ / CiteScore / Scopus / SCIE 收录 / 交叉验证 / 二级权威 / journal authority。不用于：全画像（那是 letpub-sci-journal-review）、中文众包评论（那是 journal-research-cn:muchong-cn-journal-review）、最终决策（那是 journal-research-orchestrator）、掠夺刊判定（那是 predatory-risk-check）。
---

# journal-authority-check

## 一句话定位

journal-authority-check = 学术界的「工商查询 + 国资委名录」。
输入期刊 ISSN → 二级权威源（SJR / DOAJ / CiteScore / Crossref）交叉核验。
P0 三层流程的**第二层「验证」**辅助，跟 letpub 平行。

## Runtime（推荐方式 — Python 脚本）

==禁止使用 WebFetch 工具访问 DOAJ/Crossref/SJR 等外部 API——可能被 Claude Code 域名安全验证拦截。必须使用下方 Python 脚本。==

```bash
# 检查期刊权威性（DOAJ + Crossref）
python3 plugins/oh-my-paper/skills/journal-authority-check/scripts/authority_check.py "2167-8359"

# 保存到文件
python3 plugins/oh-my-paper/skills/journal-authority-check/scripts/authority_check.py "2167-8359" -o auth.json
```

脚本使用 `urllib.request`（Python 标准库，零依赖）。

==本 skill 是补强不是替代==——letpub 拿到的就用 letpub，本 skill 只在 letpub 缺数据 / 数据可疑 / 用户主动要求第二来源时跑。

## 方法论核心（内联）

- ==LetPub 转载的 JCR 数字可能滞后==——遇到 letpub 拿不到 / 不全 / 用户问"这数字准吗"时，调本 skill 跑 SJR + DOAJ + CiteScore 三源做交叉验证。
- 本 skill 是**补强不是替代**：letpub 拿到的就用 letpub，本 skill 只在 letpub 缺数据时跑。
- 输出永远标 `trust_level: "authority-secondary"`——决策矩阵中单独成列「二级权威核验」，不和 letpub 的 `authoritative` 字段混展示。
- ==MJL（Web of Science 主表）v0.1 不抓==——纯 SPA，依赖 letpub 转载的 SCIE/SSCI 收录信息兜底。

## 工具优先级

| 场景 | Primary | Fallback |
|---|---|---|
| GUI 内演示 | **Tier 1** Claude Code Preview / Codex in-app browser | Tier 2 firecrawl |
| Runtime 调度（orchestrator）| **Tier 2** firecrawl scrape | Tier 3 chrome-devtools（仅 CiteScore SPA / MJL）|
| CiteScore 详情 / MJL（如真要做）| **Tier 3** chrome-devtools | 跳过，标 `not_implemented` |

==不许跳到 Tier 4 computer-use==——本 skill 范围内的站都没强 captcha。

## Trust Level

继承 letpub 的分层，本 skill 输出的所有字段标：

| trust_level | 适用 |
|---|---|
| `authority-secondary` | SJR / DOAJ / CiteScore 数据（站方权威，但相对 JCR 是次级权威）|

==输出绝不与 letpub 的 `authoritative` 字段混展示==——orchestrator 决策矩阵里要单独成列「二级权威核验」。

## Adapter 路由（按 ISSN 调度）

```
            User / orchestrator 输入（ISSN list）
                       │
                       ▼
              并发调三个 adapter
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     ✅ SJR         ✅ DOAJ       ⚠️ CiteScore
     (实装)         (实装)         (部分实装)
     scimagojr.com  doaj.org       Scopus 半公开
        │              │              │
        ▼              ▼              ▼
     SJR / H-index  OA whitelist   CiteScore 数值
     Q1-Q4 / rank   APC / license  / SNIP / 学科百分位
                       │
                  合并到 authority_metrics
                  trust_level=authority-secondary
```

MJL（Web of Science Master Journal List）**v0.1 不实装**——纯 SPA，static HTML 空响应。让 letpub 转载的 SCIE/SSCI 收录信息兜底；本 skill 标 `mjl_status: "deferred-to-letpub"`。

## SJR Adapter（v0.1 实装）

### URL 模式

```
搜期刊（按 ISSN 或名称）：
https://www.scimagojr.com/journalsearch.php?q={query}

详情页（journalid 是 SJR 内部 ID）：
https://www.scimagojr.com/journalsearch.php?q={journalid}&tip=sid
```

### 抓取

```bash
firecrawl scrape \
  'https://www.scimagojr.com/journalsearch.php?q=2041-1723' \
  --formats markdown,html \
  --only-main-content true
```

==server-rendered，无登录，无反爬==。

### 字段抽取

| 字段 | 类型 | trust |
|---|---|---|
| `sjr_value` | float | authority-secondary |
| `sjr_quartile` | str ("Q1"-"Q4") | authority-secondary |
| `sjr_subject_categories` | list[dict] `[{category, rank, total}]` | authority-secondary |
| `h_index_sjr` | int | authority-secondary（与 letpub 的 h_index 字段交叉验证）|
| `total_docs_2024` | int | authority-secondary |
| `cited_by_per_doc` | float | authority-secondary |

详见 `references/sjr-adapter-cheatsheet.md`。

## DOAJ Adapter（v0.1 实装）

### URL 模式

```
搜期刊：
https://doaj.org/search/journals?source={"query":{"query_string":{"query":"{issn}"}}}

或公开 API（推荐）：
https://doaj.org/api/search/journals/issn:{issn}
```

### 抓取

DOAJ 有完全公开的 JSON API：

```bash
curl -L 'https://doaj.org/api/search/journals/issn:2041-1723'
```

==无需登录、无反爬、JSON 直出==。

### 字段抽取

| 字段 | 类型 | 说明 |
|---|---|---|
| `in_doaj` | bool | 是否被 DOAJ 收录（OA 白名单核心信号）|
| `doaj_seal` | bool | 是否获 DOAJ Seal（高质量 OA 标记）|
| `apc_doaj` | dict `{has_apc: bool, currency, amount}` | DOAJ 登记的 APC（与 letpub APC 交叉）|
| `license` | str | "CC BY" / "CC BY-NC" / ... |
| `peer_review_process` | str | "Editorial review" / "Double blind" / ... |
| `country` | str | 出版国 |

==被 DOAJ 收录是判断 OA 期刊正规性的关键信号==——掠夺刊几乎都不在 DOAJ。本字段供 `predatory-risk-check` 下游消费。

详见 `references/sjr-adapter-cheatsheet.md`（含 DOAJ 段）。

## CiteScore Adapter（部分实装）

### URL 模式

```
https://www.scopus.com/sourceid/{scopus_id}
或
https://www.scopus.com/sources?searchTerm={issn}
```

### 抓取约束

Scopus 半公开——CiteScore 数值能拿到，详情（学科百分位 / 5 年趋势）需机构登录。

v0.1 实装 ==只取 CiteScore 主指标==，详情留 TODO：

| 字段 | 是否实装 |
|---|---|
| `citescore_value` | ✅ |
| `citescore_year` | ✅ |
| `snip` | ✅ |
| `subject_percentile` | ⏳ TODO（需登录）|
| `5yr_trend` | ⏳ TODO |

如 firecrawl 拿不到（被反爬或 0 字段），升级 Tier 3 chrome-devtools。

## 输出 Schema

返回 dict（按 ISSN 索引）：

```python
{
    "2041-1723": {
        "metadata": {
            "fetched_at": "<ISO>",
            "trust_level": "authority-secondary",
            "sources_consulted": ["sjr", "doaj", "citescore"],
            "tool_tier_used": "2",
        },
        "sjr": {
            "sjr_value": 4.761,
            "sjr_quartile": "Q1",
            "h_index_sjr": 248,
            "subject_categories": [
                {"category": "Multidisciplinary", "rank": 4, "total": 88}
            ],
        },
        "doaj": {
            "in_doaj": False,         # Nature Comms 是 hybrid，不在 DOAJ
            "doaj_seal": None,
        },
        "citescore": {
            "citescore_value": 23.4,
            "citescore_year": 2024,
            "snip": 3.150,
        },
        "mjl_status": "deferred-to-letpub",
        "error_log": [],
    },
    ...
}
```

## Anti-pattern

- ❌ 把 SJR 当 JCR 替代（不同算法，结果不互通；都是参考维度）
- ❌ DOAJ 不在 = 期刊不正规（hybrid OA 期刊本来就不进 DOAJ；OA 期刊不在才是 red flag）
- ❌ 强抓 MJL（纯 SPA，浪费——用 letpub 转载值）
- ❌ 强抓 JCR 公共 UI（同上）
- ❌ 与 letpub 重复抓相同字段（IF / WOS 分区）—— letpub 已转载，本 skill 只补 letpub 没有的二级源
- ❌ 静默丢错——任何 adapter 失败必须 `error_log` 记一条 + 字段返 None

## 协作边界

| Skill | 关系 |
|---|---|
| `journal-research-orchestrator` | **上游**：第二层并发调度方 |
| `letpub-sci-journal-review` | **平行**：与本 skill 并发跑，结果合并到同一 `authority_metrics`（不同 trust_level）|
| `predatory-risk-check` | **下游**：消费本 skill 的 `in_doaj` / `doaj_seal` 信号 |
| `ai-journal-match` | **上游**：本 skill 不主动调它，但 ai-match 输出的 candidate 会被本 skill 验证 |

## References

| 文件 | 用途 | 何时读 |
|---|---|---|
| `references/sjr-doaj-cheatsheet.md` | SJR + DOAJ 抓取命令 + 字段抽取 schema + DOAJ API 用法 | 跑这两个 adapter 时 |
| `references/citescore-mjl-deferred.md` | CiteScore 部分实装注意事项 + MJL 为什么 v0.1 不做 | CiteScore 调用 / 用户问 MJL 时 |

## 本 skill 的 deletion-spec

- **触发删除条件**：letpub 全面接管所有二级权威源转载（SJR/DOAJ/CiteScore 都进 letpub 详情页）使本 skill 冗余；或学术评价生态发生重大变化（如 SJR 停服、DOAJ 关闭）；或 Claude/Codex 原生支持期刊 metadata 多源聚合 MCP。
- **禁用方式**：`rm -rf plugins/journal-research-en/skills/journal-authority-check/` → bump plugin（patch）→ 跑 `python3 plugins/scripts/generate_plugin_marketplaces.py` + `verify_plugin_distribution.py`。
- **卸载清单**：
  - `plugins/journal-research-en/.claude-plugin/plugin.json`（版本 bump）
  - `plugins/journal-research-en/README.md`（Skills 表 + 三层协作图）
  - `plugins/journal-research-en/skills/journal-research-orchestrator/SKILL.md`（第二层并发调用引用）
  - `plugins/journal-research-en/skills/predatory-risk-check/SKILL.md`（下游消费 DOAJ 信号，需调整为直接调 DOAJ API）
