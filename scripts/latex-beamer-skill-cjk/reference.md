# Beamer reference — language-neutral templates

## main.tex

```latex
\documentclass[aspectratio=169,11pt]{beamer}
\input{preamble.tex}

\title{Presentation Title}
\subtitle{Optional subtitle}
\author{Author One \and Author Two}
\institute{Affiliation}
\date{2026-06-04}

\begin{document}
\input{slides/01_title.tex}
\input{slides/02_results.tex}
% ...
\end{document}
```

## preamble.tex — English (default block)

```latex
\usepackage{fontspec}
\setmainfont{TeX Gyre Heros}[
  UprightFont = * Regular,
  BoldFont = * Bold,
  ItalicFont = * Italic,
]
\setsansfont{TeX Gyre Heros}

\usepackage{booktabs,amsmath}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,calc}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}

\definecolor{Accent}{HTML}{1B4965}
\definecolor{SeriesA}{HTML}{2E86AB}
\definecolor{SeriesB}{HTML}{E07A2F}

\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{footline}{%
  \hfill\footnotesize\insertframenumber/\inserttotalframenumber\hspace{1em}}

\input{metadata.tex}
```

## preamble.tex — CJK (use when user requests 中文/日文/韓文)

Install fonts without sudo: `bash ~/.cursor/skills/latex-beamer-slides/scripts/install-cjk-fonts-user.sh TC` (or `SC`).

```latex
\usepackage{fontspec}
% User-local Noto OTF (after install-cjk-fonts-user.sh TC):
\newcommand{\CJKFontDir}{/home/USER/.local/share/fonts/noto-sans-cjk-tc/}
\setCJKmainfont{NotoSansCJKtc-Regular}[
  Path=\CJKFontDir,
  Extension=.otf,
  BoldFont=NotoSansCJKtc-Bold,
]
\setsansfont{NotoSansCJKtc-Regular}[
  Path=\CJKFontDir,
  Extension=.otf,
  BoldFont=NotoSansCJKtc-Bold,
]
% SC: noto-sans-cjk-sc/ + NotoSansCJKsc-Regular/Bold

\usepackage{booktabs,amsmath}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,calc}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}

\input{metadata.tex}
```

## metadata.tex

```latex
% Names, version, plot values — no frame text here
\newcommand{\DeckVersion}{v1.0.0}
\newcommand{\MetricA}{32.69}
\newcommand{\MetricB}{48.19}
```

## pgfplots — horizontal bars (xbar)

```latex
\begin{tikzpicture}
\begin{axis}[
  xbar,
  width=11cm,
  height=5cm,
  xmin=0, xmax=60,
  ytick={1,2,3},
  yticklabels={CatA,CatB,CatC},
  xlabel={$|\Delta|$ (\%)},
  legend style={font=\footnotesize},
]
\addplot[fill=SeriesA!80] coordinates {
  (32.5,3) (18.2,2) (41.0,1)
};
\addlegendentry{Series A}
\end{axis}
\end{tikzpicture}
```

## pgfplots — vertical bars (ybar)

```latex
\addplot coordinates {(A,14.8) (B,22.5) (C,32.7) (D,32.7)};
% symbolic x: (LabelMacro,\value) with xticklabels set separately
```

## TikZ — simple pipeline

```latex
\begin{tikzpicture}[
  >=Stealth,
  box/.style={draw=Accent, rounded corners=2pt, minimum height=0.7cm, font=\footnotesize},
]
  \node[box] (a) {Input};
  \node[box, right=1.2cm of a] (b) {Model};
  \node[box, right=1.2cm of b] (c) {Output};
  \draw[->, thick] (a) -- (b) -- (c);
\end{tikzpicture}
```

## Frame with keywords only

```latex
\begin{frame}{Results}
  \centering
  \input{figures/results_bars.tex}
  \vspace{0.5em}
  {\footnotesize baseline RPR · single checkpoint · lower is better\par}
\end{frame}
```

## Speaker notes (`notes.tex` + dual builds)

**Package:** `pgfpages` (required for `show notes on second screen`; do not use `pdfpages`).

`notes.tex` — include from `preamble.tex` after other packages:

```latex
% notes.tex — pick one mode via \NotesMode (set in main.tex or build.sh)
\usepackage{pgfpages}

\providecommand{\NotesMode}{hide} % hide | second | interleave | only

\ifstrequal{\NotesMode}{hide}{%
  \setbeameroption{hide notes}%
}{%
\ifstrequal{\NotesMode}{second}{%
  \setbeameroption{show notes on second screen=right}%
}{%
\ifstrequal{\NotesMode}{interleave}{%
  \setbeameroption{show notes}%
}{%
\ifstrequal{\NotesMode}{only}{%
  \setbeameroption{show only notes}%
}{%
  \setbeameroption{hide notes}%
}}}}}

% Optional: more text, smaller slide preview on notes panel
\setbeamertemplate{note page}{%
  \insertslideintonotes{0.12}%
  \rule{\textwidth}{0.4pt}%
  \scriptsize\insertnote
}
```

