# Oh My Paper - 期刊分析系统使用指南

## 1. 系统概述

期刊分析系统为 Oh My Paper 添加了以下功能：
1. **期刊数据库**：存储某期刊的大量文章（md + 结构化数据）
2. **期刊偏好分析**：分析期刊的题材偏好、标题风格、行文风格、实证性、创新性
3. **知识库系统**：混合检索（BM25 + 向量检索）+ 自进化插件
4. **写作辅助**：根据期刊风格调整写作，生成投稿建议

## 2. 安装依赖

### Python 依赖
```bash
# PDF 处理
pip install pdfplumber  # 或 pip install PyMuPDF

# NLP 分析
pip install scikit-learn nltk spacy sentence-transformers

# 信息检索
pip install rank-bm25 chromadb

# 数据处理
pip install pyyaml pandas numpy
```

### 可选依赖
```bash
# 使用 arxiv 库（简化 arXiv API 调用）
pip install arxiv

# 使用 BeautifulSoup（解析 HTML）
pip install beautifulsoup4
```

## 3. 快速开始

### 步骤 1：创建期刊数据库
```bash
# 1. 创建期刊目录
mkdir -p .my-paper/journals/{journal-id}/papers
mkdir -p .my-paper/journals/{journal-id}/analysis
mkdir -p .my-paper/journals/{journal-id}/embeddings

# 2. 创建期刊元数据文件
cat > .my-paper/journals/{journal-id}/metadata.yaml << EOF
journal:
  id: "{journal-id}"
  name: "期刊名称"
  issn: "0000-0000"
  publisher: "出版社名称"
  year_range: [2020, 2024]
  paper_count: 0
  last_updated: "2026-05-02"
EOF
```

### 步骤 2：爬取期刊论文
```bash
# 使用 omp:journal-crawl 技能
# 注意：这是一个 CLI 脚本，需要通过 Bash 调用

# 示例 1：从 arXiv 爬取
python skills/omp:journal-crawl/scripts/crawl.py \
  --journal {journal-id} \
  --source arxiv \
  --query "transformer" \
  --max 20 \
  --year-from 2023

# 示例 2：从 Semantic Scholar 爬取
python skills/omp:journal-crawl/scripts/crawl.py \
  --journal {journal-id} \
  --source semantic-scholar \
  --query "large language model" \
  --max 30 \
  --year-from 2022

# 示例 3：手动上传 PDF
python skills/omp:journal-crawl/scripts/crawl.py \
  --journal {journal-id} \
  --source manual \
  --pdf-dir /path/to/pdfs/
```

### 步骤 3：分析期刊
```bash
# 使用 omp:journal-analyze 技能

# 运行分析脚本
python skills/omp:journal-analyze/scripts/topic_modeling.py \
  .my-paper/journals/{journal-id}/papers/ \
  .my-paper/journals/{journal-id}/analysis/topic-distribution.yaml

python skills/omp:journal-analyze/scripts/style_analysis.py \
  .my-paper/journals/{journal-id}/papers/ \
  .my-paper/journals/{journal-id}/analysis/style-profile.yaml

python skills/omp:journal-analyze/scripts/empirical_analysis.py \
  .my-paper/journals/{journal-id}/papers/ \
  .my-paper/journals/{journal-id}/analysis/empirical-tendency.yaml

python skills/omp:journal-analyze/scripts/innovation_eval.py \
  .my-paper/journals/{journal-id}/papers/ \
  .my-paper/journals/{journal-id}/analysis/innovation-metrics.yaml
```

### 步骤 4：生成期刊画像和写作指南
```bash
# 根据分析结果，手动创建以下文件：

# 1. 期刊画像
# 复制到 .pipeline/memory/journal_profile.md
# 参考 templates/research/memory/journal_profile.md

# 2. 写作风格指南
# 复制到 .pipeline/memory/style_guide.md
# 参考 templates/research/memory/style_guide.md
```

### 步骤 5：构建知识库
```bash
# 使用 omp:knowledge-base 技能

# 构建索引
python skills/omp:knowledge-base/scripts/build_index.py \
  .my-paper/journals/{journal-id}/papers/ \
  .my-paper/journals/{journal-id}/embeddings/ \
  --methods both \
  --model all-MiniLM-L6-v2

# 检索
python skills/omp:knowledge-base/scripts/retrieve.py \
  "transformer efficiency" \
  .my-paper/journals/{journal-id}/embeddings/ \
  .my-paper/journals/{journal-id}/papers/ \
  --top-k 10 \
  --weight-bm25 0.3 \
  --weight-vector 0.7
```

