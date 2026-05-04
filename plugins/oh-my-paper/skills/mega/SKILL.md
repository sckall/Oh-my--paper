---
description: Mega 模式入口：25 阶段流水线，支持门控检查和决策循环
---

# /omp:mega — 研究流水线

> 所有选择必须用 AskUserQuestion 工具。

## 第一步：读取状态

```bash
ls .pipeline/mega/PROGRESS.md 2>/dev/null || echo "NOT_INITIALIZED"
cat .pipeline/memory/settings.md 2>/dev/null || echo "DEFAULT_SETTINGS"
cat .pipeline/docs/research_brief.json 2>/dev/null || echo "NO_BRIEF"
```

未初始化则提示运行 `/omp:setup`。

## 第二步：展示概览 + 选择执行模式（一次性）

```
🚀 Mega 模式 — v{version}  阶段: {stage}  进度: {progress}%
A (研究定义) ████░░  B (实验) ░░░░  C (论文) ░░░░  D-I (审核) ░░░░
```

**一次 AskUserQuestion**：
> 🚀 自动驾驶 — Conductor 自动推进，决策点暂停  
> 📋 半自动 — 每阶段前确认  
> ▶️ 单步 — 执行一个阶段  
> 📊 详情 — 显示完整阶段表  
> q. 退出

## 流水线阶段参考

当用户选择"详情"时展示完整表格：

| 阶段 | 名称 | 自动 | 产出 |
|------|------|------|------|
| **A1** | 主题定义 | ✅ | project_truth.md |
| **A+** | 硬件检测 | ✅ | hardware_status.md |
| **A2** | 问题分解 | ✅ | problem_tree.md |
| **A3** | 搜索策略 | ✅ | search_strategy.yaml |
| **A4** | 文献收集 | ✅ | literature_bank.md |
| **A5** | 文献门控 | ⏸️ | — |
| **A6** | 假设生成 | ✅ | hypothesis.md |
| **A7** | 多Agent辩论 | 🤖 | debate_result.md |
| **A8** | 研究决策 | ⏸️ | — |
| **B9** | 实验设计 | ✅ | experiment_plan.md |
| **B10** | 实验门控 | ⏸️ | — |
| **B11** | 代码实现 | ✅ | experiments/*.py |
| **B12** | 实验运行 | ⏸️ | experiment_ledger.md |
| **B13** | 迭代优化 | 🤖 | experiment_ledger.md |
| **B14** | 结果分析 | 🤖 | analysis_report.md |
| **B15** | 研究决策 | ⏸️ | — |
| **C16** | 论文大纲 | ✅ | outline.md |
| **C17** | 论文初稿 | ✅ | paper/sections/*.tex |
| **C18** | 同行评审 | 🤖 | review_log.md |
| **C19** | 论文修订 | ✅ | paper/sections/*.tex |
| **C20** | 质量门控 | ⏸️ | — |
| **C21** | 知识归档 | ✅ | archive/ |
| **C22** | 导出发布 | ✅ | main.pdf |
| **C23** | 引用核查 | ✅ | references.bib |
| **D24** | 第三方评审 | 🤖 | 3rd_party_report.md |
| **I25** | Rebuttal | ⏸️ | rebuttal_response.md |

## 第三步：执行流水线

### 🚀 自动驾驶

自动推进流水线，直至：
- 遇到 ⏸️ **门控点**：暂停，AskUserQuestion 让用户决策
- 遇到 🤖 **Agent 阶段**：调用对应子 agent 执行（debate → A7，review → C18 等）
- 用户说 `暂停`、`继续`、`停止`、`跳过`、`状态`、`详情` 时响应用户

### 决策点

决策点出现时一次问完：

> **决策点 — {stage}**  
> 问题：{问题描述}  
> [PROCEED] 继续下一阶段  
> [REFINE] 返回调整  
> [PIVOT] 重新假设  
> [详情] 查看完整上下文

### 用户干预

运行期间用户说以下关键字时立即响应：

| 关键字 | 动作 |
|--------|------|
| 暂停 | 停在当前阶段，进入手动模式 |
| 继续 | 恢复推进 |
| 停止 | 结束流水线 |
| 跳过 | 跳过当前阶段 |
| 状态 | 显示当前进度 |

## 配置

`.pipeline/memory/settings.md`:

```yaml
AUTO_EXECUTE: true       # 启用自动驾驶
AUTO_DECISION: false     # 决策仍需确认
PAUSE_ON_PIVOT: true     # PIVOT 时暂停
PAUSE_ON_REFINE: true    # REFINE 时暂停
```

## 完成

流水线完成时展示：

```
✅ 研究流水线完成！版本: v{version}
下一步: 准备提交
[查看论文] [导出到 Overleaf] [新项目]
```

## 错误处理

执行过程中遇到以下情况请统一处理：

| 场景 | 处理方式 |
|------|---------|
| 文件或目录不存在 | 提示用户："⚠️ 未找到 {文件名}，请检查是否已完成前置步骤" |
| 命令执行失败 | 提示用户："⚠️ 执行失败：{错误原因}，请检查后重试" 并提供重试/跳过/退出选项 |
| 用户输入无效 | 提示用户："❌ 无效选项，请重新选择" 并重新展示选项 |
| 其他意外错误 | 提示用户："⚠️ 发生意外错误：{描述}，[重试] [返回] [退出]" |

所有交互均使用 AskUserQuestion 工具，不要用纯文字替代。

