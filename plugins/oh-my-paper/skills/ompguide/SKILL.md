---
description: 交互式教程，用模拟项目引导新用户熟悉 OMP 全流程
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Oh My Paper 交互式教程引导员。

## 参数解析

用户可能输入：
- `/ompguide` — 完整教程
- `/ompguide --skip-intro` — 跳过介绍
- `/ompguide --quick` — 快速模式（合并部分步骤）

将参数存入变量 `skipIntro` 和 `quickMode`。

## 全局设定

**模拟项目目录**：`.omp-tutorial/`（教程结束后提示用户删除）
**模拟研究主题**：`基于视觉变换器的多模态医学影像分割`
**模拟目录**：当前工作目录下的 `.omp-tutorial/`

---

## 第 1 步：欢迎介绍

（如果 `--skip-intro` 参数存在，跳到**第 2 步**）

用 `AskUserQuestion` 展示：

```
═══════════════════════════════════════════════════════════
  欢迎使用 Oh My Paper 交互式教程！
═══════════════════════════════════════════════════════════

OMP (Oh My Paper) 是一个 AI 驱动的学术研究助手，
帮你完成从选刊到论文发表的全流程。

本教程将用「模拟项目」带你体验核心功能。
教程分两个阶段：
  阶段一：选题准备（选刊 → 定方案）
  阶段二：研究写作（调研 → 实验 → 写作 → 投稿）

预计耗时：约 5 分钟

选项：[开始教程] [跳过介绍] [退出]
```

如果选 `跳过介绍`，直接跳到**第 2 步**。
如果选 `退出`，停止。

---

## 第 2 步：模拟项目初始化

> **第 2/7 步：项目初始化**
>
> 正在创建模拟项目...

### 创建目录结构

