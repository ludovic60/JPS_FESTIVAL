"""Export CSV / PDF de la liste finale des prêts."""

import pandas as pd
import openpyxl
import io
import config_bar_jeux
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import os
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, A4, landscape, portrait
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

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
  df_export = df.copy()
  for i in range(1, 21):
    df_export[f"Jeu{i:02d}"] = ""

  # --- Si mode EXCEL : on utilise openpyxl (votre code original) ---
  if mode == "excel":
    excel_buffer = io.BytesIO()
    df_export.to_excel(excel_buffer, index=False, sheet_name="Liste_jeux")
    excel_buffer.seek(0)
    wb = openpyxl.load_workbook(excel_buffer)
    ws = wb["Liste_jeux"]

    col_indices = {}
    for col_idx in range(1, ws.max_column + 1):
      header_val = ws.cell(row=1, column=col_idx).value
      if header_val:
        col_indices[header_val] = col_idx

    if page_size == "A3":
      target_widths = {"Classement": 20, "Jeu": 40}
      for i in range(1, 21):
        target_widths[f"Jeu{i:02d}"] = 4
      for header_name, width in target_widths.items():
        if header_name in col_indices:
          ws.column_dimensions[
              get_column_letter(col_indices[header_name])
          ].width = width
      ws.page_setup.paperSize = ws.PAPERSIZE_A3
      ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
    else:
      ws.page_setup.paperSize = ws.PAPERSIZE_A4
      ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE

    thin_border = Border(
        left=Side(style="thin", color="B0B0B0"),
        right=Side(style="thin", color="B0B0B0"),
        top=Side(style="thin", color="B0B0B0"),
        bottom=Side(style="thin", color="B0B0B0"),
    )
    classement_col_idx = col_indices.get("Classement", 1)

    for row in range(2, ws.max_row + 1):
      for col in range(1, ws.max_column + 1):
        ws.cell(row=row, column=col).border = thin_border
      # (Vos applications de couleurs openpyxl restent ici si besoin pour le fichier Excel)

    output_final = io.BytesIO()
    wb.save(output_final)
    output_final.seek(0)
    return output_final.getvalue()

  # --- Si mode PDF : Génération propre en pur Python via ReportLab ---
  elif mode == "pdf":
    pdf_buffer = io.BytesIO()

    # Orientation du PDF
    if page_size == "A3":
      pagesize = portrait(A3)
    else:
      pagesize = landscape(A4)

    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=pagesize,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20,
    )
    elements = []

    # Préparation des données pour le tableau PDF
    data = [df_export.columns.tolist()] + df_export.astype(str).values.tolist()

    table = Table(data)

    # Style de base du tableau PDF
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B0B0B0")),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
    ]

    # Application des couleurs conditionnelles sur la colonne "Classement" dans ReportLab
    try:
      classement_idx = df_export.columns.get_loc("Classement")
      color_map = {
          config_bar_jeux._CLS_ENQUETE_ESCAPE: colors.HexColor("#1FC7FF"),
          config_bar_jeux._CLS_COOP: colors.HexColor("#7A0EE3"),
          config_bar_jeux._CLS_INITIE: colors.HexColor("#F5E20C"),
          config_bar_jeux._CLS_ENFANT: colors.HexColor("#1128D6"),
          config_bar_jeux._CLS_AMBIANCE: colors.HexColor("#57B02C"),
          config_bar_jeux._CLS_FAMILLE: colors.HexColor("#E655DA"),
          config_bar_jeux._CLS_EXPERT: colors.HexColor("#E67A70"),
          config_bar_jeux._CLS_EXPERT_PLUS: colors.HexColor("#8C0E07"),
          config_bar_jeux._CLS_NON_CLASSE: colors.HexColor("#C7C5C5"),
          config_bar_jeux._CLS_DUO: colors.HexColor("#FF9224"),
      }

      for row_idx, row in enumerate(df_export.itertuples(), start=1):
        val = getattr(row, "Classement", None)
        if val in color_map:
          style.append(
              ("BACKGROUND", (classement_idx, row_idx), (classement_idx, row_idx), color_map[val])
          )
    except Exception:
      pass

    table.setStyle(TableStyle(style))
    elements.append(table)
    doc.build(elements)

    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


