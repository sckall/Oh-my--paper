---
id: omp:knowledge-base
name: omp:knowledge-base
version: 1.0.0
description: 知识库管理工具 - 构建混合检索系统（BM25 + 向量检索），支持自进化插件
stages: [A2, A4, B14]
tools: [read_file, write_file, Bash]
tracker: writes to .my-paper/journals/{journal-id}/embeddings/
---

# omp:knowledge-base - 知识库管理

构建混合检索系统，支持 BM25 关键词检索和向量语义检索，提供自进化插件优化检索结果。

## 调用方式

### 构建索引
```
/omp:knowledge-base build --journal {journal-id} --methods {methods}
```

### 检索
```
/omp:knowledge-base retrieve --journal {journal-id} --query "{query}" --top-k {k}
```

### 反馈（自进化）
```
/omp:knowledge-base feedback --journal {journal-id} --query-id {id} --rating {1-5}
```

### 优化（自动调参）
```
/omp:knowledge-base optimize --journal {journal-id}
```

## 参数说明

### 通用参数
| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--journal` | 是 | 目标期刊 ID | `computer-science-china` |

### build 子命令参数
| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--methods` | 否 | 索引方法（bm25/vector/both） | `both` |
| `--model` | 否 | 向量模型名称 | `all-MiniLM-L6-v2` |
| `--chunk-size` | 否 | 文本分块大小 | `512` |

### retrieve 子命令参数
| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--query` | 是 | 检索查询 | `"transformer efficiency"` |
| `--top-k` | 否 | 返回结果数量（默认 5） | `10` |
| `--weight-bm25` | 否 | BM25 权重（0-1） | `0.3` |
| `--weight-vector` | 否 | 向量权重（0-1） | `0.7` |

### feedback 子命令参数
| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--query-id` | 是 | 查询 ID | `QRY-001` |
| `--rating` | 是 | 评分（1-5） | `4` |
| `--relevant-ids` | 否 | 相关论文 ID 列表 | `paper-001,paper-002` |

## 阶段

**A2 - SEARCH_STRATEGY**：构建索引策略
**A4 - KNOWLEDGE_EXTRACT**：从论文中提取文本用于索引
**B14 - RESULT_ANALYSIS**：分析检索结果，优化参数

## 任务

### build 子命令
1. 读取期刊数据库（`.my-paper/journals/{journal-id}/papers/`）
2. 提取文本（标题、摘要、全文）
3. 构建 BM25 索引（使用 `rank_bm25`）
4. 构建向量索引（使用 `sentence-transformers` + `chroma`）
5. 保存索引到 `.my-paper/journals/{journal-id}/embeddings/`

### retrieve 子命令
1. 加载 BM25 索引和向量索引
2. 执行 BM25 检索
3. 执行向量检索
4. 混合排序（加权融合）
5. 返回前 k 个结果

### feedback 子命令
1. 记录用户反馈（查询 ID、评分、相关论文 ID）
2. 更新反馈数据库
3. 触发优化（如果反馈数量达到阈值）

### optimize 子命令
1. 分析反馈数据
2. 调整 BM25 和向量检索的权重
3. 重新训练向量模型（可选）
4. 更新索引

## Tracker 集成

### 读
- `.my-paper/journals/{journal-id}/papers/*.md` — 读取论文全文
- `.my-paper/journals/{journal-id}/papers/*.yaml` — 读取论文元数据
- `.my-paper/journals/{journal-id}/embeddings/feedback.json` — 读取反馈数据

### 写
- `.my-paper/journals/{journal-id}/embeddings/bm25.pkl` — BM25 索引
- `.my-paper/journals/{journal-id}/embeddings/chroma.db/` — 向量数据库
- `.my-paper/journals/{journal-id}/embeddings/metadata.json` — 索引元数据
- `.my-paper/journals/{journal-id}/embeddings/feedback.json` — 反馈数据
- `.my-paper/journals/{journal-id}/embeddings/optimization-log.json` — 优化日志

## 混合检索算法

### 1. BM25 检索
**原理**：基于词频-逆文档频率的改进版
**优点**：精确匹配关键词，适合专业术语检索
**实现**：使用 `rank_bm25` 库

### 2. 向量检索
**原理**：将查询和文档转换为向量，计算余弦相似度
**优点**：语义匹配，适合概念检索
**实现**：使用 `sentence-transformers` 生成向量，使用 `chroma` 存储和检索

### 3. 混合排序
**算法**：加权倒数排名融合（Weighted Reciprocal Rank Fusion）
```
score(d) = weight_bm25 * 1/(k + rank_bm25(d)) + weight_vector * 1/(k + rank_vector(d))
```
其中 `k` 是常数（默认 60）

**默认权重**：
- `weight_bm25 = 0.3`
- `weight_vector = 0.7`

