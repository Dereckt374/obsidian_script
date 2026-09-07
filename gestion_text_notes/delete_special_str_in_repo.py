from pathlib import Path

# === CONFIGURATION ===
REPERTOIRE = Path(r"C:\Users\virgil.mesle\OneDrive - Sirius Space Services\Documents\obsidian_system_analysis\2.Functionnal\Functions")
CHAINE_A_SUPPRIMER = "../Functions/"

# Extensions considérées comme des notes
EXTENSIONS = {".md"}

# === TRAITEMENT ===
for fichier in REPERTOIRE.rglob("*"):
    if fichier.is_file() and fichier.suffix.lower() in EXTENSIONS:
        try:
            contenu = fichier.read_text(encoding="utf-8")

            if CHAINE_A_SUPPRIMER in contenu:
                nouveau_contenu = contenu.replace(CHAINE_A_SUPPRIMER, "")
                fichier.write_text(nouveau_contenu, encoding="utf-8")
                print(f"Modifié : {fichier}")

        except UnicodeDecodeError:
            print(f"Ignoré (encodage non compatible) : {fichier}")
        except Exception as e:
            print(f"Erreur avec {fichier} : {e}")

print("Terminé.")