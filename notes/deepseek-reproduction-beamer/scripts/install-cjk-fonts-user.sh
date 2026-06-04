#!/usr/bin/env bash
set -euo pipefail
LOCALE="${1:-TC}"
FONT_ROOT="${HOME}/.local/share/fonts"
case "$LOCALE" in
  TC) SUB=TW; LOC=tc ;;
  SC) SUB=SC; LOC=sc ;;
  JP) SUB=JP; LOC=jp ;;
  KR) SUB=KR; LOC=kr ;;
  *) echo "Usage: $0 [TC|SC|JP|KR]" >&2; exit 1 ;;
esac
FONT_DIR="${FONT_ROOT}/noto-sans-cjk-${LOC}"
mkdir -p "$FONT_DIR"
BASE="https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/${SUB}"
for face in Regular Bold; do
  F="NotoSansCJK${LOC}-${face}.otf"
  curl -fsSL -o "${FONT_DIR}/${F}" "${BASE}/${F}"
  echo "ok ${F}"
done
fc-cache -f "${FONT_ROOT}" 2>/dev/null || true
echo "Fonts in ${FONT_DIR}"
