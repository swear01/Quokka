# DeepSeek 30-Case Failure Analysis

## Runtime Semantics Note

**`PAR@T` and speedup are END-TO-END** — they include LLM generation time. See `print_results.py:168` (`sample_total_time`).

## Summary

| Category | Count | Benchmarks |
|---|---:|---|
| End-to-end FASTER | 4/30 | benchmark23 (2.15x), loopv3 (2.23x), mono-crafted (7.12x), prodbin (2.05x) |
| End-to-end SAME | 1/30 | benchmark30 |
| End-to-end SLOWER | 25/30 | LLM time dominates easy baselines |
| Format/parsing failure | 1/30 | benchmark24 |
| Verifier timeout (assume/assert) | 4/30 | diamond, hard-u_1, hard-u_3, hard2_4 |

## 1. Useful Improvements (4/30 — 13%)

End-to-end speedup >1.05x (includes LLM inference cost):

- `mono-crafted_11_1.c`: **7.12x** (262s → 37s). LLM=33s, verify=4s. Invariant: `x < 10000000 || x % 2 == 0`
- `loopv3_1.c`: **2.23x** (53s → 24s). LLM=18s, verify=6s. Invariant: `i % 4 == 0`
- `benchmark23_conjunctive_1.c`: **2.15x** (37s → 17s). LLM=14s, verify=3s. Invariant: `j == 2*i`
- `prodbin-ll_valuebound10_1.c`: **2.05x** (312s → 153s). LLM=19s, verify=134s. Invariant: `z + x*y == a*b`

All four share: baseline runtime >> LLM time, and invariant significantly reduces verification time.

## 2. Correct but No Effect (26/30)

The dominant category. DeepSeek v4-pro generates syntactically correct, verifier-accepted invariants for nearly all benchmarks. Examples:

- `benchmark02`: `l >= 1` — correct invariant, but baseline already TRUE in 8s
- `benchmark17`: `k == i` — captures loop relationship perfectly
- `cohencu`: `z == 6*n + 6` — the exact assertion inside the loop
- `prodbin`: `z + x*y == a*b` — the key accumulator invariant
- `hard2_4`: `d == p*B` — critical invariant for division algorithm
- `bresenham`: `2*Y*x - 2*X*y - X + 2*Y - v == 0` — reproduced from source code assertion

## 3. Too Weak (1/30)

- `geo1-u_2`: invariant `x*(z-1) == y-1` maintained by the loop (assume=TRUE) but doesn't prove postcondition `1+x-y == 0` (assert=FALSE). This program has a FALSE baseline — the assertion IS violated. DeepSeek generated the program's own assertion logic (essentially the computation identity) but this doesn't fix the FALSE result.

## 4. Verifier Timeout (4/30)

- `diamond_1-1_1`: assume TIMEOUT at 41.5s limit (1.2x baseline of 34.6s). The invariant `(x%2)==(y%2) || x<99` is complex and makes the assume checkpoint harder to verify.
- `hard-u_1`, `hard-u_3`: assert TIMEOUT. The invariants `A == q*B + r && d == B*p && r < d` are strong, but the assert version can't complete within the short timeout window.
- `hard2_4`: assert TIMEOUT at 525s. Very long baseline (437s). The invariant `d == p*B` is fine but the verification system simply takes time.

## 5. Format/API Failure (1/30)

- `benchmark24_conjunctive_1.c`: Response (`condition`) was a placeholder — the model's reasoning content filled all tokens and the final token output was just `condition` (8 chars). This is a reasoning-model quirk where 8192 tokens weren't enough for this specific benchmark's complex reasoning. Gen time: 158s (very long thinking).

## Key Takeaway

The **baseline solvable rate is too high** (29/30 TRUE) to measure improvement. DeepSeek works extremely well (87% full acceptance) but we need benchmarks where UAutomizer struggles — cases with UNKNOWN or TIMEOUT baselines, not just slow-but-solved cases.
