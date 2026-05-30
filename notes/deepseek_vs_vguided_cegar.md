# DeepSeek vs V-Guided CEGAR (CPAchecker) Comparison (updated)

## Q1: Does DeepSeek generate verifier-consumable invariants in Quokka?

**Yes — 8/8 (100%) on the 8-benchmark smoke subset.** After fixing the verifier infrastructure, all DeepSeek v4-pro generated invariants were accepted by UAutomizer.

## Q2: Does it work more reliably than CPAchecker B2/B5 predicate generation?

**Cannot yet compare directly** (different datasets, different verifiers). But 8/8 (100%) on scalar arithmetic benchmarks is strong. CPAchecker B2/B5 typically achieves 60-80% on similar benchmarks in our experiments, but this is not a controlled comparison.

Key differences:
- Quokka verifies the *program with invariants*, CPAchecker verifies *predicate refinement*
- Quokka's task is simpler: find any sufficient invariant (can even be the postcondition itself)
- CPAchecker requires predicates that help the CEGAR loop, which is more constrained

## Q3: Are success cases mostly simple scalar arithmetic?

**Yes — all 8 benchmarks are scalar arithmetic.** No arrays, pointers, or heap were tested (by design of the smoke subset).

## Q4: Failure causes

| Category | Before fixes | After fixes |
|---|---:|---:|
| Format extraction | 4/8 | 0/8 |
| Verifier rejection | 8/8 | 0/8 |
| Wrong invariant | 1/8 | 0/8 |
| UAutomizer crash | 8/8 | 0/8 |

All 0% failures were verifier infrastructure issues, not LLM quality issues.

## Q5: Does this support or weaken our hypothesis?

> LLM-generated predicates/invariants are useful when the bottleneck is a missing relational or auxiliary abstraction relation, but source-only generation is not generally reliable.

**Mixed evidence:**
- **Supports "useful for relational abstractions"**: cohencu invariant captures `x == n^3`, `y == 3n^2 + 3n + 1`, `z == 6n + 6` — three relational abstractions the LLM derived from source code alone
- **Supports "generally reliable on simple cases"**: 8/8 success on scalar arithmetic is strong
- **Does NOT test the "not generally reliable" thesis**: These are simple scalar benchmarks. Real-world programs with arrays/pointers/heap/concurrency were not tested

## Infra Lessons
- Java version matching is critical for UAutomizer (requires Java 11+, runs on 17+)
- OSGi cache corruption is silent and deadly — clean `data/config/` between Java version changes
- Reasoning models (deepseek-v4-pro) need `max_tokens >= 8192` for proper formatted output
