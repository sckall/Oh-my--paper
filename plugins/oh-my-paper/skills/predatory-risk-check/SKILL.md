---
name: predatory-risk-check
description: 用于英文 / SCI 路线 P0 期刊调研第三层「风险筛查」——输入候选期刊（已被 letpub + authority-check 填好基础字段），输出 risk_flags + verdict (safe / warning / predatory_suspected)。综合 5 类信号：DOAJ 白名单 + Think.Check.Submit. 防坑清单 + Beall's List archive + APC 异常检测（与领域均值对比）+ letpub 预警名单。被 journal-research-orchestrator 第三层调用，predatory_suspected 自动降到「不建议」组。GUI 内 Tier 1 Preview，runtime 主要纯计算，仅 TCS / Beall archive 走 Tier 2 firecrawl。触发关键词：掠夺性期刊 / predatory journal / 水刊 / Beall list / Think Check Submit / TCS / DOAJ 白名单 / APC 异常 / 期刊风险。不用于：全画像（那是 letpub-sci-journal-review）、DOAJ 直查（那是 journal-authority-check）、最终决策（那是 journal-research-orchestrator）、中文期刊水准判定（那是 journal-research-cn:muchong-cn-journal-review）。
---

# predatory-risk-check

## 一句话定位

predatory-risk-check = 学术界的「315 黑榜 / 反传销组织名录」。
输入候选期刊（已被前序 skill 填好字段）→ 输出 risk_flags + verdict。
P0 三层流程的**第三层「风险筛查」**——下游消费方。

## 方法论核心（内联）

P0 期刊调研常见误区（来自坤坤 10 步法）——本 skill 的判定要避免重蹈：

- ==只看 IF 不看审稿周期== → 周期 > 6 月可能延毕
- ==忽略评论区真实反馈== → 踩秒拒 / 多轮改 / 编辑刁难的概率上升（letpub `recent_review_excerpts` 是直接证据）
- ==只选一刊== → 被拒后无备选；orchestrator 才能给 2 主投 + 2 备选
- 仅靠"不在 DOAJ"判水刊 → hybrid OA 期刊本就不在 DOAJ；==仅当 OA 期刊不在 DOAJ 才是 critical signal==

本 skill 输出永远标 `trust_level: "risk-aggregated"`，与官方 IF / 分区指标在决策矩阵中**绝不同列**展示——风险标签是单独一列。

## 工具优先级

| 场景 | Primary | Fallback |
|---|---|---|
| 主流程（信号合成）| **无网络**——纯计算 | — |
| TCS 防坑清单查询 | **Tier 2** firecrawl scrape `thinkchecksubmit.org` | Tier 1 Preview（开发期）|
| Beall archive 查询 | **Tier 2** firecrawl scrape `web.archive.org/Beall` | Tier 3 chrome-devtools（罕见）|

==本 skill 90% 工作是数据合成，不是抓网==——大部分判断基于前序 skill（letpub + authority-check）已填好的字段。只在做 TCS / Beall 反查时才走网络。

## Trust Level

| trust_level | 适用 |
|---|---|
| `risk-aggregated` | 本 skill 的所有 risk_flags 输出 |

==与官方 IF / 分区指标绝不同列展示==——orchestrator 决策矩阵里"风险标签"是单独一列。

## 5 类风险信号

```
                输入：CandidateJournal（letpub + authority-check 已填）
                              │
                              ▼
                    并行计算 5 类信号
                              │
        ┌──────────┬──────────┼──────────┬──────────┐
        ▼          ▼          ▼          ▼          ▼
     DOAJ       TCS         Beall     APC 异常    letpub
     白名单     防坑清单     archive   检测        预警名单
   (消费上游)   (Tier 2)   (Tier 2)  (纯计算)   (消费上游)
        │          │          │          │          │
        └──────────┴──────────┴──────────┴──────────┘
                              ▼
                    risk_flags 合成
                              ▼
                  verdict 三档（safe/warning/predatory_suspected）
```

### 信号 1：DOAJ 白名单（消费 authority-check 输出）

```python
in_doaj = candidate.evidence.get_doaj_check()  # 来自 authority-check
oa_claimed = candidate.cost_intel.get("open_access") in ("Yes", "Hybrid")

if oa_claimed and not in_doaj:
    risk_flags.append("oa_but_not_in_doaj")  # ⚠️ critical signal
elif oa_claimed and in_doaj and candidate.evidence.doaj_seal:
    safety_signals.append("doaj_sealed")     # ✅ 高质量 OA
```

==关键 critical signal==：声称 OA 但不在 DOAJ → 几乎可以判定有问题。

### 信号 2：Think.Check.Submit. (TCS) 防坑清单

TCS 不是黑名单，是**自查清单 + 推荐期刊检索**。本 skill 的用法：

- 抓 `https://thinkchecksubmit.org/journals/` 期刊清单（如有公开列表）
- 检查候选 ISSN 是否在 TCS 推荐之列
- ==不在 TCS 不能反推水刊==（TCS 不全），只在 TCS 出现是 ✅ 信号

```python
in_tcs_recommended = check_tcs_recommended(issn)
if in_tcs_recommended:
    safety_signals.append("tcs_recommended")
```

详见 `references/risk-signals-catalog.md`。

### 信号 3：Beall's List（残留 archive）

Beall's List 已停更（Beall 2017 关博）但 archive 仍存在。==价值降低，但有历史包袱信号==：

```python
on_beall_archive = check_beall_archive(issn_or_publisher)
if on_beall_archive:
    risk_flags.append("beall_legacy_match")  # 历史标记，不是当前判定
```

archive URL：`https://web.archive.org/web/2017*/https://scholarlyoa.com/...`

