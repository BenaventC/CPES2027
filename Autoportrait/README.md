# Annotation du corpus de rap avec Qwen3-32B

Le carnet [autoportrait_qwen3_32b.ipynb](autoportrait_qwen3_32b.ipynb)
se concentre sur **l'annotation de [Rap/corpus.csv](../corpus.csv)**
avec **Qwen/Qwen3-32B en mode raisonnement**, sur un **corpus d'étude
stratifié par année** (12 938 chansons, voir ci-dessous). `taille_echantillon`
annote ce corpus d'étude entier (`None`) ou un petit échantillon tiré dedans
pour un test, sans pilote préalable ni approbation.
Le réglage actuel est un test de **220 chansons**. Il ne fait plus de comparaison entre modèles
et ne dépend plus de l'ancien échantillon de 200 chansons.

## Données et consigne

- Le corpus doit comporter les colonnes `artist`, `title`, `year` et
  `lyrics`. Il reste local.
- `source_row_index` est la position de la ligne de données, à partir
  de zéro, dans le corpus ; ce n'est pas un `document_id`.
- Toutes les chansons avec des paroles exploitables peuvent être sélectionnées.
  Les textes vides ou égaux à `NA`, ainsi que les textes devenus vides
  après nettoyage, sont exclus. Aucun filtre de longueur ni aucune
  troncature ne sont appliqués.
- [consigne.md](consigne.md) définit les trois catégories :
  `autoportrait`, `pas_autoportrait`, `je_ne_sais_pas`.
- [annoter.py](annoter.py) fournit la lecture du corpus, le nettoyage,
  les messages et le schéma JSON communs.

## Exécution

Utiliser un noyau Python avec les dépendances de
[requirements.txt](requirements.txt) :

```bash
python -m pip install -r requirements.txt
```

Le noyau est un client CPU. L'inférence utilise deux instances vLLM locales
servant chacune `Qwen/Qwen3-32B` avec `--reasoning-parser qwen3` :
GPU physique 1 sur `http://127.0.0.1:8016/v1` et GPU physique 2 sur
`http://127.0.0.1:8017/v1`. `QWEN_BASE_URLS` configure une liste d'URL
séparées par des virgules. Sans cette variable, `QWEN_BASE_URL` reste
compatible pour une seule instance ; sinon les deux adresses ci-dessus
sont utilisées. `QWEN_API_KEY` configure une clé commune. Le carnet ne démarre aucun
serveur et ne télécharge aucun modèle.

Une erreur `Connection refused` au contrôle `/v1/models` signifie que
la connexion au serveur est refusée : vérifier qu'il est démarré, que
son chargement est terminé et que l'adresse et le port sont corrects.
Ce n'est pas une erreur du tirage de l'échantillon. Après démarrage,
vérifier `/v1/models` sur chaque serveur, puis relancer la dernière cellule.
Un serveur arrêté pour libérer le GPU doit être redémarré avant une
nouvelle inférence ; les réussites déjà journalisées restent disponibles.

**Avant tout démarrage du serveur**, vérifier avec `nvidia-smi` la mémoire,
l'activité et les processus de chaque GPU, puis choisir un GPU libre avec
`CUDA_VISIBLE_DEVICES`. Ne pas interrompre les processus d'autres utilisateurs.
Le serveur doit disposer d'un contexte suffisant pour les paroles
et les 8192 tokens de sortie, raisonnement compris.

Exécuter les cellules dans l'ordre depuis la racine du dépôt, `Rap/`
ou `Rap/Autoportrait/` :

0. **Configuration** : en tête de la première cellule, vérifier les strates
   puis choisir `taille_echantillon = None` pour annoter tout le corpus
   d'étude stratifié, ou un entier (220 actuellement) pour un test tiré
   dans ce corpus d'étude.
1. **Chargement du corpus** : lecture et nettoyage de toute la base.
2. **Constitution du corpus d'étude stratifié** : tirage par année et
   tableau du nombre de chansons par année.
3. **Échantillonnage : test ou corpus complet** dans le corpus d'étude.
4. **Annotation** : client vLLM (4.1), journal et exports (4.2), puis
   lancement de l'annotation de la sélection (4.3).

Les étapes 1 à 3 ne lancent aucune inférence ; seule la cellule 4.3
interroge le modèle. Examiner ensuite les décisions, justifications et
raisonnements exportés.

### Corpus d'étude stratifié

Le corpus étudié est constitué à partir des 84 821 chansons exploitables
(paroles non vides après nettoyage), selon la colonne `year` :

