# Quokka / InvBench 重現報告（DeepSeek V4 Pro）

**最後修訂：** 2026-06-04（§2.1.1：一次 LLM 呼叫只產一個 invariant、針對哪個 loop）

在 Quokka artifact 上將推論後端換成 DeepSeek V4 Pro 並跑通全基準。論文 **gpt-5.2 列僅作文獻對照**（本機未重跑 gpt-5.2，API 成本過高）。

---

## 1. 結果一覽

| 設定 | `#Corr` | `#Ext@30s` | `PAR@30s` | `#Ext@500s` | `PAR@500s` |
|---|---:|---:|---:|---:|---:|
| gpt-5.2（論文參考列） | 710 | 21 | 22.2s | 1 | 105.1s |
| DeepSeek temp=0.2 | 703 | 48 | 11.4s | 3 | 102.0s |
| DeepSeek temp=0.7 | 691 | 59 | 13.1s | 3 | 111.6s |

- **主設定：temp=0.2**（本復現 single-pass 結果）。
- **temp=0.7**：另一次完整 single-pass（較高 `#Ext@30s`、較低 `#Corr`），僅作 temperature 對照。
- 論文列僅參考，**不宣稱勝負**；差異含後端、N、temperature、環境。

補充（`#Slv@T`，temp=0.2 / 0.7）：`#Slv@30s` 676 / 653；`#Slv@500s` 703 / 691。

---

## 2. 原始 Quokka 方法 vs 本次改動

### 2.1 原始流程（artifact，演算法未改）

1. **Prompt**：`prompt.yaml` + 帶行號程式 + 所有迴圈插入點 `{POINTS}`。
2. **LLM**：產生 **一條** `After line X, insert assume(...)`（見 §2.1.1）。
3. **Best-of-N**：N 次獨立 LLM 呼叫，每次仍是一條不變式，各自插入後驗證。
4. **驗證**（UAutomizer）：**assume**（不變式可證）→ **assert**（在假設下原 assertion 可證）。
5. **彙總**：至少一 sample 的 assert=TRUE → 計入 `#Corr`。
6. **指標**：對 `Dataset/timing_uautomizer.json` 用 `print_results.py` 算 `#Corr`、`#Ext@T`、`PAR@T`。

### 2.1.1 一次 LLM 呼叫與哪個 loop

| 問題 | 行為 |
|---|---|
| 一次 LLM 呼叫幾個 invariant？ | **1 個**（prompt 與後處理皆如此） |
| 哪個 loop？ | **模型從候選插入點中自選一個** |
| 多 loop 是否全覆蓋？ | **否**；需靠 N 次抽樣碰運氣 |

**插入點怎麼來：** `baselines/batch_invariant_generation.py` 的 `find_loop_invariant_insertion_points()` 掃描程式中每個 `while` / `for` / `do`，在**迴圈體開頭前一行**各產生一個合法點，由 `create_messages()` 全部寫入 prompt 的 `{POINTS}`，例如：

```
After line 24
After line 37
```

**一次呼叫產什麼：** `baselines/prompt.yaml` 要求 `Choose one of the points` 且 `only output one loop invariant`；回覆格式為單行 `After line X, insert assume(condition);`。`extract_invariants_from_response()` 可解析多條，但 `validate_invariant_insertions()` **只保留第一條**合法者（行號須在 `{POINTS}` 內、condition 不可含賦值）。驗證時 `insert_invariant_into_program()` 只在該行後插入**一條** `assume`；`_generate_llm_invariants_for_file()` 對每個 best-of-N sample 各處理一條。

**不是「每個 loop 各打一 API」：** 單次呼叫只加強**被選到的那一個 loop**；其餘 loop 在該 sample 不插不變式。

**Best-of-N=16：** DeepSeek API 不支援 `n>1`，故為 **16 次獨立 LLM 呼叫**（非 1 次 call 回 16 條）。每次仍是 1 條 invariant；16 個 sample 可能都選同一 loop，也可能分散到不同 loop，**無保證覆蓋所有 loop**。多 loop 程式（如 `egcd2_2.c`）的 `#Corr` 因此也受「是否抽到關鍵 loop」影響——此為 artifact 既有設計，非本次 DeepSeek 復現特有。

### 2.2 本次改動

| 項目 | 論文 artifact（參考） | 本復現 |
|---|---|---|
| 推論後端 | gpt-5.2 等 | **DeepSeek V4 Pro** |
| Best-of-N | 論文列約 N=2 | **N=16**（16 次 n=1 呼叫 + `one_prime_parallel`） |
| Temperature | 論文列約 0.7 | **0.2**（主）、**0.7**（對照 run） |
| Reasoning | OpenAI 預設 | `thinking=disabled` |
| `max_new_tokens` | 約 200 | 未傳 |
| 環境 / verifier | conda 等 | venv；Java 17、OSGi 修正 |
| 程式 | — | `DeepSeekClient`、`--resume`、`--bon_*` 等 |

**N=16：** DeepSeek API 不支援 n>1，故用 16 次獨立請求；配合平行排程後，**單題端到端時間並未隨 N 線性放大**（驗證時間佔比高、取樣可平行）。本復現**不另做 N=2 對照或依 N 加權**。

**gpt-5.2：** 未在本機重跑；下表論文數字僅供對照 artifact 文獻，**不宣稱模型優劣**。

