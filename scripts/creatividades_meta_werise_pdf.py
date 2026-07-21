# -*- coding: utf-8 -*-
"""
PDF «Propostes de creativitats — Meta WeRise»: copys nous (catala) per als 3
programes que corren amb un sol anunci. Marca UVic.

Ejecutar:  ./.venv/bin/python scripts/creatividades_meta_werise_pdf.py
Salida:    /Users/misael/Documents/UVIC/Creatividades_Meta_WeRise_UVic.pdf
"""
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

SALIDA = "/Users/misael/Documents/UVIC/Creatividades_Meta_WeRise_UVic.pdf"

GRANATE = colors.HexColor("#CF0A2C")
GRANATE_OSC = colors.HexColor("#7C061A")
GRIS = colors.HexColor("#4B4B4B")
GRIS_CLARO = colors.HexColor("#F4F0F1")

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], textColor=GRANATE, fontSize=16,
                    spaceAfter=5, spaceBefore=8, leading=19)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=GRANATE_OSC, fontSize=12.5,
                    spaceAfter=3, spaceBefore=12, leading=15)
BODY = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5, leading=13.5,
                      textColor=GRIS, alignment=TA_LEFT, spaceAfter=4)
SMALL = ParagraphStyle("Small", parent=BODY, fontSize=8, textColor=GRIS)
CELL = ParagraphStyle("Cell", parent=BODY, fontSize=8.4, leading=11, spaceAfter=0)
CELLW = ParagraphStyle("CellW", parent=CELL, textColor=colors.white, fontName="Helvetica-Bold")
ANG = ParagraphStyle("Ang", parent=CELL, fontName="Helvetica-Bold", textColor=GRANATE_OSC)
META = ParagraphStyle("Meta", parent=CELL, textColor=colors.black)


def P(t, s=BODY):
    return Paragraph(t, s)


