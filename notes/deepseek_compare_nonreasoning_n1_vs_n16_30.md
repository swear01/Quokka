# N=16 vs N=1 Non-Reasoning Comparison (30 benchmarks)

## Command
```bash
# N=16
python batch_invariant_generation.py --max_workers 1 --model_name deepseek-v4-pro \
  --inference_client deepseek --reasoning_mode off --best_of_n 16 \
  --bon_schedule one_prime_parallel --bon_parallelism 15 --temperature 0.2 \
  --benchmark_dir Dataset/evaluation_deepseek_30
```
No `--max_new_tokens`.

## Quality

| Metric | N=1 | N=16 | Delta |
|---|---:|---:|---|
| Extraction rate | 30/30 (100%) | 79/79 (100%) | same |
| Assume TRUE (samples) | 27/30 (90%) | 74/79 (94%) | +4pp |
| **#Corr (benchmarks)** | 21/30 (70%) | **25/30 (83%)** | **+4** |
| Recovered from N=1 failure | — | 4/6 | quality restored |

### Recovered benchmarks
- **benchmark25**: `x < 10` (was `x >= 0 && x <= 10` — too strong)
- **fermat1_3**: `u*u - v*v - 2*u + 2*v == 4*(A+r)` (was assume timeout)
- **hard-u_1**: `q == 0 && d == B*p && r == A` (was assert timeout)
- **hard-u_3**: `d == B*p && r == A - B*q + d - B*p` (was assert timeout)

### Still failing (5)
- benchmark16: precondition as invariant
- benchmark31: only `y >= 0`, missing `x < 0` disjunct
- diamond: invariant `x%2 == y%2` not sufficient
- geo1-u_2: FALSE baseline, invariant can't fix
- hard2_4: `A == q*B + r && r >= 0 && d == B*p` correct but assert fails

## Timing (cold-start, includes prime call)

| Metric | N=1 | N=16 |
|---|---:|---:|
| E2E faster | 23/30 (77%) | 27/30 (90%) |
| Avg gen time | 1.5s | 1.4s (sample0) + 1.5s (parallel max) |
| Avg verify time | 3.5s | 4.0s |
| Avg e2e time | 5.0s | 5.5s |

## Cache Performance

Per-benchmark cache behavior: sample0 sees variable hit (depends on prior benchmark proximity), sample1+ sees ~90% cache hit rate consistently.

## Recommendation

**N=16 non-reasoning is the best reproduction mode so far:**
- 25/30 (83%) #Corr — highest of all configurations
- 4/6 quality regressions from N=1 recovered
- Cold E2E time remains ~5.5s avg
- One-prime-parallel scheduling works as designed
