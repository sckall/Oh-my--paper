#!/usr/bin/env python3
"""
生成 Computers & Education 期刊的模拟论文数据用于测试
"""

import yaml
import time
from pathlib import Path
from datetime import datetime

# Computers & Education 模拟论文数据
SAMPLE_PAPERS = [
    {
        'id': 'computers-and-education-2023-001',
        'title': 'Enhancing student engagement through AI-based chatbots: A mixed-methods study',
        'authors': [
            {'name': 'Smith, J.', 'affiliation': 'Stanford University', 'email': 'jsmith@stanford.edu'},
            {'name': 'Wang, L.', 'affiliation': 'MIT', 'email': 'lwang@mit.edu'}
        ],
        'year': 2023,
        'volume': 195,
        'issue': None,
        'pages': '104712',
        'doi': '10.1016/j.compedu.2023.104712',
        'keywords': ['AI', 'chatbot', 'student engagement', 'mixed-methods'],
        'section_structure': ['Abstract', 'Introduction', 'Literature Review', 'Methodology', 'Results', 'Discussion', 'Conclusions'],
        'empirical': True,
        'citation_count': 45,
        'url': 'https://doi.org/10.1016/j.compedu.2023.104712',
        'pdf_path': None,
        'markdown_path': 'papers/computers-and-education-2023-001.md',
        'abstract': 'This study investigates the impact of AI-based chatbots on student engagement in online learning environments. Using a mixed-methods approach, we collected data from 150 undergraduate students...',
        'created_at': '2026-05-02T09:00:00+08:00'
    },
    {
        'id': 'computers-and-education-2023-002',
        'title': 'What makes a good online teacher? Student perceptions and expectations in post-pandemic education',
        'authors': [
            {'name': 'Johnson, M.', 'affiliation': 'Harvard University', 'email': 'mjohnson@harvard.edu'}
        ],
        'year': 2023,
        'volume': 198,
        'issue': None,
        'pages': '104845',
        'doi': '10.1016/j.compedu.2023.104845',
        'keywords': ['online teaching', 'student perceptions', 'teacher quality', 'post-pandemic'],
        'section_structure': ['Abstract', 'Introduction', 'Literature Review', 'Methodology', 'Results', 'Discussion', 'Conclusions'],
        'empirical': True,
        'citation_count': 32,
        'url': 'https://doi.org/10.1016/j.compedu.2023.104845',
        'pdf_path': None,
        'markdown_path': 'papers/computers-and-education-2023-002.md',
        'abstract': 'This qualitative study explores student perceptions of effective online teaching practices in the post-pandemic era. Through semi-structured interviews with 40 students...',
        'created_at': '2026-05-02T09:05:00+08:00'
    },
    {
        'id': 'computers-and-education-2023-003',
        'title': 'Learning analytics in higher education: A systematic review of empirical research',
        'authors': [
            {'name': 'Brown, A.', 'affiliation': 'University of Edinburgh', 'email': 'a.brown@ed.ac.uk'},
            {'name': 'Davis, C.', 'affiliation': 'University of Melbourne', 'email': 'cdavis@unimelb.edu.au'}
        ],
        'year': 2023,
        'volume': 201,
        'issue': None,
        'pages': '104921',
        'doi': '10.1016/j.compedu.2023.104921',
        'keywords': ['learning analytics', 'systematic review', 'higher education', 'empirical research'],
        'section_structure': ['Abstract', 'Introduction', 'Methodology', 'Results', 'Discussion', 'Conclusions'],
        'empirical': True,
        'citation_count': 28,
        'url': 'https://doi.org/10.1016/j.compedu.2023.104921',
        'pdf_path': None,
        'markdown_path': 'papers/computers-and-education-2023-003.md',
        'abstract': 'This systematic review examines empirical research on learning analytics in higher education published between 2018 and 2022. Following PRISMA guidelines, we analyzed 85 studies...',
        'created_at': '2026-05-02T09:10:00+08:00'
    },
    {
        'id': 'computers-and-education-2024-001',
        'title': 'AI-generated feedback vs. teacher feedback: A comparative study of student satisfaction and learning outcomes',
        'authors': [
            {'name': 'Lee, H.', 'affiliation': 'Seoul National University', 'email': 'hlee@snu.ac.kr'},
            {'name': 'Chen, W.', 'affiliation': 'National Taiwan University', 'email': 'wchen@ntu.edu.tw'}
        ],
        'year': 2024,
        'volume': 210,
        'issue': None,
        'pages': '105012',
        'doi': '10.1016/j.compedu.2024.105012',
        'keywords': ['AI feedback', 'teacher feedback', 'student satisfaction', 'learning outcomes'],
        'section_structure': ['Abstract', 'Introduction', 'Literature Review', 'Methodology', 'Results', 'Discussion', 'Conclusions'],
        'empirical': True,
        'citation_count': 12,
        'url': 'https://doi.org/10.1016/j.compedu.2024.105012',
        'pdf_path': None,
        'markdown_path': 'papers/computers-and-education-2024-001.md',
        'abstract': 'This study compares the effectiveness of AI-generated feedback and teacher feedback in EFL writing contexts. Using a quasi-experimental design with 120 participants...',
        'created_at': '2026-05-02T09:15:00+08:00'
    },
    {
        'id': 'computers-and-education-2024-002',
        'title': 'The role of self-regulated learning in online STEM education: The impact of learning analytics dashboards',
        'authors': [
            {'name': 'Garcia, P.', 'affiliation': 'University of California, Berkeley', 'email': 'pgarcia@berkeley.edu'}
        ],
        'year': 2024,
        'volume': 215,
        'issue': None,
        'pages': '105156',
        'doi': '10.1016/j.compedu.2024.105156',
        'keywords': ['self-regulated learning', 'STEM education', 'learning analytics', 'dashboard'],
        'section_structure': ['Abstract', 'Introduction', 'Theoretical Framework', 'Methodology', 'Results', 'Discussion', 'Conclusions'],
        'empirical': True,
        'citation_count': 8,
        'url': 'https://doi.org/10.1016/j.compedu.2024.105156',
        'pdf_path': None,
        'markdown_path': 'papers/computers-and-education-2024-002.md',
        'abstract': 'This study examines the role of self-regulated learning (SRL) in online STEM education and the impact of learning analytics dashboards on SRL behaviors...',
        'created_at': '2026-05-02T09:20:00+08:00'
    }
]

