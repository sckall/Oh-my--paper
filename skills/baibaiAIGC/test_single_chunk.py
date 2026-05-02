#!/usr/bin/env python3
import sys
sys.path.insert(0, 'scripts')

from llm_client import llm_completion
from aigc_round_service import load_prompt, build_prompt_input, validate_and_clean_chunk_output

# Test with first chunk
chunk_text = "遗传系谱图分析作为高中生物学人类遗传病这一单元的核心内容，涉及基因型推导和遗传方式判断。"

prompt_text = load_prompt('cn', 2)
prompt_input = build_prompt_input(prompt_text, chunk_text, 2, 'p0_c0')

print(f"Calling LLM with prompt length {len(prompt_input)}...", flush=True)

result = llm_completion(
    prompt=prompt_input,
    model='MiniMax-M2.7',
    api_key='sk-cp-ZGT39wY8qOBRA3tmUGED7QLiqP4VRMbyQ5QZFL1wTRowtgc2NbR-XKWRrMyWNh6UpdtS28NIyvtJNFnZncxU_AjO1Iv_VfDAess2cidp7jJ569tbQHsfnwE',
    base_url='https://api.minimaxi.com/v1',
    temperature=0.7,
    timeout=120
)

print(f"Result length: {len(result)}", flush=True)
clean = validate_and_clean_chunk_output(chunk_text, result, 'p0_c0')
print(f"Clean length: {len(clean)}", flush=True)
print(f"First 100 chars: {clean[:100]}", flush=True)
