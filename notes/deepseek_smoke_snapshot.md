# DeepSeek Smoke Test Snapshot (8 cases, best_of_n=1)

## Command
```bash
source .venv/bin/activate
python baselines/batch_invariant_generation.py \
  --max_workers 1 \
  --model_name "deepseek-v4-pro" \
  --inference_client deepseek \
  --best_of_n 1 \
  --temperature 0.2 \
  --benchmark_dir /home/swear01/Quokka/Dataset/evaluation_deepseek_smoke
```
(no `--max_new_tokens` flag → default 8192, no client-side cap)

## Model & Settings
- Model: deepseek-v4-pro (reasoning model)
- best_of_n: 1
- temperature: 0.2
- max_new_tokens: 8192 (default, no client-side cap)
- Verifier: UAutomizer

## Results Table

| Benchmark | Generated Invariant | Assume | Assert | Result | Gen Time |
|---|---:|---:|---:|---:|---:|
| benchmark02_linear_1.c | `l >= 1` | TRUE | TRUE | TRUE | 25.7s |
| benchmark09_conjunctive_1.c | `x == y && x >= 0` | TRUE | TRUE | TRUE | 30.5s |
| benchmark16_conjunctive_1.c | `i >= 1 && 1 <= i + k && i + k <= 2` | TRUE | TRUE | TRUE | 28.9s |
| benchmark25_linear_1.c | `x <= 10` | TRUE | TRUE | TRUE | 44.9s |
| benchmark31_disjunctive_1.c | `x < 0 \|\| y >= 0` | TRUE | TRUE | TRUE | 113.0s |
| benchmark38_conjunctive_1.c | `x == 4 * y && x >= 0` | TRUE | TRUE | TRUE | 25.2s |
| benchmark53_polynomial_1.c | `x * y >= 0` | TRUE | TRUE | TRUE | 33.5s |
| cohencu_1.c | `x == n*n*n && y == 3*n*n + 3*n + 1 && z == 6*n + 6` | TRUE | TRUE | TRUE | 64.9s |

**8/8 (100%) extracted, 8/8 (100%) verifier-accepted.**

## Fixes Required to Reach 8/8
1. Java 17 + `--add-opens` (java.lang, java.util, java.io)
2. OSGi configuration fix — removed corrupted `-Dosgi.configuration.area`
3. No client-side token cap
4. Reasoning model output: fallback `reasoning_content` when `content` is empty

## Result Files
- Results JSON: `baselines/results/deepseek-v4-pro_cot=False_best_of_n=1_num_shots=0_temperature=0.2_verifier=uautomizer_SMOKE_8.json`
