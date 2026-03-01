"""
Professional GIS PDF Report - Optimized for PyInstaller EXE
"""
import json
import os
import sys
from datetime import datetime

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))



BASE_DIR = get_base_path()
OUTPUT_PATH  = os.path.join(BASE_DIR, "gis_report.pdf")
SUMMARY_PATH = os.path.join(BASE_DIR, "report_output.json")

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable,
    PageBreak, KeepTogether
)

# ── Colors ────────────────────────────────────────────────────────────────────
C_PRIMARY = colors.HexColor("#2563EB")
C_PURPLE  = colors.HexColor("#7C3AED")
C_GREEN   = colors.HexColor("#059669")
C_AMBER   = colors.HexColor("#D97706")
C_RED     = colors.HexColor("#DC2626")
C_CYAN    = colors.HexColor("#0891B2")
C_SURFACE = colors.HexColor("#F1F5F9")
C_BORDER  = colors.HexColor("#CBD5E1")
C_TEXT    = colors.HexColor("#0F172A")
C_MUTED   = colors.HexColor("#64748B")
C_WHITE   = colors.white

W, H    = A4
MARGIN  = 1.8 * cm
USABLE  = W - 2 * MARGIN

# ── Styles ────────────────────────────────────────────────────────────────────
def mk_style(name, **kw):
    base = dict(fontName="Helvetica", fontSize=10,
                textColor=C_TEXT, leading=14,
                spaceAfter=0, spaceBefore=0)
    base.update(kw)
    return ParagraphStyle(name, **base)

ST = {
    "title":  mk_style("title",  fontName="Helvetica-Bold", fontSize=24,
                        textColor=C_PRIMARY, alignment=TA_CENTER,
                        spaceAfter=6, leading=30),
    "sub":    mk_style("sub",    fontSize=10, textColor=C_MUTED,
                        alignment=TA_CENTER, spaceAfter=20),
    "h2":     mk_style("h2",     fontName="Helvetica-Bold", fontSize=13,
                        textColor=C_PRIMARY, spaceBefore=18, spaceAfter=4),
    "label":  mk_style("label",  fontSize=8,  textColor=C_MUTED),
    "value":  mk_style("value",  fontName="Helvetica-Bold", fontSize=9,
                        textColor=C_TEXT),
    "cell":   mk_style("cell",   fontSize=8,  textColor=C_TEXT),
    "cell_b": mk_style("cell_b", fontName="Helvetica-Bold", fontSize=8,
                        textColor=C_TEXT),
    "cell_m": mk_style("cell_m", fontSize=8,  textColor=C_MUTED),
    "hdr":    mk_style("hdr",    fontName="Helvetica-Bold", fontSize=8,
                        textColor=C_WHITE),
    "warn":   mk_style("warn",   fontSize=8,  textColor=C_AMBER),
    "note":   mk_style("note",   fontSize=8,  textColor=C_MUTED,
                        leading=12),
}

def fmt(n):
    if n is None: return "—"
    try:
        x = float(n)
        if abs(x) >= 1e9: return f"{x/1e9:.2f}B"
        if abs(x) >= 1e6: return f"{x/1e6:.2f}M"
        if abs(x) >= 1e3: return f"{x/1e3:.1f}K"
        return f"{x:,.4g}"
    except:
        return str(n)

# ── Reusable table style ──────────────────────────────────────────────────────
def base_ts(has_header=False):
    cmds = [
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_WHITE, C_SURFACE]),
        ("BOX",            (0, 0), (-1, -1), 0.5,  C_BORDER),
        ("INNERGRID",      (0, 0), (-1, -1), 0.25, C_BORDER),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 7),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ]
    if has_header:
        cmds += [
            ("BACKGROUND",     (0, 0), (-1, 0), C_PRIMARY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_SURFACE]),
        ]
    return TableStyle(cmds)

# ── Helpers ───────────────────────────────────────────────────────────────────
def section(title):
    return [
        Paragraph(title, ST["h2"]),
        HRFlowable(width="100%", thickness=1,
                   color=C_PRIMARY, spaceAfter=10),
    ]

def kv_table(rows):
    cw = [3.2*cm, USABLE/2-3.2*cm, 3.2*cm, USABLE/2-3.2*cm]
    data = []
    for row in rows:
        r = [Paragraph(str(row[0]), ST["label"]),
             Paragraph(str(row[1]), ST["value"]),
             Paragraph(str(row[2]) if len(row) > 2 else "", ST["label"]),
             Paragraph(str(row[3]) if len(row) > 3 else "", ST["value"])]
        data.append(r)
    t = Table(data, colWidths=cw)
    t.setStyle(base_ts())
    return t

