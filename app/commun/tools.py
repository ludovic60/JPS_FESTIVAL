import random

# Fixer le seed (42) garantit que les couleurs attribuées ne changeront JAMAIS, 
# même si vous relancez le script ou l'application.
random.seed(42)
def  calc_color( liste) : 
    couleurs_fixes = {}
    for val in liste :
        if val == "n/a":
            couleurs_fixes[val] = "#C7C5C5" # Gris fixe pour n/a
        else:
            # Génération d'une couleur hexadécimale stable
            r = random.randint(40, 220)
            g = random.randint(40, 220)
            b = random.randint(40, 220)
            couleurs_fixes[val] = f"#{r:02x}{g:02x}{b:02x}"

    return couleurs_fixes


def remove_emojis(text):
    if not isinstance(text, str):
      return str(text)
    # Expression régulière pour cibler et supprimer les émojis
    return re.sub(
        r"[\U00010000-\U0010ffff]|[\u2600-\u27BF]|[\U0001f300-\U0001f64f]|[\U0001f680-\U0001f6ff]",
        "",
        text,
    ).strip()
