import os
import shutil

# === Paramètres ===
root_dir = "/chemin/vers/ton/repertoire"  # Répertoire racine à scanner
extensions_cibles = {".png", ".jpeg", ".pdf"}
destination_dir = os.path.join(root_dir, "Attachments", "isolated")

# Création du dossier cible
os.makedirs(destination_dir, exist_ok=True)

# 1) Récupérer tous les fichiers avec extensions ciblées
fichiers_cibles = []
for dirpath, _, filenames in os.walk(root_dir):
    for filename in filenames:
        ext = os.path.splitext(filename)[1].lower()
        if ext in extensions_cibles:
            fichiers_cibles.append(os.path.join(dirpath, filename))

# 2) Lire tout le contenu des fichiers .md
contenu_md = ""
for dirpath, _, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename.lower().endswith(".md"):
            md_path = os.path.join(dirpath, filename)
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    contenu_md += f.read()
            except UnicodeDecodeError:
                # Si encodage exotique
                with open(md_path, "r", encoding="latin-1") as f:
                    contenu_md += f.read()

# 3) Vérifier si les fichiers sont mentionnés
fichiers_non_utilises = []
for fichier in fichiers_cibles:
    nom_fichier = os.path.basename(fichier)
    if nom_fichier not in contenu_md:
        fichiers_non_utilises.append(fichier)

# 4) Déplacer les fichiers non utilisés
for fichier in fichiers_non_utilises:
    rel_path = os.path.relpath(fichier, root_dir)  # chemin relatif
    new_path = os.path.join(destination_dir, rel_path)
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    shutil.move(fichier, new_path)

print(f"{len(fichiers_non_utilises)} fichier(s) déplacé(s) vers {destination_dir}")

