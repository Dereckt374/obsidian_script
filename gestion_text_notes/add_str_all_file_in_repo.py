from pathlib import Path

"""
Insertion de texte dans tous les fichiers d'un répertoire.

Parcourt chaque fichier du répertoire indiqué et y insère un bloc de texte
à la position choisie :
  - "debut" : avant tout le contenu existant
  - "fin"   : après tout le contenu existant
  - "avant" : juste avant la première occurrence d'une chaîne cible
  - "apres" : après la fin de la ligne contenant la première occurrence
              (dans les deux derniers cas, le fichier est ignoré si la
               chaîne est absente)

Les fichiers sont lus intégralement en mémoire puis réécrits en UTF-8.
L'original est écrasé, sans sauvegarde préalable.

Configuration : variables `repertoire`, `mode`, `chaine_cible`
et `texte_a_inserer` en tête de script.
"""

# Répertoire contenant les fichiers
repertoire = Path(r"C:\Users\virgil.mesle\Documents\architecture-systeme\2.Functional\Spec_test")

# Position d'insertion : "debut", "fin", "avant" ou "apres"
mode = "fin"

# Chaîne cible (utilisée uniquement si mode == "avant" ou "apres")
chaine_cible = """
"""

# Texte à insérer
texte_a_inserer = """
# Rational

# Childrens
```base
filters:
  and:
    - file.hasLink(this.file)
    - not:
        - this.file.hasLink(file.file)
views:
  - type: table
    name: Tableau
    filters:
      and:
        - '!file.name.startsWith("temp")'
    groupBy:
      property: tags
      direction: ASC
```
"""

for fichier in repertoire.iterdir():
    if not fichier.is_file():
        continue

    contenu = fichier.read_text(encoding="utf-8")

    if mode == "debut":
        nouveau = texte_a_inserer + contenu

    elif mode == "fin":
        nouveau = contenu + texte_a_inserer

    elif mode == "avant":
        position = contenu.find(chaine_cible)
        if position == -1:
            print(f"Ignoré (chaîne absente) : {fichier}")
            continue
        nouveau = contenu[:position] + texte_a_inserer + contenu[position:]

    elif mode == "apres":
        position = contenu.find(chaine_cible)
        if position == -1:
            print(f"Ignoré (chaîne absente) : {fichier}")
            continue
        fin_ligne = contenu.find("\n", position + len(chaine_cible))
        if fin_ligne == -1:
            nouveau = contenu + "\n" + texte_a_inserer
        else:
            coupure = fin_ligne + 1
            nouveau = contenu[:coupure] + texte_a_inserer + contenu[coupure:]

    else:
        raise ValueError(f"Mode inconnu : {mode}")

    fichier.write_text(nouveau, encoding="utf-8")
    print(f"Modifié : {fichier}")