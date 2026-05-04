# Tier 升级 Playbook

## 升级触发条件

按出现频次列：

| 信号 | 含义 | 升级到 |
|---|---|---|
| `HTTP 200` + 期望字段全到 | Tier 2 firecrawl 工作正常 | 不升级 |
| `HTTP 200` + 部分字段缺失（如 IF 行变成空） | DOM 结构小变动 | 先报 `error_log`，下次抓样本时升 Tier 1 复核 |
| `HTTP 403 Forbidden` | 限频或 UA 黑名单 | **Tier 3** chrome-devtools |
| `HTTP 429 Too Many Requests` | 限频 | 加 `Retry-After` 等待，连续 2 次仍 429 → **Tier 3** |
| `HTTP 503 Service Unavailable` | 站点临时挂 | 等 60s 重试，2 次仍 503 → 报 error，不升级 |
| 内容变成"请稍后再试" / "访问异常" | 软封禁 | **Tier 3** chrome-devtools |
| 内容变成 cloudflare challenge | bot 检测 | **Tier 3**（带 cookie 解 challenge），仍失败 → **Tier 4** computer-use（罕见）|
| firecrawl 返回 "Total lines: 0" | 页面渲染依赖 JS | **Tier 3**（headless Chrome）|
| GUI 内 Preview 截图发现 banner 异常 | 站方临时维护 | 等待，不升级 |

## Tier 1 → Tier 2 降级（开发完毕）

GUI 内打样确认 DOM 结构稳定后，Runtime 用 firecrawl 批量。降级前必须：

- ✅ Tier 1 抓 ≥ 3 个不同 journalid 都拿到完整字段
- ✅ DOM 锚点 / markdown key 文本与 `field-extraction-schema.md` 一致
- ✅ 用 `_shared/showjcr_offline_db/`（如已建）做了 sample 对比

## Tier 2 → Tier 3 升级

==不许静默重试 firecrawl==。换层时必须：

```python
metadata["tool_tier_used"] = "3"
metadata["upgrade_reason"] = "HTTP 403 from firecrawl on 2 consecutive requests"
```

chrome-devtools 调用模板：

```
mcp__chrome-devtools__navigate_page(url="https://letpub.com.cn/...")
mcp__chrome-devtools__wait_for(selector="#main_content table")
mcp__chrome-devtools__take_snapshot()  # 拿 DOM
mcp__chrome-devtools__evaluate_script(expression="document.querySelector('#main_content').innerText")
```

## Tier 3 → Tier 4 升级（极罕见）

LetPub 极少用强 captcha。出现时：

- 用户授权后用 `mcp__computer-use__*`（需 `request_access`）
- 浏览器在 Read tier，不能 click——用 Claude in Chrome 扩展点击 captcha
- 通过后回到 Tier 3 继续

==Tier 4 不写进自动化流程==——必须人工授权后再走。

## 反爬自检清单

每抓 10 条停下来检查：

- [ ] 抓取成功率 ≥ 90%
- [ ] 字段完整率 ≥ 95%（核心字段：IF / 分区 / ISSN / journal_name）
- [ ] 平均响应时间 < 3 s
- [ ] 没有连续 3 个 403/429

任一不达标，先查是否限频太松、UA 不对、是否漏了 cookie。

## 维护备注

LetPub DOM 结构 2024-2026 期间稳定，但**新锐期刊分区表**字段是 2026 新增——见过有些老期刊页面缺这一行（=未收录新锐分区），按 `null` 处理，写 `error_log`：

```json
{
  "field": "cas_partition_letpub",
  "reason": "journal not in 新锐分区 list (likely too new or de-listed)",
  "raw_value": null
}
```
