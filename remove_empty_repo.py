import os

def supprimer_dossiers_vides(chemin_racine):
    """
    Supprime récursivement les dossiers vides à partir du chemin spécifié.
    """
    # Parcourir les sous-dossiers en profondeur (postorder)
    for dossier_racine, sous_dossiers, fichiers in os.walk(chemin_racine, topdown=False):
        for sous_dossier in sous_dossiers:
            chemin_complet = os.path.join(dossier_racine, sous_dossier)
            if not os.listdir(chemin_complet):  # Vérifier si le dossier est vide
                os.rmdir(chemin_complet)
                print(f"Supprimé : {chemin_complet}")
    
    # Vérifier si le dossier racine est vide et le supprimer s'il l'est
    if not os.listdir(chemin_racine):
        os.rmdir(chemin_racine)
        print(f"Supprimé : {chemin_racine}")

# Exemple d'utilisation
chemin = '/home/vmesle/Documents/Obsidian'  # Remplacez par votre chemin
supprimer_dossiers_vides(chemin)

