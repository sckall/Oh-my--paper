#!/usr/bin/env python3
"""
元数据提取脚本 - 从 PDF 或 API 数据中提取论文元数据

依赖：
- pdfplumber: pip install pdfplumber
- PyMuPDF: pip install PyMuPDF
"""

import sys
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

# 尝试导入 PDF 解析库
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


def extract_from_pdf(pdf_path: Path) -> Dict:
    """
    从 PDF 文件中提取元数据

    Args:
        pdf_path: PDF 文件路径

    Returns:
        元数据字典
    """
    if not pdf_path.exists():
        print(f"错误: PDF 文件不存在 - {pdf_path}")
        return {}

    print(f"正在从 PDF 提取元数据: {pdf_path.name}")

    metadata = {
        'id': pdf_path.stem,
        'title': '',
        'authors': [],
        'year': None,
        'keywords': [],
        'abstract': '',
        'doi': '',
        'sections': []
    }

    # 优先使用 pdfplumber
    if HAS_PDFPLUMBER:
        return _extract_with_pdfplumber(pdf_path, metadata)
    elif HAS_PYMUPDF:
        return _extract_with_pymupdf(pdf_path, metadata)
    else:
        print("错误: 未安装 PDF 解析库")
        print("请安装: pip install pdfplumber 或 pip install PyMuPDF")
        return metadata


def _extract_with_pdfplumber(pdf_path: Path, metadata: Dict) -> Dict:
    """使用 pdfplumber 提取元数据"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # 提取第一页文本（通常包含标题、作者）
            first_page = pdf.pages[0]
            first_text = first_page.extract_text()

            if first_text:
                # 提取标题（简化版：第一行作为标题）
                lines = [line.strip() for line in first_text.split('\n') if line.strip()]
                if lines:
                    metadata['title'] = lines[0]

                # 提取作者（简化版：查找包含 @ 或 .edu 的行）
                for line in lines[:20]:  # 只检查前 20 行
                    if '@' in line or '.edu' in line:
                        # 简化版：整个行作为作者
                        metadata['authors'].append({
                            'name': line,
                            'affiliation': '',
                            'email': ''
                        })

            # 提取所有文本（用于后续分析）
            full_text = ''
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + '\n'

            # 提取摘要（简化版：查找 "Abstract" 或 "摘要" 关键词）
            abstract = _extract_abstract(full_text)
            if abstract:
                metadata['abstract'] = abstract

            # 提取年份（简化版：查找 4 位数字）
            year = _extract_year(full_text)
            if year:
                metadata['year'] = year

            # 提取 DOI（简化版：查找 "doi:" 或 "DOI:"）
            doi = _extract_doi(full_text)
            if doi:
                metadata['doi'] = doi

            print(f"✓ 元数据提取成功:")
            print(f"  标题: {metadata['title'][:50]}...")
            print(f"  作者数: {len(metadata['authors'])}")
            print(f"  年份: {metadata['year']}")
            print(f"  DOI: {metadata['doi']}")

        return metadata

    except Exception as e:
        print(f"错误: 使用 pdfplumber 提取失败 - {e}")
        return metadata


def _extract_with_pymupdf(pdf_path: Path, metadata: Dict) -> Dict:
    """使用 PyMuPDF 提取元数据"""
    try:
        doc = fitz.open(pdf_path)

        # 提取第一页文本
        first_page = doc[0]
        first_text = first_page.get_text()

        if first_text:
            lines = [line.strip() for line in first_text.split('\n') if line.strip()]
            if lines:
                metadata['title'] = lines[0]

        # 提取所有文本
        full_text = ''
        for page in doc:
            text = page.get_text()
            if text:
                full_text += text + '\n'

        doc.close()

        # 提取其他元数据
        abstract = _extract_abstract(full_text)
        if abstract:
            metadata['abstract'] = abstract

        year = _extract_year(full_text)
        if year:
            metadata['year'] = year

        doi = _extract_doi(full_text)
        if doi:
            metadata['doi'] = doi

        print(f"✓ 元数据提取成功:")
        print(f"  标题: {metadata['title'][:50]}...")
        print(f"  年份: {metadata['year']}")
        print(f"  DOI: {metadata['doi']}")

        return metadata

    except Exception as e:
        print(f"错误: 使用 PyMuPDF 提取失败 - {e}")
        return metadata


def _extract_abstract(text: str) -> Optional[str]:
    """提取摘要"""
    # 查找 "Abstract" 或 "摘要"
    patterns = [
        r'Abstract\s*(.*?)(?=\n\s*(Introduction|Keywords|1\.)|$)',
        r'摘要\s*(.*?)(?=\n\s*(引言|关键词|1\.)|$)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            abstract = match.group(1).strip()
            # 限制长度
            if len(abstract) > 2000:
                abstract = abstract[:2000] + '...'
            return abstract

    return None


def _extract_year(text: str) -> Optional[int]:
    """提取年份"""
    # 查找 4 位数字（1900-2099）
    pattern = r'\b(19\d{2}|20\d{2})\b'
    matches = re.findall(pattern, text)

    if matches:
        # 返回最大的年份（可能是最新版本）
        return max(int(year) for year in matches)

    return None


def _extract_doi(text: str) -> Optional[str]:
    """提取 DOI"""
    # 查找 DOI 模式
    patterns = [
        r'doi:\s*([0-9]+\.[0-9]+/[^\s]+)',
        r'DOI:\s*([0-9]+\.[0-9]+/[^\s]+)',
        r'https?://doi\.org/([0-9]+\.[0-9]+/[^\s]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def extract_from_api_data(api_data: Dict, journal_id: str) -> Dict:
    """
    从 API 数据中提取元数据

    Args:
        api_data: API 返回的字典
        journal_id: 期刊 ID

    Returns:
        元数据字典
    """
    metadata = {
        'id': f"{journal_id}-{api_data.get('id', 'unknown')}",
        'title': api_data.get('title', ''),
        'authors': [],
        'year': api_data.get('year'),
        'keywords': api_data.get('keywords', []),
        'abstract': api_data.get('abstract', ''),
        'doi': api_data.get('doi', ''),
        'citation_count': api_data.get('citationCount', 0),
        'url': api_data.get('url', ''),
        'sections': [],
        'empirical': None,  # 需要后续分析
        'innovation_score': None  # 需要后续分析
    }

    # 处理作者
    for author in api_data.get('authors', []):
        metadata['authors'].append({
            'name': author.get('name', ''),
            'affiliation': author.get('affiliation', ''),
            'email': ''
        })

    return metadata


def save_metadata(metadata: Dict, output_path: Path) -> None:
    """
    保存元数据到 YAML 文件

    Args:
        metadata: 元数据字典
        output_path: 输出文件路径
    """
    import yaml

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(metadata, f, allow_unicode=True, sort_keys=False)

    print(f"✓ 已保存元数据: {output_path}")


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python metadata.py <pdf_path> [output_path]")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    # 提取元数据
    metadata = extract_from_pdf(pdf_path)

    if metadata['title']:
        print(f"\n✓ 提取成功！")

        # 保存元数据
        if output_path:
            save_metadata(metadata, output_path)
    else:
        print("\n✗ 提取失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
