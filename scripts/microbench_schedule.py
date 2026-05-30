#!/usr/bin/env python3
"""Microbenchmark: cache-primed Best-of-N scheduling for DeepSeek V4 Pro non-reasoning.

Tests three schedules on a single benchmark:
  A. sequential-3:     sample1 -> sample2 -> sample3
  B. one-prime-parallel-4:  sample1 -> parallel(sample2, sample3, sample4)
  C. two-prime-parallel-6:  sample1 -> sample2 -> parallel(sample3, sample4, sample5, sample6)

Reports cold-start wall-clock, cache-primed wall-clock, and token cache metrics.
"""

import os, sys, time, json, hashlib, threading, concurrent.futures
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "baselines"))

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=str(repo_root / ".env"))
except Exception:
    pass

from openai import OpenAI
import yaml
from batch_invariant_generation import (
    read_c_file_with_line_numbers,
    find_loop_invariant_insertion_points,
    create_messages,
)

# --- config ---
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
TEMPERATURE = 0.2
THREADS = 6  # max parallel

# --- pick one benchmark ---
BENCHMARK_FILE = str(repo_root / "Dataset/evaluation_deepseek_30/benchmark02_linear_1.c")

api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key:
    raise SystemExit("DEEPSEEK_API_KEY is not set")

client = OpenAI(api_key=api_key, base_url=BASE_URL)

# --- build stable prompt ---
with open(str(repo_root / "baselines/prompt.yaml")) as f:
    prompts = yaml.safe_load(f)

code = read_c_file_with_line_numbers(BENCHMARK_FILE)
messages = create_messages(code, prompts)
prompt_text = json.dumps(messages, sort_keys=True, ensure_ascii=False)
stable_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()[:16]


def call_api(sample_index: int) -> dict:
    """Single DeepSeek API call with non-reasoning mode."""
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        extra_body={"thinking": {"type": "disabled"}},
    )
    elapsed = time.perf_counter() - start

    msg = response.choices[0].message
    content = msg.content or ""
    reasoning = getattr(msg, "reasoning_content", None)

    usage = getattr(response, "usage", None)
    cache_hit = getattr(usage, "prompt_cache_hit_tokens", None) if usage else None
    cache_miss = getattr(usage, "prompt_cache_miss_tokens", None) if usage else None

    return {
        "sample_index": sample_index,
        "generation_time_sec": round(elapsed, 3),
        "content_len": len(content),
        "content_nonempty": bool(content),
        "has_reasoning": bool(reasoning),
        "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
        "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
        "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
        "prompt_cache_hit_tokens": cache_hit,
        "prompt_cache_miss_tokens": cache_miss,
        "stable_prefix_sha256": stable_hash,
        "invariant_preview": content[:80],
    }


