# DeepSeek Smoke Benchmark Subset

## Selection: 8 benchmarks from Dataset/evaluation_all/

| # | Filename | Why selected | Has loop? | Has assertion? | Arrays/pointers? | Expected difficulty |
|---|---:|---|---|---|---:|---|
| 1 | benchmark02_linear_1.c | Simple linear invariant (l >= 1), trivial | while loop | yes | no | Easy |
| 2 | benchmark16_conjunctive_1.c | Conjunctive invariant, nondet loop | while nondet | yes | no | Easy-Medium |
| 3 | benchmark25_linear_1.c | Simple linear invariant (x <= 10), trivial | while loop | yes | no | Easy |
| 4 | benchmark09_conjunctive_1.c | Conjunctive invariant, loop with break | while loop+break | yes | no | Medium |
| 5 | benchmark31_disjunctive_1.c | Disjunctive invariant, infinite loop | while(1)+break | yes | no | Medium |
| 6 | benchmark38_conjunctive_1.c | Arithmetic relation (x == 4*y), nondet loop | while nondet | yes | no | Medium |
| 7 | benchmark53_polynomial_1.c | Polynomial invariant (x*y>=0), nondet loop | while nondet | yes | no | Hard |
| 8 | cohencu_1.c | Arithmetic invariant (z==6*n+6), assert inside loop | while+break | yes (inside loop) | no | Hard |

All benchmarks use scalar variables only (no arrays, no pointers, no heap, no concurrency).

Category breakdown:
- 2 easy (trivial invariant, simple while)
- 2 medium (conjunctive/disjunctive with break)
- 2 medium-hard (arithmetic relations)
- 2 hard (polynomial, assert inside loop)
