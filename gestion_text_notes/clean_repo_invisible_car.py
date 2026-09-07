"""Nettoie recursivement les caracteres invisibles : noms de fichiers, noms de
dossiers et contenu des fichiers texte (+ .xlsx via pandas)."""

import os
import re
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------- PARAMETRES
RACINE = r"C:\Users\virgil.mesle\OneDrive - Sirius Space Services\Documents\obsidian_system_analysis"                          # dossier a parcourir
EXTENSIONS = [".md"]   # [] = toutes les extensions
DRY_RUN = False                         # True = simulation, aucune ecriture
NETTOYER_NOMS = True                   # renommer les fichiers
RENOMMER_DOSSIERS = True               # renommer aussi les dossiers
NETTOYER_CONTENU = True                # reecrire le contenu des fichiers
TAILLE_MAX_MO = 20                     # au-dela, le contenu est ignore
# ---------------------------------------------------------------------------

ESPACES = dict.fromkeys(
    "\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008"
    "\u2009\u200a\u202f\u205f\u3000\t",
    " ",
)
SUPPRIMER = dict.fromkeys(
    "\u200b\u200c\u200d\u2060\ufeff\u00ad\u180e\u200e\u200f\u202a\u202b"
    "\u202c\u202d\u202e",
    None,
)
SUPPRIMER = {}
TABLE = {ord(k): v for k, v in {**ESPACES, **SUPPRIMER}.items()}
CTRL = re.compile(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]")
ENCODAGES = ["utf-8-sig", "utf-8", "cp1252"]
INTERDITS_NOM = '<>:"/\\|?*'


def _base(txt):
    txt = txt.translate(TABLE)
    txt = CTRL.sub("", txt)
    return "".join(c for c in txt if unicodedata.category(c) != "Cf")


def nettoyer_nom(nom):
    """Nom de fichier/dossier : espaces multiples reduits, bords nettoyes."""
    txt = _base(nom).replace("\n", " ").replace("\r", " ")
    txt = "".join(c for c in txt if c not in INTERDITS_NOM)
    txt = re.sub(r" {2,}", " ", txt).strip(" .")
    return txt or nom


def nettoyer_ligne(ligne):
    """Une ligne de contenu : retours a la ligne preserves par l'appelant."""
    return re.sub(r" {2,}", " ", _base(ligne)).rstrip()


def nettoyer_texte(txt):
    sorties = []
    for ligne in txt.splitlines(keepends=True):
        corps = ligne.rstrip("\r\n")
        fin = ligne[len(corps):]
        sorties.append(nettoyer_ligne(corps) + fin)
    return "".join(sorties)


def extension_ok(chemin):
    return not EXTENSIONS or chemin.suffix.lower() in [
        e.lower() for e in EXTENSIONS
    ]


def traiter_contenu(chemin):
    """Retourne True si le contenu a ete (ou serait) modifie."""
    if chemin.stat().st_size > TAILLE_MAX_MO * 1024 * 1024:
        return False

    if chemin.suffix.lower() in (".xlsx", ".xlsm"):
        return _traiter_excel(chemin)

    brut = chemin.read_bytes()
    if b"\x00" in brut[:8192]:
        return False

    bom = brut.startswith(b"\xef\xbb\xbf")
    for enc in ENCODAGES:
        try:
            txt = brut.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return False

    propre = nettoyer_texte(txt)
    if propre == txt:
        return False
    if not DRY_RUN:
        sortie = "utf-8-sig" if bom else ("utf-8" if enc == "utf-8-sig" else enc)
        chemin.write_text(propre, encoding=sortie, newline="")
    return True


def _traiter_excel(chemin):
    import pandas as pd

    feuilles = pd.read_excel(chemin, sheet_name=None, dtype=object)
    modifie = False
    for nom, df in feuilles.items():
        avant = df.to_numpy(dtype=object, copy=True)
        df = df.map(lambda v: nettoyer_ligne(v) if isinstance(v, str) else v)
        df.columns = [nettoyer_nom(str(c)) for c in df.columns]
        modifie |= bool((avant != df.to_numpy(dtype=object)).sum())
        feuilles[nom] = df
    if modifie and not DRY_RUN:
        with pd.ExcelWriter(chemin, engine="openpyxl") as writer:
            for nom, df in feuilles.items():
                df.to_excel(writer, sheet_name=nom, index=False)
    return modifie


def renommer(chemin):
    """Retourne True si le nom a ete (ou serait) change."""
    nouveau = nettoyer_nom(chemin.name)
    if nouveau == chemin.name:
        return False
    cible = chemin.with_name(nouveau)
    if cible.exists():
        print(f"  ! collision ignoree : {chemin} -> {nouveau}")
        return False
    print(f"  RENOMME  {chemin}  ->  {nouveau}")
    if not DRY_RUN:
        chemin.rename(cible)
    return True


def main():
    racine = Path(RACINE).resolve()
    n_noms = n_contenus = n_dossiers = 0

    for dossier, sous_dossiers, fichiers in os.walk(racine, topdown=False):
        for nom in fichiers:
            chemin = Path(dossier) / nom
            if not extension_ok(chemin):
                continue
            if NETTOYER_CONTENU and traiter_contenu(chemin):
                print(f"  CONTENU  {chemin}")
                n_contenus += 1
            if NETTOYER_NOMS and renommer(chemin):
                n_noms += 1

        if RENOMMER_DOSSIERS and Path(dossier) != racine:
            if renommer(Path(dossier)):
                n_dossiers += 1

    mode = "SIMULATION (aucune modification)" if DRY_RUN else "APPLIQUE"
    print(
        f"\n[{mode}] {n_noms} fichier(s) renomme(s), "
        f"{n_dossiers} dossier(s) renomme(s), {n_contenus} contenu(s) nettoye(s)"
    )


if __name__ == "__main__":
    main()