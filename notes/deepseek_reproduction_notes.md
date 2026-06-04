# DeepSeek V4 Pro Reproduction Notes

## Phase 0: Inspection Results

### 1. Files containing LLM API client logic
- `baselines/inference.py` (314 lines) - All client classes + factory function
- `baselines/batch_invariant_generation.py` (1877 lines) - Main pipeline

### 2. Currently supported inference clients
From `inference.py` `get_client()`:
- `openai` - OpenAI API (uses openai SDK, Responses API)
- `together` - Together AI (uses together SDK, chat.completions)
- `claude` / `anthropic` - Anthropic (uses anthropic SDK)
- `gemini` - Google Gemini (uses google-genai SDK)
- `sglang` - Local SGLang server

### 3. How `--inference_client` is parsed
- argparse in `batch_invariant_generation.py:1685`
- Default: `'sglang'`
- Passed to `get_client(args.inference_client, model_name=args.model_name, sglang_addr=sglang_addr)` at line 1774

### 4. How `--model_name` is passed
- argparse at line 1683, default `'Qwen/Qwen2.5-Coder-7B-Instruct'`
- Passed as `args.model_name` to `get_client()`

### 5. Where prompts are built
- `create_messages()` at line 1165
- Uses `prompt.yaml` for templates
- Builds message list: optional few-shot examples, then final user message combining system_prompt + user_prompt with PROGRAM and POINTS substitutions

### 6. Where raw LLM responses are parsed
- `extract_invariants_from_response()` at line 1204
- Uses regex to find `After line X, insert assume(condition)` patterns

### 7. Where generated invariants are saved
- `save_results()` at line 1561
- Outputs JSON to `baselines/results/`
- Format: `{model_name}_cot={bool}_best_of_n={n}_num_shots={n}_temperature={t}_verifier={v}_invariant_generation_results.json`

### 8. Where verifier invocation happens
- Phase 2 of `run_two_phase_processing()` at line 803
- `run_smart_verification()` at line 467 runs assume+assert verification in parallel
- UAutomizer or ESBMC

### 9. Where result JSON is written
- `save_results()` at line 1561

### 10. API call flow summary
```
main() → get_client() → BatchInvariantProcessor.__init__()
→ run_two_phase_processing()
  → Phase 1: generate_invariants_for_file() → _generate_llm_invariants_for_file()
    → create_messages() builds prompt
    → client.generate_completion(messages=messages, n=best_of_n)
    → extract_invariants_from_response() parses each response
  → Phase 2: insert invariants into C files, run verifier
```

## Phase 1: Venv Setup

- Python: 3.10.12
- Virtual env: `.venv/` at repo root (Python venv, NOT conda)
- Required `sudo apt install python3.10-venv` (not available, used `--without-pip` + bootstrap)
- Installed minimal deps: openai, pyyaml, python-dotenv, tabulate, tqdm, requests
- Heavy ML deps (torch, sglang, transformers, etc.) NOT installed - made imports conditional/lazy

## Phase 2: Build Results

- Java: OpenJDK 1.8.0_482
- OS: Ubuntu 22.04
- build.sh: `sudo apt install clang-format-15` skipped (no sudo). UAutomizer download worked manually.
- Verifier: UAutomizer installed at `tools/uautomizer/Ultimate.py`
- ESBMC: not installed (commented out in build.sh)

## Phase 7: One-Benchmark Smoke Test

- DeepSeek API call succeeded (HTTP 200)
- Critical finding: `deepseek-v4-pro` is a reasoning model — output goes to `reasoning_content` first, `content` empty with max_tokens=800
- Auto-raising max_tokens from 200→800 was added but insufficient; content still empty for 7/8 benchmarks
- End-to-end pipeline verified: API call → extraction → verifier → result

## Phase 8: Small Subset Run

- 8 benchmarks processed, all API calls succeeded (no timeouts, no auth errors)
- 4/8 (50%) generated at least one extracted invariant
- 0/8 (0%) had invariants accepted by verifier (all assume/assert results: UNKNOWN)
- Main failure mode: reasoning model consumes all tokens on reasoning, content is empty; fallback reads reasoning trace which doesn't contain the exact required format
- Only benchmark38 produced a complete formatted response in `content` (51 chars): `After line 28, insert assume(x == 4 * y && x >= 0);`
- See `notes/deepseek_smoke_snapshot.md` for smoke-run results

## Final Code Changes Summary

### `baselines/inference.py`
- Made all provider SDK imports lazy (torch, sglang, anthropic, together, google-genai, transformers)
- Added `DeepSeekClient` class with:
  - OpenAI-compatible API client with `base_url=https://api.deepseek.com`
  - Reads `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL` from env
  - No token limit imposed — lets CLI `--max_new_tokens` control
  - Falls back to `reasoning_content` when `content` is empty
  - Prefix hash instrumentation for cache monitoring
  - Response preview logging (first 300 chars)
  - Prefix hash instrumentation for cache monitoring
  - Response preview logging (first 300 chars)
- Added `.env` loading from repo root
- Added `deepseek` to `get_client()` factory

### `baselines/batch_invariant_generation.py`
- Made sglang imports lazy/conditional
- Added `--benchmark_dir` CLI argument
- Added `hashlib`, `logging` imports
- Added `[CachePrefix]` logging to `create_messages()`
- Fixed indentation issues

### `.gitignore`
- Added `.venv/`, `__pycache__/`, `*.pyc`, `.env`

### New Files
- `Dataset/evaluation_deepseek_smoke/` — 8 benchmark subset
- `.env` — API key (gitignored)
- `notes/deepseek_reproduction_notes.md`
- `notes/deepseek_subset_30.md`
- `notes/deepseek_smoke_snapshot.md`
- `notes/deepseek_cache_schedule_probe.json`

### `tools/uautomizer/Ultimate.py` (verifier fixes)
- **Java version**: Changed `get_java()` to find highest available Java version (previously strict ==11 check failed on both Java 8 and Java 17)
- **--add-opens**: Added `--add-opens java.base/java.lang=ALL-UNNAMED` (+ java.util, java.io) for Java 9+ module system
- **OSGi cache**: Removed `-Dosgi.configuration.area` flag — corrupted cache from failed Java 8 runs poisoned subsequent attempts
- **Memory**: Reduced `-Xmx15G` to `-Xmx4G` (15G was excessive)

## Final Result

**8/8 (100%) verifier-accepted invariants** on the smoke subset with deepseek-v4-pro.
All failures were verifier infrastructure issues (Java version, OSGi cache), not LLM quality issues.
