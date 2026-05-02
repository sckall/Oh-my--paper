#!/usr/bin/env python3
"""
题材偏好分析脚本 - LDA 主题建模或关键词聚类

依赖：
- scikit-learn: pip install scikit-learn
- numpy: pip install numpy
"""

import sys
import yaml
from pathlib import Path
from typing import List, Dict, Tuple
import re


def load_paper_data(papers_dir: Path) -> List[Dict]:
    """
    加载论文元数据

    Args:
        papers_dir: 论文目录路径

    Returns:
        论文元数据列表
    """
    papers = []

    for yaml_file in papers_dir.glob("*.yaml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                paper = yaml.safe_load(f)
                if paper:
                    papers.append(paper)
        except Exception as e:
            print(f"警告: 无法加载 {yaml_file.name} - {e}")

    print(f"✓ 已加载 {len(papers)} 篇论文元数据")
    return papers


def extract_text_features(papers: List[Dict]) -> List[str]:
    """
    从论文元数据中提取文本特征

    Args:
        papers: 论文元数据列表

    Returns:
        文本特征列表（标题 + 关键词）
    """
    texts = []

    for paper in papers:
        # 组合标题和关键词
        title = paper.get('title', '')
        keywords = paper.get('keywords', [])

        text = title
        if keywords:
            text += ' ' + ' '.join(keywords)

        texts.append(text)

    return texts


def analyze_with_lda(texts: List[str], num_topics: int = 5) -> List[Dict]:
    """
    使用 LDA 进行主题建模

    Args:
        texts: 文本特征列表
        num_topics: 主题数量

    Returns:
        主题列表，每个主题包含关键词和权重
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import LatentDirichletAllocation
    except ImportError:
        print("错误: scikit-learn 未安装")
        print("安装命令: pip install scikit-learn")
        return []

    print(f"正在进行 LDA 主题建模（{num_topics} 个主题）...")

    # 1. 创建 TF-IDF 向量izer
    # 注意：中文需要分词，这里使用简化版（按空格分词）
    vectorizer = TfidfVectorizer(
        max_df=0.95,
        min_df=2,
        stop_words=None  # 中文需要自定义停用词
    )

    try:
        tfidf = vectorizer.fit_transform(texts)
    except ValueError as e:
        print(f"警告: TF-IDF 向量化失败 - {e}")
        print("提示: 如果处理中文文本，建议使用分词工具（如 jieba）")
        return []

    # 2. 训练 LDA 模型
    lda = LatentDirichletAllocation(
        n_components=num_topics,
        max_iter=10,
        learning_method='online',
        random_state=42
    )

    lda.fit(tfidf)

    # 3. 提取主题关键词
    feature_names = vectorizer.get_feature_names_out()
    topics = []

    for topic_idx, topic in enumerate(lda.components_):
        # 获取权重最高的 10 个词
        top_features_idx = topic.argsort()[:-11:-1]
        top_features = [feature_names[i] for i in top_features_idx]

        topics.append({
            'topic_id': topic_idx + 1,
            'keywords': top_features,
            'weight': float(topic[top_features_idx].mean())  # 平均权重
        })

    print(f"✓ LDA 主题建模完成")
    return topics


def analyze_with_clustering(texts: List[str], num_clusters: int = 5) -> List[Dict]:
    """
    使用 TF-IDF + KMeans 进行关键词聚类

    Args:
        texts: 文本特征列表
        num_clusters: 聚类数量

    Returns:
        聚类列表，每个聚类包含关键词
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import KMeans
    except ImportError:
        print("错误: scikit-learn 未安装")
        return []

    print(f"正在进行关键词聚类（{num_clusters} 个聚类）...")

    # 1. 创建 TF-IDF 向量izer
    vectorizer = TfidfVectorizer(
        max_df=0.95,
        min_df=2,
        stop_words=None
    )

    try:
        tfidf = vectorizer.fit_transform(texts)
    except ValueError as e:
        print(f"警告: TF-IDF 向量化失败 - {e}")
        return []

    # 2. KMeans 聚类
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    kmeans.fit(tfidf)

    # 3. 提取每个聚类的关键词
    feature_names = vectorizer.get_feature_names_out()
    clusters = []

    for cluster_idx in range(num_clusters):
        # 获取属于该聚类的文档
        cluster_docs = [i for i, label in enumerate(kmeans.labels_) if label == cluster_idx]

        # 计算该聚类中所有词的平均 TF-IDF 值
        cluster_tfidf = tfidf[cluster_docs].mean(axis=0).A1
        top_features_idx = cluster_tfidf.argsort()[:-11:-1]
        top_features = [feature_names[i] for i in top_features_idx]

        clusters.append({
            'cluster_id': cluster_idx + 1,
            'keywords': top_features,
            'doc_count': len(cluster_docs),
            'percentage': len(cluster_docs) / len(texts) * 100
        })

    print(f"✓ 关键词聚类完成")
    return clusters


def save_topic_distribution(topics: List[Dict], output_path: Path) -> None:
    """
    保存题材分布分析结果

    Args:
        topics: 主题或聚类列表
        output_path: 输出文件路径
    """
    # 计算百分比（简化版：平均分配）
    total = len(topics)
    for topic in topics:
        if 'percentage' not in topic:
            topic['percentage'] = round(100 / total, 1)

    # 构建 YAML 结构
    result = {
        'topic_distribution': []
    }

    for topic in topics:
        if 'keywords' in topic:
            result['topic_distribution'].append({
                'topic': f"主题 {topic.get('topic_id', topic.get('cluster_id', 0))}",
                'keywords': topic['keywords'][:5],  # 只保留前 5 个关键词
                'percentage': topic['percentage']
            })

    # 保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(result, f, allow_unicode=True, sort_keys=False)

    print(f"✓ 已保存题材分布分析: {output_path}")


def main():
    """命令行入口"""
    if len(sys.argv) < 3:
        print("用法: python topic_modeling.py <papers_dir> <output_path> [--method lda|clustering] [--num 5]")
        sys.exit(1)

    papers_dir = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    # 解析可选参数
    method = 'lda'
    num = 5

    if '--method' in sys.argv:
        method = sys.argv[sys.argv.index('--method') + 1]

    if '--num' in sys.argv:
        num = int(sys.argv[sys.argv.index('--num') + 1])

    # 加载论文数据
    papers = load_paper_data(papers_dir)
    if not papers:
        print("错误: 没有找到论文数据")
        sys.exit(1)

    # 提取文本特征
    texts = extract_text_features(papers)

    # 分析
    if method == 'lda':
        topics = analyze_with_lda(texts, num)
    else:
        topics = analyze_with_clustering(texts, num)

    if topics:
        # 保存结果
        save_topic_distribution(topics, output_path)
        print(f"\n✓ 题材偏好分析完成！共识别 {len(topics)} 个主题/聚类")
    else:
        print("\n✗ 题材偏好分析失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
