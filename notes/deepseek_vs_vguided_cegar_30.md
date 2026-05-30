# DeepSeek Quokka vs CPAchecker CEGAR — 30-Case Comparison

## Q1: Does DeepSeek in Quokka show broader usefulness than in our CPAchecker prototype?

**Yes, but only on slow-baseline benchmarks.** 4/30 (13%) showed end-to-end speedup including LLM cost, with up to 7.12x improvement. On easy baselines (<15s), LLM time dominates and makes end-to-end worse. This is a selection problem, not a quality problem.

CPAchecker B5 had 2/6 (33%) targeted improvement, but on a much smaller, deliberately-chosen hard subset.

## Q2: Are successful Quokka cases mostly scalar arithmetic / accumulator cases?

**Yes — all 30 are scalar.** DeepSeek v4-pro consistently produces correct invariants for:
- Linear relations: `i == k`, `x == y`, `j == 2*i`
- Accumulators: `c >= 0 && i >= 0`, `z + x*y == a*b`
- Disjunctive: `x > 0 || y > 0`
- Polynomial: `x * y >= 0`
- Complex arithmetic: `4*(A+r) == u*u - v*v - 2*u + 2*v`

This is encouraging but doesn't test the "relational abstraction" hypothesis yet.

## Q3: Are failures due to model output, verifier rejection, or benchmark issues?

| Cause | Count |
|---|---:|
| Model output (format) | 1/30 (3%) |
| Verifier timeout | 4/30 (13%) |
| Invariant too weak | 1/30 (3%) |
| **Baseline already solved** | **29/30 (97%)** |

The dominant "failure" is: **these benchmarks don't need invariants**.

## Q4: Does Quokka's standalone invariant insertion appear easier or harder than CPAchecker precision injection?

**Easier.** Quokka's task (find any sufficient invariant) is less constrained than CPAchecker's (find predicates that guide the CEGAR loop). DeepSeek's 87% acceptance rate reflects this.

But Quokka's value proposition is different — it's about accelerating verification, not solving harder problems. The invariant must reduce verification time, not just exist.

## Q5: Is Best-of-N likely necessary?

**Likely yes for harder benchmarks.** best_of_n=3 could help with:
- benchmark24 (format failure): one of 3 samples might format correctly
- diamond_1-1_1 (timeout): different invariant might be simpler to verify

But for format-only failures, it's also worth considering:
- Increase max_tokens for complex benchmarks
- Add a retry if format parsing fails

## Q6: Should we continue Quokka reproduction or return to CPAchecker?

**Recommendation: Test Quokka on truly hard subset before deciding.**

Next steps:
1. Select 20-30 benchmarks where UAutomizer baseline is UNKNOWN or high-runtime TIMEOUT
2. Run same DeepSeek v4-pro best_of_n=1 on that subset
3. Compare: does Quokka solve previously-unsolved cases?
4. If yes → scale up. If no → return to CPAchecker.

Quokka's infrastructure is solid and DeepSeek integration works perfectly. But 0% improvement on baseline-solved benchmarks tells us nothing useful.
