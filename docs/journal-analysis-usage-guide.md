# 期刊论文分析系统 - 完整使用指南

> **系统版本**: 1.0.0  
> **最后更新**: 2026-05-02  
> **适用期刊**: Computers & Education、中国科学、计算机学报等

---

## 📋 目录

1. [系统简介](#系统简介)
2. [安装与配置](#安装与配置)
3. [快速开始](#快速开始)
4. [添加期刊](#添加期刊)
5. [爬取论文](#爬取论文)
6. [分析期刊](#分析期刊)
7. [使用分析结果](#使用分析结果)
8. [高级功能](#高级功能)
9. [故障排除](#故障排除)

---

## 系统简介

**期刊论文分析系统**帮助你：

- 📥 **爬取论文**：从 arXiv、Semantic Scholar、PubMed 自动爬取期刊论文
- 📊 **分析期刊**：分析期刊的选题偏好、标题风格、行文风格、实证性倾向
- 📝 **辅助写作**：根据期刊风格调整你的论文写作
- 🔍 **文献综述**：生成文献综述时考虑期刊偏好

### 核心概念

| 术语 | 说明 | 示例 |
|------|------|------|
| **期刊 ID** | 期刊的唯一标识符 | `computers-and-education`、`computer-science-china` |
| **期刊数据库** | 存储期刊论文的目录 | `.my-paper/journals/{journal-id}/` |
| **论文元数据** | YAML 格式的论文信息 | `papers/xxx.yaml` |
| **论文全文** | Markdown 格式的论文全文 | `papers/xxx.md` |
| **期刊画像** | 分析生成的期刊特征报告 | `analysis/journal_profile.md` |
| **风格指南** | 基于分析的写作建议 | `analysis/style_guide.md` |

---

## 安装与配置

### 1. 依赖安装

```bash
# 核心依赖
pip install requests pyyaml

# 可选依赖（推荐）
pip install xml.etree.ElementTree numpy nltk

# PDF 解析（如果需要处理 PDF）
pip install pdfplumber PyMuPDF
```

### 2. 目录结构检查

确保你的项目目录结构如下：

```
Oh-my--paper/
├── .my-paper/
│   └── journals/              # 期刊数据库根目录
│       └── {journal-id}/     # 单个期刊数据
│           ├── metadata.yaml  # 期刊元数据
│           ├── papers/        # 论文数据
│           └── analysis/     # 分析结果
│
├── skills/
│   ├── omp:journal-crawl/   # 论文爬取技能
│   ├── omp:journal-analyze/ # 期刊分析技能
│   └── omp:knowledge-base/  # 知识库管理技能
│
└── docs/
    └── journal-analysis-usage-guide.md  # 本文档
```

---

## 快速开始

### 示例：分析 Computers & Education 期刊

#### 步骤 1：添加期刊配置

创建 `.my-paper/journals/computers-and-education/metadata.yaml`：

```yaml
journal:
  id: "computers-and-education"
  name: "Computers & Education"
  publisher: "Elsevier"
  issn: "0360-1315"
  impact_factor: 11.9
  
  data_sources:
    - name: "Semantic Scholar"
      method: "API"
      enabled: true
    
    - name: "Manual Upload"
      method: "PDF Upload"
      enabled: true
```

#### 步骤 2：爬取论文

**方法 A：使用 API 自动爬取**

```bash
# 从 Semantic Scholar 爬取
python skills/omp:journal-crawl/scripts/crawl.py \
  --journal computers-and-education \
  --source semantic-scholar \
  --query "AI in education" \
  --max 30 \
  --year-from 2022
```

**方法 B：手动上传 PDF（推荐）**

```bash
# 1. 将 PDF 文件放到一个目录
mkdir -p ~/Downloads/computers-and-education-pdfs
# 2. 将你下载的 PDF 复制到这个目录
# 3. 运行爬取脚本
python skills/omp:journal-crawl/scripts/crawl.py \
  --journal computers-and-education \
  --source manual \
  --pdf-dir ~/Downloads/computers-and-education-pdfs/
```

#### 步骤 3：分析期刊

```bash
# 全方面分析
python skills/omp:journal-analyze/scripts/demo_analysis.py

# 或使用完整分析脚本
python skills/omp:journal-analyze/scripts/style_analysis.py \
  --journal computers-and-education

python skills/omp:journal-analyze/scripts/empirical_analysis.py \
  --journal computers-and-education
```

#### 步骤 4：查看分析结果

分析完成后，查看以下文件：

```
.my-paper/journals/computers-and-education/analysis/
├── journal_profile.md      # 期刊画像（选题偏好、标题风格等）
├── style_guide.md         # 写作风格指南
├── topic-distribution.yaml # 选题分布
├── style-profile.yaml      # 标题和行文风格
└── empirical-tendency.yaml # 实证性倾向
```

---

## 添加期刊

### 方法 1：手动创建配置文件

在 `.my-paper/journals/` 下创建期刊目录和元数据文件：

```bash
# 创建目录
mkdir -p .my-paper/journals/{journal-id}/papers
mkdir -p .my-paper/journals/{journal-id}/analysis

# 创建元数据文件
touch .my-paper/journals/{journal-id}/metadata.yaml
```

然后编辑 `metadata.yaml`（参考模板见下方）。

### 方法 2：使用脚本生成

```bash
# 运行模拟数据生成器（会创建目录结构和模板）
python skills/omp:journal-crawl/scripts/generate_sample_data.py
```

### 元数据模板

```yaml
# .my-paper/journals/{journal-id}/metadata.yaml

journal:
  id: "computers-and-education"
  name: "Computers & Education"
  full_name: "Computers & Education"
  publisher: "Elsevier"
  issn: "0360-1315"
  eissn: "1873-782X"
  url: "https://www.sciencedirect.com/journal/computers-and-education"
  
  impact_factor: 11.9
  h_index: 185
  
  subject_categories:
    - "Education & Educational Research"
    - "Computer Science Applications"
  
  # 数据获取配置
  data_sources:
    - name: "Semantic Scholar"
      method: "API"
      enabled: true
      rate_limit: "100 requests/5min"
    
    - name: "Manual Upload"
      method: "PDF Upload"
      enabled: true
  
  # 爬取配置
  crawl_config:
    default_source: "semantic-scholar"
    filters:
      year_from: 2020
      year_to: 2026
  
  # 分析配置
  analysis_config:
    aspects:
      - "topic"
      - "title"
      - "style"
      - "empirical"
      - "innovation"

# 统计信息（自动更新）
stats:
  paper_count: 0
  last_updated: null
  year_distribution: {}
  topic_distribution: {}

created_at: "2026-05-02T09:00:00+08:00"
```

---

## 爬取论文

### 数据源对比

| 数据源 | 适用场景 | 优点 | 限制 |
|--------|----------|------|------|
| **arXiv API** | 预印本论文（CS/物理/数学） | 免费、开放获取、API 稳定 | 仅包含 arXiv 论文 |
| **Semantic Scholar API** | 已发表论文（全学科） | 元数据丰富、支持期刊过滤 | 速率限制（100次/5分钟） |
| **PubMed API** | 生物医学期刊 | 数据权威、官方 API | 仅限生物医学领域 |
| **手动上传** | 所有期刊（推荐） | 无速率限制、数据完整 | 需要手动下载 PDF |

### 使用方法

#### 1. arXiv API

```bash
python skills/omp:journal-crawl/scripts/crawl.py \
  --journal computers-and-education \
  --source arxiv \
  --query "AI in education" \
  --max 20 \
  --year-from 2023
```

**输出示例**：
```
正在从 arXiv 搜索: AI in education
✓ 从 arXiv 获取到 15 篇论文
✓ 已保存元数据: .my-paper/journals/computers-and-education/papers/arxiv-2024-001.yaml
✓ 已更新期刊元数据: .my-paper/journals/computers-and-education/metadata.yaml

✓ 完成！共处理 15 篇论文
```

#### 2. Semantic Scholar API

```bash
python skills/omp:journal-crawl/scripts/crawl.py \
  --journal computers-and-education \
  --source semantic-scholar \
  --query "AI in education" \
  --max 30 \
  --year-from 2022
```

**注意**：如果遇到 `429` 错误（速率限制），脚本会自动等待 60 秒后重试。

#### 3. 手动上传 PDF（推荐）

**步骤**：

1. **下载 PDF**：从学校图书馆或期刊官网下载论文 PDF
2. **整理文件**：将 PDF 放到一个目录，建议按期刊命名
   ```bash
   mkdir -p ~/Downloads/computers-and-education-pdfs
   # 将 PDF 复制到这个目录
   ```
3. **运行脚本**：
   ```bash
   python skills/omp:journal-crawl/scripts/crawl.py \
     --journal computers-and-education \
     --source manual \
     --pdf-dir ~/Downloads/computers-and-education-pdfs/
   ```

**输出示例**：
```
正在从本地目录处理 PDF: ~/Downloads/computers-and-education-pdfs/
处理: paper1.pdf
处理: paper2.pdf
✓ 从本地目录处理了 2 个 PDF 文件
✓ 已保存元数据: .my-paper/journals/computers-and-education/papers/computers-and-education-manual-paper1.yaml
✓ 已更新期刊元数据: .my-paper/journals/computers-and-education/metadata.yaml

✓ 完成！共处理 2 篇论文
```

### 速率限制处理

| API | 速率限制 | 处理方法 |
|-----|-----------|----------|
| arXiv | 3 秒/请求 | 脚本自动添加延迟 |
| Semantic Scholar | 100 次/5分钟 | 脚本自动重试（等待 60 秒） |
| PubMed | 3 秒/请求 | 脚本自动添加延迟 |

**如果持续遇到速率限制**，建议：
1. 使用手动上传模式（`--source manual`）
2. 等待 5-10 分钟后重试
3. 减少 `--max` 参数（每次请求数量）

---

## 分析期刊

### 分析方面

| 方面 | 说明 | 输出文件 |
|------|------|----------|
| `topic` | 选题偏好（研究主题分布） | `topic-distribution.yaml` |
| `title` | 标题风格（长度、结构、高频词） | `style-profile.yaml` |
| `style` | 行文风格（章节结构、语言特点） | `style-profile.yaml` |
| `empirical` | 实证性（理论 vs 实证） | `empirical-tendency.yaml` |
| `innovation` | 创新性（方法论创新、应用创新） | `innovation-metrics.yaml` |

### 使用方法

#### 1. 使用演示脚本（快速）

```bash
python skills/omp:journal-analyze/scripts/demo_analysis.py
```

**输出示例**：
```
============================================================
期刊分析演示：Computers & Education
============================================================
✓ 找到 5 篇论文，开始分析...

📊 分析标题风格...
  - 平均长度: 12.4 词
  - 冒号分隔: 80%
  - 疑问句: 0%

📝 分析行文风格...
  - 常见章节: Abstract, Introduction, Methodology, Results, Discussion

🔬 分析实证性...
  - 实证论文比例: 100%

📄 生成期刊画像...
  ✓ 已保存: .my-paper/journals/computers-and-education/analysis/journal_profile.md

📋 生成写作风格指南...
  ✓ 已保存: .my-paper/journals/computers-and-education/analysis/style_guide.md

✅ 分析完成！结果已保存到 .my-paper/journals/computers-and-education/analysis
```

#### 2. 使用完整分析脚本

```bash
# 分析标题风格
python skills/omp:journal-analyze/scripts/style_analysis.py \
  --journal computers-and-education \
  --aspect title

# 分析行文风格
python skills/omp:journal-analyze/scripts/style_analysis.py \
  --journal computers-and-education \
  --aspect style

# 分析实证性
python skills/omp:journal-analyze/scripts/empirical_analysis.py \
  --journal computers-and-education

# 分析创新性
python skills/omp:journal-analyze/scripts/innovation_eval.py \
  --journal computers-and-education
```

### 分析结果解读

#### 1. 期刊画像（`journal_profile.md`）

```markdown
# 期刊画像：Computers & Education

## 基本信息
- **期刊名称**：Computers & Education
- **出版社**：Elsevier
- **分析论文数**：50 篇
- **分析时间**：2026-05-02

## 标题风格
- **平均长度**：12 个单词
- **常见结构**：80% 使用冒号分隔，0% 为疑问句
- **高频词**：learning, education, student, online, analytics

## 行文风格
- **常见章节**：Abstract, Introduction, Literature Review, Methodology, Results, Discussion, Conclusions
- **实证聚焦**：是
- **方法论要求**：是

## 实证性倾向
- **实证论文比例**：100%
- **理论/综述比例**：0%

## 投稿建议
1. 标题建议使用冒号分隔结构或疑问句形式
2. 必须包含实证研究，有明确的假设和研究问题
3. Methodology 部分必须详细描述参与者、数据收集工具、分析方法
4. Results 部分必须包含统计分析结果（p-value、effect size）
5. Discussion 部分必须讨论实践意义（practical implications）
```

#### 2. 写作风格指南（`style_guide.md`）

```markdown
# 写作风格指南：Computers & Education

## 标题
- 长度：9-15 个单词
- 结构：推荐使用冒号分隔或疑问句
- 示例：
  - "Enhancing student engagement through AI: A mixed-methods study"
  - "What makes a good online teacher? Student perceptions"

## Abstract
- 长度：150-250 词
- 结构：Purpose, Methods, Results, Conclusions
- 必须包含：研究问题、方法、主要发现、实践意义

## Introduction
- 必须包含：研究背景、问题陈述、研究目标、研究问题/假设
- 长度：建议 2-3 页

## Methodology
- 必须包含：研究设计、参与者描述、数据收集工具、数据分析方法
- 细节程度：其他研究者可以复现

## Results
- 必须包含：描述性统计、推断性统计、效应量
- 表格/图表：清晰、标注完整、符合 APA 格式

## Discussion
- 必须包含：主要发现解释、与文献对比、实践意义、研究局限
- 强调：实践意义（practical implications）

## 引用格式
- 必须使用 APA 7th Edition 格式
- DOI：尽可能提供
```

---

## 使用分析结果

### 1. 根据期刊风格调整写作

在写论文时，参考 `style_guide.md`：

- **标题**：按照指南中的长度和结构调整
- **章节**：确保包含所有必需章节（如 Methodology、Results、Discussion）
- **语言**：使用指南中的语言特点（如被动语态比例、句子长度）
- **引用**：严格按照期刊要求的引用格式

### 2. 生成文献综述时考虑期刊偏好

```bash
# 生成文献综述，自动考虑期刊偏好
python skills/omp:survey/scripts/generate.py \
  --journal computers-and-education \
  --topic "AI in education" \
  --output literature_review.md
```

### 3. 检查论文是否符合期刊要求

```bash
# 检查论文是否符合期刊风格
python skills/omp:review/scripts/check_style.py \
  --journal computers-and-education \
  --paper my_draft.md
```

---

## 高级功能

### 1. 知识库管理（混合检索）

```bash
# 构建索引（BM25 + 向量）
python skills/omp:knowledge-base/scripts/build_index.py \
  --journal computers-and-education

# 检索相关论文（混合检索）
python skills/omp:knowledge-base/scripts/retrieve.py \
  --journal computers-and-education \
  --query "AI-based chatbot for student engagement" \
  --top-k 10
```

### 2. 自进化插件（反馈学习）

```bash
# 记录用户反馈
python skills/omp:knowledge-base/scripts/evolve.py \
  --action log-feedback \
  --query "AI in education" \
  --rating 4 \
  --comment "检索结果很相关"

# 自动调参（调整 BM25 和向量检索权重）
python skills/omp:knowledge-base/scripts/evolve.py \
  --action optimize-weights \
  --journal computers-and-education
```

### 3. 批量处理多个期刊

```bash
# 创建批量处理脚本 batch_analyze.sh
#!/bin/bash

JOURNALS=(
  "computers-and-education"
  "computer-science-china"
  "ieee-tlt"
)

for journal in "${JOURNALS[@]}"; do
  echo "正在分析期刊: $journal"
  python skills/omp:journal-analyze/scripts/demo_analysis.py \
    --journal "$journal"
done

echo "✅ 所有期刊分析完成！"
```

---

## 故障排除

### 常见问题

#### 1. API 速率限制（429 错误）

**错误信息**：
```
⚠ API 速率限制，等待 60 秒后重试...
```

**解决方法**：
- 等待 5-10 分钟后重试
- 使用手动上传模式（`--source manual`）
- 减少 `--max` 参数

#### 2. PDF 解析失败

**错误信息**：
```
警告: 无法解析 PDF: paper1.pdf
```

**解决方法**：
- 检查 PDF 是否加密或扫描件
- 使用 OCR 工具处理扫描件
- 手动输入元数据

#### 3. 期刊元数据未找到

**错误信息**：
```
错误: 期刊目录不存在 - .my-paper/journals/{journal-id}
请先创建期刊元数据: .my-paper/journals/{journal-id}/metadata.yaml
```

**解决方法**：
- 运行 `generate_sample_data.py` 创建模板
- 或手动创建 `metadata.yaml`（参考本文档中的模板）

#### 4. 路径错误

**错误信息**：
```
错误: 论文数据保存到错误位置
```

**解决方法**：
- 检查脚本中的 `project_root` 计算是否正确
- 手动指定项目根目录：
  ```bash
  python scripts/xxx.py --project-root /path/to/Oh-my--paper
  ```

### 获取帮助

如果遇到其他问题，请：

1. 查看脚本的输出日志
2. 检查 `.my-paper/journals/{journal-id}/` 目录结构
3. 查看本文档的相关章节
4. 联系开发者（如果你的团队有技术支持）

---

## 附录

### A. 支持的期刊列表

| 期刊 ID | 期刊名称 | 出版社 | 适用领域 |
|----------|----------|--------|----------|
| `computers-and-education` | Computers & Education | Elsevier | 教育技术 |
| `computer-science-china` | 计算机学报 | 科学出版社 | 计算机科学 |
| `ieee-tlt` | IEEE Transactions on Learning Technologies | IEEE | 学习技术 |

### B. API 字段说明

#### Semantic Scholar API

| 字段 | 说明 |
|------|------|
| `title` | 论文标题 |
| `authors` | 作者列表 |
| `year` | 发表年份 |
| `abstract` | 摘要 |
| `doi` | DOI |
| `citationCount` | 引用数 |
| `url` | Semantic Scholar 页面 URL |

### C. 文件格式说明

#### 论文元数据（YAML）

```yaml
paper:
  id: "computers-and-education-2023-001"
  title: "Enhancing student engagement through AI: A mixed-methods study"
  authors:
    - name: "Smith, J."
      affiliation: "Stanford University"
      email: "jsmith@stanford.edu"
  year: 2023
  doi: "10.1016/j.compedu.2023.104712"
  keywords: ["AI", "chatbot", "student engagement"]
  empirical: true
  citation_count: 45
  markdown_path: "papers/computers-and-education-2023-001.md"
  created_at: "2026-05-02T09:00:00+08:00"
```

---

**文档版本**: 1.0.0  
**最后更新**: 2026-05-02  
**作者**: Oh-my-paper 开发团队

如有问题或建议，请提交 Issue 或联系开发团队。
