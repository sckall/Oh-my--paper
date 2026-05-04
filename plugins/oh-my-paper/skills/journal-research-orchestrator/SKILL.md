---
name: journal-research-orchestrator
description: 用于做英文 / SCI 路线 P0 期刊调研全流程编排：用户给研究方向或候选期刊 list，本 skill 调度 6 个探索 adapter（OpenAlex/Crossref/dblp/B!SON/arXiv/Google Scholar）+ LetPub/authority/risk 出决策矩阵（2 主投 + 2 备选 + 1 不建议）。三种场景路由：A 粗糙方向走完整三层；B 已有 ISSN list 跳第一层；C 单期刊靠不靠谱直接转 letpub+predatory。触发关键词：P0 期刊调研 / journal targeting / 投稿编排 / 决策矩阵 / 主投备选 / 选刊全流程 / 期刊推荐。不用于：单期刊单看（那是 letpub-sci-journal-review）、AI 推荐探索（那是 ai-journal-match）、二级权威核验（那是 journal-authority-check）、风险筛查（那是 predatory-risk-check）、中文期刊（那是 journal-research-cn:muchong-cn-journal-review）、P0 之外阶段（如 P1 文献发现）。
---

# journal-research-orchestrator

## 一句话定位

orchestrator = 学术界的「求职总教练 / 职业规划顾问」。
接客户来料（研究方向 / 候选期刊 list）→ 调度英文路线探索、验证、风险 sub-skill → 出**决策矩阵**（2 主投 + 2 备选 + 1 不建议）。

==本 skill 不直接抓数据，只调度==。

## 方法论核心（内联）

- ==先选刊再做实验==——投稿调研应占整个项目工作量的 1/4 到 1/3。期刊决定格式、方向侧重、审稿难度和发表周期。
- 双轨路由：英文 / SCI 路线在本 plugin 内部跑；中文期刊不在本 plugin 内执行，遇到时**只提示**用户跨 plugin 跑 `journal-research-cn:muchong-cn-journal-review`，不硬调用。
- 三层流程：探索 → 验证 → 风险筛查。探索的 trust level 只能当候选生成证据，不能直接进决策矩阵。
- 输出格式固定为决策矩阵（2 主投 + 2 备选 + 1 不建议）+ 数据来源声明，不替用户做"我建议你投 X"的最终判断。
- ==中科院分区双轨==：2026 起官方分区表停更，默认引用 LetPub 新锐分区表，提到 legacy 必加 "(YYYY 年冻结)" 注释。

## 工具优先级（透传给 sub-skill）

orchestrator 自己**不直接调网络工具**。只把宿主信号透传给 sub-skill：

| 宿主 | 透传 tier | sub-skill 行为 |
|---|---|---|
| Claude Code GUI | Tier 1 (Preview) | sub-skill 用 `mcp__Claude_Preview__*` 演示 |
| Codex 桌面 | Tier 1 (in-app browser) | sub-skill 用 in-app browser + element 标注 |
| 无 GUI / batch runtime | Tier 2 (firecrawl) | sub-skill 走 firecrawl 批量 |

## 场景路由（决策树）

```
                  User 来料
                     │
    ┌────────────────┼─────────────────┐
    ▼                ▼                 ▼
场景 A             场景 B             场景 C
粗糙研究方向       已有 ISSN list     单期刊靠不靠谱
"我研究 LLM RAG"  [issn1, issn2,..]  "Sci Rep 能投吗"
    │                │                 │
    ▼                ▼                 ▼
完整三层流程       跳第一层（探索）   直接转
                  进二+三层           letpub + predatory
                                     单条画像
```

## 三层流程（场景 A 完整版）

### 第一层「探索」：候选生成

按学科和偏好路由到 6 个 adapter。默认主源是 `journal-research-en:openalex-explore`，只在生医方向保留 `ai-journal-match` 的 JANE 路径作为高召回专用入口。

| 输入信号 | 主 adapter | 副 adapter / cross-check | 说明 |
|---|---|---|---|
| 生医 / 临床 / 药学 / 生物 | `ai-journal-match` | `openalex-explore` | JANE 召回生医候选，OpenAlex 补跨学科 source |
| 化学 / 材料 / 物理 | `openalex-explore` | `arxiv-preprint-explore`（preprint 明显时） | OpenAlex journal source 聚合为主 |
| 工程 / 电气 / 计算机 | `openalex-explore` | `dblp-cs-explore` 并发 | CS venue 用 dblp 修正 OpenAlex 漏召回 |
| 数学 / 理论 CS / 物理 preprint | `openalex-explore` | `arxiv-preprint-explore` 并发 | 从 arXiv 样本反推正式出版 source |
| 商科 / 经管 / 文社科 | `openalex-explore` | `google-scholar-explore` | Scholar 只做 venue 频次 cross-check |
| 跨学科 / AI for X | `openalex-explore` | `google-scholar-explore` | 先广撒，再用 Scholar 校验具体论文 venue |
| OA 偏好 / Plan-S / DOAJ | `bison-oa-explore` | `openalex-explore --oa-only` | B!SON 输出 OA/Plan-S/APC 字段 |
| 已有 ISSN / DOI | 跳第一层 | `crossref-validator` | 直接进入第二层轻量校验 |

