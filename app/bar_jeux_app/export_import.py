"""Export CSV / PDF de la liste finale des prêts."""
import io

import pandas as pd


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
