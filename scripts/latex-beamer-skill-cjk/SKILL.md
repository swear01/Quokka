---
name: latex-beamer-slides
description: >-
  Create and compile Beamer slide decks to PDF with TikZ/pgfplots diagrams,
  keywords-only slides, and speaker notes via \\note or slides_script.md.
  Supports hide/show notes, dual-screen PDF (pgfpages), and presenters like
  pdfpc/Pympress. Use for LaTeX/Beamer in any language or duration.
---

# LaTeX Beamer Slides (PDF)

## Slidev vs Beamer

| Need | Use |
|------|-----|
| Live demo, Vue, `v-click`, PPTX export, browser presenter | **Slidev** (`slidev` skill) |
| **PDF**, TikZ/pgfplots flowcharts, stable print layout, no Node | **Beamer** (this skill) |

Do not mix both in one deck unless the user asks.

## Core principles (always)

1. **Slides = diagrams + keywords** — charts, flowcharts, tables; at most a few short phrases per slide (typically ≤6 bullets or one footer keyword line).
2. **Full sentences not on slides** — put them in `\note{...}` inside frames and/or `slides_script.md` for rehearsal; never paragraph blocks on the visible slide.
3. **Numbers in `metadata.tex`** — every value on a chart comes from macros; slides/figures do not hardcode metrics.
4. **One figure file per complex drawing** — `figures/*.tex` with TikZ or pgfplots; frames only `\input` them.
5. **Split crowded slides** — if a frame has two ideas or a dense diagram, use two frames.

**Do not assume** language, talk length, audience, or course-specific rules unless the user states them.

## Repository layout

```
<deck>/slides/              # or report/slides/, docs/talk/slides/
├── main.tex
├── preamble.tex            # fonts, theme, packages (language-specific)
├── metadata.tex            # data macros
├── build.sh
├── figures/
└── slides/
    ├── 01_title.tex
    └── ...

<deck>/slides_plan.md       # optional: slide list, figures, per-slide seconds
<deck>/slides_script.md     # optional: spoken script (authoring source; can mirror into \note)
```

## Speaker notes (Beamer built-in)

Beamer supports **embedded speaker notes** with `\note` inside `\begin{frame}...\end{frame}`. Requires `\usepackage{pgfpages}` (not `pdfpages`).

### Output modes (`\setbeameroption`)

| Option | PDF result | When to use |
|--------|------------|-------------|
| `hide notes` | Slides only (default) | Audience PDF, submission |
| `show notes on second screen=right` | Slide left, notes right on same PDF page | **Presenting** with pdfpc / Pympress |
| `show notes` | Each slide followed by a notes page | Print rehearsal pack |
| `show only notes` | Notes pages only | Print script without slides |

Toggle in `preamble.tex` or via build flag (see [reference.md](reference.md) `notes.tex` pattern).

### Writing notes in frames

```latex
\begin{frame}{Results}
  \centering
  \input{figures/bars.tex}
  \note{Full spoken paragraph for this slide. Not visible on the slide itself.}
  \note[item]{Optional bullet in the notes panel.}
\end{frame}
```

- Use `\note{...}` **inside** the frame (preferred); multiple `\note` on one frame merge into one notes page.
- Keep slide body to keywords + figures; put the script in `\note`.

### Presenting dual-screen PDF

