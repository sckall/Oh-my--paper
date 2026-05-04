---
name: ai-journal-match
description: 用于英文 / SCI 路线 P0 期刊调研第一层「探索」——输入研究方向/题目/摘要，输出 5-10 个候选期刊（含 fit_score + ISSN）。Adapter 模式：生医走 JANE（v0.1 实装），化学/材料/物理走 Springer/Elsevier（TODO），工程/CS 走 IEEE PR（TODO），商科/文社科 fallback 提示 letpub 手动筛。被 journal-research-orchestrator 第一层调用。触发关键词：JANE / AI 选刊 / AI journal recommender / 题目摘要选刊 / Boss 直聘式选刊 / 候选期刊池 / 探索期刊。不用于：全画像验证（那是 letpub-sci-journal-review）、最终决策（那是 journal-research-orchestrator）、中文期刊推荐（那是 journal-research-cn:muchong-cn-journal-review）、跨学科主源探索（那是 openalex-explore）。
---

# ai-journal-match

## 一句话定位

ai-journal-match = 学术界的「Boss 直聘 AI 智能推荐」。
输入研究方向 / 题目 / 摘要 → 5-10 个候选期刊（含 fit_score + ISSN）。
P0 三层流程的**第一层「探索」**。

## 方法论核心（内联）

- ==AI 推荐结果必须二次核实==——AI 训练数据可能滞后或脑补 IF / 分区数字。本 skill 输出永远标 `trust_level: "ai-推断"`，由 orchestrator 自动调 letpub + authority-check 二次验证。
- AI 缩范围只是**第一层探索**——生成候选池；不直接进入决策矩阵。
- 只有 `fit_score` 达不到判定门槛——`< 0.5` 标 `weak_match` warning，让 orchestrator 决定取舍。

## 工具优先级

| 场景 | Primary | Fallback |
|---|---|---|
| GUI 内演示（视频镜头）| **Tier 1** Claude Code Preview / Codex in-app browser | Tier 2 firecrawl |
| Runtime 调度（orchestrator）| **Tier 2** firecrawl POST | Tier 3 chrome-devtools（仅 SPA adapter）|

## Trust Level 新增

继承 letpub 的 trust 分层，本 skill 引入新一档：

| trust_level | 定义 | 决策权重 |
|---|---|---|
| `ai-推断` | AI 算法基于文献相似度的推荐 | ==**仅供探索**——不能当决策依据== |

输出里**必须**标 `trust_level: "ai-推断"`。orchestrator 看到这个标记会自动调 letpub + authority-check 二次验证。

## Adapter 模式：学科路由决策树

```
            User 输入（research_direction / abstract）
                       │
                       ▼
              检测语言 / 关键词 / 学科
                       │
        ┌──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
     生医/生物       化学/材料      工程/电气     商科/文社科
     PubMed范畴      物理            计算机
        │              │              │              │
     ✅ JANE        ⏳ Springer    ⏳ IEEE PR        ❌ Fallback
     (v0.1 实装)    Suggester /    (TODO)          空 list +
                   Elsevier JF    防护较强         提示 letpub 手筛
                   (TODO，SPA)    需 Tier 3-4
                       │
                  跨学科 / 多学科
                       │
                  默认 JANE（PubMed 覆盖最广）
                  下轮加并发其他 adapter 后取并集
```

## JANE Adapter（v0.1 实装）

### URL 模式

```
https://jane.biosemantics.org/suggestions.php?findJournals=&text={url-encoded title+abstract}
```

`text` 参数支持 URL 编码后的题目 + 摘要（5-200 字典型）。多段连接用空格。

### 抓取路径

Tier 2 firecrawl：

```bash
firecrawl scrape \
  'https://jane.biosemantics.org/suggestions.php?findJournals=&text=YOUR_QUERY' \
  --formats markdown,html \
  --only-main-content true
```

curl 兜底：

```bash
curl -L -A 'Mozilla/5.0' \
  "https://jane.biosemantics.org/suggestions.php?findJournals=&text=$(python3 -c 'import urllib.parse;print(urllib.parse.quote("YOUR QUERY"))')"
```

==无登录、无 captcha、反爬未观察到==。

### 输出 HTML 结构

JANE 返回 server-rendered 表格，每行一个候选：

| 列 | 字段 | 说明 |
|---|---|---|
| 期刊名 | str | 全名 |
| confidence | float 0-1 | JANE 算法相似度 |
| 标签 | list[str] | "Medline-indexed" / "PMC" / "OA" / "High-quality OA" |
| 期刊主页 URL | str | 用于 ISSN 反查 |

==ISSN 不在 JANE 直接输出==——本 skill 输出 identity 时 ISSN 字段留 None，由 orchestrator 调 letpub 反查。

详见 `references/jane-adapter-cheatsheet.md`。

## 其他 Adapter（v0.1 留 stub，下轮迭代）