# 模拟论文全文（Markdown 格式）
SAMPLE_MARKDOWNS = {
    'computers-and-education-2023-001': """# Enhancing student engagement through AI-based chatbots: A mixed-methods study

**Authors**: Smith, J. (Stanford University), Wang, L. (MIT)  
**Year**: 2023  
**DOI**: 10.1016/j.compedu.2023.104712  
**Citation Count**: 45

---

## Abstract

This study investigates the impact of AI-based chatbots on student engagement in online learning environments. Using a mixed-methods approach, we collected data from 150 undergraduate students across two semesters. Quantitative data were collected through pre- and post-surveys measuring engagement levels, while qualitative data were gathered through semi-structured interviews. Results show that students who interacted with AI chatbots demonstrated significantly higher levels of behavioral engagement (p < 0.01, d = 0.65) and emotional engagement (p < 0.05, d = 0.42) compared to the control group. Qualitative findings reveal that students appreciated the immediate feedback and 24/7 availability of chatbots, though some expressed concerns about the lack of human empathy.

## 1. Introduction

The rapid advancement of artificial intelligence (AI) has opened new possibilities for enhancing student engagement in online learning environments. Student engagement, a multifaceted construct encompassing behavioral, emotional, and cognitive dimensions (Fredricks et al., 2004), is a strong predictor of academic achievement and retention...

## 2. Literature Review

### 2.1 AI in Education

Recent years have witnessed growing interest in applying AI technologies to educational contexts. AI-based chatbots, in particular, have shown promise in providing personalized learning support (Hwang & Chang, 2021). However, empirical research on their impact on student engagement remains limited...

### 2.2 Student Engagement Theory

This study draws on Fredricks et al.'s (2004) three-dimensional model of student engagement...

## 3. Methodology

### 3.1 Research Design

A mixed-methods explanatory sequential design was employed (Creswell & Plano Clark, 2018). Quantitative data were collected first, followed by qualitative data to explain the quantitative findings.

### 3.2 Participants

150 undergraduate students enrolled in an introductory computer science course participated in this study...

### 3.3 Data Collection

**Quantitative**: Pre- and post-surveys using the University Student Engagement Inventory (USEI; Kahu et al., 2017)...  
**Qualitative**: Semi-structured interviews with 20 purposively selected students...

### 3.4 Data Analysis

Quantitative data were analyzed using independent samples t-tests and ANOVA. Qualitative data were analyzed using thematic analysis (Braun & Clarke, 2006)...

## 4. Results

### 4.1 Quantitative Findings

Students in the experimental group (n = 75) showed significant increases in behavioral engagement (M_pre = 3.21, M_post = 3.89, p < 0.01, d = 0.65) and emotional engagement (M_pre = 2.98, M_post = 3.41, p < 0.05, d = 0.42)...

### 4.2 Qualitative Findings

Three main themes emerged from the interview data: (1) Immediate feedback and support, (2) 24/7 availability, (3) Lack of human empathy...

## 5. Discussion

This study provides empirical evidence that AI-based chatbots can enhance student engagement in online learning environments. The findings align with previous research suggesting that immediate feedback promotes engagement (Hwang & Chang, 2021)...

### 5.1 Practical Implications

The findings suggest that educators should consider integrating AI chatbots as supplementary support tools...

### 5.2 Limitations

This study was conducted in a single institution with a relatively homogeneous sample...

## 6. Conclusions

This mixed-methods study demonstrates that AI-based chatbots can significantly enhance student engagement in online learning. Future research should examine long-term effects and explore ways to incorporate empathy into AI systems...

## References

Braun, V., & Clarke, V. (2006). Using thematic analysis in psychology. *Qualitative Research in Psychology*, 3(2), 77-101.

Creswell, J. W., & Plano Clark, V. L. (2018). *Designing and conducting mixed methods research* (3rd ed.). Sage Publications.

Fredricks, J. A., Blumenfeld, P. C., & Paris, A. H. (2004). School engagement: Potential of the concept, state of the evidence. *Review of Educational Research*, 74(1), 59-109.

Hwang, G. J., & Chang, C. Y. (2021). A review of opportunities and challenges of chatbots in education. *Interactive Learning Environments*, 1-14.

Kahu, E. R., Nelson, K. J., & Picton, C. (2017). Student engagement in the educational interface: Understanding the engagement of first-year students. *Higher Education Research & Development*, 36(2), 317-331.
""",
    # 可以添加更多模拟论文的 Markdown 内容
}


