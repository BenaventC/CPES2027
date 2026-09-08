---
name: export-organization
description: 'Conventions d''organisation des fichiers produits par les scripts et notebooks de ce projet : scripts/notebooks à la racine, images générées dans images/, tables et CSV de résultats dans result/. Use when saving a figure, exporting a CSV/table, adding a new output file, or setting up folders for a new script/notebook.'
---

# Organisation des exports du projet

## Quand utiliser
- Un chunk de code produit un graphique (matplotlib/seaborn) qui doit être sauvegardé sur disque.
- Un chunk de code exporte une table ou un résumé de données (CSV, etc.).
- Mise en place d'un nouveau script ou notebook qui va générer des fichiers.

## Règles d'organisation
- **Scripts et notebooks** (`.py`, `.ipynb`) restent à la racine du dossier de travail : ne pas les déplacer dans un sous-dossier.
- **Images** (figures matplotlib/seaborn, captures, schémas) vont dans le dossier `images/` à la racine.
- **Résultats tabulaires** (CSV, tables agrégées, exports pour d'autres notebooks) vont dans le dossier `result/` à la racine (jamais `résultats/` — pas d'accent, pas de pluriel).
- Créer ces dossiers avec `Path("images").mkdir(exist_ok=True)` / `Path("result").mkdir(exist_ok=True)` (ou équivalent) en tout début de script/notebook, dans la cellule de configuration.

## Convention de code
Définir les chemins une seule fois en haut du notebook/script, puis les réutiliser :

```python
from pathlib import Path

IMAGES_DIR = Path("images")
RESULT_DIR = Path("result")
IMAGES_DIR.mkdir(exist_ok=True)
RESULT_DIR.mkdir(exist_ok=True)
```

Puis pour chaque figure :

```python
fig.savefig(IMAGES_DIR / "0X_Y_nom_descriptif.png", bbox_inches="tight")
plt.show()
```

Et pour chaque export tabulaire :

```python
output_path = RESULT_DIR / "nom_descriptif.csv"
df_resume.to_csv(output_path)
```

## Conventions de nommage des fichiers
- Préfixer le nom de fichier par le numéro de section/sous-section du notebook qui le produit (ex. `05_1_histogrammes.png`, `08_2_tendances_lissees.png`) pour retrouver facilement l'origine d'un export.
- Utiliser un nom descriptif en français, en minuscules, mots séparés par `_`, sans accents ni espaces.
- Toujours appeler `plt.show()` après `fig.savefig(...)` pour conserver l'affichage inline dans le notebook.

## Vérification avant de livrer
- Aucun fichier `.png`/`.csv` généré par le code n'est écrit à la racine ou ailleurs que dans `images/` ou `result/`.
- Les dossiers `images/` et `result/` sont créés par le code lui-même (pas seulement supposés déjà exister).