```bash
# 创建模拟项目目录
mkdir -p .omp-tutorial/.pipeline/memory
mkdir -p .omp-tutorial/.pipeline/tasks
mkdir -p .omp-tutorial/.pipeline/docs

# 创建模拟 research_brief.json
cat > .omp-tutorial/.pipeline/docs/research_brief.json << 'EOF'
{
  "topic": "基于视觉变换器的多模态医学影像分割",
  "goal": "提出一种融合 MRI 和 CT 的多模态分割模型，在 BraTS 数据集上 Dice 提升 3%",
  "currentStage": "survey",
  "successThreshold": "Dice > 0.90，Hausdorff95 < 5mm，在 3 个数据集上验证",
  "mode": "Legacy"
}
EOF

# 创建模拟 project_truth.md
cat > .omp-tutorial/.pipeline/memory/project_truth.md << 'EOF'
# Project Truth

## 研究主题
基于视觉变换器（Vision Transformer）的多模态医学影像分割

## 核心问题
现有方法在 Brats 2023 数据集上 Dice < 0.85，且对 MRI/CT 模态融合不充分

## 已确认决策
- 2026-04-10：决定使用 Swin U-Net 作为基础架构
- 2026-04-12：决定融合 T1、T2、FLAIR 三种 MRI 序列
EOF

# 创建模拟 tasks.json
cat > .omp-tutorial/.pipeline/tasks/tasks.json << 'EOF'
{
  "version": 1,
  "tasks": [
    {"id": "1", "stage": "survey", "description": "搜索多模态医学影像分割相关论文", "status": "done"},
    {"id": "2", "stage": "survey", "description": "整理 literature_bank.md", "status": "done"},
    {"id": "3", "stage": "ideation", "description": "分析研究空白，生成创新点", "status": "in_progress"},
    {"id": "4", "stage": "ideation", "description": "撰写 hypothesis.md", "status": "pending"},
    {"id": "5", "stage": "experiment", "description": "设计实验方案", "status": "pending"}
  ]
}
EOF

# 创建模拟 literature_bank.md
cat > .omp-tutorial/.pipeline/memory/literature_bank.md << 'EOF'
# Literature Bank

## 1. Swin U-Net: U-Net-like Pure Transformer for Medical Image Segmentation

- **Authors**: Hu Cao, Yueyue Wang, Joy Chen, Dongsheng Jiang, Xiaopeng Zhang, Qi Tian, Manning Wang
- **Year**: 2022
- **Venue**: IEEE Transactions on Medical Imaging
- **DOI**: 10.1109/TMI.2022.3182231
- **Summary**: 提出 Swin U-Net 架构，将 Swin Transformer 与 U-Net 结合，在医学影像分割任务上表现优异。
- **Relevance**: 核心基础架构
- **Notes**: 我们的方法基于此架构改进

## 2. TransFuse: Fusing Transformers and CNNs for Medical Image Segmentation

- **Authors**: Yundong Zhang, Huiye Liu, Qiang Hu
- **Year**: 2021
- **Venue**: MICCAI 2021
- **DOI**: 10.1007/978-3-030-87199-4_28
- **Summary**: 提出 TransFuse，将 Transformer 的全局建模能力和 CNN 的局部特征提取能力结合。
- **Relevance**: 重要参考
- **Notes**: 模态融合部分可借鉴

## 3. Multi-modal Brain Tumor Segmentation using Transformer

- **Authors**: Wenxuan Wang, Chen Chen, Meng Ding, Hong Yu, Sen Zeng, Hong Qin
- **Year**: 2023
- **Venue**: Medical Image Analysis
- **DOI**: 10.1016/j.media.2022.102595
- **Summary**: 提出基于 Transformer 的多模态脑肿瘤分割方法，利用跨模态注意力机制。
- **Relevance**: 最直接相关工作
- **Notes**: 我们的创新点在于改进其跨模态注意力模块

## 4. Vision Transformer for Medical Image Analysis: A Review

- **Authors**: Yutong Xie, Quanzheng Li
- **Year**: 2022
- **Venue**: Medical Image Analysis
- **DOI**: 10.1016/j.media.2022.102586
- **Summary**: 综述 Vision Transformer 在医学影像分析中的应用。
- **Relevance**: 背景综述
- **Notes**: 可作为 Related Work 部分参考

## 5. nnU-Net: A Self-configuring Method for Deep Learning-based Biomedical Image Segmentation

- **Authors**: Fabian Isensee, Paul F. Jaeger, Simon A.A. Kohl, Jens Petersen, Klaus H. Maier-Hein
- **Year**: 2021
- **Venue**: Nature Methods
- **DOI**: 10.1038/s41592-020-01008-z
- **Summary**: 提出 nnU-Net，自动配置深度学习模型用于生物医学图像分割。
- **Relevance**: 重要基线方法
- **Notes**: 我们的方法需要与 nnU-Net 对比
EOF

# 创建模拟 decision_log.md
cat > .omp-tutorial/.pipeline/memory/decision_log.md << 'EOF'
# Decision Log

## 2026-04-10: 选择基础架构

- **Context**: 需要选择合适的基础网络架构
- **Decision**: 使用 Swin U-Net 作为基础架构
- **Rationale**: Swin Transformer 在医学影像分割上表现优异，且开源实现完善
- **Alternatives considered**: U-Net、Attention U-Net、TransUNet

## 2026-04-12: 模态融合策略

- **Context**: 如何有效融合多模态 MRI 数据
- **Decision**: 使用跨模态注意力机制（Cross-Modal Attention）
- **Rationale**: 允许模型自适应地学习不同模态间的关系
- **Alternatives considered**: 早期融合、晚期融合、加权求和
EOF
```

创建完成后，展示：

```
模拟项目已创建：`.omp-tutorial/`

项目结构：
  .omp-tutorial/
    .pipeline/
      docs/research_brief.json   ← 研究简介
      memory/project_truth.md    ← 项目真相文档
      memory/literature_bank.md ← 文献库（5 篇）
      memory/decision_log.md    ← 决策日志
      tasks/tasks.json          ← 任务列表
```

用 `AskUserQuestion` 继续：

> **模拟项目已就绪！**
>
> 上面的文件模拟了一个真实研究项目的状态。
> 接下来将按两阶段展示 OMP 的核心功能。
>
> 选项：[下一步：选刊] [快速浏览全部] [退出教程]

如果 `--quick` 参数存在，合并此步和下一步。

---

## 第 3 步：期刊选刊演示

> **第 3/7 步：期刊选刊（阶段一：选题准备）**
>
> 写论文前先确定目标期刊。期刊决定格式要求、方向侧重、审稿难度和发表周期。
> 选刊是写作前的准备，不是写作中的步骤。

### 展示模拟选刊结果

```
模拟选刊结果（由 /journal-research-orchestrator 生成）

基于研究主题「基于视觉变换器的多模态医学影像分割」：

主投期刊：
  1. Medical Image Analysis (IF: 10.7, Q1)
     - 方向匹配度：95%（医学影像分析核心期刊）
     - 审稿周期：约 3 个月
     - APC：$3,400

  2. IEEE Transactions on Medical Imaging (IF: 10.6, Q1)
     - 方向匹配度：90%（医学影像领域顶刊）
     - 审稿周期：约 4 个月
     - APC：无（传统订阅期刊）

备选期刊：
  3. NeuroImage (IF: 4.7, Q1) — 影像+神经科学交叉
  4. Computerized Medical Imaging and Graphics (IF: 5.4, Q2)

不建议：
  5. PLOS ONE — 虽然容易发表但不利于学术声誉建立
```

