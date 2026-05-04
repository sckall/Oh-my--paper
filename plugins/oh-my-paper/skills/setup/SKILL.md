---
description: 初始化研究项目结构（.pipeline/），包括目录、配置文件和基础文档
---

# /omp:setup — 初始化研究项目

> 所有选择必须用 AskUserQuestion 工具。

## 第一步：一键收集项目信息

**一次性 AskUserQuestion 完成所有信息收集**（不要分步问）：

> 请填写研究项目信息：
> - **研究主题**（必填，如"多模态医学影像分割"）
> - **起始阶段**：survey（文献调研）| ideation（创新点）| experiment（实验）| publication（论文写作）
> - **工作模式**：Mega（25 阶含门控，推荐）| Legacy（5 阶传统模式）

## 第二步：创建目录结构和文件

```bash
# 基础目录
mkdir -p .pipeline/memory .pipeline/tasks .pipeline/docs .pipeline/.hook-events

# Mega 模式额外目录
if [ "$MODE" = "Mega" ]; then
  mkdir -p .pipeline/mega/plans .pipeline/mega/logs
  cp -n "${CLAUDE_PLUGIN_ROOT}/templates/PROGRESS.md" .pipeline/mega/ 2>/dev/null || true
  cp -n "${CLAUDE_PLUGIN_ROOT}/templates/RESTRICTIONS.md" .pipeline/mega/ 2>/dev/null || true
fi
```

创建以下初始文件（已存在则跳过）：

**`.pipeline/docs/research_brief.json`**：
```json
{
  "topic": "[用户填写的主题]",
  "goal": "",
  "currentStage": "[用户选择的阶段]",
  "successThreshold": "",
  "mode": "[Legacy 或 Mega]"
}
```

**`.pipeline/memory/project_truth.md`**：研究主题和已确认决策记录
**`.pipeline/tasks/tasks.json`**：空任务列表 `{"version": 1, "tasks": []}`
**`.pipeline/memory/orchestrator_state.md`**、`execution_context.md`、`review_log.md`、`agent_handoff.md`、`decision_log.md`、`literature_bank.md`、`experiment_ledger.md`：均创建空白文件，标注"待填充"

## 第三步：完成确认

> ✅ 项目已初始化
> - 主题：{topic}
> - 起始阶段：{stage}
> - 工作模式：{mode}
>
> 下一步推荐：
> - `/omp:help` — 浏览全部命令
> - `/omp:plan` — 制定任务计划
> - `/omp:mega` — 进入流水线（Mega 模式）

选项：
- `开始！运行 /omp:plan`
- `先自己看看文件结构`

## 注意事项

- SessionStart 钩子由插件 `hooks/hooks.json` 自动处理，无需手动注册
- 插件命令通过 `/omp:` 命名空间访问，无需复制技能到 `.claude/skills/`
- Codex 等外部工具非必须，可随时启用

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| 目录已存在 | 跳过，不覆盖 |
| 模板文件不存在 | 静默跳过，不影响初始化 |
| 写入失败 | 提示具体路径，提供重试/跳过选项 |
