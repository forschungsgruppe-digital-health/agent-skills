#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wo-ist-was-PDF-Builder fuer MII-KDS-Modul-Migrationen.

Festes 6-Seiten-Layout (siehe SKILL.md); alles Modulspezifische kommt aus einer
content.json (Schema: references/example-bildgebung.json). Texte in der JSON sind
reportlab-Paragraph-Markup (HTML-Entities fuer Umlaute erlaubt, KEINE
Unicode-Pfeile/Sub-/Superscripts - Helvetica rendert sie als Kaestchen).

Aufruf:
  python3 build_pdf.py --content content.json --shots <screenshot-dir> --out <datei.pdf>
"""
import argparse
import json
import os

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

MII_BLUE = colors.HexColor("#1a4f7a")
SEC_BLUE = colors.HexColor("#4a7ba6")
ACCENT = colors.HexColor("#c8102e")
LIGHT = colors.HexColor("#eef3f7")
GRID = colors.HexColor("#c9d4dd")
GREY = colors.HexColor("#666666")

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1x", parent=ss["Title"], fontSize=19, leading=23,
                    textColor=MII_BLUE, spaceAfter=4, alignment=0)
SUB = ParagraphStyle("SUBx", parent=ss["Normal"], fontSize=10.5, leading=14,
                     textColor=GREY, spaceAfter=8)
H2 = ParagraphStyle("H2x", parent=ss["Heading2"], fontSize=13, leading=16,
                    textColor=MII_BLUE, spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle("Bodyx", parent=ss["Normal"], fontSize=9.2, leading=12.6)
SMALL = ParagraphStyle("Smallx", parent=ss["Normal"], fontSize=8, leading=10.5,
                       textColor=GREY)
CAP = ParagraphStyle("Capx", parent=SMALL, spaceBefore=2)
CELL = ParagraphStyle("Cellx", parent=ss["Normal"], fontSize=8.2, leading=10.6)
CELLB = ParagraphStyle("CellBx", parent=CELL, fontName="Helvetica-Bold",
                       textColor=colors.white)
CELLH = ParagraphStyle("CellHx", parent=CELL, fontName="Helvetica-Bold",
                       textColor=MII_BLUE)


def P(text, style=BODY):
    return Paragraph(text, style)


def img(path, max_w_mm, max_h_mm=None):
    with PILImage.open(path) as im:
        w, h = im.size
    scale = (max_w_mm * mm) / w
    if max_h_mm and h * scale > max_h_mm * mm:
        scale = (max_h_mm * mm) / h
    return Image(path, width=w * scale, height=h * scale)


def kv_table(rows, label_w=30, total_w=170):
    data = [[P("<b>%s</b>" % a, CELLH), P(b, CELL)] for a, b in rows]
    t = Table(data, colWidths=[label_w * mm, (total_w - label_w) * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build(content, shots, out):
    c = content
    story = []

    # ---- Seite 1: Titel, Meta, Grundideen
    story.append(P(c["title"], H1))
    story.append(P(c["subtitle"], SUB))
    story.append(kv_table(c["meta"]))
    story.append(P(c.get("ideas_heading", "Die drei Grundideen der neuen Struktur"), H2))
    for title, body in c["ideas"]:
        box = Table([[P("<b>%s</b><br/>%s" % (title, body), CELL)]], colWidths=[170 * mm])
        box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
            ("LINEBEFORE", (0, 0), (0, -1), 2.2, ACCENT),
            ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(box)
        story.append(Spacer(1, 3))
    story.append(Spacer(1, 4))
    story.append(P(c["shots_note"], SMALL))
    story.append(PageBreak())

    # ---- Seite 2: Simplifier-Baum
    simp = c["simplifier"]
    story.append(P(simp["heading"], H2))
    imgs = [img(os.path.join(shots, f), 80, 195) for f in simp["images"]]
    if len(imgs) == 1:
        story.append(imgs[0])
    else:
        colw = 170.0 / len(imgs)
        t = Table([imgs], colWidths=[colw * mm] * len(imgs))
        style = [("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("LEFTPADDING", (0, 0), (-1, -1), 3), ("TOPPADDING", (0, 0), (-1, -1), 3)]
        for i in range(len(imgs)):
            style.append(("BOX", (i, 0), (i, 0), 0.5, GRID))
        t.setStyle(TableStyle(style))
        story.append(t)
    story.append(P(simp["caption"], CAP))
    story.append(PageBreak())

    # ---- Seite 3: neue Menues
    menus = c["menus"]
    story.append(P(menus["heading"], H2))
    for item in menus["items"]:
        story.append(P(item["text"], BODY))
        story.append(img(os.path.join(shots, item["img"]),
                         item.get("max_w", 140), item.get("max_h", 70)))
        story.append(Spacer(1, 6))
    story.append(PageBreak())

    # ---- Seite 4: Artefaktseiten-Muster
    art = c["artifact"]
    story.append(P(art["heading"], H2))
    story.append(P(art["body"], BODY))
    story.append(Spacer(1, 4))
    story.append(img(os.path.join(shots, art["img"]), 168, 122))
    story.append(P(art["caption"], CAP))
    story.append(PageBreak())

    # ---- Seiten 5-6: Zuordnungstabelle
    mp = c["mapping"]
    story.append(P(mp["heading"], H2))
    rows = [[P("<b>%s</b>" % h, CELLB) for h in mp["columns"]]]
    section_idx = []
    for sec in mp["sections"]:
        section_idx.append(len(rows))
        rows.append([P(sec["title"], CELLB), P("", CELLB), P("", CELLB)])
        for old, new, url in sec["rows"]:
            rows.append([P(old, CELL), P(new, CELL),
                         P("<font face='Courier' size='6.8'>%s</font>" % url, CELL)])
    tbl = Table(rows, colWidths=[46 * mm, 72 * mm, 52 * mm], repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), MII_BLUE),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f9fb")]),
    ]
    for i in section_idx:
        style.append(("BACKGROUND", (0, i), (-1, i), SEC_BLUE))
        style.append(("SPAN", (0, i), (-1, i)))
    tbl.setStyle(TableStyle(style))
    story.append(tbl)
    story.append(Spacer(1, 8))

    ex = c["extras"]
    story.append(P(ex["heading"], H2))
    story.append(kv_table(ex["rows"], label_w=32))
    story.append(Spacer(1, 6))
    story.append(P(c["source_note"], SMALL))

    def footer(canv, doc):
        canv.saveState()
        canv.setFont("Helvetica", 7)
        canv.setFillColor(GREY)
        canv.drawString(15 * mm, 10 * mm, c["footer"])
        canv.drawRightString(A4[0] - 15 * mm, 10 * mm, "Seite %d" % doc.page)
        canv.restoreState()

    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=14 * mm, bottomMargin=16 * mm,
                            title=c["title"], author="mii-ig-wo-ist-was")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--content", required=True, help="content.json (Schema: references/example-bildgebung.json)")
    ap.add_argument("--shots", required=True, help="Verzeichnis mit den Screenshots")
    ap.add_argument("--out", required=True, help="Ziel-PDF")
    args = ap.parse_args()
    with open(args.content, encoding="utf-8") as f:
        content = json.load(f)
    missing = [i["img"] for i in content["menus"]["items"]
               if not os.path.exists(os.path.join(args.shots, i["img"]))]
    missing += [f for f in content["simplifier"]["images"]
                if not os.path.exists(os.path.join(args.shots, f))]
    if not os.path.exists(os.path.join(args.shots, content["artifact"]["img"])):
        missing.append(content["artifact"]["img"])
    if missing:
        raise SystemExit("Fehlende Screenshots in %s: %s" % (args.shots, ", ".join(missing)))
    out = build(content, args.shots, args.out)
    print("OK:", out)


if __name__ == "__main__":
    main()
