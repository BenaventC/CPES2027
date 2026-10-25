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
- [`R05_political_references_mistral.ipynb`](R05_political_references_mistral.ipynb): complete, self-contained pipeline for extracting political figures, political organizations, and institutions with Mistral 7B.

R04 starts with a manual 1% pilot on GPU 2. It detects currencies and common or slang terms for money, then produces JSON/CSV counts, an 80-term word cloud, an 80-term UMAP projection, cooccurrence data, and yearly lexical density for 1990-2024.

## R05b — Environnement Qwen3-32B et BGE-M3

Le notebook [R05b_political_references_qwen3_32b.ipynb](R05b_political_references_qwen3_32b.ipynb) utilise le noyau **Rap R05b (PyTorch CPU)**. Son environnement `.venv-r05b` est indépendant des environnements existants et du serveur vLLM. Les dépendances sont définies dans [requirements-r05b.txt](requirements-r05b.txt).

Depuis le dossier `Rap`, pour recréer cet environnement avec Python 3.11 :

```bash
python3.11 -m venv .venv-r05b
.venv-r05b/bin/python -m pip install -r requirements-r05b.txt
.venv-r05b/bin/python -m ipykernel install --user --name rap-r05b-cpu --display-name "Rap R05b (PyTorch CPU)"
```

Le couple testé est **PyTorch 2.6.0+cpu / Transformers 5.18.0**. Transformers 5.18.0 désactive PyTorch 2.4.0 : l'erreur « AutoModel requires the PyTorch library » peut donc apparaître même lorsque `import torch` fonctionne. Ne pas modifier l'environnement GPU de vLLM pour corriger ce problème.

Après sélection du nouveau noyau, réexécuter la cellule des paramètres et les définitions de fonctions de la section 2. Pour reprendre sans réannoter, charger le JSON des annotations déjà exportées (adapter le nom au traitement souhaité) :

```python
annotations_path = export_dir / 'R05b_qwen32_n_200_annotations.json'
results = json.loads(annotations_path.read_text(encoding='utf-8'))
output_prefix = f'R05b_qwen32_n_{len(results)}'
references_df = flatten_reference_rows(results)
```

Reprendre ensuite à la cellule de canonicalisation, puis aux fréquences et aux nuages. Le modèle `BAAI/bge-m3` doit être présent dans le cache local ; les embeddings sont calculés sur CPU.

### Annotation manuelle du corpus complet

Le notebook est configuré avec `run_mode = 'full'` et
`max_concurrent_requests = 16`. Le filtre conserve les paroles de 10 à 4 000 mots.
`test_sample_size = 10000` n'intervient qu'en mode `test`.
Les contrôles d'extraction et de vérification
sémantique restent identiques. `batch_size = 32` borne la fenêtre de tâches
soumises (avec un minimum égal à la concurrence), et non le nombre de chansons
traitées simultanément. Les résultats sont remis dans l'ordre du corpus avant
export ; les métriques CSV enregistrent les deux réglages. Mettre
`max_concurrent_requests = 1` rétablit le traitement séquentiel.

Le benchmark sur les mêmes 200 chansons a mesuré environ 69 secondes à 16
requêtes simultanées contre 440 secondes en séquentiel. Le précédent traitement
de 10 000 chansons a demandé environ 52 minutes ; celui de 84 155 chansons,
environ 7 h 25. Ces durées restent indicatives. Des annotations différentes ont été observées
malgré `temperature=0` : une revue qualitative reste nécessaire.

Depuis le noyau **Rap R05b (PyTorch CPU)**, exécuter les cellules dans l'ordre
jusqu'à la section 9. Un serveur existant est vérifié et réutilisé sans charger
une deuxième instance. Les exports portent le préfixe
`R05b_qwen32_n_<effectif>_`, construit à partir du corpus sélectionné.

L'annotation sauvegarde un checkpoint
`export/R05b_qwen32_n_<effectif>_annotation_checkpoint.json` toutes les `batch_size`
chansons terminées, ainsi qu'en fin de traitement ou lors d'une exception.
L'écriture est atomique : un nouveau snapshot remplace l'ancien après écriture
complète. Pour reprendre, mettre `restart_annotation = False`, recharger
les paramètres, les définitions et le même corpus, puis relancer la cellule
d'annotation. Les chansons déjà sauvegardées ne font
pas l'objet de nouveaux appels, y compris les échecs explicites. Un arrêt
brutal peut nécessiter de recalculer les dernières chansons non sauvegardées.

