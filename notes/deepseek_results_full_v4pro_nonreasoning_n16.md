# DeepSeek V4 Pro — Full Quokka / InvBench Reproduction (866 benchmarks)

## Configuration
- Model: deepseek-v4-pro (non-reasoning, thinking disabled)
- best_of_n: 16 (one-prime-parallel, bon_parallelism=15)
- temperature: 0.2
- max_new_tokens: omitted (no limit)
- max_workers: 16
- Verifier: UAutomizer (Java 17, --add-opens)
- Python: 3.10.12, venv

## Results (Audited by analyze_deepseek_results.py)

| Metric | Count |
|---:|---|
| Total benchmarks | 866 |
| **#Corr** (≥1 assert TRUE) | **703/866 (81.2%)** |
| First-correct real improvements | 638/866 (73.7%) |
| Fastest-correct real improvements | 658/866 (76.0%) |
| solved_and_faster (first) | 627 |
| solved_and_faster (fastest) | 647 |
| **extension** (baseline→solved) | **11** |
| regression | 48 |
| faster_but_not_solved | 41 |
| correct_but_slower | 52 |
| correct_no_effect | 4 |
| both_false_or_incomparable | 95 |
| raw E2E faster (misleading) | 753 |

## Headline

**On the full 866-benchmark Quokka / InvBench suite, DeepSeek V4 Pro non-reasoning N=16 achieved 703/866 (81%) #Corr and 638/866 (74%) first-correct real end-to-end improvements.**

11 benchmarks went from baseline-unsolved to DeepSeek-solved (extension).
48 benchmarks had baseline solved but all DeepSeek invariants rejected (regression).

## PAR@T, #Slv@T, #Ext@T

(TBD — requires print_results.py analysis)

## Comparison to Subsets

| Metric | Easy-30 | Hard-30 | Full (866) |
|---:|---:|---:|---|
| #Corr | 25/30 (83%) | 20/30 (67%) | 703/866 (81%) |
| First-correct faster | 23/30 (77%) | 20/30 (67%) | 638/866 (74%) |
| Extensions | 0 | 0 | 11 |
| Regressions | 0 | 1 | 48 |

The full benchmark #Corr (81%) matches the Easy-30 (83%) closely, suggesting the subset was representative.

## Failure Modes

| Category | Count | Examples |
|---:|---|
| Regression (baseline solved, invariant rejected) | 48 | soft_float variants, tree_del variants |
| both_false_or_incomparable | 95 | mostly FALSE baselines with no fix |
| faster_but_not_solved | 41 | fast rejections, not improvements |
| correct_but_slower | 52 | invariant correct but gen time makes E2E slower |

## Reproducibility

- git commit: 60301cb79ba594945f2049990421f5d5d4d95afc
- result file: baselines/results/deepseek_v4pro_nonreasoning_n16_full_20260530_015014/
- result SHA256: 9c24537ab6216d...
- analysis: scripts/analyze_deepseek_results.py
