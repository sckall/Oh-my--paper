---
name: muchong-cn-journal-review
description: 用于中文期刊 P0 调研第二层「验证」抓取投稿口碑时使用——输入 ISSN（强匹配，主路径）或中文刊名（弱匹配，兜底），返回基本资料 + 虫友提供资料 + 期刊点评列表三个 evidence block，归纳审稿速度 / 录用倾向 / 审稿费 / 版面费 / 编辑流程体验。可由用户在中文路线直接触发，也可由 journal-research-cn:cn-orchestrator 在画像层引用。Runtime 主路径用 curl + iconv 解 GBK（~0.45s/期刊，比 firecrawl 快 10-20×），firecrawl 仅用于批量重试 / 反爬升级。触发关键词：小木虫、muchong、中文期刊点评、虫友评论、审稿周期、版面费、投稿口碑、cn journal review。不用于 SCI 分区检查（那是 journal-research-en:letpub-sci-journal-review）、不用于英文期刊评价（那是 journal-research-en）、不用于最终决策（那是 cn-orchestrator）、不用于通用网页爬虫（仅小木虫期刊点评页）。
---

# muchong-cn-journal-review

## 一句话定位

muchong = 学术界的「脉脉匿名区」。
输入 ISSN → 抓三个 evidence block → 输出 `review_intel.cn_excerpts`（虫友点评摘要 + 审稿速度 / 费用 / 录用倾向）。
P0 三层流程的**第二层验证之一**——和 letpub + authority-check 并发调用。

## P0 方法论（内联）

P0 = 投稿前"先选期刊再定方向"，调研工作量应占整个流程 1/4 到 1/3。中文路线四步：AI 缩范围 → 小木虫核实口碑 → 等级目录确认 → 锁定 2 主投 + 2 备选。本 skill 是第二步「小木虫核实」的实现：抓审稿周期、版面费、投稿人真实反馈，作为 `community-cn` 单列证据进决策矩阵——不与 letpub authoritative 指标合并、不当最终结论。

## 工具优先级

==站点特性允许走 plugin 4-Tier 之下的"站点级捷径"==——小木虫是 server-rendered + GBK + GET 表单 + 无登录 + 无 cookie 依赖，bare curl + iconv 是单期刊查询的最优解（实测验证）。

| 场景 | 工具 | 时间/页 | 备注 |
|---|---|---|---|
| **Runtime 默认（单期刊 / 小批量）** | **curl + `iconv -f GBK -t UTF-8 -c`** | ~0.45s | 站点级捷径，==非 plugin Tier 0==，是站点静态特性允许的 |
| Runtime 大批量（≥ 30 期刊连发）| Tier 2 firecrawl scrape `-f rawHtml` | ~2.4s | firecrawl 自动转码 + IP 轮换 + 重试逻辑 |
| GUI 演示 / 视频镜头 | Tier 1 Preview / Codex in-app browser | 视场景 | 录屏可见点评页，演示用 |
| 兜底 | Tier 3 chrome-devtools | ~15-30s | 仅 JS 渲染 / 验证码 / 登录字段。==新版默认不再走== |

升级判定：

- curl 连续 4xx ≥ 3 / HTML body < 5KB / iconv fallback >5% → 升 firecrawl
- 站点改版回 JS 加载提示 / Cloudflare 拦截 / 需登录字段 → 升 chrome-devtools

==旧版 chrome-devtools 默认路径整个废弃==——属"用 Tier 3 解决静态站点"过度工程。

## Trust Level

| trust_level | 适用 |
|---|---|
| `community-cn` | 本 skill 所有输出（虫友提供资料 + 点评列表 + 归纳结论）|

==决策矩阵里"中文经验"是单独一列，不与 letpub 的 authoritative / authority-secondary 同列展示==。

## URL 协议（实测验证）

入口：`https://muchong.com/bbs/journal_cn.php`

GET 查询字段（==字段名是 `issn` / `tagname` / `name`，不是 `searchissn` / `searchname`==）：

```
journal_cn.php?issn=<ISSN>           # 强匹配，主路径
journal_cn.php?name=<GBK-encoded>    # 弱匹配，兜底
journal_cn.php?tagname=<研究方向>    # 横向同方向比对，不参与单刊查询
```

Detail page：`journal_cn.php?view=detail&jid=<JID>`（JID 从搜索结果的 `view=detail&jid=N` anchor 提取）

## 输入参数协议（ISSN-first）

