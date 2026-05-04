---
name: letpub-sci-journal-review
description: 用于英文 / SCI 路线已有候选期刊名或 ISSN 时，从 LetPub 抓一站全画像（IF / WOS 分区 / 新锐期刊分区 / CiteScore / SJR / 审稿 / APC / 录用比例 / 用户评论 / 预警名单）。被 journal-research-orchestrator 编排批量调用，也可单条直用。GUI 内默认 Tier 1（Claude Code Preview / Codex in-app browser），runtime 批量用 Tier 2 firecrawl，反爬升级 Tier 3 chrome-devtools。触发关键词：LetPub / 看准网式期刊画像 / 期刊全画像 / IF 分区审稿 APC / 中科院分区 / WOS 分区 / 新锐期刊分区 / 期刊预警名单。不用于：AI 选刊（那是 ai-journal-match）、中文众包评论（那是 journal-research-cn:muchong-cn-journal-review）、掠夺刊判定（那是 predatory-risk-check）、二级权威核验（那是 journal-authority-check）、最终决策（那是 journal-research-orchestrator）。
---

# letpub-sci-journal-review

## 一句话定位

LetPub = 学术界的「看准网 / 脉脉公司主页」。
输入期刊名或 ISSN → 一页全画像（IF / 分区 / 审稿 / APC / 评论 / 预警）。
P0 期刊调研「验证层」的主力 skill。

## 方法论核心（内联）

LetPub 是 SCI 路线第 2 步「核实」的主力。最低必抓字段集（来自坤坤 10 步法）：

- ==JCR 分区 + 中科院分区==（双分区——CAS 旧 frozen + LetPub 新锐双轨；2026 起中科院永久停更，本 skill 默认引用新锐分区）
- ==平均审稿速度==（2-6 个月正常，超 6 个月影响毕业节点）
- ==录用率==（< 20% 难度高）
- ==在线出版周期==（影响毕业时间节点）
- ==评论区==（审稿人是否专业、有没有秒拒、改了几轮——`recent_review_excerpts` 最多 5 条）
- ==预警名单==（`in_warning_list` + `sci_index_status`，下游 predatory-risk-check 直接消费）

==永远不要自己计算 IF / 编 SJR==——只转载 LetPub 站方数值，每个 metric 标 `source: "LetPub-aggregated (origin: JCR)"`。

## 工具优先级声明（Tier）

按 plugin 级 `journal-research-en/README.md` 的 Tool priority 模型：

| 场景 | Primary tier | 工具 | Fallback |
|---|---|---|---|
| GUI 内开发 / 演示 / 单条新期刊打样 | **Tier 1** | curl（letpub.com.cn 被 WebFetch 拦截，必须用 curl） | Tier 2 firecrawl |
| Runtime 批量（orchestrator 调度查 ≥ 3 个候选） | **Tier 2** | firecrawl scrape | Tier 3 chrome-devtools |
| LetPub 限频 / 反爬升级 | **Tier 3** | chrome-devtools / Claude in Chrome MCP | — |

不许跳到 Tier 4 computer-use——LetPub 无强反爬，跳层是过度反应。

## 工作流决策树

```
        User 来料（ISSN / 期刊名 / 候选 list）
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
    单条画像                  批量 N 条
    （视频演示 / 探索）        （orchestrator 调度）
        │                         │
        ▼                         ▼
   默认 Tier 1                默认 Tier 2 firecrawl
   GUI pane 内截图 + eval     ≥ 1 s/req，并发上限 5
        │                         │
        └─────────┬───────────────┘
                  ▼
            Step 1-5 串行
```

## Step 1 — ISSN / 期刊名 → letpub_id 解析

LetPub 用内部 `journalid` 寻址。详情页 URL 模式：

```
https://letpub.com.cn/index.php?page=journalapp&view=detail&journalid={id}
```

只有期刊名或 ISSN 时，先查搜索页：

```
https://letpub.com.cn/index.php?page=journalapp&view=search&searchname={name|issn}
```

从搜索结果列表里抽 `journalid`（每条期刊一个 link）。

==消歧规则==：
- 搜索结果 = 1 → 直取
- 搜索结果 ≥ 2 + 提供了 ISSN → 取 ISSN 完全匹配项
- 搜索结果 ≥ 2 + 仅有名称且歧义 → 停下，把候选列表交回 orchestrator 或用户决策。**不要瞎猜**。

==缓存优先==：先查 `_shared/showjcr_offline_db/` 离线 ISSN→letpub_id 映射（未来由 orchestrator 落地）；命中则跳过搜索请求。

==网络请求规则==：**禁止使用 WebFetch 工具访问 letpub.com.cn**——该域名会被 Claude Code 安全验证拦截，100% 失败。**必须使用下方 Python 脚本发起请求，不使用 curl 或 WebFetch。**

## Runtime（默认方式 — Python 脚本）

