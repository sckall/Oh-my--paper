---
description: 全自动文献调研：先和用户确认搜索方向，再交给 Codex 执行
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Oh My Paper Orchestrator。执行文献调研前先和用户对齐方向。

## 第一步：读取研究主题

```bash
cat .pipeline/memory/project_truth.md
cat .pipeline/docs/research_brief.json
cat .pipeline/memory/literature_bank.md  # 查看已有多少文献
```

## 第二步：展示搜索计划，等待确认

用 `AskUserQuestion` 展示：

> 准备搜索以下方向的文献：
> 1. [方向 A]（关键词：...）
> 2. [方向 B]（关键词：...）
> 3. [方向 C]（关键词：...）
>
> 目标：约 20-30 篇，已有 X 篇
> 技能：inno-deep-research + paper-finder

选项：
- `确认，开始搜索`
- `调整搜索方向`
- `只搜某个方向`

如果用户选择调整，`AskUserQuestion` 询问具体方向修改，更新后再确认一次。

## 第三步：执行搜索（仅在确认后）

直接调用 `inno-deep-research` skill 执行搜索：

- 搜索确认后的方向列表，每个方向至少找 5 篇
- 将论文逐条追加到 `.pipeline/memory/literature_bank.md`（格式：`| DOI/URL | Title | Year | Venue | Relevance | accepted | Date |`）
- 完成后生成 `.pipeline/docs/gap_matrix.md` 分析研究空白
- 更新 `.pipeline/memory/agent_handoff.md`

## 第四步（新）：文献门控 A5（仅 Mega 模式）

如果 research_brief.json 中 mode 为 "Mega"，执行门控检查：

```bash
# 统计文献总数
grep -c "Status: accepted" .pipeline/memory/literature_bank.md 2>/dev/null || echo "0"
# 统计相关文献
grep -c "Relevance: high\|Relevance: medium" .pipeline/memory/literature_bank.md 2>/dev/null || echo "0"
# 检查领域覆盖
cat .pipeline/docs/gap_matrix.md 2>/dev/null || echo "NOT_FOUND"
```

用 `AskUserQuestion` 展示：

> **门控 A5：文献筛选**
>
> **检查项**：
> - [ ] 文献总数 ≥ 15 篇（当前：{count}）
> - [ ] 相关文献 ≥ 10 篇（当前：{relevant_count}）
> - [ ] 覆盖 3 个领域（方法论、基线、相关工作）
>
> **通过条件**：满足上述 3 项

选项：
- `通过` — 文献基础充足，继续假设生成
- `补充搜索` — 返回继续搜索，补充不足的领域
- `调整范围` — 调整研究问题范围

如果用户选择"通过"，更新 `.pipeline/mega/PROGRESS.md` 中 A5 为 "passed"。

## 第六步：展示结果摘要

结果回来后告诉用户：

- 新增了多少篇（总计多少篇）
- 主要覆盖了哪些方向
- gap_matrix.md 找到了哪几个研究空白

用 `AskUserQuestion` 询问：
- `够了，进入 /omp:ideate`
- `还需要补充搜索某个方向`
- `看看 gap_matrix 后再决定`

## 错误处理

执行过程中遇到以下情况请统一处理：

| 场景 | 处理方式 |
|------|---------|
| 文件或目录不存在 | 提示用户："⚠️ 未找到 {文件名}，请检查是否已完成前置步骤" |
| 命令执行失败 | 提示用户："⚠️ 执行失败：{错误原因}，请检查后重试" 并提供重试/跳过/退出选项 |
| 用户输入无效 | 提示用户："❌ 无效选项，请重新选择" 并重新展示选项 |
| 其他意外错误 | 提示用户："⚠️ 发生意外错误：{描述}，[重试] [返回] [退出]" |

所有交互均使用 AskUserQuestion 工具，不要用纯文字替代。

