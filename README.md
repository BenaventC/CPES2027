# ProjetRap - Analyse du corpus de rap français

Ce dépôt rassemble des analyses quantitatives, linguistiques et computationnelles du rap français. Il s'inscrit dans le parcours CPES Sciences des données, Arts et Cultures (DAC), porté par l'[Université PSL](https://psl.eu/) et le [Lycée Louis-le-Grand](https://www.louislegrand.fr/), avec l'appui de l'[Institut ACSS-PSL](https://acss-dig.psl.eu/).

Le corpus `corpus.csv` contient des paroles de rap français et des métadonnées telles que l'artiste, le titre, l'année, la longueur des paroles, la popularité et l'URL source.

## Données

Le corpus est dérivé de **LRFAF**, collecté sur Genius et enrichi avec des informations Wikipedia/Wikidata par Benoît de Courson (`regicid`) :

- [Jeu de données LRFAF sur Hugging Face](https://huggingface.co/datasets/regicid/LRFAF)
- [Article associé](https://www.researchgate.net/publication/379061284_LRFAF_une_exploration_numerique_du_rap_francais_depuis_les_annees_1990)
- [Exploration Gallicagram du corpus Rap](https://shiny.ens-paris-saclay.fr/app/gallicagram)

Le corpus brut n'est pas versionné. Placez `corpus.csv` à la racine du dossier Rap avant toute exécution :

```powershell
Invoke-WebRequest -Uri "https://huggingface.co/datasets/regicid/LRFAF/resolve/main/corpus.csv?download=true" -OutFile "corpus.csv"
```

Le fichier doit notamment contenir les colonnes `doc_id`, `year`, `lyrics` et, lorsque disponible, `n_words`.

## Current Analysis Pipeline

The repository contains a GPU-ready analysis pipeline:

- [`01_description_variables_quantitatives.ipynb`](01_description_variables_quantitatives.ipynb): initial quantitative-variable description;
- [`R00_corpus_analysis.ipynb`](R00_corpus_analysis.ipynb): corpus exploration and lexical statistics;
- [`R01_pos_analysis.ipynb`](R01_pos_analysis.ipynb): Stanza POS and dependency analysis on GPU;
- [`R02_bge_m3_embeddings.ipynb`](R02_bge_m3_embeddings.ipynb): BGE-M3 lyric embeddings;
- [`R03_toxicity_vllm_gemma_clean.ipynb`](R03_toxicity_vllm_gemma_clean.ipynb): toxicity scores from 0 to 10 for four dimensions;
- [`R04_money_extraction_mistral_gpu2.ipynb`](R04_money_extraction_mistral_gpu2.ipynb): extraction and counting of monetary entities and expressions.

R04 starts with a manual 1% pilot on GPU 2. It detects currencies and common or slang terms for money, then produces JSON/CSV counts, an 80-term word cloud, an 80-term UMAP projection, cooccurrence data, and yearly lexical density for 1990-2024.

## Repository Organisation

- Scripts and notebooks (`.py`, `.ipynb`) remain at the repository root.
- `images/`: generated figures.
- `export/`: CSV, JSON, reports, manifests, and other structured outputs.
- Only full-corpus outputs are intended for Git; pilot outputs, shards, logs, and temporary files are ignored.
- Large raw data, CoNLL-U exports, and embedding artifacts remain local.

See [`notebook-authoring`](.github/skills/notebook-authoring/SKILL.md), [`export-organization`](.github/skills/export-organization/SKILL.md), and [`rap-eda-hip-hop-aesthetic`](.github/skills/rap-eda-hip-hop-aesthetic/SKILL.md) for project conventions.

## Notebooks

- [`01_description_variables_quantitatives.ipynb`](01_description_variables_quantitatives.ipynb): original quantitative-variable description.
- [`R00_corpus_analysis.ipynb`](R00_corpus_analysis.ipynb): corpus exploration.
- [`R01_pos_analysis.ipynb`](R01_pos_analysis.ipynb): POS and dependency analysis.
- [`R02_bge_m3_embeddings.ipynb`](R02_bge_m3_embeddings.ipynb): hierarchical BGE-M3 embeddings.
- [`R03_toxicity_vllm_gemma_clean.ipynb`](R03_toxicity_vllm_gemma_clean.ipynb): toxicity measurement with vLLM.
- [`R04_money_extraction_mistral_gpu2.ipynb`](R04_money_extraction_mistral_gpu2.ipynb): monetary-entity extraction with Mistral.
