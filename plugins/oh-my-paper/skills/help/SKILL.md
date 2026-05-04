---
description: 显示 Oh My Paper 插件的所有可用命令和帮助信息
---

# /omp:help — OMP 命令速查

> 不询问任何问题，直接展示以下帮助信息。

## 快速开始

初次使用请运行：
1. `/omp:setup` — 初始化研究项目结构
2. `/omp:guide` — 交互式教程（推荐新手先走一遍）
3. `/omp:mega` — 进入 25 阶段研究流水线

## 推荐科研工作流

```
阶段一：选题准备（确定投什么）
  /journal-research-orchestrator 或 /cn-orchestrator（选刊）
  → /omp:plan（基于目标期刊制定研究计划）

阶段二：研究写作（写什么、怎么写）
  /omp:setup → /omp:survey → /omp:ideate → /omp:experiment
  → /omp:write → /omp:review → /omp:export
```

**核心理念：先选刊再动手。** 期刊决定格式、方向侧重、审稿难度和发表周期。
选刊是写作前的准备，不是写作中间的步骤。确定目标期刊后，再围绕期刊要求规划研究方案和实验设计。

## 全部命令

| 命令 | 用途 |
|------|------|
| `/omp:setup` | 初始化 `.pipeline/` 研究项目结构 |
| `/omp:analyze` | 扫描并分析期刊论文库 |
| `/omp:mega` | 25 阶段研究流水线（自动驾驶/半自动/单步） |
| `/omp:ideate` | 生成研究创新点 |
| `/omp:plan` | 制定研究计划 |
| `/omp:progress` | 查看项目进展 |
| `/omp:review` | 同行评审论文质量 |
| `/omp:write` | 论文写作冲刺 |
| `/omp:export` | 导出论文为 PDF |
| `/omp:debate` | 多 Agent 辩论验证假设 |
| `/omp:experiment` | 实验设计、实现和分析 |
| `/omp:recover` | 从快照恢复项目状态 |
| `/omp:update` | 检查并更新 OMP 插件 |
| `/omp:survey` | 文献调研 |
| `/omp:guide` | 交互式教程（模拟项目引导） |

## 期刊选刊（v0.3.0 新增）

| 命令 | 用途 |
|------|------|
| `/journal-research-orchestrator` | 英文/SCI 期刊选刊全流程（2 主投 + 2 备选 + 1 不建议） |
| `/cn-orchestrator` | 中文期刊选刊全流程（北核/CSSCI/CSCD/CSTPCD） |
| `/ai-journal-match` | AI 智能匹配期刊（JANE 路径） |
| `/openalex-explore` | OpenAlex 学术数据库探索 |
| `/crossref-validator` | Crossref 元数据校验 |
| `/letpub-sci-journal-review` | LetPub SCI 期刊画像（IF/分区/审稿周期/APC） |
| `/predatory-risk-check` | 掠夺刊风险筛查 |
| `/cn-discover-by-catalog` | 中文核心期刊目录发现 |
| `/cn-discover-by-paper` | 通过已发表论文反推中文期刊 |
| `/easyscholar-rank` | EasyScholar 期刊等级标签查询 |
| `/muchong-cn-journal-review` | 小木虫中文期刊投稿口碑 |
| `/nppa-validator` | 国家新闻出版署官方刊号核验 |

## 子代理

运行 `/omp:setup` 后，每次开启 Claude Code 会自动询问工作模式并指派对应 agent：
- **conductor** — 总指挥，统筹全局
- **literature-scout** — 文献侦察兵
- **experiment-driver** — 实验驾驶员
- **paper-writer** — 论文作家
- **reviewer** — 质量审查员

## 期刊选刊场景路由

| 用户输入 | 走哪个流程 |
|---------|-----------|
| "帮我做期刊调研，我研究 LLM RAG" | `/journal-research-orchestrator`（英文完整三层） |
| "帮我找中文核心期刊，经济学方向" | `/cn-orchestrator`（中文完整流程） |
| "这 5 个 ISSN 帮我对比一下" | `/journal-research-orchestrator`（跳探索层） |
| "Scientific Reports 现在能投吗？" | `/letpub-sci-journal-review` + `/predatory-risk-check` |
| "查一下 CN 号是否合法" | `/nppa-validator` |

> 提示：随时可以输入命令名的一部分（如 `analyze`）让 Claude 自动匹配技能。
