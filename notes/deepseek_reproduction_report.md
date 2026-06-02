# Reproducing Quokka / InvBench with DeepSeek V4 Pro

**A model-substitution reproduction and comparison with the reported gpt-5.2 row**

---

## 1. Executive Summary

We reproduced the Quokka / InvBench artifact for LLM-based loop invariant synthesis using DeepSeek V4 Pro as the inference backend in place of the original model APIs. The artifact uses UAutomizer to validate LLM-generated loop invariants on 866 benchmarks derived from SV-COMP.

**In this reproduction, the best single-pass DeepSeek setting (non-reasoning, temperature 0.2, N=16) achieves results competitive with the paper-reported gpt-5.2 row under official Quokka metrics:**

| Metric | gpt-5.2 (paper) | DeepSeek temp=0.2 (this reproduction) |
|---|---:|---:|
| `#Corr` | 710 | 703 |
| `#Ext@30s` | 21 | 48 |
| `PAR@30s` | 22.2s | 11.4s |
| `#Ext@500s` | 1 | 3 |
| `PAR@500s` | 105.1s | 102.0s |

DeepSeek is close on `#Corr` (−1%), substantially better on short-timeout metrics (`#Ext@30s`: 48 vs 21, `PAR@30s`: 11.4s vs 22.2s), and roughly tied at the 500s timeout. One of the three `#Ext@500s` cases was later classified as a timeout/reporting artifact (`bresenham`) and is not used as a qualitative success example. Temperature 0.7 is not uniformly better: it improves `#Ext@30s` to 59 but reduces `#Corr` to 691 and worsens PAR. An adaptive two-stage pass (temp=0.2 full run + targeted temp=0.7 rescue on previously failed cases) raises combined `#Corr` to 754/866, but this is not a single-pass comparison.

**This comparison is not model-only.** The paper's gpt-5.2 row appears to use N=2, while our DeepSeek runs use N=16 with cache-aware separate calls and explicit non-reasoning mode. Sampling budget, temperature, and serving behavior all affect the measured outcome.

---

## 2. What Was Reproduced

**Original target:** Quokka / InvBench (Wei et al., 2025/2026), an evaluation-oriented framework for LLM-based loop invariant synthesis. The artifact generates loop invariants with an LLM, inserts them into C programs, and validates them with the UAutomizer verifier. Soundness comes from verifier validation, not from trusting the LLM.

**What we used:**
- The same benchmark suite: `Dataset/evaluation_all`, 866 benchmarks
- The same verification pipeline: UAutomizer with assume/assert queries
- The same official metrics: `print_results.py` computing `#Corr`, `#Ext@T`, `#Slv@T`, `PAR@T`

**What we changed:** Replaced the inference backend with DeepSeek V4 Pro, adapted the environment from conda to Python venv, and added necessary engineering adaptations for compatibility.

---

## 3. How This Reproduction Differs from the Original Artifact

| Aspect | Original paper / artifact | This reproduction |
|---|---|---|
| Model | Reported best row: gpt-5.2 | DeepSeek V4 Pro |
| Best-of-N | gpt-5.2 row appears to use N=2 | N=16 |
| Temperature | gpt-5.2 row appears to use 0.7 | 0.2 and 0.7 (separate runs) |
| Max tokens | gpt-5.2 row appears to use max_new_tokens=200 | Omitted (provider default) |
| Reasoning mode | Default OpenAI client behavior | Explicit non-reasoning (`thinking=disabled`) |
| API `n` parameter | Original OpenAI client setting | DeepSeek rejects `n>1`; we use separate `n=1` calls |
| Serving / cache | Original artifact behavior | Separate calls with observed provider prompt cache |
| Verifier | UAutomizer | Same verifier, with Java 17/OSGi fixes |
| Environment | conda / original dependencies | Python venv / lazy imports |

Because these settings differ, **this is not a pure model-only comparison.** It is a reproduction using the Quokka artifact with DeepSeek substituted as the inference backend, with settings adapted to DeepSeek's API behavior.

---

## 4. Engineering Adaptations

The following adaptations were required to run the artifact with DeepSeek V4 Pro.

### 4.1 DeepSeek API Client (`baselines/inference.py`)

Added `DeepSeekClient` using OpenAI-compatible endpoint (`https://api.deepseek.com`):
- Reads `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL` from environment
- Supports non-reasoning mode via `extra_body={"thinking": {"type": "disabled"}}`
- Does not send `max_tokens` unless `--max_new_tokens` is explicitly passed
- Logs generation time, token usage, and cache hit/miss per call

