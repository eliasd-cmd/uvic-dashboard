# -*- coding: utf-8 -*-
"""
Genera el informe PDF «Análisis Meta WeRise — Optimización de captación» con la
marca UVic. Datos reales del 17-jun al 20-jul-2026 (34 días) extraídos de la
Graph API de Meta + HubSpot.

Ejecutar:  ./.venv/bin/python scripts/informe_meta_werise_pdf.py
Salida:    /Users/misael/Documents/UVIC/Analisis_Meta_WeRise_UVic.pdf
"""
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

SALIDA = "/Users/misael/Documents/UVIC/Analisis_Meta_WeRise_UVic.pdf"

# --- Marca UVic ------------------------------------------------------------- #
GRANATE = colors.HexColor("#CF0A2C")
GRANATE_OSC = colors.HexColor("#7C061A")
GRIS = colors.HexColor("#4B4B4B")
GRIS_CLARO = colors.HexColor("#F2F2F2")
VERDE = colors.HexColor("#198754")
AMBAR = colors.HexColor("#D97706")
ROJO = colors.HexColor("#CF0A2C")

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], textColor=GRANATE,
                    fontSize=17, spaceAfter=6, spaceBefore=10, leading=20)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=GRANATE_OSC,
                    fontSize=12.5, spaceAfter=4, spaceBefore=12, leading=15)
BODY = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5, leading=13.5,
                      textColor=GRIS, alignment=TA_LEFT, spaceAfter=4)
BODYW = ParagraphStyle("BodyW", parent=BODY, textColor=colors.white)
SMALL = ParagraphStyle("Small", parent=BODY, fontSize=8, textColor=GRIS)
CELL = ParagraphStyle("Cell", parent=BODY, fontSize=8.3, leading=10.5, spaceAfter=0)
CELLB = ParagraphStyle("CellB", parent=CELL, textColor=colors.black, fontName="Helvetica-Bold")
CELLW = ParagraphStyle("CellW", parent=CELL, textColor=colors.white, fontName="Helvetica-Bold")


def P(t, s=BODY):
    return Paragraph(t, s)


def bullet(items, s=BODY):
    return [Paragraph(f"• {t}", s) for t in items]


def tabla(data, col_widths, header_bg=GRANATE, zebra=True, align=None):
    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, header_bg),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
    ]
    if zebra:
        for i in range(1, len(data)):
            if i % 2 == 0:
                ts.append(("BACKGROUND", (0, i), (-1, i), GRIS_CLARO))
    if align:
        for col, a in align.items():
            ts.append(("ALIGN", (col, 1), (col, -1), a))
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle(ts))
    return t


def chip(txt, color):
    return Paragraph(f'<font color="white"><b>&nbsp;{txt}&nbsp;</b></font>',
                     ParagraphStyle("chip", parent=CELL, backColor=color, alignment=TA_CENTER))


story = []

# ===== PORTADA ============================================================== #
story.append(Spacer(1, 1.2 * cm))
story.append(Paragraph("UVic · WeRise", ParagraphStyle(
    "kick", parent=BODY, textColor=GRANATE, fontSize=11, alignment=TA_CENTER,
    fontName="Helvetica-Bold", spaceAfter=2)))
story.append(Paragraph("Análisis de captación en Meta Ads", ParagraphStyle(
    "title", parent=H1, fontSize=25, alignment=TA_CENTER, textColor=GRANATE,
    spaceAfter=4, leading=28)))
story.append(Paragraph("Diagnóstico a fondo y plan de optimización para captar más leads",
             ParagraphStyle("sub", parent=BODY, fontSize=12, alignment=TA_CENTER,
                            textColor=GRIS, spaceAfter=10)))
story.append(HRFlowable(width="40%", thickness=2, color=GRANATE, spaceAfter=10,
                        hAlign="CENTER"))
story.append(Paragraph("Periodo analizado: 17 jun – 20 jul 2026 (34 días) · Cuenta act_33542477",
             ParagraphStyle("meta", parent=SMALL, alignment=TA_CENTER)))
story.append(Paragraph("Fuente: Graph API de Meta + HubSpot (leads reales) · 5 campañas WeRise",
             ParagraphStyle("meta2", parent=SMALL, alignment=TA_CENTER)))
story.append(Spacer(1, 0.7 * cm))

