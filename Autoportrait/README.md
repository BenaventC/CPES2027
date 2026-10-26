# Annotation des autoportraits dans le rap

Le carnet [autoportrait_qwen3_32b.ipynb](autoportrait_qwen3_32b.ipynb)
annote 200 chansons avec **Qwen/Qwen3-32B**, puis compare les décisions
avec [reference_claude_200.csv](reference_claude_200.csv).

## Données et consigne

- [chansons_test_200.csv](chansons_test_200.csv) contient les métadonnées,
  les annotations Qwen, leurs justifications et le modèle utilisé.
- `source_row_index` désigne la position de la ligne de données, à partir
  de zéro, dans `../corpus.csv`. Ce corpus reste local et n'est pas inclus.
  `document_id` n'est pas utilisé pour retrouver les paroles.
- [consigne.md](consigne.md) définit les trois catégories :
  `autoportrait`, `pas_autoportrait`, `je_ne_sais_pas`.
- [annoter.py](annoter.py) fournit le nettoyage, les messages et le schéma
  JSON réutilisés par le carnet.

## Exécution

Installer [requirements.txt](requirements.txt) avec le Python du noyau Jupyter :

```bash
python -m pip install -r requirements.txt
```

L'annotation nécessite un serveur vLLM local servant `Qwen/Qwen3-32B`,
par défaut à `http://127.0.0.1:8016/v1`. Les variables `QWEN_BASE_URL`
et `QWEN_API_KEY` permettent de configurer la connexion sans inscrire
de clé dans le carnet. Aucun serveur n'est démarré automatiquement.

Exécuter le pilote, examiner ses justifications, puis activer
`pilote_approuve` et `lancer_les_200` pour annoter tout l'échantillon.
Les journaux JSONL permettent de reprendre les réussites et de retenter
les erreurs. Les fichiers de verrouillage et caches ne sont pas versionnés.

Pour **comparer les annotations déjà enregistrées sans utiliser de GPU**,
exécuter uniquement la cellule des paramètres et la section 6.

## Résultats enregistrés

Le traitement du 26 octobre 2026 utilise une température de 0,
le raisonnement Qwen3 désactivé et 8 requêtes simultanées :

| Décision Qwen | Effectif |
|---|---:|
| Autoportrait | 116 |
| Pas autoportrait | 82 |
| Je ne sais pas | 2 |

Les 200 annotations sont techniquement valides. Le temps mesuré côté
client est d'environ 70 secondes sur un serveur utilisant une H100 NVL.

La comparaison avec Claude donne **158 accords sur 200 (79 %)**,
un **kappa de Cohen non pondéré de 0,608**, un IC de Wald à 95 %
de **[0,518 ; 0,699]** et une valeur p bilatérale de **5,78 × 10⁻²⁷**
pour H₀ : κ = 0.

Les sorties sont séparées dans :

- [data/results/](data/results/) : annotations, journaux de reprise,
  appariements et 42 désaccords avec les deux justifications ;
- [data/performance/](data/performance/) : performances client,
  distributions, tableaux de contingence en effectifs et pourcentages,
  statistiques du kappa.

Claude n'est pas une vérité terrain. Le test porte sur l'accord au-delà
du hasard, pas sur la justesse des décisions. L'intervalle asymptotique
suppose des chansons indépendantes et ne tient pas compte d'un éventuel
regroupement par artiste. Une revue humaine des désaccords reste nécessaire.
