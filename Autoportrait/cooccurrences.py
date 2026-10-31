"""Structure des cooccurrences d'aspects dans les descriptions d'autoportraits.

Usage :
    python cooccurrences.py <chemin_csv_b> <suffixe>

Exemple :
    python cooccurrences.py data/results/archive_consigne_v1/autoportrait2_qwen_description_8861b.csv 8861

Entrées : le CSV « b » (annotations seules) avec les colonnes indicatrices `aspect_*`.
Sorties :
    - images/autoportrait2_aspects_cooccurrence_<suffixe>.png (figure deux panneaux)
    - images/autoportrait2_aspects_mds_<suffixe>.png (projection MDS 2D)
    - <dossier du CSV>/autoportrait2_qwen_description_<suffixe>_cooccurrence.csv (% de co-citation)
    - <dossier du CSV>/autoportrait2_qwen_description_<suffixe>_phi.csv (coefficients phi)
    - <dossier du CSV>/autoportrait2_qwen_description_<suffixe>_mds.csv (coordonnées MDS)
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

ROSE = "#C48793"
VERT = "#7FBF00"
# Palette hip-hop du dépôt, sur fond clair (cf. étape 5 du notebook).
OR = "#B8860B"
ORANGE = "#FF8C00"
CRAMOISI = "#DC143C"
FOND_AXES = "#FFFDF5"
TEXTE = "#222222"
GRILLE = "#D9D9D9"
FOND = "#FFFFFF"

LIBELLES = {
    "aspect_talent_art": "Talent, art",
    "aspect_origines": "Origines",
    "aspect_caractere_valeurs": "Caractère, valeurs",
    "aspect_argent_reussite": "Argent, réussite",
    "aspect_rue_illegalite": "Rue, illégalité",
    "aspect_failles_emotions": "Failles, émotions",
    "aspect_identite_collective": "Identité collective",
    "aspect_proches": "Proches",
    "aspect_ambitions": "Ambitions",
    "aspect_corps_apparence": "Corps, apparence",
    "aspect_foi_destin": "Foi, destin",
    "aspect_seduction_sexualite": "Séduction, sexualité",
}


def phi_coefficient(x: np.ndarray, y: np.ndarray) -> float:
    n = len(x)
    n11 = float(np.sum((x == 1) & (y == 1)))
    n10 = float(np.sum((x == 1) & (y == 0)))
    n01 = float(np.sum((x == 0) & (y == 1)))
    n00 = float(np.sum((x == 0) & (y == 0)))
    denominateur = np.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
    if denominateur == 0:
        return np.nan
    return (n11 * n00 - n10 * n01) / denominateur


def main() -> None:
    chemin_csv = Path(sys.argv[1])
    suffixe = sys.argv[2]
    racine = Path(__file__).resolve().parent

    df = pd.read_csv(chemin_csv)
    colonnes = [c for c in LIBELLES if c in df.columns]
    frequences = df[colonnes].mean().sort_values(ascending=False)
    ordre = list(frequences.index)
    noms = [LIBELLES[c] for c in ordre]
    n = len(df)
    k = len(ordre)

    cooc = np.zeros((k, k))
    phi = np.zeros((k, k))
    for i, ci in enumerate(ordre):
        for j, cj in enumerate(ordre):
            cooc[i, j] = 100.0 * np.mean((df[ci] == 1) & (df[cj] == 1))
            phi[i, j] = 1.0 if i == j else phi_coefficient(
                df[ci].to_numpy(), df[cj].to_numpy()
            )

    dossier_sortie = chemin_csv.parent
    pd.DataFrame(cooc, index=noms, columns=noms).round(1).to_csv(
        dossier_sortie / f"autoportrait2_qwen_description_{suffixe}_cooccurrence.csv"
    )
    pd.DataFrame(phi, index=noms, columns=noms).round(3).to_csv(
        dossier_sortie / f"autoportrait2_qwen_description_{suffixe}_phi.csv"
    )

    cmap_cooc = LinearSegmentedColormap.from_list("blanc_rose", [FOND, ROSE])
    cmap_phi = LinearSegmentedColormap.from_list("rose_blanc_vert", [ROSE, FOND, VERT])

    fig, axes = plt.subplots(1, 2, figsize=(14.5, 7.2), facecolor=FOND)
    masque = np.triu(np.ones((k, k), dtype=bool))

    for ax, matrice, cmap, vmin, vmax, titre, fmt in (
        (
            axes[0], cooc, cmap_cooc, 0, np.nanmax(np.where(masque, np.nan, cooc)),
            "Co-citation des aspects (% des descriptions)", "{:.0f}",
        ),
        (
            axes[1], phi, cmap_phi, -0.3, 0.3,
            "Association entre aspects (coefficient phi)", "{:+.2f}",
        ),
    ):
        affichee = np.where(masque, np.nan, matrice)
        image = ax.imshow(affichee, cmap=cmap, vmin=vmin, vmax=vmax)
        ax.set_facecolor(FOND)
        ax.set_xticks(range(k), noms, rotation=45, ha="right", fontsize=9, color=TEXTE)
        ax.set_yticks(range(k), noms, fontsize=9, color=TEXTE)
        ax.set_title(titre, fontsize=12, color=TEXTE, pad=12)
        for cote in ax.spines.values():
            cote.set_color(GRILLE)
        ax.tick_params(color=GRILLE)
        for i in range(k):
            for j in range(i):
                ax.text(
                    j, i, fmt.format(matrice[i, j]),
                    ha="center", va="center", fontsize=7.5, color=TEXTE,
                )
        barre = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)
        barre.ax.tick_params(labelsize=8, color=GRILLE, labelcolor=TEXTE)
        barre.outline.set_edgecolor(GRILLE)

    fig.suptitle(
        f"Structure des cooccurrences d'aspects — {n:,} descriptions valides".replace(",", "\u202f"),
        fontsize=13, color=TEXTE,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))

    chemin_image = racine / "images" / f"autoportrait2_aspects_cooccurrence_{suffixe}.png"
    fig.savefig(chemin_image, dpi=200, facecolor=FOND, bbox_inches="tight")
    print(f"Figure : {chemin_image}")

    # Projection MDS 2D (PCoA, Torgerson) sur la dissimilarité 1 - phi ;
    # points proportionnels à la fréquence de citation de chaque aspect.
    # Méthode déterministe, identique à la section 5.2 du notebook.
    dissimilarite = 1.0 - phi
    np.fill_diagonal(dissimilarite, 0.0)
    centrage = np.eye(k) - np.full((k, k), 1.0 / k)
    b_centre = -0.5 * centrage @ (dissimilarite ** 2) @ centrage
    valeurs, vecteurs = np.linalg.eigh(b_centre)
    ordre_axes = np.argsort(valeurs)[::-1]
    valeurs, vecteurs = valeurs[ordre_axes], vecteurs[:, ordre_axes]
    if valeurs[1] <= 0:
        raise ValueError("Moins de deux axes positifs : projection 2D impossible.")
    coordonnees = vecteurs[:, :2] * np.sqrt(valeurs[:2])
    part_plan = valeurs[:2].sum() / valeurs[valeurs > 0].sum()
    # Part des descriptions où l'aspect est principal (premier de la liste).
    principaux = df["aspect_principal"].astype(str)
    cles = {c: c.removeprefix("aspect_") for c in ordre}
    citees_pct = 100.0 * frequences.loc[ordre].to_numpy()
    principales_pct = np.array(
        [100.0 * (principaux == cles[c]).mean() for c in ordre]
    )

    export_mds = pd.DataFrame(
        {
            "aspect": noms,
            "dim1": np.round(coordonnees[:, 0], 4),
            "dim2": np.round(coordonnees[:, 1], 4),
            "frequence_pct": np.round(citees_pct, 1),
            "principal_pct": np.round(principales_pct, 1),
        }
    )
    export_mds.to_csv(
        dossier_sortie / f"autoportrait2_qwen_description_{suffixe}_mds.csv",
        index=False,
    )

    fig2, ax2 = plt.subplots(figsize=(9.5, 7.5), facecolor=FOND)
    ax2.set_facecolor(FOND_AXES)
    ax2.scatter(
        coordonnees[:, 0], coordonnees[:, 1],
        s=citees_pct * 55, c=ORANGE, edgecolors=OR,
        linewidths=0.8, alpha=0.85, zorder=3,
    )
    ax2.scatter(
        coordonnees[:, 0], coordonnees[:, 1],
        s=np.maximum(principales_pct * 55, 4), c=CRAMOISI, edgecolors="none",
        alpha=0.9, zorder=4,
    )
    for i, ((x, y), nom, f) in enumerate(zip(coordonnees, noms, citees_pct)):
        rayon = 0.03 + 0.0011 * np.sqrt(f * 55)
        # Étiquette sous le point si un voisin proche se trouve au-dessus.
        voisin_haut = any(
            j != i and np.hypot(cx - x, cy - y) < 0.15 and cy >= y
            for j, (cx, cy) in enumerate(coordonnees)
        )
        position = (x, y - rayon) if voisin_haut else (x, y + rayon)
        ax2.annotate(
            nom, (x, y), xytext=position,
            ha="center", va="top" if voisin_haut else "bottom",
            fontsize=9.5, color=TEXTE, zorder=5,
        )
    poignees = [
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=ORANGE,
                   markeredgecolor=OR, markersize=10, label="Citée (%)"),
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=CRAMOISI,
                   markeredgecolor="none", markersize=6, label="Principale (%)"),
    ]
    ax2.legend(handles=poignees, loc="upper right", fontsize=9, frameon=False)
    ax2.axhline(0, color=GRILLE, linewidth=0.8, zorder=1)
    ax2.axvline(0, color=GRILLE, linewidth=0.8, zorder=1)
    ax2.grid(color=GRILLE, linewidth=0.5, alpha=0.6, zorder=0)
    ax2.set_title(
        "Projection MDS des aspects (dissimilarité 1 − phi)",
        fontsize=12.5, color=TEXTE, pad=12,
    )
    ax2.set_xlabel("Dimension 1", fontsize=10, color=TEXTE)
    ax2.set_ylabel("Dimension 2", fontsize=10, color=TEXTE)
    for cote in ax2.spines.values():
        cote.set_color(GRILLE)
    ax2.tick_params(colors=TEXTE, labelsize=8)
    ax2.annotate(
        "Surfaces proportionnelles aux parts de chansons : citée (orange),"
        f" principale (cramoisi) — plan : {100 * part_plan:.1f} % de la variance positive",
        xy=(0.5, -0.11), xycoords="axes fraction",
        ha="center", fontsize=8.5, color=TEXTE,
    )
    marge_x = 0.18 * (coordonnees[:, 0].max() - coordonnees[:, 0].min())
    marge_y = 0.18 * (coordonnees[:, 1].max() - coordonnees[:, 1].min())
    ax2.set_xlim(coordonnees[:, 0].min() - marge_x, coordonnees[:, 0].max() + marge_x)
    ax2.set_ylim(coordonnees[:, 1].min() - marge_y, coordonnees[:, 1].max() + marge_y)
    fig2.tight_layout()

    chemin_mds = racine / "images" / f"autoportrait2_aspects_mds_{suffixe}.png"
    fig2.savefig(chemin_mds, dpi=200, facecolor=FOND, bbox_inches="tight")
    print(f"Figure : {chemin_mds}")
    print(f"Variance positive restituée par le plan : {100 * part_plan:.1f} %")
    print(f"CSV : {dossier_sortie}/autoportrait2_qwen_description_{suffixe}_cooccurrence.csv")
    print(f"CSV : {dossier_sortie}/autoportrait2_qwen_description_{suffixe}_phi.csv")

    paires = [
        (noms[i], noms[j], cooc[i, j], phi[i, j])
        for i in range(k) for j in range(i)
    ]
    paires.sort(key=lambda p: p[3], reverse=True)
    print("\nAssociations les plus fortes (phi) :")
    for a, b, c, p in paires[:5]:
        print(f"  {a} × {b} : phi={p:+.3f}, co-citation={c:.1f} %")
    print("Répulsions les plus fortes (phi) :")
    for a, b, c, p in paires[-5:]:
        print(f"  {a} × {b} : phi={p:+.3f}, co-citation={c:.1f} %")


if __name__ == "__main__":
    main()
