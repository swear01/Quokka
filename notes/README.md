# DeepSeek 復現 — 文件

## 報告

**[`deepseek_reproduction_report.md`](deepseek_reproduction_report.md)** — 方法、改動、結果、testcase 限制、case studies、重現指令。

**口頭簡報（約 5 分鐘，Beamer）**：[`deepseek-reproduction-beamer/slides/`](deepseek-reproduction-beamer/slides/) — 投影片與 `\note{}` 講稿同一套 TeX，`./build.sh` 出 PDF

## 附錄清單

| 檔案 | 內容 |
|---|---|
| [`deepseek_full_extensions.md`](deepseek_full_extensions.md) | 11 題 semantic_extension |
| [`deepseek_full_regressions.md`](deepseek_full_regressions.md) | 48 題 regression |

## 工程

| 檔案 | 內容 |
|---|---|
| [`deepseek_full_reproducibility.md`](deepseek_full_reproducibility.md) | 指令、SHA、環境 |
| [`deepseek_reproduction_notes.md`](deepseek_reproduction_notes.md) | 程式修改日誌 |
| `deepseek_subset_30.md` / `deepseek_hard30_selection.md` / `smoke_snapshot.md` / `n3_probe.md` | 子集實驗 |

## 分析

```bash
python baselines/print_results.py <result_dir> --timeouts 30 500 --list-ext
python scripts/analyze_deepseek_results.py <result.json> --timeouts 30 500
```