def generate_sample_data(project_root: Path, num_papers: int = 5):
    """生成模拟论文数据"""

    # 正确路径：项目根目录下的 .my-paper/journals/computers-and-education/
    journal_dir = project_root / '.my-paper' / 'journals' / 'computers-and-education'
    papers_dir = journal_dir / "papers"
    papers_dir.mkdir(parents=True, exist_ok=True)

    # 保存论文元数据（YAML）和全文（Markdown）
    for i, paper in enumerate(SAMPLE_PAPERS[:num_papers]):
        # 保存元数据
        meta_path = papers_dir / f"{paper['id']}.yaml"
        with open(meta_path, 'w', encoding='utf-8') as f:
            yaml.dump(paper, f, allow_unicode=True, sort_keys=False)
        print(f"✓ 已生成元数据: {meta_path}")

        # 保存全文（Markdown）
        if paper['id'] in SAMPLE_MARKDOWNS:
            md_path = papers_dir / f"{paper['id']}.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(SAMPLE_MARKDOWNS[paper['id']])
            print(f"✓ 已生成全文: {md_path}")

    # 更新期刊元数据
    meta_path = journal_dir / "metadata.yaml"
    if meta_path.exists():
        with open(meta_path, 'r', encoding='utf-8') as f:
            journal_meta = yaml.safe_load(f)

        journal_meta['journal']['stats']['paper_count'] = num_papers
        journal_meta['journal']['stats']['last_updated'] = datetime.now().strftime("%Y-%m-%d")

        with open(meta_path, 'w', encoding='utf-8') as f:
            yaml.dump(journal_meta, f, allow_unicode=True, sort_keys=False)
        print(f"\n✓ 已更新期刊元数据: {meta_path}")

    print(f"\n✅ 完成！共生成 {num_papers} 篇模拟论文")


if __name__ == '__main__':
    # 项目根目录（脚本位于 skills/omp:journal-crawl/scripts/，需要向上 4 级）
    project_root = Path(__file__).parent.parent.parent.parent
    print(f"项目根目录: {project_root}")
    generate_sample_data(project_root, num_papers=5)
