#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Renomme une clé du frontmatter YAML des notes .md d'un dossier d'un vault Obsidian.
La valeur du champ n'est jamais modifiée : seule la clé (à gauche du ':') est réécrite.

- Non récursif : seuls les .md directement dans TARGET_DIR sont traités.
- DRY_RUN = True  -> aucun fichier écrit, on affiche seulement ce qui serait fait.
- Si une note contient déjà OLD_KEY et NEW_KEY, elle est ignorée (signalée en conflit).
- Réécriture ligne par ligne : ordre, commentaires, listes, blocs multilignes,
  guillemets et fins de ligne d'origine sont préservés.
"""

import os

# ----------------------------------------------------------------------------
# CONFIGURATION (à modifier ici)
# ----------------------------------------------------------------------------
TARGET_DIR = r"C:\Users\virgil.mesle\OneDrive - Sirius Space Services\Documents\2 - Git\architecture-systeme\2.Functional\Functions"   # dossier du vault à traiter
OLD_KEY = "name"                                  # nom actuel de la clé YAML
NEW_KEY = "AUTO_name"                                 # nouveau nom de la clé YAML
DRY_RUN = False                                            # True = simulation, False = écriture réelle
# ----------------------------------------------------------------------------


def split_frontmatter(lines):
    """
    Retourne (start, end) : index de la ligne '---' d'ouverture et de fermeture.
    Le frontmatter doit commencer à la toute première ligne du fichier.
    Retourne (None, None) s'il n'y a pas de frontmatter valide.
    """
    if not lines:
        return None, None
    if lines[0].strip() != "---":
        return None, None
    for i in range(1, len(lines)):
        stripped = lines[i].strip()
        if stripped in ("---", "..."):
            return 0, i
    return None, None


def key_of_line(line):
    """
    Retourne le nom de la clé si la ligne est une clé de premier niveau du
    frontmatter (pas d'indentation, pas un élément de liste, pas un commentaire).
    Sinon retourne None.
    """
    if not line.strip() or line.lstrip().startswith("#"):
        return None
    if line[:1] in (" ", "\t"):          # clé imbriquée -> on ignore
        return None
    if line.lstrip().startswith("- "):   # élément de liste -> on ignore
        return None
    if ":" not in line:
        return None
    raw_key = line.split(":", 1)[0]
    # une clé peut être quotée : "mon champ": valeur
    key = raw_key.strip()
    if len(key) >= 2 and key[0] == key[-1] and key[0] in ("'", '"'):
        key = key[1:-1]
    return key


def rename_in_file(path):
    """
    Traite un fichier. Retourne un statut :
    'renamed', 'conflict', 'no_key', 'no_frontmatter', 'error'
    """
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            content = f.read()
    except Exception as exc:
        print("  [ERREUR] lecture %s : %s" % (path, exc))
        return "error"

    lines = content.splitlines(keepends=True)
    start, end = split_frontmatter(lines)
    if start is None:
        return "no_frontmatter"

    old_idx = []
    has_new = False
    for i in range(start + 1, end):
        key = key_of_line(lines[i])
        if key == OLD_KEY:
            old_idx.append(i)
        elif key == NEW_KEY:
            has_new = True

    if not old_idx:
        return "no_key"
    if has_new:
        return "conflict"

    # Réécriture : on remplace uniquement la partie clé, avant le premier ':'
    for i in old_idx:
        line = lines[i]
        before, after = line.split(":", 1)
        # on conserve l'éventuel espacement de fin dans 'before'
        trailing = before[len(before.rstrip()):]
        lines[i] = NEW_KEY + trailing + ":" + after

    if not DRY_RUN:
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write("".join(lines))
        except Exception as exc:
            print("  [ERREUR] écriture %s : %s" % (path, exc))
            return "error"

    return "renamed"


def main():
    if not os.path.isdir(TARGET_DIR):
        print("Dossier introuvable : %s" % TARGET_DIR)
        return
    if not OLD_KEY or not NEW_KEY or OLD_KEY == NEW_KEY:
        print("OLD_KEY / NEW_KEY invalides.")
        return

    print("Dossier   : %s" % TARGET_DIR)
    print("Renommage : '%s' -> '%s'" % (OLD_KEY, NEW_KEY))
    print("Mode      : %s" % ("DRY-RUN (aucune écriture)" if DRY_RUN else "ÉCRITURE RÉELLE"))
    print("-" * 70)

    stats = {"renamed": 0, "conflict": 0, "no_key": 0, "no_frontmatter": 0, "error": 0}

    for name in sorted(os.listdir(TARGET_DIR)):
        path = os.path.join(TARGET_DIR, name)
        if not os.path.isfile(path) or not name.lower().endswith(".md"):
            continue

        status = rename_in_file(path)
        stats[status] += 1

        if status == "renamed":
            print("[%s] %s" % ("OK " if not DRY_RUN else "SIM", name))
        elif status == "conflict":
            print("[CONFLIT] %s : contient déjà '%s', note ignorée" % (name, NEW_KEY))

    print("-" * 70)
    print("Notes modifiées%s : %d" % (" (simulation)" if DRY_RUN else "", stats["renamed"]))
    print("Conflits ignorés         : %d" % stats["conflict"])
    print("Sans le champ '%s' : %d" % (OLD_KEY, stats["no_key"]))
    print("Sans frontmatter         : %d" % stats["no_frontmatter"])
    print("Erreurs                  : %d" % stats["error"])
    if DRY_RUN and stats["renamed"]:
        print("\n>>> Passez DRY_RUN = False pour appliquer réellement les modifications.")


if __name__ == "__main__":
    main()