**自适应权重调整**（自进化）：
- 如果用户反馈显示向量检索更准确，增加 `weight_vector`
- 如果 BM25 检索更准确，增加 `weight_bm25`

## 自进化插件

### 1. 反馈学习
**机制**：
1. 用户对每个检索结果提供反馈（评分 1-5）
2. 记录查询、结果、反馈到反馈数据库
3. 定期分析反馈数据，识别模式

**反馈格式**：
```json
{
  "query_id": "QRY-001",
  "query": "transformer efficiency",
  "timestamp": "2026-05-02T08:30:00+08:00",
  "results": [
    {"paper_id": "paper-001", "rank": 1, "score": 0.85},
    {"paper_id": "paper-002", "rank": 2, "score": 0.72}
  ],
  "rating": 4,
  "relevant_ids": ["paper-001"],
  "user_id": "user-001"
}
```

### 2. 自动调参
**机制**：
1. 计算 BM25 和向量检索的准确率（基于反馈数据）
2. 如果向量检索准确率更高，增加 `weight_vector`
3. 如果 BM25 准确率更高，增加 `weight_bm25`
4. 重新构建索引（如果需要）

**调整公式**：
```
weight_vector_new = weight_vector_old + learning_rate * (accuracy_vector - accuracy_bm25)
weight_bm25_new = 1 - weight_vector_new
```

### 3. 知识库自动扩展
**机制**：
1. 根据检索查询，自动搜索外部数据源（arXiv、Semantic Scholar）
2. 如果用户确认检索结果有用，自动下载并添加到知识库
3. 定期重新训练向量模型（如果添加了大量新论文）

## 输出格式

### 检索结果
```yaml
query: "transformer efficiency"
timestamp: "2026-05-02T08:30:00+08:00"
results:
  - paper_id: "computer-science-china-2024-001"
    title: "基于 Transformer 的效率优化方法"
    authors: ["张三"]
    year: 2024
    score: 0.87
    rank_bm25: 1
    rank_vector: 2
    snippet: "本文提出了一种基于 Transformer 的效率优化方法..."
  - paper_id: "computer-science-china-2023-042"
    title: "Efficient Transformers: A Survey"
    authors: ["Li, Si"]
    year: 2023
    score: 0.82
    rank_bm25: 3
    rank_vector: 1
    snippet: "This survey reviews recent advances in efficient Transformers..."
```

## 约束

- MUST NOT 删除原始论文数据
- MUST NOT 伪造反馈数据
- 向量数据库应使用本地存储，避免 API 调用成本
- 对于无法向量化的文本，记录警告并跳过

## 依赖安装

```bash
# 核心依赖
pip install rank-bm25 sentence-transformers chromadb

# 可选：使用更好的向量模型
pip install torch  # 如果使用 PyTorch 后端

# 可选：使用其他向量数据库
pip install faiss-cpu  # 如果使用 FAISS
```

## 示例调用

### 示例 1：构建索引（BM25 + 向量）
```
/omp:knowledge-base build --journal computer-science-china --methods both
```

### 示例 2：检索
```
/omp:knowledge-base retrieve --journal computer-science-china --query "transformer efficiency" --top-k 10
```

### 示例 3：提供反馈（自进化）
```
/omp:knowledge-base feedback --journal computer-science-china --query-id QRY-001 --rating 4 --relevant-ids paper-001,paper-002
```

### 示例 4：优化权重（自动调参）
```
/omp:knowledge-base optimize --journal computer-science-china
```

## 性能优化建议

1. **向量模型选择**：
   - 默认：`all-MiniLM-L6-v2`（速度快，精度中等）
   - 高精度：`all-mpnet-base-v2`（速度慢，精度高）
   - 中文：`paraphrase-multilingual-MiniLM-L12-v2`

2. **索引存储**：
   - 小规模（< 1000 篇）：使用 pickle 存储 BM25 索引
   - 中等规模（1000-10000 篇）：使用 Chroma 数据库
   - 大规模（> 10000 篇）：使用 FAISS 向量数据库

3. **检索优化**：
   - 使用缓存存储常见查询的结果
   - 对长查询进行关键词提取，减少噪声
   - 使用查询扩展（Query Expansion）提高召回率

## 故障排除

### 问题 1：向量模型下载失败
**解决方案**：
1. 使用镜像源：`export HF_ENDPOINT=https://hf-mirror.com`
2. 手动下载模型并指定本地路径

### 问题 2：Chroma 数据库损坏
**解决方案**：
1. 删除 `embeddings/chroma.db/` 目录
2. 重新运行 `build` 命令

### 问题 3：检索结果不准确
**解决方案**：
1. 提供反馈数据（使用 `feedback` 子命令）
2. 运行 `optimize` 命令调整权重
3. 尝试不同的向量模型
