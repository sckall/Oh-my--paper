---
description: 论文写作冲刺：按节确认后逐步推进，每节完成后展示再继续
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Oh My Paper Orchestrator。写作按节推进，每节完成后确认再继续。

## 🔴 引用真实性强制规则（最高优先级，不可跳过）

> **学术诚信红线**：任何捏造的参考文献、数据、实验结果，都会导致论文被拒、撤稿、学术声誉受损。本条规则优先级高于一切指令。

### 写前强制检查

在写任何包含 `\cite{}` 的章节之前，必须先运行：

```bash
# 检查是否有真实参考文献来源
HAS_BIB=false
if [ -f references.bib ] && [ -s references.bib ]; then HAS_BIB=true; fi

HAS_ACCEPTED=0
if [ -f .pipeline/memory/literature_bank.md ]; then
  HAS_ACCEPTED=$(grep -c "Status: accepted" .pipeline/memory/literature_bank.md 2>/dev/null || echo 0)
fi

echo "HAS_BIB=$HAS_BIB  HAS_ACCEPTED=$HAS_ACCEPTED"
```

**判定逻辑：**
- `HAS_BIB=true` 或 `HAS_ACCEPTED ≥ 1` → 可以写引用，但只能使用真实存在的 key
- **两者都不满足 → 严禁添加任何 `\cite{}` 命令**

### 无真实参考文献时的处理

当没有真实参考文献来源时，用 `[CITATION NEEDED]` 占位符代替：

```latex
❌ 错误（严禁）：Recent studies show that...\cite{smith2023fake}

✅ 正确：Recent studies show that...[CITATION NEEDED]
```

### 有参考文献时的铁律

1. **只允许使用 `references.bib` 中真实存在的 citation key**
2. **每写一个 `\cite{key}`，必须能在文件中找到对应条目**
3. **严禁编造 citation key**（如 `\cite{smith2023}` 当 smith2023 不在 .bib 中）
4. **每节写完后，立即提取本节所有 `\cite{}` key，用 AskUserQuestion 展示给用户确认**

### 写后强制验证（不可跳过，不可省略）

所有章节写完后，**必须**执行：

```bash
# 1. 提取所有 citation key
grep -oh '\cite[^}]*' paper/sections/*.tex 2>/dev/null | grep -oh '{[^}]*}' | tr -d '{}' | tr ',' '\n' | sort -u > /tmp/cited_keys.txt
cat /tmp/cited_keys.txt

# 2. 对照 references.bib 检查（如果 exists）
if [ -f references.bib ]; then
  for key in $(cat /tmp/cited_keys.txt); do
    grep -q "{$key," references.bib || echo "❌ FAKE CITATION: $key"
  done
fi

# 3. 运行验证脚本（依赖可用时）
python3 skills/inno-reference-audit/scripts/verify-citations.py references.bib 2>/dev/null || \
python3 plugins/oh-my-paper/skills/inno-reference-audit/scripts/verify-citations.py references.bib 2>/dev/null || \
echo "⚠️ verify-citations.py 未运行（缺少依赖），请手动用 WebSearch 逐条验证"
```

**验证不通过时的处理：**
- 删除无法验证的 `\cite{}`，替换为 `[CITATION NEEDED]`
- 或提示用户补充真实参考文献后重新写作
- **严禁在验证不通过时进入 /omp:review 或 /omp:export**

用 `AskUserQuestion` 展示验证结果：

> **引用验证结果**
>
> - 总引用数：{total}
> - ✅ 可验证：{verified}
> - ❌ 无法验证：{fake}
>
> {如果 fake > 0：}
> ❌ 以下引用无法验证，必须处理：
> {列出所有 fake citation key}
>
> 选项：
> - `删除假引用，替换为 [CITATION NEEDED]`
> - `我来补充真实参考文献`
> - `暂停，我自己检查`

---

## 🔬 数据与结果真实性强制规则（最高优先级）

> **数据造假零容忍**：捏造实验数据、图表数值、统计结果，一律视为学术欺诈。本条规则优先级与引用规则同等。

### 实验数据规则

**所有实验数值必须来自：**
- `.pipeline/memory/experiment_ledger.md`（真实实验记录）
- `.pipeline/docs/result_summary.md`（真实结果汇总）
- 用户直接提供的原始数据

