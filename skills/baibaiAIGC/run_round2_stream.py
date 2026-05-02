#!/usr/bin/env python3
"""Streaming round2 runner - saves only completed paragraphs every 10 chunks."""
from __future__ import annotations
import sys, json, time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "scripts"))

from llm_client import llm_completion
from aigc_round_service import (
    build_manifest, restore_text_from_chunks, save_manifest,
    load_prompt, build_prompt_input, validate_and_clean_chunk_output,
)
from aigc_records import update_round

API_KEY = "sk-cp-ZGT39wY8qOBRA3tmUGED7QLiqP4VRMbyQ5QZFL1wTRowtgc2NbR-XKWRrMyWNh6UpdtS28NIyvtJNFnZncxU_AjO1Iv_VfDAess2cidp7jJ569tbQHsfnwE"
BASE_URL = "https://api.minimaxi.com/v1"
MODEL = "MiniMax-M2.7"
TIMEOUT = 90
MAX_RETRIES = 3

doc_id = "查重.txt"
input_path = ROOT / "origin" / "查重.txt"
output_path = ROOT / "finish" / "intermediate" / "查重_round2.txt"
manifest_path = ROOT / "finish" / "intermediate" / "查重_round2_manifest.json"

input_text = input_path.read_text(encoding="utf-8")
prompt_text = load_prompt("cn", 2)

manifest = build_manifest(input_text, chunk_limit=200, chunk_metric="char")
print(f"Total chunks: {manifest.chunk_count}, paragraphs: {manifest.paragraph_count}")

# Build set of chunk_ids that belong to each paragraph index
paragraph_chunk_ids = [set(p.chunk_ids) for p in manifest.paragraphs]
# Track which paragraph indices are complete
done_paragraph_indices = set()

chunks_done = {}
start = time.time()

for idx, chunk in enumerate(manifest.chunks):
    chunk_id = chunk.chunk_id
    elapsed = time.time() - start
    print(f"[{elapsed:.0f}s] Chunk {idx+1}/{manifest.chunk_count} ({chunk_id})...", end="", flush=True)
    
    prompt_input = build_prompt_input(prompt_text, chunk.text, 2, chunk_id)
    
    for attempt in range(MAX_RETRIES):
        try:
            result = llm_completion(
                prompt=prompt_input,
                model=MODEL,
                api_key=API_KEY,
                base_url=BASE_URL,
                temperature=0.7,
                timeout=TIMEOUT
            )
            clean = validate_and_clean_chunk_output(chunk.text, result, chunk_id)
            break
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f" retry{attempt+1}...", end="", flush=True)
                continue
            print(f" FALLBACK({e})", flush=True)
            clean = chunk.text  # fallback
    
    chunks_done[chunk_id] = clean
    print(f" ({len(clean)} chars)")
    
    # Check which paragraphs are now complete
    for pi, pcids in enumerate(paragraph_chunk_ids):
        if pi not in done_paragraph_indices and pcids.issubset(set(chunks_done.keys())):
            done_paragraph_indices.add(pi)
    
    # Save every 10 chunks - only completed paragraphs
    if (idx + 1) % 10 == 0:
        # Build partial result using only completed paragraphs
        completed_paras = []
        for pi in sorted(done_paragraph_indices):
            para = manifest.paragraphs[pi]
            parts = [chunks_done[cid].strip() for cid in para.chunk_ids if cid in chunks_done]
            completed_paras.append("".join(parts))
        partial = "\n\n".join(completed_paras)
        output_path.write_text(partial, encoding="utf-8")
        print(f"  >> Partial saved ({idx+1}/{manifest.chunk_count}, {len(done_paragraph_indices)}/{manifest.paragraph_count} paras done)")

# Final save - all paragraphs
final = restore_text_from_chunks(manifest, chunks_done)
output_path.write_text(final, encoding="utf-8")
save_manifest(manifest, manifest_path)

elapsed = time.time() - start
print(f"\nDone in {elapsed:.0f}s. Output: {len(final)} chars at {output_path}")