| Adapter | 状态 | 待做 |
|---|---|---|
| Springer Journal Suggester | ⏳ TODO | SPA + JS 表单提交，需 Tier 3 chrome-devtools |
| Elsevier JournalFinder | ⏳ TODO | 反爬强（直 403），需真实 Chrome + UA + cookie |
| Wiley Journal Finder | ⏳ TODO | 同上，结果偏 Wiley 内部期刊 |
| IEEE Publication Recommender | ⏳ TODO | 防护较强，可能需 computer-use 兜底 |

调度上述 adapter 时本版本返回：

```python
{"adapter": "springer", "status": "not_implemented",
 "message": "v0.1 仅支持 JANE。其他 adapter 下轮迭代。"}
```

## Fallback：商科 / 文社科 / 中文期刊

JANE 是 PubMed 语料，商科/管理/文社科召回率极低。命中此场景时：

```python
{
    "candidates": [],
    "fallback_reason": "商科/文社科/管理领域无 AI 选刊器，请用 letpub 手动筛或 ABS 目录",
    "trust_level": "ai-推断",
    "tool_tier_used": "n/a"
}
```

中文期刊推荐**不属于本 skill** —— 提示用户改用 `journal-research-cn:muchong-cn-journal-review` 或 PLAN-3 后续中文探索 skill。

## 输出 Schema

返回 list[CandidateJournal]，本 skill 只填 identity + fit_score：

```python
[
    CandidateJournal(
        identity=JournalIdentity(
            title="Journal of the International AIDS Society",
            issn=None,             # JANE 不直接输出，由 orchestrator 调 letpub 反查
            eissn=None,
            publisher=None,
            official_site="https://...",
            submission_site=None,
        ),
        fit_score=0.87,            # JANE confidence
        authority_metrics={},       # 留空，由 letpub 后续填
        cas_legacy=None,
        cas_letpub=None,
        review_intel={},
        speed_intel={},
        cost_intel={},
        risk_flags=[],
        evidence=[
            SourceEvidence(
                source="jane-result",
                url="https://jane.biosemantics.org/suggestions.php?...",
                access_level="public",
                trust_level="ai-推断",
                fetched_at="<ISO>",
                raw_snippet_path="./cache/jane-<query-hash>.html",
                tool_tier_used="2",
            )
        ],
    ),
    ...
]
```

## Anti-pattern

- ❌ 把 fit_score 当决策依据（必须二次验证；orchestrator 看到 `trust_level=ai-推断` 自动会做）
- ❌ fit_score < 0.5 还强行返回（标 `weak_match` warning，让 orchestrator 决定是否丢弃）
- ❌ 商科/文社科硬塞 JANE（语料不匹配 → 走 fallback）
- ❌ 中文期刊用本 skill（→ `journal-research-cn:muchong-cn-journal-review` / PLAN-3 中文探索 skill）
- ❌ 静默丢失 fit_score（缺则 None + error_log）
- ❌ v0.1 强行接 SPA adapter（Springer/Elsevier 留 TODO，认真做需要 Tier 3 + 字段抽取实测）

## 协作边界

| Skill | 关系 |
|---|---|
| `journal-research-orchestrator` | **上游**：第一层调度方 |
| `letpub-sci-journal-review` | **下游**：本 skill 输出由 letpub 二次验证（含 ISSN 反查）|
| `journal-authority-check` | **下游**：权威源核验（MJL/SJR/CiteScore/DOAJ）|
| `predatory-risk-check` | **下游**：可能含掠夺刊，由 risk-check 排除 |
| `journal-research-cn:muchong-cn-journal-review` | **跨 plugin 平行**（中文期刊不在本 skill 范围）|

## References

| 文件 | 用途 | 何时读 |
|---|---|---|
| `references/jane-adapter-cheatsheet.md` | JANE URL + 字段抽取 + 边缘案例 | 跑 JANE 时 |
| `references/discipline-routing-playbook.md` | 学科 → adapter 路由决策树 + 关键词触发器 | 路由不确定时 |

## 本 skill 的 deletion-spec

- **触发删除条件**：JANE 站停服 / 被替代；其他 4 个 adapter（Springer/Elsevier/Wiley/IEEE）全部接入后本 skill 升级到独立 plugin（v1.0+）；或 Claude/Codex 原生 AI 选刊集成（如官方 MCP）使本 skill 冗余。
- **禁用方式**：`rm -rf plugins/journal-research-en/skills/ai-journal-match/` → bump plugin（patch）→ 跑 `python3 plugins/scripts/generate_plugin_marketplaces.py` + `verify_plugin_distribution.py`。
- **卸载清单**：
  - `plugins/journal-research-en/.claude-plugin/plugin.json`（版本 bump）
  - `plugins/journal-research-en/README.md`（Skills 表 + 三层协作图 + Roadmap）
  - `plugins/journal-research-en/skills/journal-research-orchestrator/SKILL.md`（第一层调用引用）
  - `plugins/journal-research-en/_shared/journal_identity.py`（CandidateJournal dataclass 仍由其他 skill 复用，本 skill 拆除不删 dataclass）