```bash
# 搜索期刊（返回匹配列表）
python3 plugins/oh-my-paper/skills/letpub-sci-journal-review/scripts/letpub_profile.py "Nature" --search-only

# 抓取详情页（输入期刊名自动搜索 journalid）
python3 plugins/oh-my-paper/skills/letpub-sci-journal-review/scripts/letpub_profile.py "Nature"

# 直接用 journalid 抓取（跳过搜索）
python3 plugins/oh-my-paper/skills/letpub-sci-journal-review/scripts/letpub_profile.py --id 6078

# 输出原始 HTML（调试用）
python3 plugins/oh-my-paper/skills/letpub-sci-journal-review/scripts/letpub_profile.py --id 6078 --raw

# 保存到文件
python3 plugins/oh-my-paper/skills/letpub-sci-journal-review/scripts/letpub_profile.py --id 6078 -o result.json
```

脚本使用 `urllib.request`（Python 标准库，零依赖），自动处理 URL 编码和中文解码。

## Step 2 — 详情页抓取

URL 套上 `journalid` 后请求。按 Tier 选工具：

### Tier 1（默认，推荐）

==使用上方 Runtime 段的 Python 脚本。禁止使用 WebFetch 或 curl。==

### Tier 2（runtime 批量）

firecrawl：

```bash
firecrawl scrape \
  'https://letpub.com.cn/index.php?page=journalapp&view=detail&journalid={id}' \
  --formats markdown,json \
  --only-main-content true
```

或 curl + 自然 HTML：

```bash
curl -A 'Mozilla/5.0' \
  'https://letpub.com.cn/index.php?page=journalapp&view=detail&journalid={id}'
```

==每条 ≥ 1 s 间隔，并发上限 5==。

### Tier 3（反爬升级）

Tier 2 拿到 403 / 5xx / 内容被换 / 页面结构突变 → 升级到 chrome-devtools 真实浏览器，UA + cookie 复用。

==不许静默重试 firecrawl==——必须换层并在 evidence 里标记 `tool_tier_used: 3`。

## Step 3 — 字段抽取与可信度分层

==输出必须给每个字段标 `trust_level`==。两类绝对不能混展示。

### 3.1 站方权威层（`trust=authoritative`，LetPub 转载官方）

| 字段 | 类型 | 说明 |
|---|---|---|
| `journal_name` | str | 期刊全名 |
| `issn` / `eissn` | str | （eissn 可空）|
| `impact_factor_2024` | float | 最新 IF |
| `impact_factor_5yr` | float | 5-year IF |
| `jci` | float | JCI 指标 |
| `citescore` | float | CiteScore（最新年份）|
| `sjr` | float | SJR |
| `snip` | float | SNIP |
| `h_index` | int | h-index |
| `wos_quartile` | str | Q1 / Q2 / Q3 / Q4 |
| `wos_subjects` | list[dict] | `[{category, indexed_by(SCIE/SSCI/...), quartile, rank}]` |
| `open_access` | str | "Yes" / "No" / "Hybrid" |
| `apc` | dict | `{GBP: float?, USD: float?, EUR: float?}` |
| `publication_freq` | str | Monthly / Bimonthly / ... |
| `year_first_pub` | int | 创刊年 |
| `articles_per_year` | int | 年文章数 |
| `gold_oa_ratio` | float | 0.0-1.0 |
| `official_site` / `submission_site` | url | |

### 3.2 CAS 分区双轨（关键设计）

==2026 起中科院文献情报中心永久停更分区表==。LetPub「新锐期刊分区表」是事实接班人。

==实测发现==：页面上**不出现"中科院"三字**。两个 key 文本是：

- 旧版：`期刊分区表（YYYY 年 X 月升级版）` —— 多版本可能并存（如 2025 + 2023）
- 接班：`《新锐期刊分区表》（YYYY 年 X 月发布）`

输出**必须双字段**：

| 字段 | trust_level | 说明 |
|---|---|---|
| `cas_partition_legacy` | `frozen` | `list[dict]`，每条 `{version, frozen_year, big_category, small_category, top_journal, review_journal}` |
| `cas_partition_letpub` | `letpub-aggregated` | dict，含 release 月份 + 同上字段 |

==默认引用规则==：用户问"中科院分区"时，默认引用 letpub 新锐分区；提到 legacy 必加 "(YYYY 年冻结)" 注释。

==Firecrawl markdown 副作用警告==：详情页的多列分区表会被 markdown 拍扁（"综合性期刊 3区1区4区"），分不清列归属。批量抓时建议 `--formats markdown,html` 双开，分区字段从 html 解析。详见 `references/field-extraction-schema.md` 的 "Firecrawl markdown 副作用" 段。

### 3.3 用户众包层（`trust=community`）

| 字段 | 说明 |
|---|---|
| `review_speed_user_months` | float（"网友分享平均 X 个月"）|
| `acceptance_rate_user` | float 0.0-1.0 |
| `letpub_score` | dict `{overall, reputation, impact, speed}` 0-10 |
| `letpub_score_voters` | int |
| `user_review_count` | int |
| `recent_review_excerpts` | list[dict] `[{date, research_dir, cycle_months, decision, raw}]`，最多 5 条 |

### 3.4 预警 / 风险层（`trust=letpub-aggregated`）

