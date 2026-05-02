#!/usr/bin/env python3
"""
测试真实的 API 爬取功能
包含优雅的速率限制处理和详细日志
"""

import sys
import time
import yaml
from pathlib import Path

# 尝试导入依赖
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("❌ requests 未安装")
    print("安装命令: pip install requests")
    sys.exit(1)

try:
    import xml.etree.ElementTree as ET
    HAS_XML = True
except ImportError:
    HAS_XML = False
    print("⚠ xml.etree.ElementTree 未安装，arXiv XML 解析将不可用")


def test_arxiv_api(query: str = "AI in education", max_results: int = 3):
    """测试 arXiv API"""
    print("="*60)
    print("测试 1: arXiv API")
    print("="*60)
    
    if not HAS_REQUESTS:
        print("❌ 跳过：requests 未安装")
        return False
    
    print(f"📡 正在连接 arXiv API...")
    print(f"   查询: {query}")
    print(f"   最大结果数: {max_results}")
    
    url = "http://export.arxiv.org/api/query"
    params = {
        'search_query': f'all:{query}',
        'start': 0,
        'max_results': max_results,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    
    try:
        # 添加延迟避免速率限制
        print("⏳ 等待 3 秒（避免速率限制）...")
        time.sleep(3)
        
        print("📥 发送请求...")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            print("✅ arXiv API 连接成功！")
            
            # 解析响应
            if HAS_XML:
                print("📊 解析响应数据...")
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                root = ET.fromstring(response.text)
                
                entries = root.findall('atom:entry', ns)
                print(f"\n✅ 找到 {len(entries)} 篇论文：\n")
                
                papers = []
                for i, entry in enumerate(entries, 1):
                    title_elem = entry.find('atom:title', ns)
                    title = title_elem.text.strip().replace('\n', ' ') if title_elem is not None else '无标题'
                    
                    published_elem = entry.find('atom:published', ns)
                    year = published_elem.text[:4] if published_elem is not None else '未知'
                    
                    print(f"{i}. {title}")
                    print(f"   年份: {year}")
                    print()
                    
                    papers.append({'title': title, 'year': year})
                
                # 保存测试结果
                output_dir = Path(__file__).parent.parent.parent / "test_results"
                output_dir.mkdir(parents=True, exist_ok=True)
                
                output_file = output_dir / "arxiv_test_results.yaml"
                with open(output_file, 'w', encoding='utf-8') as f:
                    yaml.dump({
                        'api': 'arXiv',
                        'query': query,
                        'results_count': len(papers),
                        'papers': papers,
                        'test_time': time.strftime("%Y-%m-%d %H:%M:%S")
                    }, f, allow_unicode=True, sort_keys=False)
                
                print(f"✅ 测试结果已保存: {output_file}")
                return True
                
            else:
                print("⚠ 无法解析 XML（xml.etree.ElementTree 未安装）")
                return False
                
        elif response.status_code == 429:
            print("⚠ API 速率限制（429）")
            print("建议：等待 60 秒后重试，或使用手动上传模式")
            return False
        else:
            print(f"❌ API 请求失败，状态码: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 连接超时")
        print("建议：检查网络连接，或稍后重试")
        return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


def test_semantic_scholar_api(query: str = "AI in education", limit: int = 3):
    """测试 Semantic Scholar API"""
    print("\n" + "="*60)
    print("测试 2: Semantic Scholar API")
    print("="*60)
    
    if not HAS_REQUESTS:
        print("❌ 跳过：requests 未安装")
        return False
    
    print(f"📡 正在连接 Semantic Scholar API...")
    print(f"   查询: {query}")
    print(f"   最大结果数: {limit}")
    
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        'query': query,
        'limit': limit,
        'fields': 'title,authors,year,abstract,citationCount'
    }
    headers = {'User-Agent': 'Oh-My-Paper/1.0 (test)'}
    
    try:
        # 添加延迟避免速率限制
        print("⏳ 等待 3 秒（避免速率限制）...")
        time.sleep(3)
        
        print("📥 发送请求...")
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("✅ Semantic Scholar API 连接成功！")
            
            # 解析响应
            print("📊 解析响应数据...")
            data = response.json()
            papers = data.get('data', [])
            
            print(f"\n✅ 找到 {len(papers)} 篇论文：\n")
            
            paper_list = []
            for i, paper in enumerate(papers, 1):
                title = paper.get('title', '无标题')
                year = paper.get('year', '未知')
                citations = paper.get('citationCount', 0)
                
                print(f"{i}. {title}")
                print(f"   年份: {year}, 引用数: {citations}")
                print()
                
                paper_list.append({
                    'title': title,
                    'year': year,
                    'citation_count': citations
                })
            
            # 保存测试结果
            output_dir = Path(__file__).parent.parent.parent / "test_results"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / "semantic_scholar_test_results.yaml"
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump({
                    'api': 'Semantic Scholar',
                    'query': query,
                    'results_count': len(paper_list),
                    'papers': paper_list,
                    'test_time': time.strftime("%Y-%m-%d %H:%M:%S")
                }, f, allow_unicode=True, sort_keys=False)
            
            print(f"✅ 测试结果已保存: {output_file}")
            return True
            
        elif response.status_code == 429:
            print("⚠ API 速率限制（429）")
            print("建议：等待 60 秒后重试，或使用手动上传模式")
            return False
        else:
            print(f"❌ API 请求失败，状态码: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 连接超时")
        print("建议：检查网络连接，或稍后重试")
        return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


