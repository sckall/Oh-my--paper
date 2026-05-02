#!/usr/bin/env python3
"""
omp:journal-crawl - 期刊论文爬取脚本

支持数据源：
- arXiv API (arxiv)
- Semantic Scholar API (semantic-scholar)
- PubMed API (pubmed)
- 手动上传 PDF (manual)
"""

import argparse
import json
import os
import sys
import time
import yaml
from pathlib import Path
from typing import List, Dict, Optional

# 尝试导入可选依赖
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("警告: requests 未安装，API 爬取功能将不可用")
    print("安装命令: pip install requests")

try:
    import xml.etree.ElementTree as ET
    HAS_XML = True
except ImportError:
    HAS_XML = False


class JournalCrawler:
    """期刊论文爬取器基类"""

    def __init__(self, journal_id: str, output_dir: Path):
        self.journal_id = journal_id
        self.output_dir = output_dir
        self.papers_dir = output_dir / "papers"
        self.papers_dir.mkdir(parents=True, exist_ok=True)

        # 加载期刊元数据
        self.journal_meta = self._load_journal_metadata()

    def _load_journal_metadata(self) -> Dict:
        """加载期刊元数据"""
        meta_path = self.output_dir.parent / self.journal_id / "metadata.yaml"
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def crawl(self, query: str, max_results: int = 20,
              year_from: Optional[int] = None, year_to: Optional[int] = None) -> List[Dict]:
        """爬取论文（由子类实现）"""
        raise NotImplementedError

    def save_paper(self, paper_data: Dict) -> None:
        """保存论文数据和元数据"""
        paper_id = paper_data['id']

        # 保存元数据
        meta_path = self.papers_dir / f"{paper_id}.yaml"
        with open(meta_path, 'w', encoding='utf-8') as f:
            yaml.dump(paper_data, f, allow_unicode=True, sort_keys=False)

        print(f"✓ 已保存元数据: {meta_path}")

    def update_journal_metadata(self, new_count: int) -> None:
        """更新期刊元数据中的论文数量"""
        meta_path = self.output_dir.parent / self.journal_id / "metadata.yaml"
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = yaml.safe_load(f)

            meta['journal']['paper_count'] = meta['journal'].get('paper_count', 0) + new_count
            meta['journal']['last_updated'] = time.strftime("%Y-%m-%d")

            with open(meta_path, 'w', encoding='utf-8') as f:
                yaml.dump(meta, f, allow_unicode=True, sort_keys=False)

            print(f"✓ 已更新期刊元数据: {meta_path}")


