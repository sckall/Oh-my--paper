# .workflow — Tracker 系统

Oh My Paper 项目使用的四个核心 tracker 文件，作为多 Agent 协作的交接介质和真相源。

## 文件概览

| 文件 | 用途 | 谁写 |
|------|------|------|
| `paper-issues.yaml` | 论文问题追踪 | omp:critique / Conductor |
| `literature-bank.yaml` | **唯一文献真相源** | research-literature-trace |
| `experiment-log.yaml` | 实验执行记录 | omp:experiment |
| `decision-log.yaml` | 阶段门控决策 | Conductor |

> ⚠️ `literature_bank.md`（markdown 表格）和 `paper_bank.json`（JSON）为**衍生格式**，可从 YAML 导出，不必手动维护。YAML 是唯一写入目标。

## 快速开始

### 1. 发现问题 → 记录到 paper-issues.yaml

```yaml
- id: OMP-001
  title: Introduction 缺少方法论概述
  description: 读者无法快速理解论文技术路线
  severity: major
  status: open
  source: reviewer
  created_at: "2026-04-08T01:30:00+08:00"
```

### 2. 做实验 → 记录到 experiment-log.yaml

```yaml
- id: EXP-001
  hypothesis_id: H-001
  title: 验证 RAG 提升生物试题召回率
  config:
    model: gpt-4
    top_k: 5
  result: 召回率从 0.62 提升至 0.81
  evidence: results/run_001.json
  decision: PROCEED
  created_at: "2026-04-08T01:35:00+08:00"
```

### 3. 阶段决策 → 记录到 decision-log.yaml

```yaml
- id: DEC-001
  stage: experiment-design
  decision: PROCEED
  reason: 召回率提升 30%，超过 0.75 阈值
  confidence: 0.85
  evidence: experiment-log.yaml EXP-001
  timestamp: "2026-04-08T01:40:00+08:00"
  next_step: 进入写作阶段
```

### 4. 收集文献 → 记录到 literature-bank.yaml

```yaml
- id: LIT-001
  title: "Chain-of-Thought Prompting Elicits Reasoning in LLMs"
  authors: ["Wei, Jason", "Wang, Xuezhi", "Schuurmans, Dan"]
  venue: NeurIPS 2022
  year: 2022
  tags: ["prompt-engineering", "reasoning"]
  notes: "CoT 是本文实验设计的重要 baseline"
  quality: high
  url: "https://arxiv.org/abs/2201.11903"
  added_at: "2026-04-08T01:00:00+08:00"
```

## 状态机

### paper-issues 状态流

```
open → actionable → completed → cleaned
                ↘ wont-do   → reopened
```

## 决策类型

| 决策 | 条件 | 行动 |
|------|------|------|
| `PROCEED` | 达标 + 证据充分 | 推进下一阶段 |
| `REFINE` | 接近达标或证据可修复 | 版本 +0.1，调整后继续 |
| `PIVOT` | 完全不达标或假设证伪 | 版本 +1.0，返回假设阶段 |

## 协作规则

1. **只追加，不覆盖** — 所有记录只追加，保留完整历史
2. **每个阶段必须有决策** — 进入下一阶段前必须记录 decision-log
3. **问题不过夜** — open 状态当日完成 triage
4. **证据链必须完整** — decision 必须引用 experiment-log 或 paper-issues

详细字段说明请参阅 [schema.md](./schema.md)。
