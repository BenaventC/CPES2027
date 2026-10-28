# Annotation du corpus de rap avec Qwen3-32B

Le carnet [autoportrait_qwen3_32b.ipynb](autoportrait_qwen3_32b.ipynb)
se concentre sur **l'annotation de [Rap/corpus.csv](../corpus.csv)**
avec **Qwen/Qwen3-32B en mode raisonnement**. Un seul paramètre choisit
un échantillon ou la totalité, sans pilote préalable ni approbation.
Le réglage actuel est **100 chansons**. Il ne fait plus de comparaison entre modèles
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

1. Choisir `taille_echantillon = 100` (réglage actuel), un autre entier positif
   pour cet effectif, ou `taille_echantillon = None` pour le corpus entier.
2. Exécuter les cellules dans l'ordre : préparation, client, pipeline,
   puis annotation directe de la sélection.
3. Examiner les décisions, justifications et raisonnements exportés.

Le tirage est sans remise, reproductible avec la graine 42, puis remis
dans l'ordre du corpus. Une taille supérieure au corpus ou non positive
est refusée. Avec `None`, aucun tirage n'est effectué et la dernière cellule
traite directement tout le corpus exploitable. Aucun autre paramètre
d'autorisation n'est nécessaire. Vérifier ce réglage avant d'exécuter.

La préparation lit tout le corpus en mémoire, même lorsque seulement
les 100 chansons de l'échantillon actuel seront ensuite sélectionnées.

Le modèle utilise une température de 0, au plus **8 requêtes par serveur,
soit 16 workers au total**, des lots de
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
- les journaux techniques JSONL, avec mode, périmètre et empreinte.

`n` est le **nombre de chansons sélectionnées, erreurs comprises** :
100 actuellement, ou la taille réelle du corpus exploitable avec `None`.
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
`data/performance/perfGPU_autoportrait_{n}.csv`, avec une nouvelle ligne
par exécution, sans écraser les précédentes. Il contient la date UTC,
le périmètre, l'empreinte, la durée totale côté client,
`secondes_par_chanson_session` (durée divisée par les chansons nouvellement
traitées), `chansons_s_session`, les effectifs, les erreurs, les reprises,
les adresses et le nombre de serveurs, ainsi que la concurrence.
`type_execution` distingue `calcul`, `mixte` et `reprise_cache`.
Pour une reprise entièrement en cache, les secondes par chanson restent
vides : ce n'est pas une nouvelle mesure d'inférence. Le ratio global
s/chanson est l'inverse du débit, **pas la latence moyenne d'une requête**,
car plusieurs chansons sont traitées simultanément. Malgré son nom
`perfGPU`, ce fichier mesure le temps côté client, pas le temps GPU.
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
