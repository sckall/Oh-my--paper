# 知乎提示词功能对照表

本文档确保 Oh My Paper 覆盖知乎提示词的所有功能。

## 25 阶段流水线

| 知乎阶段 | 名称 | Oh My Paper 命令 | 状态 |
|----------|------|-----------------|------|
| A1 | TOPIC_INIT | `/omp:setup` | ✅ |
| A+ | 硬件检测 | `/omp:hardware` | ✅ |
| A2 | 问题分解 | `/omp:decompose` | ✅ |
| A3 | SEARCH_STRATEGY | `survey.md` | ✅ |
| A4 | LITERATURE_COLLECT | `/omp:survey` | ✅ |
| A5 | LITERATURE_SCREEN [门控] | `/omp:gate` | ✅ |
| A6 | KNOWLEDGE_EXTRACT | `/omp:ideate` | ✅ |
| A7 | HYPOTHESIS_GEN + 辩论 | `/omp:ideate` + `/omp:debate` | ✅ |
| **8.5** | THEORETICAL_BOUNDS | `/omp:theory` | ✅ 新增 |
| A8 | RESEARCH_DECISION | 自动决策 | ✅ |
| B9 | EXPERIMENT_DESIGN | `/omp:experiment` | ✅ |
| B10 | EXPERIMENT_DESIGN [门控] | `/omp:gate` | ✅ |
| B11 | CODE_GENERATION | `/omp:experiment` | ✅ |
| B12 | EXPERIMENT_RUN | `/omp:experiment` | ✅ |
| B13 | ITERATIVE_REFINE | `/omp:repair` | ✅ 新增 |
| B14 | RESULT_ANALYSIS | `/omp:analyze` | ✅ |
| B15 | RESEARCH_DECISION | 自动决策 | ✅ |
| C16 | PAPER_OUTLINE | `/omp:write` | ✅ |
| C17 | PAPER_DRAFT | `/omp:write` | ✅ |
| C18 | PEER_REVIEW | `/omp:review` | ✅ |
| C19 | PAPER_REVISION | `/omp:write` | ✅ |
| C20 | QUALITY_GATE [门控] | `/omp:gate` | ✅ |
| C21 | KNOWLEDGE_ARCHIVE | `/omp:archive` | ✅ 新增 |
| C22 | EXPORT_PUBLISH | `/omp:export` | ✅ |
| C23 | CITATION_VERIFY | `/omp:review` | ✅ |
| D24 | 3RD_PARTY_REVIEW | `/omp:3rdparty` | ✅ |
| I25 | REBUTTAL | `/omp:rebuttal` | ✅ |

## 知乎提示词核心功能

### 1. 计算与资源守卫

| 功能 | 实现 | 状态 |
|------|------|------|
| Pilot 运行 + TIME_ESTIMATE | `experiment.md` B4 | ✅ |
| 动态种子缩放 | `experiment.md` 4.4 | ✅ |
| time_guard | `experiment.md` 5.1 | ✅ |
| 优雅中断 | `experiment.md` 5.1 | ✅ |
| 资源预算 80% 停止 | `constraints.mjs` | ✅ |

### 2. 真实性代码红线

| 功能 | 实现 | 状态 |
|------|------|------|
| 禁止 random.uniform() | `constraints.mjs` | ✅ |
| 真实数学逻辑 | `constraints.mjs` | ✅ |
| 收敛检查 | `constraints.mjs` | ✅ |
| NaN/Inf 追踪根源 | `/omp:repair` | ✅ |
| 禁止 np.nan_to_num() 掩盖 | `/omp:repair` | ✅ |

### 3. 顶会论文标准

| 功能 | 实现 | 状态 |
|------|------|------|
| Sushi not Curry | `paper-writer.md` | ✅ |
| Figure 1 霸权 | `paper-writer.md` | ✅ |
| 强制消融实验 | `constraints.mjs` + `paper-writer.md` | ✅ |
| 强基线 | `paper-writer.md` | ✅ |
| 字数防卫 | `paper-writer.md` | ✅ |

### 4. 证据与相关性红线

| 功能 | 实现 | 状态 |
|------|------|------|
| Methodology-Evidence 一致性 | `reviewer.md` | ✅ |
| Trial Count 核查 | `reviewer.md` | ✅ |
| 统计检验核查 | `reviewer.md` | ✅ |
| CRITICAL FABRICATION 退回 | `reviewer.md` | ✅ |
| 文献保真 | `constraints.mjs` | ✅ |

### 5. 环境与库兼容性

| 功能 | 实现 | 状态 |
|------|------|------|
| np.trapz → np.trapezoid | `constraints.mjs` | ✅ |
| np.erfinv → scipy.special.erfinv | `constraints.mjs` | ✅ |
| np.bool → bool | `constraints.mjs` | ✅ |
| np.math → math | `constraints.mjs` | ✅ |

### 6. 多智能体协作

| 功能 | 实现 | 状态 |
|------|------|------|
| A7 多 Agent 辩论 | `/omp:debate` | ✅ |
| B14 独立 LLM 分析 | `/omp:analyze` | ✅ |
| D24 第三方评审 | `/omp:3rdparty` | ✅ |
| 并行执行 | `/omp:parallel` | ✅ |

### 7. 决策循环

| 功能 | 实现 | 状态 |
|------|------|------|
| PROCEED | `conductor.md` | ✅ |
| REFINE | `conductor.md` | ✅ |
| PIVOT | `conductor.md` | ✅ |
| 版本化 | `conductor.md` | ✅ |
| 循环验证 | `conductor.md` | ✅ |

### 8. 渐进式披露

| 功能 | 实现 | 状态 |
|------|------|------|
| 自动驾驶模式 | `mega.md` | ✅ |
| 状态摘要展示 | `mega.md` | ✅ |
| 详情按需展开 | `mega.md` | ✅ |
| 暂停时简洁展示 | `mega.md` | ✅ |

### 9. 其他功能

| 功能 | 实现 | 状态 |
|------|------|------|
| 文献多源搜索 | `/omp:survey` | ✅ |
| Gap 分析 | `/omp:survey` | ✅ |
| Citation 核查 | `/omp:review` | ✅ |
| Rebuttal | `/omp:rebuttal` | ✅ |
| Overleaf 导出 | `/omp:export` | ✅ |

## 未实现的功能

无。所有知乎提示词功能均已实现。

## 命令速查

```bash
# 启动自动驾驶
/omp:mega → 选择"🚀 自动驾驶"

# 单独使用
/omp:hardware   # A+ 硬件检测
/omp:decompose  # A2 问题分解
/omp:survey     # A4 文献调研
/omp:ideate     # A6 假设生成
/omp:debate     # A7 辩论验证
/omp:theory     # 8.5 理论分析
/omp:experiment # B9-B13 实验
/omp:repair     # B13 自修复
/omp:analyze    # B14 结果分析
/omp:write      # C16-C19 论文写作
/omp:review     # C18 同行评审
/omp:archive    # C21 知识归档
/omp:export     # C22 导出发布
/omp:3rdparty   # D24 第三方评审
/omp:rebuttal   # I25 Rebuttal
/omp:parallel   # 并行执行
```

## 更新时间

2026-04-05