```yaml
inputs:
  issn:         { type: string, format: "XXXX-XXXX", priority: 1 }   # 强匹配，主路径
  chinese_name: { type: string, priority: 2 }                        # 弱匹配，仅 ISSN 缺失或 0 命中时启用
  tagname:      { type: string, optional: true }                     # 横向比对，不参与单刊查询

behavior:
  - 同时给 issn + chinese_name 时，忽略 chinese_name
  - issn 0 命中时降级到 chinese_name；chinese_name 多命中时返回 candidates 列表给 orchestrator，==不擅自取 head[0]==
  - chinese_name 必须 GBK URL-encode（`urllib.parse.quote(s.encode('gbk'))`）；UTF-8 编码 0 命中且不报错——隐性坑
```

完整 cookbook（curl + iconv + GBK URL-encode 三段管道）见 `references/gbk-decode-playbook.md`。

## 三个 Evidence Block

### 1. 基本资料

期刊名 / 英文名 / 出版周期 / ISSN / CN / 邮发代号 / 主办单位 / 出版地 / 期刊主页网址 / 在线投稿网址 / 数据库收录荣誉 / 复合 IF / 综合 IF

==注意==：复合 IF / 综合 IF 是小木虫站方计算口径，**不等于** JCR / CAS 分区——填入 `review_intel.cn_excerpts.basic` 时标 source=muchong-basic，不混入 letpub 的 authority_metrics。

### 2. 虫友提供资料

偏重研究方向（带计数）/ 投稿录用比例 / 平均审稿周期（月）/ 审稿费 / 版面费

### 3. 期刊点评列表

按 `#1` `#2` `#3` 楼层切分，每楼字段：作者 + uid / 时间戳 / "对我有帮助"票数 / 研究方向 / 投稿周期 / 录用情况 / 点评正文（含投稿时间线）。

==默认抓最新 5-10 条==（`top_n=5..10`），可见少于 5 条时全抓。

==零点评期刊==：detail page 完全没有 `期刊点评列表` 段，==无"暂无点评"占位==。提取逻辑必须 `if "期刊点评列表" not in html: reviews = []`，不能假设标题永远存在。

## 输出 Schema（对齐 orchestrator）

```python
{
    "issn": "1003-3289",
    "jid": 1234,                            # 小木虫内部 id，反向查询用
    "trust_level": "community-cn",
    "review_intel": {
        "cn_excerpts": {
            "basic": {
                "title_cn": "...",
                "title_en": "...",
                "frequency": "月刊",
                "host_org": "...",
                "official_site": "...",
                "submission_site": "...",
                "muchong_composite_if": 0.45,    # 站方口径，不等于 JCR
                "muchong_overall_if": 0.62
            },
            "user_provided": {
                "preferred_topics": [{"topic": "...", "votes": 12}, ...],
                "acceptance_rate": "30%",
                "avg_review_months": 3,
                "review_fee_cny": 200,
                "page_fee_cny": 1500
            },
            "reviews": [
                {
                    "floor": 1, "author": "...", "uid": "...", "ts": "2024-...",
                    "helpful_votes": 5, "topic": "...",
                    "submission_cycle": "...", "outcome": "accepted_after_revision",
                    "body": "..."
                }
            ],
            "review_count_visible": 7,
            "free_text_signals": ["多轮外审", "编辑催稿响应慢", ...]
        }
    },
    "evidence_completeness": "full" | "partial: no_reviews_yet" | "partial: detail_fail",
    "evidence": [
        SourceEvidence(
            source="muchong-search",
            url="https://muchong.com/bbs/journal_cn.php?issn=...",
            access_level="public",
            trust_level="community-cn",
            fetched_at="<ISO>",
            raw_snippet_path="<tmp>/muchong_search.html",
            tool_tier_used="0"          # 站点级 curl，区别于 plugin 1/2/3/4
        ),
        SourceEvidence(
            source="muchong-detail",
            url="https://muchong.com/bbs/journal_cn.php?view=detail&jid=...",
            access_level="public",
            trust_level="community-cn",
            fetched_at="<ISO>",
            raw_snippet_path="<tmp>/muchong_detail.html",
            tool_tier_used="0"
        )
    ]
}
```

==`evidence_completeness` 是新增字段==——让 orchestrator 区分"小木虫收录但无点评"（不算抓取失败）vs"detail 抓取失败"。

## 边缘案例