### 4.2 Best-of-N via Separate Calls

DeepSeek does not support request-side `n>1`. Our API probe returned:
```
400: Invalid n value (currently only n = 1 is supported)
```
Therefore `best_of_n=16` is implemented as 16 separate `n=1` API calls. A one-prime-parallel schedule is used: sample 1 runs sequentially (cold call), samples 2–16 run in parallel. This is an implementation adaptation for DeepSeek's API limitation, not an algorithmic contribution.

### 4.3 Environment and Verifier Fixes

- Python venv instead of conda; heavy ML imports (torch, sglang, transformers) made lazy
- Java 17 compatibility (`--add-opens java.base/java.lang=ALL-UNNAMED`)
- UAutomizer OSGi cache fix (removed corrupted `-Dosgi.configuration.area`)
- `.env` for API key (gitignored)

### 4.4 Analysis Script (`scripts/analyze_deepseek_results.py`)

Added a reusable analysis script that computes audited helper metrics and explicitly labels raw E2E faster as misleading. It outputs table, CSV, or JSON.

### 4.5 Pipeline Arguments (`baselines/batch_invariant_generation.py`)

Added `--benchmark_dir`, `--reasoning_mode`, `--bon_schedule`, `--bon_parallelism`, `--output_dir`, `--resume`. Changed `--max_new_tokens` default to `None`.

---

## 5. Metrics

**Official Quokka metrics** (from `print_results.py`):

| Metric | Definition |
|---|---|
| `#Corr` | Benchmarks with ≥1 verifier-confirmed invariant (assert=TRUE) |
| `#Ext@T` | Benchmarks solved by Quokka within timeout T that the baseline does not solve within the same timeout T |
| `#Slv@T` | Benchmarks solved by Quokka within timeout T |
| `PAR@T` | Penalized average runtime under timeout T (includes LLM generation time) |

**Audited helper metrics** (from our analysis script):

| Metric | Definition |
|---|---|
| First-correct real improvement | First assert=TRUE sample has E2E time < 95% baseline |
| Fastest-correct real improvement | At least one assert=TRUE sample with E2E faster than baseline |
| Raw E2E faster | DeepSeek path faster regardless of correctness. **Misleading, not improvement.** |

---

## 6. Single-Pass Official Results

| Setting | `#Corr` | `#Ext@30s` | `PAR@30s` | `#Ext@500s` | `PAR@500s` |
|---|---:|---:|---:|---:|---:|
| gpt-5.2 (paper best) | 710 | 21 | 22.2s | 1 | 105.1s |
| DeepSeek temp=0.2 | 703 | 48 | 11.4s | 3 | 102.0s |
| DeepSeek temp=0.7 | 691 | 59 | 13.1s | 3 | 111.6s |

**Interpretation:**

- **temp=0.2 is the best single-pass DeepSeek setting.** It nearly matches gpt-5.2 on `#Corr` (703 vs 710, −1%) and substantially improves short-timeout metrics (`#Ext@30s`: 48 vs 21, `PAR@30s`: 11.4s vs 22.2s). At the 500s timeout, the two settings are roughly tied.
- **temp=0.7 is not uniformly better.** It achieves the highest `#Ext@30s` (59) but has lower `#Corr` (691) and worse PAR than temp=0.2.
- The comparison is not model-only. Sampling budget (N=16 vs N=2), temperature, non-reasoning mode, and serving behavior all differ.

---

## 7. Adaptive Two-Stage Result

This result is separate from the single-pass official rows.

| Setting | `#Corr` | Notes |
|---|---:|---|
| DeepSeek temp=0.2 single-pass | 703/866 | Main single-pass reproduction setting |
| DeepSeek temp=0.2 + targeted temp=0.7 rescue | 754/866 | Adaptive two-stage; not directly comparable to paper single-pass rows |
| gpt-5.2 (paper best) | 710/866 | Paper-reported single-pass row |

**Method:** The temp=0.2 run had 163 non-`#Corr` cases. Of these, 114 were baseline-TRUE and considered rescue-worthy (the remaining 49 were excluded because their baseline status was FALSE or otherwise unsuitable for straightforward rescue; these require separate semantic inspection). Running temp=0.7 on those 114 cases rescued 51. Combined `#Corr` = 703 + 51 = 754/866.

