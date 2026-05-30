# DeepSeek N=3 API Probe Result

## Result: UNSUPPORTED

DeepSeek V4 Pro rejects `n=3` in a single `/chat/completions` request.

```
Error code: 400
Invalid n value (currently only n = 1 is supported)
```

## Probe Method
- Model: `deepseek-v4-pro`
- Non-reasoning mode: `extra_body={"thinking": {"type": "disabled"}}`
- `n=3` parameter sent
- No `max_tokens`
- `temperature=0.2`
- Small deterministic prompt

## Response
- HTTP 400
- `BadRequestError`
- Response time: 0.457s (instant rejection, no processing)

## Conclusion
DeepSeek does not support OpenAI-style multiple completions (`n > 1`) in a single request.

## Recommended Fallback: Separate Calls with Cache-Aware Prefix

Since a single request `n=3` is impossible, use 3 separate API calls.

### Implementation

```python
for sample_idx in range(best_of_n):
    suffix = f"\n[sample {sample_idx+1}/{best_of_n}]\n"
    messages = base_messages + [{"role": "user", "content": suffix}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        extra_body={"thinking": {"type": "disabled"}},
    )
```

### Cache Strategy
- **base_messages** (system prompt + program + insertion points) remains byte-identical across all 3 calls
- Only append a small distinguishing suffix
- DeepSeek prompt cache (automatic, best-effort) should hit for the stable prefix
- Log `prompt_cache_hit_tokens` and `prompt_cache_miss_tokens` for each call

### Expected Cost
- First call: full prompt tokens charged
- Calls 2-3: mostly cache hits → cost ~30-60% of first call
- Total time: ~3 × 1.5s = 4.5s (vs 47s for one reasoning call)

### Verification
Before running N=3 on the 30-case subset, test a single benchmark with N=3 separate calls:
- Verify all 3 calls succeed
- Verify cache hit tokens are logged for calls 2-3
- Verify 3 distinct invariants are generated
