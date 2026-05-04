# GBK 解码 Cookbook

小木虫是 `text/html; charset=gbk` 站点。curl 直抓必须 iconv，中文名 query 必须 GBK URL-encode。

==本 cookbook 三段管道实测验证==（subagent 报告 2026-04-27，3 期刊各 3 轮，curl+iconv 0.45s ± 0.02s）。

## 三段管道

### Pipeline 1：ISSN → 搜索结果（主路径）

```bash
ISSN="0254-4156"
curl -s -L -A 'Mozilla/5.0' \
  "https://muchong.com/bbs/journal_cn.php?issn=${ISSN}" \
  | iconv -f GBK -t UTF-8 -c \
  > /tmp/muchong_search.html

# 提 jid（可能 0 / 1 / N 条；正则只抓 detail link 防 hot/new 视图链接干扰）
JID=$(grep -oE 'view=detail&jid=[0-9]+' /tmp/muchong_search.html \
        | head -1 | grep -oE '[0-9]+')
```

==判定 0 命中==：`grep -oE 'view=detail&jid=[0-9]+' /tmp/muchong_search.html | wc -l == 0`。站点不返回 "未找到" 文案，必须靠 jid 链接数判定。

### Pipeline 2：jid → detail page

```bash
curl -s -L -A 'Mozilla/5.0' \
  "https://muchong.com/bbs/journal_cn.php?view=detail&jid=${JID}" \
  | iconv -f GBK -t UTF-8 -c \
  > /tmp/muchong_detail.html
```

字段抽取锚点：

```
<h2 class="xmc_title xmc_blue">基本资料</h2>          → 基本资料块
<h2 class="xmc_title xmc_blue">虫友提供资料（X 人参与）</h2>  → 虫友提供资料块
<h2 class="xmc_title xmc_blue">期刊点评列表</h2>      → 期刊点评列表块（==零点评刊缺整段==）
```

楼层切分：`#1` `#2` `#3`（HTML 里通常是 `<div class="xmc_floor"><h3>#N</h3>...`）。

### Pipeline 3：中文名 → 搜索结果（兜底）

==关键==：name 参数必须先 GBK 编码，再 URL-encode。UTF-8 编码 0 命中且无报错——隐性坑。

```bash
# Python 单行：GBK encode → URL quote
NAME_GBK_ENC=$(python3 -c \
  "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1].encode('gbk')))" \
  "电力系统自动化")

curl -s -L -A 'Mozilla/5.0' \
  "https://muchong.com/bbs/journal_cn.php?name=${NAME_GBK_ENC}" \
  | iconv -f GBK -t UTF-8 -c \
  > /tmp/muchong_byname.html
```

中文名搜索是模糊匹配，常多命中——必须返回 candidates 列表给上游，==不擅自取 head[0]==：

```bash
grep -oE 'view=detail&jid=[0-9]+' /tmp/muchong_byname.html | sort -u
# 实测："自动化学报" 召回 2 条（含 "电力系统及其自动化学报"）
# 实测："计算机应用" 召回 4 条（含 3 条强干扰）
```

## 关键 flag 解释

- `iconv -c`：静默丢弃非法字节。==必须加==——避免 GB18030 扩展字符（边缘姓名用字）让整段管道炸
- `curl -A 'Mozilla/5.0'`：==必须带==——缺 UA 时部分代理回 200 + 空 body 或 Cloudflare 风控页
- `curl -L`：跟 302 重定向。HTTP 入口会跳 HTTPS
- `curl -s`：silent 模式，避免 progress bar 污染管道

## 性能基准

| 路径 | 时间/期刊 | 用途 |
|---|---:|---|
| **curl + iconv（本 cookbook）** | **~0.45s** | 默认主路径 |
| firecrawl scrape `-f rawHtml` | ~2.4s | 批量重试 / 反爬升级 |
| firecrawl scrape `-f markdown` | ~9.0s | ==不推荐==（表格被压成单行 + 噪音重）|
| chrome-devtools（旧路径）| ~15-30s | 仅 JS / 验证码 / 登录态兜底 |

curl 一发请求 ~0.45s 端到端（搜索 + detail 共 2 次 HTTP）。批量 10 期刊 ~5s，30 期刊 ~15s。

==firecrawl 自动转码==（不需要手 iconv），但慢 5-20×。

## HEAD 请求异常

```bash
curl -I https://muchong.com/bbs/journal_cn.php
# 返回 application/octet-stream + 0 body（CDN 配置坑）
```

==不能用 HEAD 探活==——用 GET + body length 判定（< 5KB 视为异常）。

## 常见错误模式

| 现象 | 原因 | 修复 |
|---|---|---|
| 中文显示乱码（`å¤§å­¦å­¦æŠ¥`）| 没跑 iconv | 加 `\| iconv -f GBK -t UTF-8 -c` |
| 中文名搜索 0 命中 | UTF-8 URL-encode | 改 GBK encode 再 quote（Pipeline 3）|
| iconv 报 illegal input sequence | 撞 GB18030 扩展字符 | 加 `-c` flag 静默丢 |
| HTTP 200 + empty body | 缺 UA header | 加 `-A 'Mozilla/5.0'` |
| 多 jid 但只取一个 | head[0] 误判 | grep + sort -u 取全集，返回 candidates |
| HEAD 返回 octet-stream | CDN 配置 | 改用 GET + body length |
