#!/usr/bin/env python3
"""
索引构建脚本 - 构建 BM25 和/或向量索引

依赖：
- rank_bm25: pip install rank-bm25
- sentence-transformers: pip install sentence-transformers
- chromadb: pip install chromadb
"""

import sys
import pickle
import yaml
from pathlib import Path
from typing import List, Dict, Optional

# 尝试导入 BM25
try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

# 尝试导入 sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    HAS_ST = True
except ImportError:
    HAS_ST = False

# 尝试导入 Chroma
try:
    import chromadb
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False


def load_paper_texts(papers_dir: Path) -> tuple[List[str], List[str]]:
    """
    加载论文文本

    Returns:
        (paper_ids, texts)
    """
    paper_ids = []
    texts = []

    # 加载元数据
    for yaml_file in papers_dir.glob("*.yaml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                paper = yaml.safe_load(f)

            if not paper:
                continue

            paper_id = paper.get('id', yaml_file.stem)
            paper_ids.append(paper_id)

            # 组合标题、关键词、摘要
            title = paper.get('title', '')
            keywords = ' '.join(paper.get('keywords', []))
            abstract = paper.get('abstract', '')

            text = f"{title}. {abstract}"
            if keywords:
                text += f" Keywords: {keywords}."

            # 尝试加载全文
            md_path = papers_dir / f"{paper_id}.md"
            if md_path.exists():
                try:
                    with open(md_path, 'r', encoding='utf-8') as f:
                        full_text = f.read()
                    # 只取前 2000 字符（避免过长）
                    text += f"\n{full_text[:2000]}"
                except Exception:
                    pass

            texts.append(text)

        except Exception as e:
            print(f"警告: 无法加载 {yaml_file.name} - {e}")

    print(f"✓ 已加载 {len(texts)} 篇论文文本")
    return paper_ids, texts


def build_bm25_index(texts: List[str], output_path: Path) -> Optional[object]:
    """
    构建 BM25 索引

    Args:
        texts: 文本列表
        output_path: 输出文件路径

    Returns:
        BM25 索引对象，如果失败则返回 None
    """
    if not HAS_BM25:
        print("警告: rank_bm25 未安装，跳过 BM25 索引")
        print("安装命令: pip install rank-bm25")
        return None

    print("正在构建 BM25 索引...")

    # 分词（简化版：按空格分词）
    tokenized_texts = [text.split() for text in texts]

    # 构建 BM25 索引
    bm25 = BM25Okapi(tokenized_texts)

    # 保存索引
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        pickle.dump(bm25, f)

    print(f"✓ BM25 索引已保存: {output_path}")
    return bm25


def build_vector_index(paper_ids: List[str], texts: List[str],
                      output_dir: Path, model_name: str = 'all-MiniLM-L6-v2') -> Optional[object]:
    """
    构建向量索引（使用 Chroma）

    Args:
        paper_ids: 论文 ID 列表
        texts: 文本列表
        output_dir: 输出目录
        model_name: 向量模型名称

    Returns:
        向量数据库对象，如果失败则返回 None
    """
    if not HAS_ST:
        print("警告: sentence-transformers 未安装，跳过向量索引")
        print("安装命令: pip install sentence-transformers")
        return None

    if not HAS_CHROMA:
        print("警告: chromadb 未安装，跳过向量索引")
        print("安装命令: pip install chromadb")
        return None

    print(f"正在构建向量索引（模型: {model_name}）...")

    # 1. 加载向量模型
    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        print(f"错误: 无法加载向量模型 - {e}")
        return None

    # 2. 生成向量
    print("  正在生成向量...")
    embeddings = model.encode(texts, show_progress_bar=True)

    # 3. 存储到 Chroma
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        client = chromadb.PersistentClient(path=str(output_dir))

        # 创建或获取集合
        collection = client.get_or_create_collection(
            name="papers",
            metadata={"hnsw:space": "cosine"}
        )

        # 添加文档
        collection.add(
            embeddings=embeddings.tolist(),
            documents=texts,
            ids=paper_ids
        )

        print(f"✓ 向量索引已保存: {output_dir}")
        return collection

    except Exception as e:
        print(f"错误: 无法保存到 Chroma - {e}")
        return None


def save_metadata(paper_ids: List[str], papers_dir: Path, output_path: Path) -> None:
    """
    保存索引元数据

    Args:
        paper_ids: 论文 ID 列表
        papers_dir: 论文目录路径
        output_path: 输出文件路径
    """
    metadata = {
        'paper_count': len(paper_ids),
        'papers_dir': str(papers_dir),
        'created_at': __import__('datetime').datetime.now().isoformat()
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(metadata, f, allow_unicode=True, sort_keys=False)

    print(f"✓ 元数据已保存: {output_path}")


def main():
    """命令行入口"""
    if len(sys.argv) < 3:
        print("用法: python build_index.py <papers_dir> <output_dir> [--methods bm25|vector|both] [--model model_name]")
        sys.exit(1)

    papers_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    # 解析可选参数
    methods = 'both'
    model_name = 'all-MiniLM-L6-v2'

    if '--methods' in sys.argv:
        methods = sys.argv[sys.argv.index('--methods') + 1]

    if '--model' in sys.argv:
        model_name = sys.argv[sys.argv.index('--model') + 1]

    if not papers_dir.exists():
        print(f"错误: 论文目录不存在 - {papers_dir}")
        sys.exit(1)

    # 加载论文文本
    paper_ids, texts = load_paper_texts(papers_dir)

    if not paper_ids:
        print("错误: 没有找到论文数据")
        sys.exit(1)

    # 构建索引
    if methods in ['bm25', 'both']:
        bm25_path = output_dir / 'bm25.pkl'
        build_bm25_index(texts, bm25_path)

    if methods in ['vector', 'both']:
        chroma_dir = output_dir / 'chroma.db'
        build_vector_index(paper_ids, texts, chroma_dir, model_name)

    # 保存元数据
    metadata_path = output_dir / 'metadata.yaml'
    save_metadata(paper_ids, papers_dir, metadata_path)

    print(f"\n✓ 索引构建完成！共处理 {len(paper_ids)} 篇论文")


if __name__ == '__main__':
    main()
