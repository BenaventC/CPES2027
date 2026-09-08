---
name: notebook-authoring
description: 'Conventions pour rédiger ou modifier des notebooks Jupyter (.ipynb) dans ce projet : structuration en sections/sous-sections, une cellule markdown avant chaque chunk de code, style des commentaires. Use when creating, editing, or reviewing a Jupyter notebook, adding a code cell, or organizing notebook sections.'
---

# Rédaction de notebooks Jupyter

## Quand utiliser
- Création d'un nouveau notebook d'analyse.
- Ajout, modification ou réorganisation de cellules dans un notebook existant.
- Revue d'un notebook pour vérifier qu'il respecte les conventions du projet.

## Structure générale
- Le notebook commence par une cellule markdown de titre (`#`) avec un court paragraphe d'objectifs et un plan numéroté des sections.
- Chaque grande étape de l'analyse correspond à une **section** markdown `##` numérotée (`## 1. ...`, `## 2. ...`).
- Une étape secondaire à l'intérieur d'une section utilise une **sous-section** `###` numérotée (`### 1.1 ...`).
- **Chaque cellule de code est précédée d'une cellule markdown** (section ou sous-section) qui explique :
  - ce que la cellule calcule ou affiche,
  - pourquoi (le rôle dans l'analyse), pas seulement le "quoi".
- Ne jamais enchaîner deux cellules de code sans cellule markdown intermédiaire, sauf si elles appartiennent à un même bloc logique déjà documenté juste avant (ex. plusieurs `print` de contrôle qui suivent directement le chargement).

## Style des commentaires dans le code
- Un commentaire de code ne doit dire que ce que le code ne montre pas déjà (ex. une convention, une raison, un choix arbitraire), jamais reformuler la ligne suivante.
- Une ligne de commentaire max par choix notable, pas de docstring multi-paragraphes pour une opération simple.
- Exemple correct : `# Organisation du projet : scripts à la racine, figures dans images/, tables dans result/`
- Exemple à éviter : `# On importe pandas` au-dessus de `import pandas as pd`.

## Découpage des chunks
- Un chunk de code = une opération ou un groupe d'opérations cohérent (ex. un graphique, une agrégation, un export).
- Séparer les variantes d'une même analyse (histogramme / densité / boxplot, moyennes brutes / standardisées / lissées) en chunks distincts, chacun avec sa propre sous-section.
- Préférer plusieurs petits chunks documentés à un chunk monolithique qui mélange plusieurs analyses.

## Vérification avant de livrer un notebook
- Chaque cellule de code a bien une cellule markdown juste au-dessus.
- La numérotation des sections/sous-sections dans le plan initial correspond à celle utilisée dans les titres.
- Le code a été validé (exécution ou script équivalent en terminal) pour s'assurer qu'il tourne sans erreur avant de considérer le notebook terminé.

## Lien avec les exports
- Voir le skill `export-organization` pour les conventions de sauvegarde des figures et des tables produites par les cellules de code.
