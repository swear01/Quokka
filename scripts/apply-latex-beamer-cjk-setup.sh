#!/usr/bin/env bash
# Run on the host (needs network + write outside Quokka): completes skill sync, fonts, rebuild.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_SCRIPTS="${HOME}/.cursor/skills/latex-beamer-slides/scripts"
SKILL_ROOT="$(dirname "$SKILL_SCRIPTS")"

install -m 755 "${REPO}/scripts/install-cjk-fonts-user.sh" "${SKILL_SCRIPTS}/install-cjk-fonts-user.sh"
bash "${SKILL_SCRIPTS}/install-cjk-fonts-user.sh" TC

# Patch SKILL.md if subsection missing
if ! grep -q 'CJK fonts without sudo' "${SKILL_ROOT}/SKILL.md"; then
  python3 - "${SKILL_ROOT}/SKILL.md" <<'PY'
import sys
path = sys.argv[1]
text = open(path).read()
needle = "`pdflatex` without `fontspec` is only OK for English-only decks with limited Unicode.\n\n## Figure-first slide patterns"
insert = """`pdflatex` without `fontspec` is only OK for English-only decks with limited Unicode.

### CJK fonts without sudo

Install Noto Sans CJK OTF files under `~/.local/share/fonts` (no root):

```bash
bash ~/.cursor/skills/latex-beamer-slides/scripts/install-cjk-fonts-user.sh TC   # TW/traditional
bash ~/.cursor/skills/latex-beamer-slides/scripts/install-cjk-fonts-user.sh SC   # simplified
```

Then in `preamble.tex` with `ctexbeamer` or `fontspec`, point `Path` at the install directory and use the `.otf` basenames (see [reference.md](reference.md) CJK block).

## Figure-first slide patterns"""
if needle not in text:
    raise SystemExit("SKILL.md anchor not found")
open(path, "w").write(text.replace(needle, insert, 1))
PY
fi

# Patch reference.md CJK block (simplified: marker-based)
REF="${SKILL_ROOT}/reference.md"
if ! grep -q 'install-cjk-fonts-user.sh' "$REF"; then
  python3 - "$REF" "${REPO}/scripts/latex-beamer-skill-cjk/reference-CJK-snippet.md" <<'PY'
import sys
path, snippet_path = sys.argv[1], sys.argv[2]
text = open(path).read()
start = "## preamble.tex — CJK (use when user requests"
end = "## metadata.tex"
i, j = text.find(start), text.find(end)
if i < 0 or j < 0:
    raise SystemExit("reference.md anchors not found")
snippet = open(snippet_path).read()
# drop first line (title comment)
body = "\n".join(snippet.splitlines()[2:])  # skip title + blank
new_block = start + " 中文/日文/韓文)\n\n" + body.split("```latex", 1)[0].strip() + "\n\n```latex\n" + body.split("```latex", 1)[1]
open(path, "w").write(text[:i] + new_block + "\n\n" + text[j:])
PY
fi

SLIDES="${REPO}/notes/deepseek-reproduction-beamer/slides"
(cd "$SLIDES" && ./build.sh)
echo "---"
echo "Fonts:"
ls -lh "${HOME}/.local/share/fonts/noto-sans-cjk-tc/" || true
echo "PDF:"
ls -lh "${SLIDES}/main.pdf" "${REPO}/notes/deepseek-reproduction-beamer/deepseek-reproduction-slides.pdf"
echo "Glyph warnings (if any):"
grep -iE 'glyph|missing character|font.*not found' "${SLIDES}/main.log" 2>/dev/null || true
