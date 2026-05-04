# LetPub URL Cheatsheet

## 详情页

```
https://letpub.com.cn/index.php?page=journalapp&view=detail&journalid={id}
```

`journalid` 是 LetPub 内部主键，纯数字。例：

| 期刊 | journalid |
|---|---|
| Nature Communications | 8411 |
| Innovation (The) | 39337 |
| Scientific Reports | （搜索接口反查）|

## 搜索接口（双参数，按场景选）

==实测发现 LetPub 用两个独立参数==：`searchname` 走名称，`searchissn` 走 ISSN。混用会拿到 0 结果。

**按名称搜**：

```
https://letpub.com.cn/index.php?page=journalapp&view=search&searchname={journal_name}
```

**按 ISSN 搜**（必须用此路径，==不能把 ISSN 塞 searchname==）：

```
https://letpub.com.cn/index.php?page=journalapp&view=search&searchname=&searchissn={issn}
```

返回结果是 server-rendered HTML 列表，每行一个候选 + `journalid` 链接。

==严格匹配==：LetPub 搜索对名称连字符位置敏感——"Angewandte Chemie International Edition" 全名 0 命中，要试缩写或核心关键词。先 ISSN 搜（最稳），fallback 名称模糊匹配。

## 消歧策略

| 场景 | 动作 |
|---|---|
| 输入 ISSN，搜索结果 1 条 | 直取 |
| 输入 ISSN，结果 ≥ 2 条 | 取 ISSN 完全匹配 |
| 输入名称，结果 1 条 | 直取 |
| 输入名称，结果 ≥ 2 条且无 ISSN | **停下来**，把候选列表交回 orchestrator / 用户 |
| 名称匹配字段为空 | 报 `error_log: "letpub search returned 0 hits for {query}"`，return null |

## 反爬观察

- **首页 / 搜索 / 详情**：暂未观察到限频，UA 仅需 `Mozilla/5.0` 即可
- **建议节奏**：≥ 1 s/req，并发 ≤ 5
- **反爬升级信号**：`HTTP 403` / `HTTP 429` / 内容被换成提示页 / DOM 结构突变
- **签名变量**：偶发出现 cookie 检查（`PHPSESSID` 写入），firecrawl 默认会保留

## 镜像域名

LetPub 同时维护两个域：

- `letpub.com.cn`（主，国内 IP 友好）
- `aspb.letpub.com`（也通，海外 IP 友好）

==默认用 `.com.cn`，海外网络抖动时切 `aspb.letpub.com`==。两个域结构一致。
