# Case Study: DeepSeek on the 3 Hardest Benchmarks

## Baseline UAutomizer Solvability

UAutomizer fails to solve 3 of 866 benchmarks within 500s:

| Timeout | Solved | Unsolved |
|---:|---:|---:|
| 30s | 748 | 118 |
| 500s | 863 | 3 |

DeepSeek solves all 3 (`#Ext@500s=3` at temp=0.2 and temp=0.7).

---

## Case 1: `prodbin-ll_valuebound50_1.c` — Binary Product

**Baseline:** Not solved at 500s (TRUE at 541s)  
**DeepSeek:** TRUE in 248s (2.2× speedup)

### Program
Shift-add algorithm computing `a × b` (with a,b ≤ 50). Accumulates product in `z` while halving `y` and doubling `x`. The loop body contains an assertion:

```c
while (1) {
    __VERIFIER_assert(z + x * y == (long long)a * b);  // line 38
    if (!(y != 0)) break;
    if (y % 2 == 1) { z = z + x; y = y - 1; }
    x = 2 * x; y = y / 2;
}
```

### DeepSeek Invariant
```
After line 37, insert assume(z + x * y == (long long)a * b);
```

### Why Baseline Struggled
UAutomizer's own invariant synthesis must derive the accumulator relation `z + x*y == a*b` from loop semantics. The state space involves `a,b ≤ 50`, `x,y,z` as `long long`, with multiplication, division, and modulo. UAutomizer takes 541s to find this relation internally.

DeepSeek reads the assertion text at line 38 and proposes it as the invariant directly. With the invariant provided as an assumption, the verifier's task reduces to checking induction (3.5s) and then proving the assertion under the invariant (247.4s).

### Correctness
Sample 1/1: assume=TRUE, assert=TRUE. Single candidate, correct and sufficient.

---

## Case 2: `egcd2_2.c` — Extended Euclidean GCD

**Baseline:** Not solved at 500s (TRUE at 515s)  
**DeepSeek:** TRUE in 6s (88.2× speedup)

### Program
Extended Euclidean algorithm with 10 integer variables and nested loops. Key assertion (line 43):
```c
__VERIFIER_assert(a == y * r + x * p);
```

### DeepSeek Invariant
```
After line 35, insert assume(a == y * r + x * p && b == y * s + x * q);
```

### Why Baseline Struggled
The Bézout identity involves 8 variables in a polynomial relation. UAutomizer uses predicate abstraction and interpolation — discovering this specific multi-variable invariant requires exploring a large space of variable combinations (515s).

DeepSeek recognizes the extended GCD pattern and generates the textbook Bézout invariant directly.

### Candidate Diversity
3 samples: 2 correct, 1 wrong (swapped coefficients). Hit rate: 2/3 at temp=0.2.

---

## Case 3: `bresenham-ll_unwindbound10_2.c` — Bresenham (Timeout Artifact)

**Baseline:** Not solved at 500s (TIMEOUT at ~508s)  
**DeepSeek:** FALSE in 6s (formally counts in `#Ext@500s`)

**⚠️ Classification: `timeout_reporting_artifact`.** Full audit: `notes/deepseek_bresenham_semantic_audit.md`

### Program
Bresenham line-drawing with unbounded X,Y, bounded loop (`counter++ < 10`), and **no internal loop assertion**. The final assertion contains products `Y*x` and `X*y` — non-linear arithmetic.

### What Actually Happened

| Phase | Details |
|---|---|
| **Baseline** | TIMEOUT after 118s (49 CEGAR iterations). Every iteration fails with `Unsupported non-linear arithmetic`. No counterexample trace produced. The `FALSE` label in the timing file is a timeout classification artifact. |
| **DeepSeek assume** | Returns FALSE (6.2s). Verifier cannot independently prove the invariant `v == 2*Y*x - 2*X*y + 2*Y - X` is inductive — same non-linear arithmetic limitation. |
| **DeepSeek assert** | Returns TRUE (4.2s). With the invariant assumed, the assertion reduces to algebraic manipulation that UAutomizer handles quickly. |
| **Aggregate** | FALSE per Quokka's assume-FALSE→FALSE rule. |

### Key Point
The assert-phase TRUE depends on an **unvalidated invariant** (assume=FALSE). The DeepSeek result does not prove the program is correct — it only proves that *if* the invariant holds, *then* the assertion holds. The invariant is likely correct (it is the standard Bresenham error term) but was not independently validated by the verifier.

### Why Counted in #Ext@500s
The metric is mechanical: baseline exceeds 500s, DeepSeek returns within 500s. This case should not be used as a qualitative success example.

---

## Summary

| | prodbin-ll | egcd2_2 | bresenham |
|---|---:|---:|---:|
| Baseline | 541s TRUE | 515s TRUE | 508s TIMEOUT |
| DeepSeek | 248s TRUE | 6s TRUE | 6s FALSE |
| DeepSeek assume | TRUE | TRUE | FALSE |
| DeepSeek assert | TRUE | TRUE | TRUE |
| Qualitative success? | **Yes** | **Yes** | **No** (timeout artifact) |
| Root cause | Large-state synthesis | Multi-var polynomial | Non-linear arithmetic |
