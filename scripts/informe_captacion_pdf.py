"""
Genera el PDF del análisis de captación WeRise-UVic (Google Ads + Meta).
Datos: últimos 30 días, extraídos vía API el 14-jul-2026.

Uso:  python scripts/informe_captacion_pdf.py
"""
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

SALIDA = "/Users/misael/Documents/UVIC/Analisis_Captacion_WeRise_UVic.pdf"

# --- Marca UVic ------------------------------------------------------------- #
ROJO = colors.HexColor("#CF0A2C")
GRANATE = colors.HexColor("#7C061A")
GRIS = colors.HexColor("#4B4B4B")
GRIS_CLARO = colors.HexColor("#F2F2F2")
TEXTO = colors.HexColor("#212529")
VERDE = colors.HexColor("#198754")
AMBAR = colors.HexColor("#D97706")

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="Helvetica-Bold",
                    fontSize=17, textColor=ROJO, spaceBefore=14, spaceAfter=6, leading=21)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold",
                    fontSize=12, textColor=GRANATE, spaceBefore=10, spaceAfter=4, leading=15)
BODY = ParagraphStyle("BODY", parent=ss["BodyText"], fontName="Helvetica", fontSize=9.5,
                      textColor=TEXTO, leading=13.5, alignment=TA_LEFT, spaceAfter=5)
SMALL = ParagraphStyle("SMALL", parent=BODY, fontSize=8, textColor=GRIS, leading=11)
TITULO = ParagraphStyle("TITULO", parent=ss["Title"], fontName="Helvetica-Bold",
                        fontSize=22, textColor=ROJO, spaceAfter=2, leading=26)
SUB = ParagraphStyle("SUB", parent=BODY, fontSize=10.5, textColor=GRIS, spaceAfter=2)
CELDA = ParagraphStyle("CELDA", parent=BODY, fontSize=8.5, leading=11, spaceAfter=0)
CELDA_B = ParagraphStyle("CELDA_B", parent=CELDA, fontName="Helvetica-Bold")


def p(txt, estilo=CELDA):
    return Paragraph(txt, estilo)


def tabla(datos, anchos, alinear_dcha=None, resaltar=None):
    """Tabla con cabecera granate y filas alternas."""
    t = Table(datos, colWidths=anchos, repeatRows=1, hAlign="LEFT")
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), ROJO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
    ]
    if alinear_dcha:
        for c in alinear_dcha:
            estilo.append(("ALIGN", (c, 1), (c, -1), "RIGHT"))
    if resaltar:
        for fila, color in resaltar:
            estilo.append(("TEXTCOLOR", (0, fila), (-1, fila), color))
            estilo.append(("FONTNAME", (0, fila), (-1, fila), "Helvetica-Bold"))
    t.setStyle(TableStyle(estilo))
    return t


