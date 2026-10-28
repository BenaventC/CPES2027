# Article : l'autoportrait dans le rap français

- `article.tex` : article en français, résumé français et abstract anglais.
- `article.pdf` : version compilée.
- `pipeline.mmd` : source Mermaid de la chaîne de traitement.
- `pipeline.pdf` : diagramme vectoriel Mermaid inclus dans l'article.
- `build.sh` : génération du diagramme et compilation.
- `references.bib` : bibliographie BibTeX, avec Béthune (2011).
- `annexe_detection.tex` et `annexe_description.tex` : consignes intégrales,
  adaptées à la typographie LaTeX depuis les versions actuelles du dépôt.

La méthode résume les deux consignes et cite Béthune avant leur présentation.
Les annexes documentent les consignes actuelles, sans certifier leur identité
avec les versions employées dans la campagne. Leur ajout allonge le document
au-delà des cinq pages de la première version.

Les deux figures originales sont incluses par des chemins relatifs depuis
`../images/` ; conserver cette organisation lors de la compilation.
Leurs couleurs originales sont préservées. Le nouveau diagramme utilise
le rose ancien et le vert chartreuse de la palette du projet.

## Compilation

Depuis ce dossier :

```bash
bash build.sh
```

Le script demande Tectonic (qui lance BibTeX automatiquement), ou `pdflatex`
avec `bibtex` et notamment les paquets `natbib`,
`babel-french`, `lmodern`, `microtype`, `geometry`, `caption` et `fancyhdr`.
Pour modifier et régénérer le diagramme, installer aussi Mermaid CLI
(`@mermaid-js/mermaid-cli`, version utilisée : 11.12.0).
Sans Mermaid CLI, le script réutilise explicitement le PDF fourni :
après modification de `pipeline.mmd`, le régénérer avant compilation.
Le navigateur local de Mermaid doit être compatible avec les règles
de sécurité de l'environnement.

## Périmètre scientifique

Les valeurs sont calculées à partir des exports locaux du 28 octobre 2026 :

- `../data/results/autoportrait_qwen_annotation_12938.csv` ;
- `../data/results/autoportrait2_qwen_description_8861b.csv` ;
- `../data/results/autoportrait2_qwen_description_8861_aspects.csv` ;
- `../data/results/autoportrait2_qwen_description_8861_aspects_par_annee.csv`.

Le dénominateur des figures est **8 856 descriptions valides**, malgré le
suffixe `8861` qui correspond au nombre de chansons soumises à la phase 2.
Le document explicite les erreurs, le plan stratifié, le lissage pondéré,
les limites de validation et le décalage entre la consigne actuelle et
la fréquence des listes de quatre aspects. Aucune inférence GPU n'est relancée.
Les données de résultats individuelles ne sont pas copiées ici.
