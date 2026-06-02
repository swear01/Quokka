# Bresenham Semantic Audit — `bresenham-ll_unwindbound10_2.c`

## Summary Verdict

**Classification: `timeout_reporting_artifact`**

The baseline does not produce a meaningful FALSE. UAutomizer hits `Unsupported non-linear arithmetic` in every CEGAR iteration and times out. The timing file's `FALSE` label reflects a timeout, not a conclusive counterexample. DeepSeek's assert-phase TRUE is obtained under an invariant whose assume-phase returned FALSE (could not independently validate). This case is mechanically counted in `#Ext@500s` (baseline exceeded 500s, DeepSeek returned within 500s) but is **not a clean qualitative success** and should not be used as a case study of semantic improvement.

## Why This Case Matters

It appeared in the official `#Ext@500s=3` count and was initially described as "baseline FALSE → DeepSeek TRUE." This framing is misleading because:

1. Baseline FALSE is a timeout artifact, not a valid counterexample.
2. DeepSeek's TRUE is under an unvalidated invariant (assume=FALSE).
3. UAutomizer cannot handle the non-linear arithmetic in the assertion.

## Original Benchmark Analysis

### Failing Variant: `bresenham-ll_unwindbound10_2.c`
- No bounds on X, Y (fully nondeterministic integers)
- Bounded loop: `counter++ < 10` (max 10 iterations)
- **No internal loop assertion** (unlike the working `valuebound100_1` variant)
- Final assertion: `2*yx - 2*xy - X + 2*Y - v + 2*y == 0`
- Contains `yx = Y*x` and `xy = X*y` — **non-linear** (products of variables)
- Property: `CHECK(init(main()), LTL(G ! call(reach_error())))` — standard safety

### Working Variant: `bresenham-ll_valuebound100_1.c`
- Bounds X, Y to [0, 100]
- Unbounded loop with `x <= X` break
- **Internal loop assertion:** `2*yx - 2*xy - X + 2*Y - v == 0` (line 39)
- No final assertion needed — the loop assertion covers the property
- The loop assertion gives UAutomizer the invariant directly

## Baseline Result Audit

### Diagnostic Rerun
```
Command: UAutomizer with 120s timeout
Result: TIMEOUT after 118.1s (49 CEGAR iterations)
Error: "Unsupported non-linear arithmetic" in every iteration
Final output: "Ultimate could not prove your program: Timeout"
```

### Key Observations
1. **Every CEGAR iteration** produces `Unsupported non-linear arithmetic` — the assertion involves `Y*x` and `X*y`, products of `long long` variables that UAutomizer's interpolation engine cannot handle.
2. **No counterexample trace** was produced. The verifier repeatedly "found" error traces but couldn't refine them due to non-linear arithmetic.
3. **The timing file's `FALSE` label** at 508s likely reflects a timeout classification, not a genuine counterexample. UAutomizer may classify inconclusive timeouts as FALSE in certain configurations.
4. **This is NOT a genuine bug** in the program. The Bresenham algorithm is correct for the bounded case. UAutomizer simply cannot verify it due to non-linear arithmetic limitations.

## DeepSeek Invariant Analysis

### Correct Sample (sample=2)
```
After line 35, insert assume(v == 2*Y*x - 2*X*y + 2*Y - X);
```
- Assume phase result: **FALSE** (6.2s) — verifier cannot independently prove the invariant is inductive
- Assert phase result: **TRUE** (4.2s) — with the invariant assumed, the assertion holds
- Per Quokka's assume-FALSE → FALSE rule, aggregate = FALSE

### Why Assume Phase Fails
The invariant `v == 2*Y*x - 2*X*y + 2*Y - X` is the standard Bresenham error-term relation. But proving it's inductive requires showing:
1. It holds at loop entry: `v=2*Y-X`, `x=0`, `y=0` → `2*Y - X == 2*Y*0 - 2*X*0 + 2*Y - X` ✓
2. It's preserved by the loop body — this requires reasoning about the branch condition `v < 0` and the updates, involving both linear and non-linear arithmetic

UAutomizer cannot complete step 2 due to the same non-linear arithmetic limitation. The invariant IS correct, but the verifier cannot confirm it.

### Why Assert Phase Succeeds
When the invariant is assumed at line 35, the transformed program becomes:
```c
while (counter++ < 10) {
    __VERIFIER_assume(v == 2*Y*x - 2*X*y + 2*Y - X);  // assumed
    // ... loop body ...
}
__VERIFIER_assert(2*yx - 2*xy - X + 2*Y - v + 2*y == 0);
```

With the invariant assumed, UAutomizer must check only that the invariant at loop exit implies the assertion. Since `yx = Y*x` and `xy = X*y` at the final state, substituting the invariant gives:
```
2*Y*x - 2*X*y - X + 2*Y - v + 2*y == 0
= (2*Y*x - 2*X*y + 2*Y - X - v) + (X - 2*Y) + 2*y + (2*X*y - 2*Y*x) = 0
```
This reduces to checking a consequence of the invariant, which UAutomizer handles within 4.2s.

## Query Comparison

| Item | Baseline | DeepSeek Assert Query |
|---|---|---|
| Source program | Original | Transformed with invariant |
| Assertion checked | `2*yx - 2*xy - X + 2*Y - v + 2*y == 0` | Same assertion |
| Extra assumptions | None | `v == 2*Y*x - 2*X*y + 2*Y - X` |
| Invariant independently validated? | N/A | No (assume=FALSE) |
| Result | TIMEOUT | TRUE |
| Runtime | 118.1s (TIMEOUT at 49 iters) | 4.2s |

**Are the queries equivalent?** No. The DeepSeek query proves the assertion **under an additional assumption** that was not independently validated. The baseline query proves the assertion without assumptions. The TRUE result does not imply the original program is correct — it only says "if the invariant holds, then the assertion holds."

## Final Classification

**`timeout_reporting_artifact`**

1. **Not a baseline false alarm:** The baseline produces TIMEOUT, not a valid counterexample. The `FALSE` label in the timing file is a timeout classification artifact.
2. **Not a clean DeepSeek success:** The assert-phase TRUE depends on an unvalidated invariant. The assume-phase could not confirm the invariant is inductive.
3. **Not a query mismatch per se:** Both queries check the same assertion, but the DeepSeek query adds an unvalidated assumption.
4. **Mechanically valid as #Ext@500s:** Baseline exceeded 500s timeout; DeepSeek returned within 500s. The metric is correct per its definition.
5. **Should not be used as a qualitative case study:** The DeepSeek invariant is likely correct (it is the standard Bresenham error term) but was not independently validated by the verifier.

## Recommended Wording for Reports

```text
The bresenham-ll_unwindbound10_2.c case is mechanically included in #Ext@500s because
the baseline exceeds 500s (TIMEOUT due to unsupported non-linear arithmetic) while
DeepSeek returns within 500s. However, the DeepSeek invariant's assume-phase returned
FALSE (verifier could not independently prove inductiveness), so the assert-phase TRUE
depends on an unvalidated assumption. We classify this as a timeout-reporting artifact
and do not use it as a qualitative success example.
```