La reprise vérifie l'empreinte du corpus, du prompt et des paramètres ; un
checkpoint incompatible ou corrompu provoque une erreur sans écraser le fichier.
Pour une nouvelle expérience, utiliser un préfixe distinct ou archiver
explicitement le checkpoint avant de recommencer. Ne pas lancer deux traitements
simultanés avec le même préfixe. Le temps et le débit exportés cumulent les
sessions d'annotation enregistrées, hors période d'interruption ; il ne s'agit
pas d'un chronométrage des kernels GPU.

Pour le nouveau lancement manuel du corpus complet, le notebook utilise
`run_mode = 'full'` et `restart_annotation = True`. La cellule 5.1 supprime
le checkpoint courant avant de réannoter toutes les chansons ; les exports
de même préfixe sont remplacés à la fin. Aucun processus externe n'est requis.
Pour reprendre après interruption sans repartir de zéro, mettre
`restart_annotation = False` et réexécuter les paramètres avant l'annotation.
Un verrou exclusif refuse un deuxième lancement du même préfixe avant toute
suppression du checkpoint. Le modèle servi est revérifié avant cette suppression.

### Facettes par périodes de cinq ans

La section **9** de R05b calcule et exporte les fréquences par période.
La section **11** produit une figure à facettes par type de référence,
soit trois figures avec six panneaux : avant 2000, 2000–2004,
2005–2009, 2010–2014, 2015–2019 et 2020 et après. Les première et dernière
périodes sont ouvertes. Les six panneaux occupent une grille 2 × 3.

La section 8 définit uniquement le placement sans chevauchement et les libellés.
La section 11 ne représente que les références d'effectif strictement
supérieur à 2, avec une taille de police directement proportionnelle à l'effectif
et jusqu'à 100 références par nuage. Les effectifs faibles peuvent rester petits ;
aucun plancher de taille n'est ajouté. Les PNG haute résolution
`images/<préfixe_export_scoring>_political_orientation_five_year_facets_<type>.png`
sont affichés et enregistrés lors de l'exécution du notebook. Les exports
`export/R05b_qwen32_n_84155_five_year_type_reference_frequencies.csv`
et `export/R05b_qwen32_n_84155_five_year_summary.csv` conservent les fréquences
complètes, y compris les effectifs de 1 ou 2, et les effectifs par période.
Les années absentes ou non entières et les annotations en échec sont exclues
et signalées ; aucune borne 1990 ou 2024 ne limite les périodes ouvertes.
Les bornes ouvertes sont vides dans les colonnes CSV `year_start` / `year_end`.
Le dénominateur
de prévalence comprend toutes les chansons annotées avec succès de la période,
y compris celles sans référence. Les comparaisons entre panneaux doivent
utiliser les CSV pour les effectifs : les tailles sont ajustées par facette,
mais les couleurs des scores sont fixes entre toutes les figures.

Pour régénérer les figures depuis les exports de scoring, exécuter les imports
et paramètres, puis les sections 8 et 11. La section 11 lit les fréquences
par période associées au dernier export complet ; aucun appel à Qwen ni
nouveau calcul d'embeddings n'est nécessaire. Pour recalculer les fréquences,
exécuter la section 9 avec `results` et `canonical_lookup` chargés.
Les anciens nuages globaux et non colorés par score ne sont plus produits.
Neuf couleurs fixes représentent les scores : rouge à −4, mauve à 0,
bleu nuit à +4. Le gris est réservé aux références sans score, conservées
dans les nuages sans être assimilées au centre.

### Positionnement politique exploratoire des références

La section **10** de [R05b](R05b_political_references_qwen3_32b.ipynb)
réutilise le serveur local `Qwen/Qwen3-32B` pour estimer un positionnement
**global par couple `(type, reference_canon)`**, commun à toutes les périodes.
Elle ne mesure pas les opinions des artistes ni celles exprimées dans les chansons.

| Score | Catégorie |
|---|---|
| −4 | Extrême gauche |
| −3 | Gauche radicale |
| −2 | Gauche |
| −1 | Centre gauche |
| 0 | Centre |
| +1 | Centre droit |
| +2 | Droite |
| +3 | Droite radicale |
| +4 | Extrême droite |

Tous les types sont examinés, mais seuls les acteurs politiques publics
identifiables et les partis/mouvements dont le positionnement est établi peuvent
recevoir un score. Institutions, pays, termes génériques et personnes sans
activité politique publique explicite ne sont pas classés. Les références
non applicables, ambiguës ou insuffisamment connues ont un score vide/null,
**jamais zéro par défaut**. Un échec technique porte `scoring_status=failed`,
avec son diagnostic, et ne devient pas un résultat non applicable.
Le prompt demande également null si le type source est incompatible avec l'identité.
Ce contrôle dépend désormais du modèle, sans identité retournée pour une
vérification automatique.