def tbl_angles(rows):
    """rows = [(angle, text, titular, nn_t, descripcio, nn_d), ...]"""
    data = [[P("Àngle", CELLW), P("Text primari (Meta)", CELLW), P("Titular · Descripció", CELLW)]]
    for ang, txt, tit, nt, des, nd in rows:
        meta = (f'<b>Titular:</b> "{tit}" <font color="#888">({nt})</font><br/>'
                f'<b>Descripció:</b> "{des}" <font color="#888">({nd})</font>')
        data.append([P(ang, ANG), P(txt, CELL), P(meta, META)])
    t = Table(data, colWidths=[2.5 * cm, 8.9 * cm, 5.2 * cm], repeatRows=1)
    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), GRANATE),
        ("FONTSIZE", (0, 0), (-1, -1), 8.4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            ts.append(("BACKGROUND", (0, i), (-1, i), GRIS_CLARO))
    t.setStyle(TableStyle(ts))
    return t


story = []

# ---- Portada ----
story.append(Spacer(1, 0.8 * cm))
story.append(P("UVic · WeRise", ParagraphStyle("k", parent=BODY, textColor=GRANATE, fontSize=11,
               alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=2)))
story.append(P("Propostes de creativitats · Meta Ads", ParagraphStyle("t", parent=H1, fontSize=23,
               alignment=TA_CENTER, spaceAfter=4, leading=26)))
story.append(P("Copys nous per als 3 programes que corren amb un sol anunci",
               ParagraphStyle("s", parent=BODY, fontSize=11.5, alignment=TA_CENTER, spaceAfter=9)))
story.append(HRFlowable(width="40%", thickness=2, color=GRANATE, spaceAfter=9, hAlign="CENTER"))
story.append(P("Comunicació Científica · Màrqueting Esportiu · Documental Social",
               ParagraphStyle("m", parent=SMALL, alignment=TA_CENTER)))
story.append(Spacer(1, 0.5 * cm))

# ---- Context ----
story.append(P("<b>Per què això.</b> L'anunci guanyador «Executive MBA v2» (CPL 17 €) té <b>el mateix "
               "copy</b> que l'original (CPL 294 €): va guanyar per ser una <b>creativitat/imatge nova</b>, "
               "no pel text. Ho confirma el playbook Andromeda de Meta 2026: el que cal és <b>volum de "
               "creativitats fresques</b> amb àngles variats. Aquí tens copys nous (en català, com els "
               "actuals) pensats per a la compradora principal: <b>dones 35-54</b>.", BODY))
story.append(P("<b>Especificacions Meta:</b> el text primari mostra ~125 car. visibles (posa el ganxo al "
               "principi); titular ≤ 40 car.; descripció ≤ 30 car. CTA recomanat: «Més informació».", SMALL))

DATA = {
    "1 · Postgrau Comunicació Científica": (
        "cloud.info-uvic.cat/Comunicacio-Cientifica",
        [
            ("A — Transformació", "Saps molt, però la teva feina no arriba al gran públic? Aprèn a explicar ciència en articles, vídeo, ràdio i xarxes — i desenvolupa el teu propi projecte de divulgació.", "Comunica ciència amb impacte", 28, "Aprèn fent el teu projecte", 26),
            ("B — Identitat", "Per a investigadors, sanitaris i divulgadors que volen que la seva ciència s'entengui. Domina els formats i el llenguatge que connecten amb l'audiència.", "De la recerca a l'audiència", 27, "Professorat en actiu", 20),
            ("C — Dolor", "Un bon estudi que ningú llegeix no canvia res. Converteix el teu coneixement en històries que la gent entén, comparteix i recorda.", "Fes que t'entenguin fora del lab", 32, "Postgrau UVic · 2026", 20),
            ("D — Compatibilitat", "Compagina la teva feina amb una formació que et fa portaveu de la ciència. Un format pensat per a professionals en actiu.", "Divulga ciència amb criteri", 27, "Compatible amb la feina", 23),
        ],
        "Tens formació científica o sanitària i veus com la desinformació guanya terreny mentre el bon "
        "coneixement no arriba? El Postgrau en Comunicació Científica de la UVic t'ensenya a explicar "
        "ciència amb rigor i que s'entengui: articles, ràdio, vídeo, YouTube i xarxes. Amb professorat en "
        "actiu als mitjans i metodologia «aprèn fent» on desenvolupes el teu propi projecte. Compatible "
        "amb la teva feina. Sol·licita informació per al 2026.",
        "Una divulgadora (dona 35-50) gravant un vídeo/podcast amb el mòbil, estil selfie natiu, amb el "
        "ganxo com a text a sobre. Variant: text pla sobre fons de color amb la frase de dolor.",
    ),
    "2 · Màster Gestió i Màrqueting Esportiu": (
        "cloud.info-uvic.cat/master-sport-management-uvic",
        [
            ("A — Vocació", "Converteix la teva passió per l'esport en professió. Aprèn màrqueting esportiu, patrocini i experiència del fan amb professionals de la indústria.", "Treballa a la indústria de l'esport", 35, "Màster UVic · 2026", 18),
            ("B — Prova social", "Connecta amb professionals del FC Barcelona i de la indústria de l'esport. Especialitza't en gestió i màrqueting i fes el salt que esperaves.", "Del teu amor per l'esport, carrera", 34, "Xarxa professional real", 23),
            ("C — Contrari", "El màrqueting esportiu no va de futbol: va de crear experiències que la gent recorda. Aprèn a fer-ho amb els que ho fan cada dia.", "Més enllà del marcador", 22, "Gestió i màrqueting esportiu", 28),
            ("D — Gir professional", "Vols un gir professional cap a un sector que t'apassiona? Especialitza't en gestió i màrqueting esportiu i entra a la indústria de l'esport.", "Fes el salt a l'esport", 22, "Màster professionalitzador", 26),
        ],
        "Sempre has volgut treballar en el món de l'esport però no saps com fer el salt? El Màster en "
        "Gestió i Màrqueting Esportiu de la UVic t'especialitza en màrqueting, patrocini i experiència del "
        "fan, i et connecta amb professionals del FC Barcelona i de la indústria. Aprendràs dels qui ja hi "
        "treballen i sortiràs amb una xarxa i un perfil que el sector busca. Places obertes per al 2026.",
        "Foto d'ambient d'estadi/afició o una professional amb acreditació en un esdeveniment esportiu, "
        "estil «behind the scenes» natiu.",
    ),
    "3 · Postgrau Documental Social": (
        "cloud.info-uvic.cat/Postgrau-Documental-Social",
        [
            ("A — Vocació", "Tens històries que mereixen ser explicades? Aprèn tot el procés del documental social — direcció, producció, guió i distribució — amb professionals premiats.", "Explica històries amb impacte", 29, "Postgrau UVic · 2026", 20),
            ("B — Prova social", "Formació amb professionals de documentals premiats internacionalment. Converteix-te en documentalista social i porta les teves històries a la pantalla.", "Aprèn amb documentalistes premiats", 34, "Procés complet de rodatge", 25),
            ("C — Identitat", "Per a qui vol usar la càmera per canviar mirades. Domina direcció, producció, guió i distribució del documental social.", "Converteix-te en documentalista", 31, "De la idea a la distribució", 27),
            ("D — Dolor", "Una bona història social sense ofici es queda al calaix. Aprèn a dirigir, produir i distribuir documentals que remouen consciències.", "Del guió a la pantalla", 22, "Documental social · UVic", 24),
        ],
        "Sempre has volgut explicar històries que importen? El Postgrau en Documental Social de la UVic "
        "t'ensenya tot el procés — direcció, producció, guió i distribució — de la mà de professionals de "
        "documentals premiats internacionalment. Aprendràs fent, amb un projecte real de principi a fi. "
        "Reserva la teva plaça per al 2026.",
        "Operador/a de càmera enfocant una persona real, look una mica gra/autèntic, amb la frase "
        "«explica històries que importen».",
    ),
}

for titulo, (landing, angles, largo, arte) in DATA.items():
    story.append(P(titulo, H1))
    story.append(P(f'<b>Landing:</b> {landing} &nbsp;·&nbsp; <b>CTA:</b> Més informació', SMALL))
    story.append(Spacer(1, 3))
    story.append(tbl_angles(angles))
    story.append(P("<b>Text llarg (Andromeda):</b> " + largo, ParagraphStyle(
        "lg", parent=SMALL, spaceBefore=5, backColor=GRIS_CLARO, borderPadding=6, leading=12)))
    story.append(P("<b>Direcció d'art:</b> " + arte, SMALL))

story.append(Spacer(1, 0.3 * cm))
story.append(HRFlowable(width="100%", thickness=0.6, color=GRANATE))
story.append(P("Regla Andromeda: statics > vídeo polit. Prioritza 3-5 imatges noves per setmana i deixa "
               "que Meta reparteixi. Material llest per pujar — cap canvi executat al compte.", SMALL))


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5); canvas.setFillColor(GRIS)
    canvas.drawString(2 * cm, 1.1 * cm, "UVic · WeRise — Creativitats Meta Ads")
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Pàgina {doc.page}")
    canvas.setFillColor(GRANATE); canvas.rect(0, A4[1] - 0.35 * cm, A4[0], 0.35 * cm, fill=1, stroke=0)
    canvas.restoreState()


doc = SimpleDocTemplate(SALIDA, pagesize=A4, topMargin=1.4 * cm, bottomMargin=1.6 * cm,
                        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                        title="Creativitats Meta WeRise — UVic", author="WeRise")
doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
print("PDF generado:", SALIDA)