# ===== RESUMEN EJECUTIVO ==================================================== #
story.append(Paragraph("Resumen ejecutivo", H1))
resumen = (
    "En 34 días se invirtieron <b>2.066 €</b> en las 5 campañas WeRise. Meta declara "
    "<b>27 leads</b> (CPL 77 €), pero HubSpot solo confirma <b>15 leads reales de Meta</b> "
    "→ el <b>CPL real ronda los 138 €</b>, muy por encima del objetivo de 50-70 €. "
    "La buena noticia: el margen de mejora es enorme y está a la vista en los datos. Hay "
    "<b>~30 % del presupuesto mal colocado</b> (hombres que no convierten, ubicaciones basura, "
    "un anuncio ganador ahogado y una campaña top pausada). Reasignándolo — sin gastar más — "
    "el CPL real debería acercarse al rango 50-70 €."
)
story.append(P(resumen))

destacados = [
    [P("#", CELLW), P("Hallazgo clave", CELLW), P("Oportunidad", CELLW)],
    ["1", "3 de 5 campañas corren con UN solo anuncio", "Volumen de creatividad = mayor palanca de crecimiento"],
    ["2", "El anuncio 'MBA v2' logró 8 leads con 133 € (CPL 17 €); el original, 1 lead con 294 €", "Escalar el ganador, pausar el perdedor"],
    ["3", "Las mujeres 35-54 generan ~el 100 % de los leads; los hombres, 0", "Excluir hombres y acotar a mujeres 30-54"],
    ["4", "Instagram Reels + Audience Network: 207 € y 0 leads", "Apagar ubicaciones basura"],
    ["5", "'Documental Social' (top en leads reales) está PAUSADA", "Reactivarla ya"],
    ["6", "75 % de los leads llegan sin UTM", "Arreglar la medición para optimizar bien"],
]
destacados = [destacados[0]] + [[P(f[0], CELL), P(f[1], CELL), P(f[2], CELL)] for f in destacados[1:]]
story.append(Spacer(1, 3))
story.append(tabla(destacados, [0.8 * cm, 9.0 * cm, 6.8 * cm]))

# ===== 1. FOTO GENERAL ====================================================== #
story.append(Paragraph("1 · La foto general por campaña", H1))
cab = [P(x, CELLW) for x in ["Campaña", "Gasto", "CTR", "CPC", "Frec.", "Leads", "CPL", "Estado"]]
filas = [
    ["EP Lidera IA", "456 €", "1,25 %", "0,57 €", "2,31", "5", "91 €", "Activa"],
    ["Màster Mkt Deportivo", "437 €", "0,68 %", "0,55 €", "2,63", "4", "109 €", "Activa"],
    ["Executive MBA", "427 €", "0,62 %", "0,73 €", "2,93", "9", "47 €", "Activa"],
    ["Comunicació Científica", "423 €", "0,70 %", "0,67 €", "2,31", "6", "70 €", "Activa"],
    ["Documental Social", "324 €", "0,92 %", "0,42 €", "2,16", "3", "108 €", "PAUSADA"],
]
data = [cab] + [[P(c, CELL) for c in f] for f in filas]
data.append([P("TOTAL", CELLB), P("2.066 €", CELLB), P("", CELL), P("", CELL),
             P("", CELL), P("27", CELLB), P("77 €", CELLB), P("", CELL)])
w = [3.9 * cm, 1.7 * cm, 1.6 * cm, 1.6 * cm, 1.4 * cm, 1.5 * cm, 1.5 * cm, 2.0 * cm]
story.append(tabla(data, w, align={1: "RIGHT", 5: "CENTER", 6: "RIGHT"}))
story.append(Spacer(1, 3))
story.append(P("<b>Realidad vs plataforma:</b> Meta infla ~1,8×. Los <b>15 leads reales</b> de "
               "HubSpot sitúan el CPL real en <b>~138 €</b>. Los CPL por campaña de arriba son "
               "los que reporta Meta (optimistas); úsalos para comparar campañas entre sí, no "
               "como coste real.", SMALL))

# ===== 2. HALLAZGOS ========================================================= #
story.append(Paragraph("2 · Hallazgos a fondo", H1))

