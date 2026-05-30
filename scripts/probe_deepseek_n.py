#!/usr/bin/env python3
"""Probe whether DeepSeek V4 Pro supports OpenAI-style n=3 in one request."""
import os, time, json, hashlib
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=str(Path(__file__).resolve().parent.parent / ".env"))
except Exception:
    pass

from openai import OpenAI

api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key:
    raise SystemExit("DEEPSEEK_API_KEY is not set")

model = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

client = OpenAI(api_key=api_key, base_url=base_url)

messages = [
    {"role": "system", "content": "You are a precise invariant generator. Output only the requested final line."},
    {"role": "user", "content": "Return exactly one line in the format:\nINVARIANT: assume(x >= 0);"},
]

prompt_text = json.dumps(messages, sort_keys=True, ensure_ascii=False)
prompt_sha256 = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()

start = time.perf_counter()
try:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        n=3,
        extra_body={"thinking": {"type": "disabled"}},
    )
    elapsed = time.perf_counter() - start

    choices = response.choices or []
    rows = []
    for i, ch in enumerate(choices):
        msg = ch.message
        content = getattr(msg, "content", None)
        reasoning = getattr(msg, "reasoning_content", None)
        rows.append({
            "index": i,
            "finish_reason": getattr(ch, "finish_reason", None),
            "content": content,
            "reasoning_content_present": bool(reasoning),
        })

    usage = getattr(response, "usage", None)
    usage_dict = {}
    if usage is not None:
        for name in ["prompt_tokens", "completion_tokens", "total_tokens",
                      "prompt_cache_hit_tokens", "prompt_cache_miss_tokens"]:
            usage_dict[name] = getattr(usage, name, None)

    result = {
        "success": True,
        "model": model,
        "n_requested": 3,
        "choices_len": len(choices),
        "contents_distinct": len(set((r["content"] or "") for r in rows)) == max(len(rows), 1),
        "generation_time_sec": round(elapsed, 3),
        "prompt_sha256": prompt_sha256,
        "choices": rows,
        "usage": usage_dict,
    }

except Exception as e:
    elapsed = time.perf_counter() - start
    result = {
        "success": False,
        "model": model,
        "n_requested": 3,
        "generation_time_sec": round(elapsed, 3),
        "error_type": type(e).__name__,
        "error_message": str(e),
    }

Path("notes").mkdir(exist_ok=True)
out = Path("notes/deepseek_n3_probe_result.json")
out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
print(json.dumps(result, indent=2, ensure_ascii=False))
print(f"Saved to {out}")
