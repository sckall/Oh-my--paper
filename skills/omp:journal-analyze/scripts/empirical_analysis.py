#!/usr/bin/env python3
"""
实证性分析脚本 - 判断论文是理论型还是实证型

依赖：
- numpy: pip install numpy
"""

import sys
import re
import yaml
from pathlib import Path
from typing import Dict, List
from collections import Counter


def load_paper_metadata(papers_dir: Path) -> List[Dict]:
    """加载论文元数据"""
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


def analyze_empirical_tendency(papers: List[Dict], papers_dir: Path) -> Dict:
    """
    分析实证性倾向

    Returns:
        实证性分析结果
    """
    print("正在分析实证性倾向...")

    empirical_count = 0
    theoretical_count = 0
    common_datasets = Counter()
    evaluation_metrics = Counter()

    for paper in papers:
        paper_id = paper.get('id', 'unknown')

        # 1. 检查是否已标记 empirical 字段
        if paper.get('empirical') is not None:
            if paper['empirical']:
                empirical_count += 1
            else:
                theoretical_count += 1
            continue

        # 2. 检查章节结构
        section_structure = paper.get('section_structure', [])
        has_experiment = any(
            keyword in ' '.join(section_structure).lower()
            for keyword in ['experiment', '实验', 'evaluation', '评估', 'result', '结果']
        )

        # 3. 检查关键词
        keywords = paper.get('keywords', [])
        has_empirical_keyword = any(
            keyword in ' '.join(keywords).lower()
            for keyword in ['experiment', '实验', 'dataset', '数据集', 'evaluation', '评估']
        )

        # 4. 尝试读取 Markdown 文件进行深度分析
        md_path = papers_dir / f"{paper_id}.md"
        has_dataset_mention = False
        has_result_table = False

        if md_path.exists():
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 查找数据集提及
                dataset_patterns = [
                    r'dataset:\s*(\w+)',
                    r'使用\s*(\w+)\s*数据集',
                    r'(\w+)\s*dataset'
                ]
                for pattern in dataset_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        common_datasets[match] += 1

                # 检查是否有结果表格
                if '|' in content and '-+-' in content:
                    has_result_table = True

                # 查找评估指标
                metric_patterns = ['accuracy', 'precision', 'recall', 'f1', 'bleu', 'rouge']
                for metric in metric_patterns:
                    if metric in content.lower():
                        evaluation_metrics[metric] += 1

            except Exception as e:
                print(f"警告: 无法读取 {md_path.name} - {e}")

        # 5. 判断是否为实证论文
        is_empirical = has_experiment or has_empirical_keyword or has_result_table

        if is_empirical:
            empirical_count += 1
        else:
            theoretical_count += 1

    # 计算比例
    total = len(papers)
    if total == 0:
        print("警告: 没有找到论文数据")
        return {}

    empirical_ratio = empirical_count / total
    theoretical_ratio = theoretical_count / total

    # 构建结果
    result = {
        'empirical_tendency': {
            'empirical_ratio': round(empirical_ratio, 2),
            'theoretical_ratio': round(theoretical_ratio, 2),
            'common_datasets': [dataset for dataset, count in common_datasets.most_common(5)],
            'evaluation_metrics': [metric for metric, count in evaluation_metrics.most_common(5)]
        }
    }

    print(f"✓ 实证性分析完成")
    print(f"  实证论文比例: {empirical_ratio:.2%}")
    print(f"  理论论文比例: {theoretical_ratio:.2%}")

    if common_datasets:
        print(f"  常用数据集: {', '.join(common_datasets.most_common(3))}")

    return result


def save_empirical_analysis(result: Dict, output_path: Path) -> None:
    """
    保存实证性分析结果

    Args:
        result: 分析结果
        output_path: 输出文件路径
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(result, f, allow_unicode=True, sort_keys=False)

    print(f"✓ 已保存实证性分析: {output_path}")


def main():
    """命令行入口"""
    if len(sys.argv) < 3:
        print("用法: python empirical_analysis.py <papers_dir> <output_path>")
        sys.exit(1)

    papers_dir = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not papers_dir.exists():
        print(f"错误: 论文目录不存在 - {papers_dir}")
        sys.exit(1)

    # 加载论文数据
    papers = load_paper_metadata(papers_dir)

    if not papers:
        print("错误: 没有找到论文数据")
        sys.exit(1)

    # 分析实证性倾向
    result = analyze_empirical_tendency(papers, papers_dir)

    if result:
        # 保存结果
        save_empirical_analysis(result, output_path)
        print(f"\n✓ 实证性分析完成！")
    else:
        print("\n✗ 实证性分析失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
