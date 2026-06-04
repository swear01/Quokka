# DeepSeek 復現 — Beamer 簡報（約 5 分鐘）

投影片與**演講者備忘**在同一套 `slides/` 內（每頁 `\note{...}`）。

## 編譯

```bash
cd /home/swear01/Quokka/notes/deepseek-reproduction-beamer/slides
chmod +x build.sh
./build.sh
# → ../deepseek-reproduction-slides.pdf
```

需 Tectonic 或 LuaLaTeX。`build.sh` 會自動處理字型：

1. 若已有 `~/.local/share/fonts/noto-sans-cjk-tc/*.otf` → 直接用
2. 否則從系統 `NotoSansCJK-*.ttc` 擷取 TC（`../scripts/extract-noto-cjk-tc-from-ttc.py`，需 `fonttools`）
3. 再不行才 `curl` 下載（`latex-beamer-slides` 的 `install-cjk-fonts-user.sh TC`）

`main.tex` 使用 `fontset=none` + **Noto Sans CJK TC** OTF；TikZ/pgfplots 經 `\TikzCJKFont` 同一字型。

### 繁中字型（無 sudo，手動）

```bash
bash ~/.cursor/skills/latex-beamer-slides/scripts/install-cjk-fonts-user.sh TC
# 或
python3 ../scripts/extract-noto-cjk-tc-from-ttc.py
cd slides && ./build.sh
```

## 看備忘稿

- **PDF 編輯器**：部分可顯示 Beamer notes 註解層
- **放映雙螢幕**：在 `preamble.tex` 取消註解 `\setbeameroption{show notes on second screen=right}` 後重編

## 結構

```
slides/
├── main.tex
├── metadata.tex      # 數字
├── preamble.tex
├── figures/
└── slides/01–07 + 02b.tex  # 8 頁投影片 + \note{講稿}
```

文字報告：`../deepseek_reproduction_report.md`
