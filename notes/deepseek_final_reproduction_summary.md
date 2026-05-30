# DeepSeek V4 Pro — Final Reproduction Summary

## All Experiments

| Experiment | Benchmarks | #Corr | First-Correct Faster | Extensions | Regressions |
|---|:---:|---:|---:|---:|---:|
| Reasoning N=1 | Easy-30 | 25/30 (83%) | 4/30 (13%) | 0 | 4 |
| Non-Reasoning N=1 | Easy-30 | 21/30 (70%) | 21/30 (70%) | 0 | 3 |
| Non-Reasoning N=16 | Easy-30 | 25/30 (83%) | 23/30 (77%) | 0 | 0 |
| Non-Reasoning N=16 | Hard-30 | 20/30 (67%) | 20/30 (67%) | 0 | 1 |
| **Non-Reasoning N=16** | **Full 866** | **703/866 (81%)** | **638/866 (74%)** | **11** | **48** |

## Full 866 Breakdown

| Category | Count |
|---:|---|
| #Corr | 703 (81.2%) |
| solved_and_faster (first-correct) | 627 (72.4%) |
| solved_and_faster (fastest-correct) | 647 (74.7%) |
| extension | 11 (1.3%) |
| correct_but_slower | 32 (3.7%) |
| correct_no_effect | 4 (0.5%) |
| regression | 48 (5.5%) |
| faster_but_not_solved | 95 (11.0%) |
| both_false_or_incomparable | 20 (2.3%) |

## Failure Mode Summary

| Mode | Count | % |
|---:|---:|---|
| Invariant rejected (assert≠TRUE) | 95+48=143 | 16.5% |
| Both unsolved (FALSE+FALSE) | 20 | 2.3% |
| Correct but slower than baseline | 32 | 3.7% |
| Genuine improvement | 638 | 73.7% |

## Cache Performance (estimated)

| Metric | Value |
|---:|---|
| sample1 cache hit | ~0-10% (cold) |
| sample2+ cache hit | ~85-95% (warm) |
| Priming overhead | ~2-3s per benchmark (first call) |
| Parallel speed (sample2+) | ~1.3-1.8s per call |

## Infra Notes

- Java 17 required for UAutomizer (openjdk 17.0.15)
- `--add-opens` required for module system
- OSGi `-Dosgi.configuration.area` must be omitted (corrupted cache)
- One-prime-parallel schedule: sample1 cold + parallel(sample2..sample16)
- Incremental save + `--resume` flag for crash recovery

## Safe Final Claim

**On the full 866-benchmark Quokka / InvBench suite, DeepSeek V4 Pro non-reasoning with cache-aware N=16 achieved 703/866 (81%) #Corr and 638/866 (74%) first-correct real end-to-end improvements under our reproduced pipeline. 11 cases went from baseline-unsolved to DeepSeek-solved.**

This reproduction validates:
1. DeepSeek V4 Pro non-reasoning mode is viable for invariant generation
2. Cache-aware one-prime-parallel N=16 balances quality and latency
3. The Quokka / InvBench artifact can run end-to-end without conda, using Python venv
4. Reporting must distinguish #Corr, real improvements, and raw E2E faster
