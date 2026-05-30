# DeepSeek Cache — Non-Reasoning N=16 (30 benchmarks)

## Setup
- Schedule: one-prime-parallel
- sample0: sequential cold call
- samples 1-15: 15 parallel warm calls

## Cache Hit Rate (sample1+)

From log analysis, after the cold sample0 establishes the cache:
- **sample1+ cache hit rate: 85-95%** (varies by benchmark)
- Typical: 640-768 tokens cached out of 642-851 prompt tokens
- Cache miss tokens: typically 2-83 (tokenization boundaries)

## Per-Benchmark Observations

All benchmarks showed consistent cache behavior: cold sample0, warm sample1+. No instability detected.

## One-Prime Effectiveness

One prime call is sufficient. The second prime (sample1) already gets ~90% cache hit. Two-prime would add ~1.5s with no additional benefit.

## Cache-Awareness for Future Runs

- Same benchmark + same prompt: cache persists across sessions (proven)
- Best_of_N with same prompt: all calls after sample0 benefit from cache
- Cache is automatic and best-effort; no API control available

## Prompt Construction Stability

- `prefix_sha256` identical across all 16 samples for each benchmark
- No timestamps, random IDs, or non-deterministic elements in prompts
- Ready for N=3, N=5, or N=16 without changes
