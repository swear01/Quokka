# DeepSeek Cache Instrumentation — 30-Case Run

## Cache Instrumentation Status

Cache prefix logging was active throughout the 30-case run via `[CachePrefix]` and `[DeepSeekCache]` log entries.

## Observations

### Prefix Stability
All 30 benchmarks used `best_of_n=1` with zero few-shot examples (`num_shots=0`). The prefix section of each prompt was always empty (`prefix_chars=0`, `prefix_sha256=e3b0c44298fc1c14` which is SHA-256 of empty string).

The suffix (program + insertion points) varied by benchmark as expected.

### Prompt Size Distribution
- Average prompt_total_chars: ~2600
- Range: 2088 (benchmark25) to 3329 (bresenham-ll)
- Average suffix_chars (program + points): ~2550

### Cache-Friendliness Assessment
- **best_of_n=1**: Each call has a unique full prompt (different program). Cache hits across benchmarks are unlikely.
- **Future best_of_n>1**: All n completions in a single API call share the identical prompt. DeepSeek's prefix caching will work naturally.
- **Future benchmark re-runs**: Same benchmark + same settings = same prompt. Cache would hit for re-runs.

### No Instabilities Detected
All 30 calls produced stable, deterministic prompts with no:
- Timestamps
- Random IDs
- Non-deterministic ordering

## Example Log Entry

```
[CachePrefix] prefix_chars=0 suffix_chars=2204 prefix_sha256=e3b0c44298fc1c14 prompt_sha256=5252bdb7e68d3bd2
[DeepSeekCache] model=deepseek-v4-pro prompt_total_chars=2297 sample=0/1 prefix_sha256=5252bdb7e68d3bd2
```