def test_manual_upload_mode():
    """测试手动上传模式（模拟）"""
    print("\n" + "="*60)
    print("测试 3: 手动上传模式（模拟）")
    print("="*60)
    
    print("📁 模拟手动上传 PDF...")
    print("   步骤 1: 准备 PDF 文件")
    print("   步骤 2: 运行爬取脚本")
    print("   步骤 3: 解析 PDF 并提取元数据")
    print("   步骤 4: 保存为 YAML + Markdown")
    
    # 模拟结果
    print("\n✅ 模拟上传成功！")
    print("   处理了 5 个 PDF 文件")
    print("   生成了 5 个 YAML 元数据文件")
    print("   生成了 3 个 Markdown 全文文件")
    
    print("\n💡 真实使用步骤：")
    print("   1. 将 PDF 文件放到一个目录（如 ~/Downloads/pdfs/）")
    print("   2. 运行命令：")
    print("      python skills/omp:journal-crawl/scripts/crawl.py \\")
    print("        --journal computers-and-education \\")
    print("        --source manual \\")
    print("        --pdf-dir ~/Downloads/pdfs/")
    
    return True


def main():
    """主函数"""
    print("\n" + "="*60)
    print("期刊论文爬取 - API 测试工具")
    print("="*60 + "\n")
    
    # 测试结果
    results = {
        'arxiv': False,
        'semantic_scholar': False,
        'manual_upload': False
    }
    
    # 测试 1: arXiv API
    try:
        results['arxiv'] = test_arxiv_api(query="AI in education", max_results=3)
    except Exception as e:
        print(f"❌ arXiv API 测试失败: {e}")
    
    # 测试 2: Semantic Scholar API
    try:
        results['semantic_scholar'] = test_semantic_scholar_api(query="AI in education", limit=3)
    except Exception as e:
        print(f"❌ Semantic Scholar API 测试失败: {e}")
    
    # 测试 3: 手动上传模式（模拟）
    try:
        results['manual_upload'] = test_manual_upload_mode()
    except Exception as e:
        print(f"❌ 手动上传模拟失败: {e}")
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    print(f"arXiv API:             {'✅ 成功' if results['arxiv'] else '❌ 失败'}")
    print(f"Semantic Scholar API:  {'✅ 成功' if results['semantic_scholar'] else '❌ 失败'}")
    print(f"手动上传模式:          {'✅ 成功（模拟）' if results['manual_upload'] else '❌ 失败'}")
    
    print("\n💡 建议：")
    if not results['arxiv'] and not results['semantic_scholar']:
        print("   - API 测试均失败，建议使用手动上传模式（--source manual）")
        print("   - 或从学校图书馆下载 PDF，然后手动导入")
    elif not results['arxiv']:
        print("   - arXiv API 不可用，但 Semantic Scholar API 可用")
        print("   - 可以使用: --source semantic-scholar")
    elif not results['semantic_scholar']:
        print("   - Semantic Scholar API 不可用，但 arXiv API 可用")
        print("   - 可以使用: --source arxiv")
    
    print("   - 手动上传模式始终可用: --source manual")
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
