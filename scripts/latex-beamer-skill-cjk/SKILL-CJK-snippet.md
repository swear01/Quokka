# Paste into ~/.cursor/skills/latex-beamer-slides/SKILL.md (under Language setup)

### CJK fonts without sudo

Install Noto Sans CJK OTF files under `~/.local/share/fonts` (no root):

```bash
bash ~/.cursor/skills/latex-beamer-slides/scripts/install-cjk-fonts-user.sh TC   # TW/traditional
bash ~/.cursor/skills/latex-beamer-slides/scripts/install-cjk-fonts-user.sh SC   # simplified
```

Then in `preamble.tex` with `ctexbeamer` or `fontspec`, point `Path` at the install directory and use the `.otf` basenames (see [reference.md](reference.md) CJK block).
