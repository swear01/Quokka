# Reproducing Quokka / InvBench with DeepSeek V4 Pro — Short Report

## What We Did

We reproduced the Quokka / InvBench artifact for LLM-based loop invariant synthesis using DeepSeek V4 Pro as the inference backend. The artifact validates LLM-generated invariants with UAutomizer on 866 benchmarks. We replaced the original model APIs with DeepSeek, adapted the environment from conda to Python venv, and added necessary compatibility fixes.

## How Our Setting Differs

| Aspect | gpt-5.2 (paper) | DeepSeek (this reproduction) |
|---|---|---|
| Model | gpt-5.2 | DeepSeek V4 Pro |
| Best-of-N | N=2 | N=16 |
| Temperature | 0.7 | 0.2 and 0.7 |
| Max tokens | max_new_tokens=200 | Omitted |
| Reasoning | Default client | Explicit non-reasoning |
| API `n` | n=2 | Separate n=1 calls (DeepSeek rejects n>1) |

## Single-Pass Official Results

| Setting | `#Corr` | `#Ext@30s` | `PAR@30s` | `#Ext@500s` | `PAR@500s` |
|---|---:|---:|---:|---:|---:|
| gpt-5.2 (paper) | 710 | 21 | 22.2s | 1 | 105.1s |
| DeepSeek temp=0.2 | 703 | 48 | 11.4s | 3 | 102.0s |
| DeepSeek temp=0.7 | 691 | 59 | 13.1s | 3 | 111.6s |

**temp=0.2 is the best single-pass setting.** It nearly matches gpt-5.2 on `#Corr` (−1%) and is substantially better on short-timeout metrics. temp=0.7 has higher `#Ext@30s` but lower `#Corr` and worse PAR. Temperature is not monotonic.

## Adaptive Two-Stage

| Setting | `#Corr` |
|---|---:|
| DeepSeek temp=0.2 single-pass | 703/866 |
| + targeted temp=0.7 rescue on failed cases | **754/866** |
| gpt-5.2 (paper) | 710/866 |

A temp=0.7 pass on 114 previously-failed baseline-TRUE cases rescued 51. Combined `#Corr` = 754, exceeding gpt-5.2 by 44. **This is an adaptive two-stage result, not a single-pass comparison.**

## Audited Metrics (temp=0.2)

| Metric | Value |
|---|---|
| First-correct real improvements | 638/866 (74%) |
| Extensions (audited) | 11 |
| Regressions | 48 |
| Raw E2E faster (misleading) | 753/866 |

**Raw faster ≠ improvement.** 115 cases are fast rejections, not real wins.

## Key Points

- This is **not a pure model-only comparison** — settings differ in N, temperature, and serving.
- DeepSeek is **competitive** with gpt-5.2, with stronger short-timeout performance.
- The reproduction supports the original paper's conclusion while showing that sampling and serving decisions matter.
- Exact commands, result directories, and analysis scripts are documented in the full report.

## Reproducibility

```bash
source .venv/bin/activate
python baselines/batch_invariant_generation.py \
  --max_workers 16 --model_name deepseek-v4-pro \
  --inference_client deepseek --reasoning_mode off \
  --best_of_n 16 --bon_schedule one_prime_parallel \
  --bon_parallelism 15 --temperature 0.2 \
  --benchmark_dir Dataset/evaluation_all
```

No `--max_new_tokens`. API key from `.env`. Analysis: `scripts/analyze_deepseek_results.py`.

Full report: `notes/deepseek_reproduction_report.md`