Qwen renvoie uniquement `{"score": entier}` ou `{"score": null}` :
**aucune justification, aucun indice de confiance ni autre champ d'évaluation**.
Le parseur exige un entier de −4 à +4 ou null, et refuse notamment booléens,
décimaux et clés supplémentaires. Le tableau affiche seulement type, référence
et score ; les diagnostics techniques restent disponibles dans les exports.

Les résultats sont des **estimations exploratoires à revoir humainement** :
pas de recherche documentaire ni de citations vérifiées.
L'axe gauche-droite est réducteur, notamment hors du contexte français et pour
des trajectoires historiques changeantes. Les écarts entre scores ne sont pas
des distances mesurées.

La section 10 est **activée en mode complet**
(`enable_political_scoring = True`, `political_scoring_mode = 'full'`).
L'exécution de cette cellule lance le scoring ; la désactiver pour ne pas
réévaluer les références. La cellule utilise le modèle, l'endpoint,
le dossier d'export et le préfixe du traitement courant, sans taille de corpus
codée en dur. Les CSV canoniques et des fréquences par période des sections
6 et 9 doivent être présents. Les références sans année et les effectifs
inférieurs ou égaux à 2 restent inclus.

Le mode optionnel `political_scoring_mode = 'pilot'` retient, par type, les
quatre références les plus fréquentes et une référence rare, soit **15 couples**.
Ce pilote déterministe ne représente pas la distribution politique du corpus.
La concurrence est fixée à 4 ; la barre affiche progression, débit, ETA et échecs.
Le mode `'full'` évalue tous les couples uniques du CSV canonique. Il n'y a pas
de reprise automatique : chaque relance réévalue les cibles et crée de nouveaux
fichiers horodatés, sans écraser les précédents.

Les exports suivent
`export/R05b_qwen32_n_<effectif>_political_position_scale_m4_p4_<mode>_refs<N>_<UTC>` :

