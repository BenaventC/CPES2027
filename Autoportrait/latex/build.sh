#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"

if command -v mmdc >/dev/null 2>&1; then
    mmdc -i pipeline.mmd -o pipeline.pdf -b white --pdfFit
elif [[ ! -s pipeline.pdf ]]; then
    printf '%s\n' "Erreur : installer Mermaid CLI (mmdc) pour créer pipeline.pdf." >&2
    exit 1
else
    printf '%s\n' "Mermaid CLI absent : réutilisation explicite du diagramme PDF fourni." >&2
fi

if command -v tectonic >/dev/null 2>&1; then
    tectonic article.tex
elif command -v pdflatex >/dev/null 2>&1; then
    if ! command -v bibtex >/dev/null 2>&1; then
        printf '%s\n' "Erreur : bibtex est nécessaire pour compiler references.bib." >&2
        exit 1
    fi
    pdflatex -interaction=nonstopmode -halt-on-error article.tex
    bibtex article
    pdflatex -interaction=nonstopmode -halt-on-error article.tex
    pdflatex -interaction=nonstopmode -halt-on-error article.tex
else
    printf '%s\n' "Erreur : installer Tectonic ou une distribution LaTeX avec pdflatex." >&2
    exit 1
fi
