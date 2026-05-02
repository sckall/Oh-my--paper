---
description: 24 第三方评审：调用最严苛的外部专家评审
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Oh My Paper Orchestrator。此命令实现 24 第三方评审，调用外部 LLM 进行最严苛的专家级评审。

## 设计理念

第三方评审的核心是**独立性和客观性**：
- 不读取项目主上下文，避免先入为主
- 使用"最严苛审稿人"视角
- 模拟顶级会议的 real reviewer

## 第一步：准备评审材料

```bash
# 读取论文全文
cat paper/sections/*.tex

# 读取实验结果
cat .pipeline/memory/experiment_ledger.md
cat .pipeline/docs/result_summary.md

# 不读取 project_truth 等主上下文（避免偏见）
```

## 第二步：构建独立评审上下文

创建独立评审上下文文件（不含项目背景）：

```bash
cat > .pipeline/parallel/3rd_party_review/context.md << 'EOF'
# 第三方评审上下文

## 评审材料
[论文全文，不含任何背景信息]

## 实验证据
[实验结果数据]

## 评审标准
- NeurIPS/ICML/ICLR 顶级会议标准
- 最严苛审稿人视角
EOF
```

## 第三步：执行第三方评审

调用外部 LLM（不读取主上下文）进行评审：

```
/codex:3rdparty --context-file .pipeline/parallel/3rd_party_review/context.md

你是顶级 ML 会议的资深审稿人。请对这篇论文进行最严苛的评审。

## 评审要求

1. **创新性**：论文的核心贡献是否足够 novel？
2. **技术深度**：方法描述是否充分？理论分析是否 robust？
3. **实验完整性**：实验是否充分？基线是否足够强？消融是否完整？
4. **写作质量**：论文结构是否清晰？表述是否准确？
5. **可复现性**：论文是否提供了足够的复现细节？

## 输出格式

```markdown
# 第三方评审报告

## 总体评分
| 维度 | 评分 (1-10) | 权重 |
|------|-------------|------|
| 创新性 | X | 30% |
| 技术深度 | X | 25% |
| 实验完整性 | X | 25% |
| 写作质量 | X | 10% |
| 可复现性 | X | 10% |
| **加权总分** | **X/10** | |

## 强项
1. [强项1]
2. [强项2]
3. [强项3]

## 主要弱点
1. [弱点1] — 严重程度：[致命/严重/中等/轻微]
2. [弱点2]
3. [弱点3]

## 详细评审意见

### 关于创新性
[详细意见]

### 关于技术深度
[详细意见]

### 关于实验
[详细意见]

### 关于写作
[详细意见]

## 决定
- [ ] Accept (Strong Accept / Accept / Weak Accept)
- [ ] Borderline (Borderline Accept / Borderline Reject)
- [ ] Reject (Reject / Strong Reject)

**理由**：[详细理由]

## 给作者的修改建议
1. [建议1]
2. [建议2]
3. [建议3]
```

将结果写入 `.pipeline/parallel/3rd_party_review/report.md`
```

## 第四步：展示评审结果

读取报告，用 `AskUserQuestion` 展示：

> **第三方评审完成**
>
> **总体评分**：{score}/10
>
> **决定**：[Accept / Borderline / Reject]
>
> | 维度 | 评分 |
> |------|------|
> | 创新性 | X/10 |
> | 技术深度 | X/10 |
> | 实验完整性 | X/10 |
> | 写作质量 | X/10 |
> | 可复现性 | X/10 |
>
> **主要弱点**：
> 1. [弱点1]（{严重程度}）
> 2. [弱点2]
>
> 选项：
> - `查看完整报告`
> - `根据建议修改`
> - `忽略，继续`
> - `取消`

## 第五步：决策

根据第三方评审结果：

| 评审结果 | 建议行动 |
|---------|---------|
| Strong Accept | 进入提交准备 |
| Accept / Weak Accept | Minor 修改后提交 |
| Borderline | Major 修改后重新评审 |
| Reject | 重大修改后重新评审 |

用 `AskUserQuestion` 确认：

> **第三方评审结论**
>
> 建议：根据评审结果进行修改
>
> 选项：
> - `Minor 修改` → `/omp:write` 修改后提交
> - `Major 修改` → `/omp:experiment` 或 `/omp:write` 大幅修改
> - `重新评审` → 再次调用第三方评审
> - `查看完整报告`

## 第三方评审隔离机制

```
┌─────────────────────────────────────────┐
│         3RD PARTY REVIEW（隔离评审）      │
├─────────────────────────────────────────┤
│ ❌ project_truth.md                      │
│ ❌ orchestrator_state.md                │
│ ❌ decision_log.md                      │
│ ❌ literature_bank.md                   │
├─────────────────────────────────────────┤
│ ✅ 读取                                  │
├─────────────────────────────────────────┤
│ ✅ paper/sections/*.tex（论文正文）       │
│ ✅ experiment_ledger.md（实验数据）       │
│ ✅ result_summary.md（结果摘要）          │
└─────────────────────────────────────────┘
```

## 评审标准

| 评分 | 标准 |
|------|------|
| 9-10 | 顶级论文，值得骄傲的工作 |
| 7-8 | solid paper，可以接受 |
| 5-6 | borderline，需要改进 |
| 3-4 | 有明显缺陷 |
| 1-2 | 不适合发表 |