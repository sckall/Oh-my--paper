#!/usr/bin/env python3
"""
演示：分析 Computers & Education 期刊的模拟数据
生成期刊画像和写作风格指南
"""

import yaml
from pathlib import Path
from collections import Counter
import re

def analyze_journal(journal_dir: Path):
    """分析期刊数据并生成报告"""
    
    papers_dir = journal_dir / "papers"
    analysis_dir = journal_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    
    # 读取所有论文元数据
    papers = []
    for yaml_file in papers_dir.glob("*.yaml"):
        with open(yaml_file, 'r', encoding='utf-8') as f:
            paper = yaml.safe_load(f)
            papers.append(paper)
    
    if not papers:
        print("❌ 未找到论文数据")
        return
    
    print(f"✓ 找到 {len(papers)} 篇论文，开始分析...")
    
    # 1. 分析标题风格
    title_analysis = analyze_titles([p['title'] for p in papers])
    
    # 2. 分析行文风格（基于 section_structure）
    style_analysis = analyze_writing_style(papers)
    
    # 3. 分析实证性
    empirical_analysis = analyze_empirical(papers)
    
    # 4. 生成期刊画像
    generate_journal_profile(journal_dir, papers, title_analysis, style_analysis, empirical_analysis)
    
    # 5. 生成写作风格指南
    generate_style_guide(journal_dir, title_analysis, style_analysis)
    
    print(f"\n✅ 分析完成！结果已保存到 {analysis_dir}")

def analyze_titles(titles):
    """分析标题风格"""
    print("\n📊 分析标题风格...")
    
    # 统计标题长度
    title_lengths = [len(t.split()) for t in titles]
    avg_length = sum(title_lengths) / len(title_lengths)
    
    # 检测标题结构
    colon_count = sum(1 for t in titles if ':' in t)
    question_count = sum(1 for t in titles if t.endswith('?'))
    
    # 提取高频词
    all_words = ' '.join(titles).lower()
    words = re.findall(r'\b\w+\b', all_words)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'through', 'via', 'using', 'based'}
    filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
    high_freq_words = [word for word, count in Counter(filtered_words).most_common(10)]
    
    result = {
        'avg_length_words': round(avg_length, 1),
        'length_range': [min(title_lengths), max(title_lengths)],
        'structure': {
            'colon_separated': round(colon_count / len(titles), 2),
            'question': round(question_count / len(titles), 2),
            'declarative': round(1 - (colon_count + question_count) / len(titles), 2)
        },
        'high_freq_words': high_freq_words[:5]
    }
    
    print(f"  - 平均长度: {result['avg_length_words']} 词")
    print(f"  - 冒号分隔: {result['structure']['colon_separated']*100:.0f}%")
    print(f"  - 疑问句: {result['structure']['question']*100:.0f}%")
    
    return result

def analyze_writing_style(papers):
    """分析行文风格"""
    print("\n📝 分析行文风格...")
    
    # 统计常见章节
    all_sections = []
    for paper in papers:
        if 'section_structure' in paper and paper['section_structure']:
            all_sections.extend(paper['section_structure'])
    
    section_counts = Counter(all_sections)
    common_sections = [s for s, count in section_counts.most_common(10)]
    
    result = {
        'common_sections': common_sections,
        'empirical_focus': True,
        'methodology_required': True
    }
    
    print(f"  - 常见章节: {', '.join(common_sections[:5])}")
    
    return result

def analyze_empirical(papers):
    """分析实证性倾向"""
    print("\n🔬 分析实证性...")
    
    empirical_count = sum(1 for p in papers if p.get('empirical', False))
    empirical_ratio = empirical_count / len(papers) if papers else 0
    
    result = {
        'empirical_ratio': round(empirical_ratio, 2),
        'theoretical_ratio': round(1 - empirical_ratio, 2)
    }
    
    print(f"  - 实证论文比例: {result['empirical_ratio']*100:.0f}%")
    
    return result