def kpi_table(items):
    n  = len(items)
    cw = [USABLE / n] * n
    cells = []
    for label, value, color in items:
        cells.append(
            Paragraph(
                f'<font name="Helvetica-Bold" size="20" color="{color.hexval()}">{value}</font>'
                f'<br/><font size="8" color="{C_MUTED.hexval()}">{label}</font>',
                mk_style("kpi", alignment=TA_CENTER, leading=26)
            )
        )
    t = Table([cells], colWidths=cw)
    t.setStyle(TableStyle([
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 14),
        ("BOTTOMPADDING", (0,0), (-1,-1), 14),
        ("BACKGROUND",    (0,0), (-1,-1), C_SURFACE),
        ("BOX",           (0,0), (-1,-1), 0.5, C_BORDER),
        ("INNERGRID",     (0,0), (-1,-1), 0.5, C_BORDER),
    ]))
    return t

def quality_table(fields):
    hdr = [Paragraph(h, ST["hdr"]) for h in ["Field", "Type", "Unique", "Null %", "Complete"]]
    data = [hdr]
    for f in fields:
        ok  = 100 - f["null_pct"]
        nc  = C_GREEN if f["null_pct"] == 0 else (C_AMBER if f["null_pct"] < 20 else C_RED)
        bar = "█" * int(ok / 10) + "░" * (10 - int(ok / 10))
        data.append([
            Paragraph(f["name"],          ST["cell_b"]),
            Paragraph(f["type"],          ST["cell_m"]),
            Paragraph(str(f["unique"]),   ST["cell"]),
            Paragraph(f'{f["null_pct"]}%', mk_style("np", fontSize=8, textColor=nc, fontName="Helvetica-Bold")),
            Paragraph(f'<font color="{nc.hexval()}">{bar}</font> {ok:.0f}%', mk_style("bar", fontSize=7, textColor=nc)),
        ])
    cw = [4.5*cm, 2*cm, 1.8*cm, 1.5*cm, USABLE-9.8*cm]
    t  = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(base_ts(has_header=True))
    return t

def numeric_table(num_fields, summary):
    hdr = [Paragraph(h, ST["hdr"]) for h in ["Field","Type","Min","Max","Mean","Median","Std Dev","Null %","NoData"]]
    data = [hdr]
    for f in num_fields:
        nd  = ", ".join(str(v) for v in f.get("nodata_removed", [])) or "—"
        nc  = C_GREEN if f["null_pct"] == 0 else (C_AMBER if f["null_pct"] < 20 else C_RED)
        data.append([
            Paragraph(f["name"],          ST["cell_b"]),
            Paragraph(f["type"],          ST["cell_m"]),
            Paragraph(fmt(f["min"]),       ST["cell"]),
            Paragraph(fmt(f["max"]),       ST["cell"]),
            Paragraph(fmt(f["mean"]),      ST["cell"]),
            Paragraph(fmt(f["median"]),    ST["cell"]),
            Paragraph(fmt(f["std"]),       ST["cell"]),
            Paragraph(f'{f["null_pct"]}%', mk_style("np2", fontSize=8, textColor=nc, fontName="Helvetica-Bold")),
            Paragraph(nd, ST["warn"] if nd != "—" else ST["cell_m"]),
        ])
    cw = [3.5*cm, 1.4*cm, 1.5*cm, 1.5*cm, 1.6*cm, 1.6*cm, 1.6*cm, 1.2*cm, 1.6*cm]
    t  = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(base_ts(has_header=True))
    return t

def categorical_table(str_fields, summary):
    hdr = [Paragraph(h, ST["hdr"]) for h in ["Field","Unique Values","Null %","Most Common Value"]]
    data = [hdr]
    for f in str_fields:
        cd  = summary.get("chart_data", {}).get(f["name"], {})
        top = cd.get("top_n", {})
        mc  = top.get("labels", ["—"])[0] if top.get("labels") else "—"
        nc  = C_GREEN if f["null_pct"] == 0 else (C_AMBER if f["null_pct"] < 20 else C_RED)
        data.append([
            Paragraph(f["name"],      ST["cell_b"]),
            Paragraph(str(f["unique"]), ST["cell"]),
            Paragraph(f'{f["null_pct"]}%', mk_style("np3", fontSize=8, textColor=nc, fontName="Helvetica-Bold")),
            Paragraph(str(mc)[:50],   ST["cell"]),
        ])
    cw = [4.5*cm, 2.5*cm, 1.8*cm, USABLE-8.8*cm]
    t  = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(base_ts(has_header=True))
    return t

