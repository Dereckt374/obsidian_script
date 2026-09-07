#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nomme les requirements : lit la section "# Requirement Statement" et ecrit un
titre synthetique anglais dans le champ 'name' du frontmatter YAML et/ou
directement dans le nom du fichier.

DOSSIER SOURCE : SRC_DIR est une variable en dur. Si elle est laissee vide,
une boite de dialogue s'ouvre au lancement pour choisir le dossier.

SORTIE : deux interrupteurs independants.
  WRITE_FIELD  -> ecrit le titre dans le frontmatter
  RENAME_FILE  -> renomme le fichier, le titre remplace tout l'ancien nom

FILTRE PRELIMINAIRE : une note n'est traitee que si son champ YAML de controle
satisfait le critere configure ci-dessous. Le filtre s'applique AVANT toute
lecture de section et avant tout appel au modele.

Par securite DRY_RUN vaut True : le script affiche ce qu'il ferait sans rien ecrire.
"""

import re
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

# ============================== REGLAGES (a editer) ==============================

# Chemin en dur. Laisse la chaine vide ("") pour ouvrir une boite de dialogue.
SRC_DIR = r"C:\Users\virgil.mesle\Documents\architecture-systeme\2.Functional\Spec_test"

# --- que fait-on du titre produit -------------------------------------------
WRITE_FIELD = False        # ecrire le titre dans le frontmatter
RENAME_FILE = True        # renommer le fichier avec le titre
TARGET_FIELD = "name"     # champ dans lequel le titre est ecrit

MAX_FILENAME = 120        # longueur max du nom de fichier, extension exclue
ON_NAME_CLASH = "suffix"  # "suffix" = ajoute " 2", " 3"... | "skip" = ne renomme pas

# --- filtre preliminaire sur le frontmatter ---------------------------------
FILTER_FIELD = None     # champ YAML de controle ; None desactive le filtre
FILTER_MODE = "empty"     # "empty" | "filled" | "missing" | "present" | "equals"
FILTER_VALUE = ""         # utilise uniquement si FILTER_MODE == "equals"
#   empty   : champ absent, ou present mais sans valeur  -> c'est ton cas
#   filled  : champ present ET renseigne
#   missing : champ totalement absent du frontmatter
#   present : champ present, renseigne ou non
#   equals  : champ dont la valeur vaut exactement FILTER_VALUE

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gemma4:latest"

SECTION_TITLE = "Requirement Statement"
TEMPERATURE = 0.2
NUM_CTX = 4096
NUM_PREDICT = 40          # coupe net si le modele part en explication
DEBUG_RAW = True          # affiche la reponse brute quand le format est rejete
MAX_WORDS = 12
MAX_INPUT_CHARS = 4000
TIMEOUT = 300
RETRIES = 2

DRY_RUN = False            # True = affiche seulement, n'ecrit rien
LIMIT = 0                 # 0 = toutes les notes ; sinon n premieres
EXCLUDE_DIRS = {".obsidian", ".git", ".trash", "node_modules", ".smart-env"}

# ================================================================================

SYSTEM_PROMPT = """You generate short titles for software requirements. You do nothing else.

The user message contains the raw body of the "# Requirement Statement" section
taken from a requirement note. The source text may be in French or in English.
Your reply is the title of that requirement, in English.

RULES
1. Output an English noun phrase of 3 to 12 words. Never a full sentence.
2. Your entire reply must be the title. Starting your reply with anything other than the first word of the title is a failure.
3. Name the SUBJECT of the requirement, not the fact that it is a requirement.
4. Keep domain terms, product names, acronyms and figures exactly as written in
   the source. Do not invent anything that is not in the text.
5. Capitalise the first word and proper nouns only. No trailing period.
6. Never use any of these characters: : / \\ | # ^ [ ] " * ? < >
7. If the text covers several points, title the dominant one. Do not enumerate.

OUTPUT FORMAT
Output the title alone, on a single line.
No quotes. No "Title:" prefix. No explanation. No markdown. No blank line.

EXAMPLES

Input: The system shall require a second authentication factor for any account holding administrator privileges, using either TOTP or a hardware key.
Output: Two-factor authentication for administrator accounts

Input: Le systeme doit purger automatiquement les journaux d'audit de plus de 400 jours, en conservant une archive chiffree hors ligne.
Output: Automatic audit log purge after 400 days

