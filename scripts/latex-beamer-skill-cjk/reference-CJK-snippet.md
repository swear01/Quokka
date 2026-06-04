# Replace CJK block in ~/.cursor/skills/latex-beamer-slides/reference.md

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
```
