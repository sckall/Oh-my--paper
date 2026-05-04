# JANE Adapter Cheatsheet

## URL 模式

```
https://jane.biosemantics.org/suggestions.php?findJournals=&text={url-encoded-query}
```

`text` 参数：URL 编码后的题目 + 摘要（5-200 字典型）。多段连接用 `+` 或 `%20`。

## 抓取命令

### Tier 2 firecrawl（runtime 主路径）

```bash
firecrawl scrape \
  'https://jane.biosemantics.org/suggestions.php?findJournals=&text=Treatment+of+HIV+in+third+world+countries' \
  --formats markdown,html \
  --only-main-content true
```

### curl 兜底

```bash
QUERY=$(python3 -c 'import urllib.parse;print(urllib.parse.quote("Treatment of HIV in third world countries"))')
curl -L -A 'Mozilla/5.0' "https://jane.biosemantics.org/suggestions.php?findJournals=&text=${QUERY}"
```

### Tier 1 Preview（GUI 演示）

```python
mcp__Claude_Preview__preview_start(
    url="https://jane.biosemantics.org/suggestions.php?findJournals=&text=Treatment+of+HIV"
)
mcp__Claude_Preview__preview_screenshot()
mcp__Claude_Preview__preview_eval(
    expression="Array.from(document.querySelectorAll('table tr')).map(tr => tr.innerText).join('\\n')"
)
```

## 输出 HTML 结构

JANE 返回 server-rendered HTML，主体是结果表格。每行一个候选期刊：

```html
<tr>
  <td>Journal of the International AIDS Society</td>
  <td>0.87</td>  <!-- confidence score -->
  <td>High-quality open access</td>
  <td>Medline-indexed</td>
  <td>PMC</td>
  <td><a href="...">期刊主页</a></td>
</tr>
```

## 字段抽取 schema

| 字段 | DOM 锚 | 类型 | 说明 |
|---|---|---|---|
| `title` | 第 1 列 td 文本 | str | 期刊全名 |
| `confidence` | 第 2 列 td 文本 | float | 0-1，越高越匹配 |
| `tags` | 第 3+ 列 td 文本（多列）| list[str] | "Medline-indexed" / "PMC" / "OA" / "High-quality OA" |
| `official_site` | 第 N 列 a[href] | url | 期刊主页（用于 ISSN 反查）|

## 不在 JANE 输出的字段

- ❌ ISSN / eISSN（必须由 orchestrator 调 letpub 反查 title → issn）
- ❌ Publisher
- ❌ IF / 分区 / CiteScore（不是 JANE 职责，由 letpub 填）

## 边缘案例

| 场景 | 处理 |
|---|---|
| query 为空 / < 5 字 | 拒绝调用，返回 `error: "query too short, min 5 chars"` |
| confidence 全部 < 0.3 | 标 `weak_match: true`，让 orchestrator 决定是否丢弃 |
| 返回 0 候选 | 返回 `{candidates: [], reason: "no matches in PubMed corpus"}` |
| query 含中文字符 | 返回 `error: "JANE only supports English queries"`，建议改 fallback |
| 返回 > 50 候选 | 取前 10（按 confidence desc 排序），其余丢弃 |

## 性能基线（实测预期）

- 单次请求：1-3 s
- 0 反爬观察记录
- 建议节奏：≥ 0.5 s/req 即可（比 letpub 宽松，因为 JANE 是单一研究机构小流量站）

## 维护备注

- JANE 由 Erasmus MC（鹿特丹）维护，是学术研究项目，**不是商业站**——不会频繁改 DOM 结构
- 但 PubMed 语料每年更新，召回结果会逐年漂移——不要 cache 同一 query 超 30 天
