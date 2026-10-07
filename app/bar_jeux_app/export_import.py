"""Export CSV / PDF de la liste finale des prêts."""

import pandas as pd
import openpyxl
import io
import config_bar_jeux
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import os
import subprocess
import tempfile

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




 

def export_excel_bytes(df, page_size, mode):
  # Copie pour éviter de modifier le DataFrame original de Streamlit
  df_export = df.copy()

  # Ajout des colonnes Jeu01 à Jeu20
  for i in range(1, 21):
    df_export[f"Jeu{i:02d}"] = ""

  # Création d'un buffer en mémoire pour pandas
  excel_buffer = io.BytesIO()
  df_export.to_excel(excel_buffer, index=False, sheet_name="Liste_jeux")
  excel_buffer.seek(0)

  # Chargement avec openpyxl depuis le buffer
  wb = openpyxl.load_workbook(excel_buffer)
  ws = wb["Liste_jeux"]

  # --- Recherche dynamique des indices de colonnes ---
  col_indices = {}
  for col_idx in range(1, ws.max_column + 1):
    header_val = ws.cell(row=1, column=col_idx).value
    if header_val:
      col_indices[header_val] = col_idx

  # --- Largeur des colonnes & Format ---
  if page_size == "A3":
    target_widths = {"Classement":20, "Jeu": 40}
    for i in range(1, 21):
      target_widths[f"Jeu{i:02d}"] = 4

    for header_name, width in target_widths.items():
      if header_name in col_indices:
        col_letter = get_column_letter(col_indices[header_name])
        ws.column_dimensions[col_letter].width = width

    ws.row_dimensions[1].height = 30  # En-tête
    for row in range(2, ws.max_row + 1):
      ws.row_dimensions[row].height = 15  # Données

    ws.page_setup.paperSize = ws.PAPERSIZE_A3
    ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
  else:  # Format A4
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE

  # --- Définition des bordures ---
  thin_border = Border(
      left=Side(style="thin", color="B0B0B0"),
      right=Side(style="thin", color="B0B0B0"),
      top=Side(style="thin", color="B0B0B0"),
      bottom=Side(style="thin", color="B0B0B0"),
  )

  # --- Couleurs conditionnelles ---
  fill_green = PatternFill(
      start_color="57B02C", end_color="57B02C", fill_type="solid"
  )  # AMBIANCE
  fill_red = PatternFill(
      start_color="E67A70", end_color="E67A70", fill_type="solid"
  )  # EXPERT
  fill_red_fonce = PatternFill(
      start_color="8C0E07", end_color="8C0E07", fill_type="solid"
  )  # EXPERT +
  fill_grey = PatternFill(
      start_color="C7C5C5", end_color="C7C5C5", fill_type="solid"
  )  # NON CLASSE
  fill_orange = PatternFill(
      start_color="FF9224", end_color="FF9224", fill_type="solid"
  )  # JEU DUO
  fill_pink = PatternFill(
      start_color="E655DA", end_color="E655DA", fill_type="solid"
  )  # FAMILLE
  fill_yellow = PatternFill(
      start_color="F5E20C", end_color="F5E20C", fill_type="solid"
  )  # INITIE
  fill_blue = PatternFill(
      start_color="1128D6", end_color="1128D6", fill_type="solid"
  )  # ENFANT
  fill_violet = PatternFill(
      start_color="7A0EE3", end_color="7A0EE3", fill_type="solid"
  )  # COOP/SEMI COOP
  fill_blue_light = PatternFill(
      start_color="1FC7FF", end_color="1FC7FF", fill_type="solid"
  )  # ENQUETE/ESCAPE/ENIGME/CASSETETE

  classement_col_idx = col_indices.get("Classement", 1)

  for row in range(2, ws.max_row + 1):
    for col in range(1, ws.max_column + 1):
      ws.cell(row=row, column=col).border = thin_border

    cell_classement = ws.cell(row=row, column=classement_col_idx)
    val = cell_classement.value

    if val == config_bar_jeux._CLS_ENQUETE_ESCAPE :
      cell_classement.fill = fill_blue_light
    elif val == config_bar_jeux._CLS_COOP :
      cell_classement.fill = fill_violet
    elif val == config_bar_jeux._CLS_INITIE :
      cell_classement.fill = fill_yellow
    elif val == config_bar_jeux._CLS_ENFANT :
      cell_classement.fill = fill_blue
    elif val == config_bar_jeux._CLS_AMBIANCE :
      cell_classement.fill = fill_green
    elif val == config_bar_jeux._CLS_FAMILLE :
      cell_classement.fill = fill_pink
    elif val == config_bar_jeux._CLS_EXPERT :
      cell_classement.fill = fill_red
    elif val == config_bar_jeux._CLS_EXPERT_PLUS :
      cell_classement.fill = fill_red_fonce
    elif val == config_bar_jeux._CLS_NON_CLASSE :
      cell_classement.fill = fill_grey
    elif val == config_bar_jeux._CLS_DUO :
      cell_classement.fill = fill_orange


    


  ws.sheet_properties.pageSetUpPr.fitToPage = True
  ws.page_setup.fitToWidth = 1

  if mode == "excel" :  

      # Sauvegarde dans un buffer final et récupération des octets (bytes)
      output_final = io.BytesIO()
      wb.save(output_final)
      output_final.seek(0)
      return output_final.getvalue()
  elif mode == "pdf" :
      # --- Conversion en PDF via LibreOffice (dans un dossier temporaire) ---
      with tempfile.TemporaryDirectory() as tmpdirname:
        excel_path = os.path.join(tmpdirname, "temp.xlsx")
        wb.save(excel_path)
    
        # Appel de LibreOffice en arrière-plan pour convertir le fichier
        subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                tmpdirname,
                excel_path,
            ],
            check=True,
        )
    
        pdf_path = os.path.join(tmpdirname, "temp.pdf")
    
        # Lecture du fichier PDF converti sous forme de bytes
        with open(pdf_path, "rb") as f:
          pdf_bytes = f.read()
        return pdf_bytes