### 解释选刊命令

> 在真实项目中，你可以运行：
> ```
> /journal-research-orchestrator     # 英文/SCI 期刊选刊
> /cn-orchestrator                   # 中文核心期刊选刊
> /ai-journal-match                  # AI 智能匹配
> /letpub-sci-journal-review         # 查看期刊画像（IF/分区/审稿周期）
> /predatory-risk-check              # 掠夺刊风险筛查
> ```
> 选刊流程会根据你的研究主题自动：
> 1. 探索相关期刊（OpenAlex / Crossref）
> 2. 深度分析候选期刊（影响因子、审稿周期、APC、收录情况）
> 3. 筛查掠夺刊风险
> 4. 推荐 2 主投 + 2 备选 + 1 不建议

### 解释为什么选刊在前

> **为什么选刊必须在研究之前？**
> - 不同期刊对创新程度、实验规模、写作风格的要求不同
> - 确定期刊后可以针对性设计实验和调整研究方案
> - 避免写完论文才发现不符合目标期刊的格式或方向要求

用 `AskUserQuestion` 继续：

> **选刊演示完成（模拟）**
>
> 选刊是阶段一的核心。确定目标期刊后进入阶段二：研究写作。
>
> 选项：[下一步：文献调研] [快速浏览] [退出教程]

---

## 第 4 步：文献调研演示

> **第 4/7 步：文献调研（阶段二：研究写作 — 第 1 步）**
>
> 文献调研是研究的起点。
> OMP 通过 `/omp:survey` 命令帮你搜索、筛选和整理文献。

### 展示模拟文献库

读取 `.omp-tutorial/.pipeline/memory/literature_bank.md`，以表格形式展示：

```
模拟文献库（literature_bank.md）

| # | 论文标题 | 年份 | 相关度 |
|---|---------|------|--------|
| 1 | Swin U-Net | 2022 | 极高 |
| 2 | TransFuse | 2021 | 高 |
| 3 | Multi-modal Brain Tumor Segmentation using Transformer | 2023 | 极高 |
| 4 | Vision Transformer for Medical Image Analysis: A Review | 2022 | 中 |
| 5 | nnU-Net | 2021 | 高 |
```

### 解释 /omp:survey 命令

> 在真实项目中，你可以运行：
> ```
> /omp:survey
> ```
> 它会：
> 1. 根据 `research_brief.json` 中的主题搜索论文
> 2. 自动筛选高质量论文（引用数、期刊等级）
> 3. 生成 `literature_bank.md`（如上所示）
> 4. 生成 `search_strategy.yaml`（搜索策略记录）

用 `AskUserQuestion` 继续：

> **文献调研已完成（模拟）**
>
> 下一步：从文献中发现研究空白，生成创新点。
>
> 选项：[下一步：创新点生成] [快速浏览] [退出教程]

---

## 第 5 步：创新点生成演示

> **第 5/7 步：创新点生成（阶段二 — 第 2 步）**
>
> 从文献中发现研究空白，生成可验证的创新点。
> OMP 通过 `/omp:ideate` 命令驱动。

### 展示模拟创新点

```
模拟创新点（由 /omp:ideate 生成）

研究空白：
现有方法（如 [3]）的跨模态注意力模块计算复杂度高（O(n^2)），
且在模态缺失时性能下降明显。

创新点：
提出「轻量级跨模态注意力（LCA）」模块：
1. 将复杂度降至 O(n sqrt(n))
2. 引入模态缺失鲁棒性机制
3. 在 Brats 2023 数据集上验证

假设：
LCA 模块能在保持分割精度的同时，将推理速度提升 2x，
并在模态缺失 30% 时性能下降 < 5%。
```

### 解释 /omp:ideate 命令

> 在真实项目中，你可以运行：
> ```
> /omp:ideate
> ```
> 它会：
> 1. 分析 `literature_bank.md` 发现研究空白
> 2. 生成多个创新点（由 AI 辩论评选最佳）
> 3. 输出 `hypothesis.md`（假设文档）
> 4. 更新 `project_truth.md`

用 `AskUserQuestion` 继续：

> **创新点已生成（模拟）**
>
> 下一步：查看当前研究进度。
>
> 选项：[下一步：查看进度] [退出教程]

