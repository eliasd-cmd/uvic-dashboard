# -*- coding: utf-8 -*-
"""Genera statics de texto (1080x1350, feed 4:5) con la marca UVic para las
campañas WeRise de Meta. Formato text-on-brand (rinde bien en Andromeda).

Salida: /Users/misael/Documents/UVIC/creatividades_img/*.png
"""
import os
import textwrap as _tw

from PIL import Image, ImageDraw, ImageFont

OUT = "/Users/misael/Documents/UVIC/creatividades_img"
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1350
GRANATE = (207, 10, 44)       # #CF0A2C
GRANATE_OSC = (124, 6, 26)    # #7C061A
NEGRO = (33, 37, 41)          # #212529
BLANCO = (255, 255, 255)
GRIS = (120, 120, 120)

FB = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FR = "/System/Library/Fonts/Supplemental/Arial.ttf"


def font(bold, size):
    return ImageFont.truetype(FB if bold else FR, size)


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def pill(draw, x, y, txt, fnt, bg, fg, pad=(34, 20)):
    tw = draw.textlength(txt, font=fnt)
    asc, desc = fnt.getmetrics()
    th = asc + desc
    w = tw + pad[0] * 2
    h = th + pad[1] * 2
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=bg)
    draw.text((x + pad[0], y + pad[1]), txt, font=fnt, fill=fg)
    return w, h


def static(nombre, hook, programa, oscuro=True):
    img = Image.new("RGB", (W, H), GRANATE if oscuro else BLANCO)
    d = ImageDraw.Draw(img)
    M = 96
    txt_col = BLANCO if oscuro else NEGRO
    acc = BLANCO if oscuro else GRANATE

    # Barra superior de marca (variante clara) / wordmark
    if not oscuro:
        d.rectangle([0, 0, W, 14], fill=GRANATE)
    d.text((M, 74), "UVic", font=font(True, 40), fill=acc)
    d.text((M + d.textlength("UVic", font=font(True, 40)) + 14, 82),
           "· WeRise", font=font(False, 30), fill=(GRIS if not oscuro else (255, 255, 255)))

    # Hook grande centrado verticalmente
    fs = 78
    fnt = font(True, fs)
    lines = wrap(d, hook, fnt, W - 2 * M)
    while len(lines) > 5 and fs > 52:
        fs -= 4
        fnt = font(True, fs)
        lines = wrap(d, hook, fnt, W - 2 * M)
    lh = int(fs * 1.16)
    block_h = lh * len(lines)
    y = (H - block_h) // 2 - 40
    # regla de acento
    d.rectangle([M, y - 46, M + 120, y - 34], fill=acc)
    for ln in lines:
        d.text((M, y), ln, font=fnt, fill=txt_col)
        y += lh

    # Programa (subtítulo)
    d.text((M, y + 26), programa.upper(), font=font(True, 30),
           fill=(255, 255, 255) if oscuro else GRANATE)

    # CTA pill abajo
    cta_bg = BLANCO if oscuro else GRANATE
    cta_fg = GRANATE if oscuro else BLANCO
    pill(d, M, H - 190, "Més informació  →", font(True, 40), cta_bg, cta_fg)

    p = os.path.join(OUT, nombre)
    img.save(p, quality=95)
    return p


JOBS = [
    ("comunicacio_1.png", "Fes que la teva ciència s'entengui.", "Postgrau Comunicació Científica", True),
    ("comunicacio_2.png", "Un bon estudi que ningú llegeix no canvia res.", "Postgrau Comunicació Científica", False),
    ("esportiu_1.png", "Del teu amor per l'esport, una carrera.", "Màster Gestió i Màrqueting Esportiu", True),
    ("esportiu_2.png", "Fes el salt a la indústria de l'esport.", "Màster Gestió i Màrqueting Esportiu", False),
    ("documental_1.png", "Explica històries que importen.", "Postgrau Documental Social", True),
    ("documental_2.png", "Del guió a la pantalla.", "Postgrau Documental Social", False),
]

for n, hk, pr, osc in JOBS:
    print("generado:", static(n, hk, pr, osc))
print("\nCarpeta:", OUT)