**This exceeds gpt-5.2's `#Corr` by 44 cases, but it is an adaptive two-stage result and should not be compared with the paper's single-pass rows.** Official PAR/Ext metrics for the two-stage approach would need to account for the cost of the rescue pass.

---

## 8. Temperature Analysis

Temperature is not monotonic in this reproduction:

| Metric | temp=0.2 | temp=0.7 | Delta |
|---:|---:|---:|---|
| `#Corr` | 703 | 691 | −12 |
| `#Ext@30s` | 48 | 59 | +11 |
| `PAR@30s` | 11.4s | 13.1s | +1.7s |
| `PAR@500s` | 102.0s | 111.6s | +9.6s |

Higher temperature increases sample diversity, which can find stronger invariants (more `#Ext@30s`) but also generates more wrong or unusable invariants (lower `#Corr`, higher PAR). temp=0.2 is the best single-pass setting for correctness. temp=0.7 is useful as a targeted rescue distribution for cases that temp=0.2 could not solve.

---

## 9. Comparison with Baseline UAutomizer

Using official metrics (temp=0.2):

- `#Ext@30s = 48`: DeepSeek solves 48 benchmarks at 30s that the baseline does not solve at 30s.
- `#Ext@500s = 3` under the official script. Qualitatively, two of the three are clean timeout-budget speedups (`prodbin-ll_valuebound50_1.c`, `egcd2_2.c`), while the third (`bresenham-ll_unwindbound10_2.c`) is a timeout/reporting artifact caused by unsupported non-linear arithmetic in UAutomizer and an unvalidated DeepSeek invariant. Therefore, only two should be used as clean qualitative case studies.

Using temp=0.7:

- `#Ext@30s = 59`
- `#Ext@500s = 3`

Note: `#Ext@T` is the official timeout-dependent extension metric reported by `print_results.py`. Our audited "extensions" category (11 cases) is a separate classification based on benchmark-level baseline result changes and should not be used for official comparison.

---

## 10. Audited Metrics and Raw Faster Warning

The following audited metrics are from our analysis script applied to the temp=0.2 full run:

| Metric | Value |
|---|---|
| `#Corr` | 703/866 (81.2%) |
| First-correct real improvements | 638/866 (73.7%) |
| Fastest-correct real improvements | 658/866 (76.0%) |
| Extensions (audited) | 11 |
| Regressions | 48 |
| Faster but not solved | 95 |
| Correct but slower | 32 |
| Raw E2E faster | 753/866 (86.9%) |

**Raw E2E faster (753) is not improvement.** The gap between 753 and 638 is 115 cases — benchmarks where DeepSeek was faster than baseline but the invariant was not verifier-confirmed. These fast rejections must not be counted as success. Our analysis script explicitly prevents this mistake.

---

## 11. Extensions and Regressions

The full extension and regression lists are reported in `notes/deepseek_full_extensions.md` and `notes/deepseek_full_regressions.md`. In brief:

- **11 extensions:** Benchmarks where the baseline did not solve but DeepSeek found a verifier-confirmed invariant. Cases involving baseline-FALSE require separate semantic inspection — an invariant accepted on a FALSE-baseline program may prove a different property than the original assertion.
- **48 regressions:** Benchmarks where the baseline solved but all DeepSeek invariants were rejected. These cluster in specific families (Cohen cube `*_9` variants, extended GCD variants, power-series variants).

### Bresenham Semantic Audit

The `bresenham-ll_unwindbound10_2.c` case was audited separately because it showed a baseline FALSE vs DeepSeek assert-TRUE discrepancy, and because it is one of only three `#Ext@500s` cases. The full audit is at `notes/deepseek_bresenham_semantic_audit.md`.

**Key findings:**
1. The baseline `FALSE` label was caused by repeated `Unsupported non-linear arithmetic` failures in UAutomizer's CEGAR loop, not by a genuine counterexample. The verifier timed out after 49 iterations.
2. The DeepSeek assert query (`assume(v == 2*Y*x - 2*X*y + 2*Y - X)`) returned TRUE, but the corresponding assume query returned FALSE — the verifier could not independently prove the invariant is inductive (same non-linear arithmetic limitation).
3. An assert TRUE under an unvalidated assumption does not constitute a sound proof.
4. **Classification:** `timeout/reporting artifact`. The case is mechanically counted in official `#Ext@500s` but is not used as a qualitative success example.

---

## 12. Relation to CPAchecker / CEGAR Work