Input: L'utilisateur doit pouvoir exporter ses donnees personnelles au format JSON depuis la page de profil, en moins de 30 secondes.
Output: JSON export of personal data from profile

Input: The API shall return HTTP 429 together with a Retry-After header once a client exceeds 1000 requests per minute on any public endpoint.
Output: Rate limiting for public API clients

Input: En cas de coupure reseau, l'application doit conserver les saisies en cours localement et les resynchroniser des le retour de la connexion.
Output: Offline capture and resynchronisation
"""

FORBIDDEN = r':/\\|#^\[\]"*?<>'
FRONTMATTER_RE = re.compile(r"(?s)\A\ufeff?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?")

RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}

# ------------------------------ dossier source ------------------------------

def resolve_src_dir():
    """Chemin en dur si renseigne, sinon boite de dialogue."""
    raw = (SRC_DIR or "").strip().strip('"')
    if raw:
        p = Path(raw)
        if not p.is_dir():
            raise SystemExit("Dossier source introuvable : %s" % p)
        return p

    try:
        import tkinter
        from tkinter import filedialog
    except ImportError:
        raise SystemExit("SRC_DIR est vide et tkinter n'est pas disponible.\n"
                         "Renseigne SRC_DIR en dur dans le script.")

    root = tkinter.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    chosen = filedialog.askdirectory(title="Choisis le dossier des notes a traiter")
    root.destroy()

    if not chosen:
        raise SystemExit("Aucun dossier choisi, arret.")
    p = Path(chosen)
    if not p.is_dir():
        raise SystemExit("Dossier invalide : %s" % p)
    return p


# ----------------------------- frontmatter YAML -----------------------------

def split_frontmatter(text):
    """Retourne (contenu_du_frontmatter, corps). contenu vaut None s'il n'y en a pas."""
    m = FRONTMATTER_RE.match(text)
    if m:
        return m.group(1), text[m.end():]
    return None, text


def field_line_re(field):
    # clef de premier niveau : aucune indentation devant
    return re.compile(r"(?m)^(?P<key>%s)[ \t]*:(?P<val>.*)$" % re.escape(field))


def read_field(front, field):
    """Retourne (present, valeur_normalisee).
    Gere 'name:', 'name: ""', 'name: Titre' et les blocs indentes / listes."""
    if front is None:
        return False, ""
    m = field_line_re(field).search(front)
    if not m:
        return False, ""

    raw = m.group("val")
    # commentaire YAML en fin de ligne, hors valeur entre quotes
    if not raw.strip().startswith(("'", '"')):
        raw = re.split(r"\s+#", raw, 1)[0]
    value = raw.strip()

    if value in ('""', "''"):
        value = ""
    elif len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1].strip()

    # valeur sur la ligne vide : le champ peut porter un bloc indente ou une liste
    if value == "":
        after = front[m.end():].lstrip("\r\n")
        for line in after.split("\n"):
            if not line.strip():
                continue
            if line[:1] in (" ", "\t") or line.lstrip().startswith("- "):
                value = "<bloc>"
            break

    return True, value


def passes_filter(front):
    """Filtre preliminaire. Retourne (garde, motif_du_rejet)."""
    if not FILTER_FIELD:
        return True, ""
    present, value = read_field(front, FILTER_FIELD)

    if FILTER_MODE == "empty":
        ok = (not present) or value == ""
        why = "%s = %r" % (FILTER_FIELD, value)
    elif FILTER_MODE == "filled":
        ok = present and value != ""
        why = "%s vide ou absent" % FILTER_FIELD
    elif FILTER_MODE == "missing":
        ok = not present
        why = "%s present" % FILTER_FIELD
    elif FILTER_MODE == "present":
        ok = present
        why = "%s absent" % FILTER_FIELD
    elif FILTER_MODE == "equals":
        ok = present and value == FILTER_VALUE
        why = "%s = %r (attendu %r)" % (FILTER_FIELD, value, FILTER_VALUE)
    else:
        raise SystemExit("FILTER_MODE inconnu : %r" % FILTER_MODE)

    return ok, "" if ok else why


def set_field(text, field, value):
    """Ecrit field: value dans le frontmatter, en creant le bloc si besoin."""
    front, body = split_frontmatter(text)
    line = "%s: %s" % (field, value)
    if front is None:
        return "---\n%s\n---\n\n%s" % (line, text.lstrip("\ufeff"))
    pat = field_line_re(field)
    if pat.search(front):
        front = pat.sub(lambda _: line, front, count=1)
    else:
        front = line + "\n" + front
    return "---\n%s\n---\n%s" % (front, body)


# ------------------------------- nom de fichier -------------------------------

def safe_filename(title):
    """Transforme un titre en nom de fichier valide, sans extension."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title)
    name = re.sub(r"\s{2,}", " ", name).strip(" .")
    if len(name) > MAX_FILENAME:
        name = name[:MAX_FILENAME].rsplit(" ", 1)[0].strip(" .")
    if name.upper() in RESERVED_NAMES:
        name = "_" + name
    return name