---

## 第 6 步：进度查看演示

> **第 6/7 步：进度查看**
>
> OMP 提供可视化进度条，帮你了解项目状态。
> 运行 `/omp:progress` 查看。

### 展示模拟进度

读取 `.omp-tutorial/.pipeline/tasks/tasks.json` 和 `research_brief.json`，模拟进度输出：

```
═══════════════════════════════════════════════════════════
  Oh My Paper — 进度总览
═══════════════════════════════════════════════════════════
  主题：基于视觉变换器的多模态医学影像分割
  模式：Legacy  |  当前阶段：ideation (2/5)

  Survey      ████████████████████ 100%  已完成
  Ideation    ████████░░░░░░░░░░  40%  进行中
  Experiment  ░░░░░░░░░░░░░░░░░░░   0%  待开始
  Publication ░░░░░░░░░░░░░░░░░░░   0%  待开始
  Promotion   ░░░░░░░░░░░░░░░░░░░   0%  待开始

  进行中任务：1  |  已完成：2  |  待开始：2
═══════════════════════════════════════════════════════════
```

### 解释进度条含义

> **进度条解读**：
> - `█` = 已完成   `░` = 未完成
>
> **5 个阶段**：
> 1. `Survey` — 文献调研
> 2. `Ideation` — 创新点生成
> 3. `Experiment` — 实验设计与运行
> 4. `Publication` — 论文写作
> 5. `Promotion` — 投稿与推广

用 `AskUserQuestion` 继续：

> **进度查看完成**
>
> 选项：[下一步：总结] [退出教程]

---

## 第 7 步：总结与下一步

> **第 7/7 步：总结**
>
> 你已经了解了 OMP 的完整工作流！

```
═══════════════════════════════════════════════════════════
  教程完成！
═══════════════════════════════════════════════════════════

  你已体验的功能：
  [阶段一：选题准备]
  - 期刊选刊（/journal-research-orchestrator）
  - 研究计划（/omp:plan）

  [阶段二：研究写作]
  - 文献调研（/omp:survey）
  - 创新点生成（/omp:ideate）
  - 进度查看（/omp:progress）

  推荐的完整工作流：
  1. 先选刊：/journal-research-orchestrator
  2. 初始化：/omp:setup
  3. 做调研：/omp:survey
  4. 找创新：/omp:ideate
  5. 做实验：/omp:experiment
  6. 写论文：/omp:write
  7. 评审：  /omp:review
  8. 导出：  /omp:export

  模拟项目位于 .omp-tutorial/ 目录
  查看完毕后可以删除：rm -rf .omp-tutorial/
═══════════════════════════════════════════════════════════
```

用 `AskUserQuestion` 提供最后选项：

> **教程结束！**
>
> 选项：
> - `查看模拟文件` — 在编辑器中打开 `.omp-tutorial/` 目录
> - `删除模拟项目` — 运行 `rm -rf .omp-tutorial/`
> - `结束教程` — 退出

如果选 `查看模拟文件`：

```bash
open .omp-tutorial/ 2>/dev/null || echo "请用文件管理器打开 .omp-tutorial/ 目录"
```

如果选 `删除模拟项目`：

```bash
rm -rf .omp-tutorial/
echo "模拟项目已删除"
```

---

## 快速模式（--quick）

如果 `--quick` 参数存在，将步骤合并为 3 步：

1. **欢迎 + 项目初始化 + 选刊**（合并第 1、2、3 步）
2. **核心功能演示**（合并第 4、5、6 步，只展示最关键的输出）
3. **总结**（第 7 步）

---

## 错误处理

### .omp-tutorial/ 目录已存在

> 模拟项目目录 `.omp-tutorial/` 已存在。是否删除并重新创建？

选项：`重新创建` / `使用现有项目继续` / `退出`

如果选 `重新创建`：

```bash
rm -rf .omp-tutorial/
# 然后重新执行第 2 步
```

### 用户中途退出

任何时候用户选择 `退出教程`，执行：

> 教程已退出。
>
> 模拟项目保存在 `.omp-tutorial/`，你可以随时查看或删除。
> 重新运行 `/omp:guide` 可以重新开始教程。

---

## 教程结束后

无论正常完成还是中途退出，都在 `.omp-tutorial/` 中留下一个标记文件：

```bash
echo "Guide completed at $(date)" > .omp-tutorial/.guide-completed
```

下次运行 `/omp:guide` 时，检测到此文件可以询问用户是否重新开始。