| 字段 | 说明 |
|---|---|
| `in_warning_list` | dict `{<year>: {in_list: bool, reason: str \| None}}` —— ==实测有 reason 字符串==（如 "Under Review"），非简单 bool |
| `sci_index_status` | str —— 当前 SCIE 索引状态（"Active" / "Under Review" / "Discontinued"），独立于年份矩阵 |
| `warning_reasons_aggregated` | list[str]（去重后的所有 reason，如 `["self_cite_high", "Under Review"]`）|

## Step 4 — Metadata 注解（CAS 停更 + 来源追溯）

输出 JSON 顶层固定 metadata：

```json
{
  "metadata": {
    "fetched_at": "<ISO 8601>",
    "tool_tier_used": "1a | 1b | 2 | 3",
    "source_url": "https://letpub.com.cn/...",
    "letpub_id": 8411,
    "cas_legacy_status": "frozen since 2026",
    "cas_replacement_source": "LetPub 新锐期刊分区表",
    "skill_version": "<plugin version>"
  }
}
```

==永远不要自己计算 JIF==——只转载 LetPub 提供的数值，每个 metric 个体保留 `source: "LetPub-aggregated (origin: JCR)"` 类标注。

## Step 5 — 输出 schema

返回结构（伪 dataclass，落地由 `_shared/journal_identity.py` 完成，本 skill 现阶段先内联输出）：

```python
@dataclass
class LetPubProfile:
    metadata: dict                  # Step 4 metadata
    identity: dict                  # name / issn / eissn / publisher / sites
    authoritative: dict             # 3.1 字段（trust=authoritative）
    cas_legacy: dict | None         # 3.2 frozen 值（trust=frozen）
    cas_letpub: dict | None         # 3.2 新锐分区（trust=letpub-aggregated）
    community: dict                 # 3.3（trust=community）
    risk: dict                      # 3.4（trust=letpub-aggregated）
    raw_snippet_path: str | None    # 抓到的 markdown / HTML 片段落盘路径
    error_log: list[str]            # 字段缺失 / 抓取失败的逐条记录
```

==每个字段都能追溯到 `metadata.source_url + raw_snippet_path`==——orchestrator 跨 skill 整合时要用。

## Anti-pattern（不要做）

- ❌ 直接抓 JCR 公共 UI（SPA + 登录墙，徒劳）
- ❌ 凭训练数据脑补 IF / 分区数字（Grok 报告踩过的雷）
- ❌ 把 CAS 旧分区当 primary metric（2026 起 stale）
- ❌ 混合 trust 等级在同一行展示（把"网友评分"和"官方 IF"并排，误导）
- ❌ 反爬时跳 Tier 4 computer-use（LetPub 没强反爬，应升 Tier 3）
- ❌ 用来路不明的 JCR 镜像 / 第三方"实时 IF"
- ❌ 静默丢错——抓不到 / 字段缺失必须返回 `null` + 写入 `error_log`

## References

按需读取的细节文档：

| 文件 | 用途 | 何时读 |
|---|---|---|
| `references/letpub-url-cheatsheet.md` | URL 模式、搜索接口、journalid 解析、消歧策略 | Step 1 |
| `references/field-extraction-schema.md` | DOM/markdown 字段抽取规则 + JSON output schema 完整版 | Step 3 |
| `references/tier-upgrade-playbook.md` | Tier 1→2→3 升级触发条件、反爬识别 | Step 2 反爬时 |

## 与其他 skill 的协作

| Skill | 关系 |
|---|---|
| `journal-research-orchestrator` | **上游**：批量调度本 skill，传 ISSN list → 收集 LetPubProfile list → 合并到决策矩阵 |
| `ai-journal-match` | **上游**：AI 推荐候选 → 本 skill 验证全画像 |
| `journal-research-cn:muchong-cn-journal-review` | **跨 plugin 平行**：中文众包评论补充（GBK 编码站）|
| `journal-authority-check` | **平行**：MJL/SJR/DOAJ 第二权威源交叉 |
| `predatory-risk-check` | **下游**：本 skill 的 `in_warning_list` / `warning_reasons` 字段供其参考 |

## 本 skill 的 deletion-spec

- **触发删除条件**：LetPub 站本身停服或被替代；DOM 字段结构剧变到维护成本 > 重写；Claude Code / Codex 原生集成期刊数据集（如官方 MCP）使本 skill 冗余。
- **禁用方式**：删除 `plugins/journal-research-en/skills/letpub-sci-journal-review/`，bump plugin 版本（patch），更新本仓库 marketplace manifest，并重新安装本地插件。
- **卸载清单**：
  - `plugins/journal-research-en/.claude-plugin/plugin.json`（版本 bump）
  - `plugins/journal-research-en/README.md`（Skills 表 + Roadmap 段）
  - `plugins/journal-research-en/skills/journal-research-orchestrator/SKILL.md`（如已建：去掉对本 skill 的调用引用）
  - `plugins/journal-research-en/_shared/journal_identity.py`（如已建：删除 `LetPubProfile` dataclass）