def caja(titulo, texto, color=ROJO):
    """Caja destacada tipo callout."""
    inner = [[Paragraph(f"<b>{titulo}</b><br/>{texto}", BODY)]]
    t = Table(inner, colWidths=[170 * mm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBF0F2")),
        ("LINEBEFORE", (0, 0), (0, -1), 3, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def pie(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#DDDDDD"))
    canvas.line(20 * mm, 14 * mm, 190 * mm, 14 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GRIS)
    canvas.drawString(20 * mm, 9.5 * mm,
                      "Análisis de captación WeRise · UVic — datos vía API (Google Ads, Meta, GA4, HubSpot) · últimos 30 días")
    canvas.drawRightString(190 * mm, 9.5 * mm, f"Pág. {doc.page}")
    canvas.restoreState()


S = []

# ---------------------------------------------------------------- Portada --- #
S.append(Paragraph("Análisis de captación · WeRise UVic", TITULO))
S.append(Paragraph("Google Ads + Meta Ads · Últimos 30 días (a 14 de julio de 2026)", SUB))
S.append(HRFlowable(width="100%", thickness=2, color=ROJO, spaceBefore=6, spaceAfter=10))

S.append(Paragraph("Resumen ejecutivo", H1))
S.append(Paragraph(
    "Se han invertido <b>2.860 €</b> (Google 1.540 € + Meta 1.320 €) generando <b>33 leads</b> "
    "(CPL neto <b>87 €</b>, objetivo 45 €) y <b>39 oportunidades</b>, pero <b>0 matrículas</b>.", BODY))
S.append(Paragraph(
    "El diagnóstico clave: <b>el problema no es traer tráfico</b> — CTR, CPC y CPM están en benchmark. "
    "El problema es el <b>gasto mal dirigido en Google</b> y la <b>oferta / post-clic en Meta</b>. "
    "Hay <b>~640 €/mes de gasto directamente recuperable</b> sin tocar el presupuesto.", BODY))
S.append(Spacer(1, 4))
S.append(caja("Dato clave",
              "En la misma cuenta de Meta, otros ad sets de UVic consiguen <b>CPL de 4-42 €</b>, mientras "
              "los 5 de WeRise están en <b>65-273 €</b>. Mismo píxel, misma audiencia, resultados 2-7× peores. "
              "La diferencia está en la <b>oferta</b>: los que funcionan usan webinar/sesión informativa; "
              "los de WeRise promocionan el producto directamente."))

# --------------------------------------------------- 1. Por programa --------- #
S.append(Paragraph("1. Rendimiento por programa", H1))
datos = [
    [p("Programa", CELDA_B), p("Inversión", CELDA_B), p("Leads", CELDA_B), p("CPL", CELDA_B),
     p("Rebote", CELDA_B), p("Estado", CELDA_B)],
    [p("Marketing Deportivo"), p("610 €"), p("19"), p("<b>32 €</b>"), p("56,8%"), p("Bajo objetivo")],
    [p("Documentación Social"), p("450 €"), p("6"), p("75 €"), p("58,5%"), p("Aceptable")],
    [p("MBA Executive"), p("598 €"), p("4"), p("150 €"), p("57,6%"), p("Alto")],
    [p("Liderazgo IA"), p("645 €"), p("3"), p("215 €"), p("<b>69,9%</b>"), p("Alto · peor rebote")],
    [p("Comunicación Científica"), p("557 €"), p("1"), p("<b>557 €</b>"), p("61,0%"), p("Crítico")],
]
S.append(tabla(datos, [42 * mm, 22 * mm, 16 * mm, 22 * mm, 20 * mm, 36 * mm], alinear_dcha=[1, 2, 3, 4]))
S.append(Spacer(1, 4))
S.append(Paragraph(
    "<b>Marketing Deportivo tiene un CPL 17× mejor que Comunicación Científica</b> con inversión casi "
    "idéntica. Ahí hay una reasignación de presupuesto evidente.", BODY))

# ------------------------------------------------------ 2. Google Ads -------- #
S.append(Paragraph("2. Google Ads — 1.540 € · 4 conversiones", H1))

S.append(Paragraph("Fuga 1 — Tráfico de marca pagado a precio de oro", H2))
S.append(Paragraph(
    "Las campañas de programa capturan búsquedas de marca (“uvic”, “universitat de vic”…) a <b>2-4 € el clic</b>, "
    "cuando la campaña BRANDING obtiene esos mismos clics a <b>0,24 €</b>.", BODY))
datos = [
    [p("Término de búsqueda", CELDA_B), p("Campaña donde cae", CELDA_B), p("Coste", CELDA_B), p("Conv.", CELDA_B)],
    [p("uvic"), p("WeRise_Postgrau_Documental_Social"), p("56,07 €"), p("0")],
    [p("uvic"), p("WeRise_MBA_Executive"), p("54,65 €"), p("0")],
    [p("universitat de vic"), p("WeRise_MBA_Executive"), p("13,36 €"), p("0")],
    [p("otras variantes de marca"), p("varias"), p("~15 €"), p("0")],
    [p("<b>TOTAL desperdiciado</b>"), p(""), p("<b>~135 €/mes</b>"), p("<b>0</b>")],
]
S.append(tabla(datos, [42 * mm, 62 * mm, 26 * mm, 20 * mm], alinear_dcha=[2, 3],
               resaltar=[(5, ROJO)]))

S.append(Paragraph("Fuga 2 — Keywords broad con CERO conversiones", H2))
datos = [
    [p("Keyword", CELDA_B), p("Concordancia", CELDA_B), p("Coste", CELDA_B), p("Conv.", CELDA_B)],
    [p("curs inteligencia artificial"), p("BROAD"), p("139,55 €"), p("0")],
    [p("master comunicacio cientifica"), p("BROAD"), p("132,87 €"), p("0")],
    [p("curso cine documental"), p("PHRASE"), p("98,99 €"), p("0")],
    [p("formacio ia"), p("BROAD"), p("86,92 €"), p("0")],
    [p("mba  (una sola palabra genérica)"), p("BROAD"), p("72,40 €"), p("0")],
    [p("master gestio esportiva"), p("BROAD"), p("71,78 €"), p("0")],
    [p("<b>TOTAL</b>"), p("<b>= 39% del gasto de Google</b>"), p("<b>~602 €</b>"), p("<b>0</b>")],
]
S.append(tabla(datos, [52 * mm, 52 * mm, 26 * mm, 20 * mm], alinear_dcha=[2, 3],
               resaltar=[(7, ROJO)]))

S.append(Paragraph("Fuga 3 — Términos irrelevantes y de competencia", H2))
S.append(Paragraph(
    "Se está pagando por: <b>universitat de l'experiència</b> (universidad para mayores), "
    "<i>curso de entrenador de futbol</i>, <i>cursos futbol</i>, <i>moocs gratuitos</i>, "
    "<i>mba online barato</i>, <i>elements of ai</i>, <i>curso claude ai</i>, <i>programa doctorado</i>, "
    "<i>postdoc</i>, <i>grado de periodismo</i>; y competidores: <i>esade masters, mba pompeu fabra, "
    "mba urv, la salle, iqs, uoc, universitat politècnica, uic, johan cruyff institute, bihub, "
    "barça innovation hub</i>.", BODY))

S.append(Paragraph("Lo que SÍ convierte (escalar)", H2))
datos = [
    [p("Keyword", CELDA_B), p("Coste", CELDA_B), p("Conv.", CELDA_B), p("CPL", CELDA_B)],
    [p("executive mba  (broad)"), p("12,28 €"), p("2"), p("<b>6,14 €</b>")],
    [p("màster documental  (phrase)"), p("5,01 €"), p("1"), p("<b>5,01 €</b>")],
    [p("comunicacio cientifica uvic"), p("45,89 €"), p("1"), p("45,89 €")],
]
S.append(tabla(datos, [62 * mm, 26 * mm, 20 * mm, 26 * mm], alinear_dcha=[1, 2, 3]))

S.append(Paragraph("Estructura de cuenta", H2))
S.append(Paragraph(
    "3 de las 5 campañas usan un ad group genérico llamado <b>“Grupo de anuncios 1”</b> → sin segmentación "
    "temática → Quality Score bajo → <b>CPCs de 3-15 €</b> (ej. <i>mba deportivo</i> 15,06 €, "
    "<i>mba distancia</i> 22,86 €). También hay campañas antiguas (Master Biología, Master Com. Digital "
    "Interactiva) con keywords broad todavía ENABLED.", BODY))

# ----------------------------------------------------------- 3. Meta --------- #
S.append(Paragraph("3. Meta Ads — 1.320 € · 10 leads · CPL 132 €", H1))

S.append(Paragraph("Los 5 ad sets WeRise nunca salen de “learning phase”", H2))
S.append(Paragraph(
    "Todos están en <b>in_learning_phase</b> con 1-4 conversiones al mes. Meta necesita ~50 conversiones "
    "por semana y ad set para optimizar. <b>Con esta fragmentación, el algoritmo nunca aprende.</b>", BODY))

S.append(Paragraph("La comparativa que lo explica todo (misma cuenta, mismo píxel)", H2))
datos = [
    [p("Ad set", CELDA_B), p("Tipo de oferta", CELDA_B), p("Leads", CELDA_B), p("CPL", CELDA_B)],
    [p("IDIOMES cursos online"), p("Curso"), p("24"), p("<b>3,98 €</b>")],
    [p("EP_SOLEDAT webinar"), p("Webinar"), p("9"), p("<b>16,88 €</b>")],
    [p("DRET producte"), p("Producto"), p("5"), p("17,41 €")],
    [p("EP_CC webinar juliol"), p("Webinar"), p("15"), p("<b>25,04 €</b>")],
    [p("GRAUS general"), p("Producto"), p("27"), p("42,27 €")],
    [p("<b>WeRise_Comunicació Científica</b>"), p("Producto"), p("4"), p("<b>64,90 €</b>")],
    [p("<b>WeRise_Documental Social</b>"), p("Producto"), p("2"), p("<b>129,56 €</b>")],
    [p("<b>WeRise_Màrqueting Esportiu</b>"), p("Producto"), p("2"), p("<b>134,88 €</b>")],
    [p("<b>WeRise_Executive MBA</b>"), p("Producto"), p("1"), p("<b>258,96 €</b>")],
    [p("<b>WeRise_Lidera IA</b>"), p("Producto"), p("1"), p("<b>273,11 €</b>")],
]
S.append(tabla(datos, [58 * mm, 32 * mm, 20 * mm, 26 * mm], alinear_dcha=[2, 3],
               resaltar=[(6, ROJO), (7, ROJO), (8, ROJO), (9, ROJO), (10, ROJO)]))
S.append(Spacer(1, 4))
S.append(caja("El patrón",
              "Los ad sets con <b>oferta blanda</b> (webinar, sesión informativa, “5 motius”) consiguen "
              "<b>CPL de 17-25 €</b>. Los de <b>“producte” directo — como todos los de WeRise —</b> se van "
              "a <b>65-273 €</b>. Esta es la palanca más grande de todo el análisis."))

S.append(Paragraph("La buena noticia: el tráfico está bien comprado", H2))
S.append(Paragraph(
    "El tráfico de WeRise en Meta es correcto: <b>CTR 0,63-1,39%</b> (benchmark 0,9%), "
    "<b>CPC 0,39-0,60 €</b>, <b>CPM 3,26-5,46 €</b>, <b>frecuencia 2,0-2,7</b> (sin fatiga). "
    "<b>No hace falta tocar targeting ni pujas.</b> El fallo está en la oferta y en el post-clic.", BODY))

# ------------------------------------------------------- 4. Post-clic -------- #
S.append(Paragraph("4. Post-clic (Google Analytics 4)", H1))
S.append(Paragraph(
    "• <b>Rebote 57-70%</b> y <b>1,13 páginas/sesión</b>: la gente aterriza y se va.<br/>"
    "• Liderazgo IA: <b>69,9% de rebote</b> — y es el CPL más caro de Google. No es casualidad.<br/>"
    "• Solo <b>77 eventos clave de 1.208 sesiones</b> (6,4%).", BODY))
S.append(caja("Anomalía a revisar",
              "<b>Comunicación Científica</b> registra <b>16 eventos clave en GA4</b> pero solo "
              "<b>1 lead en HubSpot</b>. Posible fallo del formulario o del envío a CRM. Debe revisarse.",
              color=AMBAR))

# ------------------------------------------------ 5. Recomendaciones --------- #
S.append(Paragraph("5. Recomendaciones priorizadas", H1))

S.append(Paragraph("HACER YA — alto impacto · bajo esfuerzo (recupera ~640 €/mes)", H2))
datos = [
    [p("#", CELDA_B), p("Acción", CELDA_B), p("Efecto esperado", CELDA_B)],
    [p("1"), p("<b>Negativizar la marca</b> en las 5 campañas WeRise: <i>uvic, universitat de vic, "
              "universidad de vic, uvic ucc, u vic, uni vic, universitat central de catalunya</i>."),
     p("Ahorro ~135 €/mes. Ese tráfico vuelve a BRANDING a 0,24 €/clic en vez de 3-4 €.")],
    [p("2"), p("<b>Pausar las 6 keywords broad</b> con 0 conversiones (tabla Fuga 2)."),
     p("Libera ~500 €/mes de gasto improductivo.")],
    [p("3"), p("<b>Lista de negativas</b> (mín. 20): competidores (esade, pompeu fabra, urv, la salle, iqs, "
              "uoc, upc, uic, johan cruyff, bihub, barça) + irrelevantes (universitat de l'experiència, "
              "entrenador futbol, moocs, barato, gratis, doctorado, postdoc, grado, ciclo formativo)."),
     p("Elimina clics sin intención de compra.")],
    [p("4"), p("<b>Escalar lo que convierte</b>: subir puja/presupuesto en <i>executive mba</i>, "
              "<i>màster documental</i>, <i>comunicacio cientifica uvic</i>."),
     p("Son los únicos con CPL de 5-46 €.")],
    [p("5"), p("<b>Reasignar presupuesto</b> de Comunicación Científica (CPL 557 €) y Liderazgo IA (215 €) "
              "hacia <b>Marketing Deportivo</b> (32 €)."),
     p("Mismo gasto, más leads.")],
]
S.append(tabla(datos, [8 * mm, 92 * mm, 60 * mm]))

S.append(Paragraph("PRIORITARIO — alto impacto · esfuerzo medio", H2))
datos = [
    [p("#", CELDA_B), p("Acción", CELDA_B), p("Efecto esperado", CELDA_B)],
    [p("6"), p("<b>Cambiar la oferta en Meta</b>: pasar de “producte” a <b>webinar / sesión informativa / "
              "“5 motius per estudiar X”</b>. Es el patrón que YA funciona en la propia cuenta."),
     p("CPL de 17-25 € en vez de 65-273 €. <b>La palanca más grande.</b>")],
    [p("7"), p("<b>Consolidar los 5 ad sets WeRise en 1 CBO</b> para acumular conversiones."),
     p("Permite salir de learning phase y que Meta optimice.")],
    [p("8"), p("<b>Arreglar el post-clic</b>: headline mirroring (el titular del anuncio ganador = H1 exacto "
              "de la landing), acortar formulario, revisar velocidad. Empezar por Liderazgo IA."),
     p("+15-20% de conversión típico solo con el headline mirroring.")],
    [p("9"), p("<b>Reestructurar ad groups</b> de Google (eliminar “Grupo de anuncios 1”), segmentando por tema."),
     p("Sube Quality Score → baja el CPC.")],
]
S.append(tabla(datos, [8 * mm, 92 * mm, 60 * mm]))

S.append(Paragraph("SIGUIENTE SPRINT", H2))
datos = [
    [p("#", CELDA_B), p("Acción", CELDA_B)],
    [p("10"), p("Investigar la anomalía de Comunicación Científica (16 eventos clave GA4 vs 1 lead HubSpot) — posible formulario roto.")],
    [p("11"), p("Volumen creativo en Meta (era Andromeda): 1 h/semana de statics nativos + “one-keyword hack” (insertar el identificador del programa en el titular).")],
    [p("12"), p("Limpiar campañas legacy (Master Biología, Master Com. Digital Interactiva) con keywords broad aún ENABLED.")],
    [p("13"), p("Revisar el pipeline comercial: 39 oportunidades → 0 matrículas. Medir la velocidad del embudo.")],
]
S.append(tabla(datos, [10 * mm, 150 * mm]))

# --------------------------------------------------- 6. Ritmo inversión ------ #
S.append(Paragraph("6. Nota sobre el ritmo de inversión", H1))
S.append(caja("Recomendación: NO escalar todavía",
              "Se está al <b>17% del objetivo mensual</b> (2.860 € de 17.002 €). Antes de escalar hay que "
              "<b>arreglar el CPL</b> (hoy 87 €, objetivo 45 €). Escalar con el CPL actual solo multiplicaría "
              "el gasto ineficiente. <b>Primero arreglar, luego escalar.</b>", color=AMBAR))

S.append(Spacer(1, 8))
S.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#DDDDDD")))
S.append(Paragraph(
    "Fuentes: Google Ads (cuenta 297-053-3333), Meta Ads (act_33542477), Google Analytics 4 "
    "(propiedad 308288730) y HubSpot (Rise Education, portal 144637943). Datos extraídos vía API "
    "el 14 de julio de 2026, ventana de 30 días. Nota: las conversiones de Meta se han corregido "
    "(la plataforma reporta el mismo lead bajo dos tipos de acción; se contaba por duplicado).", SMALL))

doc = SimpleDocTemplate(
    SALIDA, pagesize=A4,
    leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=20 * mm,
    title="Análisis de captación WeRise · UVic",
    author="WeRise", subject="Auditoría Google Ads + Meta Ads",
)
doc.build(S, onFirstPage=pie, onLaterPages=pie)
print("PDF generado:", SALIDA)
