# DeepSeek V4 Pro: Reasoning vs Non-Reasoning N=1 Comparison

## Command
```bash
# Reasoning
python batch_invariant_generation.py ... --reasoning_mode (default)

# Non-Reasoning
python batch_invariant_generation.py ... --reasoning_mode off
```
No `--max_new_tokens` in either run. `extra_body={'thinking': {'type': 'disabled'}}` sent for non-reasoning.

## Aggregate Comparison

| Metric | Reasoning | Non-Reasoning | Winner |
|---|---:|---:|---|
| Extraction rate | 29/30 (97%) | 30/30 (100%) | Non-reasoning |
| Assume TRUE | 28/30 (93%) | 27/30 (90%) | Reasoning |
| Assert TRUE / #Corr | 26/30 (87%) | 21/30 (70%) | Reasoning |
| **Gen time mean** | 46.9s | 1.5s | **Non-reasoning (31x faster)** |
| Gen time median | 43.0s | 1.5s | Non-reasoning |
| Gen time range | 4.3-158.3s | 1.0-2.0s | Non-reasoning |
| Verifier-only faster | — | 27/30 (90%) | — |
| **End-to-end faster** | 4/30 (13%) | **23/30 (77%)** | **Non-reasoning** |
| End-to-end slower | 25/30 (83%) | 2/30 (7%) | Non-reasoning |
| Regressions | 1/30 | 1/30 | Tie |
| Avg overall time | 73.9s | 10.1s | Non-reasoning |
| Token usage (output) | 11-2920 | 11-42 | Non-reasoning |

## Per-Benchmark Speedup

| Benchmark | Reasoning E2E | Non-reasoning E2E | Reasoning OK? | Non-reas OK? | Better |
|---|---|---:|---:|---:|---|---|
| benchmark02 | 0.32x | 1.72x | yes | yes | Non-reasoning |
| benchmark09 | 0.17x | 2.16x | yes | yes | Non-reasoning |
| benchmark10 | 0.19x | 2.01x | yes | yes | Non-reasoning |
| benchmark16 | 0.27x | 1.86x | yes | no (assert FALSE) | Reasoning (quality) |
| benchmark17 | 0.32x | 1.72x | yes | yes | Non-reasoning |
| benchmark23 | 2.15x | 8.58x | yes | yes | Non-reasoning |
| benchmark24 | 0.04x | 1.74x | no (format) | yes | Non-reasoning |
| benchmark25 | 0.16x | 1.79x | yes | no (assert FALSE) | Reasoning (quality) |
| benchmark30 | 1.04x | 1.89x | yes | yes | Non-reasoning |
| benchmark31 | 0.13x | 2.04x | yes | no (assert FALSE) | Reasoning (quality) |
| benchmark38 | 0.35x | 1.59x | yes | yes | Non-reasoning |
| benchmark39 | 0.39x | 1.63x | yes | yes | Non-reasoning |
| benchmark45 | 0.34x | 1.78x | yes | yes | Non-reasoning |
| benchmark46 | 0.38x | 1.77x | yes | yes | Non-reasoning |
| benchmark53 | 0.29x | 1.72x | yes | yes | Non-reasoning |
| bresenham | 0.20x | 1.74x | yes | yes | Non-reasoning |
| cohencu | 0.12x | 1.54x | yes | yes | Non-reasoning |
| cohendiv | 0.08x | 1.72x | yes | yes | Non-reasoning |
| diamond | 0.25x | 4.65x | yes (TIMEOUT) | no (assert FALSE) | Neither |
| egcd | 0.17x | 1.47x | yes | yes | Non-reasoning |
| fermat1_1 | 0.19x | 2.10x | yes | yes | Non-reasoning |
| fermat1_2 | 0.23x | 2.21x | yes | yes | Non-reasoning |
| fermat1_3 | 0.25x | 0.75x | yes | no (TIMEOUT+FALSE) | Reasoning |
| geo1-u_2 | 0.10x | 0.69x | yes | no (TIMEOUT+FALSE) | Reasoning |
| hard-u_1 | 0.11x | 0.70x | yes | no (assert TIMEOUT) | Reasoning |
| hard-u_3 | 0.13x | 0.71x | yes | no (assert TIMEOUT) | Reasoning |
| hard2_4 | 0.68x | 94.21x | yes (TIMEOUT) | no (assert FALSE) | Neither |
| loopv3 | 2.23x | 8.08x | yes | yes | Non-reasoning |
| mono-crafted | 7.12x | 33.50x | yes | yes | Non-reasoning |
| prodbin | 2.05x | 2.38x | yes | yes | Non-reasoning |

## Analysis

### Non-reasoning wins on speed (massively)
- Generation time dropped from avg 47s to 1.5s (31x)
- 23/30 end-to-end faster (vs 4/30 for reasoning)
- Average overall time: 10.1s (vs 73.9s)

### Reasoning wins on quality (moderately)
- #Corr: 26/30 (87%) vs 21/30 (70%)
- 6 cases where non-reasoning invariant was rejected or timed out
- Non-reasoning tends to produce simpler/weaker invariants

### Key quality regressions in non-reasoning
- benchmark16: precondition as invariant (not strong enough)
- benchmark25: over-constrained (assert fails on the invariant itself)
- benchmark31: `y >= 0` only (missing the `x < 0` disjunct)
- diamond: invariant asserts wrong property format
- hard2_4: invariant is correct but assert fails (94x faster but quality issue)

### Recommendation
**Run non-reasoning best_of_n=3 to recover quality through sampling.**
The 1.5s gen time means N=3 costs only ~4.5s total, far less than even one reasoning call (avg 47s).
N=3 should recover most of the 6 quality regressions by sampling multiple candidates.