story.append(Paragraph("2.1 · Creatividad — el mayor cuello de botella", H2))
story.append(P("En el Meta de 2026 (algoritmo Andromeda) el sistema necesita <b>volumen de "
               "creatividades frescas</b> para encontrar compradores. Hoy 3 campañas corren con "
               "un solo anuncio. La prueba está en el MBA:"))
mba = [["Anuncio (MBA)", "Gasto", "Leads", "CPL"],
       ["Executive MBA (original)", "294 €", "1", "294 €"],
       ["Executive MBA — v2", "133 €", "8", "17 €  ★"]]
story.append(tabla(mba, [8.0 * cm, 3.0 * cm, 2.5 * cm, 3.0 * cm],
                   align={1: "RIGHT", 2: "CENTER", 3: "RIGHT"}))
story.append(Spacer(1, 2))
story.append(P("El ganador (v2, CPL 17 €) recibió menos de la mitad de presupuesto que el "
               "perdedor. Está <b>ahogado</b>.", SMALL))

story.append(Paragraph("2.2 · Audiencia — las compradoras son muy claras", H2))
aud = [["Segmento", "Gasto", "Leads", "CPL"],
       ["Mujeres 35-44", "132 €", "10", "13 €  ★"],
       ["Mujeres 45-54", "207 €", "4", "52 €"],
       ["Mujeres 25-34", "86 €", "1", "86 €"],
       ["TODOS los hombres", "~236 €", "0", "sin leads"],
       ["Mujeres 55-64 / 18-24 / 65+", "~113 €", "0", "sin leads"]]
story.append(tabla(aud, [7.5 * cm, 3.0 * cm, 3.0 * cm, 3.0 * cm],
                   align={1: "RIGHT", 2: "CENTER", 3: "RIGHT"}))
story.append(Spacer(1, 2))
story.append(P("<b>Mujeres 35-54 = casi el 100 % de los leads</b> sobre 339 €. Los hombres no "
               "convierten ni un lead y consumen ~236 €. Sumando jóvenes y mayores sin conversión: "
               "<b>~350 €/mes (17 % del presupuesto) desperdiciados.</b>", SMALL))

story.append(Paragraph("2.3 · Ubicaciones — dinero mal colocado", H2))
plc = [["Ubicación", "Gasto", "Leads", "CPL"],
       ["Facebook feed", "323 €", "10", "32 €  ★"],
       ["Instagram feed", "1.007 €", "12", "84 €"],
       ["Instagram stories", "427 €", "4", "107 €"],
       ["Instagram reels", "105 €", "0", "sin leads"],
       ["Audience Network", "102 €", "0 (961 clics basura)", "sin leads"]]
story.append(tabla(plc, [4.6 * cm, 3.0 * cm, 4.6 * cm, 3.0 * cm],
                   align={1: "RIGHT", 3: "RIGHT"}))
story.append(Spacer(1, 2))
story.append(P("<b>Facebook feed es tu mejor ubicación (CPL 32 €) pero recibe 3× menos que "
               "Instagram feed</b>, que convierte 2,6× peor. Reels + Audience Network: 207 € "
               "y cero leads.", SMALL))

story.append(Paragraph("2.4 · Configuración y medición", H2))
for b in bullet([
    "Cada campaña tiene <b>un solo conjunto de anuncios</b> (sin test de audiencias): correcto para "
    "Andromeda, pero desperdiciado si no se alimenta con creatividades.",
    "<b>Documental Social está PAUSADA</b> — y era de las mejores: 5 leads reales (la que más), "
    "mejor CTR (0,92 %) y CPC más bajo (0,42 €). Reactivarla es prioritario.",
    "<b>Medición rota:</b> 53 de 71 leads (75 %) llegan sin UTM y hay un token sin resolver "
    "(<font face='Courier'>{{site_source_name}}</font>) ensuciando la fuente. Sin arreglarlo no se "
    "puede medir el CPL real por campaña.",
]):
    story.append(b)

