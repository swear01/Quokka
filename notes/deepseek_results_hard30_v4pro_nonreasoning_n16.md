# DeepSeek Hard-30 Results — V4 Pro Non-Reasoning N=16

## Command
```bash
python batch_invariant_generation.py --max_workers 16 --model_name deepseek-v4-pro \
  --inference_client deepseek --reasoning_mode off --best_of_n 16 \
  --bon_schedule one_prime_parallel --bon_parallelism 15 --temperature 0.2 \
  --benchmark_dir Dataset/evaluation_deepseek_hard30
```

## Quality (Audited by scripts/analyze_deepseek_results.py)

| Metric | Count |
|---:|---|
| #Corr | 20/30 (67%) |
| **REAL improvements** (solved_and_faster) | **20/30 (67%)** |
| raw E2E faster (misleading) | 28/30 |
| faster_but_not_solved (fast rejections) | 8/30 |
| extension (baseline unsolved → solved) | 0/30 |
| regression | 1/30 |
| incomparable | 1/30 |

**20/30 benchmarks get verifier-verified invariant with end-to-end speedup.**
8/30 are "raw faster" because UAutomizer quickly rejects weak invariants — these are NOT improvements.

## Top Speedups

| Benchmark | Baseline | E2E | Speedup |
|---|---|---:|---:|
| egcd2_2 | 515s | 5s | **102x** |
| bresenham-ll_unwindbound10_2 | 508s FALSE | 7s | 77x |
| hard2_4 | 438s | 6s | 71x |
| divbin2_valuebound2_2 | 338s | 6s | 56x |
| geo3-ll_unwindbound5_2 | 336s | 6s | 52x |
| prod4br-ll_valuebound2_2 | 247s | 5s | 51x |
| cohencu-ll_unwindbound20_7 | 264s FALSE | 6s | 43x |
| prod4br-ll_unwindbound5_2 | 203s FALSE | 5s | 39x |

## Slower Cases (2/30)

| Benchmark | Baseline | E2E | Speedup |
|---|---|---:|---:|
| hard-u_5 | 402s FALSE | 483s | 0.8x (all asserts timeout) |
| hard2_valuebound10_5 | 175s | 210s | 0.8x (asserts timeout) |

## Comparison: Easy-30 vs Hard-30

| Metric | Easy-30 N=16 | Hard-30 N=16 |
|---|---:|---:|
| #Corr | 25/30 (83%) | 20/30 (67%) |
| E2E faster | 27/30 (90%) | **28/30 (93%)** |
| Avg benchmark speedup | ~5x | **~30x** |
| FALSE baselines | 1/30 | 7/30 |
| Baseline avg | 8s | 260s |

DeepSeek invariants provide massive speedup on hard benchmarks (avg 30x) but slightly lower #Corr (67% vs 83%) because these are genuinely harder problems.
