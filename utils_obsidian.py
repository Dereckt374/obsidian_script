import os
import yaml
import shutil

def add_yaml_field_from_md(filepath, field,  type_value):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Vérifie la présence d'un front‑matter YAML
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            yaml_block = parts[1]
            body = parts[2]

            data = yaml.safe_load(yaml_block) or {}

            # Ajout / mise à jour du FIELD 
            data[field] = type_value

            new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True)
            new_content = f"---\n{new_yaml}---{body}"

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"[OK] Mis à jour : {filepath}")
            return

    # Si pas de YAML, on en crée un
    new_yaml = yaml.dump({field: type_value}, sort_keys=False, allow_unicode=True)
    new_content = f"---\n{new_yaml}---\n{content}"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"[OK] YAML ajouté : {filepath}")

def remove_yaml_field_from_md(directory, field_name, recursive=False):
    """
    Supprime un champ YAML dans les fichiers .md d'un répertoire.
    
    :param directory: Chemin du répertoire à traiter
    :param field_name: Nom du champ YAML à supprimer
    :param recursive: Booléen, True pour parcourir récursivement
    """
    if recursive:
        walker = os.walk(directory)
    else:
        walker = [(directory, [], os.listdir(directory))]

    for root, _, files in walker:
        for filename in files:
            if filename.endswith(".md"):
                filepath = os.path.join(root, filename)
                process_markdown_file(filepath, field_name)


def process_markdown_file(filepath, field_name):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Vérifie la présence d’un front‑matter YAML
    if not content.startswith("---"):
        return

    parts = content.split("---", 2)
    if len(parts) < 3:
        return

    yaml_block = parts[1]
    body = parts[2]

    try:
        data = yaml.safe_load(yaml_block) or {}
    except yaml.YAMLError:
        print(f"⚠️ YAML invalide dans {filepath}")
        return

    # Supprime le champ si présent
    if field_name in data:
        del data[field_name]
        print(f"🗑️ Champ '{field_name}' supprimé dans {filepath}")

        # Reconstruit le fichier
        new_yaml = yaml.safe_dump(data, sort_keys=False).strip()
        new_content = f"---\n{new_yaml}\n---{body}"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)


import os
import shutil
import yaml

def move_md_by_yaml_header(root_dir, yaml_key, yaml_value, dest_dir):
    """
    Parcourt root_dir récursivement, lit les headers YAML des fichiers .md,
    et déplace ceux dont yaml_key == yaml_value vers dest_dir.
    Ne déplace pas un fichier s'il est déjà à la destination.
    Affiche des logs pour diagnostiquer les fichiers ignorés.
    """
    root_dir_abs = os.path.abspath(root_dir)
    dest_dir_abs = os.path.abspath(dest_dir)

    if not os.path.exists(dest_dir_abs):
        os.makedirs(dest_dir_abs)

    for dirpath, dirnames, filenames in os.walk(root_dir_abs):
        dirpath_abs = os.path.abspath(dirpath)

        # Si dest_dir est un sous-dossier de root_dir, empêcher os.walk d'y descendre
        # en retirant précisément ce sous-dossier de la liste dirnames.
        # Ne pas sauter le traitement du répertoire courant (root) par erreur.
        filtered = []
        for d in dirnames:
            candidate = os.path.abspath(os.path.join(dirpath_abs, d))
            if candidate == dest_dir_abs:
                print(f"Ignorer le sous-dossier de destination dans la descente: {candidate}")
                continue
            filtered.append(d)
        dirnames[:] = filtered

        for filename in filenames:
            if not filename.lower().endswith(".md"):
                # debug: extension non prise en compte
                print(f"Ignoré (extension) : {os.path.join(dirpath_abs, filename)}")
                continue

            full_path = os.path.join(dirpath_abs, filename)
            full_path_abs = os.path.abspath(full_path)

            # Lecture du fichier entier (gestion BOM)
            try:
                with open(full_path_abs, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(f"Erreur lecture {full_path_abs}: {e}")
                continue

            if not content:
                print(f"Ignoré (vide) : {full_path_abs}")
                continue

            if content.startswith("\ufeff"):
                content = content.lstrip("\ufeff")

            lines = content.splitlines(keepends=True)
            if len(lines) < 3 or lines[0].strip() != "---":
                print(f"Ignoré (pas de header YAML) : {full_path_abs}")
                continue

            # Extraction du bloc YAML
            yaml_lines = []
            for line in lines[1:]:
                if line.strip() == "---":
                    break
                yaml_lines.append(line)

            try:
                header = yaml.safe_load("".join(yaml_lines)) or {}
            except yaml.YAMLError:
                print(f"Ignoré (YAML invalide) : {full_path_abs}")
                continue

            if header.get(yaml_key) == yaml_value:
                dest_path_abs = os.path.abspath(os.path.join(dest_dir_abs, filename))

                # Ne rien faire si le fichier est déjà à la destination (même chemin)
                if full_path_abs == dest_path_abs:
                    print(f"Ignoré (déjà à la destination) : {full_path_abs}")
                    continue

                # Éviter écrasement : trouver un nom disponible
                final_dest = dest_path_abs
                base, ext = os.path.splitext(dest_path_abs)
                i = 1
                while os.path.exists(final_dest):
                    final_dest = f"{base} ({i}){ext}"
                    i += 1

                try:
                    print(f"Déplacement : {full_path_abs} → {final_dest}")
                    shutil.move(full_path_abs, final_dest)
                except Exception as e:
                    print(f"Échec déplacement {full_path_abs} → {final_dest}: {e}")
            else:
                print(f"Ignoré (clé/valeur non correspondante) : {full_path_abs}")