# ===== 3. OPTIMIZACIONES PRIORIZADAS ======================================== #
story.append(Paragraph("3 · Optimizaciones priorizadas (impacto × esfuerzo)", H1))
op = [["#", "Acción", "Impacto", "Esfuerzo"],
      ["1", "Reactivar Documental Social (pausada, top en leads reales)", "Alto", "Bajo"],
      ["2", "Rescatar el ganador del MBA: pausar el original y escalar 'v2' (CPL 17 €)", "Alto", "Bajo"],
      ["3", "Apagar Audience Network + Instagram Reels (207 € → 0 leads)", "Alto", "Bajo"],
      ["4", "Excluir hombres y acotar a mujeres 30-54", "Alto", "Bajo"],
      ["5", "Subir Facebook feed (CPL 32 €) frente a IG stories/reels", "Medio", "Bajo"],
      ["6", "Volumen de creatividad: 3-5 statics nuevos/semana por campaña", "Alto", "Medio"],
      ["7", "Arreglar el paso de UTMs al formulario/HubSpot (campos ocultos uvic_utm_*)", "Alto", "Medio"]]
data = [[P(x, CELLW) for x in op[0]]]
for f in op[1:]:
    imp_col = VERDE if f[2] == "Alto" else (AMBAR if f[2] == "Medio" else GRIS)
    esf_col = VERDE if f[3] == "Bajo" else (AMBAR if f[3] == "Medio" else ROJO)
    data.append([P(f[0], CELL), P(f[1], CELL), chip(f[2], imp_col), chip(f[3], esf_col)])
story.append(tabla(data, [0.8 * cm, 11.6 * cm, 2.1 * cm, 2.1 * cm], zebra=True))

# ===== 4. PLAN PARA CAPTAR MÁS LEADS ======================================== #
story.append(Paragraph("4 · Cómo captar más leads UVic", H1))

story.append(Paragraph("Ganancia rápida (esta semana, sin gastar más)", H2))
story.append(P("Reactivar Documental, escalar el MBA v2, apagar Audience Network + Reels y excluir "
               "hombres. Solo reasignando ese ~30 % de presupuesto mal colocado hacia lo que funciona "
               "(Facebook feed + mujeres 35-54 + creatividades ganadoras), el CPL real debería bajar "
               "de ~138 € hacia el rango 50-70 € <b>sin tocar el presupuesto total.</b>"))

story.append(Paragraph("Motor de crecimiento (playbook Andromeda)", H2))
for b in bullet([
    "<b>Volumen de creatividad estática</b>, no vídeo pulido: 3-5 statics nativos nuevos por oferta "
    "cada semana. Es lo que el algoritmo necesita para escalar y no fatigarse.",
    "<b>Truco de la palabra-identidad</b> en el titular: «…para profesionales de la comunicación "
    "científica», «…para tu salto a dirección con el Executive MBA». Dispara la relevancia.",
    "<b>Clonar el MBA v2</b> (tu fórmula ganadora) adaptándola a cada programa.",
    "<b>Oferta / gancho:</b> con un CPL real de 138 € en programas de ticket alto, conviene un paso "
    "intermedio. El <b>webinar</b> ya funcionó históricamente (CPL mucho menor que ir directo a "
    "matrícula). Plantear un webinar o lead magnet por programa como imán de leads.",
]):
    story.append(b)

story.append(Paragraph("La base que hay que arreglar", H2))
story.append(P("El paso de UTMs al CRM. Con el 75 % de los leads sin fuente, ni este análisis ni el "
               "dashboard pueden atribuir bien. Es la palanca que desbloquea medir — y por tanto "
               "optimizar — todo lo demás."))

story.append(Spacer(1, 0.5 * cm))
story.append(HRFlowable(width="100%", thickness=0.6, color=GRANATE))
story.append(Paragraph(
    "Informe elaborado para el equipo de campañas · Datos reales Meta + HubSpot · "
    "Análisis, sin cambios ejecutados en la cuenta publicitaria.", SMALL))


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GRIS)
    canvas.drawString(2 * cm, 1.1 * cm, "UVic · WeRise — Análisis Meta Ads")
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Página {doc.page}")
    canvas.setFillColor(GRANATE)
    canvas.rect(0, A4[1] - 0.35 * cm, A4[0], 0.35 * cm, fill=1, stroke=0)
    canvas.restoreState()


doc = SimpleDocTemplate(SALIDA, pagesize=A4, topMargin=1.4 * cm, bottomMargin=1.6 * cm,
                        leftMargin=2 * cm, rightMargin=2 * cm,
                        title="Análisis Meta WeRise — UVic", author="WeRise")
doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
print("PDF generado:", SALIDA)
