---
id: omp:journal-analyze
name: omp:journal-analyze
version: 1.0.0
description: 期刊分析工具 - 分析期刊的题材偏好、标题风格、行文风格、实证性、创新性
stages: [A4, B11]
tools: [read_file, write_file, Bash]
tracker: writes to .my-paper/journals/{journal-id}/analysis/
---

# omp:journal-analyze - 期刊分析

分析特定期刊的论文，提取期刊偏好和风格特征，辅助用户调整写作策略以符合期刊要求。

## 调用方式

```
/omp:journal-analyze --journal {journal-id} --aspects {aspects} --output {format}
```

### 参数说明

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--journal` | 是 | 目标期刊 ID | `computers-and-education` 或 `computer-science-china` |
| `--aspects` | 否 | 分析方面（逗号分隔） | `topic,title,style,empirical,innovation` |
| `--output` | 否 | 输出格式（markdown/json/yaml） | `markdown` |
| `--max-papers` | 否 | 最大分析论文数（默认全部） | `50` |

**分析方面选项**：
- `topic` - 题材偏好（研究主题分布）
- `title` - 标题风格（长度、结构、关键词）
- `style` - 行文风格（章节结构、语言特点）
- `empirical` - 实证性分析（理论 vs 实证）
- `innovation` - 创新性评估（方法论创新、应用创新）

## 阶段

**A4 - KNOWLEDGE_EXTRACT**：从论文中提取特征
**B11 - SYNTHESIS**：综合分析结果，生成期刊画像

## 任务

1. 读取期刊数据库（`.my-paper/journals/{journal-id}/papers/`）
2. 对每篇论文提取特征（标题、摘要、章节结构、关键词等）
3. 执行分析：
   - **题材偏好**：LDA 主题建模或关键词聚类
   - **标题风格**：统计标题长度、结构模式、高频词
   - **行文风格**：分析章节结构、语言特点（被动语态、专业术语密度等）
   - **实证性**：判断论文是理论型还是实证型
   - **创新性**：评估方法论创新、应用创新、引用潜力
4. 生成分析报告，保存到 `.my-paper/journals/{journal-id}/analysis/`
5. 生成期刊画像（用户画像），保存到 `.pipeline/memory/journal_profile.md`

## Tracker 集成

### 读
- `.my-paper/journals/{journal-id}/papers/*.yaml` — 读取论文元数据
- `.my-paper/journals/{journal-id}/papers/*.md` — 读取论文全文（可选）

### 写
- `.my-paper/journals/{journal-id}/analysis/style-profile.yaml` — 标题风格、行文风格
- `.my-paper/journals/{journal-id}/analysis/topic-distribution.yaml` — 题材偏好
- `.my-paper/journals/{journal-id}/analysis/empirical-tendency.yaml` — 实证性分析
- `.my-paper/journals/{journal-id}/analysis/innovation-metrics.yaml` — 创新性评估
- `.pipeline/memory/journal_profile.md` — 期刊画像（用户画像）
- `.pipeline/memory/style_guide.md` — 写作风格指南

## 分析方法

### 1. 题材偏好分析
**方法**：
- **LDA 主题建模**（适合大规模数据）：使用 `scikit-learn` 的 LatentDirichletAllocation
- **关键词聚类**（适合小规模数据）：使用 TF-IDF + KMeans
- **手工分类**（备用）：基于领域知识预定义类别

**输出**：
```yaml
topic_distribution:
  - topic: "深度学习"
    keywords: ["deep learning", "neural network", "CNN"]
    percentage: 35.2
  - topic: "自然语言处理"
    keywords: ["NLP", "Transformer", "LLM"]
    percentage: 28.7
  - topic: "计算机视觉"
    keywords: ["computer vision", "image recognition", "object detection"]
    percentage: 21.3
  - topic: "其他"
    percentage: 14.8
```

### 2. 标题风格分析
**分析维度**：
- **长度**：字符数、单词数
- **结构**：陈述句 vs 疑问名 vs 冒号分隔
- **关键词**：高频词、领域术语
- **时态**：现在时 vs 过去时

**输出**：
```yaml
title_style:
  avg_length: 45  # 字符数
  length_range: [20, 80]
  structure:
    declarative: 0.65  # 陈述句比例
    interrogative: 0.05  # 疑问句比例
    colon_separated: 0.30  # 冒号分隔比例
  common_patterns:
    - "基于...的..."
    - "...研究"
    - "...应用"
  high_freq_words: ["基于", "研究", "分析", "设计", "实现"]
```

### 3. 行文风格分析
**分析维度**：
- **章节结构**：常见章节、章节顺序
- **语言特点**：被动语态比例、专业术语密度、句子长度
- **引用风格**：引用格式、引用密度

**输出**：
```yaml
writing_style:
  common_sections:
    - "摘要"
    - "引言"
    - "相关工作"
    - "方法"
    - "实验"
    - "结论"
  section_order: ["摘要", "引言", "相关工作", "方法", "实验", "结论"]
  language_features:
    passive_voice_ratio: 0.42
    avg_sentence_length: 28.5  # 单词数
    technical_term_density: 0.15  # 专业术语密度
  citation_style: "GB/T 7714"
  avg_citations_per_paper: 25
```

### 4. 实证性分析
**判断依据**：
- 是否有实验部分（`experiment` 或 `实验` 章节）
- 是否有数据集描述
- 是否有结果分析（`results` 或 `结果` 章节）
- 关键词匹配（"实验"、"数据集"、"评估"、"验证"等）

**输出**：
```yaml
empirical_tendency:
  empirical_ratio: 0.78  # 实证论文比例
  theoretical_ratio: 0.22  # 理论论文比例
  common_datasets: ["ImageNet", "GLUE", "SQuAD"]
  evaluation_metrics: ["accuracy", "F1-score", "BLEU"]
```

### 5. 创新性评估
**评估维度**：
- **方法论创新**：是否提出新方法、新模型、新算法
- **应用创新**：是否将现有方法应用到新领域
- **引用潜力**：基于引用网络的预测（如果有数据）

**输出**：
```yaml
innovation_metrics:
  avg_innovation_score: 0.72  # 0-1，越高越创新
  methodology_innovation_ratio: 0.45  # 方法论创新比例
  application_innovation_ratio: 0.55  # 应用创新比例
  common_contributions:
    - "提出新方法"
    - "改进现有模型"
    - "跨领域应用"
```

## 约束

- MUST NOT 修改原始论文数据
- MUST NOT 伪造分析结果
- 对于无法分析的论文，记录警告并跳过
- 分析结果应基于实际数据，避免主观判断

## 示例调用

### 示例 1：全方面分析 Computers & Education 期刊
```
/omp:journal-analyze --journal computers-and-education
```

### 示例 2：仅分析标题风格和行文风格
```
/omp:journal-analyze --journal computers-and-education --aspects title,style
```

### 示例 3：分析前 50 篇论文，输出 JSON 格式
```
/omp:journal-analyze --journal computers-and-education --max-papers 50 --output json
```

## 输出示例

### 期刊画像（journal_profile.md）

```markdown
# 期刊画像：Computers & Education

## 基本信息
- **期刊名称**：Computers & Education
- **出版社**：Elsevier
- **ISSN**：0360-1315
- **影响因子**：11.9 (2023)
- **分析论文数**：50 篇
- **分析时间**：2026-05-02

## 题材偏好
该期刊主要关注以下研究主题：
1. **AI in Education**（32.5%）：包括智能辅导系统、学习分析、教育 AI 应用
2. **在线与混合学习**（28.3%）：包括在线学习平台、混合教学模式、学习效果评估
3. **教育技术研究**（21.8%）：包括教育技术设计、技术接受模型、用户体验
4. **语言学习技术**（12.4%）：包括计算机辅助语言学习（CALL）、语音识别应用
5. **STEM 教育**（5.0%）：包括科学、技术、工程、数学教育中的技术应用

## 标题风格
- **平均长度**：12 个单词
- **常见结构**：45% 使用冒号分隔主副标题，30% 为疑问句，25% 为描述性标题
- **常用模式**：冒号分隔（"Enhancing...: A ..."）、疑问句（"What makes..."）
- **高频词**：enhancing, effectiveness, impact, students, learning, AI, online

## 行文风格
- **常见章节**：Abstract, Introduction, Literature Review, Methodology, Results, Discussion, Conclusions
- **语言特点**：被动语态比例 35%，平均句长 22.5 词，强调实证研究
- **引用格式**：APA 7th Edition
- **平均引用数**：45 篇/篇

## 实证性倾向
- **实证论文比例**：85%
- **理论/综述比例**：15%
- **常用数据集**：K-12 学生、大学生、在线学习平台用户
- **评估方法**：定量（回归、ANOVA、t-test）、定性（访谈、观察）、混合方法

## 创新性要求
- **平均创新评分**：0.75/1.0
- **方法论创新**：40%（新干预设计、新测量工具）
- **应用创新**：60%（新技术在教育场景的应用）
- **常见贡献类型**：验证技术效果、提出新教学模式、开发学习工具

## 投稿建议
1. 标题建议使用冒号分隔结构或疑问句形式
2. 必须包含实证研究，有明确的假设和研究问题
3. Methodology 部分必须详细描述参与者、数据收集工具、分析方法
4. Results 部分必须包含统计分析结果（p-value、effect size）
5. Discussion 部分必须讨论实践意义（practical implications）
6. 引用格式必须符合 APA 7th Edition
7. 强调技术在教育中的应用效果和局限性

### 写作风格指南（style_guide.md）

```markdown
# 写作风格指南：Computers & Education

## 标题
- 长度：8-15 个单词
- 结构：推荐使用冒号分隔或疑问句
- 示例：
  - "Enhancing student engagement through AI: A mixed-methods study"
  - "What makes a good online teacher? Student perceptions and expectations"
  - "Learning analytics in higher education: A systematic review"

## Abstract
- 长度：150-250 词
- 结构：Purpose, Methods, Results, Conclusions
- 语言：简洁、客观、避免主观评价
- 必须包含：研究问题、方法、主要发现、实践意义

## Introduction
- 必须包含：研究背景、问题陈述、研究目标、研究问题/假设、主要贡献
- 长度：建议 2-3 页
- 引用：必须引用最新相关研究（近 5 年）

## Literature Review
- 必须包含：理论框架、相关研究综述、研究空白
- 结构：按主题组织，而非按作者罗列
- 批判性分析：指出前人研究的局限性

## Methodology
- 必须包含：研究设计、参与者描述、数据收集工具、数据分析方法
- 细节程度：其他研究者可以复现
- 伦理考虑：必须说明伦理审查批准（如适用）

## Results
- 必须包含：描述性统计、推断性统计、效应量
- 表格/图表：清晰、标注完整、符合 APA 格式
- 避免：主观解释（留在 Discussion）

## Discussion
- 必须包含：主要发现解释、与文献对比、实践意义、研究局限、未来研究建议
- 长度：建议 3-5 页
- 强调：实践意义（practical implications）和政策建议

## Conclusions
- 长度：0.5-1 页
- 内容：主要发现总结、实践意义、未来研究方向
- 避免：重复 Abstract 或 Discussion 内容

## 引用格式
- 必须使用 APA 7th Edition 格式
- DOI：尽可能提供
- 英文文献：必须包含 DOI 或 URL
```