class arXivCrawler(JournalCrawler):
    """arXiv API 爬取器"""

    BASE_URL = "http://export.arxiv.org/api/query"

    def crawl(self, query: str, max_results: int = 20,
              year_from: Optional[int] = None, year_to: Optional[int] = None) -> List[Dict]:
        """从 arXiv API 爬取论文"""
        if not HAS_REQUESTS:
            print("错误: requests 未安装，无法使用 arXiv API")
            return []

        print(f"正在从 arXiv 搜索: {query}")

        # 构建查询参数
        params = {
            'search_query': f'all:{query}',
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }

        try:
            # 添加延迟避免速率限制
            time.sleep(3)

            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()

            # 解析 XML 响应
            papers = self._parse_arxiv_xml(response.text, year_from, year_to)

            print(f"✓ 从 arXiv 获取到 {len(papers)} 篇论文")
            return papers

        except requests.exceptions.RequestException as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                print("⚠ API 速率限制，等待 60 秒后重试...")
                time.sleep(60)
                return self.crawl(query, max_results, year_from, year_to)
            else:
                print(f"错误: 从 arXiv 爬取失败 - {e}")
                return []

    def _parse_arxiv_xml(self, xml_text: str, year_from: Optional[int], year_to: Optional[int]) -> List[Dict]:
        """解析 arXiv API 的 XML 响应"""
        if not HAS_XML:
            print("错误: xml.etree.ElementTree 未安装")
            return []

        papers = []
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        try:
            root = ET.fromstring(xml_text)

            for entry in root.findall('atom:entry', ns):
                # 提取标题
                title_elem = entry.find('atom:title', ns)
                title = title_elem.text.strip().replace('\n', ' ') if title_elem is not None else ''

                # 提取年份
                published_elem = entry.find('atom:published', ns)
                year = int(published_elem.text[:4]) if published_elem is not None else None

                # 年份过滤
                if year_from and year and year < year_from:
                    continue
                if year_to and year and year > year_to:
                    continue

                # 提取作者
                authors = []
                for author in entry.findall('atom:author', ns):
                    name_elem = author.find('atom:name', ns)
                    if name_elem is not None:
                        authors.append({
                            'name': name_elem.text,
                            'affiliation': '',
                            'email': ''
                        })

                # 提取摘要
                summary_elem = entry.find('atom:summary', ns)
                abstract = summary_elem.text.strip() if summary_elem is not None else ''

                # 提取 ID
                id_elem = entry.find('atom:id', ns)
                paper_id = id_elem.text.split('/')[-1] if id_elem is not None else ''

                paper = {
                    'id': f"{self.journal_id}-{year}-{paper_id}",
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'abstract': abstract,
                    'doi': '',
                    'keywords': [],
                    'citation_count': 0,
                    'url': id_elem.text if id_elem is not None else '',
                    'pdf_path': None,
                    'markdown_path': None,
                    'empirical': None,
                    'innovation_score': None,
                    'created_at': time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
                }

                papers.append(paper)

        except Exception as e:
            print(f"错误: 解析 arXiv XML 失败 - {e}")

        return papers


class SemanticScholarCrawler(JournalCrawler):
    """Semantic Scholar API 爬取器"""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def crawl(self, query: str, max_results: int = 20,
              year_from: Optional[int] = None, year_to: Optional[int] = None) -> List[Dict]:
        """从 Semantic Scholar API 爬取论文"""
        if not HAS_REQUESTS:
            print("错误: requests 未安装，无法使用 Semantic Scholar API")
            return []

        print(f"正在从 Semantic Scholar 搜索: {query}")

        # 构建查询参数
        params = {
            'query': query,
            'limit': min(max_results, 100),  # API 限制每次最多 100 条
            'fields': 'title,authors,year,abstract,doi,url,citationCount,keywords,venue'
        }

        try:
            # 添加延迟避免速率限制
            time.sleep(3)

            url = f"{self.BASE_URL}/paper/search"
            headers = {'User-Agent': 'Oh-My-Paper/1.0 (mailto:your-email@example.com)'}

            response = requests.get(url, params=params, headers=headers, timeout=30)

            # 处理速率限制
            if response.status_code == 429:
                print("⚠ API 速率限制，等待 60 秒后重试...")
                time.sleep(60)
                return self.crawl(query, max_results, year_from, year_to)

            response.raise_for_status()

            data = response.json()
            papers = self._parse_s2_response(data, year_from, year_to)

            print(f"✓ 从 Semantic Scholar 获取到 {len(papers)} 篇论文")
            return papers

        except requests.exceptions.RequestException as e:
            print(f"错误: 从 Semantic Scholar 爬取失败 - {e}")
            return []

    def _parse_s2_response(self, data: Dict, year_from: Optional[int], year_to: Optional[int]) -> List[Dict]:
        """解析 Semantic Scholar API 响应"""
        papers = []

        for paper_data in data.get('data', []):
            # 年份过滤
            year = paper_data.get('year')
            if year_from and year and year < year_from:
                continue
            if year_to and year and year > year_to:
                continue

            # 构建论文元数据
            paper = {
                'id': f"{self.journal_id}-{year}-{paper_data.get('paperId', 'unknown')}",
                'title': paper_data.get('title', ''),
                'authors': [{'name': author.get('name', ''), 'affiliation': '', 'email': ''}
                            for author in paper_data.get('authors', [])],
                'year': year,
                'doi': paper_data.get('doi', ''),
                'keywords': paper_data.get('keywords', []),
                'citation_count': paper_data.get('citationCount', 0),
                'url': paper_data.get('url', ''),
                'abstract': paper_data.get('abstract', ''),
                'venue': paper_data.get('venue', ''),
                'pdf_path': None,
                'markdown_path': None,
                'empirical': None,
                'innovation_score': None,
                'created_at': time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
            }

            papers.append(paper)

        return papers


