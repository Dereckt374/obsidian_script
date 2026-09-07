#!/usr/bin/env python3
"""Crée une note Markdown (avec front matter YAML) pour chaque bullet point d'un fichier texte."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

# Caractères qui, en début de valeur, obligent à mettre des guillemets en YAML.
_DEBUTS_RESERVES = "-?:,[]{}#&*!|>'\"%@`"


def slugify(texte: str, longueur_max: int = 60) -> str:
    """Transforme un texte quelconque en nom de fichier sûr."""
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    texte = re.sub(r"[^\w\s-]", "", texte).strip() #.lower()
    # texte = re.sub(r"[\s_-]+", "-", texte)
    return texte[:longueur_max].strip("-") or "note"


def chemin_libre(dossier: Path, slug: str) -> Path:
    """Renvoie un chemin .md non utilisé (suffixe -2, -3... en cas de doublon)."""
    chemin = dossier / f"{slug}.md"
    i = 2
    while chemin.exists():
        chemin = dossier / f"{slug}-{i}.md"
        i += 1
    return chemin


def formater_scalaire(valeur) -> str:
    """Sérialise une valeur simple en YAML, en ne citant que si nécessaire."""
    if isinstance(valeur, bool):
        return "true" if valeur else "false"
    if isinstance(valeur, (int, float)):
        return str(valeur)

    texte = str(valeur)
    doit_citer = (
        not texte
        or texte != texte.strip()
        or texte[0] in _DEBUTS_RESERVES
        or ": " in texte
        or " #" in texte
        or "\n" in texte
    )
    if doit_citer:
        return '"' + texte.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return texte


def construire_frontmatter(proprietes: dict, placeholder: str = "à-renseigner") -> str:
    """Construit le bloc YAML à partir d'un dict {champ: valeur | liste | None}."""
    lignes = ["---"]
    for cle, valeur in proprietes.items():
        if valeur is None:
            lignes.append(f"{cle}: {formater_scalaire(placeholder)}")
        elif isinstance(valeur, (list, tuple, set)):
            valeurs = list(valeur)
            if not valeurs:
                lignes.append(f"{cle}: []")
            else:
                lignes.append(f"{cle}:")
                lignes.extend(f"  - {formater_scalaire(v)}" for v in valeurs)
        else:
            lignes.append(f"{cle}: {formater_scalaire(valeur)}")
    lignes.append("---")
    return "\n".join(lignes)


def creer_notes(
    fichier_source: str | Path,
    dossier_sortie: str | Path = "notes",
    proprietes: dict | None = None,
    placeholder: str = "à-renseigner",
    marqueur: str = "- ",
) -> list[Path]:
    """Crée une note .md par ligne commençant par `marqueur`.

    Args:
        fichier_source: fichier texte à lire.
        dossier_sortie: dossier où écrire les notes (créé si absent).
        proprietes: champs YAML à écrire, dans l'ordre. La valeur peut être
            un scalaire (str, int, float, bool), une liste (champ multi-valeurs)
            ou None (le placeholder est inséré, champ à renseigner).
            Défaut: {"tags": None}.
        placeholder: valeur écrite pour les champs à None.
        marqueur: préfixe identifiant un bullet point.

    Returns:
        La liste des chemins des notes créées.
    """
    source = Path(fichier_source)
    sortie = Path(dossier_sortie)
    sortie.mkdir(parents=True, exist_ok=True)

    if proprietes is None:
        proprietes = {"tags": None}

    creees: list[Path] = []
    for ligne in source.read_text(encoding="utf-8").splitlines():
        contenu = ligne.strip()
        if not contenu.startswith(marqueur):
            continue

        titre = contenu[len(marqueur):].strip()
        if not titre:
            continue

        # "title" d'abord, sauf si l'appelant l'a déjà positionné lui-même.
        note = f"{construire_frontmatter(proprietes, placeholder)}"

        chemin = chemin_libre(sortie, slugify(titre))
        chemin.write_text(note, encoding="utf-8")
        creees.append(chemin)

    return creees


if __name__ == "__main__":
    notes = creer_notes(
        r"C:\Users\virgil.mesle\OneDrive - Sirius Space Services\Documents\obsidian_system_analysis\1.Operationnal\External Stakeholder List.md",
        dossier_sortie=r"C:\Users\virgil.mesle\OneDrive - Sirius Space Services\Documents\obsidian_system_analysis",
        proprietes={
            "tags": "stakeholder",                  # à renseigner
            "family": "",         # valeur unique
        },
    )
    print(f"{len(notes)} note(s) créée(s)")