def unique_path(folder, stem, current):
    """Chemin cible libre. Retourne None si aucune place trouvee."""
    target = folder / (stem + ".md")
    if target == current or not target.exists():
        return target
    if ON_NAME_CLASH != "suffix":
        return None
    for i in range(2, 100):
        cand = folder / ("%s %d.md" % (stem, i))
        if cand == current or not cand.exists():
            return cand
    return None


# ------------------------------ lecture de la section ------------------------------

def extract_section(body, title):
    """Texte sous '# <title>', jusqu'au prochain titre quel que soit son niveau."""
    pat = re.compile(r"(?m)^\#{1,6}[ \t]+%s[ \t]*$" % re.escape(title))
    m = pat.search(body)
    if not m:
        return ""
    rest = body[m.end():]
    nxt = re.search(r"(?m)^\#{1,6}[ \t]+\S", rest)
    section = rest[:nxt.start()] if nxt else rest
    # on retire le balisage qui perturbe un petit modele
    section = re.sub(r"(?s)```.*?```", " ", section)
    section = re.sub(r"!?\[\[([^\]|]*)(?:\|([^\]]*))?\]\]", lambda x: x.group(2) or x.group(1), section)
    section = re.sub(r"\[([^\]\n]*)\]\([^)\n]*\)", r"\1", section)
    section = re.sub(r"(?m)^[ \t]*[-*+][ \t]+(?:\[[ xX]\][ \t]+)?", "", section)
    section = re.sub(r"[*_`>]", "", section)
    section = re.sub(r"[ \t]*\r?\n[ \t]*", " ", section)
    return re.sub(r"\s{2,}", " ", section).strip()


# --------------------------------- appel du modele ---------------------------------

