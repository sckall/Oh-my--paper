---
description: 论文写作冲刺：按节确认后逐步推进，每节完成后展示再继续
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Oh My Paper Orchestrator。写作按节推进，每节完成后确认再继续。

## 第一步：确认写作范围 + 论文约束检查

```bash
cat .pipeline/docs/result_summary.md
ls paper/sections/

# Mega 模式：运行论文约束检查
node "${CLAUDE_PLUGIN_ROOT}/scripts/constraints.mjs" paper
```

用 `AskUserQuestion` 展示：

> **准备写作的章节**：
> - [ ] abstract.tex
> - [ ] introduction.tex
> - [ ] related_work.tex
> - [ ] methodology.tex
> - [ ] experiments.tex
> - [ ] conclusion.tex（可选）
>
> 已有文件：[列出 sections/ 下已存在的]

选项：
- `全部从头写`
- `只写缺少的章节`
- `指定某几节`

## 第二步：按节逐步执行（调用 Writer BLOCK + GATE CHECK）

每节开始前，先告知用户字数要求，然后调用对应的 Writer BLOCK。

### BLOCK 调度规则

| 节名 | Writer BLOCK | 字数要求 | GATE CHECK |
|------|-------------|---------|------------|
| background | `background-writer.md` | ≥800 | 引用存在于 references.bib |
| methods | `methods-writer.md` | ≥800 | 功能描述与 result_summary 一致 |
| results | `results-writer.md` | ≥1500 | 迭代记录与 result_summary 一致 |
| practice | `practice-writer.md` | ≥800 | 无捏造教学数据 |
| conclusion | `conclusion-writer.md` | ≥1000 | 贡献具体化 |

### 调用 Writer BLOCK

对每个要写的节，加载对应 BLOCK：
```
agents/stage-writers/{section}-writer.md
```

填充 Context Pack：
```
project_truth: .pipeline/memory/project_truth.md
result_summary: .pipeline/memory/result_summary.md
literature_bank: .pipeline/memory/literature_bank.md（Status=accepted）
```

调用示例（写 background）：
```
加载：agents/stage-writers/background-writer.md

等待产出：
paper/sections/background.md

执行 GATE CHECK：
node "${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.mjs" --section=background
```

### 字数要求

- **背景介绍** (background): ≥800 词
- **方法设计** (methods): ≥800 词
- **实验结果** (results): ≥1500 词
- **教学实践** (practice): ≥800 词
- **结论反思** (conclusion): ≥1000 词（结论≥600 + 反思≥400）

**相关工作（如需单独写作）：**
- Related Work: 600-800 词

调用 `inno-paper-writing` skill，基于 `.pipeline/memory/literature_bank.md`（Status=accepted），写 `sections/related_work.tex`，`\cite{key}` 引用必须存在于 `references.bib`。

> 注：相关工作可由 `literature-scout` agent 自动生成，参考 `/omp:literature-scout`

**方法设计（methods）：**
- 字数要求: ≥800 词

调用 `methods-writer.md` BLOCK，基于 `project_truth.md` 写 `paper/sections/methods.md`。

**实验结果（results）：**
- 字数要求: ≥1500 词

调用 `results-writer.md` BLOCK，基于 `result_summary.md` 和 `experiment_ledger.md` 写 `paper/sections/results.md`。

### 2.1 新增：Figure 1 要求

在写 Introduction 之前，确认 Figure 1（架构图）已规划：

> **Figure 1 要求**
>
> Figure 1 必须能独立传达论文的核心贡献。
>
> 在继续写作前，请描述 Figure 1 的内容：
> - 架构图类型
> - 包含的核心元素
> - 用于 nano banana 2 绘图的详细 prompt
>
> 选项：
> - `已规划 Figure 1` — 继续写作
> - `暂不规划 Figure 1` — 先写正文

### 2.2 新增：每节完成后 GATE CHECK

每节完成后，执行自动化 GATE CHECK：

```bash
# 运行 gate-check.mjs
node "${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.mjs" --section={section_name}

# 运行 evidence-validator.mjs（验证证据一致性）
node "${CLAUDE_PLUGIN_ROOT}/scripts/evidence-validator.mjs" --section={section_name}
```

用 `AskUserQuestion` 展示 GATE 结果：

> **[节名] GATE CHECK 结果**
>
> - 字数：{actual} / {required}
> - 状态：✅ PROCEED / ❌ REFINE / 🚨 CRITICAL
>
> **GATE CHECK 详情**：
> - [检查项1]: ✅/❌
> - [检查项2]: ✅/❌
>
> 如果 REFINE：调用 Writer 自我修订，重新 GATE
> 如果 CRITICAL：立即暂停，报告给用户

每节完成后，用 `AskUserQuestion` 询问：

