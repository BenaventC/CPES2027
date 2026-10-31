# Article : l'autoportrait dans le rap français

- `article.tex` : article en français, résumé français et abstract anglais.
- `article.pdf` : version compilée.
- `pipeline.mmd` : source Mermaid de la chaîne de traitement.
- `pipeline.pdf` : diagramme vectoriel Mermaid inclus dans l'article.
- `build.sh` : génération du diagramme et compilation.
- `references.bib` : bibliographie BibTeX, avec Beaujour (1980) pour la
  distinction entre autoportrait et autobiographie, Béthune (2011) pour
  l'écriture et les outils du rappeur, et de Courson (2024) pour la
  construction du corpus LRFAF à partir de Genius.
- `annexe_detection.tex` et `annexe_description.tex` : consignes intégrales,
  adaptées à la typographie LaTeX depuis les versions actuelles du dépôt.

La partie théorique et la présentation des consignes distinguent les apports
de Beaujour et de Béthune ; l'ancrage théorique cite la formule de
*Miroirs d'encre* : « Je ne vous raconterai pas ce que j'ai fait :
je vais vous dire qui je suis ».
La conclusion comporte un paragraphe « Disponibilité du code et des données »
renvoyant au dépôt public
[BenaventC/CPES2027, dossier Autoportrait](https://github.com/BenaventC/CPES2027/tree/main/Autoportrait)
(notebooks, consignes et figures ; hors données locales et résultats
individuels non publiés).
Les annexes documentent les consignes actuelles, sans certifier leur identité
avec les versions employées dans la campagne. Leur ajout allonge le document
au-delà des cinq pages de la première version.
Les remerciements et la déclaration sur l'usage de l'intelligence
artificielle figurent sur la première page, sous le bloc de titre,
en petit corps. Les consignes en annexe sont composées en
`\footnotesize`.

Les deux figures originales sont incluses par des chemins relatifs depuis
`../images/` ; conserver cette organisation lors de la compilation.
Leurs couleurs originales sont préservées. Seule la projection MDS
(`../images/autoportrait2_aspects_mds_8861.png`) est affichée dans
l'article : double point par aspect — surface orange proportionnelle à la
part de citation, disque cramoisi à la part de premier rang — dans la
palette hip-hop du dépôt sur fond clair. La figure des matrices de
cooccurrences (`../images/autoportrait2_aspects_cooccurrence_8861.png`)
reste disponible comme pièce complémentaire. Les deux sont produites par
`../cooccurrences.py`, aligné sur la section 5.2 du notebook. Le diagramme Mermaid
utilise un fond blanc et des bordures sombres.

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

Les valeurs sont calculées à partir des exports locaux du 28 octobre 2026,
archivés dans `../data/results/archive_consigne_v1/` en attendant les
résultats de la campagne en cours (consigne révisée) :

- `autoportrait_qwen_annotation_12938.csv` ;
- `autoportrait2_qwen_description_8861b.csv` ;
- `autoportrait2_qwen_description_8861_aspects.csv` ;
- `autoportrait2_qwen_description_8861_aspects_par_annee.csv` ;
- `autoportrait2_qwen_description_8861_cooccurrence.csv`,
  `autoportrait2_qwen_description_8861_phi.csv` et
  `autoportrait2_qwen_description_8861_mds.csv`, produits par
  `../cooccurrences.py`.

Le dénominateur des figures est **8 856 descriptions valides**, malgré le
suffixe `8861` qui correspond au nombre de chansons soumises à la phase 2.
Le document explicite les erreurs, le plan stratifié, le lissage pondéré,
les limites de validation et le décalage entre la consigne actuelle et
la fréquence des listes de quatre aspects. Aucune inférence GPU n'est relancée.
Les données de résultats individuelles ne sont pas copiées ici.
