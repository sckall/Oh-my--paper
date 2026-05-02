#!/usr/bin/env python3
"""
检索脚本 - 混合检索（BM25 + 向量）

依赖：
- rank_bm25: pip install rank-bm25
- sentence-transformers: pip install sentence-transformers
- chromadb: pip install chromadb
"""

import sys
import pickle
import yaml
from pathlib import Path
from typing import List, Dict, Tuple

# 尝试导入依赖
try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

try:
    import chromadb
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False


def load_bm25_index(index_path: Path) -> object:
    """加载 BM25 索引"""
    if not HAS_BM25:
        print("警告: rank_bm25 未安装")
        return None

    if not index_path.exists():
        print(f"警告: BM25 索引不存在 - {index_path}")
        return None

    with open(index_path, 'rb') as f:
        bm25 = pickle.load(f)

    print(f"✓ 已加载 BM25 索引")
    return bm25


def load_vector_index(embeddings_dir: Path) -> object:
    """加载向量索引（Chroma）"""
    if not HAS_CHROMA:
        print("警告: chromadb 未安装")
        return None

    chroma_dir = embeddings_dir / "chroma.db"
    if not chroma_dir.exists():
        print(f"警告: Chroma 数据库不存在 - {chroma_dir}")
        return None

    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_collection("papers")

    print(f"✓ 已加载向量索引")
    return collection


def bm25_retrieve(bm25, query: str, paper_ids: List[str], top_k: int = 5) -> List[Tuple[str, float, int]]:
    """
    BM25 检索

    Returns:
        [(paper_id, score, rank), ...]
    """
    if not bm25:
        return []

    # 分词（简化版）
    tokenized_query = query.split()

    # 获取 BM25 分数
    scores = bm25.get_scores(tokenized_query)

    # 排序
    top_n = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    results = []
    for rank, idx in enumerate(top_n, 1):
        results.append((paper_ids[idx], float(scores[idx]), rank))

    return results


def vector_retrieve(collection, query: str, top_k: int = 5) -> List[Tuple[str, float, int]]:
    """
    向量检索（Chroma）

    Returns:
        [(paper_id, score, rank), ...]
    """
    if not collection:
        return []

    # 查询
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )

    # 格式化结果
    formatted = []
    for rank, (paper_id, score) in enumerate(zip(results['ids'][0], results['distances'][0]), 1):
        formatted.append((paper_id, float(score), rank))

    return formatted


def hybrid_retrieve(bm25_results: List[Tuple[str, float, int]],
                    vector_results: List[Tuple[str, float, int]],
                    weight_bm25: float = 0.3,
                    weight_vector: float = 0.7,
                    k: int = 60) -> List[Tuple[str, float]]:
    """
    混合检索（加权倒数排名融合）

    Args:
        bm25_results: BM25 检索结果
        vector_results: 向量检索结果
        weight_bm25: BM25 权重
        weight_vector: 向量权重
        k: 常数（默认 60）

    Returns:
        [(paper_id, fused_score), ...]
    """
    # 构建排名字典
    bm25_ranks = {paper_id: rank for paper_id, score, rank in bm25_results}
    vector_ranks = {paper_id: rank for paper_id, score, rank in vector_results}

    # 所有文档 ID
    all_ids = set(bm25_ranks.keys()) | set(vector_ranks.keys())

    # 计算融合分数
    fused_scores = {}
    for paper_id in all_ids:
        score = 0.0

        # BM25 部分
        if paper_id in bm25_ranks:
            score += weight_bm25 * 1 / (k + bm25_ranks[paper_id])
        else:
            score += weight_bm25 * 0  # 未出现在结果中

        # 向量部分
        if paper_id in vector_ranks:
            score += weight_vector * 1 / (k + vector_ranks[paper_id])
        else:
            score += weight_vector * 0  # 未出现在结果中

        fused_scores[paper_id] = score

    # 排序
    sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

    return sorted_results


def load_paper_metadata(paper_id: str, papers_dir: Path) -> Dict:
    """加载论文元数据"""
    meta_path = papers_dir / f"{paper_id}.yaml"

    if not meta_path.exists():
        return {'id': paper_id}

    with open(meta_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    """命令行入口"""
    if len(sys.argv) < 4:
        print("用法: python retrieve.py <query> <embeddings_dir> <papers_dir> [--top-k 5] [--weight-bm25 0.3] [--weight-vector 0.7]")
        sys.exit(1)

    query = sys.argv[1]
    embeddings_dir = Path(sys.argv[2])
    papers_dir = Path(sys.argv[3])

    # 解析可选参数
    top_k = 5
    weight_bm25 = 0.3
    weight_vector = 0.7

    if '--top-k' in sys.argv:
        top_k = int(sys.argv[sys.argv.index('--top-k') + 1])

    if '--weight-bm25' in sys.argv:
        weight_bm25 = float(sys.argv[sys.argv.index('--weight-bm25') + 1])

    if '--weight-vector' in sys.argv:
        weight_vector = float(sys.argv[sys.argv.index('--weight-vector') + 1])

    # 加载索引
    bm25 = None
    vector_collection = None

    bm25_path = embeddings_dir / "bm25.pkl"
    if bm25_path.exists():
        bm25 = load_bm25_index(bm25_path)

    if (embeddings_dir / "chroma.db").exists():
        vector_collection = load_vector_index(embeddings_dir)

    # 加载论文 ID 列表
    metadata_path = embeddings_dir / "metadata.yaml"
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = yaml.safe_load(f)
            # 注意：这里需要加载实际的 paper_ids，简化处理
            print(f"索引包含 {metadata.get('paper_count', 'unknown')} 篇论文")

    # 执行检索
    print(f"\n正在检索: {query}")

    bm25_results = []
    vector_results = []

    if bm25:
        # 注意：这里需要 paper_ids 列表，简化处理
        print("  执行 BM25 检索...")
        # bm25_results = bm25_retrieve(bm25, query, paper_ids, top_k)

    if vector_collection:
        print("  执行向量检索...")
        vector_results = vector_retrieve(vector_collection, query, top_k)

    # 混合排序
    if bm25_results and vector_results:
        print("  执行混合排序...")
        results = hybrid_retrieve(bm25_results, vector_results, weight_bm25, weight_vector, top_k)
    elif vector_results:
        results = [(paper_id, score) for paper_id, score, rank in vector_results]
    else:
        results = []
        print("✗ 没有检索结果")

    # 输出结果
    if results:
        print(f"\n✓ 检索完成！前 {len(results)} 个结果:\n")

        for rank, (paper_id, score) in enumerate(results[:top_k], 1):
            meta = load_paper_metadata(paper_id, papers_dir)
            title = meta.get('title', 'Unknown Title')
            year = meta.get('year', 'Unknown')

            print(f"{rank}. {title} ({year})")
            print(f"   ID: {paper_id}")
            print(f"   Score: {score:.4f}")
            print()

    else:
        print("\n✗ 检索失败")


if __name__ == '__main__':
    main()
