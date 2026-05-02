#!/usr/bin/env python3
"""
自进化插件脚本 - 实现反馈学习和自动调参

依赖：
- numpy: pip install numpy
"""

import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def load_feedback(embeddings_dir: Path) -> List[Dict]:
    """加载反馈数据"""
    feedback_path = embeddings_dir / "feedback.json"

    if not feedback_path.exists():
        return []

    with open(feedback_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_feedback(feedback_data: List[Dict], embeddings_dir: Path) -> None:
    """保存反馈数据"""
    feedback_path = embeddings_dir / "feedback.json"
    embeddings_dir.mkdir(parents=True, exist_ok=True)

    with open(feedback_path, 'w', encoding='utf-8') as f:
        json.dump(feedback_data, f, ensure_ascii=False, indent=2)

    print(f"✓ 已保存反馈数据: {feedback_path}")


def add_feedback(query: str, rating: int, relevant_ids: List[str],
                 embeddings_dir: Path) -> None:
    """
    添加用户反馈

    Args:
        query: 查询字符串
        rating: 评分（1-5）
        relevant_ids: 相关论文 ID 列表
        embeddings_dir: 嵌入目录路径
    """
    feedback_data = load_feedback(embeddings_dir)

    # 生成查询 ID
    query_id = f"QRY-{len(feedback_data) + 1:03d}"

    # 创建反馈记录
    feedback = {
        'query_id': query_id,
        'query': query,
        'timestamp': datetime.now().isoformat(),
        'rating': rating,
        'relevant_ids': relevant_ids
    }

    feedback_data.append(feedback)
    save_feedback(feedback_data, embeddings_dir)

    print(f"✓ 已添加反馈: {query_id}")
    print(f"  查询: {query}")
    print(f"  评分: {rating}/5")
    print(f"  相关论文数: {len(relevant_ids)}")


def analyze_feedback(feedback_data: List[Dict]) -> Dict:
    """
    分析反馈数据

    Returns:
        分析结果（准确率、权重建议等）
    """
    if not feedback_data:
        return {'count': 0}

    # 计算平均评分
    avg_rating = sum(f['rating'] for f in feedback_data) / len(feedback_data)

    # 计算相关论文比例
    total_relevant = sum(len(f['relevant_ids']) for f in feedback_data)
    avg_relevant = total_relevant / len(feedback_data)

    result = {
        'count': len(feedback_data),
        'avg_rating': round(avg_rating, 2),
        'avg_relevant_count': round(avg_relevant, 2),
        'last_updated': datetime.now().isoformat()
    }

    return result


def optimize_weights(embeddings_dir: Path, learning_rate: float = 0.1) -> Dict:
    """
    根据反馈数据优化权重

    Args:
        embeddings_dir: 嵌入目录路径
        learning_rate: 学习率

    Returns:
        优化后的权重
    """
    feedback_data = load_feedback(embeddings_dir)

    if len(feedback_data) < 5:
        print(f"警告: 反馈数据不足（{len(feedback_data)} 条），需要至少 5 条")
        return {'weight_bm25': 0.3, 'weight_vector': 0.7}

    # 分析反馈
    analysis = analyze_feedback(feedback_data)

    # 简化版：根据平均评分调整权重
    avg_rating = analysis['avg_rating']

    # 评分高（>= 4）：向量检索效果更好
    # 评分低（< 4）：BM25 可能更好
    if avg_rating >= 4.0:
        weight_vector = min(0.9, 0.7 + learning_rate)
    elif avg_rating <= 2.5:
        weight_vector = max(0.1, 0.7 - learning_rate)
    else:
        weight_vector = 0.7  # 保持不变

    weight_bm25 = 1.0 - weight_vector

    result = {
        'weight_bm25': round(weight_bm25, 2),
        'weight_vector': round(weight_vector, 2),
        'based_on_feedback': len(feedback_data),
        'avg_rating': avg_rating
    }

    # 保存优化日志
    log_path = embeddings_dir / "optimization-log.json"
    log_data = []

    if log_path.exists():
        with open(log_path, 'r', encoding='utf-8') as f:
            log_data = json.load(f)

    log_data.append({
        'timestamp': datetime.now().isoformat(),
        'weights': result,
        'analysis': analysis
    })

    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    print(f"✓ 权重优化完成")
    print(f"  新权重: BM25={weight_bm25:.2f}, Vector={weight_vector:.2f}")
    print(f"  基于 {len(feedback_data)} 条反馈数据")

    return result


def expand_knowledge_base(query: str, relevant_ids: List[str],
                        journal_id: str, papers_dir: Path) -> None:
    """
    扩展知识库（根据反馈自动添加相关论文）

    Args:
        query: 查询字符串
        relevant_ids: 相关论文 ID 列表
        journal_id: 期刊 ID
        papers_dir: 论文目录路径
    """
    # 简化版：只打印提示，不实际执行
    print(f"提示: 根据查询 '{query}' 和相关论文，建议添加以下论文到知识库:")
    for paper_id in relevant_ids:
        print(f"  - {paper_id}")

    print("注意: 自动扩展功能需要集成外部 API（如 arXiv、Semantic Scholar）")


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  添加反馈: python evolve.py add-feedback <query> <rating> <relevant-ids> <embeddings-dir>")
        print("  分析反馈: python evolve.py analyze <embeddings-dir>")
        print("  优化权重: python evolve.py optimize <embeddings-dir> [learning-rate]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'add-feedback':
        if len(sys.argv) < 6:
            print("用法: python evolve.py add-feedback <query> <rating> <relevant-ids> <embeddings-dir>")
            sys.exit(1)

        query = sys.argv[2]
        rating = int(sys.argv[3])
        relevant_ids = sys.argv[4].split(',')
        embeddings_dir = Path(sys.argv[5])

        add_feedback(query, rating, relevant_ids, embeddings_dir)

    elif command == 'analyze':
        embeddings_dir = Path(sys.argv[2])
        feedback_data = load_feedback(embeddings_dir)
        analysis = analyze_feedback(feedback_data)

        print(f"\n✓ 反馈分析完成:")
        print(f"  反馈数量: {analysis['count']}")
        if analysis['count'] > 0:
            print(f"  平均评分: {analysis['avg_rating']}/5")
            print(f"  平均相关论文数: {analysis['avg_relevant_count']}")

    elif command == 'optimize':
        embeddings_dir = Path(sys.argv[2])
        learning_rate = float(sys.argv[3]) if len(sys.argv) > 3 else 0.1

        optimize_weights(embeddings_dir, learning_rate)

    else:
        print(f"错误: 未知命令 - {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
