# DeepSeek Prompt Cache Awareness Notes

## 1. Where prompts are built

`create_messages()` in `baselines/batch_invariant_generation.py:1184`

The function builds a list of messages:
1. Optional few-shot examples (user/assistant pairs using the system prompt + sample program)
2. Final user message containing `system_prompt + "\n\n" + formatted_user_prompt`

## 2. Was original repo cache-aware?

No. The original repo made a single API call with `n=best_of_n`, which means all n completions come from the same API request. While DeepSeek's API will see identical prefix within a single request, the code had no instrumentation or structure to verify cache-friendliness across calls.

## 3. What was changed for cache-friendliness

- Added `hashlib` import for computing SHA-256 prefix hashes
- Added `logging` for cache instrumentation in `create_messages()`
- Added `[CachePrefix]` log entries showing `prefix_chars`, `suffix_chars`, `prefix_sha256`, `prompt_sha256`
- In `DeepSeekClient.generate_completion()`, added `[DeepSeekCache]` log entries for each completion call

## 4. Stable prefix definition

The stable prefix is:
- `json.dumps(messages[:-1], sort_keys=True, ensure_ascii=False)` — the few-shot examples as a deterministic serialized JSON string

The final user message (`messages[-1]`) is the suffix that varies per benchmark.

The system prompt and few-shot examples are byte-identical across all calls for the same `enable_cot` and `num_shots` settings.

## 5. Best-of-N cache strategy

The current architecture makes a single API call with `n=best_of_n`, sending one request with all messages. DeepSeek's API processes this internally and caches the shared prefix. No code changes needed for best_of_n cache reuse.

If in the future the code needs to make separate API calls for each sample (e.g., to include previous candidate feedback), the messages should be constructed as:
- `messages = stable_prefix_messages + [{"role": "user", "content": suffix}]` where `stable_prefix_messages` is byte-identical across calls.

## 6. Feedback loop cache strategy

Currently not implemented in the artifact (no verifier feedback to LLM). If added:
- Use append-only transcript style
- Previous rounds should remain byte-identical in the new prompt
- Append new sections at the end

## 7. Determinism requirements met

- No timestamps in prompts
- No random IDs
- No absolute temp paths in prompts
- `json.dumps(sort_keys=True)` for deterministic serialization
- Benchmark ordering is sorted (line 975)
- No logs in prompt content
- No API model responses from previous calls in the prompt
