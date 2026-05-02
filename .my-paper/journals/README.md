# 期刊数据库目录结构

> **最后更新**: 2026-05-02  
> **用途**: 存储各期刊的论文数据、分析结果和向量数据

---

## 📂 目录结构

```
.my-paper/journals/
├── computer-science-china/      # 期刊 1：计算机学报
│   ├── metadata.yaml            # 期刊元数据
│   ├── papers/                 # 论文数据（YAML + Markdown）
│   │   ├── 2023-001.yaml
│   │   ├── 2023-001.md
│   │   └── ...
│   ├── analysis/               # 分析结果
│   │   ├── journal_profile.md   # 期刊画像
│   │   ├── style_guide.md      # 写作风格指南
│   │   ├── topic-distribution.yaml
│   │   ├── style-profile.yaml
│   │   ├── empirical-tendency.yaml
│   │   └── innovation-metrics.yaml
│   └── embeddings/            # 向量数据（用于知识库检索）
│
└── computers-and-education/   # 期刊 2：Computers & Education
    ├── metadata.yaml
    ├── papers/
    ├── analysis/
    └── embeddings/
```

---

## 📋 各目录说明

### 1️⃣ `metadata.yaml` - 期刊元数据

**用途**: 存储期刊的基本信息、配置和统计

**内容示例**:
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
  
  crawl_config:
    default_source: "semantic-scholar"
    filters:
      year_from: 2020
      year_to: 2026

stats:
  paper_count: 50
  last_updated: "2026-05-02"
  year_distribution:
    2023: 15
    2024: 20
    2025: 15
```

---

### 2️⃣ `papers/` - 论文数据

**用途**: 存储期刊的所有论文（元数据 + 全文）

**文件命名规则**:
- 元数据：`{year}-{seq}.yaml`（如 `2023-001.yaml`）
- 全文：`{year}-{seq}.md`（如 `2023-001.md`）

**元数据示例** (`2023-001.yaml`):
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

**全文示例** (`2023-001.md`):
```markdown
# Enhancing student engagement through AI: A mixed-methods study

**Authors**: Smith, J. (Stanford University), Wang, L. (MIT)  
**Year**: 2023  
**DOI**: 10.1016/j.compedu.2023.104712  

---

## Abstract

This study investigates the impact of AI-based chatbots on student engagement...

## 1. Introduction

The rapid advancement of artificial intelligence (AI) has opened new possibilities...

## 2. Literature Review

...

## 3. Methodology

...

## 4. Results

...

## 5. Discussion

...

## 6. Conclusions

...
```

---

### 3️⃣ `analysis/` - 分析结果

**用途**: 存储期刊分析生成的所有报告

| 文件 | 说明 | 生成脚本 |
|------|------|------------|
| `journal_profile.md` | 期刊画像（选题偏好、标题风格、投稿建议） | `demo_analysis.py` |
| `style_guide.md` | 写作风格指南（标题、章节、引用格式） | `demo_analysis.py` |
| `topic-distribution.yaml` | 选题分布（LDA 主题建模结果） | `topic_modeling.py` |
| `style-profile.yaml` | 标题风格和行文风格分析 | `style_analysis.py` |
| `empirical-tendency.yaml` | 实证性倾向分析 | `empirical_analysis.py` |
| `innovation-metrics.yaml` | 创新性评估 | `innovation_eval.py` |

**期刊画像示例** (`journal_profile.md`):
```markdown
# 期刊画像：Computers & Education

## 基本信息
- **期刊名称**: Computers & Education
- **出版社**: Elsevier
- **分析论文数**: 50 篇

## 标题风格
- **平均长度**: 12 个单词
- **常见结构**: 80% 使用冒号分隔
- **高频词**: learning, education, student, online

## 投稿建议
1. 标题建议使用冒号分隔结构
2. 必须包含实证研究
3. Methodology 部分必须详细描述方法
...
```

---

### 4️⃣ `embeddings/` - 向量数据

**用途**: 存储论文的向量表示（用于知识库检索）

**内容**:
- Chroma 向量数据库文件
- BM25 索引文件
- 其他检索相关的数据文件

**使用场景**:
```bash
# 构建索引
python skills/omp:knowledge-base/scripts/build_index.py \
  --journal computers-and-education

# 检索相关论文
python skills/omp:knowledge-base/scripts/retrieve.py \
  --journal computers-and-education \
  --query "AI-based chatbot" \
  --top-k 10
```

---

## ➕ 添加新期刊

### 方法 1：手动创建

```bash
# 1. 创建目录结构
mkdir -p .my-paper/journals/{journal-id}/papers
mkdir -p .my-paper/journals/{journal-id}/analysis
mkdir -p .my-paper/journals/{journal-id}/embeddings

# 2. 创建元数据文件
touch .my-paper/journals/{journal-id}/metadata.yaml
# 然后编辑 metadata.yaml（参考上面的示例）
```

### 方法 2：使用脚本

```bash
# 运行模拟数据生成器（会创建目录结构和模板）
python skills/omp:journal-crawl/scripts/generate_sample_data.py
```

---

## 🔍 查询和维护

### 查看期刊列表

```bash
ls -la .my-paper/journals/
```

### 查看某期刊的论文数量

```bash
ls .my-paper/journals/computers-and-education/papers/*.yaml | wc -l
```

### 查看某期刊的分析结果

```bash
cat .my-paper/journals/computers-and-education/analysis/journal_profile.md
cat .my-paper/journals/computers-and-education/analysis/style_guide.md
```

### 删除某期刊（谨慎！）

```bash
rm -rf .my-paper/journals/{journal-id}/
```

---

## 📊 数据流程

```
┌─────────────────┐
│  数据源（arXiv / Semantic   │
│  Scholar / PubMed / PDF）    │
└────────────┬──────────────┘
             │
             ▼
┌─────────────────────┐
│  omp:journal-crawl  │
│  （爬取脚本）              │
└────────────┬──────────────┘
             │
             ▼
┌─────────────────────┐
│  .my-paper/journals/│
│  {journal-id}/papers/ │
│  （存储论文数据）        │
└────────────┬──────────────┘
             │
             ▼
┌─────────────────────┐
│  omp:journal-      │
│  analyze（分析脚本）   │
└────────────┬──────────────┘
             │
             ▼
┌─────────────────────┐
│  .my-paper/journals/│
│  {journal-id}/analysis/ │
│  （存储分析结果）        │
└────────────┬──────────────┘
             │
             ▼
┌─────────────────────┐
│  使用分析结果          │
│  - 调整写作风格      │
│  - 选择合适选题      │
│  - 优化论文结构      │
└─────────────────────┘
```

---

## 💡 最佳实践

1. **定期更新**: 每月爬取一次新论文，保持数据新鲜
2. **备份数据**: 定期备份 `.my-paper/journals/` 目录
3. **多期刊对比**: 可以同时分析多个期刊，对比它们的风格差异
4. **结合知识库**: 使用 `omp:knowledge-base` 构建检索系统，快速找到相关论文

---

**文档版本**: 1.0.0  
**最后更新**: 2026-05-02  
**维护者**: Oh-my-paper 开发团队