- avant 2004 (`annee_exhaustive_avant = 2004`) : **toutes** les chansons,
  soit 2 438 chansons de 1990 à 2003 ;
- de 2004 à 2024 : **500 chansons par année** (`chansons_par_annee = 500`),
  tirées sans remise avec la graine `42 + année` (chaque année en compte
  au moins 524) ;
- écartées : les chansons sans année (`NA`, 9 594), 2025 (année incomplète)
  et 1905 (date aberrante), via `annees_exclues = {1905, 2025}`.

Total : **12 938 chansons**, 35 années. Les années anciennes sont
volontairement sur-représentées : une proportion globale calculée sur ce
corpus d'étude doit être repondérée par les effectifs réels des années
(colonne `chansons_exploitables` du tableau par année) ; les comparaisons
année par année restent directement lisibles.

`taille_echantillon = None` annote les 12 938 chansons (environ 3 h 30 à
1 chanson/s). Un entier tire ce nombre de chansons au hasard (graine 42)
**dans le corpus d'étude stratifié**, pour un test ; ce petit échantillon
n'est pas lui-même stratifié. Une taille non positive ou supérieure au
corpus d'étude est refusée. Les chansons sont remises dans l'ordre du
corpus. Aucun autre paramètre d'autorisation n'est nécessaire. Vérifier
ce réglage avant d'exécuter.

La préparation lit tout le corpus en mémoire avant de constituer le
corpus d'étude.

Les réglages principaux sont **en tête de la première cellule de code**
(bloc « PARAMÈTRES À RÉGLER ») : les strates (`annee_exhaustive_avant`,
`chansons_par_annee`, `annees_exclues`), `taille_echantillon`,
`workers_par_gpu` et `taille_lot`. Le modèle utilise une température de 0, **`workers_par_gpu=12`
requêtes simultanées par serveur (donc par GPU), soit 24 workers au total**
avec deux GPU. Ce nombre doit rester inférieur ou égal à `--max-num-seqs`
du serveur vLLM, sinon les requêtes en trop attendent sans gain de vitesse.
Les deux serveurs sont lancés avec `--max-num-seqs 12` (GPU 1 → port 8016,
GPU 2 → port 8017) ; pour passer à 16 workers par GPU, il faut les relancer
avec `--max-num-seqs 16`.
Les autres réglages : des lots de
128 tâches, un délai de 600 s par requête et deux tentatives au maximum.
La taille des lots limite les tâches en mémoire ; chaque chanson garde
sa propre requête. `taille_echantillon` détermine le nombre total de
chansons traitées ; `taille_lot` ne change pas ce nombre.

Une file de créneaux partagée distribue les chansons aux serveurs disponibles,
sans partager un modèle entre GPU ni imposer deux moitiés fixes du corpus.
Un seul client écrit le journal et les exports ; la colonne `serveur`
trace l'instance utilisée. Tous les serveurs configurés sont vérifiés
avant une nouvelle inférence. Les tentatives d'une chanson restent sur
la même instance et aucun serveur absent n'est ignoré silencieusement.
Réexécuter la configuration, le client et le pipeline avant l'annotation
pour remplacer les anciennes fonctions dans le noyau Jupyter.
Ne pas modifier la configuration pendant qu'une annotation est en cours.
Les deux instances doivent utiliser les mêmes poids et réglages serveur ;
le contrôle du nom du modèle seul ne garantit pas cette identité.

## Validation et reprise

Chaque réussite exige un raisonnement séparé non vide (`reasoning`
ou `reasoning_content`) et un JSON final strictement valide. Le raisonnement
est conservé dans la colonne `raisonnement`, distincte de `justification`.
Une panne réseau, un dépassement de contexte ou une génération tronquée
reste une erreur technique, jamais une décision `je_ne_sais_pas`.

Les journaux JSONL sont synchronisés sur disque après chaque réponse.
Leur empreinte distingue les configurations et les sélections.
Une relance reprend les réussites compatibles et retente les erreurs.
Une reprise entièrement en cache ne nécessite ni serveur ni GPU.
Les échantillons et le corpus ont des journaux distingués par leur périmètre
et leur empreinte.

Un verrou empêche deux lots de même taille d'écrire simultanément les
mêmes exports. Les fichiers de verrouillage et caches ne sont pas versionnés.
En cas d'erreurs persistantes, les exports sont conservés et la cellule
signale explicitement que le lot n'est pas entièrement réussi.

## Sorties

Dans [data/results/](data/results/) :