def generate_journal_profile(journal_dir, papers, title_analysis, style_analysis, empirical_analysis):
    """生成期刊画像"""
    print("\n📄 生成期刊画像...")
    
    profile_path = journal_dir / "analysis" / "journal_profile.md"
    
    with open(profile_path, 'w', encoding='utf-8') as f:
        f.write("# 期刊画像：Computers & Education\n\n")
        f.write("## 基本信息\n")
        f.write("- **期刊名称**：Computers & Education\n")
        f.write("- **出版社**：Elsevier\n")
        f.write(f"- **分析论文数**：{len(papers)} 篇\n")
        f.write(f"- **分析时间**：2026-05-02\n\n")
        
        f.write("## 标题风格\n")
        f.write(f"- **平均长度**：{title_analysis['avg_length_words']} 个单词\n")
        f.write(f"- **常见结构**：{title_analysis['structure']['colon_separated']*100:.0f}% 使用冒号分隔，{title_analysis['structure']['question']*100:.0f}% 为疑问句\n")
        f.write(f"- **高频词**：{', '.join(title_analysis['high_freq_words'])}\n\n")
        
        f.write("## 行文风格\n")
        f.write(f"- **常见章节**：{', '.join(style_analysis['common_sections'][:5])}\n")
        f.write(f"- **实证聚焦**：是\n")
        f.write(f"- **方法论要求**：是\n\n")
        
        f.write("## 实证性倾向\n")
        f.write(f"- **实证论文比例**：{empirical_analysis['empirical_ratio']*100:.0f}%\n")
        f.write(f"- **理论/综述比例**：{empirical_analysis['theoretical_ratio']*100:.0f}%\n\n")
        
        f.write("## 投稿建议\n")
        f.write("1. 标题建议使用冒号分隔结构或疑问句形式\n")
        f.write("2. 必须包含实证研究，有明确的假设和研究问题\n")
        f.write("3. Methodology 部分必须详细描述参与者、数据收集工具、分析方法\n")
        f.write("4. Results 部分必须包含统计分析结果（p-value、effect size）\n")
        f.write("5. Discussion 部分必须讨论实践意义（practical implications）\n")
    
    print(f"  ✓ 已保存: {profile_path}")

def generate_style_guide(journal_dir, title_analysis, style_analysis):
    """生成写作风格指南"""
    print("\n📋 生成写作风格指南...")
    
    guide_path = journal_dir / "analysis" / "style_guide.md"
    
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write("# 写作风格指南：Computers & Education\n\n")
        
        f.write("## 标题\n")
        f.write(f"- 长度：{title_analysis['length_range'][0]}-{title_analysis['length_range'][1]} 个单词\n")
        f.write("- 结构：推荐使用冒号分隔或疑问句\n")
        f.write("- 示例：\n")
        f.write("  - \"Enhancing student engagement through AI: A mixed-methods study\"\n")
        f.write("  - \"What makes a good online teacher? Student perceptions\"\n\n")
        
        f.write("## Abstract\n")
        f.write("- 长度：150-250 词\n")
        f.write("- 结构：Purpose, Methods, Results, Conclusions\n")
        f.write("- 必须包含：研究问题、方法、主要发现、实践意义\n\n")
        
        f.write("## Introduction\n")
        f.write("- 必须包含：研究背景、问题陈述、研究目标、研究问题/假设\n")
        f.write("- 长度：建议 2-3 页\n\n")
        
        f.write("## Methodology\n")
        f.write("- 必须包含：研究设计、参与者描述、数据收集工具、数据分析方法\n")
        f.write("- 细节程度：其他研究者可以复现\n\n")
        
        f.write("## Results\n")
        f.write("- 必须包含：描述性统计、推断性统计、效应量\n")
        f.write("- 表格/图表：清晰、标注完整、符合 APA 格式\n\n")
        
        f.write("## Discussion\n")
        f.write("- 必须包含：主要发现解释、与文献对比、实践意义、研究局限\n")
        f.write("- 强调：实践意义（practical implications）\n\n")
        
        f.write("## 引用格式\n")
        f.write("- 必须使用 APA 7th Edition 格式\n")
        f.write("- DOI：尽可能提供\n")
    
    print(f"  ✓ 已保存: {guide_path}")

if __name__ == '__main__':
    # 项目根目录（脚本位于 skills/omp:journal-analyze/scripts/，需要向上 4 级）
    project_root = Path(__file__).parent.parent.parent.parent
    journal_dir = project_root / ".my-paper" / "journals" / "computers-and-education"
    
    print("="*60)
    print("期刊分析演示：Computers & Education")
    print("="*60)
    
    analyze_journal(journal_dir)