Our earlier CPAchecker / CEGAR experiments motivated this reproduction because they suggested that LLM predicates are highly integration-dependent. In CPAchecker, the benefit was limited to selected relational bottlenecks — the CEGAR integration constrained how effectively the LLM signal could be used.

This Quokka reproduction provides a complementary data point: when the pipeline is designed to directly validate standalone LLM proposals without complex post-processing, the same underlying model capability translates into broad, measurable improvement (81% `#Corr`, 74% real E2E improvement). The reproduction supports the broader hypothesis that LLMs can generate useful semantic hypotheses when the formal pipeline can validate and consume them directly.

---

## 13. Limitations and Threats to Direct Comparability

1. **Sampling budget:** DeepSeek uses N=16; gpt-5.2 row appears to use N=2. More samples increase the chance of finding good invariants.
2. **Non-reasoning mode:** DeepSeek uses explicit thinking-disabled mode; the gpt-5.2 row uses default OpenAI client behavior (the exact mode is not documented in the paper's default configuration).
3. **Serving behavior:** DeepSeek prompt cache and parallel separate calls affect runtime (PAR). These differ from the original artifact's serving setup.
4. **Temperature:** We tested both 0.2 and 0.7. The best setting depends on which metric is prioritized.
5. **Adaptive rescue:** The two-stage 754 `#Corr` is not a single-pass result.
6. **API variance:** Provider behavior may change over time. Exact `#Corr` may vary on re-run due to LLM nondeterminism.
7. **No matched comparison:** We did not run DeepSeek N=2 with the paper's exact parameters.
8. **Verifier fixes:** Java/OSGi changes may affect verifier behavior compared with the paper's original environment.

---

## 14. Reproducibility

### temp=0.2 full run

```bash
source .venv/bin/activate
python baselines/batch_invariant_generation.py \
  --max_workers 16 \
  --model_name deepseek-v4-pro \
  --inference_client deepseek \
  --reasoning_mode off \
  --best_of_n 16 \
  --bon_schedule one_prime_parallel \
  --bon_parallelism 15 \
  --temperature 0.2 \
  --benchmark_dir Dataset/evaluation_all
```

### temp=0.7 full run

```bash
source .venv/bin/activate
python baselines/batch_invariant_generation.py \
  --max_workers 16 \
  --model_name deepseek-v4-pro \
  --inference_client deepseek \
  --reasoning_mode off \
  --best_of_n 16 \
  --bon_schedule one_prime_parallel \
  --bon_parallelism 15 \
  --temperature 0.7 \
  --benchmark_dir Dataset/evaluation_all
```

**Common settings:** No `--max_new_tokens` was passed. API key read from `.env` (gitignored).

**Environment:** Git commit `60301cb`, Python 3.10.12 (venv), Java OpenJDK 17.0.15, Ubuntu 22.04, 125GB RAM.

**Result directories:**
- temp=0.2: `baselines/results/deepseek_v4pro_nonreasoning_n16_full_20260530_015014/`
- temp=0.7: `baselines/results/deepseek_v4pro_nonreasoning_n16_temp07_full_20260530_211946/`

**Analysis:** `scripts/analyze_deepseek_results.py`
**Official metrics:** `python baselines/print_results.py <result_dir> --timeouts 30 500`

---

## 15. Conclusion

This reproduction shows that replacing the Quokka / InvBench inference backend with DeepSeek V4 Pro produces results competitive with the paper-reported gpt-5.2 row under official Quokka metrics. The best single-pass DeepSeek setting, temperature 0.2 with non-reasoning N=16, achieves `#Corr=703/866`, close to gpt-5.2's `710/866`, while improving short-timeout metrics (`#Ext@30s=48` vs 21, `PAR@30s=11.4s` vs 22.2s). Temperature 0.7 is not uniformly better: it improves `#Ext@30s` but reduces `#Corr` and worsens PAR. A targeted temp=0.7 rescue pass can raise combined `#Corr` to `754/866`, but this is an adaptive two-stage result and should not be compared directly with paper single-pass rows. The qualitative interpretation of `#Ext@500s=3` is more conservative than the raw number suggests: two cases are clean timeout-budget speedups, while one (`bresenham`) is a timeout/reporting artifact caused by verifier non-linear arithmetic limitations.

Overall, this reproduction supports the original paper's conclusion that verifier-validated LLM invariants can improve software verification, while highlighting that model choice, sampling budget, and serving behavior materially affect the measured outcome. These results should be interpreted as a reproduction under a different inference backend and serving configuration, not as a pure model-only comparison.