- `.csv` : type, référence, score entier nullable, effectif et métadonnées
  techniques (statut d'exécution, erreur, modèle, empreinte, réponse brute),
  sans confiance ni justification ;
- `.json` : résultats, prompt et métadonnées, avec empreintes du prompt et des cibles ;
- `_performance.csv` : temps mural client, débit, concurrence, scores,
  résultats valides sans score et échecs techniques ;
- `_period_frequencies.csv` : jointure many-to-one sur les fréquences par période,
  sans changement des lignes, effectifs ou prévalences ; les références sans
  correspondance de scoring restent `not_evaluated`, avec score vide.

**Changement d'échelle :** ne pas mélanger les anciens scores −3 à +3
avec les nouveaux scores. Le traitement complet −4 à +4 du 25 octobre 2026
a évalué **5 812 couples** : **1 185 scores**, **4 627 résultats valides
sans score** et **aucun échec technique**. Ces résultats ne garantissent pas
un classement correct et nécessitent toujours une revue humaine.

## R05 — Références politiques dans les chansons

### Organisation et lancement

Le notebook R05 contient toutes les étapes du pipeline, organisées en cellules courtes et documentées : préparation du corpus, prompt et validation, appels au modèle, exports, rapprochement sémantique et statistiques. Il n'a pas besoin d'un script Python R05 séparé.

Un schéma Mermaid en tête du notebook présente les flux de données, les validations, les tentatives correctives et les exports.

- Modèle d'annotation : `mistralai/Mistral-7B-Instruct-v0.3`, via un serveur vLLM local, avec `temperature=0`.
- Échantillon par défaut : **50 chansons**, graine **42**, après filtrage à **10–4 000 mots**.
- Trois types : `figure_politique`, `organisation_politique`, `institution`. Les partis et mouvements relèvent d'`organisation_politique` ; les slogans et événements ne sont plus extraits.
- Le périmètre du prompt conservé inclut notamment la police, l'armée et l'éducation dans les institutions publiques.
- Le notebook inspecte les GPU avant de démarrer le serveur sur un seul GPU disponible, au port **8015**. Un serveur existant peut être réutilisé après vérification du modèle ; sa disponibilité ne garantit pas à elle seule son placement GPU.
- Les chemins sont relatifs au dossier du projet : ouvrir le notebook avec ce dossier comme répertoire de travail.

Exécuter les cellules dans l'ordre depuis un noyau neuf. Le notebook vérifie les imports nécessaires avant l'annotation et utilise par défaut un échantillon déterministe de 50 chansons. Dans la première section, `run_mode = 'pilot'` avec `pilot_fraction = 0.01` sélectionne 1 % du corpus filtré ; `run_mode = 'full'` sélectionne toutes les chansons filtrées. N'utiliser ces modes qu'après examen qualitatif de l'échantillon.

L'annotation nécessite `pandas`, `requests` et `tqdm`. Le rapprochement nécessite aussi `numpy`, un couple **PyTorch/Transformers compatible**, et le modèle **`BAAI/bge-m3` déjà en cache local**. Il utilise le CPU pour ne pas concurrencer Mistral sur GPU. L'environnement local `vllm_mistral` a été validé ; les chemins de lancement du serveur dans le notebook sont à adapter sur une autre machine.

La section finale **8** nécessite également `matplotlib`. Elle produit un nuage par type à partir des fréquences canoniques de la section 7.1, sans nouvelle inférence. Les noms composés restent entiers ; les 80 références les plus fréquentes au maximum sont affichées, y compris les occurrences uniques. La taille et le dégradé chartreuse–rose ancien indiquent la fréquence ; la distance elliptique au centre ne peut pas diminuer quand la fréquence décroît. Le placement évite les chevauchements et affiche explicitement les catégories vides. Les PNG sont enregistrés dans `images/R05_nuage_<type>_<label>.png`.

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

La cellule de reprise spécifique à l'ancien échantillon de 5 000 chansons a été supprimée : elle pouvait écraser les variables d'une nouvelle exécution. Les anciens exports sont conservés sur disque. Les nouveaux exports utilisent le label de l'échantillon courant, par défaut `50songs`.

La section **7** calcule les effectifs et parts par type ainsi que le nombre et la proportion de chansons concernées. La section **7.1** regroupe par `type` et `reference_canon`. Les dénominateurs de prévalence excluent les annotations en échec. Une chanson compte au plus une fois par groupe ; un effectif de références compte les éléments extraits, pas les répétitions des mots dans les paroles.

Les tableaux de fréquences n'affichent que les effectifs **strictement supérieurs à 1**. Les aperçus des CSV canoniques, des correspondances et des fréquences sont limités aux **10 premières lignes**. Les CSV exportés et les dénominateurs des pourcentages restent complets.

Les données et métriques ci-dessous sont écrites dans `export/`, sous le préfixe `R05_political_references_<label>` ; par exemple `50songs`, `1pct` ou `full` (les nuages sont exportés séparément dans `images/`). Les pourcentages fractionnaires sont conservés, par exemple `0.5pct`. Le filtre de longueur reste appliqué mais ne figure plus dans les noms des nouveaux exports :

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

Le prompt est désormais simplifié à trois types. Les résultats de pilotes décrits ci-dessous concernent l'ancienne version à cinq types et ne valident pas cette nouvelle version. Les anciennes sorties du notebook ont été effacées pour éviter toute confusion ; les fichiers exportés sur disque sont conservés. Relancer le pipeline depuis les paramètres avant d'interpréter les nouveaux résultats.

L'extraction vérifie le schéma, la catégorie et la présence de la mention et de l'extrait dans les paroles. L'extrait doit également contenir la mention. Le parseur refuse le contenu supplémentaire après le tableau JSON. Les métadonnées manquantes deviennent `null`, pas des valeurs JSON non standard comme `NaN`.

Chaque référence passe ensuite une vérification sémantique séparée, avec une réponse stricte `OUI` ou `NON`. Un refus déclenche une nouvelle annotation avec retour correctif, jusqu'à deux nouvelles tentatives ; un refus persistant devient un échec explicite par chanson. Aucune référence refusée n'est simplement retirée d'une liste présentée comme valide. Les réponses de vérification tronquées ou mal formées sont également rejetées. Des contrôles positifs et négatifs vérifient ce mécanisme avant l'annotation du corpus.

Le premier test technique sur 50 chansons avait produit 45 succès de format et 66 références, mais une revue a révélé de nombreux faux positifs : ces chiffres ne mesuraient pas la qualité sémantique. Le contrôle séparé a été ajouté pour traiter cette limite. **Il utilise le même modèle : ce n'est pas une validation indépendante ni une garantie de justesse.** Il augmente aussi le nombre de requêtes et la durée. Le rapprochement canonique ne corrige pas les erreurs de classification ; une revue humaine reste nécessaire avant un passage à grande échelle.

Après révision, le même échantillon de **50 chansons** a exécuté les **34 cellules** en **192,8 secondes**, dont **174,4 secondes** d'annotation : **19 chansons ont passé les contrôles**, **31 sont en échec explicite**, et **18 références ont été acceptées automatiquement**. Les neuf exports de données/métriques et les cinq nuages ont été produits. Une relecture des références acceptées révèle encore des erreurs, notamment des artistes classés comme figures politiques. **Ce pilote n'est donc pas validé pour une analyse de corpus à grande échelle.** Le taux d'échec est de 62 % ; les prévalences calculées sur les seuls succès ne doivent pas être interprétées comme une estimation représentative du corpus. Une baisse du nombre de références acceptées ne prouve pas, à elle seule, une amélioration de la précision.

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
