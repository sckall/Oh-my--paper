# LetPub 字段抽取 Schema

LetPub 详情页用 server-rendered HTML 表格组织信息。firecrawl 转 markdown 后字段以 `| key | value |` 行为主。

## DOM 锚点

主信息块在 `#main_content` 内，结构是嵌套 `<table>`：

- 顶部 banner：期刊名 + ISSN
- 第一张大表：Authoritative metrics（IF / 分区 / CiteScore / SJR / SNIP / h-index / APC / OA）
- 第二张表：CAS 双轨分区 + 预警名单（年份矩阵）
- 第三张表：网友分享（审稿速度 / 录用率）+ LetPub 评分
- 评论列表：`<div class="reviews">` 或类似，分页

==DOM 类名不稳定==——优先用 markdown 文本匹配（key 列文字），不要硬编码 CSS selector。

## Markdown 行匹配规则

firecrawl `--formats markdown,json --only-main-content true` 输出后，关键 key 文本（中文）：

| 字段 | markdown key 文本 | 抽取规则 |
|---|---|---|
| `journal_name` | 顶部 H1 / banner | 第一行非空 |
| `issn` | "ISSN" | 行尾 4-4 数字串（含 X 校验位）|
| `eissn` | "E-ISSN" / "eISSN" | 同上 |
| `impact_factor_2024` | "2024-2025最新影响因子" / "影响因子" | float |
| `impact_factor_5yr` | "五年影响因子" | float |
| `jci` | "JCI期刊引文指标" / "JCI" | float |
| `citescore` | "CiteScore" + 年份 | float |
| `sjr` | "SJR" | float |
| `snip` | "SNIP" | float |
| `h_index` | "h-index" | int |
| `wos_quartile` | "WOS分区等级" | "1区" / "2区" / "Q1".. 之一，统一转 Q1-Q4 |
| `wos_subjects` | 行内含 "SCIE" / "SSCI" 关键字 | regex `(\w+) \| (SCIE\|SSCI\|...) \| (Q[1-4]) \| (\d+/\d+)` |
| `cas_partition_legacy` | "**期刊分区表**（YYYY 年 X 月升级版）" | ==实测页面无"中科院"三字==。多版本可能并存（如 2025 + 2023），抽时全部保留为 list[dict]，每条标 frozen 年份 |
| `cas_partition_letpub` | "**《新锐期刊分区表》**（YYYY 年 X 月发布）" | 标 letpub-aggregated + 注 release 月份 |
| `open_access` | "是否OA开放访问" | "Yes"/"No"/"Hybrid" |
| `apc` | "APC" | regex 抽 `GBP\d+ \| USD\d+ \| EUR\d+` |
| `publication_freq` | "出版周期" | str |
| `year_first_pub` | "出版年份" | int |
| `articles_per_year` | "年文章数" | int |
| `gold_oa_ratio` | "Gold OA文章占比" | percentage → float 0-1 |
| `review_speed_user_months` | "平均审稿速度" + "网友分享：平均X个月" | float |
| `acceptance_rate_user` | "平均录用比例" + "网友分享：X%" | percentage → float 0-1 |
| `letpub_score` | "LetPub 评分" + "(N人评分)" | regex `(\d+\.\d+) \((\d+)人.+声誉(\d+\.\d+)/影响力(\d+\.\d+)/速度(\d+\.\d+)` |
| `user_review_count` | "共N条" / "N人参与" | int |
| `in_warning_list` | "期刊分区表预警名单" / "新锐期刊分区表预警名单" | ==实测发现值不只 bool==——可能是 "预警原因：Under Review" 这类 reason 字符串。schema 升级到 `{<year>: {in_list: bool, reason: str \| None}}` |
| `sci_index_status` | 顶层字段 | 期刊在 SCIE/SSCI 索引中的当前状态（如 "Under Review" / "Active" / "Discontinued"），独立于年份矩阵 |

## 评论摘要抽取

最近 N 条评论（默认 5）：

```
| date | author | research_dir | cycle_months | decision | raw |
```

