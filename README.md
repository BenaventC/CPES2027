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
- [`R05_political_references_mistral.ipynb`](R05_political_references_mistral.ipynb): complete, self-contained pipeline for extracting political figures, parties, slogans, events, and institutions with Mistral 7B.

R04 starts with a manual 1% pilot on GPU 2. It detects currencies and common or slang terms for money, then produces JSON/CSV counts, an 80-term word cloud, an 80-term UMAP projection, cooccurrence data, and yearly lexical density for 1990-2024.

## R05 — Références politiques dans les chansons

### Organisation et lancement

Le notebook R05 contient toutes les étapes du pipeline, organisées en cellules courtes et documentées : préparation du corpus, prompt et validation, appels au modèle, exports, rapprochement sémantique et statistiques. Il n'a pas besoin d'un script Python R05 séparé.

- Modèle d'annotation : `mistralai/Mistral-7B-Instruct-v0.3`, via un serveur vLLM local, avec `temperature=0`.
- Échantillon par défaut : **200 chansons**, graine **42**, après filtrage à **10–4 000 mots**.
- Cinq types : `figure_politique`, `parti_politique`, `slogan`, `evenement_politique`, `institution`.
- Le notebook inspecte les GPU avant de démarrer le serveur sur un seul GPU disponible, au port **8015**. Un serveur existant peut être réutilisé après vérification du modèle ; sa disponibilité ne garantit pas à elle seule son placement GPU.
- Les chemins sont relatifs au dossier du projet : ouvrir le notebook avec ce dossier comme répertoire de travail.

Le notebook utilise par défaut un échantillon déterministe de 200 chansons. Dans la première section, `run_mode = 'pilot'` avec `pilot_fraction = 0.01` sélectionne 1 % du corpus filtré ; `run_mode = 'full'` sélectionne toutes les chansons filtrées. N'utiliser ces modes qu'après examen qualitatif de l'échantillon.

L'annotation nécessite `pandas`, `requests` et `tqdm`. Le rapprochement nécessite aussi `numpy`, un couple **PyTorch/Transformers compatible**, et le modèle **`BAAI/bge-m3` déjà en cache local**. Il utilise le CPU pour ne pas concurrencer Mistral sur GPU. L'environnement local `vllm_mistral` a été validé ; les chemins de lancement du serveur dans le notebook sont à adapter sur une autre machine.

### Colonnes et rapprochement sémantique

| Colonne | Origine et signification |
|---|---|
| `mention` | Texte de la mention extrait par Mistral et vérifié dans les paroles. |
| `reference` | Nom proposé par Mistral, conservé sans modification par notre rapprochement. |
| `extrait` | Justification textuelle proposée par Mistral et vérifiée dans les paroles. |
| `reference_canon` | Nom construit par notre processus de rapprochement des références. |
| `annotation_status`, `annotation_error` | Statut et diagnostic par chanson dans le JSON ; un échec n'est pas une absence de référence. |

La section **6** calcule des embeddings BGE-M3 des références distinctes. Les rapprochements restent séparés par type, avec une similarité cosinus d'au moins **0,85** et un écart d'au moins **0,03** entre les deux meilleurs candidats. Ils utilisent des représentants directs, sans fusion transitive. Des garde-fous sur les noms évitent de confondre des prénoms différents et corrigent prudemment certaines coquilles. Les noms préférés sont modifiables, avec `Emmanuel Macron` comme exemple.

Le cas `Macron` / `emmanuel Macron` / `Président Marcon` a été testé : il devient `Emmanuel Macron`. Les contrôles conservent Brigitte Macron, François Hollande, Marine et Jean-Marie Le Pen séparément, et ne résolvent pas automatiquement le nom ambigu `Le Pen`. **Une proximité sémantique n'est pas une preuve d'identité** : examiner les correspondances, les textes corrigés et les scores exportés.

### Statistiques et exports

La section **7** calcule les effectifs et parts par type ainsi que le nombre et la proportion de chansons concernées. La section **7.1** regroupe par `type` et `reference_canon`. Les dénominateurs de prévalence excluent les annotations en échec. Une chanson compte au plus une fois par groupe ; un effectif de références compte les éléments extraits, pas les répétitions des mots dans les paroles.

Les tableaux de fréquences n'affichent que les effectifs **strictement supérieurs à 1**. Les aperçus des CSV canoniques, des correspondances et des fréquences sont limités aux **10 premières lignes**. Les CSV exportés et les dénominateurs des pourcentages restent complets.

Tous les fichiers sont écrits dans `export/`, sous le préfixe `R05_political_references_<label>` ; par exemple `200songs_10to4000w` :

| Suffixe | Contenu |
|---|---|
| `.json` | Une ligne logique par chanson, références, statut et erreur éventuelle. |
| `.csv` | Une ligne par référence extraite, avec métadonnées de la chanson. |
| `_errors.csv` | Diagnostics des annotations en échec. |
| `_performance.csv` | Durée client, chansons/s, succès, échecs et effectif des références. |
| `_canonical.csv` | Tableau enrichi avec `reference_canon`, sans modifier les colonnes brutes. |
| `_canonical_mapping.csv` | Correspondances source/canonique, similarités et décisions. |
| `_canonical_performance.csv` | Paramètres et performance du rapprochement sur CPU. |
| `_type_frequencies.csv` | Fréquences par type. |
| `_type_reference_frequencies.csv` | Fréquences par type et référence canonique. |

Les métriques d'annotation mesurent le **temps mural côté client**, pas le temps des kernels CUDA ni le pic de mémoire GPU. Les fichiers portent le label de l'échantillon pour séparer les tailles ; relancer le même label réécrit ses exports.

### Validation et limites

Le dernier essai local sur **200 chansons** a terminé avec **181 annotations réussies**, **19 échecs de validation** et **303 références extraites** ; l'annotation a pris environ **311 secondes**. Ces chiffres décrivent cet essai, pas une garantie de qualité sémantique ou de reproductibilité exacte des sorties du modèle.

Des faux positifs restent présents, notamment `Michael Jackson` classé comme figure politique et `Année` comme événement. Le rapprochement canonique ne corrige pas les erreurs de classification. Une revue manuelle et un ajustement du prompt sont nécessaires avant un passage à grande échelle.

Les réponses tronquées sont rejetées ; une connexion refusée au serveur arrête le traitement plutôt que de transformer toutes les chansons suivantes en échecs. **Il n'y a pas encore de sauvegarde intermédiaire ni de reprise** : un arrêt avant l'export final perd les résultats en mémoire. Les résultats partiels ne sont pas présentés comme complets.

Une cellule de contrôles rapides intégrée au notebook vérifie le schéma JSON, les preuves textuelles, les distinctions entre noms de personnes et le cas d'une table canonique vide. Elle s'exécute sans lancer vLLM ni charger BGE-M3.

Les sorties du pilote, les journaux et les données restent locaux ; le notebook publié est fourni sans sorties d'exécution.

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
- [`R05_political_references_mistral.ipynb`](R05_political_references_mistral.ipynb): political-reference annotation with Mistral and a deterministic pilot-first workflow.