第一层统一返回 `list[CandidateJournal]`（至少 identity + fit_score + evidence）。探索层的 trust level 只能当候选生成证据，不能直接进入最终推荐。

### 第二层「验证」：并发画像

对每个 candidate **并发**调验证 sub-skill。中文期刊口碑证据不在本 plugin 内抓取；需要时提示用户另跑 `journal-research-cn:muchong-cn-journal-review`。

| Sub-skill | 填充字段 | trust_level |
|---|---|---|
| `crossref-validator` | `identity` 的 title / ISSN / publisher / DOI coverage 轻量校验 | crossref-validator |
| `letpub-sci-journal-review` | `authority_metrics` + `cas_legacy` + `cas_letpub` + `community` + `risk_flags` | authoritative / frozen / community / letpub-aggregated |
| `journal-authority-check` | `authority_metrics.{mjl,sjr,citescore,doaj}` | authority-secondary |

==并发约束==：每个 candidate 同时调英文验证 sub-skill 是 OK 的；但同一 sub-skill 对外网络请求 ≥ 1s/req（letpub skill 自身保证），orchestrator 不另外加节流。

### 第三层「风险筛查」

调 `journal-research-en:predatory-risk-check`：

- 输入：所有 candidates 的 ISSN + APC + DOAJ 状态
- 输出：每个 candidate 的 `risk_flags`（list[str]，如 `["predatory_suspected", "abnormal_apc", "not_in_doaj"]`）

被标 `predatory_suspected` 的 candidate ==自动降级到「不建议」组==，不进主投/备选。

### 收敛：决策矩阵

合并三层结果，输出 markdown 决策矩阵 + 锁定建议。

## 决策矩阵 Schema

输出格式（直接交付给用户）：

```markdown
# P0 期刊调研结果

研究方向：<input>
候选池：N 个
调研时间：<ISO>

## 决策矩阵

| 期刊 | 方向匹配度 | 权威指标 (IF/分区) | 审稿速度 | 成本 (APC) | 中文经验 | 风险标签 | 推荐动作 |
|---|---|---|---|---|---|---|---|
| Nature Communications | 0.87 | IF 15.7 / Q1 | 6 周 | USD 6790 | 较多 | — | **主投** |
| Scientific Reports | 0.81 | IF 4.6 / Q2 | 3.9 月 | USD 2290 | 多 | — | 备选 |

## 锁定建议

**主投**（2 篇）
1. Nature Communications — 方向匹配最高、审稿快、IF 高，但 APC 高
2. ...

**备选**（2 篇）
3. Scientific Reports — IF 中等但接收率高，作 fallback
4. ...

**不建议**（1 篇）
5. <Journal X> — 风险标签：abnormal_apc + not_in_doaj，疑似掠夺刊

## 数据来源声明

每列的 data_source（按列）：
- 方向匹配度: ai-match (JANE / Springer / ...)
- 权威指标: letpub-aggregated (origin: JCR/Scopus)
- 审稿速度: community + community-cn
- 成本: letpub-aggregated
- 中文经验: community-cn (muchong)
- 风险标签: risk-aggregated (DOAJ / TCS / letpub warning list)

## CAS 分区说明

中科院文献情报中心**2026 起永久停更**分区表。本报告引用：
- 历史分区：标注 `(2025 年冻结)`
- 当前分区：默认引用 LetPub 新锐期刊分区表（接班）
```

## 共享资产落地：`_shared/journal_identity.py`

==本 skill 是 dataclass 的实际使用方，必须负责落地此文件==。其他 sub-skill 共用。

dataclass 形态（实际跑时由 agent 写出 .py 文件，不预先建空文件）：