1. Compile with `show notes on second screen=right`.
2. Open PDF in **[pdfpc](https://pdfpc.github.io/)** (`pdfpc -d screen -g deck.pdf`) or **[Pympress](https://cimbali.github.io/pympress/)**.
3. These tools detect Beamer’s side-by-side layout and show slides to the audience while you read notes locally.

Online talks: share the **slide-only** window; keep the notes window on your screen (same idea as PowerPoint presenter view).

### `slides_script.md` vs `\note`

| | `slides_script.md` | `\note` in `.tex` |
|--|-------------------|-------------------|
| Best for | Drafting, git diff, non-LaTeX editors | PDF-integrated presenter view |
| Visible in pdfpc/Pympress | No (unless copied into `\note`) | Yes |
| Audience PDF | Never included if you compile `hide notes` | Never on slide surface |

**Recommended:** write `slides_script.md` first, then paste each section into `\note{...}` (or maintain both during prep). Do not duplicate maintenance long-term unless the user wants both.

### Notes page layout (optional)

Customize thumbnail size of the current slide on the notes panel:

```latex
\setbeamertemplate{note page}{%
  \insertslideintonotes{0.12}%
  \rule{\textwidth}{0.4pt}%
  \scriptsize\insertnote
}
```

Smaller `0.12` → more room for text (pdfpc/Pympress). See [reference.md](reference.md).

## Workflow

### 1. Gather requirements (ask if missing)

| Item | Examples |
|------|----------|
| **Language** | English, 中文, bilingual titles |
| **Duration** | 5 / 15 / 45 min — drives slide count |
| **Aspect** | 16:9 (`aspectratio=169`) default; 4:3 if required |
| **Deliverable path** | e.g. `report/MyTalk_slides.pdf` |
| **Must-show content** | results first? demo video? appendix? |

**Slide count (rough):** `slides ≈ duration_min × (1.0–1.5)` for figure-heavy decks; `× 1.5–2.5` if more text. Adjust after script rehearsal.

**Script length:** language-dependent — do not use a fixed 字/分. Estimate from user’s speaking style or a short timed read-aloud of `slides_script.md`.

### 2. Plan (`slides_plan.md`)

For each slide: title, figure file(s), keywords on slide, target seconds, script section anchor.

Order slides by user goals (often: title → key results → method diagrams → details → close). Shared background material: **at most one light slide** unless the user wants more.

### 3. Implement TeX

1. `metadata.tex` — `\newcommand` for all metrics and labels used in plots.
2. `preamble.tex` — see [reference.md](reference.md) for **English** vs **CJK** font blocks.
3. `slides/NN_name.tex` — one `frame` per file; short `\frametitle{}`.
4. `figures/` — pgfplots for bars/lines; TikZ for pipelines/architecture.

### 4. Speaker notes

1. If the user will present with pdfpc/Pympress: add `\note{...}` per frame (from `slides_script.md` or direct).
2. Set `\setbeameroption{hide notes}` for submission PDF; `show notes on second screen=right` for presenter PDF (two builds or one flag in `build.sh`).

### 5. Write `slides_script.md` (optional)

Markdown script keyed by slide number — useful before migrating text into `\note`. Language matches the talk.

### 6. Compile

```bash
# Preferred on minimal TeX installs
tectonic -X compile main.tex --outdir . --print

# Or LuaLaTeX / XeLaTeX (two passes)
lualatex -interaction=nonstopmode main.tex && lualatex main.tex
```

`build.sh`: compile inside `slides/`, copy PDF to the path the user wants.

Tectonic install (linux x86_64 example):
`curl -fsSL https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-gnu.tar.gz | tar -xz -C ~/.local/bin`

### 7. Verify

- Page count matches plan.
- Log: no fatal errors; fix overfull boxes if figures clip.
- Keywords on slides are readable at projected size (avoid long sentences).

## Language setup

Pick **one** path in `preamble.tex` (requires `fontspec` → LuaLaTeX, XeLaTeX, or Tectonic):

| Language | Fonts (examples) |
|----------|------------------|
| English | `Latin Modern Sans`, `TeX Gyre Heros`, or system `Helvetica` |
| 中文 | `Noto Sans CJK TC` / `SC` / `JP` / `KR` as appropriate |
| Mixed EN+中文 | CJK font as `\setmainfont`; monospace `Latin Modern Mono` |

Do **not** default to CJK. If the user writes in English, use an English sans font block from [reference.md](reference.md).

`pdflatex` without `fontspec` is only OK for English-only decks with limited Unicode.

### CJK fonts without sudo

Install Noto Sans CJK OTF files under `~/.local/share/fonts` (no root):

```bash
bash ~/.cursor/skills/latex-beamer-slides/scripts/install-cjk-fonts-user.sh TC   # TW/traditional
bash ~/.cursor/skills/latex-beamer-slides/scripts/install-cjk-fonts-user.sh SC   # simplified
```

Then in `preamble.tex` with `ctexbeamer` or `fontspec`, point `Path` at the install directory and use the `.otf` basenames (see [reference.md](reference.md) CJK block).

## Figure-first slide patterns

| Pattern | `figures/` | Slide keywords (example) |
|---------|------------|---------------------------|
| Results | bar/line chart | metric names, “vs baseline” |
| Architecture | TikZ flowchart | component names |
| Comparison | grouped bars | legend terms only |
| Timeline | TikZ axis | phase labels |
| Equation + table | — | equation + small tabular only |

Prefer **horizontal bar charts** (`xbar`) for many categories; **TikZ** when pgfplots is awkward.

## pgfplots / TikZ pitfalls

| Issue | Fix |
|-------|-----|
| `symbolic coords` + macros | Numeric ticks `ytick={1,2,...}` + `yticklabels={...}` |
| `ybar` / `xbar` order | `(x, y) = (category_or_index, value)` for ybar; `(value, index)` for xbar |
| Non-ASCII in symbolic coords | ASCII internal labels + `xticklabels` / `yticklabels` |
| `nodes near coords` TeX overflow | Omit or simplify |
| TikZ style `cap` | Reserved — rename (e.g. `limitbox`) |

## Frame template (keywords + notes)

```latex
\begin{frame}{Short title}
  \vspace{-0.3em}
  \centering
  \input{figures/my_diagram.tex}
  \vspace{0.4em}
  {\footnotesize\textcolor{gray}{keyword · keyword · keyword}\par}
  \note{Spoken script for this slide. Stays off the slide; appears in presenter PDF.}
\end{frame}
```

## Duration scaling (no fixed template)

Example only — replace with user’s minutes and topics:

| min | ~slides (figure-heavy) | Notes |
|-----|------------------------|--------|
| 5 | 6–8 | results + one method figure |
| 15 | 12–18 | method split across 2–3 figures |
| 45 | 25–40 | sections + appendix optional |

Rebalance by merging script sections or splitting figures, not by shrinking fonts.

## Other skills

- Templates / themes: [reference.md](reference.md)
- Academic polish: [Noi1r/beamer-skill](https://github.com/Noi1r/beamer-skill), `beamer-presentation` (econ) — optional review pass
- From Slidev: reuse slide **order** and **numbers**; redraw diagrams in TikZ/pgfplots

## Scaffold new deck

```bash
bash ~/.cursor/skills/latex-beamer-slides/scripts/scaffold.sh path/to/slides
# optional: LANG=en|zh  (see script --help)
```