| 场景 | 处理 |
|---|---|
| ISSN 0 命中（小木虫未收录）| 降级 chinese_name；仍 0 → `evidence_completeness: "partial: not_indexed"` + 返回 empty review_intel |
| 中文名模糊匹配多命中（如 "自动化学报" 命中 2 条含强干扰）| 返回 candidates 列表给 orchestrator，==不自动取 head[0]== |
| 零点评刊（如 jid=2 癌症）| `reviews=[]` + `evidence_completeness: "partial: no_reviews_yet"` |
| UTF-8 URL-encode 中文名 | 0 命中且无报错——必须 GBK 编码再 quote |
| 缺 `User-Agent` header | 部分代理回 200 + 空 body 或 Cloudflare 风控页——==必须带 `Mozilla/5.0`== |
| `curl -I` 返回 `application/octet-stream` 0 body | CDN 配置坑，==不能用 HEAD 探活==，用 GET + body length |
| iconv 撞 GB18030 扩展字符（边缘姓名用字）| 必须加 `-c` flag 静默丢弃非法字节，否则整段管道炸 |

## Anti-pattern

- ❌ 默认走 chrome-devtools 抓 detail page（旧路径，对静态站过度工程）
- ❌ 用 UTF-8 URL-encode 中文名（0 命中 + 无报错的隐性坑）
- ❌ 把小木虫复合 IF / 综合 IF 当 JCR 影响因子（站方计算口径）
- ❌ ISSN 命中后仍用中文名再搜一次（同一 query 放大成 2-3 倍带宽）
- ❌ chinese_name 多命中时擅自取 head[0]（误判）
- ❌ 假定 detail page 一定有"期刊点评列表"段（零点评刊会让提取炸）
- ❌ 输出混入 letpub 的 authority_metrics 字段（trust level 越界）
- ❌ 把虫友评论的"投稿被拒"当 letpub 预警名单（community-cn ≠ letpub-aggregated）

## 协作边界

| Skill | 关系 |
|---|---|
| `journal-research-en:journal-research-orchestrator` | **跨 plugin 上游**：英文路线需要中文口碑时提示用户单独触发 |
| `journal-research-en:letpub-sci-journal-review` | **跨 plugin 平行**：letpub 填 authority_metrics，本 skill 填 review_intel.cn_excerpts，==字段不重叠== |
| `journal-research-en:journal-authority-check` | **跨 plugin 平行**：authority-check 填 SJR/DOAJ/CiteScore，互补 |
| `journal-research-en:ai-journal-match` | **远上游**：英文候选池来源（不直接消费）|
| `journal-research-en:predatory-risk-check` | **跨 plugin 下游消费方**：可能消费本 skill 的"虫友指控水刊"信号合成风险标签 |

## References

| 文件 | 用途 | 何时读 |
|---|---|---|
| `references/gbk-decode-playbook.md` | curl + iconv + GBK URL-encode 三段管道 cookbook + 性能基准 | runtime 抓取时 |
| `references/output-schema-alignment.md` | 输出 schema 字段映射（orchestrator review_intel.cn_excerpts）+ evidence_completeness 三态 | 字段填充前 |

## 本 skill 的 deletion-spec

- **触发删除条件**：小木虫站点关闭 / 改版到要求登录 / 切到 SPA 后 curl 路径完全失效；或学术圈中文期刊评价生态根本性变化（如 CNKI 推出官方点评 + 用户体系替代）；或 plugin 整体被中文期刊调研专用平台 MCP 取代。
- **禁用方式**：`rm -rf plugins/journal-research-cn/skills/muchong-cn-journal-review/` → bump plugin（minor，因为是 6→5 skill 移除）→ 跑 `python3 plugins/scripts/generate_plugin_marketplaces.py` + `verify_plugin_distribution.py`。
- **卸载清单**：
  - `plugins/journal-research-cn/.claude-plugin/plugin.json`（版本 bump + description 去掉 muchong）
  - `plugins/journal-research-cn/README.md`（Skills 表第 4 行 + 三层协作图 verification 段去 muchong）
  - `plugins/journal-research-en/skills/journal-research-orchestrator/SKILL.md`（第二层并发表去 muchong 行 + 协作边界表 + dataclass 注释）
  - `plugins/journal-research-en/skills/ai-journal-match/SKILL.md`（"中文期刊不在本 skill"段引用）
  - `plugins/journal-research-en/skills/predatory-risk-check/SKILL.md`（协作边界表"平行：muchong"行）