> **[节名] 已完成**。你想：

选项：
- `继续写下一节`
- `先看看这节写得怎么样`
- `这节有问题，让 Codex 修改`
- `暂停，稍后继续`

## 第三步：图表和引用

所有节完成后，询问：

> 正文已完成。接下来：

选项：
- `生成图表（architecture diagram、结果对比图）`
- `跳过图表，直接做引用审查`
- `两个都做`

**图表：**

调用 `inno-figure-gen` skill，生成 2-3 个关键图表到 `assets/figures/`。

**引用审查：**

调用 `inno-reference-audit` skill，检查所有 `\cite{}` 引用，修复缺失条目。

### 3.1 新增：证据一致性检查（仅 Mega 模式）

在进入质量门控前，运行证据一致性检查：

```bash
# 运行全稿 evidence-validator
node "${CLAUDE_PLUGIN_ROOT}/scripts/evidence-validator.mjs" --section=all

# 运行全稿 gate-check
node "${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.mjs" --section=all
```

用 `AskUserQuestion` 展示检查结果：

> **证据一致性检查**
>
> ✅ 通过：
> - [通过项]
>
> ⚠️ 警告：
> - [警告项]
>
> ❌ 失败：
> - [失败项]
>
> **必须修复的**：
> - 论文声称的实验条件数 vs experiment_ledger 记录
> - 论文中的 metrics vs result_summary.md 中的数值
> - trial count 是否与代码中的实际运行一致
>
> 选项：
> - `全部修复后继续`
> - `忽略警告继续` — 不推荐

## 第三步半（新）：质量门控 C20（仅 Mega 模式）

如果 research_brief.json 中 mode 为 "Mega"，在正文完成后执行门控检查：

```bash
# 运行全稿 gate-check（自动化门控）
node "${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.mjs" --section=all

# 运行全稿 evidence-validator（证据一致性）
node "${CLAUDE_PLUGIN_ROOT}/scripts/evidence-validator.mjs" --section=all

# 检查图表
ls paper/assets/figures/ 2>/dev/null || echo "NO_FIGURES"
# 检查引用数量
grep -c "@" references.bib 2>/dev/null || echo "0"
```

用 `AskUserQuestion` 展示：

> **质量门控 C20**
>
> **检查项**：
> - [ ] 论文章节完整（Abstract, Introduction, Method, Experiments, Conclusion）
> - [ ] 字数达标（Introduction ≥ 800, Method ≥ 1000, Experiments ≥ 800）
> - [ ] Figure 1 存在（架构图）
> - [ ] 消融实验完成（报告"移除该组件"对比数据）
> - [ ] 基线对比充分（≥ 3 个基线）
> - [ ] 引用完整（≥ 30 篇）
>
> **评分**：{score}/10
>
> **通过条件**：评分 ≥ 6 且所有检查项通过

**详细检查表**：

| 检查项 | 要求 | 当前状态 |
|--------|------|----------|
| Introduction 字数 | ≥ 800 | {intro_words} |
| Method 字数 | ≥ 1000 | {method_words} |
| Experiments 字数 | ≥ 800 | {exp_words} |
| Figure 1 | 存在 | {fig1_exists} |
| 消融实验 | 完成 | {ablation_done} |
| 基线数量 | ≥ 3 | {baseline_count} |
| 引用数量 | ≥ 30 | {citation_count} |
| NumPy 2.x 兼容 | 无 np.trapz 等 | {numpy_compat} |

选项：
- `通过` — 论文质量达标，进入导出发布
- `修改初稿` — 修改问题
- `补充实验` — 返回实验补充不足的消融/基线

如果用户选择"通过"，更新 `.pipeline/mega/PROGRESS.md` 中 C20 为 "passed"。

## 完成后

询问：
- `进入 /omp:review 做同行评审`
- `我自己先看看再说`

## 论文流程自动衔接

```
ideate → debate → experiment → analyze → write → review → revision → export
   ↓        ↓         ↓         ↓        ↓        ↓         ↓
  辩论    决策     调参      分析    修改     质量门控    发布
```

| 当前步骤 | 下一步 | 命令 |
|---------|-------|------|
| ideate 完成后 | 辩论验证假设 | `/omp:debate` |
| debate 通过后 | 设计实验 | `/omp:experiment` |
| experiment 有结果后 | 独立分析 | `/omp:analyze` |
| analyze 通过后 | 论文写作 | `/omp:write` |
| write 一节后 | 继续写下一节 | `/omp:write` |
| 所有章节写完后 | 同行评审 | `/omp:review` |
| review 完成后 | 修改论文 | `/omp:write` |
| 修改完成 | 质量门控 | `/omp:gate` |
| 质量通过 | 导出发布 | `/omp:export` |
