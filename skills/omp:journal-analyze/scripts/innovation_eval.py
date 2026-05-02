#!/usr/bin/env python3
"""
创新性评估脚本 - 评估论文的创新性

依赖：
- numpy: pip install numpy
"""

import sys
import re
import yaml
from pathlib import Path
from typing import Dict, List


def load_paper_data(papers_dir: Path) -> List[Dict]:
    """加载论文元数据和全文"""
    papers = []

    for yaml_file in papers_dir.glob("*.yaml"):
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                paper = yaml.safe_load(f)

            if paper:
                # 尝试加载对应的 Markdown 文件
                paper_id = paper.get('id', yaml_file.stem)
                md_path = papers_dir / f"{paper_id}.md"

                if md_path.exists():
                    try:
                        with open(md_path, 'r', encoding='utf-8') as f:
                            paper['full_text'] = f.read()
                    except Exception:
                        paper['full_text'] = ''
                else:
                    paper['full_text'] = ''

                papers.append(paper)
        except Exception as e:
            print(f"警告: 无法加载 {yaml_file.name} - {e}")

    print(f"✓ 已加载 {len(papers)} 篇论文")
    return papers


def evaluate_innovation(papers: List[Dict]) -> Dict:
    """
    评估论文的创新性

    Returns:
        创新性评估结果
    """
    print("正在评估创新性...")

    methodology_innovation_count = 0
    application_innovation_count = 0
    innovation_scores = []

    # 创新相关关键词
    methodology_keywords = [
        'novel', 'new method', 'propose', 'introduce',
        '新方法', '提出', '设计', '改进'
    ]

    application_keywords = [
        'apply', 'application', 'use', 'utilize',
        '应用', '使用', '用于'
    ]

    for paper in papers:
        innovation_score = 0.0
        has_methodology_innovation = False
        has_application_innovation = False

        # 1. 检查标题
        title = paper.get('title', '').lower()

        if any(keyword in title for keyword in methodology_keywords):
            has_methodology_innovation = True
            innovation_score += 0.3

        if any(keyword in title for keyword in application_keywords):
            has_application_innovation = True
            innovation_score += 0.2

        # 2. 检查摘要和全文
        full_text = paper.get('full_text', '').lower()

        if full_text:
            # 查找创新相关短语
            novelty_patterns = [
                r'novel\s+\w+',
                r'new\s+\w+\s+method',
                r'we\s+propose',
                r'our\s+contribution',
                r'创新',
                r'首次',
                r'提出一种'
            ]

            for pattern in novelty_patterns:
                if re.search(pattern, full_text, re.IGNORECASE):
                    innovation_score += 0.1

            # 检查是否有数学公式（可能表示方法论创新）
            if '$' in full_text or '\\[' in full_text:
                innovation_score += 0.2

        # 3. 检查引用数（如果有）
        citation_count = paper.get('citation_count', 0)
        if citation_count > 50:
            innovation_score += 0.2
        elif citation_count > 20:
            innovation_score += 0.1

        # 限制分数在 0-1 之间
        innovation_score = min(innovation_score, 1.0)

        # 统计
        if has_methodology_innovation:
            methodology_innovation_count += 1

        if has_application_innovation:
            application_innovation_count += 1

        innovation_scores.append(innovation_score)

    # 计算平均创新评分
    avg_innovation_score = sum(innovation_scores) / len(innovation_scores) if innovation_scores else 0.0

    # 计算比例
    total = len(papers)
    methodology_innovation_ratio = methodology_innovation_count / total if total > 0 else 0.0
    application_innovation_ratio = application_innovation_count / total if total > 0 else 0.0

    # 识别常见贡献类型
    common_contributions = []

    if methodology_innovation_ratio > 0.3:
        common_contributions.append("提出新方法")

    if application_innovation_ratio > 0.3:
        common_contributions.append("跨领域应用")

    if methodology_innovation_ratio > 0.2 or application_innovation_ratio > 0.2:
        common_contributions.append("改进现有模型")

    # 构建结果
    result = {
        'innovation_metrics': {
            'avg_innovation_score': round(avg_innovation_score, 2),
            'methodology_innovation_ratio': round(methodology_innovation_ratio, 2),
            'application_innovation_ratio': round(application_innovation_ratio, 2),
            'common_contributions': common_contributions
        }
    }

    print(f"✓ 创新性评估完成")
    print(f"  平均创新评分: {avg_innovation_score:.2f}/1.0")
    print(f"  方法论创新比例: {methodology_innovation_ratio:.2%}")
    print(f"  应用创新比例: {application_innovation_ratio:.2%}")

    return result


def save_innovation_metrics(result: Dict, output_path: Path) -> None:
    """
    保存创新性评估结果

    Args:
        result: 评估结果
        output_path: 输出文件路径
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(result, f, allow_unicode=True, sort_keys=False)

    print(f"✓ 已保存创新性评估: {output_path}")


def main():
    """命令行入口"""
    if len(sys.argv) < 3:
        print("用法: python innovation_eval.py <papers_dir> <output_path>")
        sys.exit(1)

    papers_dir = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not papers_dir.exists():
        print(f"错误: 论文目录不存在 - {papers_dir}")
        sys.exit(1)

    # 加载论文数据
    papers = load_paper_data(papers_dir)

    if not papers:
        print("错误: 没有找到论文数据")
        sys.exit(1)

    # 评估创新性
    result = evaluate_innovation(papers)

    if result:
        # 保存结果
        save_innovation_metrics(result, output_path)
        print(f"\n✓ 创新性评估完成！")
    else:
        print("\n✗ 创新性评估失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
