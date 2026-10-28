#!/usr/bin/env python3
"""Generate political-reference charts using a manually reviewed affiliation map.

The chart encodes an editorial classification, not an objective property of an
entity. Unmapped and ambiguous references remain neutral grey.

Usage:
    python political_reference_palette.py
    python political_reference_palette.py --frequencies export/my_type_reference_frequencies.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parent
DEFAULT_FREQUENCIES = (
    ROOT / "export/R05b14b_political_references_500songs_type_reference_frequencies.csv"
)
DEFAULT_MAPPING = ROOT / "political_reference_affiliations.csv"
DEFAULT_OUTPUT_CSV = (
    ROOT / "export/R05b14b_political_references_500songs_political_palette.csv"
)
DEFAULT_OUTPUT_DIR = ROOT / "images"
MAX_REFERENCES_PER_TYPE = 40

ORIENTATIONS = {
    "extreme_droite": ("Extrême droite", "#8C4A2F"),
    "conservateur": ("Conservateurs", "#3569A8"),
    "centriste": ("Centristes", "#E68613"),
    "social_democratie": ("Social-démocratie", "#D66A9F"),
    "gauche": ("Gauche", "#A50F15"),
    "extreme_gauche": ("Extrême gauche", "#FF1744"),
    "non_classe": ("Non classé", "#9E9E9E"),
}
REFERENCE_TYPES = {
    "figure_politique",
    "organisation_politique",
    "institution",
}
TYPE_LABELS = {
    "figure_politique": "Figures politiques",
    "organisation_politique": "Organisations politiques",
    "institution": "Institutions",
}
TEXT_COLOR = "#222222"
GRID_COLOR = "#D9D9D9"
BACKGROUND_COLOR = "#FFFFFF"


def read_mapping(path: Path) -> dict[tuple[str, str], str]:
    """Read exact, manually reviewed entity-to-orientation assignments."""
    mapping: dict[tuple[str, str], str] = {}
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"type", "reference_canon", "orientation"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(
                f"{path} doit contenir les colonnes : "
                + ", ".join(sorted(required))
            )
        for line_number, row in enumerate(reader, start=2):
            reference_type = (row.get("type") or "").strip()
            reference = (row.get("reference_canon") or "").strip()
            orientation = (row.get("orientation") or "").strip()
            if not reference_type or not reference or not orientation:
                continue
            if reference_type not in REFERENCE_TYPES:
                raise ValueError(
                    f"Type inconnu à la ligne {line_number} de {path}: {reference_type!r}"
                )
            if orientation not in ORIENTATIONS or orientation == "non_classe":
                raise ValueError(
                    f"Orientation inconnue ou non classable à la ligne {line_number} "
                    f"de {path}: {orientation!r}"
                )
            key = (reference_type, reference)
            if key in mapping:
                raise ValueError(f"Classement en double pour {key!r} dans {path}")
            mapping[key] = orientation
    return mapping


def read_frequencies(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    required = {"type", "reference_canon", "reference_count"}
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fields = reader.fieldnames or []
        missing = required.difference(fields)
        if missing:
            raise ValueError(
                f"{path} ne contient pas les colonnes : " + ", ".join(sorted(missing))
            )
        rows = list(reader)
    for line_number, row in enumerate(rows, start=2):
        if row["type"] not in REFERENCE_TYPES:
            raise ValueError(
                f"Type inconnu à la ligne {line_number} de {path}: {row['type']!r}"
            )
        if not row["reference_canon"].strip():
            raise ValueError(f"Référence vide à la ligne {line_number} de {path}")
        try:
            row["reference_count"] = str(int(row["reference_count"]))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Fréquence invalide à la ligne {line_number} de {path}"
            ) from exc
    return rows, fields


def frequency_label(path: Path) -> str:
    suffix = "_type_reference_frequencies"
    stem = path.stem
    if stem.endswith(suffix):
        stem = stem[: -len(suffix)]
    prefix = "R05b14b_political_references_"
    if stem.startswith(prefix):
        stem = stem[len(prefix) :]
    if stem == "500songs":
        return "500 chansons · Qwen3-14B"
    return stem


def write_enriched_csv(
    rows: list[dict[str, str]],
    source_fields: list[str],
    mapping: dict[tuple[str, str], str],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [*source_fields, "orientation", "orientation_label", "color"]
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            orientation = mapping.get(
                (row["type"], row["reference_canon"]), "non_classe"
            )
            label, color = ORIENTATIONS[orientation]
            writer.writerow(
                {
                    **row,
                    "orientation": orientation,
                    "orientation_label": label,
                    "color": color,
                }
            )


def plot_type(
    rows: list[dict[str, str]],
    reference_type: str,
    label: str,
    output_dir: Path,
) -> Path:
    selected = [row for row in rows if row["type"] == reference_type]
    selected.sort(
        key=lambda row: (
            -int(row["reference_count"]),
            row["reference_canon"].casefold(),
        )
    )
    selected = selected[:MAX_REFERENCES_PER_TYPE]
    if not selected:
        print(f"Aucune référence pour le type {reference_type}; aucun graphique créé.")
        return output_dir / f"R05b14b_palette_{label}_{reference_type}.png"

    orientations = [
        mapping_orientation if mapping_orientation in ORIENTATIONS else "non_classe"
        for mapping_orientation in (row.get("orientation", "non_classe") for row in selected)
    ]
    colors = [ORIENTATIONS[orientation][1] for orientation in orientations]
    names = [row["reference_canon"] for row in selected]
    counts = [int(row["reference_count"]) for row in selected]
    height = max(5.5, 0.34 * len(selected) + 1.7)
    figure, axis = plt.subplots(figsize=(14, height), facecolor=BACKGROUND_COLOR)
    axis.set_facecolor(BACKGROUND_COLOR)
    y_positions = list(range(len(selected)))
    bars = axis.barh(
        y_positions,
        counts,
        color=colors,
        edgecolor=BACKGROUND_COLOR,
        linewidth=0.7,
    )
    axis.bar_label(
        bars,
        labels=[str(count) for count in counts],
        padding=4,
        color=TEXT_COLOR,
    )
    axis.set_xlim(0, max(counts) * 1.18)
    axis.set_yticks(y_positions, labels=names)
    axis.invert_yaxis()
    axis.set_title(
        f"{TYPE_LABELS[reference_type]} — {label}",
        loc="left",
        fontsize=16,
        color=TEXT_COLOR,
        pad=16,
    )
    axis.set_xlabel("Nombre de mentions", color=TEXT_COLOR)
    axis.set_ylabel("")
    axis.tick_params(axis="both", colors=TEXT_COLOR, labelsize=9)
    axis.xaxis.grid(True, color=GRID_COLOR, linewidth=0.7)
    axis.set_axisbelow(True)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.spines["bottom"].set_color(GRID_COLOR)
    axis.legend(
        handles=[
            Patch(facecolor=color, label=orientation_label)
            for orientation_label, color in ORIENTATIONS.values()
        ],
        title="Orientation politique (classement manuel)",
        loc="upper center",
        bbox_to_anchor=(0.5, -0.11),
        ncol=4,
        frameon=False,
        fontsize=8,
        title_fontsize=9,
    )
    figure.text(
        0.01,
        0.012,
        "Gris : orientation non classée ou ambiguë. Couleurs fondées sur le mapping manuel.",
        color=TEXT_COLOR,
        fontsize=8,
    )
    figure.tight_layout(rect=(0, 0.08, 1, 1))
    output_dir.mkdir(parents=True, exist_ok=True)
    filename_parts = "".join(
        char.lower() if char.isalnum() else "_" for char in label
    ).split("_")
    filename_label = "_".join(part for part in filename_parts if part)
    output_path = output_dir / f"R05b14b_palette_{filename_label}_{reference_type}.png"
    figure.savefig(output_path, dpi=170, facecolor=BACKGROUND_COLOR, bbox_inches="tight")
    plt.close(figure)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Créer des graphiques politiques colorés par classement manuel."
    )
    parser.add_argument("--frequencies", type=Path, default=DEFAULT_FREQUENCIES)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    if not args.frequencies.is_file():
        raise FileNotFoundError(f"Fichier de fréquences introuvable : {args.frequencies}")
    if not args.mapping.is_file():
        raise FileNotFoundError(f"Fichier de classement manuel introuvable : {args.mapping}")

    mapping = read_mapping(args.mapping)
    rows, source_fields = read_frequencies(args.frequencies)
    for row in rows:
        row["orientation"] = mapping.get(
            (row["type"], row["reference_canon"]), "non_classe"
        )
    label = frequency_label(args.frequencies)
    write_enriched_csv(rows, source_fields, mapping, args.output_csv)
    print(f"Table avec orientation et couleur : {args.output_csv}")
    classified_count = sum(row["orientation"] != "non_classe" for row in rows)
    print(f"Références classées manuellement : {classified_count}/{len(rows)}")
    for reference_type in sorted(REFERENCE_TYPES):
        output_path = plot_type(rows, reference_type, label, args.output_dir)
        if output_path.is_file():
            print(f"Graphique : {output_path}")


if __name__ == "__main__":
    main()
