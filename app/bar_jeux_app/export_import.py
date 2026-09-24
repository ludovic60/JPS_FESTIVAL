"""Export CSV / PDF de la liste finale des prêts."""
import io

import pandas as pd
import openpyxl

def loans_matrix(finals, users, loans):
    rows = []
    for ckey, g in finals:
        row = {"Jeu": g.get("nom_jeu_complet") or g.get("nom_jeu") or "Jeu"}
        lent = set(loans.get(ckey, []))
        for u in users:
            row[u["name"]] = "Oui" if u["id"] in lent else ""
        rows.append(row)
    return pd.DataFrame(rows)


def to_csv(df) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def to_excel(df) :
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="liste_jeux")
        worksheet = writer.sheets["liste_jeux"]
        
        # Supposons que la colonne des URLs d'images est la première (colonne A, index 1)
        # On parcourt les lignes à partir de la ligne 2 (la ligne 1 étant l'en-tête)
        for row_idx, url in enumerate(df['Couverture Jeu'], start=2):
            if pd.notna(url) and str(url).startswith("http"):
                try:
                    # 1. Télécharger l'image depuis l'URL
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        img_io = io.BytesIO(response.content)
                        
                        # 2. Ouvrir avec Pillow pour redimensionner (optionnel mais conseillé pour Excel)
                        img = PILImage.open(img_io)
                        img.thumbnail((80, 80)) # Taille max de l'image dans la cellule
                        
                        # Sauvegarder dans un buffer temporaire pour openpyxl
                        temp_img_io = io.BytesIO()
                        img.save(temp_img_io, format="PNG")
                        temp_img_io.seek(0)
                        
                        # 3. Créer l'objet Image pour openpyxl
                        xl_img = OpenpyxlImage(temp_img_io)
                        
                        # 4. Positionner l'image dans la cellule correspondante (ex: A2, A3, etc.)
                        cell_coordinate = f"A{row_idx}"
                        worksheet.add_image(xl_img, cell_coordinate)
                        
                        # 5. Ajuster la hauteur de la ligne pour que l'image rentre bien visuellement
                        worksheet.row_dimensions[row_idx].height = 65
                except Exception as e:
                    # En cas d'erreur de téléchargement, on ignore l'image pour ne pas bloquer l'export
                    print(f"Erreur image ligne {row_idx}: {e}")
                    pass
                    
        # Définir la largeur de la colonne A pour l'image
        worksheet.column_dimensions['A'].width = 15
        
    return output.getvalue()


def to_pdf(df, title="Liste finale des prêts") -> bytes:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), title=title)
    styles = getSampleStyleSheet()
    data = [list(df.columns)] + df.astype(str).values.tolist()
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#002FA7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
    ]))
    doc.build([Paragraph(title, styles["Title"]), Spacer(1, 12), table])
    return buf.getvalue()
