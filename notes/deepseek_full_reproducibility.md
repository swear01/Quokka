# DeepSeek Full Run — Reproducibility

## Command
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
  --benchmark_dir Dataset/evaluation_all \
  --output_dir baselines/results/deepseek_v4pro_nonreasoning_n16_full_20260530_015014
```

No `--max_new_tokens` — omitted entirely, DeepSeek receives no max_tokens limit.

## Environment
- git commit: 60301cb79ba594945f2049990421f5d5d4d95afc
- Python: 3.10.12 (venv at .venv/)
- Java: OpenJDK 17.0.15 (Temurin, cached at /tmp/jdk-17.0.15+6/)
- OS: Linux mazu 6.8.0-60-generic x86_64 (Ubuntu 22.04)
- RAM: 125GB

## Configuration
- Model: deepseek-v4-pro
- Reasoning mode: off (extra_body={"thinking": {"type": "disabled"}})
- best_of_n: 16 (16 separate API calls, each n=1)
- schedule: one_prime_parallel
- bon_parallelism: 15
- max_workers: 16
- temperature: 0.2
- max_new_tokens: omitted (not sent to DeepSeek)
- Verifier: UAutomizer (SV-COMP 2023)
- Spec: unreach-call.prp

## Result
- Directory: baselines/results/deepseek_v4pro_nonreasoning_n16_full_20260530_015014/
- File: deepseek-v4-pro_cot=False_best_of_n=16_num_shots=0_temperature=0.2_verifier=uautomizer_invariant_generation_results.json
- SHA256: 9c24537ab6216dfd0af7497e6f4dd6c17009574d41171884f472727ab8409926

## Analysis
- Script: scripts/analyze_deepseek_results.py
- 866 benchmarks processed
- 703/866 #Corr
- 638/866 first-correct real improvements
- 11 extensions

## Infra Fixes Applied
1. Java 17 found in /tmp/, symlinked to tools/jvm/bin/java
2. `get_java()` modified to find highest available Java version
3. `--add-opens java.base/java.lang=ALL-UNNAMED` added for Java 17 module system
4. `-Dosgi.configuration.area` removed from Ultimate.py (corrupted cache)
5. `-Xmx15G` → `-Xmx4G` (15G excessive)
6. Incremental save + --resume flag for crash recovery
7. Cache-aware one-prime-parallel scheduling
8. reasoning_content → content fallback for reasoning models
9. All provider SDK imports made lazy (no conda, no torch, no sglang needed)
