# DeepSeek V4 Pro — Final Metric Comparison vs Paper gpt-5.2

## Single-Pass Official Quokka Metrics

| Metric | gpt-5.2 (paper) | DeepSeek temp=0.2 | DeepSeek temp=0.7 |
|---:|---:|---:|---|
| `#Corr` | **710** | 703 | 691 |
| `#Ext@30s` | 21 | 48 | **59** |
| `#Slv@30s` | 681 | 676 | 653 |
| `PAR@30s` | 22.2s | **11.4s** | 13.1s |
| `#Ext@500s` | 1 | 3 | 3 |
| `#Slv@500s` | 710 | 703 | 691 |
| `PAR@500s` | 105.1s | **102.0s** | 111.6s |

## Verdict

| Metric | temp=0.2 vs gpt-5.2 | temp=0.7 vs gpt-5.2 |
|---|---|---|
| #Corr | −7 (tied) | −19 (lose) |
| #Ext@30s | **+27 (win)** | **+38 (win)** |
| PAR@30s | **−49% (win)** | **−41% (win)** |
| #Ext@500s | +2 (win) | +2 (win) |
| PAR@500s | −3% (tied) | +6% (lose) |

**temp=0.2 is the best single-pass configuration for #Corr.** temp=0.7 gives more extra-solved cases at 30s but with lower overall #Corr.

## Adaptive Two-Stage (Separate)

A targeted temp=0.7 rescue pass on 114 baseline-TRUE cases that temp=0.2 failed recovered **51** additional correct invariants, bringing combined #Corr to **754/866 (87.1%)**, exceeding gpt-5.2 by 44. This is a two-pass result, not a single-pass.

## Summary Table

| Setting | #Corr | #Ext@30s | PAR@30s | #Ext@500s | PAR@500s |
|---:|---:|---:|---:|---:|---|
| gpt-5.2 paper | 710 | 21 | 22.2s | 1 | 105.1s |
| DeepSeek temp=0.2 | 703 | 48 | 11.4s | 3 | 102.0s |
| DeepSeek temp=0.7 | 691 | 59 | 13.1s | 3 | 111.6s |
| DeepSeek adaptive (0.2+0.7) | 754 | — | — | — | — |
