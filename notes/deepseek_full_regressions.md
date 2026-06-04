# Regressions（48 題）

Baseline `result=TRUE`，但 DeepSeek 無任一 sample 的 assert=TRUE。  
主報告：[`deepseek_reproduction_report.md`](deepseek_reproduction_report.md) §4–§5。

## Categorization

| Category | Count | Examples |
|---:|---|
| Invariant rejected by verifier | ~20 | cohencu variants, egcd variants, hard-u/hard2 variants |
| Fast rejection (assert timeout/quick fail) | ~15 | ps4/ps5 power-series variants, geo/geo2 variants |
| No valid invariant extracted | ~8 | poly1 (array/malloc), cohencu_9 variants |
| Verifier assume timeout | ~5 | dijkstra-u_valuebound2_4 (444s), hard2_valuebound10_5 (175s) |

## Full List

| # | Benchmark | Baseline Time | Likely Cause |
|---:|---:|---:|---|
| 1-7 | cohencu variants (*_9) | 10-46s | Complex arithmetic, invariants too weak |
| 8-10 | cohendiv variants (*_7) | 8-10s | Division algorithm, invariant format |
| 11 | dijkstra-u_valuebound2_4.c | 444s | Assume timeout (533s limit) |
| 12-17 | egcd variants | 7-65s | GCD invariants rejected |
| 18-20 | geo variants | 8-33s | Geometric series, invariant mismatch |
| 21-23 | hard-ll/hard-u/hard2 variants | 7-77s | Integer division, relational |
| 24 | hard2_valuebound10_5.c | 175s | Assert timeout |
| 25 | hard2_valuebound10_7.c | 22s | Assert timeout |
| 26 | lcm1_valuebound5_5.c | 9s | LCM invariant rejected |
| 27 | poly1_1.c | 398s | Uses malloc/arrays, no valid invariant |
| 28-29 | ps2_ll_2.c, ps5_ll_2.c | 7-10s | Power series format |
| 30-34 | ps4 variants | 8-10s | Power series format |
| 35 | ps5_ll_valuebound2_3.c | 9s | Power series format |

## Key Pattern

Regressions cluster in specific families:
- **cohencu *_9 variants** (7 cases): The "9th" variant of Cohen cube benchmarks consistently fails
- **egcd variants** (6 cases): Specific unwind/valuebound variants fail
- **ps4/ps5 power-series** (6 cases): Consistently rejected by verifier
- **hard/hard2 division** (5 cases): Integer division with timeout issues

## Root Cause Assessment

Most regressions are **not format failures** — invariants were extracted and assumed correct (assume=TRUE), but the assert phase was rejected (assert=FALSE or TIMEOUT). This means the invariant was maintained by the loop but insufficient to prove the postcondition.
