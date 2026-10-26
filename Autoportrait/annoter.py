#!/usr/bin/env python3
"""Annotation « autoportrait » des chansons du corpus LRFAF par un LLM servi avec vLLM.

Le script interroge un serveur compatible OpenAI (par exemple `vllm serve <modèle>`),
une chanson par requête. Le modèle reçoit la définition de l'autoportrait (consigne.md)
et répond « autoportrait », « pas_autoportrait » ou « je_ne_sais_pas », avec une phrase de
justification. Le script n'utilise que la bibliothèque standard de Python et reprend là où
il s'est arrêté si on le relance.

    python annoter.py --corpus /chemin/corpus.csv --echantillon chansons_test_200.csv
    python annoter.py --corpus /chemin/corpus.csv

Voir 00_LISEZ-MOI.md pour le détail.
"""
import argparse
import csv
import hashlib
import json
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ICI = Path(__file__).resolve().parent

# Le modèle applique la définition de la consigne et choisit lui-même l'une de ces trois étiquettes
ETIQUETTES = ["autoportrait", "je_ne_sais_pas", "pas_autoportrait"]
SCHEMA = {
    "type": "object",
    "properties": {
        "justification": {"type": "string"},
        "etiquette": {"type": "string", "enum": ETIQUETTES},
    },
    "required": ["justification", "etiquette"],
    "additionalProperties": False,
}
# Façons de forcer une sortie JSON valide, de la plus standard à la plus ancienne selon la version de vLLM
CONTRAINTES = {
    "json_schema": {"response_format": {"type": "json_schema", "json_schema": {"name": "annotation", "schema": SCHEMA, "strict": True}}},
    "structured_outputs": {"structured_outputs": {"json": SCHEMA}},
    "guided_json": {"guided_json": SCHEMA},
    "aucune": {},
}

# Résidus de la page Genius présents dans les paroles : une publicité de billetterie (3 489 chansons,
# parfois collée à un vers sur la même ligne) et un compteur collé à la fin du texte
PUBLICITE = re.compile(r"See (?:(?!See ).){1,80}? Live\s*Get tickets as low as \$\d+")
CHIFFRE_FINAL = re.compile(r"(?<=[^\d\s])\d{1,3}$")


def nettoyer(paroles):
    """Retire les résidus de Genius ; les balises de section ([Couplet 1 : …]) sont conservées."""
    texte = PUBLICITE.sub("\n", paroles).rstrip()
    texte = CHIFFRE_FINAL.sub("", texte)
    texte = re.sub(r"[ \t]+\n", "\n", texte)
    return re.sub(r"\n{3,}", "\n\n", texte).strip()


def lire_ids(chemin):
    with open(chemin, newline="", encoding="utf-8-sig") as f:
        return {int(ligne["source_row_index"]) for ligne in csv.DictReader(f)}


def lire_corpus(chemin, ids):
    """Lit corpus.csv ; source_row_index est la position de la ligne, en partant de 0."""
    csv.field_size_limit(sys.maxsize)
    chansons = {}
    with open(chemin, newline="", encoding="utf-8") as f:
        lecteur = csv.reader(f)
        colonne = {nom: i for i, nom in enumerate(next(lecteur))}
        for position, ligne in enumerate(lecteur):
            if ids is not None and position not in ids:
                continue
            paroles = ligne[colonne["lyrics"]]
            if not paroles or paroles == "NA":
                continue
            chansons[position] = {
                "artiste": ligne[colonne["artist"]].replace("​", "").strip(),
                "titre": ligne[colonne["title"]],
                "annee": "" if ligne[colonne["year"]] == "NA" else ligne[colonne["year"]],
                "paroles": paroles,
            }
    return chansons


