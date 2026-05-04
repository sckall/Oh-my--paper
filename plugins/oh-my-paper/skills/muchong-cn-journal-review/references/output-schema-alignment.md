# 输出 Schema 对齐（orchestrator review_intel.cn_excerpts）

本 skill 的输出是 orchestrator 第二层并发结果之一，==字段必须对齐 CandidateJournal.review_intel.cn_excerpts 的 schema==，不能扩展或重命名。

## 字段映射总表

| 输出字段 | orchestrator 接收位置 | trust_level | 必填 |
|---|---|---|:---:|
| `review_intel.cn_excerpts.basic` | candidate.review_intel.cn_excerpts.basic | community-cn | Y |
| `review_intel.cn_excerpts.user_provided` | 同上 user_provided | community-cn | N（部分刊缺）|
| `review_intel.cn_excerpts.reviews` | 同上 reviews（list[dict]） | community-cn | N（零点评刊为空）|
| `review_intel.cn_excerpts.review_count_visible` | int | — | Y |
| `review_intel.cn_excerpts.free_text_signals` | list[str] 归纳信号 | community-cn | N |
| `evidence_completeness` | candidate.evidence_completeness（覆盖式） | — | Y |
| `evidence` | candidate.evidence（append 模式）| — | Y |

==`authority_metrics` / `cas_legacy` / `cas_letpub` / `risk_flags` 这些字段不归本 skill 填==——letpub / authority-check / predatory-risk-check 各自负责。本 skill 越界写这些字段会被 orchestrator 拒收。

## review_intel.cn_excerpts 详细 schema

### basic（基本资料块）

```python
{
    "title_cn": str,                # 期刊名（中）
    "title_en": str | None,         # 英文名
    "frequency": str,               # 出版周期（月刊/双月刊/季刊）
    "issn_print": str | None,       # 印刷 ISSN
    "issn_online": str | None,      # CN 号或电子 ISSN
    "host_org": str | None,         # 主办单位
    "publisher_loc": str | None,    # 出版地
    "official_site": str | None,    # 期刊主页
    "submission_site": str | None,  # 在线投稿网址
    "indexed_in": list[str],        # 数据库收录荣誉（CSCD / EI / 北大核心 等）
    "muchong_composite_if": float | None,   # 站方复合 IF
    "muchong_overall_if": float | None      # 站方综合 IF
}
```

==重要==：`muchong_composite_if` / `muchong_overall_if` 是站方计算口径，**不等于** JCR 影响因子，==决策矩阵呈现时必须明确标注 source=muchong-basic==，不能放在 letpub 的 authority_metrics 列。

### user_provided（虫友提供资料块）

```python
{
    "preferred_topics": [
        {"topic": str, "votes": int}     # 投票数
    ],
    "acceptance_rate": str | None,        # 如 "30%"，部分刊填"未知"
    "avg_review_months": float | None,    # 平均审稿周期（月）
    "review_fee_cny": int | None,         # 审稿费（元）
    "page_fee_cny": int | None            # 版面费（元）
}
```

字段缺失时填 `None`，不填 0 / 空字符串——避免下游误判"免审稿费"。

### reviews（期刊点评列表块）

```python
[
    {
        "floor": int,                  # 楼层号 #1 #2 #3
        "author": str,                 # 用户名
        "uid": str | None,             # 小木虫 uid
        "ts": str,                     # 时间戳（ISO 或站方原文）
        "helpful_votes": int,          # "对我有帮助"票数
        "topic": str | None,           # 研究方向
        "submission_cycle": str | None,    # 投稿周期描述
        "outcome": Literal["accepted", "accepted_after_revision", "rejected", "withdrawn", "unknown"],
        "body": str                    # 点评正文（含投稿时间线）
    }
]
```

==默认 top_n=5..10==（按楼层倒序，最新优先）。可见少于 5 条全抓。

### free_text_signals

归纳层信号——从 reviews 的 body 文本里提取的高频关键词，用 list[str]：

```python
[
    "多轮外审",
    "编辑催稿响应慢",
    "对学生稿件友好",
    "审稿严格",
    "版面费偏高",
    "需要催稿",
    "拒审或久拖"
]
```

==不要原样复制评论文本==——free_text_signals 是归纳层，让 orchestrator 决策矩阵的"中文经验"列只读这个 field。

## evidence_completeness 三态

```python
Literal[
    "full",                          # 三段全抓 + 至少 1 条点评
    "partial: no_reviews_yet",       # 收录但零点评（如新刊 / 冷门刊）
    "partial: not_indexed",          # 小木虫未收录此 ISSN
    "partial: detail_fail",          # 抓取失败（HTTP 错误 / iconv 异常 / parsing fail）
    "partial: ambiguous_match"       # 中文名多命中，需用户消歧
]
```

orchestrator 读这个字段决定决策矩阵该列填什么：

- `full` → 正常填 cn_excerpts
- `partial: no_reviews_yet` → 填 basic + user_provided，reviews 留空，==不算抓取失败==
- `partial: not_indexed` → 该列填 "—"，不参与排序
- `partial: detail_fail` → 该列填 "抓取失败"，标 error_log
- `partial: ambiguous_match` → 该列填 "需消歧"，附 candidates 列表

## SourceEvidence 填法

每次 HTTP 请求填一条 SourceEvidence。三段管道对应 3 条 evidence：

```python
SourceEvidence(
    source="muchong-search" | "muchong-detail" | "muchong-byname",
    url="https://muchong.com/bbs/journal_cn.php?...",
    access_level="public",          # 全公开匿名可见
    trust_level="community-cn",
    fetched_at="<ISO 8601>",
    raw_snippet_path="/tmp/muchong_*.html",   # 实测路径
    tool_tier_used="0"              # 站点级 curl，区别于 plugin Tier 1/2/3/4
)
```

==`tool_tier_used="0"` 是本 skill 独有的标记==，因为站点静态特性允许走 plugin 4-Tier 之下的捷径。其他 skill 用 1/2/3/4。

## Anti-pattern

- ❌ 把 `muchong_composite_if` 当 JCR IF 填进 `authority_metrics`（trust level 越界）
- ❌ 把虫友评论的"投稿被拒次数"合成 risk_flags（→ predatory-risk-check 的事）
- ❌ 把 reviews 的原文长篇幅塞进 `free_text_signals`（应是归纳关键词）
- ❌ `acceptance_rate` 填 "未知" 字符串（应填 None）
- ❌ `evidence_completeness` 填 "full" 但 reviews 为空（→ 应填 "partial: no_reviews_yet"）
- ❌ 中文名多命中时擅自取 head[0]（→ 填 "partial: ambiguous_match" + candidates 列表）