def ollama_chat(user_text):
    payload = {
        "model": MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        "options": {
            "temperature": TEMPERATURE,
            "num_ctx": NUM_CTX,
            "num_predict": NUM_PREDICT,
        },
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace").strip()
        raise RuntimeError("HTTP %s sur %s -> %s" % (e.code, OLLAMA_URL, body[:200]))


def preflight():
    if not WRITE_FIELD and not RENAME_FILE:
        raise SystemExit("WRITE_FIELD et RENAME_FILE sont tous les deux False : rien a faire.")
    if not isinstance(SYSTEM_PROMPT, str):
        raise SystemExit("SYSTEM_PROMPT doit etre une chaine, pas un %s." % type(SYSTEM_PROMPT).__name__)
    tags_url = OLLAMA_URL.replace("/api/chat", "/api/tags")
    try:
        with urllib.request.urlopen(tags_url, timeout=15) as resp:
            models = [m["name"] for m in json.loads(resp.read().decode("utf-8"))["models"]]
    except Exception as e:
        raise SystemExit("Serveur injoignable sur %s (%s).\nLance 'ollama serve'." % (tags_url, e))
    if MODEL not in models:
        raise SystemExit("Modele '%s' absent.\nInstalles : %s\n-> ollama pull %s"
                         % (MODEL, ", ".join(models) or "(aucun)", MODEL))
    print("Serveur OK, modele '%s' disponible.\n" % MODEL)


def sanitize(title):
    """Un petit modele lache le format : on ne garde que ce qui ressemble a un titre."""
    title = re.sub(r"(?s)^<think>.*?</think>", " ", title).strip()
    filler = re.compile(r"(?i)^(sure|okay|ok|certainly|here|voici|bien sûr|of course)\b")
    picked = ""
    for line in title.splitlines():
        line = line.strip()
        if not line or line.endswith(":") or filler.match(line):
            continue
        picked = line
        break
    title = re.sub(r"(?i)^\s*(?:output|title|name)\s*:\s*", "", picked)
    title = title.strip().strip("\"'`*").strip()
    title = re.sub(r"[%s]" % FORBIDDEN, "", title)
    title = re.sub(r"\s{2,}", " ", title).strip(" .-")
    words = title.split()
    if len(words) > MAX_WORDS:
        title = " ".join(words[:MAX_WORDS])
    return title


def make_title(section_text):
    payload = "Input: %s\nOutput:" % section_text[:MAX_INPUT_CHARS]
    for attempt in range(RETRIES + 1):
        try:
            raw = ollama_chat(payload)
        except (RuntimeError, urllib.error.URLError, OSError, KeyError) as e:
            print("        ! erreur : %s (tentative %d)" % (e, attempt + 1))
            time.sleep(2)
            continue
        title = sanitize(raw)
        if 2 <= len(title.split()) <= MAX_WORDS:
            return title
        print("        ! sortie hors format (%r), tentative %d" % (title[:60], attempt + 1))
        if DEBUG_RAW:
            print("          reponse brute : %r" % raw[:300])
            print("          entree envoyee: %r" % section_text[:200])
    return ""


# ------------------------------------- pilote -------------------------------------

def main():
    src_dir = resolve_src_dir()
    preflight()

    files = [p for p in sorted(src_dir.rglob("*.md"))
             if not EXCLUDE_DIRS & set(p.relative_to(src_dir).parts)]
    if LIMIT:
        files = files[:LIMIT]

    print("Dossier : %s" % src_dir)
    print("Sortie  : %s%s%s"
          % ("frontmatter '%s'" % TARGET_FIELD if WRITE_FIELD else "",
             " + " if (WRITE_FIELD and RENAME_FILE) else "",
             "renommage du fichier" if RENAME_FILE else ""))
    print("%d note(s) scannee(s) | filtre : %s %s%s\n"
          % (len(files), FILTER_FIELD or "(aucun)", FILTER_MODE,
             "  [DRY_RUN]" if DRY_RUN else ""))

    kept = filtered = nosection = done = failed = renamed = 0
    t0 = time.time()

    for path in files:
        rel = path.relative_to(src_dir)
        text = path.read_text(encoding="utf-8", errors="replace")
        front, body = split_frontmatter(text)

        # --- filtre preliminaire, avant toute autre operation ---
        ok, why = passes_filter(front)
        if not ok:
            filtered += 1
            print("  -  %s -- ignoree (%s)" % (rel, why))
            continue
        kept += 1

        section = extract_section(body, SECTION_TITLE)
        if not section:
            nosection += 1
            print("  -  %s -- pas de section '%s'" % (rel, SECTION_TITLE))
            continue

        title = make_title(section)
        if not title:
            failed += 1
            print("  X  %s -- ECHEC" % rel)
            continue

        # --- cible de renommage ---
        target = None
        if RENAME_FILE:
            stem = safe_filename(title)
            if not stem:
                failed += 1
                print("  X  %s -- titre inutilisable comme nom de fichier (%r)" % (rel, title))
                continue
            target = unique_path(path.parent, stem, path)
            if target is None:
                failed += 1
                print("  X  %s -- '%s.md' existe deja, renommage abandonne" % (rel, stem))
                continue
            if target == path:
                target = None  # deja le bon nom

        print("  OK %s\n        -> %s%s"
              % (rel, title, "\n        -> fichier : %s" % target.name if target else ""))

        if not DRY_RUN:
            if WRITE_FIELD:
                path.write_text(set_field(text, TARGET_FIELD, title), encoding="utf-8")
            if target:
                try:
                    path.rename(target)
                    renamed += 1
                except OSError as e:
                    failed += 1
                    print("  X  %s -- renommage impossible (%s)" % (rel, e))
                    continue
        elif target:
            renamed += 1

        done += 1

    print("\n%d retenue(s) par le filtre, %d ecartee(s), %d sans section."
          % (kept, filtered, nosection))
    print("%d titre(s) %s, %d renommage(s), %d echec(s), en %.1f min."
          % (done, "proposes" if DRY_RUN else "ecrits", renamed, failed, (time.time() - t0) / 60))
    if DRY_RUN:
        print("Rien n'a ete modifie. Passe DRY_RUN a False pour ecrire.")


if __name__ == "__main__":
    main()