# Connexion directe au serveur, sans passer par les réglages de proxy du système
# (sur macOS, les relire à chaque requête ralentit beaucoup un envoi en parallèle)
OUVREUR = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def appeler(url, corps, cle, delai):
    """Envoie une requête au serveur (GET si `corps` est vide) et renvoie le JSON de la réponse."""
    requete = urllib.request.Request(
        url, data=json.dumps(corps).encode("utf-8") if corps is not None else None,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {cle}"})
    with OUVREUR.open(requete, timeout=delai) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


def extraire(contenu):
    """Lit l'objet JSON renvoyé par le modèle, même entouré de texte, et vérifie ses valeurs."""
    fin = contenu.rfind("}")
    objet = None
    debut = contenu.rfind("{", 0, fin)
    while debut >= 0 and objet is None:
        try:
            objet = json.loads(contenu[debut:fin + 1])
        except json.JSONDecodeError:
            debut = contenu.rfind("{", 0, debut)
    if not isinstance(objet, dict):
        raise ValueError("pas d'objet JSON dans la réponse")
    if objet.get("etiquette") not in ETIQUETTES:
        raise ValueError(f"valeur de « etiquette » inconnue : {objet.get('etiquette')!r}")
    return {"etiquette": objet["etiquette"], "justification": str(objet.get("justification", "")).strip()}


def messages(consigne, paroles, sans_system):
    texte = "Paroles de la chanson :\n\n" + nettoyer(paroles)
    if sans_system:   # pour les modèles dont le gabarit de conversation n'a pas de rôle « system »
        return [{"role": "user", "content": consigne + "\n\n---\n\n" + texte}]
    return [{"role": "system", "content": consigne}, {"role": "user", "content": texte}]


def annoter(paroles, args, consigne, contrainte):
    """Annote une chanson ; renvoie l'étiquette, la justification et, en cas d'échec, l'erreur."""
    erreur = ""
    for essai in range(args.essais):
        corps = {
            "model": args.modele,
            "messages": messages(consigne, paroles, args.sans_system),
            "max_tokens": args.max_tokens,
            # Premier essai déterministe ; les suivants varient un peu pour ne pas répéter la même réponse invalide
            "temperature": args.temperature if essai == 0 else max(args.temperature, 0.3),
            "seed": essai,
            **CONTRAINTES[contrainte],
        }
        contenu = ""
        try:
            reponse = appeler(args.url + "/chat/completions", corps, args.cle, args.timeout)
            contenu = reponse["choices"][0]["message"].get("content") or ""
            return {**extraire(contenu), "erreur": ""}
        except urllib.error.HTTPError as e:
            erreur = f"HTTP {e.code} : {e.read().decode('utf-8', 'replace')[:300]}"
            if e.code == 400:   # requête refusée (texte trop long pour le modèle, par exemple) : réessayer ne change rien
                break
        except Exception as e:   # panne réseau, délai dépassé, réponse illisible
            erreur = f"{type(e).__name__} : {e}" + (f" | réponse : {contenu[:200]!r}" if contenu else "")
        if essai < args.essais - 1:
            time.sleep(2 * (essai + 1))
    return {"etiquette": "", "justification": "", "erreur": erreur}


def choisir_contrainte(args, consigne):
    """Cherche la façon de forcer le JSON que ce serveur accepte, avec un texte d'essai."""
    if args.contrainte != "auto":
        return args.contrainte
    essai = "Je me présente : je suis un texte d'essai, écrit pour vérifier que le serveur répond au bon format."
    for nom in ("json_schema", "structured_outputs", "guided_json"):
        corps = {"model": args.modele, "messages": messages(consigne, essai, args.sans_system),
                 "max_tokens": args.max_tokens, "temperature": 0, **CONTRAINTES[nom]}
        try:
            reponse = appeler(args.url + "/chat/completions", corps, args.cle, args.timeout)
            extraire(reponse["choices"][0]["message"].get("content") or "")
            return nom
        except urllib.error.HTTPError as e:
            if e.code != 400:
                sys.exit(f"Le serveur a répondu HTTP {e.code} : {e.read().decode('utf-8', 'replace')[:300]}")
        except ValueError:
            pass   # format accepté mais réponse non conforme : on essaie le suivant
    return "aucune"


def charger_resultats(chemin):
    """Relit les annotations déjà écrites ; la dernière ligne d'une chanson l'emporte."""
    resultats = {}
    if chemin.exists():
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                if ligne.strip():
                    r = json.loads(ligne)
                    resultats[r["source_row_index"]] = r
    return resultats


def exporter_csv(resultats, chansons, chemin):
    champs = ["source_row_index", "artiste", "titre", "annee", "etiquette", "justification", "modele", "consigne", "erreur"]
    with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
        sortie = csv.DictWriter(f, fieldnames=champs, extrasaction="ignore")
        sortie.writeheader()
        for position in sorted(resultats):
            meta = chansons.get(position, {})
            sortie.writerow({**resultats[position], "artiste": meta.get("artiste", ""), "titre": meta.get("titre", ""), "annee": meta.get("annee", "")})


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--corpus", required=True, help="chemin de corpus.csv")
    p.add_argument("--ids", default=str(ICI / "chansons_corpus_84155.csv"), help="chansons à annoter (colonne source_row_index) ; « tout » pour tout le corpus")
    p.add_argument("--echantillon", help="restreindre à ces chansons (colonne source_row_index), par exemple chansons_test_200.csv")
    p.add_argument("--limite", type=int, help="n'annoter que les N premières chansons restantes")
    p.add_argument("--url", default="http://localhost:8000/v1", help="adresse du serveur vLLM")
    p.add_argument("--cle", default="EMPTY", help="clé d'API du serveur, s'il en demande une")
    p.add_argument("--modele", help="nom du modèle servi (par défaut : le premier que le serveur annonce)")
    p.add_argument("--consigne", default=str(ICI / "consigne.md"))
    p.add_argument("--sortie", default=str(ICI / "resultats"), help="dossier des résultats")
    p.add_argument("--concurrence", type=int, default=32, help="requêtes envoyées en parallèle")
    p.add_argument("--contrainte", default="auto", choices=["auto", *CONTRAINTES], help="façon de forcer une sortie JSON valide")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--max-tokens", type=int, default=300)
    p.add_argument("--essais", type=int, default=3, help="tentatives par chanson")
    p.add_argument("--timeout", type=float, default=300, help="délai par requête, en secondes")
    p.add_argument("--sans-system", action="store_true", help="mettre la consigne dans le message utilisateur")
    p.add_argument("--apercu", action="store_true", help="afficher ce qui est envoyé pour la première chanson, puis quitter")
    args = p.parse_args()
    args.url = args.url.rstrip("/")

    consigne = Path(args.consigne).read_text(encoding="utf-8").strip()
    version = f"{Path(args.consigne).stem}-{hashlib.sha1(consigne.encode('utf-8')).hexdigest()[:8]}"

    ids = None if args.ids == "tout" else lire_ids(args.ids)
    if args.echantillon:
        echantillon = lire_ids(args.echantillon)
        ids = echantillon if ids is None else ids & echantillon
    print(f"Lecture de {args.corpus}…")
    chansons = lire_corpus(args.corpus, ids)
    print(f"{len(chansons)} chansons dans le périmètre.")

    if args.apercu:
        position = min(chansons)
        for message in messages(consigne, chansons[position]["paroles"], args.sans_system):
            lignes = message["content"].splitlines()
            print(f"\n--- {message['role']} ({len(message['content'])} caractères)\n" + "\n".join(lignes[:25]) + ("\n[…]" if len(lignes) > 25 else ""))
        return

    try:
        modeles = [m["id"] for m in appeler(args.url + "/models", None, args.cle, 30)["data"]]
    except Exception as e:
        sys.exit(f"Serveur injoignable à {args.url} ({e}). Le lancer d'abord, par exemple : vllm serve <modèle> --port 8000")
    if not args.modele:
        args.modele = modeles[0]
    elif args.modele not in modeles:
        sys.exit(f"Le serveur ne sert pas « {args.modele} ». Modèles disponibles : {', '.join(modeles)}")

    dossier = Path(args.sortie)
    dossier.mkdir(parents=True, exist_ok=True)
    base = dossier / ("annotations_" + re.sub(r"[^A-Za-z0-9._-]+", "__", args.modele))
    journal, tableau = base.with_suffix(".jsonl"), base.with_suffix(".csv")

    resultats = charger_resultats(journal)
    faites = {position for position, r in resultats.items() if not r.get("erreur") and r.get("consigne") == version}
    a_faire = [position for position in sorted(chansons) if position not in faites]
    if args.limite:
        a_faire = a_faire[:args.limite]
    print(f"Modèle : {args.modele} · consigne : {version}")
    print(f"Déjà annotées : {len(faites & set(chansons))} · à annoter maintenant : {len(a_faire)}")
    if not a_faire:
        exporter_csv(resultats, chansons, tableau)
        print(f"Rien à faire. Tableau : {tableau}")
        return

    contrainte = choisir_contrainte(args, consigne)
    print(f"Sortie JSON forcée par : {contrainte}" + ("  (aucune contrainte : les réponses sont seulement vérifiées)" if contrainte == "aucune" else ""))

    verrou = threading.Lock()
    compte = {"faites": 0, "erreurs": 0}
    debut = dernier = time.time()

    def traiter(position):
        r = annoter(chansons[position]["paroles"], args, consigne, contrainte)
        return {"source_row_index": position, **r,
                "modele": args.modele, "consigne": version, "date": time.strftime("%Y-%m-%d %H:%M:%S")}

    executeur = ThreadPoolExecutor(max_workers=args.concurrence)
    try:
        with open(journal, "a", encoding="utf-8") as f:
            taches = [executeur.submit(traiter, position) for position in a_faire]
            for tache in as_completed(taches):
                r = tache.result()
                with verrou:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
                    f.flush()
                    resultats[r["source_row_index"]] = r
                    compte["faites"] += 1
                    compte["erreurs"] += bool(r["erreur"])
                    if time.time() - dernier > 30 or compte["faites"] == len(a_faire):
                        dernier = time.time()
                        debit = compte["faites"] / (dernier - debut)
                        reste = (len(a_faire) - compte["faites"]) / debit / 60 if debit else 0
                        print(f"  {compte['faites']}/{len(a_faire)} · {debit:.1f} chansons/s · reste environ {reste:.0f} min · {compte['erreurs']} erreurs")
    except KeyboardInterrupt:
        executeur.shutdown(wait=False, cancel_futures=True)
        print("\nInterrompu. Relancer la même commande pour reprendre : ce qui est fait est conservé.")
    else:
        executeur.shutdown()

    exporter_csv(resultats, chansons, tableau)
    valides = [r for position, r in resultats.items() if position in chansons and not r.get("erreur")]
    print(f"\n{len(valides)} chansons annotées, {sum(bool(r.get('erreur')) for r in resultats.values())} en erreur (relancer pour les retenter).")
    for etiquette in ETIQUETTES:
        n = sum(r.get("etiquette") == etiquette for r in valides)
        print(f"  {etiquette:17} {n:6}  ({n / max(len(valides), 1):.0%})")
    print(f"Journal : {journal}\nTableau : {tableau}")


if __name__ == "__main__":
    main()
