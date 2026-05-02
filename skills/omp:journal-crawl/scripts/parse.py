#!/usr/bin/env python3
"""
PDF 解析脚本 - 将 PDF 转换为 Markdown

依赖：
- pdfplumber (推荐): pip install pdfplumber
- PyMuPDF: pip install PyMuPDF
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict

# 尝试导入 pdfplumber
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

# 尝试导入 PyMuPDF
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


def parse_pdf(pdf_path: Path, output_path: Optional[Path] = None) -> Optional[str]:
    """
    解析 PDF 文件并转换为 Markdown

    Args:
        pdf_path: PDF 文件路径
        output_path: 输出 Markdown 文件路径（可选）

    Returns:
        解析后的 Markdown 文本，如果失败则返回 None
    """
    if not pdf_path.exists():
        print(f"错误: PDF 文件不存在 - {pdf_path}")
        return None

    print(f"正在解析 PDF: {pdf_path.name}")

    # 优先使用 pdfplumber
    if HAS_PDFPLUMBER:
        return _parse_with_pdfplumber(pdf_path, output_path)
    elif HAS_PYMUPDF:
        return _parse_with_pymupdf(pdf_path, output_path)
    else:
        print("错误: 未安装 PDF 解析库")
        print("请安装: pip install pdfplumber 或 pip install PyMuPDF")
        return None


def _parse_with_pdfplumber(pdf_path: Path, output_path: Optional[Path]) -> Optional[str]:
    """使用 pdfplumber 解析 PDF"""
    try:
        markdown_lines = []
        metadata = {}

        with pdfplumber.open(pdf_path) as pdf:
            # 提取第一页的文本（可能包含标题、作者）
            first_page = pdf.pages[0]
            first_text = first_page.extract_text()

            if first_text:
                # 尝试提取标题（简化版）
                lines = first_text.split('\n')
                if lines:
                    markdown_lines.append(f"# {lines[0].strip()}\n")

            # 遍历所有页面
            for page_num, page in enumerate(pdf.pages, start=1):
                print(f"  解析第 {page_num}/{len(pdf.pages)} 页...")

                # 提取文本
                text = page.extract_text()
                if text:
                    # 简化版：直接添加文本
                    # 实际应用需要识别章节结构、表格、图片等
                    markdown_lines.append(f"\n{text}\n")

                # 提取表格（可选）
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        markdown_lines.append("\n**表格**:\n")
                        # 简化版：不处理表格细节
                        markdown_lines.append("*（表格内容见原 PDF）*\n")

        # 合并为完整 Markdown
        markdown = '\n'.join(markdown_lines)

        # 保存文件
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            print(f"✓ 已保存 Markdown: {output_path}")

        return markdown

    except Exception as e:
        print(f"错误: 使用 pdfplumber 解析失败 - {e}")
        return None


def _parse_with_pymupdf(pdf_path: Path, output_path: Optional[Path]) -> Optional[str]:
    """使用 PyMuPDF 解析 PDF"""
    try:
        markdown_lines = []

        doc = fitz.open(pdf_path)

        for page_num, page in enumerate(doc, start=1):
            print(f"  解析第 {page_num}/{len(doc)} 页...")

            # 提取文本
            text = page.get_text()
            if text:
                markdown_lines.append(f"\n{text}\n")

        doc.close()

        # 合并为完整 Markdown
        markdown = '\n'.join(markdown_lines)

        # 保存文件
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            print(f"✓ 已保存 Markdown: {output_path}")

        return markdown

    except Exception as e:
        print(f"错误: 使用 PyMuPDF 解析失败 - {e}")
        return None


def extract_sections(markdown_text: str) -> List[Dict[str, str]]:
    """
    从 Markdown 文本中提取章节结构

    Args:
        markdown_text: Markdown 文本

    Returns:
        章节列表，每个章节包含 title 和 content
    """
    sections = []
    current_section = None

    for line in markdown_text.split('\n'):
        # 识别标题行（# 开头的行）
        if line.startswith('#'):
            # 保存上一个章节
            if current_section:
                sections.append(current_section)

            # 开始新章节
            current_section = {
                'title': line.strip('#').strip(),
                'content': ''
            }
        else:
            # 添加内容到当前章节
            if current_section:
                current_section['content'] += line + '\n'

    # 保存最后一个章节
    if current_section:
        sections.append(current_section)

    return sections


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python parse.py <pdf_path> [output_path]")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    markdown = parse_pdf(pdf_path, output_path)

    if markdown:
        print(f"\n✓ 解析成功！共 {len(markdown)} 字符")

        # 提取章节结构
        sections = extract_sections(markdown)
        if sections:
            print(f"✓ 识别到 {len(sections)} 个章节:")
            for i, section in enumerate(sections, 1):
                print(f"  {i}. {section['title']}")
    else:
        print("\n✗ 解析失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
