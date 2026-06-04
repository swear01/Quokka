#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$DIR/../deepseek-reproduction-slides.pdf}"
FONT_DIR="${HOME}/.local/share/fonts/noto-sans-cjk-tc"
REG="${FONT_DIR}/NotoSansCJKtc-Regular.otf"

ensure_noto_tc_fonts() {
  if [[ -f "$REG" ]]; then
    echo "Noto TC OTF: ${REG}"
    return 0
  fi
  EXTRACT="${DIR}/../scripts/extract-noto-cjk-tc-from-ttc.py"
  if [[ -f /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc ]] \
     && command -v python3 >/dev/null \
     && python3 -c "import fontTools" 2>/dev/null \
     && [[ -f "$EXTRACT" ]]; then
    echo "Extracting Noto Sans CJK TC from system TTC..."
    python3 "$EXTRACT"
    return 0
  fi
  INSTALL="${HOME}/.cursor/skills/latex-beamer-slides/scripts/install-cjk-fonts-user.sh"
  if command -v curl >/dev/null && [[ -f "$INSTALL" ]]; then
    echo "Downloading Noto Sans CJK TC OTF..."
    bash "$INSTALL" TC
    return 0
  fi
  echo "WARN: ${REG} missing; compile will use fontconfig fallback (Noto Sans CJK TC)" >&2
}

ensure_noto_tc_fonts
cd "$DIR"
T="${TECTONIC:-$HOME/.local/bin/tectonic}"
if [[ -x "$T" ]]; then
  "$T" -X compile main.tex --outdir . --print
elif command -v lualatex >/dev/null; then
  lualatex -interaction=nonstopmode main.tex
  lualatex -interaction=nonstopmode main.tex
else
  echo "Need tectonic or lualatex" >&2
  exit 1
fi
cp -f main.pdf "$OUT"
echo "Wrote $OUT (speaker notes in \\note{} on each frame)"
