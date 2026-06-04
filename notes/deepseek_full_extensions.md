# Semantic Extensions（11 題）

**≠ 官方 `#Ext@T`。** 見主報告 [`deepseek_reproduction_report.md`](deepseek_reproduction_report.md) §4.2、§5 Case D。

Baseline **result ≠ TRUE**，但至少一 sample **assert=TRUE**（`scripts/analyze_deepseek_results.py` 的 `semantic_extension`）。

| # | Benchmark | Baseline | Baseline Time | First Correct Sample | DeepSeek E2E | Invariant |
|---:|---:|---:|---:|---:|---:|---|
| 1 | eureka_01-1_1.c | FALSE | 395s | 0 | 421s | relational |
| 2 | fermat1-ll_unwindbound2_4.c | FALSE | 12s | 10 | 11s | Fermat identity |
| 3 | hard2_unwindbound5_7.c | FALSE | 10s | 1 | 10s | division invariant |
| 4 | lcm1_unwindbound2_5.c | FALSE | 8s | 0 | 10s | LCM bounds |
| 5 | prod4br-ll_unwindbound10_3.c | FALSE | 11s | 0 | 14s | product bounds |
| 6 | ps4-ll_unwindbound2_2.c | FALSE | 9s | 2 | 9s | power series |
| 7 | ps5-ll_unwindbound1_3.c | FALSE | 8s | 1 | 7s | power series |
| 8 | tree_del_iter_incorrect_1.c | FALSE | 10s | 0 | 13s | tree deletion |
| 9 | tree_del_iter_incorrect_2.c | FALSE | 11s | 6 | 13s | tree deletion |
| 10 | tree_del_iter_incorrect_3.c | FALSE | 13s | 2 | 16s | tree deletion |
| 11 | tree_del_iter_incorrect_4.c | FALSE | 11s | 6 | 14s | tree deletion |

## Analysis

- **eureka_01-1_1.c**: Only high-value extension (395s baseline, FALSE → assert TRUE). The invariant likely derives the Dijkstra shortest-path relational property.
- **4 tree_del_iter_incorrect cases**: These are FALSE baselines (programs with known bugs). DeepSeek generated invariants but the programs have genuine errors — the invariant proves some property but doesn't fix the underlying bug.
- **Remaining 6**: Small FALSE cases (8-13s baselines). DeepSeek corrective invariants found.

## Caution
Extensions on FALSE baselines may indicate:
1. Genuine invariant discovery (eureka case) — the program IS correct, UAutomizer just couldn't prove it
2. Invariant proves a weaker property — the original assertion might still be violated

tree_del_iter_incorrect cases are known buggy programs — invariants don't fix bugs.
