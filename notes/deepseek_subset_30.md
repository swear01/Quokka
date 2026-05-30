# DeepSeek 30-Case Controlled Subset

## Selection Method
Manual inspection of `Dataset/evaluation_all/` against `Dataset/timing_uautomizer.json`.
Filtered for: scalar only, no arrays, no pointers, no heap, no concurrency, no floating point.

## Subset Composition

| # | Benchmark | Category | Why selected | Loop? | Assert? | Arrays? | Difficulty |
|---|---:|---|---:|---:|---:|---:|---|
| 1 | benchmark02_linear_1.c | easy | simple linear, l>0 invariant | while | yes | no | Easy |
| 2 | benchmark10_conjunctive_1.c | easy | accumulator with break | while | yes | no | Easy |
| 3 | benchmark17_conjunctive_1.c | easy | i/k increment together | while | yes | no | Easy |
| 4 | benchmark24_conjunctive_1.c | easy | conjunctive invariant | while | yes | no | Easy |
| 5 | benchmark25_linear_1.c | easy | x<=10 loop counter | while | yes | no | Easy |
| 6 | benchmark09_conjunctive_1.c | medium | x==y relation with break | while+break | yes | no | Medium |
| 7 | benchmark16_conjunctive_1.c | medium | conjunctive, nondet loop | while nondet | yes | no | Medium |
| 8 | benchmark30_conjunctive_1.c | medium | conjunctive | while | yes | no | Medium |
| 9 | benchmark31_disjunctive_1.c | medium | disjunctive with break | while(1)+break | yes | no | Medium |
| 10 | benchmark38_conjunctive_1.c | medium | arithmetic relation x==4*y | while nondet | yes | no | Medium |
| 11 | benchmark39_conjunctive_1.c | medium | conjunctive | while | yes | no | Medium |
| 12 | benchmark45_disjunctive_1.c | medium | disjunctive nondet | while nondet | yes | no | Medium |
| 13 | benchmark46_disjunctive_1.c | medium | disjunctive | while | yes | no | Medium |
| 14 | benchmark53_polynomial_1.c | medium | polynomial x*y>=0 | while nondet | yes | no | Medium-Hard |
| 15 | fermat1_2.c | medium | Fermat factorization (3 GT inv) | while(1) | yes | no | Medium-Hard |
| 16 | cohencu_1.c | arithmetic | cube computation | while(1)+break | inside | no | Hard |
| 17 | cohendiv-ll_valuebound10_1.c | arithmetic | Cohen's integer division | while(1) | inside | no | Hard |
| 18 | egcd_1.c | arithmetic | extended Euclid GCD | while(1) | inside | no | Hard |
| 19 | fermat1_1.c | arithmetic | Fermat factorization (3 GT inv) | while(1)+while | inside | no | Hard |
| 20 | geo1-u_2.c | arithmetic | geometric series, FALSE result | while(1)+break | yes | no | Medium |
| 21 | diamond_1-1_1.c | branch/relational | parity relation (modulo) | while | yes | no | Hard |
| 22 | hard-u_1.c | branch/relational | integer division with asserts | while(1) | inside | no | Hard |
| 23 | hard-u_3.c | branch/relational | integer division variant | while(1)+while | inside | no | Hard |
| 24 | loopv3_1.c | branch/relational | loop variant with nondet branch | while | yes | no | Medium-Hard |
| 25 | benchmark23_conjunctive_1.c | branch/relational | conjunctive, 37s baseline | while | yes | no | Medium-Hard |
| 26 | hard2_4.c | harder | integer division, 437.8s | while(1)+while | inside | no | Very Hard |
| 27 | bresenham-ll_valuebound100_1.c | harder | Bresenham line algorithm | while(1)+break | inside | no | Very Hard |
| 28 | prodbin-ll_valuebound10_1.c | harder | binary product, 312.3s | while(1) | inside | no | Very Hard |
| 29 | mono-crafted_11_1.c | harder | crafted, 262.3s | while(1)+while | inside | no | Very Hard |
| 30 | fermat1_3.c | harder | Fermat factorization, 3 GT inv | while(1)+while | inside | no | Hard |

## Baseline Metadata

| # | Benchmark | UAutomizer | Runtime | Has GT invariants? |
|---|---:|---:|---:|---:|
| 1 | benchmark02_linear_1.c | TRUE | 8.0s | yes |
| 2 | benchmark10_conjunctive_1.c | TRUE | 8.1s | yes |
| 3 | benchmark17_conjunctive_1.c | TRUE | 6.7s | yes |
| 4 | benchmark24_conjunctive_1.c | TRUE | 7.1s | yes |
| 5 | benchmark25_linear_1.c | TRUE | 7.5s | yes |
| 6 | benchmark09_conjunctive_1.c | TRUE | 7.6s | yes |
| 7 | benchmark16_conjunctive_1.c | TRUE | 6.9s | yes |
| 8 | benchmark30_conjunctive_1.c | TRUE | 6.9s | yes |
| 9 | benchmark31_disjunctive_1.c | TRUE | 7.4s | yes |
| 10 | benchmark38_conjunctive_1.c | TRUE | 6.8s | yes |
| 11 | benchmark39_conjunctive_1.c | TRUE | 7.7s | yes |
| 12 | benchmark45_disjunctive_1.c | TRUE | 6.6s | yes |
| 13 | benchmark46_disjunctive_1.c | TRUE | 7.2s | yes |
| 14 | benchmark53_polynomial_1.c | TRUE | 8.6s | yes |
| 15 | fermat1_2.c | TRUE | 15.8s | yes (3 invariants) |
| 16 | cohencu_1.c | TRUE | 6.7s | yes |
| 17 | cohendiv-ll_valuebound10_1.c | TRUE | 8.3s | yes (2 invariants) |
| 18 | egcd_1.c | TRUE | 9.6s | yes |
| 19 | fermat1_1.c | TRUE | 13.3s | yes (3 invariants) |
| 20 | geo1-u_2.c | FALSE | 8.2s | no |
| 21 | diamond_1-1_1.c | TRUE | 34.6s | yes |
| 22 | hard-u_1.c | TRUE | 7.4s | yes |
| 23 | hard-u_3.c | TRUE | 8.2s | yes |
| 24 | loopv3_1.c | TRUE | 52.7s | yes |
| 25 | benchmark23_conjunctive_1.c | TRUE | 37.0s | yes |
| 26 | hard2_4.c | TRUE | 437.8s | yes (2 invariants) |
| 27 | bresenham-ll_valuebound100_1.c | TRUE | 9.2s | yes |
| 28 | prodbin-ll_valuebound10_1.c | TRUE | 312.3s | yes |
| 29 | mono-crafted_11_1.c | TRUE | 262.3s | yes |
| 30 | fermat1_3.c | TRUE | 12.1s | yes (3 invariants) |
