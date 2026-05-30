# DeepSeek Full Run Environment

## Environment
- git commit: 60301cb79ba594945f2049990421f5d5d4d95afc
- Python: 3.10.12
- Java: OpenJDK 17.0.15 (Temurin)
- OS: Linux mazu 6.8.0-60-generic x86_64
- RAM: 125GB

## Configuration
- Model: deepseek-v4-pro
- Reasoning mode: off (extra_body={"thinking": {"type": "disabled"}})
- best_of_n: 16
- schedule: one_prime_parallel
- bon_parallelism: 15
- max_workers: 16
- temperature: 0.2
- max_new_tokens: omitted (None → not sent)
- benchmark_dir: Dataset/evaluation_all
- Verifier: UAutomizer

## Confirmed
- DEEPSEEK_API_KEY: set via .env
- max_tokens: NOT sent when --max_new_tokens omitted
- n>1: NOT sent to DeepSeek (16 separate calls, each n=1)
- Resume: supported via --resume flag + incremental save
- benchmark count: 866
- expected LLM calls: 866 × 16 = 13,856
- peak LLM concurrency: 16 × 15 = 240
