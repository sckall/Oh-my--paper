# SJR + DOAJ Cheatsheet

## SJR (Scimago Journal Rank)

### URL 模式

```
搜索（按 ISSN / 名称）：
https://www.scimagojr.com/journalsearch.php?q={query}

详情页（{sid} 是 SJR 内部 ID，搜索结果含 link）：
https://www.scimagojr.com/journalsearch.php?q={sid}&tip=sid
```

### 抓取命令

```bash
firecrawl scrape \
  'https://www.scimagojr.com/journalsearch.php?q=2041-1723' \
  --formats markdown,html \
  --only-main-content true
```

==server-rendered，公开免费，无登录，无反爬==。基于 Scopus 数据。

### 字段抽取（DOM 锚）

详情页主表结构：

```html
<div class="cellslidekontainer">
  <h2>SJR</h2>  → 主指标
  ...
  <table class="data">
    <thead>year | SJR | quartile</thead>
    <tbody>
      <tr><td>2024</td><td>4.761</td><td>Q1</td></tr>
      ...
    </tbody>
  </table>
</div>

<div>
  <h2>Citations per document</h2>
  ...
</div>

<div>
  <h2>Subject Category</h2>
  <table>
    <tr><td>Multidisciplinary</td><td>Q1</td><td>4/88</td></tr>
  </table>
</div>
```

| 字段 | DOM 抽取规则 |
|---|---|
| `sjr_value` | 第一张表格最新年的 SJR 列 |
| `sjr_quartile` | 同行 quartile 列 |
| `h_index_sjr` | 顶部 "h-index: N" 文本 |
| `subject_categories` | "Subject Category" 表全行 |
| `total_docs_2024` | "Total documents" 表最新年 |
| `cited_by_per_doc` | "Citations per document" 表最新年 |

## DOAJ (Directory of Open Access Journals)

### URL / API 模式

==DOAJ 有公开 JSON API，优先用 API==：

```
公开 API（推荐）：
https://doaj.org/api/search/journals/issn:{issn}

Web 搜索（fallback，HTML 解析）：
https://doaj.org/toc/{issn}
```

### 抓取命令

```bash
# JSON API（首选）
curl -L 'https://doaj.org/api/search/journals/issn:2045-2322' | jq '.results[0]'
```

API 返回完整 JSON：

```json
{
  "results": [
    {
      "id": "...",
      "bibjson": {
        "title": "Scientific Reports",
        "issn": "2045-2322",
        "eissn": null,
        "publisher": {"name": "Nature Portfolio", "country": "GB"},
        "license": [{"type": "CC BY", "url": "..."}],
        "apc": {"has_apc": true, "max": [{"price": 2290, "currency": "USD"}]},
        "editorial": {"review_process": ["Single anonymous peer review"]},
        "subject": [{"term": "Multidisciplinary"}, ...]
      },
      "admin": {"seal": false}
    }
  ]
}
```

### 字段抽取（API 路径）

| 字段 | JSON 路径 |
|---|---|
| `in_doaj` | `total > 0`（API 返 results 数）|
| `doaj_seal` | `results[0].admin.seal` |
| `apc_doaj.has_apc` | `results[0].bibjson.apc.has_apc` |
| `apc_doaj.amount` | `results[0].bibjson.apc.max[0].price` |
| `apc_doaj.currency` | `results[0].bibjson.apc.max[0].currency` |
| `license` | `results[0].bibjson.license[0].type` |
| `peer_review_process` | `results[0].bibjson.editorial.review_process[0]` |
| `country` | `results[0].bibjson.publisher.country` |

### 关键判断逻辑

```python
if total == 0:
    in_doaj = False
    # 不一定是 red flag——hybrid OA 期刊本来就不在 DOAJ
    # 只在 ai-journal-match 输出的 OA 标签为 True 时才是 red flag
else:
    in_doaj = True
    # 进一步看 doaj_seal（高质量 OA 标记）
```

==掠夺刊 99% 不在 DOAJ==——`predatory-risk-check` 下游会消费 `in_doaj` 信号。

## 共同边缘案例

| 场景 | 处理 |
|---|---|
| ISSN 不存在 / 拼错 | SJR 返 0 结果 / DOAJ API 返 `total: 0` → return None + error_log |
| 期刊改名（旧 ISSN 仍能搜到，但数据停在停刊年）| SJR 标 `last_updated_year`，提示 stale |
| 多个版本（print + electronic ISSN）| 都查一遍取并集，去重保留更全的 |
| API rate limit | DOAJ 默认 100 req/15min，远超本 skill 单次需求；不用 throttle |
| firecrawl 拿 SJR 拿到 0 行 | 用 curl + Mozilla UA 重试；仍失败升 Tier 3 chrome-devtools |

## 性能基线

- SJR：单次 1-2s，0 反爬
- DOAJ API：< 500ms，0 反爬
- 推荐节奏：SJR ≥ 0.5s/req，DOAJ 无需 throttle
