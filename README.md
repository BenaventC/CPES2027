# ProjetRap - French Rap Corpus Analysis

## Contexte

Ce projet s'inscrit dans le cadre du cours d'application des méthodes de **data science et d'intelligence artificielle à l'analyse de corpus volumineux**, du parcours **CPES Sciences des données, Arts et Cultures (DAC)**, porté par l'[Université PSL](https://psl.eu/) et le [Lycée Louis-le-Grand](https://www.louislegrand.fr/) :
- Page du parcours : [psl.eu/formation/cpes-psl-louis-le-grand](https://psl.eu/formation/cpes-psl-louis-le-grand)

Ce cours mobilise également les ressources de l'[Institut ACSS-PSL](https://acss-dig.psl.eu/) (Applied Computational Social Sciences), dont l'auteur de ce projet est membre.

The corpus (`corpus.csv`) gathers French rap lyrics together with quantitative and qualitative variables such as popularity, lyric length, sentiment, and artist metadata.

## Source des données

`corpus.csv` is derived from the **LRFAF** corpus of French rap songs collected from genius.com and enriched with Wikipedia/Wikidata information by Benoit de Courson (regicid):
- Jeu de données : [huggingface.co/datasets/regicid/LRFAF](https://huggingface.co/datasets/regicid/LRFAF)
- Article associé : Benoît de Courson, *« LRFAF : une exploration numérique du rap français depuis les années 1990 »* — [researchgate.net/publication/379061284](https://www.researchgate.net/publication/379061284_LRFAF_une_exploration_numerique_du_rap_francais_depuis_les_annees_1990)
- Exploration interactive des fréquences lexicales du corpus : [Gallicagram, corpus « Rap »](https://shiny.ens-paris-saclay.fr/app/gallicagram)

Ce corpus est distribué pour un usage de recherche, sans licence formelle (les ayants droit restant les artistes).

## Installation

`corpus.csv` exceeds GitHub's 100 MB per-file limit and is therefore **not versioned**. Download the source corpus from Hugging Face before running the notebooks and place it at the repository root as `corpus.csv`:

```powershell
Invoke-WebRequest -Uri "https://huggingface.co/datasets/regicid/LRFAF/resolve/main/corpus.csv?download=true" -OutFile "corpus.csv"
```

## Current Analysis Pipeline

The repository contains a complete, GPU-ready pipeline:

- `R00_corpus_analysis.ipynb`: corpus description and exploratory analysis;
- `R01_pos_analysis.ipynb`: Stanza morphosyntactic annotation on GPU, including line-bounded dependency parsing and POS analysis;
- `R02_bge_m3_embeddings.ipynb`: BGE-M3 GPU embeddings at lyric-group level and token-weighted whole-song level.

The two GPU notebooks process lyrics containing 10 to 4,000 words inclusive. They use scoped resumable shards so that long runs can safely continue after an interruption.

## Organisation du dépôt

- Scripts and notebooks (`.py`, `.ipynb`) remain at the repository root.
- `images/`: generated figures.
- `export/`: tabular summaries, reports, manifests, and lightweight derived data.
- Large raw data, CoNLL-U token exports, and resumable embedding shards remain local and are ignored by Git.

Voir les skills [`notebook-authoring`](.github/skills/notebook-authoring/SKILL.md) et [`export-organization`](.github/skills/export-organization/SKILL.md) pour les conventions détaillées de rédaction des notebooks et d'organisation des exports.

## Notebooks

- [`01_description_variables_quantitatives.ipynb`](01_description_variables_quantitatives.ipynb): original quantitative-variable description.
- [`R00_corpus_analysis.ipynb`](R00_corpus_analysis.ipynb): current corpus exploration.
- [`R01_pos_analysis.ipynb`](R01_pos_analysis.ipynb): full-corpus POS and dependency analysis.
- [`R02_bge_m3_embeddings.ipynb`](R02_bge_m3_embeddings.ipynb): hierarchical BGE-M3 lyric embeddings.
