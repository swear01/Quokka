# DeepSeek Rescue Study — Combined Summary

## Rescued Cases

Temperature=0.7 run on 114 rescue-worthy failed cases from the original full run.

| Metric | Original | Rescue | Combined |
|---:|---:|---:|---|
| Benchmarks | 866 | 114 (non-#Corr only) | 866 |
| **#Corr** | **703** | **51 new** | **754 (87.1%)** |
| First-correct improvements | 638 | 26 (within rescue set) | 664 |
| gpt-5.2 #Corr | 710 | — | **754 > 710 ✓** |

## Newly Rescued Cases (51)

All 51 are baseline=TRUE cases that had zero assert=TRUE in the original temperature=0.2 run, but now have at least one assert=TRUE with temperature=0.7.

Notable rescues:
- `poly1_1.c`: 398s baseline → 6s (67× speedup, uses malloc/arrays)
- `cohencu-ll_valuebound20_7.c`: 145s → 11s (13.6×)
- `hard2_valuebound10_5.c`: 175s → 51s (3.4×)
- `egcd2-ll_unwindbound5_4.c`: 119s → 10s (11.7×)
- `hard-ll_valuebound2_4.c`: 77s → 8s (9.7×)

## Still Failed (63/114)

| Category | Count |
|---:|---|
| Regression (still no assert TRUE) | 41 |
| Correct but slower | 0 |
| Correct no effect | 0 |
| Faster but not solved | 22 |

The remaining 41 regressions are predominantly:
- `cohencu *_9` variants (timeout-heavy, verifier struggles)
- `geo` geometric series variants (invariant quality issues)
- `ps*` power series variants (format/complexity)
- `dijkstra-u` variants (verifier timeouts)

## Rescue Rate by Original Category

| Original Failure | Count | Rescued | Rate |
|---|---:|---:|---|
| too_weak_invariant | 76 | ~30 | ~39% |
| assert_phase_timeout | 25 | ~15 | ~60% |
| assume_phase_timeout | 13 | ~6 | ~46% |

## Key Insight

**Increasing temperature from 0.2 to 0.7 rescues 51/114 (45%) previously failed cases.** The additional diversity from N=16 samples is magnified at higher temperature, finding stronger invariants that the verifier accepts.

The combined #Corr of 754/866 (87.1%) exceeds the paper's best model (gpt-5.2: 710) by 44 cases. However, this uses a targeted rescue pass on previously failed cases, so it is not the same single-pass reproduction setting as the original full run.

## Caveat

```text
This uses an additional targeted rescue pass on failed cases with higher temperature.
It is not a single-pass reproduction.
The combined #Corr should be reported as:
  "With temperature=0.2: 703. After targeted rescue at temperature=0.7: 754."
```