def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(C_PRIMARY)
    canvas.rect(0, H - 10*mm, W, 10*mm, fill=1, stroke=0)
    canvas.setFillColor(C_WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(MARGIN, H - 6.5*mm, "GIS Report Tool")
    canvas.setFont("Helvetica", 8)
    lname = getattr(doc, "_layer_name", "")
    canvas.drawRightString(W - MARGIN, H - 6.5*mm, lname)

    canvas.setFillColor(C_SURFACE)
    canvas.rect(0, 0, W, 12*mm, fill=1, stroke=0)
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(0, 12*mm, W, 12*mm)
    canvas.setFillColor(C_MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(MARGIN, 4.5*mm, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    canvas.drawCentredString(W / 2, 4.5*mm, f"Page {doc.page}")
    canvas.drawRightString(W - MARGIN, 4.5*mm, "GIS Analysis Report — Confidential")
    canvas.restoreState()

# ── Main Generator ────────────────────────────────────────────────────────────
def generate_pdf(summary: dict = None) -> str:
    if summary is None:
        if not os.path.exists(SUMMARY_PATH):
            raise FileNotFoundError(f"No summary found at {SUMMARY_PATH}. Analyze a file first.")
        with open(SUMMARY_PATH, encoding="utf-8") as fh:
            summary = json.load(fh)

    layer_name = summary["layer_name"]
    fields     = summary["fields"]
    bbox       = summary.get("bbox", {})
    num_fields = [f for f in fields if f["type"] in ("integer", "float")]
    str_fields = [f for f in fields if f["type"] == "string"]
    complete   = sum(1 for f in fields if f["null_pct"] == 0)

    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN + 1.2*cm,
        bottomMargin=MARGIN + 1.4*cm,
    )
    doc._layer_name = layer_name

    elements = []
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph("GIS Layer Report", ST["title"]))
    elements.append(Paragraph(layer_name, ST["sub"]))

    elements.append(kpi_table([
        ("Total Features",   f"{summary['feature_count']:,}", C_PRIMARY),
        ("Attribute Fields", str(len(fields)),                C_PURPLE),
        ("Numeric Fields",   str(len(num_fields)),             C_CYAN),
        ("Complete Fields",  str(complete),                    C_GREEN),
    ]))
    elements.append(Spacer(1, .5*cm))

    elements += section("1 — Layer Overview")
    elements.append(kv_table([
        ("Layer Name",    layer_name, "CRS", summary.get("crs", "—")),
        ("EPSG Code",     str(summary.get("crs_epsg") or "Unknown"), "Geometry Type", ", ".join(summary.get("geometry_type", []))),
        ("Feature Count", f"{summary['feature_count']:,}", "Total Fields", str(len(fields))),
        ("Bbox W/E",      f"{bbox.get('minx','—')} / {bbox.get('maxx','—')}", "Bbox S/N", f"{bbox.get('miny','—')} / {bbox.get('maxy','—')}"),
    ]))

    elements += section("2 — Data Quality & Completeness")
    elements.append(quality_table(fields))

    if num_fields:
        elements += section("3 — Numeric Field Statistics")
        elements.append(numeric_table(num_fields, summary))

    if str_fields:
        elements += section("4 — Categorical Field Overview")
        elements.append(categorical_table(str_fields, summary))

    elements += section("5 — Spatial Extent")
    elements.append(kv_table([
        ("Min Longitude (West)", str(bbox.get("minx", "—")), "Max Longitude (East)", str(bbox.get("maxx", "—"))),
        ("Min Latitude (South)", str(bbox.get("miny", "—")), "Max Latitude (North)", str(bbox.get("maxy", "—"))),
    ]))

    nodata_fields = [f for f in fields if f.get("nodata_removed")]
    if nodata_fields:
        elements += section("6 — Data Warnings")
        for f in nodata_fields:
            vals = ", ".join(str(v) for v in f["nodata_removed"])
            elements.append(Paragraph(f'⚠  Field <b>{f["name"]}</b>: NoData sentinel values removed — <font color="{C_AMBER.hexval()}">{vals}</font>', ST["warn"]))
            elements.append(Spacer(1, .15*cm))

    doc.build(elements, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return OUTPUT_PATH

if __name__ == "__main__":
    try:
        path = generate_pdf()
        print(f"Success! Report generated at: {path}")
    except Exception as e:
        print(f"Error: {e}")