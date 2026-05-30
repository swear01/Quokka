# DeepSeek V4 Pro — All Modes Comparison (Audited by analyze_deepseek_results.py)

| Metric | Reasoning N=1 | Non-Reason N=1 | Non-Reason N=16 | Hard-30 N=16 |
|---|---:|---:|---:|---|
| #Corr | **25/30 (83%)** | 21/30 (70%) | **25/30 (83%)** | 20/30 (67%) |
| REAL improvements | 4/30 (13%) | **21/30 (70%)** | **23/30 (77%)** | 20/30 (67%) |
| raw E2E faster (misleading) | 4/30 | 26/30 | 27/30 | 28/30 |
| faster_but_not_solved | 0 | 5 | 4 | 8 |
| correct_but_slower | 20 | 0 | 1 | 0 |
| regression | 4 | 3 | 0 | 1 |
| avg gen time | 46.9s | 1.5s | 1.5s | 1.5s |
| avg baseline time | 55s | 55s | 55s | 260s |

## Key Insight

**Reasoning has highest #Corr (83%)** but gen time (47s) overwhelms easy baselines → only 13% real E2E improvement.

**Non-reasoning N=16** recovers reasoning's quality (83% #Corr) while being 31x faster → 77% real E2E improvement.

**Hard-30 N=16** shows where DeepSeek shines: 67% #Corr, 67% real improvement, with baselines averaging 260s.

## Definitions

- `solved_and_faster`: invariant correct (assert=TRUE) AND fastest-correct-sample E2E < 95% baseline
- `faster_but_not_solved`: E2E faster but NO sample has assert=TRUE (fast rejection)
- `raw E2E faster` = solved_and_faster + extension + faster_but_not_solved (NEVER call this "improvement")
- `real_improvement` = solved_and_faster + extension
