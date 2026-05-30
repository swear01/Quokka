# DeepSeek V4 Pro Benchmark Results (final, no token limit)

## Setup
- Model: deepseek-v4-pro (reasoning model)
- Client: DeepSeek via OpenAI-compatible API
- max_new_tokens: default 8192 (no limit imposed)
- best_of_n: 1, temperature: 0.2
- Verifier: UAutomizer (fixed: Java 17, --add-opens, no corrupted OSGi cache)

## Results

| # | Benchmark | DeepSeek invariant | Assume | Assert | Accepted | Gen time | GT match? |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | benchmark02 | `l >= 1` | TRUE | TRUE | **YES** | 25.7s | Close (GT: `0 < l`) |
| 2 | benchmark09 | `x == y && x >= 0` | TRUE | TRUE | **YES** | 30.5s | Different structure |
| 3 | benchmark16 | `i >= 1 && 1 <= i + k && i + k <= 2` | TRUE | TRUE | **YES** | 28.9s | Exact |
| 4 | benchmark25 | `x <= 10` | TRUE | TRUE | **YES** | 44.9s | Exact |
| 5 | benchmark31 | `x < 0 \|\| y >= 0` | TRUE | TRUE | **YES** | 113.0s | Similar shape |
| 6 | benchmark38 | `x == 4 * y && x >= 0` | TRUE | TRUE | **YES** | 25.2s | Different (stronger) |
| 7 | benchmark53 | `x * y >= 0` | TRUE | TRUE | **YES** | 33.5s | Core property |
| 8 | cohencu | `x == n*n*n && y == 3*n*n + 3*n + 1 && z == 6*n + 6` | TRUE | TRUE | **YES** | 64.9s | More detailed than GT |

## Aggregate

| Metric | Value |
|---:|---|
| Invariants extracted | 8/8 (100%) |
| Correctly formatted | 8/8 (100%) |
| Verifier-accepted | **8/8 (100%)** |
| Avg gen time | 45.8s |

## Fixes Applied

1. **Java 17**: System Java 8 rejected by UAutomizer OSGi bundles requiring JavaSE/11. Found Java 17 in /tmp/, added `get_java()` version detection preferring highest version.
2. **--add-opens**: Java 9+ module system blocks OSGi plugin loading. Added `--add-opens java.base/java.lang=ALL-UNNAMED` (and java.util, java.io).
3. **-Dosgi.configuration.area**: Corrupted cache from failed Java 8 runs poisoned subsequent attempts. Removed this JVM flag from `Ultimate.py`.
4. **No token limit**: Removed auto-raise logic. Default 8192 max_tokens gives reasoning model room for chain-of-thought + formatted answer.
