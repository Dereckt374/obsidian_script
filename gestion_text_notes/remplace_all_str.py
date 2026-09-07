#!/usr/bin/env python3
"""Remplace récursivement une chaîne dans le contenu ET les noms de fichiers/dossiers."""

import os

# ---------------- CONFIG ----------------
ROOT = r"C:\Users\virgil.mesle\Documents\architecture-systeme\2.Functional\Functional Interfaces"
OLD = "# Description"
NEW = "# Flux"
DRY_RUN = False                       # True = aperçu seul, aucune écriture
EXCLUDE_DIRS = {".git", ".svn", "node_modules", "__pycache__", ".venv", "venv"}
MAX_SIZE = 15 * 1024 * 1024           # ignore les fichiers > 5 Mo
# ----------------------------------------

stats = {"files_changed": 0, "occurrences": 0, "renamed": 0, "skipped": 0}

def walk(root):
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        yield dirpath, dirnames, filenames


def replace_contents(root):
    for dirpath, _, filenames in walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            if os.path.islink(path) or os.path.getsize(path) > MAX_SIZE:
                stats["skipped"] += 1
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = f.read()
            except (UnicodeDecodeError, OSError):
                stats["skipped"] += 1          # binaire ou illisible
                continue

            n = data.count(OLD)
            if not n:
                continue

            stats["files_changed"] += 1
            stats["occurrences"] += n
            print(f"[CONTENU] {path}  ({n} occurrence(s))")
            if not DRY_RUN:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(data.replace(OLD, NEW))


def rename_paths(root):
    # bottom-up : on renomme les enfants avant les parents
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        if any(part in EXCLUDE_DIRS for part in dirpath.split(os.sep)):
            continue
        for name in filenames + [d for d in dirnames if d not in EXCLUDE_DIRS]:
            if OLD not in name:
                continue
            src = os.path.join(dirpath, name)
            dst = os.path.join(dirpath, name.replace(OLD, NEW))
            if os.path.exists(dst):
                print(f"[CONFLIT] {dst} existe déjà — ignoré")
                continue
            stats["renamed"] += 1
            print(f"[RENOMMAGE] {src} -> {dst}")
            if not DRY_RUN:
                os.rename(src, dst)


if __name__ == "__main__":
    if not os.path.isdir(ROOT):
        raise SystemExit(f"Répertoire introuvable : {ROOT}")

    print(f"{'*** DRY-RUN ***' if DRY_RUN else '*** ÉCRITURE ***'}  "
          f"{ROOT}  |  {OLD!r} -> {NEW!r}\n")

    replace_contents(ROOT)
    rename_paths(ROOT)

    print(f"\nFichiers modifiés : {stats['files_changed']} "
          f"({stats['occurrences']} occurrences)")
    print(f"Éléments renommés : {stats['renamed']}")
    print(f"Ignorés (binaires/trop gros) : {stats['skipped']}")
    if DRY_RUN:
        print("\nAucune modification effectuée. Passer DRY_RUN = False pour appliquer.")