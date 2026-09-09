#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Renommage en masse des fichiers d'un répertoire.
Toute la configuration se fait dans le bloc ci-dessous.
"""

import re
from pathlib import Path

# ─────────────── CONFIGURATION ───────────────
TARGET_DIR = r"C:\Users\virgil.mesle\Documents\architecture-systeme\1.Operational\Mission S1B"

PATTERN = "S1B_M_"          # chaîne (ou regex si USE_REGEX = True) à chercher
REPLACEMENT = "S1B_M"     # texte de remplacement

USE_REGEX = False           # False = remplacement littéral / True = regex
CASE_SENSITIVE = True       # False = ignore la casse
RECURSIVE = False           # True = descend dans les sous-dossiers
KEEP_EXTENSION = True       # True = ne touche pas à l'extension (.txt, .jpg...)
DRY_RUN = False              # True = simulation, aucun fichier n'est modifié
# ─────────────────────────────────────────────


def build_regex():
    """Compile le motif : échappé si on veut un remplacement littéral."""
    pattern = PATTERN if USE_REGEX else re.escape(PATTERN)
    flags = 0 if CASE_SENSITIVE else re.IGNORECASE
    return re.compile(pattern, flags)


def free_path(path: Path) -> Path:
    """Retourne un chemin libre en ajoutant _1, _2... si besoin."""
    if not path.exists():
        return path
    i = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{i}{path.suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def new_name(file: Path, rx: re.Pattern) -> str:
    """Calcule le nouveau nom de fichier."""
    if KEEP_EXTENSION:
        return rx.sub(REPLACEMENT, file.stem) + file.suffix
    return rx.sub(REPLACEMENT, file.name)


def main():
    root = Path(TARGET_DIR)
    if not root.is_dir():
        print(f"[ERREUR] Répertoire introuvable : {root}")
        return

    rx = build_regex()
    files = root.rglob("*") if RECURSIVE else root.glob("*")

    renamed = skipped = 0
    for file in sorted(files):
        if not file.is_file():
            continue

        target_name = new_name(file, rx)
        if target_name == file.name:
            skipped += 1
            continue

        target = free_path(file.with_name(target_name))
        tag = "[SIMU]" if DRY_RUN else "[OK]  "
        note = "  (collision → suffixe)" if target.name != target_name else ""
        print(f"{tag} {file.name}  ->  {target.name}{note}")

        if not DRY_RUN:
            file.rename(target)
        renamed += 1

    mode = "SIMULATION" if DRY_RUN else "RENOMMAGE EFFECTUÉ"
    print(f"\n--- {mode} : {renamed} fichier(s) concerné(s), {skipped} inchangé(s) ---")


if __name__ == "__main__":
    main()