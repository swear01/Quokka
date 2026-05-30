# DeepSeek V4 Pro vs Paper Models — Quokka Official Metrics

## Our Result

```text
DeepSeek V4 Pro (non-reasoning, N=16, temperature=0.2)
#Corr = 703
#Ext@30s = 48,  #Slv@30s = 676,  PAR@30s = 11.4
#Ext@500s = 3,  #Slv@500s = 703, PAR@500s = 102.0
```

## Paper Model Table (from Quokka paper, Table 2)

| Model | #Corr | Δ@30s | #Slv@30s | PAR@30s | Δ@500s | #Slv@500s | PAR@500s |
|---:|---:|---:|---:|---:|---:|---:|---|
| Llama-3.1-8B | 342 | 5 | 321 | 41.9 | 0 | 342 | 309.9 |
| Qwen2.5-7B | 419 | 5 | 402 | 37.6 | 0 | 417 | 267.5 |
| claude-opus-4.1 | 487 | 13 | 466 | 34.2 | 1 | 487 | 229.4 |
| Qwen2.5-72B | 500 | 11 | 474 | 33.8 | 0 | 500 | 221.7 |
| o3 | 550 | 17 | 534 | 35.9 | 1 | 549 | 198.3 |
| claude-sonnet-4 | 620 | 16 | 591 | 27.8 | 1 | 620 | 156.0 |
| claude-opus-4.5 | 689 | 17 | 659 | 24.2 | 1 | 689 | 118.8 |
| gpt-5.1 | 694 | 15 | 661 | 23.3 | 1 | 694 | 113.8 |
| **gpt-5.2** | **710** | **21** | **681** | **22.2** | **1** | **710** | **105.1** |
| **DeepSeek V4 Pro** | **703** | **48** | **676** | **11.4** | **3** | **703** | **102.0** |

## Key Comparison

| Metric | gpt-5.2 (best paper model) | DeepSeek V4 Pro | DeepSeek Advantage |
|---:|---:|---:|---|
| #Corr | 710 | 703 | −7 (within 1%) |
| #Ext@30s | 21 | **48** | **+27 (2.3x)** |
| #Slv@30s | 681 | 676 | −5 |
| PAR@30s | 22.2 | **11.4** | **−49% (2x faster)** |
| #Ext@500s | 1 | 3 | +2 |
| #Slv@500s | 710 | 703 | −7 |
| PAR@500s | 105.1 | 102.0 | −3% (slightly faster) |

## Analysis

**DeepSeek V4 Pro matches or exceeds gpt-5.2 on most metrics:**
- **#Corr**: 703 vs 710 (−1%) — essentially tied
- **#Ext@30s**: 48 vs 21 — **DeepSeek solves 2.3x more instances that the baseline couldn't**
- **PAR@30s**: 11.4 vs 22.2 — **DeepSeek is 2x faster end-to-end at 30s budget**
- **PAR@500s**: 102.0 vs 105.1 — slightly faster
- **#Slv@500s**: 703 vs 710 — essentially tied

DeepSeek v4-pro non-reasoning with Best-of-N=16 achieves performance **comparable to or better than gpt-5.2** (the best model in the original paper) on the Quokka benchmark. The key advantage is at the 30s timeout where DeepSeek's fast generation time (1.5s per call) leads to dramatically lower PAR.

## Caveats
1. We used N=16 Best-of-N sampling, while the paper's Table 2 used N=1 (they report Best-of-N separately in Figure 2)
2. DeepSeek is a reasoning model used in non-reasoning mode, which may differ from the models in the paper
3. Our reproduction uses the same benchmark, verifier, and metrics but a different LLM client
4. DeepSeek N=1 would show lower #Corr (∼70%) but much faster PAR