工程細節：`notes/deepseek_reproduction_notes.md`。

---

## 3. 指標定義（精簡）

| 名稱 | 定義 |
|---|---|
| `#Corr` | ≥1 sample 的 assert=TRUE |
| `#Ext@T` | Quokka 在 T 內解出，baseline 在 T 內未解出 |
| `semantic_extension` | baseline `result ≠ TRUE` 但有 assert=TRUE（≠ `#Ext@T`） |

```bash
python baselines/print_results.py <result_dir> --timeouts 30 500 --list-ext
python scripts/analyze_deepseek_results.py <result.json> --timeouts 30 500
```

---

## 4. Testcase 與指標的限制

### 4.1 加速基準，不是「baseline 幾乎做不出來」

| Timeout | Baseline 在時限內解出 | 未解出 |
|---:|---:|---:|
| 30s | 748 | 118 |
| 500s | 863 | **3** |

- `#Ext@30s` 較有鑑別力；`#Ext@500s` **最多 3 題**（見 §5 Case A–C）。

### 4.2 單題／指標限制

| 限制 | 影響 |
|---|---|
| 一次 sample 只插一個 loop | 多 loop 程式靠 N 次抽樣；不保證每 loop 都有不變式 |
| 固定 `assume` 插入格式 | 格式錯 → 無法 extraction |
| UAutomizer 能力 | 非線性、大狀態 → FALSE/TIMEOUT 可能是工具限制 |
| Baseline `FALSE` | 可能是 timeout 分類，非真反例（bresenham） |
| `semantic_extension`（11 題） | 含已知 bug 題；≠ 官方 `#Ext@T` |

清單：`deepseek_full_extensions.md`、`deepseek_full_regressions.md`。

---

## 5. Case Studies

官方 `#Ext@500s=3`（temp=0.2/0.7 皆同）；質性上 **2 題**可當成功（A、B），**1 題**為計數 artifact（C）。

### Case A — `prodbin-ll_valuebound50_1.c`

| | Baseline | DeepSeek |
|---|---|---|
| 時限內 | 500s 未解（541s 才 TRUE） | 248s，assume/assert TRUE |

Shift-add 乘法；迴圈內已有 `__VERIFIER_assert(z + x * y == (long long)a * b)`。DeepSeek 不變式等同將該 assertion 當 `assume`。  
**限制：** 規格已寫在 assertion 上，考的是 **UAutomizer 合成慢**（大狀態），不是 LLM 發現未知性質。

### Case B — `egcd2_2.c`

| | Baseline | DeepSeek |
|---|---|---|
| 時限內 | 515s TRUE | ~6s，Bézout：`a == y*r + x*p`（及配對式） |

**限制：** 需正確代數模板；N=16 時 3 sample 約 2 正 1 錯。同族在 full run 仍常 **regression**（見 `deepseek_full_regressions.md`）。

### Case C — `bresenham-ll_unwindbound10_2.c`（`timeout_reporting_artifact`）

| | Baseline | DeepSeek |
|---|---|---|
| timing 檔 | `FALSE`, ~508s | 頂層 FALSE ~6s |
| 實際 | CEGAR 反覆 `Unsupported non-linear arithmetic`，無反例軌跡 | assume=FALSE；assert=TRUE（在**未證**不變式下） |

與可解變體 `bresenham-ll_valuebound100_1.c` 對照：後者有 **X/Y 界** 與 **迴圈內 assertion**；本題無界 X/Y、無 loop assertion、終點含 `Y*x`/`X*y` 非線性項。

**為何仍進 `#Ext@500s`：** 機械定義（baseline 500s 內未解、DeepSeek E2E≤500）。  
**為何不算質性成功：**

1. Baseline 的 FALSE 是逾時分類，不是真 counterexample。  
2. assert=TRUE 依賴 assume 未通過的不變式 `v == 2*Y*x - 2*X*y + 2*Y - X`。  
3. 只能說「若不變式成立則 assertion 成立」，**不是**對原程式之 sound proof。

### Case D — `semantic_extension`（11 題，≠ `#Ext@T`）

完整檔名：`deepseek_full_extensions.md`。

- **eureka_01-1_1.c**：baseline FALSE @395s，DeepSeek assert=TRUE — 可能程式可證、baseline 找不到關係不變式。  
- **tree_del_iter_incorrect_*.c**（4 題）：已知有 bug；assert=TRUE 不表示修復 reach_error。

### `#Ext@500s` 對照

| | prodbin | egcd2_2 | bresenham |
|---|---:|---:|---:|
| 質性成功 | 是 | 是 | 否 |
| 根因 | 合成慢 | 多變數多項式 | 驗證器非線性限制 |

---

## 6. 重現指令

```bash
source .venv/bin/activate
python baselines/batch_invariant_generation.py \
  --max_workers 16 --model_name deepseek-v4-pro \
  --inference_client deepseek --reasoning_mode off \
  --best_of_n 16 --bon_schedule one_prime_parallel \
  --bon_parallelism 15 --temperature 0.2 \
  --benchmark_dir Dataset/evaluation_all
```

temp=0.7：同上，改 `--temperature 0.7`。  
結果目錄與 SHA：`notes/deepseek_full_reproducibility.md`。
