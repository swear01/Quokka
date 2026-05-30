# Quokka Runtime Semantics

## Key Finding

Quokka's `PAR@T` and speedup metrics are **END-TO-END** — they include both LLM inference time AND verifier time.

## Evidence

### `print_results.py:168-191` — `sample_total_time()`

```python
def sample_total_time(sample):
    generation_time = sample.get("generation_time") or 0.0
    assume_time = sample.get("assume_verification_time") or 0.0
    assert_time = sample.get("assert_verification_time") or 0.0
    verify_time_taken = sample.get("verify_time_taken") or 0.0
    ...
    return generation_time + max(assume_time, assert_time)
```

### `print_results.py:236-268` — `build_correct_results()`

A problem is "solved" iff `assert_verification_result.result == TRUE`.
The solved time = `sample_total_time()` which includes LLM generation time.

### `print_results.py:520-535` — PAR@T computation

```python
solved_time_sum = sum(solved.values())
unsolved_count = total_instances - solved_count
par = (solved_time_sum + unsolved_count * timeout) / total_instances
```

`solved.values()` comes from `build_correct_results()`, whose time is `sample_total_time()`.
**PAR includes LLM generation time.**

### Result JSON fields

| Field | Meaning |
|---|---|
| `generation_time` | LLM API call wall-clock time |
| `assume_verification_time` | UAutomizer assume-phase runtime |
| `assert_verification_time` | UAutomizer assert-phase runtime |
| `verify_time_taken` | max(assume_time, assert_time) |

### Speedup Definitions

```text
verifier-only speedup = baseline_time / max(assume_time, assert_time)
end-to-end speedup    = baseline_time / (generation_time + max(assume_time, assert_time))
PAR@T                  = end-to-end metric (includes LLM time)
#Corr                  = invariant verifier-acceptance (assert=TRUE), no time component
#Slv@T                 = solved within timeout T, uses end-to-end time
#Ext@T                 = solved by Quokka but not by baseline within T
```

## Implications

- For easy baselines (baseline < 15s): LLM time dominates → end-to-end likely slower
- For hard baselines (baseline > 50s): LLM time is small fraction → end-to-end can be faster
- Model latency directly impacts end-to-end speedup
- `#Corr` (verifier acceptance) is independent of generation time
