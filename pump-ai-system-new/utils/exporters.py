# =============================================================================
# utils/exporters.py
# Word (.docx), PDF (.pdf), CSV (.csv) export builders
#
# Required packages (run once):
#   pip install python-docx reportlab
# =============================================================================
import io
import csv
from datetime import datetime

DEVELOPER = "Zunair Shahzad"
DEGREE    = "Chemical Engineering"
UNI       = "UET Lahore (New Campus)"
BATCH     = "2022-2026"

def _check_pkg(pkg_name, install_name):
    """Return True if importable, else raise with helpful message."""
    import importlib
    if importlib.util.find_spec(pkg_name) is None:
        raise ImportError(
            f"Package '{install_name}' is not installed.\n"
            f"Run this in your terminal:\n"
            f"   pip install {install_name}\n"
            f"Then restart Streamlit."
        )
    return True

# ─────────────────────────────────────────────────────────────────────────────
# CSV  (no extra dependencies)
# ─────────────────────────────────────────────────────────────────────────────
def build_csv(inputs_d, results_d, sp_d):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["AI-Assisted Pump Design Platform",
                     f"Developer: {DEVELOPER}",
                     f"{DEGREE} | {UNI} | {BATCH}"])
    writer.writerow(["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])
    writer.writerow(["SECTION", "PARAMETER", "VALUE"])
    for k, v in inputs_d.items():
        writer.writerow(["INPUT", k, v])
    for k, v in results_d.items():
        writer.writerow(["RESULT", k, v])
    for k, v in sp_d.items():
        writer.writerow(["PUMP SPECIFIC", k, v])
    writer.writerow([])
    writer.writerow(["DISCLAIMER", "Engineering estimates only.",
                     "Verify with licensed P.Eng / PE."])
    return buf.getvalue().encode("utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# WORD (.docx)   requires: pip install python-docx
# ─────────────────────────────────────────────────────────────────────────────
def build_docx(pump_type, inputs_d, results_d, sp_d, ds_sections=None):
    _check_pkg("docx", "python-docx")

    from docx import Document
    from docx.shared import Pt, RGBColor, Cm, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    doc = Document()

    for sec in doc.sections:
        sec.top_margin = Cm(1.8); sec.bottom_margin = Cm(2)
        sec.left_margin = Cm(2.2); sec.right_margin = Cm(2.2)

    def shade_cell(cell, hex_fill):
        tc = cell._tc; tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:fill'), hex_fill.lstrip('#'))
        shd.set(qn('w:val'), 'clear')
        tcPr.append(shd)

    def set_cell_text(cell, text, bold=False, size=9, rgb=(0,0,0), center=False):
        p = cell.paragraphs[0]
        p.clear()
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(str(text))
        run.font.bold = bold
        run.font.size = Pt(size)
        run.font.color.rgb = RGBColor(*rgb)

    def add_para(text, size=10, bold=False, rgb=(0,0,0),
                 center=False, space_before=0, space_after=6):
        p = doc.add_paragraph()
        if center: p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after  = Pt(space_after)
        run = p.add_run(text)
        run.font.size = Pt(size); run.font.bold = bold
        run.font.color.rgb = RGBColor(*rgb)
        return p

    # ── Cover ─────────────────────────────────────────────────────────────────
    add_para("SmartPump Designer", 18, True, (0,80,160), center=True, space_after=4)
    add_para(f"Developed by  {DEVELOPER}", 10, False, (0,100,0), center=True, space_after=2)
    add_para(f"{DEGREE}  ·  {UNI}  ·  Batch {BATCH}", 10, False, (21,101,192), center=True, space_after=4)
    add_para("API 610 CENTRIFUGAL PUMP DATA SHEET", 16, True, (0,70,140), center=True, space_after=2)
    add_para("International Standard · 12th Edition · Annex A Format", 9, False, (80,80,80), center=True, space_after=2)
    add_para(f"Project: SmartPump Designer  ·  Pump Type: {pump_type}  ·  "
             f"Generated: {datetime.now().strftime('%d %B %Y  %H:%M')}", 9, False,
             (0,120,100), center=True, space_after=8)

    # Horizontal rule
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'),'single'); bottom.set(qn('w:sz'),'4')
    bottom.set(qn('w:space'),'1'); bottom.set(qn('w:color'),'1565C0')
    pBdr.append(bottom); pPr.append(pBdr)

    # ── Section accent RGB palette ─────────────────────────────────────────────
    SEC_RGB = [
        (0,119,204), (0,135,90),  (204,136,0), (204,51,0),  (123,0,204),
        (0,119,136), (153,102,0), (0,102,34),  (136,0,102), (0,68,136),
        (85,85,0),   (0,68,68),   (68,0,68),   (0,34,68),
    ]

    # ── Section builder ────────────────────────────────────────────────────────
    def add_ds_section(sec_idx, sec_title, sec_rows):
        r, g, b = SEC_RGB[sec_idx % len(SEC_RGB)]
        hex_bg = f"{r:02x}{g:02x}{b:02x}"

        # Heading row
        tbl = doc.add_table(rows=1, cols=3)
        tbl.style = 'Table Grid'
        hdr = tbl.rows[0]
        hdr.cells[0].merge(hdr.cells[2])
        set_cell_text(hdr.cells[0], sec_title, bold=True, size=10, rgb=(255,255,255))
        shade_cell(hdr.cells[0], "#" + hex_bg)

        # Column header row
        col_row = tbl.add_row()
        for ci, lbl in enumerate(["Parameter", "Specified Value", "Reference / Note"]):
            set_cell_text(col_row.cells[ci], lbl, bold=True, size=8, rgb=(255,255,255))
            shade_cell(col_row.cells[ci], "#" + hex_bg)

        # Data rows
        for j, row in enumerate(sec_rows):
            param = str(row[0]); val = str(row[1])
            note  = str(row[2]) if len(row) > 2 else ""

            if param.startswith("───") or param.startswith("─"):
                dr = tbl.add_row()
                dr.cells[0].merge(dr.cells[2])
                set_cell_text(dr.cells[0], param, bold=True, size=8, rgb=(r,g,b))
                shade_cell(dr.cells[0], "#e8f4ff")
                continue

            dr = tbl.add_row()
            fill = "f0f4ff" if j % 2 == 0 else "ffffff"
            set_cell_text(dr.cells[0], param, bold=True, size=8.5, rgb=(30,30,80))
            shade_cell(dr.cells[0], fill)

            # Smart value color
            if "✅" in val or "SAFE" in val or "PASS" in val:
                vrgb = (0,100,0)
            elif "🚨" in val or "RISK" in val or "FAIL" in val:
                vrgb = (180,0,0)
            elif "⚠️" in val or "MARGINAL" in val:
                vrgb = (150,80,0)
            else:
                vrgb = (0,40,100)

            set_cell_text(dr.cells[1], val, bold=True, size=8.5, rgb=vrgb)
            shade_cell(dr.cells[1], fill)
            set_cell_text(dr.cells[2], note, size=7.5, rgb=(80,80,100))
            shade_cell(dr.cells[2], fill)

        # Column widths
        for row in tbl.rows:
            row.cells[0].width = Cm(6.5)
            row.cells[1].width = Cm(6.0)
            row.cells[2].width = Cm(4.5)

        doc.add_paragraph()  # spacing

    # ── Render ds_sections or fallback ────────────────────────────────────────
    if ds_sections:
        for sec_idx, sec_data in enumerate(ds_sections):
            add_ds_section(sec_idx, sec_data["title"], sec_data["rows"])
    else:
        # Fallback basic sections
        def make_basic_section(title_text, data_dict, hdr_hex="1565C0"):
            p = doc.add_heading(title_text, level=1)
            for run in p.runs:
                run.font.color.rgb = RGBColor(21,101,192)
            tbl = doc.add_table(rows=1, cols=2)
            tbl.style = 'Table Grid'
            hdr_cells = tbl.rows[0].cells
            hdr_cells[0].text = "Parameter"; hdr_cells[1].text = "Value"
            for c in hdr_cells:
                for run in c.paragraphs[0].runs:
                    run.font.bold = True; run.font.size = Pt(9)
                    run.font.color.rgb = RGBColor(255,255,255)
                shade_cell(c, hdr_hex)
            for i, (k, v) in enumerate(data_dict.items()):
                row = tbl.add_row()
                row.cells[0].text = str(k); row.cells[1].text = str(v)
                for c in row.cells:
                    c.paragraphs[0].runs[0].font.size = Pt(9)
                if i % 2 == 0:
                    for c in row.cells: shade_cell(c, "E8F5E9")
            for row in tbl.rows:
                row.cells[0].width = Cm(9); row.cells[1].width = Cm(7)
            doc.add_paragraph()

        make_basic_section("📥 Process Inputs",        inputs_d,  "1565C0")
        make_basic_section("📊 Design Results",        results_d, "00796B")
        make_basic_section(f"🔬 {pump_type} Specific", sp_d,      "E65100")

    # ── References ────────────────────────────────────────────────────────────
    p = doc.add_heading("📚 Engineering References", level=1)
    for run in p.runs:
        run.font.color.rgb = RGBColor(80,0,120)
    for ref in [
        "[1] API 610 12th Ed. — Centrifugal Pumps for Petroleum, Petrochemical and Natural Gas Industries",
        "[2] API 682 4th Ed. — Pumps — Shaft Sealing Systems",
        "[3] API 671 — Special Purpose Couplings",
        "[4] ANSI/HI 1.1-1.6, 9.6.1, 9.6.3 — Hydraulic Institute Standards",
        "[5] ISO 5199 / ISO 9905 — Technical Specifications for Centrifugal Pumps",
        "[6] Karassik et al. — Pump Handbook, 4th Edition (McGraw-Hill, 2008)",
        "[7] Perry's Chemical Engineers' Handbook, 9th Ed. (2018)",
        "[8] Crane Technical Paper No. 410 — Flow of Fluids (2013)",
        "[9] Stepanoff — Centrifugal and Axial Flow Pumps, 2nd Ed.",
    ]:
        pr = doc.add_paragraph(ref, style='List Bullet')
        pr.runs[0].font.size = Pt(8.5)

    doc.add_paragraph()
    disc = doc.add_paragraph(
        "DISCLAIMER: Engineering estimates only (±10-15% accuracy). "
        "All designs must be reviewed by a licensed Professional Engineer (P.Eng/PE) "
        "before implementation. SmartPump Designer — not a substitute for professional engineering judgment.")
    disc.runs[0].font.size = Pt(8); disc.runs[0].font.color.rgb = RGBColor(180,0,0)
    disc.alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_para(f"SmartPump Designer  ·  {DEVELOPER}  ·  {DEGREE}  ·  {UNI}  ·  Batch {BATCH}",
             8, False, (80,80,80), center=True, space_before=6)

    buf = io.BytesIO()
    doc.save(buf); buf.seek(0)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# PDF (.pdf)   requires: pip install reportlab
# Now includes COMPLETE API 610 datasheet sections
# ─────────────────────────────────────────────────────────────────────────────
def build_pdf(pump_type, inputs_d, results_d, sp_d, ds_sections=None):
    _check_pkg("reportlab", "reportlab")

    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable, PageBreak)
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=1.8*cm, bottomMargin=2*cm,
                            leftMargin=2.2*cm, rightMargin=2.2*cm)
    styles = getSampleStyleSheet()
    story  = []

    # ── Color palette ─────────────────────────────────────────────────────────
    C = {
        "blue":    colors.HexColor("#1565C0"),
        "green":   colors.HexColor("#006400"),
        "gold":    colors.HexColor("#B8860B"),
        "red":     colors.HexColor("#C62828"),
        "white":   colors.white,
        "lgray":   colors.HexColor("#f0f4f8"),
        "dgray":   colors.HexColor("#1a1a2e"),
        "mgray":   colors.HexColor("#cccccc"),
        "teal":    colors.HexColor("#00796B"),
        "orange":  colors.HexColor("#E65100"),
        "cyan":    colors.HexColor("#00838f"),
        "purple":  colors.HexColor("#6A1B9A"),
    }

    # ── Section accent colors (matching web app) ───────────────────────────────
    SEC_PDF_COLORS = [
        colors.HexColor("#0077cc"),  # §1 Blue
        colors.HexColor("#00875a"),  # §2 Green
        colors.HexColor("#cc8800"),  # §3 Gold
        colors.HexColor("#cc3300"),  # §4 Orange-Red
        colors.HexColor("#7b00cc"),  # §5 Purple
        colors.HexColor("#007788"),  # §6 Teal
        colors.HexColor("#996600"),  # §7 Amber
        colors.HexColor("#006622"),  # §8 Dark Green
        colors.HexColor("#880066"),  # §9 Magenta
        colors.HexColor("#004488"),  # §10 Dark Blue
        colors.HexColor("#555500"),  # §11 Olive
        colors.HexColor("#004444"),  # §12 Dark Teal
        colors.HexColor("#440044"),  # §13 Dark Purple
        colors.HexColor("#002244"),  # §14 Navy
    ]

    s = lambda name, **kw: ParagraphStyle(name, **kw)
    S = {
        "dev":    s("dev",  fontSize=9,  textColor=C["green"],  alignment=TA_CENTER, spaceAfter=1),
        "name":   s("name", fontSize=15, textColor=C["green"],  fontName="Helvetica-Bold",
                    alignment=TA_CENTER, spaceAfter=2),
        "uni":    s("uni",  fontSize=10, textColor=C["blue"],   alignment=TA_CENTER, spaceAfter=3),
        "batch":  s("batch",fontSize=9,  textColor=C["green"],  alignment=TA_CENTER, spaceAfter=3),
        "title":  s("title",fontSize=18, textColor=C["blue"],   fontName="Helvetica-Bold",
                    alignment=TA_CENTER, spaceAfter=3),
        "sub":    s("sub",  fontSize=8.5,textColor=C["dgray"],  alignment=TA_CENTER, spaceAfter=8),
        "proj":   s("proj", fontSize=10, textColor=C["teal"],   alignment=TA_CENTER,
                    fontName="Helvetica-Bold", spaceAfter=6),
        "sec":    s("sec",  fontSize=11, textColor=C["white"],  fontName="Helvetica-Bold",
                    spaceAfter=3, spaceBefore=10,
                    leftIndent=0, borderPadding=(5,8,5,8)),
        "disc":   s("disc", fontSize=7,  textColor=C["red"],    alignment=TA_CENTER, spaceBefore=8),
        "ref":    s("ref",  fontSize=8,  textColor=C["dgray"],  leftIndent=10, spaceAfter=2),
        "note":   s("note", fontSize=7.5,textColor=C["mgray"],  leftIndent=12, spaceAfter=1),
        "footer": s("footer",fontSize=7, textColor=C["mgray"],  alignment=TA_CENTER),
    }

    # ── Cover page ────────────────────────────────────────────────────────────
    story += [
        Spacer(1, .4*cm),
        Paragraph("SmartPump Designer", S["name"]),
        Paragraph(f"Developed by  <font color='#B8860B'><b>{DEVELOPER}</b></font>", S["dev"]),
        Paragraph(f'<font color="#B8860B">{DEGREE}</font>  ·  '
                  f'<font color="#1565C0"><b>{UNI}</b></font>', S["uni"]),
        Paragraph(BATCH, S["batch"]),
        HRFlowable(width="100%", thickness=2, color=C["blue"], spaceAfter=10),
        Paragraph("API 610 PUMP DATA SHEET", S["title"]),
        Paragraph("International Standard · 12th Edition · Annex A Format", S["sub"]),
        Paragraph(f"Pump Type: {pump_type}  ·  "
                  f"Project: SmartPump Designer  ·  "
                  f"Generated: {datetime.now().strftime('%d %B %Y  %H:%M')}", S["proj"]),
        HRFlowable(width="100%", thickness=1, color=C["blue"], spaceAfter=8),
    ]

    # ── Quick summary KPI strip ───────────────────────────────────────────────
    kpi_keys = ["TDH (m)", "Flow (m³/s)", "P_shaft (kW)", "P_motor (kW)", "η_overall (%)"]
    kpi_vals = []
    for k in kpi_keys:
        v = results_d.get(k, inputs_d.get(k, "—"))
        kpi_vals.append([Paragraph(f"<b>{k}</b>", ParagraphStyle("k",fontSize=7,
                         textColor=C["white"],fontName="Helvetica-Bold",alignment=TA_CENTER)),
                         Paragraph(str(v), ParagraphStyle("v",fontSize=9,
                         textColor=colors.HexColor("#00ff88"),fontName="Helvetica-Bold",
                         alignment=TA_CENTER))])
    if kpi_vals:
        kpi_tbl = Table([[row[0] for row in kpi_vals],
                          [row[1] for row in kpi_vals]],
                         colWidths=[3.4*cm]*len(kpi_vals))
        kpi_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,0), C["blue"]),
            ("BACKGROUND", (0,1),(-1,1), colors.HexColor("#0d1117")),
            ("GRID",       (0,0),(-1,-1), 0.5, colors.HexColor("#333366")),
            ("TOPPADDING", (0,0),(-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ]))
        story.append(kpi_tbl)
        story.append(Spacer(1,.3*cm))

    # ── Section renderer ──────────────────────────────────────────────────────
    def add_ds_section(sec_idx, sec_title, sec_rows, accent_color):
        # Section heading block
        heading_tbl = Table([[Paragraph(sec_title, ParagraphStyle(
            "sh", fontSize=10, textColor=C["white"],
            fontName="Helvetica-Bold", leftIndent=5
        ))]],
            colWidths=[17*cm], rowHeights=[0.65*cm])
        heading_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(0,0), accent_color),
            ("TOPPADDING", (0,0),(0,0), 6),
            ("BOTTOMPADDING",(0,0),(0,0),6),
            ("LEFTPADDING",(0,0),(0,0),10),
        ]))
        story.append(heading_tbl)

        # Data rows
        tbl_data = [[
            Paragraph("<b>Parameter</b>", ParagraphStyle("ph",fontSize=8,
                      textColor=C["white"],fontName="Helvetica-Bold")),
            Paragraph("<b>Specified Value</b>", ParagraphStyle("vh",fontSize=8,
                      textColor=C["white"],fontName="Helvetica-Bold")),
            Paragraph("<b>Reference / Note</b>", ParagraphStyle("nh",fontSize=7,
                      textColor=C["white"],fontName="Helvetica-Bold")),
        ]]

        for j, row in enumerate(sec_rows):
            param = str(row[0]); val = str(row[1])
            note  = str(row[2]) if len(row) > 2 else ""

            # Skip separator rows
            if param.startswith("───") or param.startswith("─"):
                tbl_data.append([
                    Paragraph(f"<b>{param}</b>", ParagraphStyle("sep",fontSize=7.5,
                              textColor=accent_color, fontName="Helvetica-Bold")),
                    Paragraph("", styles["Normal"]),
                    Paragraph("", styles["Normal"]),
                ])
                continue

            # Value styling
            val_color = "#006400"
            if "✅" in val or "SAFE" in val or "PASS" in val:
                val_color = "#006400"
            elif "🚨" in val or "RISK" in val or "FAIL" in val:
                val_color = "#cc0000"
            elif "⚠️" in val or "MARGINAL" in val:
                val_color = "#996600"
            else:
                val_color = "#1a1a2e"

            tbl_data.append([
                Paragraph(param, ParagraphStyle("p",fontSize=8.5,
                          textColor=colors.HexColor("#1a1a2e"), fontName="Helvetica-Bold")),
                Paragraph(val, ParagraphStyle("v",fontSize=8.5,
                          textColor=colors.HexColor(val_color),
                          fontName="Helvetica-Bold")),
                Paragraph(note, ParagraphStyle("n",fontSize=7,
                          textColor=colors.HexColor("#555577"),
                          fontName="Helvetica-Oblique")),
            ])

        tbl = Table(tbl_data, colWidths=[6.5*cm, 6.0*cm, 4.5*cm], repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),   accent_color),
            ("TEXTCOLOR",     (0,0), (-1,0),   C["white"]),
            ("ROWBACKGROUNDS",(0,1), (-1,-1),  [colors.HexColor("#f4f8ff"),
                                                colors.HexColor("#ffffff")]),
            ("GRID",          (0,0), (-1,-1),  0.4, colors.HexColor("#ccddee")),
            ("LEFTPADDING",   (0,0), (-1,-1),  7),
            ("RIGHTPADDING",  (0,0), (-1,-1),  5),
            ("TOPPADDING",    (0,0), (-1,-1),  4),
            ("BOTTOMPADDING", (0,0), (-1,-1),  4),
            ("VALIGN",        (0,0), (-1,-1),  "MIDDLE"),
            ("LINEBELOW",     (0,0), (-1,0),   1.5, accent_color),
        ]))
        story.append(tbl)
        story.append(Spacer(1, .4*cm))

    # ── Render ds_sections if available (complete API 610 datasheet) ──────────
    if ds_sections:
        for sec_idx, sec_data in enumerate(ds_sections):
            accent = SEC_PDF_COLORS[sec_idx % len(SEC_PDF_COLORS)]
            add_ds_section(sec_idx, sec_data["title"], sec_data["rows"], accent)

            # Page break every 3 sections to avoid overflow
            if (sec_idx + 1) % 3 == 0 and sec_idx < len(ds_sections) - 1:
                story.append(PageBreak())
    else:
        # Fallback: basic inputs/results tables
        def add_basic_section(heading, data_dict, hdr_color=C["blue"]):
            heading_tbl = Table([[Paragraph(f"  {heading}", ParagraphStyle(
                "bh",fontSize=10,textColor=C["white"],fontName="Helvetica-Bold"))]],
                colWidths=[17*cm])
            heading_tbl.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(0,0),hdr_color),
                ("TOPPADDING",(0,0),(0,0),6),("BOTTOMPADDING",(0,0),(0,0),6),
            ]))
            story.append(heading_tbl)
            rows = [["Parameter","Value"]]
            for k, v in data_dict.items():
                rows.append([str(k), str(v)])
            tbl = Table(rows, colWidths=[9*cm, 8*cm], repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),hdr_color),
                ("TEXTCOLOR",(0,0),(-1,0),C["white"]),
                ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                ("FONTSIZE",(0,0),(-1,-1),8.5),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#f0f4ff"),C["white"]]),
                ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cccccc")),
                ("LEFTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),4),
            ]))
            story.append(tbl); story.append(Spacer(1,.4*cm))

        add_basic_section("📥  Process Inputs",     inputs_d,  C["blue"])
        add_basic_section("📊  Design Results",     results_d, C["teal"])
        add_basic_section(f"🔬  {pump_type} Specific", sp_d,   C["orange"])

    # ── References ────────────────────────────────────────────────────────────
    story.append(PageBreak())
    ref_hdr = Table([[Paragraph("  📚  Engineering References & Standards",
        ParagraphStyle("rh",fontSize=10,textColor=C["white"],
                       fontName="Helvetica-Bold"))]],colWidths=[17*cm])
    ref_hdr.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,0),colors.HexColor("#37474f")),
        ("TOPPADDING",(0,0),(0,0),6),("BOTTOMPADDING",(0,0),(0,0),6),
        ("LEFTPADDING",(0,0),(0,0),10),
    ]))
    story.append(ref_hdr)
    story.append(Spacer(1,.2*cm))
    for ref in [
        "[1] API 610 12th Ed. — Centrifugal Pumps for Petroleum, Petrochemical and Natural Gas Industries",
        "[2] API 682 4th Ed. — Pumps — Shaft Sealing Systems for Centrifugal and Rotary Pumps",
        "[3] API 671 — Special Purpose Couplings for Petroleum, Chemical and Gas Industry Services",
        "[4] ANSI/HI 1.1-1.6, 9.6.1, 9.6.3 — Hydraulic Institute Standards for Centrifugal Pumps",
        "[5] ISO 5199 / ISO 9905 — Technical Specifications for Centrifugal Pumps",
        "[6] Karassik et al. — Pump Handbook, 4th Edition (McGraw-Hill, 2008)",
        "[7] Perry's Chemical Engineers' Handbook, 9th Ed. (2018)",
        "[8] Crane Technical Paper No. 410 — Flow of Fluids Through Valves, Fittings and Pipe",
        "[9] Moody, L.F. — Friction Factors for Pipe Flow (ASME Trans., 1944)",
        "[10] Stepanoff, A.J. — Centrifugal and Axial Flow Pumps, 2nd Ed. (Wiley, 1957)",
    ]:
        story.append(Paragraph(ref, S["ref"]))

    story += [
        Spacer(1,.5*cm),
        HRFlowable(width="100%",thickness=1,color=C["red"],spaceAfter=4),
        Paragraph(
            "DISCLAIMER: All values are engineering design calculations (±10-15% accuracy). "
            "Verify with vendor certified curves before procurement. "
            "All designs must be reviewed by a licensed Professional Engineer (P.Eng/PE).", S["disc"]),
        Spacer(1,.3*cm),
        Paragraph(f"SmartPump Designer  ·  {DEVELOPER}  ·  {DEGREE}  ·  {UNI}  ·  {BATCH}",
                  S["footer"]),
    ]

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()