```python
@dataclass
class JournalIdentity:
    title: str
    issn: str | None
    eissn: str | None
    publisher: str | None
    official_site: str | None
    submission_site: str | None

@dataclass
class SourceEvidence:
    source: str            # 'letpub-detail' | 'muchong-page' | 'jane-result' | ...
    url: str
    access_level: str      # 'public' | 'login-required' | 'paywalled'
    trust_level: str       # 'authoritative' | 'frozen' | 'community' | 'community-cn' |
                           # 'authority-secondary' | 'letpub-aggregated' | 'risk-aggregated'
    fetched_at: str        # ISO 8601
    raw_snippet_path: str | None
    tool_tier_used: str    # '1a' | '1b' | '2' | '3' | '4'

@dataclass
class CandidateJournal:
    identity: JournalIdentity
    fit_score: float | None              # 第一层 ai-match
    authority_metrics: dict              # 第二层 letpub + authority-check
    cas_legacy: dict | None              # frozen
    cas_letpub: dict | None              # 接班
    review_intel: dict                   # speed / acceptance / cn_excerpts
    speed_intel: dict                    # weeks / months 字段
    cost_intel: dict                     # APC / OA model
    risk_flags: list[str]                # 第三层 predatory
    evidence: list[SourceEvidence]       # 每条字段的追溯
```

## Anti-pattern（不要做）

- ❌ 自己直接调 firecrawl / chrome-devtools 抓 LetPub（让 sub-skill 干）
- ❌ 替用户拍最终决策（"我建议你投 X"）——只出矩阵 + 锁定建议，让用户挑
- ❌ 把 CAS 旧分区当 primary metric（继承 letpub skill 的设计：默认引用新锐分区）
- ❌ 跨场景串货（场景 C 单期刊调研用全流程是浪费）
- ❌ 在矩阵里混合 trust level（站方权威和网友评分并列展示）
- ❌ 调 sub-skill 拿不到数据时伪造 fallback 值（缺什么写 `null` + `error_log`）

## 协作边界（与 sibling skill）

| Skill | 关系 |
|---|---|
| `ai-journal-match` | **下游**：生医第一层调用，传入研究方向，收 JANE candidates |
| `openalex-explore` | **下游**：跨学科主探索 adapter，默认候选源 |
| `crossref-validator` | **下游**：已知 ISSN/DOI 轻量校验 |
| `dblp-cs-explore` | **下游**：CS / 软件工程 / AI venue 专项探索 |
| `bison-oa-explore` | **下游**：OA-only / Plan-S 偏好探索 |
| `arxiv-preprint-explore` | **下游**：preprint 样本反推出版 source |
| `google-scholar-explore` | **下游**：Scholar venue 频次 cross-check |
| `letpub-sci-journal-review` | **下游**：第二层并发调用，每 candidate 一次 |
| `journal-research-cn:muchong-cn-journal-review` | **跨 plugin**：中文期刊口碑补充；本 orchestrator 只提示，不硬调用 |
| `journal-authority-check` | **下游**：第二层并发调用 |
| `predatory-risk-check` | **下游**：第三层串行调用（依赖前面填好的 risk_flags 候补字段）|
| `req-suite:project-spec` | **上游**（可能）：投稿项目搭骨架时调本 skill 出 P0 报告 |

## 触发示例

| 用户输入 | 走哪个场景 |
|---|---|
| "帮我做 P0 期刊调研，我研究 LLM agent RAG" | A（完整三层）|
| "这 5 个 ISSN 帮我对比一下哪个值得投：[2041-1723, 2045-2322, ...]" | B（跳探索）|
| "Scientific Reports 现在能投吗？" | C（单期刊+风险）|
| "Nature Comms 的 APC 多少" | ❌ 不调本 skill，直接 `letpub-sci-journal-review` |

## 本 skill 的 deletion-spec

- **触发删除条件**：探索/验证/风险 sub-skill 中超过半数被废弃 / 替代时；或 Claude Code / Codex 原生支持期刊数据集编排（如官方 multi-source MCP）使本 skill 冗余；或场景路由 A/B/C 三类需求模式发生根本性变化（如学术出版生态转向纯 OA + AI 选刊一体化）。
- **禁用方式**：删除 `plugins/journal-research-en/skills/journal-research-orchestrator/`，bump plugin 版本（minor，因为是主入口移除），更新本仓库 marketplace manifest，并重新安装本地插件。
- **卸载清单**：
  - `plugins/journal-research-en/.claude-plugin/plugin.json`（版本 bump）
  - `plugins/journal-research-en/README.md`（Skills 表 + 三层协作图 + Roadmap）
  - `plugins/journal-research-en/_shared/journal_identity.py`（本 skill 落地的 dataclass —— 若其他 skill 仍引用，需迁移到其他 skill 内联或保留 _shared）
  - `req-suite:project-spec`（如已建立调用关系，需移除引用）
