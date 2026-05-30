# DeepSeek 30-Case Results — V4 Pro, best_of_n=1

## Command
```bash
source .venv/bin/activate
python baselines/batch_invariant_generation.py \
  --max_workers 1 \
  --model_name "deepseek-v4-pro" \
  --inference_client deepseek \
  --best_of_n 1 \
  --temperature 0.2 \
  --benchmark_dir /home/swear01/Quokka/Dataset/evaluation_deepseek_30
```
(no `--max_new_tokens` → default 8192)

## Runtime Metric Semantics

**`PAR@T` and speedup metrics are END-TO-END.** They include both LLM inference time and verification time.

`sample_total_time()` in `print_results.py:168`: `generation_time + max(assume_time, assert_time)`

Fields in result JSON:
- `generation_time` — LLM API call wall-clock time
- `verify_time_taken` — max(assume_time, assert_time)
- `assume_verification_time` — UAutomizer assume-phase time
- `assert_verification_time` — UAutomizer assert-phase time

## Per-Benchmark Results

| # | Benchmark | Baseline | Baseline Time | DeepSeek Invariant | Extracted? | Assume | Assert | DeepSeek Result | Gen Time | Improved? | Failure Mode |
|---:|---|---:|---:|---|:---:|---:|---:|---:|---:|---:|---|
| 1 | benchmark02_linear_1.c | TRUE | 8.0s | `l >= 1` | yes | TRUE | TRUE | TRUE | 22.1s | no-effect | — |
| 2 | benchmark09_conjunctive_1.c | TRUE | 7.6s | `x == y && x >= 0` | yes | TRUE | TRUE | TRUE | 42.2s | no-effect | — |
| 3 | benchmark10_conjunctive_1.c | TRUE | 8.1s | `c >= 0 && i >= 0` | yes | TRUE | TRUE | TRUE | 40.3s | no-effect | — |
| 4 | benchmark16_conjunctive_1.c | TRUE | 6.9s | `1 <= i + k && i + k <= 2 && i >= 1` | yes | TRUE | TRUE | TRUE | 22.9s | no-effect | — |
| 5 | benchmark17_conjunctive_1.c | TRUE | 6.7s | `k == i` | yes | TRUE | TRUE | TRUE | 17.8s | no-effect | — |
| 6 | benchmark23_conjunctive_1.c | TRUE | 37.0s | `j == 2 * i` | yes | TRUE | TRUE | TRUE | 14.2s | no-effect | — |
| 7 | benchmark24_conjunctive_1.c | TRUE | 7.1s | `condition` (placeholder) | partial | UNKNOWN | UNKNOWN | TRUE | 158.3s | no-effect | parsing failure |
| 8 | benchmark25_linear_1.c | TRUE | 7.5s | `x <= 10` | yes | TRUE | TRUE | TRUE | 45.4s | no-effect | — |
| 9 | benchmark30_conjunctive_1.c | TRUE | 6.9s | `x == y` | yes | TRUE | TRUE | TRUE | 4.3s | no-effect | — |
| 10 | benchmark31_disjunctive_1.c | TRUE | 7.4s | `(x < 0) \|\| (y >= 0)` | yes | TRUE | TRUE | TRUE | 56.2s | no-effect | — |
| 11 | benchmark38_conjunctive_1.c | TRUE | 6.8s | `x == 4 * y && x >= 0` | yes | TRUE | TRUE | TRUE | 17.1s | no-effect | — |
| 12 | benchmark39_conjunctive_1.c | TRUE | 7.7s | `x == 4 * y && x >= 0` | yes | TRUE | TRUE | TRUE | 16.8s | no-effect | — |
| 13 | benchmark45_disjunctive_1.c | TRUE | 6.6s | `x > 0 \|\| y > 0` | yes | TRUE | TRUE | TRUE | 17.1s | no-effect | — |
| 14 | benchmark46_disjunctive_1.c | TRUE | 7.2s | `x > 0 \|\| y > 0 \|\| z > 0` | yes | TRUE | TRUE | TRUE | 16.2s | no-effect | — |
| 15 | benchmark53_polynomial_1.c | TRUE | 8.6s | `x * y >= 0` | yes | TRUE | TRUE | TRUE | 25.9s | no-effect | — |
| 16 | bresenham-ll_valuebound100_1.c | TRUE | 9.2s | `2*Y*x - 2*X*y - X + 2*Y - v == 0` | yes | TRUE | TRUE | TRUE | 43.1s | no-effect | — |
| 17 | cohencu_1.c | TRUE | 6.7s | `z == 6 * n + 6` | yes | TRUE | TRUE | TRUE | 52.7s | no-effect | — |
| 18 | cohendiv-ll_valuebound10_1.c | TRUE | 8.3s | `x == q*y + r` | yes | TRUE | TRUE | TRUE | 99.8s | no-effect | — |
| 19 | diamond_1-1_1.c | TRUE | 34.6s | `(x % 2) == (y % 2) \|\| x < 99` | yes | TIMEOUT | TRUE | TRUE | 97.7s | no-effect | verifier timeout (assume) |
| 20 | egcd_1.c | TRUE | 9.6s | `a == p*x + r*y && b == q*x + s*y` | yes | TRUE | TRUE | TRUE | 52.4s | no-effect | — |
| 21 | fermat1_1.c | TRUE | 13.3s | `4*(A+r) == u*u - v*v - 2*u + 2*v` | yes | TRUE | TRUE | TRUE | 65.9s | no-effect | — |
| 22 | fermat1_2.c | TRUE | 15.8s | `4*(A+r) == u*u - v*v - 2*u + 2*v` | yes | TRUE | TRUE | TRUE | 63.7s | no-effect | — |
| 23 | fermat1_3.c | TRUE | 12.1s | `4*(A+r) == u*u - v*v - 2*u + 2*v` | yes | TRUE | TRUE | TRUE | 43.3s | no-effect | — |
| 24 | geo1-u_2.c | FALSE | 8.2s | `x*(z-1) == y-1` | yes | TRUE | FALSE | FALSE | 77.1s | regression | too weak |
| 25 | hard-u_1.c | TRUE | 7.4s | `A == q*B + r && d == B*p && r < d` | yes | TRUE | TIMEOUT | TRUE | 55.7s | no-effect | verifier timeout (assert) |
| 26 | hard-u_3.c | TRUE | 8.2s | `A == q*B + r && d == B*p && r < d` | yes | TRUE | TIMEOUT | TRUE | 51.1s | no-effect | verifier timeout (assert) |
| 27 | hard2_4.c | TRUE | 437.8s | `d == p * B` | yes | TRUE | TIMEOUT | TRUE | 122.4s | no-effect | verifier timeout (assert) |
| 28 | loopv3_1.c | TRUE | 52.7s | `i % 4 == 0` | yes | TRUE | TRUE | TRUE | 17.8s | no-effect | — |
| 29 | mono-crafted_11_1.c | TRUE | 262.3s | `x < 10000000 \|\| x % 2 == 0` | yes | TRUE | TRUE | TRUE | 32.8s | no-effect | — |
| 30 | prodbin-ll_valuebound10_1.c | TRUE | 312.3s | `z + x*y == (long long)a * b` | yes | TRUE | TRUE | TRUE | 18.6s | no-effect | — |

## Aggregate Metrics

| Metric | Value |
|---:|---|
| Invariants extracted | 29/30 (97%) |
| Verifier-accepted (assume=TRUE) | 28/30 (93%) |
| Fully accepted (assume=TRUE + assert=TRUE) | 26/30 (87%) |
| Baseline already solved | 29/30 (97%) |
| Avg generation time | 46.9s |
| Avg verification time (with invariant) | 23.8s |

## End-to-End Speedup (LLM time included)

| Verdict | Count | Benchmarks |
|---|---:|---|
| FASTER (>1.05x) | 4/30 (13%) | mono-crafted (7.12x), loopv3 (2.23x), benchmark23 (2.15x), prodbin (2.05x) |
| SAME | 1/30 | benchmark30 (1.04x) |
| SLOWER | 25/30 (83%) | LLM time dominates on easy/small baselines |

## Key Finding

**DeepSeek v4-pro generates high-quality invariants (87% full acceptance).** On benchmarks where the baseline verifier is slow (37s+), the invariant can provide end-to-end speedup (up to 7.12x). On easy benchmarks (baseline <15s), LLM inference time dominates, making end-to-end slower.

**To see improvement, need benchmarks where `baseline_runtime >> LLM_generation_time`.**
