# CiteScore 部分实装 + MJL 为什么 v0.1 不做

## CiteScore（部分实装）

### 站方实情

Scopus CiteScore 入口：

```
https://www.scopus.com/sources?searchTerm={query}
https://www.scopus.com/sourceid/{scopus_id}
```

==半公开==——主指标（CiteScore / SNIP / SJR）能直接看到，详情（学科百分位 / 5 年趋势 / 引用列表）需 Scopus 机构登录。

### v0.1 实装范围

| 字段 | 是否实装 | 原因 |
|---|---|---|
| `citescore_value` | ✅ | 顶部主指标公开 |
| `citescore_year` | ✅ | 同上 |
| `snip` | ✅ | 同上 |
| `subject_percentile` | ⏳ TODO | 详情段需登录 |
| `5yr_trend` | ⏳ TODO | 详情段需登录 |
| `cited_count` | ⏳ TODO | 引用列表需登录 |

### 抓取路径

```bash
# Tier 2 firecrawl（先试）
firecrawl scrape \
  'https://www.scopus.com/sources?searchTerm=Scientific%20Reports' \
  --formats markdown,html

# 如果返回空 / 0 字段 → Tier 3
# Scopus 是混合渲染，部分内容 JS 后注入
```

如 firecrawl 拿不到主指标，升 Tier 3：

```python
mcp__chrome-devtools__navigate_page(url="https://www.scopus.com/sourceid/19700188320")
mcp__chrome-devtools__wait_for(selector=".sourceMetricsValue")
mcp__chrome-devtools__evaluate_script(
    expression="document.querySelector('.sourceMetricsValue').innerText"
)
```

### Scopus ID 反查

CiteScore 用 Scopus 内部 `sourceid`（数字）。需要先用 ISSN 搜，从结果链接里抽 ID。

```
https://www.scopus.com/sources?searchTerm=2045-2322
→ 解析返回 HTML 里的 a[href] 含 /sourceid/N → N 是 sourceid
```

### CiteScore 与 letpub 的关系

==letpub 详情页已经转载了 CiteScore 主指标==——大多数情况用 letpub 转载值就够。本 adapter 只在以下场景调：

1. letpub 的 `citescore` 字段为 None（期刊不在 letpub 库）
2. 用户明确要求"从 Scopus 直查"
3. 字段交叉验证发现 letpub 与 SJR 数字差距 > 20%（疑似 letpub 滞后）

## MJL (Web of Science Master Journal List)

### v0.1 不做的原因

```
https://mjl.clarivate.com/home
```

实测：纯 SPA，static HTML 响应只有：

```html
<div id="root"></div>
```

要拿数据必须：

- Tier 3 chrome-devtools（headless Chrome 跑 SPA，每条 5-10s）
- 或 Clarivate API（需付费订阅）

==价值评估==：MJL 唯一独家数据是 "是否被 SCIE/SSCI/AHCI/ESCI 收录" 这个二元事实。但：

- letpub 详情页已转载这个信息（每个学科行标 `[Science Citation Index Expanded (SCIE)]`）
- NCBI NLM Catalog 可作 PubMed 收录证据
- Scopus 收录通过 CiteScore 页面间接验证

**结论**：v0.1 标 `mjl_status: "deferred-to-letpub"`，不实装。

### 何时考虑做 MJL？

只有当以下任一成立时才考虑加 MJL adapter：

1. letpub 期刊 SCIE 收录字段被发现错误率 > 5%（实测验证）
2. 出现新场景需要 MJL 独家字段（如"近 6 个月被踢出 SCIE 的期刊清单"）
3. Clarivate 提供免费 API tier（目前是付费 only）

## 维护备注

- DOAJ API 是 v3，URL 路径稳定，但 schema 偶发字段重命名（关注 `bibjson.apc` 字段名变化）
- SJR 每年 6 月更新一次（前一年数据），不是实时——cache 6 个月内同 ISSN 都能用
- Scopus CiteScore 也是年度更新（4-5 月发布前一年数据）