- date：评论时间（首行 `(YYYY-MM-DD)`）
- author：用户名
- research_dir：研究方向（"研究方向: ..."）
- cycle_months：投稿周期（"投稿周期: 约X个月"）
- decision：录用情况（"一投修改后录用" / "拒稿" / ...）
- raw：原文（去掉空白）

## Trust Level 映射

| 字段类别 | trust_level |
|---|---|
| 3.1 全部 IF/分区/CiteScore/SJR/SNIP/h-index/APC/OA | `authoritative`（标 `source: LetPub-aggregated (origin: JCR/Scopus)`）|
| `cas_partition_legacy` | `frozen`（附 `frozen_year: 2025`）|
| `cas_partition_letpub` | `letpub-aggregated` |
| 3.3 全部 review_speed / acceptance / letpub_score / 评论 | `community` |
| 3.4 in_warning_list / warning_reasons | `letpub-aggregated` |

## 缺失字段处理

任一字段抽取失败：

```python
authoritative["impact_factor_2024"] = None
error_log.append({
    "field": "impact_factor_2024",
    "reason": "regex match failed on row '影响因子: -'",
    "raw_value": "-"
})
```

==永远不要伪造数值==。返回 `null` + `error_log` 是正确行为。

### 已知边缘案例（实测 2026-04-27）

| 字段 | 边缘值 | 处理 |
|---|---|---|
| `h_index` | "暂无h-index数据"（中文字符串）| → `None` + error_log "no h-index data published" |
| `acceptance_rate_user` | 空字符串 | → `None` + error_log "field empty on page" |
| `cas_partition_legacy` | 多版本同时存在（2025 + 2023）| 保留 `list[dict]`，按 `frozen_year` 排序 |
| `wos_quartile` | 跨学科多分区（"3区1区4区" 拼接）| ==**这是 firecrawl markdown 副作用**==——见下节 |

## ⚠️ Firecrawl markdown 副作用

实测发现：firecrawl `--formats markdown` 把 LetPub 的**多列分区表**（`大类学科 | 小类学科 | Top期刊 | 综述期刊`）拍扁成一行，例如：

```
综合性期刊 3区1区4区
```

==分不清哪个数字属于哪一列==。

**Mitigation**（按代价排序）：

1. **Tier 1 Preview**（开发期 / 单条精解）：用 `preview_eval` 抓 `document.querySelector('table.partition').innerText`，DOM 列结构保留
2. **Tier 2 firecrawl `--formats html`**（runtime 批量）：换 HTML 输出，自己解析 `<tr>/<td>`
3. **Tier 2 markdown + structured fallback**：双开 `--formats markdown,html`，分区字段从 html 解析，其他字段从 markdown

orchestrator 调度时建议默认走 mitigation #2（html 一次拿下，runtime 友好）。

## 输出 JSON 完整 schema

```json
{
  "metadata": {
    "fetched_at": "2026-04-27T05:30:00Z",
    "tool_tier_used": "2",
    "source_url": "https://letpub.com.cn/...",
    "letpub_id": 8411,
    "cas_legacy_status": "frozen since 2026",
    "cas_replacement_source": "LetPub 新锐期刊分区表",
    "skill_version": "0.1.1"
  },
  "identity": {
    "journal_name": "Nature Communications",
    "issn": "2041-1723",
    "eissn": null,
    "publisher": "Nature Portfolio",
    "official_site": "https://www.nature.com/ncomms",
    "submission_site": "https://mts-ncomms.nature.com/cgi-bin/main.plex"
  },
  "authoritative": { /* 3.1 字段 */ },
  "cas_legacy": { "quartile": "1区", "frozen_year": 2025 },
  "cas_letpub": { "category": "综合性期刊", "quartile": "1区", "version": "2026-03" },
  "community": { /* 3.3 字段 */ },
  "risk": { /* 3.4 字段 */ },
  "raw_snippet_path": "./cache/letpub-8411-20260427.md",
  "error_log": []
}
```