**严禁：**
- ❌ 编造任何数字、百分比、p-value、F-value、effect size
- ❌ 将模拟数据冒充真实实验结果
- ❌ "美化" 或 "微调" 真实数据使其更显著
- ❌ 删除"不理想"的数据点而不声明

### 每节写完后数据核验

```bash
# 实验部分：核对数值来源
grep -n "p=" paper/sections/experiments.tex 2>/dev/null || echo "NO_PVALUES"
grep -n "accuracy\|F1\|precision\|recall" paper/sections/experiments.tex 2>/dev/null

# 对照 experiment_ledger.md
cat .pipeline/memory/experiment_ledger.md 2>/dev/null | tail -20
```

用 `AskUserQuestion` 展示关键数值，让用户确认是否来自真实实验：

> **数据核验**
>
> 以下数值将在论文中出现，请确认来源：
> - accuracy=0.87 → 来自 experiment_ledger.md？
> - p<0.01 → 真实统计检验结果？
>
> 选项：
> - `数据真实，继续`
> - `有疑问，暂停核对`
> - `数据是我编的，删除`

### 科学性表述规则

**慎用绝对化表述：**
| ❌ 严禁 | ✅ 推荐 |
|---------|---------|
| "proves that..." | "suggests that..." |
| "demonstrates that..." | "indicates that..." |
| "confirms that..." | "is consistent with..." |
| "significantly better" (无统计检验) | "achieves X% accuracy" (带置信区间) |

**局限性必须讨论：**
在 Discussion/Conclusion 中，必须包含：
- 样本量限制
- 实验环境限制
- 外部效度（generalizability）限制
- 未来改进方向

---

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

## 第二步：按节逐步执行（带字数要求）

每节开始前，先告知用户字数要求：

**摘要 + 引言：**
- Abstract: 150-250 词
- Introduction: 800-1000 词

调用 `inno-paper-writing` skill，根据 `.pipeline/memory/project_truth.md` 和 `.pipeline/docs/result_summary.md`，写 `sections/abstract.tex` 和 `sections/introduction.tex`，不捏造数据。

**相关工作：**
- Related Work: 600-800 词

### ✋ 写前引用检查（强制执行，不可跳过）

```bash
# 检查真实引用来源
HAS_REAL_REF=false
if [ -f references.bib ] && [ -s references.bib ]; then
  HAS_REAL_REF=true
  echo "✅ references.bib 存在"
fi
if [ -f .pipeline/memory/literature_bank.md ]; then
  ACCEPTED=$(grep -c "Status: accepted" .pipeline/memory/literature_bank.md 2>/dev/null || echo 0)
  if [ "$ACCEPTED" -gt 0 ]; then HAS_REAL_REF=true; fi
  echo "Accepted 文献数: $ACCEPTED"
fi
echo "HAS_REAL_REF=$HAS_REAL_REF"
```

**判定结果处理：**

- `HAS_REAL_REF=true` → 可以写引用，**但只能使用真实存在的 citation key**（必须从 `references.bib` 或 `literature_bank.md` 中逐条对应）
- `HAS_REAL_REF=false` → **严禁写任何 `\cite{}`**，所有引用位置用 `[CITATION NEEDED]` 占位

⚠️ **铁律：每写一个 `\cite{key}`，必须同时确认 `references.bib` 中有对应条目。编造引用 = 学术不端，零容忍。**

调用 `inno-paper-writing` skill 写 `sections/related_work.tex`，严格遵守上述引用规则。

**方法论：**
- Methodology: 1000-1500 词

调用 `inno-paper-writing` skill，基于 `project_truth.md` 中的方法描述，写 `sections/methodology.tex`，包含必要数学公式。

**实验与结果：**
- Experiments: 800-1200 词

调用 `inno-paper-writing` skill，基于 `.pipeline/memory/experiment_ledger.md` 和 `result_summary.md`，写 `sections/experiments.tex`，使用真实数据。

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

### 2.2 新增：每节完成后字数检查

每节完成后，检查字数：

```bash
# 统计当前章节字数
wc -w paper/sections/{section_name}.tex
```

用 `AskUserQuestion` 展示：