`main.tex` (before `\input{preamble}` or at top):

```latex
% Default audience build; override for presenter:
%   NOTES=second ./build.sh
\ifdefined\NotesSecondScreen
  \newcommand{\NotesMode}{second}
\else
  \newcommand{\NotesMode}{hide}
\fi
```

### `\note` in frames

```latex
\begin{frame}{Method}
  \input{figures/pipeline.tex}
  \note{Walk through BL → EL → gate in 30 seconds.}
  \note[item]{Mention MAC budget only if asked.}
\end{frame}
```

- `\note[item]{...}` adds bullet points on the notes page.
- Multiple `\note` inside one frame append to a single notes page for that slide.

### Presenter tools

| Tool | Install | Usage |
|------|---------|--------|
| pdfpc | `pip install pdfpc` or distro package | `pdfpc -d screen deck_presenter.pdf` |
| Pympress | `pip install pympress` | `pympress deck_presenter.pdf` |

Compile presenter PDF with `NotesMode=second`, audience PDF with `hide`.

### `build.sh` with NOTES flag

```bash
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
MODE="${NOTES:-hide}"          # hide | second | interleave | only
OUT="${1:-$DIR/../slides.pdf}"
cd "$DIR"

case "$MODE" in
  second)    EXTRA='\def\NotesSecondScreen{}' ;;
  interleave) EXTRA='\def\NotesInterleave{}' ;;  # wire in main.tex if needed
  only)      EXTRA='\def\NotesOnly{}' ;;
  *)         EXTRA='' ;;
esac

T="${TECTONIC:-$HOME/.local/bin/tectonic}"
if [[ -x "$T" ]]; then
  echo "$EXTRA\input{main.tex}" | "$T" -X compile - --outdir . --print 2>/dev/null \
    || { export TEXINPUTS="$DIR:"; lualatex -interaction=nonstopmode -jobname=main "\documentclass{beamer}\input{main.tex}"; }
fi
# Simpler alternative: two wrapper files main_audience.tex / main_presenter.tex
# that only differ in \NotesMode, then compile both.

cp -f main.pdf "$OUT"
echo "Wrote $OUT (NOTES=$MODE)"
```

**Simpler pattern:** `main_presenter.tex` with `\newcommand{\NotesMode}{second}` and `\input{main_body.tex}` shared content.

### Handout mode (printed slides, no `\note` pages)

```latex
\documentclass[handout]{beamer}
```

Overlays collapse to one slide per frame; speaker notes still controlled by `\setbeameroption`. For article-style handouts, see beamer `beamerarticle` package (separate from presenter notes).

## slides_plan.md (template)

```markdown
# Slide plan

**Language:** English  
**Target duration:** 20 min  
**Deck:** `slides/` → `../MyTalk_slides.pdf`

| # | sec | Title | Figure | Slide keywords | Script § / `\note` |
|---|----:|-------|--------|----------------|------------------|
| 1 | 30 | Title | — | — | intro |
| 2 | 90 | Overview | pipeline.tex | BL · EL · gate | overview |
| … | … | … | … | … | … |

**Total sec:** 1200 (adjust to target)
```

## slides_script.md (template)

Optional authoring file; copy into `\note{...}` when building presenter PDF.

```markdown
## Slide 1 — Title
[Full spoken paragraph…]

## Slide 2 — Results
[Full spoken paragraph…]
```

If notes live only in `.tex`, this file can be omitted.

## build.sh

```bash
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$DIR/../slides.pdf}"
cd "$DIR"
T="${TECTONIC:-$HOME/.local/bin/tectonic}"
if [[ -x "$T" ]]; then
  "$T" -X compile main.tex --outdir . --print
else
  lualatex -interaction=nonstopmode main.tex
  lualatex -interaction=nonstopmode main.tex
fi
cp -f main.pdf "$OUT"
echo "Wrote $OUT"
```

## Slidev mapping

| Slidev | Beamer |
|--------|--------|
| `slides.md` presenter notes / speaker notes | `\note{...}` + `show notes on second screen` |
| `slides.md` body (spoken) | `slides_script.md` and/or `\note` |
| `---` | `slides/NN.tex` |
| Mermaid / PlantUML | TikZ in `figures/` |
| Headmatter `theme:` | `preamble.tex` + beamer theme |
