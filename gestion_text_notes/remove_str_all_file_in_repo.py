from pathlib import Path

# Répertoire contenant les fichiers
repertoire = Path(r"C:\Users\virgil.mesle\OneDrive - Sirius Space Services\Documents\obsidian_los\Specs")

# Parcourir aussi les sous-dossiers
recursif = True

# Texte à retirer (identique, au caractère près, à celui ajouté)
texte_a_retirer = """# Requirement Statement"""

fichiers = repertoire.rglob("*") if recursif else repertoire.iterdir()

for fichier in fichiers:
    if not fichier.is_file():
        continue

    try:
        contenu = fichier.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue  # binaire ou illisible : on ignore

    if texte_a_retirer not in contenu:
        continue

    nouveau = contenu.replace(texte_a_retirer, "")  # toutes les occurrences
    fichier.write_text(nouveau, encoding="utf-8")

    n = contenu.count(texte_a_retirer)
    print(f"Modifié ({n} occurrence(s)) : {fichier}")