- `autoportrait_qwen_annotation_{n}.csv` et `.json` ;
- `autoportrait_qwen_annotation_{n}_erreurs.csv` ;
- `corpus_etude_stratifie.csv` : le corpus d'étude stratifié (12 938
  chansons, environ 38 Mo), produit à l'étape 2 : `source_row_index`,
  `artiste`, `titre`, `annee`, `strate` (`exhaustive` avant 2004, `tirage`
  ensuite), `mots_nettoyes` et `paroles` nettoyées. **Contient les paroles** :
  donnée locale à ne pas diffuser, exclue de git par `.gitignore` ;
- `corpus_chansons_par_annee.csv` : tableau produit à l'étape 2,
  sur **toute la base `corpus.csv`** (pas seulement l'échantillon) : nombre
  de chansons par année, ligne `NA` pour les années absentes, puis `Total`.
  Colonnes `chansons_base` (toutes les lignes), `chansons_exploitables`
  (paroles non vides après nettoyage), `corpus_etude` (effectif
  retenu dans le corpus d'étude) et `part_base` (%). Ne lance aucune
  inférence ;
- les journaux techniques JSONL, avec mode, périmètre et empreinte.

`n` est le **nombre de chansons sélectionnées, erreurs comprises** :
220 pour le test actuel, 12 938 pour le corpus d'étude complet (`None`).
Les lignes suivent l'ordre du corpus. Un nouveau lot de même taille
remplace les exports lisibles, sans fusionner les journaux d'expériences.
Les paroles ne sont pas recopiées dans les exports.
Les exports CSV/JSON sont produits en fin de traitement, pas après chaque
réponse. En cas d'interruption, ils peuvent être absents ou anciens :
le journal JSONL permet alors la reprise.

Dans [data/performance/](data/performance/) : durées côté client,
débits, reprises, erreurs, couverture du raisonnement et distributions
des catégories parmi les réussites. Ces mesures ne sont ni une précision
de classification ni une mesure du temps ou de la mémoire GPU.
Une relance remplace les métriques du même journal par celles de la
nouvelle session, y compris lors d'une reprise entièrement en cache.
Les métriques indiquent aussi les serveurs et la concurrence par instance.
Un historique **cumulatif** est également conservé dans
`data/performance/perfGPU_autoportrait.csv`, **unique pour toutes les tailles**,
avec une nouvelle ligne par exécution, sans écraser les précédentes.
Ses colonnes sont exactement `date,modele,batch,concurrent,n,chansons/s` :

- `date` : date et heure UTC d'enregistrement ;
- `modele` : nom du modèle ;
- `batch` : taille des lots techniques (`taille_lot`) ;
- `concurrent` : concurrence totale, tous serveurs réunis ;
- `n` : taille totale de la sélection, erreurs comprises ;
- `chansons/s` : chansons nouvellement traitées, erreurs comprises, divisées
  par la durée de la session côté client. Les lignes reprises du cache
  ne sont pas comptées dans ce débit.

Pour une reprise entièrement en cache, `chansons/s` reste vide :
ce n'est pas une nouvelle mesure d'inférence. Les détails de reprise
et d'erreur restent dans les synthèses techniques par journal.
Malgré son nom `perfGPU`, ce fichier ne mesure pas directement le temps GPU.
La première mesure de 100 chansons (114,85 s) a été reprise depuis les
métriques précédemment vérifiées. Sa date UTC exacte n'étant pas disponible,
ce champ reste vide ; les prochaines exécutions le renseigneront.
La nouvelle version multi-serveurs crée une empreinte distincte :
les anciens journaux sont conservés sans être repris comme une mesure
du débit sur deux GPU.

## Résultats antérieurs conservés

Les anciens résultats et journaux restent sur disque. Un nouveau tirage
de 10 chansons remplace l'export lisible de 10 lignes : son nom seul
ne permet donc pas d'identifier une expérience historique. Le champ
`empreinte` des résultats et les noms des journaux permettent de distinguer
les sélections. Aucun essai préalable n'est imposé avant de choisir `None`.
Les journaux du corpus d'étude portent le périmètre `strates` (complet) ou
`strates_test` (petit échantillon) ; les anciens tirages faits dans tout le
corpus ne sont pas réutilisés, car la sélection fait partie de l'empreinte.

## Phase 2 : description des autoportraits (consigne A)

Le carnet [autoportrait2_qwen3_32b.ipynb](autoportrait2_qwen3_32b.ipynb)
exploite le **sous-ensemble AUTOPORTRAIT** produit par la phase 1. Il décrit
chaque autoportrait selon [consigne_A_description.md](consigne_A_description.md),
avec une réponse conforme à [schema_A_description.json](schema_A_description.json) :

- `registre` : `egotrip`, `introspection`, `manifeste` ou `mixte` ;
- `aspects` : 1 à 4 parmi 12, ordonnés du plus au moins important ;
- `temporalite` : `present`, `passe`, `trajectoire` ou `avenir` ;
- `demarcation` : figures auxquelles il s'oppose (liste vide possible) ;
- `regard_des_autres` : `oui` ou `non` ;
- `justification`.

Plan du carnet :

0. configuration ;
1. chargement du sous-ensemble ;
2. échantillonnage, test ou complet ;
3. annotation ;
4. synthèse.

Paramètres, en tête de la première cellule :

- `n_source` : lot de phase 1 lu dans `autoportrait_qwen_annotation_{n_source}.csv`.
  `12938` correspond au corpus d'étude complet, disponible une fois la campagne de phase 1 terminée.
  Un lot déjà terminé, par exemple `1024` (696 autoportraits), permet un essai avant.
- `taille_echantillon` : `10` par défaut pour les mises au point, `None` pour tout le sous-ensemble.
- `workers_par_gpu` et `taille_lot` : même rôle qu'en phase 1.

Fonctionnement :

- Seules les chansons `etiquette == "autoportrait"` avec `statut == "ok"` sont gardées.
- Les paroles sont relues dans `corpus.csv` par `source_row_index`. Le carnet vérifie
  que l'artiste et le titre correspondent à ceux de la phase 1, puis applique le même nettoyage.
- Mêmes serveurs vLLM et mode raisonnement qu'en phase 1.
- xgrammar (vLLM) refuse le mot-clé `uniqueItems`. Le serveur reçoit donc le schéma sans ce mot-clé,
  et l'unicité des listes est vérifiée par le client avec le reste du schéma
  (valeurs autorisées, 1 à 4 aspects, clés exactes).

Sorties :

- `data/results/autoportrait2_qwen_description_{n}.csv` : listes jointes par `|`,
  `aspect_principal`, indicatrices `aspect_*` et `demarcation_*`.
- `data/results/autoportrait2_qwen_description_{n}b.csv` : version « b », annotations seules (lignes `ok`,
  sans raisonnement, statut ni colonnes techniques ; 30 colonnes). C'est le fichier des statistiques.
- `data/results/autoportrait2_qwen_description_{n}.json`, `_erreurs.csv` et `_distributions.csv` (synthèse).
- Le journal de reprise `autoportrait2_qwen32_reason_{perimetre}_n{n}_{empreinte}.jsonl`.
- `data/performance/perfGPU_autoportrait2.csv` : performances cumulées,
  avec les mêmes colonnes que la phase 1 (`date,modele,batch,concurrent,n,chansons/s`).

Premier essai réel : 10 autoportraits tirés du lot 1024, 10 descriptions valides.
L'essai a tourné à environ 0,33 chanson/s, en partageant les serveurs avec la campagne de phase 1 alors en cours.

Les étapes 5 et 6 lisent la version « b » `data/results/autoportrait2_qwen_description_{n_analyse}b.csv` (`n_analyse = 8861` dans la première cellule, valeur par défaut si la configuration n'a pas tourné). L'étape 5 est autonome ; l'étape 6 demande seulement l'étape 5 : ni annotation ni synthèse à relancer.

Étape 5 du carnet, statistiques des aspects : une figure en barres horizontales montre, pour chaque aspect, la part des chansons qui le citent (orange) et la part où il est l'aspect principal (cramoisi), dans la palette hip-hop du dépôt sur fond clair, ainsi que la répartition du nombre d'aspects par chanson. Exports :

- `data/results/autoportrait2_qwen_description_{n}_aspects.csv` ;
- `images/autoportrait2_aspects_{n}.png`.

Étape 6 du carnet, évolution des aspects : douze panneaux, un par aspect, montrent la part annuelle des autoportraits qui citent l'aspect (points), sa moyenne mobile centrée sur 5 ans (`fenetre_lissage`) et celle de l'aspect principal. Le lissage cumule les effectifs de la fenêtre au lieu de moyenner les pourcentages. Un tableau compare les périodes 1990–2003, 2004–2013 et 2014–2024. Exports :

- `data/results/autoportrait2_qwen_description_{n}_aspects_par_annee.csv` ;
- `images/autoportrait2_aspects_evolution_{n}.png`.