def run_schedule(name: str, total_samples: int, prime_count: int, parallel_count: int) -> dict:
    """
    Run a schedule.
    - prime_count: sequential priming calls
    - parallel_count: concurrent calls after priming
    - total_samples = prime_count + parallel_count
    """
    print(f"\n=== Schedule {name}: {prime_count} prime + {parallel_count} parallel == {total_samples} total ===")

    results = {}
    results_lock = threading.Lock()
    wall_start = time.perf_counter()

    # Phase 1: sequential priming
    for i in range(prime_count):
        r = call_api(i)
        with results_lock:
            results[i] = r
        print(f"  prime [{i}]: gen={r['generation_time_sec']:.2f}s "
              f"cache_hit={r['prompt_cache_hit_tokens']} cache_miss={r['prompt_cache_miss_tokens']} "
              f"content_len={r['content_len']} tokens={r['completion_tokens']}")
        time.sleep(0.05)

    # Phase 2: parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(call_api, prime_count + j): prime_count + j
                   for j in range(parallel_count)}
        for future in concurrent.futures.as_completed(futures):
            r = future.result()
            idx = r["sample_index"]
            with results_lock:
                results[idx] = r
            print(f"  parallel [{idx}]: gen={r['generation_time_sec']:.2f}s "
                  f"cache_hit={r['prompt_cache_hit_tokens']} cache_miss={r['prompt_cache_miss_tokens']} "
                  f"content_len={r['content_len']} tokens={r['completion_tokens']}")

    wall_elapsed = time.perf_counter() - wall_start

    # compute metrics
    times = [results[i]["generation_time_sec"] for i in range(total_samples)]
    prime_times = times[:prime_count]
    parallel_times = times[prime_count:]

    T_gen_cold = sum(prime_times) + (max(parallel_times) if parallel_times else 0)
    T_gen_primed = max(parallel_times) if parallel_times else 0
    T_api_sum = sum(times)

    cache_hits = sum(results[i].get("prompt_cache_hit_tokens") or 0 for i in range(total_samples))
    cache_misses = sum(results[i].get("prompt_cache_miss_tokens") or 0 for i in range(total_samples))
    total_cache = cache_hits + cache_misses
    hit_rate = cache_hits / total_cache if total_cache > 0 else 0

    # sample3+ cache rate (only applicable for 2-prime schedules)
    s3_plus_hits = sum(results[i].get("prompt_cache_hit_tokens") or 0 for i in range(prime_count, total_samples))
    s3_plus_misses = sum(results[i].get("prompt_cache_miss_tokens") or 0 for i in range(prime_count, total_samples))
    s3_plus_total = s3_plus_hits + s3_plus_misses
    s3_plus_rate = s3_plus_hits / s3_plus_total if s3_plus_total > 0 else 0

    return {
        "schedule": name,
        "total_samples": total_samples,
        "prime_count": prime_count,
        "parallel_count": parallel_count,
        "wall_clock_sec": round(wall_elapsed, 3),
        "T_gen_cold": round(T_gen_cold, 3),
        "T_gen_primed": round(T_gen_primed, 3),
        "T_api_sum": round(T_api_sum, 3),
        "cache_hit_tokens_total": cache_hits,
        "cache_miss_tokens_total": cache_misses,
        "cache_hit_rate_total": round(hit_rate, 4),
        "cache_hit_rate_sample3_plus": round(s3_plus_rate, 4),
        "stable_prefix_sha256": stable_hash,
        "samples": [results[i] for i in range(total_samples)],
    }


# --- run all schedules ---

print(f"Benchmark: {Path(BENCHMARK_FILE).name}")
print(f"Model: {MODEL}")
print(f"Prompt chars: {len(prompt_text)}, sha256: {stable_hash}")
print(f"All calls use identical prompt (same messages object)")

all_results = {}

# A: sequential-3
all_results["A_seq3"] = run_schedule("A_seq3", total_samples=3, prime_count=3, parallel_count=0)

# B: one-prime-parallel-4
all_results["B_1p4"] = run_schedule("B_1p4", total_samples=4, prime_count=1, parallel_count=3)

# C: two-prime-parallel-6
all_results["C_2p6"] = run_schedule("C_2p6", total_samples=6, prime_count=2, parallel_count=4)

# --- report ---
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

for key, r in all_results.items():
    print(f"\n{key}: wall={r['wall_clock_sec']:.2f}s "
          f"cold={r['T_gen_cold']:.2f}s primed={r['T_gen_primed']:.2f}s "
          f"api_sum={r['T_api_sum']:.2f}s")
    print(f"  cache: hit_rate={r['cache_hit_rate_total']:.1%} "
          f"hit={r['cache_hit_tokens_total']} miss={r['cache_miss_tokens_total']} "
          f"s3+_hit_rate={r['cache_hit_rate_sample3_plus']:.1%}")

# --- save ---
out_path = repo_root / "notes" / "deepseek_cache_schedule_probe.json"
out_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
print(f"\nSaved to {out_path}")
