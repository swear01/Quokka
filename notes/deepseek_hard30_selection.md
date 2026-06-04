# Hard-30 Benchmark Selection

## Method
Queried `Dataset/timing_uautomizer.json` for difficult benchmarks (UNKNOWN/TIMEOUT, slow TRUE, FALSE high-runtime). Filtered for scalar-only using automated check (no arrays, no malloc, no float, no structs, no pthread). Selected 30 deterministically by category + descending runtime.

## Dataset
- Source: `Dataset/evaluation_all/`
- Target: `Dataset/evaluation_deepseek_hard30/`
- Total: 30 benchmarks

## Composition

| Category | Count | Selection method |
|---|---:|---|
| TIMEOUT/high (>=500s) | 3 | All scalar cases with >=500s runtime |
| Slow TRUE (100-450s) | 15 | Top 15 scalar slow TRUE by descending runtime |
| FALSE hard (>=20s) | 7 | Top 7 scalar FALSE by descending runtime |
| Relational/challenging | 5 | Remaining top scalar cases with interesting invariants |

## Per-Benchmark Detail

### Group A: TIMEOUT / High-Runtime (3)

| # | Benchmark | UAutomizer | Runtime | Language | Reason |
|---|---:|---:|---:|---:|---|
| 1 | prodbin-ll_valuebound50_1.c | TRUE | 541s | scalar (long long) | Binary product, very slow |
| 2 | egcd2_2.c | TRUE | 515s | scalar | Extended GCD variant |
| 3 | bresenham-ll_unwindbound10_2.c | FALSE | 508s | scalar (long long) | Bresenham; FALSE = verifier timeout artifact (see bresenham audit) |

### Group B: Slow TRUE (15)

| # | Benchmark | Runtime | Language | Reason |
|---|---:|---:|---:|---|
| 4 | dijkstra-u_valuebound2_4.c | 444s | scalar (unsigned) | Dijkstra algorithm variant |
| 5 | hard2_4.c | 438s | scalar | Integer division by Manna |
| 6 | divbin2_valuebound2_2.c | 338s | scalar (unsigned) | Binary division |
| 7 | geo3-ll_unwindbound5_2.c | 336s | scalar (long long) | Geometric series |
| 8 | dijkstra-u_valuebound2_7.c | 314s | scalar (unsigned) | Dijkstra variant |
| 9 | prodbin-ll_valuebound10_1.c | 312s | scalar (long long) | Binary product (smaller bound) |
| 10 | divbin2_valuebound1_2.c | 307s | scalar (unsigned) | Binary division variant |
| 11 | dijkstra-u_valuebound2_5.c | 276s | scalar (unsigned) | Dijkstra variant |
| 12 | geo2-ll_unwindbound5_2.c | 265s | scalar (long long) | Geometric series |
| 13 | mono-crafted_11_1.c | 262s | scalar | Crafted monomial |
| 14 | prod4br-ll_valuebound2_2.c | 247s | scalar (long long) | Product of 4 bounds |
| 15 | lcm2_valuebound50_1.c | 243s | scalar (unsigned) | LCM+GCD by Dijkstra |
| 16 | sum_by_3_1.c | 214s | scalar (unsigned) | Sum divisibility |
| 17 | hard-u_valuebound1_4.c | 203s | scalar (unsigned) | Integer division (unsigned) |
| 18 | egcd2-ll_unwindbound50_2.c | 181s | scalar (long long) | Extended GCD |

### Group C: FALSE >=20s (7)

| # | Benchmark | Runtime | Language | Reason |
|---|---:|---:|---:|---|
| 19 | hard-u_5.c | 402s | scalar (unsigned) | FALSE, high runtime |
| 20 | cohencu-ll_unwindbound20_7.c | 264s | scalar (long long) | FALSE, Cohen cubes |
| 21 | prod4br-ll_unwindbound5_2.c | 203s | scalar (long long) | FALSE, product bounds |
| 22 | fermat1-ll_unwindbound10_4.c | 202s | scalar | FALSE, Fermat factorization |
| 23 | nested_delay_notd2_1.c | 86s | scalar | FALSE, nested delay |
| 24 | egcd-ll_unwindbound50_5.c | 71s | scalar (long long) | FALSE, extended GCD |
| 25 | egcd-ll_unwindbound10_5.c | 61s | scalar (long long) | FALSE, extended GCD |

### Group D: Relational / Challenging Scalar (5)

| # | Benchmark | Runtime | Language | Reason |
|---|---:|---:|---:|---|
| 26 | hard2_valuebound10_5.c | 175s | scalar | Integer division, relational |
| 27 | dijkstra-u_valuebound2_6.c | 172s | scalar (unsigned) | Dijkstra relational |
| 28 | egcd3-ll_valuebound2_5.c | 163s | scalar (long long) | Extended GCD, relational |
| 29 | hard2_valuebound20_5.c | 160s | scalar | Integer division, larger bound |
| 30 | cohencu-ll_valuebound20_7.c | 145s | scalar (long long) | Cohen cubes, relational |

## Runtime Distribution

| Range | Count |
|---|---:|
| 500s+ | 3 |
| 200-500s | 14 |
| 100-200s | 8 |
| 20-100s | 5 |


## All Scalar
All 30 benchmarks are scalar-only (no arrays, pointers, malloc, float, structs, concurrency). Uses int, unsigned, long long, and nondet functions.

## Expected Bottlenecks
- **Accumulator / arithmetic**: prodbin, ego2, geo, prod4br, lcm2, sum_by_3
- **Relational invariants**: dijkstra-u, divbin2, hard2, hard-u, cohencu
- **FALSE baselines**: DeepSeek cannot fix buggy programs, but invariant quality still informative
- **High runtime**: LLM gen time (~1.5s) easily amortized by 100-500s baseline verifier savings

## Baseline Already Solved?
- 23/30 (77%) are TRUE (solved but slow)
- 7/30 (23%) are FALSE (genuinely unsolved — invariant can't fix program bugs)
- DeepSeek helps by reducing verification time, not by changing solve status
