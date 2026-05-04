---
name: cn-orchestrator
description: 用于中文期刊 P0 调研主流程编排时使用：用户给研究方向、学科名、候选刊名、ISSN、CN 号或"这本刊合法吗"时，路由 A 路径 cn-discover-by-catalog、B 路径 cn-discover-by-paper，并并发使用 easyscholar-rank 与 muchong-cn-journal-review 做画像；仅在用户明确问 CN 号/合法性时调用 nppa-validator。触发关键词：中文期刊调研、投稿选刊、北核 CSSCI CSCD CSTPCD、找中文核心期刊、journal targeting cn、P0 选刊。不用于英文/SCI 路线（那是 journal-research-en:journal-research-orchestrator）、不直接抓网页数据（那是各 sub-skill）、不替用户绕验证码或反爬（那是用户人工核验）。
---

# cn-orchestrator

## 一句话定位

中文期刊 P0 调研总入口。它像“国内投稿选刊顾问”：先判定用户输入类型，再走目录白名单或论文反推生成候选，随后补等级标签、中文投稿口碑和按需合法性校验，最后输出决策矩阵。

本 skill 只负责编排和判断，不直接调用外部网站。

## P0 方法论（内联）

P0 期刊调研 = 投稿前的"先选期刊再定方向"，调研工作量应占整个流程 1/4 到 1/3。

中文路线四步：AI 缩范围 → 小木虫核实口碑 → 等级目录确认（北核/CSSCI/CSCD/CSTPCD）→ 锁定 2 主投 + 2 备选 + 1 不建议。

决策矩阵口径：
- 目录收录只代表候选池质量，不等于"必然好投"
- 小木虫口碑是 `community-cn` 必须单列，不与权威指标合并
- 影响因子单一指标 ≠ 投稿可行性；必须叠加审稿周期 + 录用率 + 评论区真实反馈
- AI 推荐结果必须拿去 easyscholar/小木虫逐一核实，不可直接采信

## Method-call

`/cn-orchestrator(input, constraints=None, candidate_limit=10)`

## 输入类型路由

| 用户输入 | 主路径 | 并行/兜底 | 说明 |
|---|---|---|---|
| 学科名，如“经济学”“电气工程” | `journal-research-cn:cn-discover-by-catalog` | `cn-discover-by-paper` 兜底 | A 路径：4 表目录 + ncpssd 学科召回 |
| 自由研究方向，如“配电网故障定位” | `journal-research-cn:cn-discover-by-paper` | `cn-discover-by-catalog` 兜底 | B 路径：百度学术论文反推 venue |
| 已有中文刊名 | `journal-research-cn:easyscholar-rank` | `journal-research-cn:muchong-cn-journal-review` | 直接进入画像层 |
| 已有 ISSN | `muchong-cn-journal-review` | `easyscholar-rank` | ISSN 强匹配口碑，刊名用于 rank |
| “查 CN 号”“是否合法”“新闻出版署” | `journal-research-cn:nppa-validator` | 手动官方查询链接 | NPPA 按需调用，不进默认主流程 |

## 三层流程

### 第一层：探索

A 路径适合用户只给学科或想要“先看国内核心目录里有哪些刊”：

```bash
python3 plugins/journal-research-cn/skills/cn-discover-by-catalog/scripts/discover_by_catalog.py "经济学" --limit 20
```

B 路径适合用户给论文题目、摘要关键词或工程研究方向：

```bash
python3 plugins/journal-research-cn/skills/cn-discover-by-paper/scripts/discover_by_paper.py "配电网故障定位" --limit 10
```

探索层返回 `CandidateJournal[]`，`trust_level` 只能用于候选生成，不能直接作为最终投稿建议。

### 第二层：画像

对每个候选刊并行补：

| Sub-skill | 填充字段 | trust_level |
|---|---|---|
| `journal-research-cn:easyscholar-rank` | `rank_profile.officialRank`、北核/CSSCI/CSCD/CSTPCD 等标签 | `rank-cn` |
| `journal-research-cn:muchong-cn-journal-review` | `review_intel.cn_excerpts`、审稿速度、费用、投稿体验 | `community-cn` |
| `journal-research-cn:nppa-validator` | `official_identity.cn_number`、主管/主办单位 | `official-cn` |

NPPA 只在用户明确要求合法性、CN 号或候选刊身份有疑点时调用。

### 第三层：决策矩阵

输出 2 主投 + 2 备选 + 1 不建议。若候选不足 5 个，按实际数量输出并解释缺口来自候选召回不足或外部 API 限制。

## 输出 Schema

```json
{
  "query": "配电网故障定位",
  "route": "B/baidu-paper-reverse",
  "candidate_count": 5,
  "decision_matrix": [
    {
      "title_cn": "电力系统自动化",
      "fit_score": 0.86,
      "catalog_labels": ["pku", "cscd"],
      "rank_summary": {"pku": true, "cssci": false, "cscd": true, "cstpcd": true},
      "review_summary": {"visible_reviews": 8, "speed": "2-4 月", "fees": "以小木虫可见记录为准"},
      "risk_flags": [],
      "recommended_action": "主投",
      "evidence_sources": ["baidu-scholar", "easyscholar-open-api", "muchong-detail"]
    }
  ]
}
```

## Anti-pattern

- 不把目录收录当作“必然好投”；目录只证明候选池质量。
- 不把小木虫口碑当官方结论；它是 `community-cn`，必须单列。
- 不默认调用 NPPA；只有合法性和 CN 号问题才查。
- 不在仓库写 API key；easyScholar 与百度 key 只读 env 或 Keychain。
- 不接维普/CNKI 路径；本 plugin 明确避开高反爬路线。
- 不替用户绕验证码；遇到验证码返回 `captcha_required` 和官方手动链接。

## 协作边界

| Skill | 关系 |
|---|---|
| `journal-research-cn:cn-discover-by-catalog` | A 路径候选生成 |
| `journal-research-cn:cn-discover-by-paper` | B 路径候选生成 |
| `journal-research-cn:easyscholar-rank` | 第二层等级画像 |
| `journal-research-cn:muchong-cn-journal-review` | 第二层中文投稿口碑 |
| `journal-research-cn:nppa-validator` | 按需官方合法性校验 |
| `journal-research-en:journal-research-orchestrator` | 英文/SCI 路线主入口 |

## 本 skill 的 deletion-spec

- **触发删除条件**：中文路线的 A/B 候选生成与画像层被统一的官方期刊数据库 MCP 取代；或本 plugin 改为单 skill 自动管线，不再需要人工路由说明；或中文期刊调研场景被并入更高层投稿项目 orchestrator。
- **禁用方式**：删除 `plugins/journal-research-cn/skills/cn-orchestrator/`，bump `journal-research-cn` minor，重生成 marketplace，并刷新 Claude/Codex cache。
- **卸载清单**：同步更新 `plugins/journal-research-cn/README.md` 的主入口与流程图、`muchong-cn-journal-review/SKILL.md` 中的 orchestrator 引用、`plugins/journal-research-cn/.claude-plugin/plugin.json` 描述，以及中文 P0 知识库入口文档。
