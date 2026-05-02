---
id: omp:journal-crawl
name: omp:journal-crawl
version: 1.0.0
description: 期刊论文爬取工具 - 从 arXiv、Semantic Scholar、PubMed 等来源爬取论文并存储到本地数据库
stages: [A2, A3]
tools: [read_file, write_file, Bash, WebFetch]
tracker: writes to .my-paper/journals/{journal-id}/papers/
---

# omp:journal-crawl - 期刊论文爬取

从多个来源爬取期刊论文，自动下载 PDF 并转换为 Markdown，提取元数据并存储到本地数据库。

## 调用方式

```
/omp:journal-crawl --journal {journal-id} --source {source} --query "{query}" --max {num}
```

### 参数说明

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--journal` | 是 | 目标期刊 ID | `computers-and-education` 或 `computer-science-china` |
| `--source` | 否 | 数据源（arxiv/semantic-scholar/pubmed/manual） | `semantic-scholar` |
| `--query` | 否 | 搜索查询（用于 API 搜索） | `"AI in education"` |
| `--max` | 否 | 最大爬取数量（默认 20） | `50` |
| `--year-from` | 否 | 起始年份过滤 | `2020` |
| `--year-to` | 否 | 结束年份过滤 | `2024` |
| `--pdf-dir` | 否 | 手动上传 PDF 的目录路径 | `/path/to/pdfs/` |

## 阶段

**A2 - SEARCH_STRATEGY**：生成搜索策略
**A3 - LITERATURE_COLLECT**：执行爬取并存储

## 任务

1. 读取期刊元数据（`.my-paper/journals/{journal-id}/metadata.yaml`）
2. 根据 `--source` 选择爬取脚本
3. 执行爬取，下载论文 PDF（如果可用）
4. 解析 PDF 为 Markdown（使用 `scripts/parse.py`）
5. 提取元数据（使用 `scripts/metadata.py`）
6. 存储到 `.my-paper/journals/{journal-id}/papers/`
7. 更新期刊元数据中的 `paper_count` 和 `last_updated`

## Tracker 集成

### 读
- `.my-paper/journals/{journal-id}/metadata.yaml` — 读取期刊信息

### 写
- `.my-paper/journals/{journal-id}/papers/{paper-id}.md` — 论文全文（Markdown）
- `.my-paper/journals/{journal-id}/papers/{paper-id}.yaml` — 论文元数据
- `.my-paper/journals/{journal-id}/metadata.yaml` — 更新论文数量

## 数据源说明

### arXiv API
- **适用**：预印本论文（CS/数学/物理等）
- **优点**：免费、开放获取、API 稳定
- **限制**：仅包含 arXiv 收录的论文
- **调用示例**：
  ```bash
  python scripts/crawl.py --source arxiv --query "large language model" --max 20 --year-from 2023
  ```

### Semantic Scholar API
- **适用**：已发表论文（涵盖多个学科，包括 Elsevier、Springer 等出版社）
- **优点**：丰富的元数据（引用数、作者信息）、支持按期刊名称过滤
- **限制**：有速率限制（100 次/5分钟）
- **调用示例**：
  ```bash
  # 搜索 Computers & Education 期刊的论文
  python scripts/crawl.py --source semantic-scholar --query "AI in education" --journal "Computers & Education" --max 30 --year-from 2022
  
  # 搜索任意期刊
  python scripts/crawl.py --source semantic-scholar --query "large language model" --max 30 --year-from 2022
  ```

### PubMed API
- **适用**：生物医学领域期刊
- **优点**：官方 API、数据权威
- **限制**：仅限生物医学领域
- **调用示例**：
  ```bash
  python scripts/crawl.py --source pubmed --query "CRISPR gene editing" --max 20
  ```

### 手动上传
- **适用**：付费期刊、无 API 的期刊
- **流程**：
  1. 用户将 PDF 文件放到指定目录
  2. 运行 `/omp:journal-crawl --source manual --pdf-dir /path/to/pdfs/`
  3. 脚本自动解析 PDF 并提取元数据

## 输出格式

### 论文元数据（{paper-id}.yaml）
```yaml
paper:
  id: "computer-science-china-2024-001"
  title: "基于深度学习的自然语言处理技术研究"
  authors:
    - name: "张三"
      affiliation: "清华大学计算机科学与技术系"
      email: "zs@tsinghua.edu.cn"
  year: 2024
  volume: 47
  issue: 3
  pages: "512-525"
  doi: "10.11897/SP.J.1016.2024.00512"
  keywords: ["深度学习", "自然语言处理", "Transformer"]
  section_structure: ["摘要", "引言", "相关工作", "方法", "实验", "结论"]
  empirical: true
  citation_count: 0
  url: "http://cjc.ict.ac.cn/EN/10.11897/SP.J.1016.2024.00512"
  pdf_path: "papers/computer-science-china-2024-001.pdf"
  markdown_path: "papers/computer-science-china-2024-001.md"
  created_at: "2026-05-02T08:30:00+08:00"
```

### 论文全文（{paper-id}.md）
```markdown
# 基于深度学习的自然语言处理技术研究

**作者**：张三（清华大学）
**年份**：2024
**DOI**：10.11897/SP.J.1016.2024.00512

---

## 摘要

本文提出了一种基于深度学习的自然语言处理技术...

## 引言

随着人工智能技术的快速发展...

## 方法

### 3.1 模型架构

我们提出了一种改进的 Transformer 架构...

## 实验

### 4.1 数据集

我们使用 GLUE 基准测试...

## 结论

本文提出了...
```

## 约束

- MUST NOT 修改其他期刊的数据
- MUST NOT 伪造 PDF 或元数据
- 对于无法解析的 PDF，记录错误并跳过，不得中断整个爬取流程
- 尊重数据源的速率限制（Semantic Scholar: 100 次/5分钟）

## 错误处理

| 错误类型 | 处理方式 |
|---------|-----------|
| PDF 下载失败 | 记录错误，继续处理下一个 |
| PDF 解析失败 | 保留元数据，标记 `markdown_path: null` |
| 元数据提取失败 | 使用默认值，记录警告 |
| API 速率限制 | 自动重试（等待 60 秒） |

## 示例调用

### 示例 1：从 arXiv 爬取 Transformer 相关论文
```
/omp:journal-crawl --journal computers-and-education --source arxiv --query "transformer" --max 20 --year-from 2023
```

### 示例 2：从 Semantic Scholar 爬取 Computers & Education 期刊论文
```
/omp:journal-crawl --journal computers-and-education --source semantic-scholar --query "AI in education" --max 30 --year-from 2022
```

### 示例 3：手动上传 PDF
```
/omp:journal-crawl --journal computers-and-education --source manual --pdf-dir /Users/guojiong/Downloads/pdfs/
```