## 4. 在 Oh My Paper 中使用

### 文献调研（`omp:survey`）
```
/omp:survey --journal computer-science-china
```
- 自动根据期刊偏好过滤文献
- 优先推荐符合期刊风格的论文

### 论文写作（`omp:write`）
```
/omp:write --match-style computer-science-china
```
- 自动模仿期刊的写作风格
- 生成符合期刊要求的标题、摘要、章节结构
- 自动检查引用格式

### 论文评审（`omp:review`）
```
/omp:review --check-journal computer-science-china
```
- 检查论文是否符合期刊偏好
- 生成期刊匹配度报告（0-10 分）

## 5. 知识库自进化

### 提供反馈
```bash
python skills/omp:knowledge-base/scripts/evolve.py \
  add-feedback \
  "transformer efficiency" \
  4 \
  "paper-001,paper-002" \
  .my-paper/journals/{journal-id}/embeddings/
```
- 评分 1-5（1 = 非常不相关，5 = 非常相关）
- 系统会根据反馈优化检索权重

### 优化权重
```bash
python skills/omp:knowledge-base/scripts/evolve.py \
  optimize \
  .my-paper/journals/{journal-id}/embeddings/ \
  0.1
```
- 自动调整 BM25 和向量检索的权重
- 学习率默认 0.1

## 6. 文件结构

```
.my-paper/
├── journals/
│   └── {journal-id}/
│       ├── metadata.yaml          # 期刊元数据
│       ├── papers/                # 论文存储
│       │   ├── {paper-id}.md   # 论文全文（Markdown）
│       │   └── {paper-id}.yaml # 论文元数据
│       ├── analysis/              # 分析结果
│       │   ├── style-profile.yaml      # 标题风格、行文风格
│       │   ├── topic-distribution.yaml # 题材偏好
│       │   ├── empirical-tendency.yaml # 实证性分析
│       │   └── innovation-metrics.yaml # 创新性评估
│       └── embeddings/          # 向量数据
│           ├── bm25.pkl         # BM25 索引
│           ├── chroma.db/       # Chroma 向量数据库
│           ├── metadata.yaml    # 索引元数据
│           ├── feedback.json     # 用户反馈
│           └── optimization-log.json # 优化日志
```

## 7. 技能列表

### 新增技能

| 技能 | 功能 | 调用方式 |
|------|------|----------|
| `omp:journal-crawl` | 期刊论文爬取 | CLI: `python skills/omp:journal-crawl/scripts/crawl.py` |
| `omp:journal-analyze` | 期刊分析 | CLI: `python skills/omp:journal-analyze/scripts/*.py` |
| `omp:knowledge-base` | 知识库管理 | CLI: `python skills/omp:knowledge-base/scripts/*.py` |

### 修改的技能

| 技能 | 修改内容 |
|------|----------|
| `omp:survey` | 添加 `--journal` 参数 |
| `omp:write` | 添加 `--match-style` 参数 |
| `omp:review` | 添加 `--check-journal` 参数 |

## 8. 常见问题

### Q1：PDF 解析失败怎么办？
**A**：尝试以下方法：
1. 使用不同的 PDF 解析库（pdfplumber 或 PyMuPDF）
2. 手动上传文本版本（.md 文件）
3. 使用 LLM 辅助解析（需要 API key）

### Q2：向量模型下载失败怎么办？
**A**：使用镜像源：
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

或手动下载模型并指定本地路径。

### Q3：检索结果不准确怎么办？
**A**：尝试以下方法：
1. 提供更多的反馈数据（使用 `add-feedback` 子命令）
2. 运行 `optimize` 子命令调整权重
3. 尝试不同的向量模型

### Q4：如何添加自定义期刊？
**A**：
1. 创建期刊目录：`.my-paper/journals/{journal-id}/`
2. 创建元数据文件：`metadata.yaml`
3. 爬取或上传论文：`omp:journal-crawl`
4. 分析期刊：`omp:journal-analyze`

## 9. 后续优化方向

1. **多模态分析**：支持图表、公式的提取和分析
2. **知识图谱**：构建期刊知识图谱，展示研究主题演化
3. **自动投稿**：集成期刊投稿系统，一键投稿
4. **协作功能**：支持多用户共享期刊数据库
5. **移动端支持**：开发移动端 App，随时随地查看期刊分析结果

---

*本文档基于 Oh My Paper 期刊分析系统（版本 1.0.0）编写。如有问题，请参考项目 README 或提交 issue。*