如 firecrawl 抓不到 archive（archive.org 偶发慢），本信号 fallback 跳过。

### 信号 4：APC 异常检测（纯计算）

==这是本 skill 最有信息量的本地计算==。

输入：letpub 抓到的 APC（GBP / USD / EUR）+ 期刊学科（letpub 的 wos_subjects）。

逻辑：

```python
field_mean_apc, field_std_apc = APC_FIELD_BENCHMARKS[discipline]
# 例如：化学领域均值 ~$2500，std ~$1200
# 多学科领域均值 ~$2000，std ~$1500

z_score = (candidate_apc_usd - field_mean_apc) / field_std_apc

if z_score > 3:
    risk_flags.append("abnormal_apc_high")  # 异常高 APC
elif z_score < -2 and candidate_apc_usd > 0:
    risk_flags.append("abnormal_apc_low")   # 异常低也可疑（hijacked journal）
```

学科 benchmark 数据**不动态抓**，落地为静态文件 `references/apc-field-benchmarks.md`（年度更新即可，非实时）。

### 信号 5：letpub 预警名单（消费 letpub 输出）

letpub-sci-journal-review 已抓 `in_warning_list` + `sci_index_status`：

```python
warning_data = candidate.risk_flags  # letpub 已填
if any(year_data["in_list"] for year_data in warning_data["in_warning_list"].values()):
    risk_flags.append("letpub_warning_list_hit")

if candidate.sci_index_status == "Under Review":
    risk_flags.append("scie_under_review")  # ⚠️ 强信号
elif candidate.sci_index_status == "Discontinued":
    risk_flags.append("scie_discontinued")  # 🔴 critical
```

## Verdict 三档

```python
def compute_verdict(risk_flags, safety_signals):
    critical_flags = {
        "oa_but_not_in_doaj",
        "scie_discontinued",
        "abnormal_apc_high",
    }

    has_critical = any(f in critical_flags for f in risk_flags)

    if has_critical:
        return "predatory_suspected"
    elif len(risk_flags) >= 3:
        return "predatory_suspected"
    elif len(risk_flags) >= 1:
        return "warning"
    else:
        return "safe"
```

==orchestrator 自动把 `predatory_suspected` 的 candidate 降到「不建议」组==。

## 输出 Schema

```python
{
    "issn": "2041-1723",
    "verdict": "safe" | "warning" | "predatory_suspected",
    "risk_score": 0.0-1.0,                    # len(critical_flags) * 0.4 + len(other_flags) * 0.15
    "risk_flags": ["oa_but_not_in_doaj", ...],
    "safety_signals": ["doaj_sealed", "tcs_recommended"],
    "evidence": [
        SourceEvidence(
            source="risk-synthesis",
            url=None,                          # 多数信号是合成，无单一 URL
            access_level="public",
            trust_level="risk-aggregated",
            fetched_at="<ISO>",
            raw_snippet_path=None,
            tool_tier_used="2"                # TCS / Beall 抓时是 2，纯合成时是 "n/a"
        )
    ],
}
```

## Anti-pattern

- ❌ 仅靠"不在 DOAJ"判定水刊（hybrid OA 期刊本就不在 DOAJ）
- ❌ 仅靠"不在 TCS"反推水刊（TCS 不是黑名单，是好刊清单）
- ❌ 直接抓 Beall 当前网站（已关博，archive only）
- ❌ APC 异常检测忽略学科（不同学科 APC 中位数差 5-10 倍）
- ❌ 把 verdict 当最终拒投建议（让用户看到 risk_flags 自己判断）
- ❌ 替 letpub / authority-check 做信号收集（本 skill 是消费方，不重抓）
- ❌ 静默通过 critical signal（OA but not in DOAJ 必须 escalate 到 predatory_suspected）

## 协作边界

| Skill | 关系 |
|---|---|
| `journal-research-orchestrator` | **上游**：第三层调度方 |
| `letpub-sci-journal-review` | **上游**：消费 `in_warning_list` / `sci_index_status` / APC 字段 |
| `journal-authority-check` | **上游**：消费 `in_doaj` / `doaj_seal` 信号 |
| `ai-journal-match` | **远上游**：候选池来源（不直接消费）|
| `journal-research-cn:muchong-cn-journal-review` | **跨 plugin 平行**：中文期刊水刊判定靠 muchong 评论，本 skill 不替代 |

## References

| 文件 | 用途 | 何时读 |
|---|---|---|
| `references/risk-signals-catalog.md` | 5 类信号详细判定 + critical 列表 + TCS/Beall 抓取 | 信号合成时 |
| `references/apc-field-benchmarks.md` | 各学科 APC 均值 / std 静态表（年度刷新）| APC 异常检测时 |

## 本 skill 的 deletion-spec

- **触发删除条件**：DOAJ + TCS + Beall 三大数据源全部停服 / 不可用；或学术圈彻底解决掠夺刊问题（理想状态）；或 Claude/Codex 原生支持期刊风险评估 MCP。
- **禁用方式**：`rm -rf plugins/journal-research-en/skills/predatory-risk-check/` → bump plugin（patch）→ 跑 generate_plugin_marketplaces.py + verify_plugin_distribution.py。
- **卸载清单**：
  - `plugins/journal-research-en/.claude-plugin/plugin.json`（版本 bump）
  - `plugins/journal-research-en/README.md`（Skills 表 + 三层协作图）
  - `plugins/journal-research-en/skills/journal-research-orchestrator/SKILL.md`（第三层调用引用 + verdict 降级逻辑）
  - 上游 skill 不需改（letpub / authority-check 不依赖本 skill 输出）
