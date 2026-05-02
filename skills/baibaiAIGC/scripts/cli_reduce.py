#!/usr/bin/env python3
"""
OMP 降重 CLI - 完整两轮降重流水线
用法:
    python cli_reduce.py <输入文件> [--output <输出文件>] [--api-key <KEY>] [--model <模型>] [--base-url <URL>] [--no-round2]

示例:
    python cli_reduce.py论文.docx
    python cli_reduce.py 论文.docx --output 降重后.docx
    python cli_reduce.py 论文.docx --no-round2        # 只跑第1轮
    python cli_reduce.py 论文.txt --api-key sk-xxx   # 指定API Key
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib import request as urllib_request

# 将 skills/baibaiAIGC/scripts 加入路径
SKILL_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from aigc_round_service import (
    build_manifest,
    build_prompt_input,
    load_prompt,
    restore_text_from_chunks,
    validate_and_clean_chunk_output,
    MAX_ROUNDS,
)
from llm_client import llm_completion, normalize_api_type, build_endpoint, build_payload, build_headers, extract_response_text
from aigc_records import update_round
from docx_pipeline import read_docx_text, write_docx_text


DEFAULT_CHUNK_LIMIT = 850  # 字


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OMP 降重 CLI - 两轮降重流水线")
    parser.add_argument("input", type=Path, help="输入文件 (.docx 或 .txt)")
    parser.add_argument("--output", "-o", type=Path, default=None, help="输出文件路径 (.docx)，默认同输入文件名加 _降重 后缀")
    parser.add_argument("--doc-id", type=str, default=None, help="文档标识ID，默认使用输入文件名")
    parser.add_argument("--api-key", type=str, default=None, help="LLM API Key，默认读取环境变量 BAIBAIAIGC_API_KEY 或 OPENAI_API_KEY")
    parser.add_argument("--base-url", type=str, default=None, help="API Base URL，默认读取环境变量 BAIBAIAIGC_BASE_URL")
    parser.add_argument("--model", type=str, default=None, help="模型名称，默认读取环境变量 BAIBAIAIGC_MODEL")
    parser.add_argument("--temperature", type=float, default=0.7, help="采样温度，默认 0.7")
    parser.add_argument("--chunk-limit", type=int, default=DEFAULT_CHUNK_LIMIT, help=f"分段字数上限，默认 {DEFAULT_CHUNK_LIMIT}")
    parser.add_argument("--no-round2", action="store_true", help="跳过第2轮，只跑第1轮")
    parser.add_argument("--dry-run", action="store_true", help="只跑分段，不调用模型")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    return parser.parse_args()


def resolve_env(key: str | None, env_var: str, default: str) -> str:
    """优先用传入参数，否则读环境变量，否则用默认值"""
    if key:
        return key
    return os.environ.get(env_var) or os.environ.get(env_var.split("_", 1)[-1], default)


def load_input_text(input_path: Path) -> str:
    """读取输入文件，自动识别格式"""
    suffix = input_path.suffix.lower()
    if suffix == ".docx":
        return read_docx_text(input_path)
    elif suffix == ".txt":
        return input_path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"不支持的文件格式: {suffix}，仅支持 .docx 和 .txt")


def save_output_text(text: str, output_path: Path):
    """保存输出文件，自动识别格式"""
    suffix = output_path.suffix.lower()
    if suffix == ".docx":
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        write_docx_text(paragraphs, output_path)
    elif suffix == ".txt":
        output_path.write_text(text, encoding="utf-8")
    else:
        # 默认保存为 txt
        output_path.write_text(text, encoding="utf-8")


def run_single_round(
    input_text: str,
    round_num: int,
    doc_id: str,
    api_key: str,
    base_url: str,
    model: str,
    temperature: float,
    chunk_limit: int,
    dry_run: bool,
    verbose: bool,
) -> str:
    """运行单轮降重，返回输出文本"""

    if round_num < 1 or round_num > MAX_ROUNDS:
        raise ValueError(f"轮次必须是 1-{MAX_ROUNDS}")

    prompt_text = load_prompt("cn", round_num)

    # 构建 manifest
    manifest = build_manifest(input_text, chunk_limit=chunk_limit, chunk_metric="char")
    if verbose:
        print(f"  第{round_num}轮: 分段 {manifest.chunk_count} 块，段落 {manifest.paragraph_count} 个")

    if dry_run:
        return input_text

    # API 配置
    api_type = normalize_api_type(None, base_url)
    endpoint = build_endpoint(base_url, api_type)
    headers = build_headers(api_key)

    chunks_done = {}
    start_time = time.time()

    for idx, chunk in enumerate(manifest.chunks):
        chunk_id = chunk.chunk_id
        elapsed = time.time() - start_time

        prompt_input = build_prompt_input(prompt_text, chunk.text, round_num, chunk_id)

        if verbose:
            print(f"  [{elapsed:.0f}s] 第{round_num}轮 块 {idx+1}/{manifest.chunk_count} ({chunk_id})...", end="", flush=True)

        # 调用 LLM
        payload = build_payload(prompt_input, model=model, temperature=temperature, api_type=api_type)

        try:
            req = urllib_request.Request(
                endpoint,
                data=json.dumps(payload).encode(),
                headers=headers,
                method="POST",
            )
            with urllib_request.urlopen(req, timeout=90) as resp:
                raw = resp.read().decode()
                data = json.loads(raw)
                output_text = extract_response_text(data, raw, api_type)
                output_text = validate_and_clean_chunk_output(chunk.text, output_text, chunk_id)
        except Exception as e:
            if verbose:
                print(f"  ❌ 错误: {e}")
            raise

        chunks_done[chunk_id] = output_text
        if verbose:
            print(f"  ✓ ({len(output_text)}字)")

    # 重建完整文本
    output_text = restore_text_from_chunks(manifest, chunks_done)

    # 更新记录
    prompt_file = f"prompts/baibaiAIGC{round_num}.md"
    input_path_str = str(SKILL_ROOT / "origin" / f"{doc_id}.txt")
    output_path_str = str(intermediate_dir / f"{doc_id}_round{round_num}.txt")
    update_round(
        doc_id=doc_id,
        round_number=round_num,
        prompt=prompt_file,
        prompt_profile="cn",
        input_path=input_path_str,
        output_path=output_path_str,
        chunk_limit=chunk_limit,
        input_segment_count=manifest.chunk_count,
        output_segment_count=manifest.chunk_count,
    )

    return output_text


def main():
    args = parse_args()

    # 解析 API 配置
    api_key = resolve_env(args.api_key, "BAIBAIAIGC_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
    base_url = resolve_env(args.base_url, "BAIBAIAIGC_BASE_URL", "https://api.minimaxi.com/v1")
    model = resolve_env(args.model, "BAIBAIAIGC_MODEL", "MiniMax-Text-01")
    doc_id = args.doc_id or args.input.stem

    # 输出路径
    if args.output is None:
        output_path = args.input.parent / f"{args.input.stem}_降重{args.input.suffix}"
    else:
        output_path = args.output

    print("=" * 60)
    print("OMP 降重 CLI")
    print("=" * 60)
    print(f"  输入:   {args.input}")
    print(f"  输出:   {output_path}")
    print(f"  文档ID: {doc_id}")
    print(f"  模型:   {model}")
    print(f"  API:    {base_url}")
    print(f"  第1轮:  {'✓' if True else '✗'} (chunk_limit={args.chunk_limit})")
    print(f"  第2轮:  {'✗ 跳过' if args.no_round2 else '✓'}")
    print("=" * 60)

    # 读取输入
    print(f"\n📖 读取文件: {args.input}")
    input_text = load_input_text(args.input)
    print(f"  完成: {len(input_text)} 字")

    # 第1轮
    print(f"\n🔄 第1轮降重...")
    round1_text = run_single_round(
        input_text=input_text,
        round_num=1,
        doc_id=doc_id,
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=args.temperature,
        chunk_limit=args.chunk_limit,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )
    print(f"  第1轮完成: {len(round1_text)} 字 → 写入 {SKILL_ROOT / 'finish' / 'intermediate' / f'{doc_id}_round1.txt'}")

    intermediate_dir = SKILL_ROOT / "finish" / "intermediate"
    intermediate_dir.mkdir(parents=True, exist_ok=True)
    (intermediate_dir / f"{doc_id}_round1.txt").write_text(round1_text, encoding="utf-8")

    if args.no_round2:
        final_text = round1_text
    else:
        # 第2轮
        print(f"\n🔄 第2轮降重...")
        round2_text = run_single_round(
            input_text=round1_text,
            round_num=2,
            doc_id=doc_id,
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=args.temperature,
            chunk_limit=args.chunk_limit,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
        (intermediate_dir / f"{doc_id}_round2.txt").write_text(round2_text, encoding="utf-8")
        final_text = round2_text
        print(f"  第2轮完成: {len(round2_text)} 字 → 写入 {intermediate_dir / f'{doc_id}_round2.txt'}")

    # 保存最终结果
    print(f"\n💾 保存结果: {output_path}")
    save_output_text(final_text, output_path)
    print(f"  完成: {len(final_text)} 字")

    print("\n" + "=" * 60)
    print("✅ 降重完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