class ManualCrawler(JournalCrawler):
    """手动上传 PDF 爬取器"""

    def crawl(self, pdf_dir: str, max_results: int = 20,
              year_from: Optional[int] = None, year_to: Optional[int] = None) -> List[Dict]:
        """从本地目录处理 PDF 文件"""
        pdf_path = Path(pdf_dir)
        if not pdf_path.exists():
            print(f"错误: PDF 目录不存在 - {pdf_dir}")
            return []

        print(f"正在从本地目录处理 PDF: {pdf_dir}")

        pdf_files = list(pdf_path.glob("*.pdf"))[:max_results]
        papers = []

        for pdf_file in pdf_files:
            print(f"处理: {pdf_file.name}")

            # 基本元数据（实际使用时应该调用 parse.py 和 metadata.py）
            paper = {
                'id': f"{self.journal_id}-manual-{pdf_file.stem}",
                'title': pdf_file.stem,  # 默认使用文件名
                'authors': [],
                'year': None,
                'doi': '',
                'keywords': [],
                'pdf_path': str(pdf_file),
                'markdown_path': None,
                'empirical': None,
                'citation_count': 0,
                'url': '',
                'abstract': '',
                'created_at': time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
            }

            papers.append(paper)

        print(f"✓ 从本地目录处理了 {len(papers)} 个 PDF 文件")
        return papers


def main():
    parser = argparse.ArgumentParser(description='omp:journal-crawl - 期刊论文爬取工具')
    parser.add_argument('--journal', required=True, help='期刊 ID')
    parser.add_argument('--source', required=True,
                        choices=['arxiv', 'semantic-scholar', 'pubmed', 'manual'],
                        help='数据源')
    parser.add_argument('--query', help='搜索查询（用于 API 搜索）')
    parser.add_argument('--max', type=int, default=20, help='最大爬取数量')
    parser.add_argument('--year-from', type=int, help='起始年份')
    parser.add_argument('--year-to', type=int, help='结束年份')
    parser.add_argument('--pdf-dir', help='手动上传 PDF 的目录路径')

    args = parser.parse_args()

    # 确定输出目录
    script_dir = Path(__file__).parent.parent.parent
    output_dir = script_dir / '.my-paper' / 'journals' / args.journal

    if not output_dir.exists():
        print(f"错误: 期刊目录不存在 - {output_dir}")
        print(f"请先创建期刊元数据: {output_dir / 'metadata.yaml'}")
        sys.exit(1)

    # 根据数据源选择爬取器
    if args.source == 'arxiv':
        crawler = arXivCrawler(args.journal, output_dir)
        papers = crawler.crawl(args.query or '', args.max, args.year_from, args.year_to)
    elif args.source == 'semantic-scholar':
        crawler = SemanticScholarCrawler(args.journal, output_dir)
        papers = crawler.crawl(args.query or '', args.max, args.year_from, args.year_to)
    elif args.source == 'manual':
        if not args.pdf_dir:
            print("错误: 手动上传模式需要 --pdf-dir 参数")
            sys.exit(1)
        crawler = ManualCrawler(args.journal, output_dir)
        papers = crawler.crawl(args.pdf_dir, args.max, args.year_from, args.year_to)
    else:
        print(f"错误: 暂不支持数据源 - {args.source}")
        sys.exit(1)

    # 保存论文数据
    for paper in papers:
        crawler.save_paper(paper)

    # 更新期刊元数据
    if papers:
        crawler.update_journal_metadata(len(papers))

    print(f"\n✓ 完成！共处理 {len(papers)} 篇论文")


if __name__ == '__main__':
    main()