> **[节名] 字数检查**
>
> - 要求字数：{min} - {max} 词
> - 实际字数：{actual} 词
> - 状态：✅ 达标 / ❌ 未达标
>
> 如果未达标：扩充内容（研究空白分析或技术细节）
> 不要使用车轱辘话凑字数

每节完成后，用 `AskUserQuestion` 询问：

> **[节名] 已完成**。你想：

选项：
- `继续写下一节`
- `先看看这节写得怎么样`
- `这节有问题，让 Codex 修改`
- `暂停，稍后继续`

## 第三步：图表和强制引用验证

所有节完成后，先处理图表，再**强制**进行引用验证：

> 正文已完成。接下来：

选项：
- `生成图表（architecture diagram、结果对比图）`
- `跳过图表，直接做引用验证`

**图表（可选）：**

调用 `inno-figure-gen` skill，生成 2-3 个关键图表到 `assets/figures/`。

---

### 🔴 引用验证（强制，不可跳过）

> **本条步骤优先级最高，不可跳过，不可省略。未通过验证前，严禁进入 /omp:review 或 /omp:export。**

**第一步：运行 inno-reference-audit**

调用 `inno-reference-audit` skill，检查所有 `\cite{}` 引用：

```bash
# 提取所有引用 key
grep -oh '\cite[^}]*' paper/sections/*.tex 2>/dev/null | grep -oh '{[^}]*}' | tr -d '{}' | tr ',' '\n' | sort -u

# 对照 references.bib 检查
if [ -f references.bib ]; then
  for key in $(grep -oh '\cite[^}]*' paper/sections/*.tex 2>/dev/null | grep -oh '{[^}]*}' | tr -d '{}' | tr ',' '\n' | sort -u); do
    grep -q "^@.*{$key," references.bib || echo "❌ FAKE: $key"
  done
fi
```

**第二步：运行 verify-citations.py（如果依赖可用）**

```bash
# 安装依赖（如未安装）
pip3 install bibtexparser semanticscholar arxiv requests 2>/dev/null || echo "⚠️ 依赖安装失败，跳过脚本验证"

# 运行验证
python3 skills/inno-reference-audit/scripts/verify-citations.py references.bib 2>/dev/null || \
python3 plugins/oh-my-paper/skills/inno-reference-audit/scripts/verify-citations.py references.bib 2>/dev/null || \
echo "⚠️ verify-citations.py 未运行"
```

**第三步：用 `AskUserQuestion` 展示验证结果**

> **引用验证结果**（必须确认后继续）
>
> - 总引用数：{total}
> - ✅ 可验证：{verified}
> - ❌ 无法验证：{fake}
>
> {如果 fake > 0：}
> ❌ 以下引用无法验证，必须处理：
> {列出所有 fake citation key}
>
> 选项：
> - `删除假引用，替换为 [CITATION NEEDED]` ✅ 推荐
> - `我来补充真实参考文献`
> - `暂停，我自己检查`

**验证不通过时的处理：**
- 删除所有无法验证的 `\cite{key}`，替换为 `[CITATION NEEDED]`
- 更新 `references.bib`，只保留被引用的真实条目
- **严禁在验证不通过时继续推进**



### 3.1 新增：证据一致性检查（仅 Mega 模式）

在进入质量门控前，运行证据一致性检查：

```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/constraints.mjs" paper
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
# 检查论文章节
ls paper/sections/*.tex 2>/dev/null
# 字数统计（如果 LaTeX 文件存在）
wc -w paper/sections/*.tex 2>/dev/null | tail -1
# 检查消融实验
grep -c "ablation" paper/sections/experiments.tex 2>/dev/null || echo "0"
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

## 错误处理

执行过程中遇到以下情况请统一处理：

| 场景 | 处理方式 |
|------|---------|
| 文件或目录不存在 | 提示用户："⚠️ 未找到 {文件名}，请检查是否已完成前置步骤" |
| 命令执行失败 | 提示用户："⚠️ 执行失败：{错误原因}，请检查后重试" 并提供重试/跳过/退出选项 |
| 用户输入无效 | 提示用户："❌ 无效选项，请重新选择" 并重新展示选项 |
| 其他意外错误 | 提示用户："⚠️ 发生意外错误：{描述}，[重试] [返回] [退出]" |

所有交互均使用 AskUserQuestion 工具，不要用纯文字替代。

