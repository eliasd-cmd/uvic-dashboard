# -*- coding: utf-8 -*-
"""Genera statics (1080x1350, feed 4:5) con la marca UVic para Meta WeRise.

Soporta FONDO:
  - Imagen real (foto IA/stock) vía `fondo=<ruta>`: se recorta a 1080x1350 y se
    le aplica un velo de marca + degradado inferior para legibilidad del texto.
  - Sin imagen: fondo degradado de marca generado por código (con profundidad).

Salida: /Users/misael/Documents/UVIC/creatividades_img/*.png
"""
import os

from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = "/Users/misael/Documents/UVIC/creatividades_img"
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1350
GRANATE = (207, 10, 44)
GRANATE_OSC = (110, 5, 22)
NEGRO = (20, 20, 24)
BLANCO = (255, 255, 255)

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


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def fondo_degradado():
    """Degradado diagonal granate→granate oscuro + círculo suave para profundidad."""
    base = Image.new("RGB", (W, H), GRANATE)
    px = base.load()
    for y in range(H):
        for x in range(0, W, 2):
            t = (x / W * 0.35 + y / H * 0.65)
            c = _lerp(GRANATE, GRANATE_OSC, min(1, t))
            px[x, y] = c
            if x + 1 < W:
                px[x + 1, y] = c
    # halo circular claro arriba-derecha para dar volumen
    halo = Image.new("L", (W, H), 0)
    hd = ImageDraw.Draw(halo)
    hd.ellipse([W - 620, -320, W + 300, 600], fill=70)
    halo = halo.filter(ImageFilter.GaussianBlur(160))
    tint = Image.new("RGB", (W, H), (255, 90, 120))
    base = Image.composite(tint, base, halo)
    return base


def preparar_foto(ruta):
    """Recorta la foto a 1080x1350 (cover) y aplica velo de marca + scrim."""
    img = Image.open(ruta).convert("RGB")
    # cover crop
    r = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * r), int(img.height * r)))
    l = (img.width - W) // 2
    t = (img.height - H) // 2
    img = img.crop((l, t, l + W, t + H))
    # velo de marca (granate multiplicado ~48%) para unificar y dar contraste
    tint = Image.new("RGB", (W, H), GRANATE)
    img = Image.blend(img, tint, 0.42)
    # scrim inferior (oscurece la parte baja para el CTA y el titular)
    scrim = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(scrim)
    for y in range(H):
        a = int(200 * max(0, (y - H * 0.35) / (H * 0.65)))
        sd.line([(0, y), (W, y)], fill=min(200, a))
    dark = Image.new("RGB", (W, H), (30, 4, 10))
    img = Image.composite(dark, img, scrim)
    return img


def pill(draw, x, y, txt, fnt, bg, fg, pad=(34, 20)):
    tw = draw.textlength(txt, font=fnt)
    asc, desc = fnt.getmetrics()
    h = asc + desc + pad[1] * 2
    w = tw + pad[0] * 2
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=bg)
    draw.text((x + pad[0], y + pad[1]), txt, font=fnt, fill=fg)


def static(nombre, hook, programa, fondo=None):
    img = preparar_foto(fondo) if fondo else fondo_degradado()
    d = ImageDraw.Draw(img)
    M = 96

    d.text((M, 74), "UVic", font=font(True, 40), fill=BLANCO)
    d.text((M + d.textlength("UVic", font=font(True, 40)) + 14, 82), "· WeRise",
           font=font(False, 30), fill=(240, 220, 224))

    fs = 78
    fnt = font(True, fs)
    lines = wrap(d, hook, fnt, W - 2 * M)
    while len(lines) > 5 and fs > 52:
        fs -= 4
        fnt = font(True, fs)
        lines = wrap(d, hook, fnt, W - 2 * M)
    lh = int(fs * 1.16)
    y = (H - lh * len(lines)) // 2 - 40
    d.rectangle([M, y - 46, M + 120, y - 34], fill=BLANCO)
    for ln in lines:
        # sombra sutil para legibilidad sobre cualquier fondo
        d.text((M + 2, y + 2), ln, font=fnt, fill=(60, 0, 12))
        d.text((M, y), ln, font=fnt, fill=BLANCO)
        y += lh
    d.text((M, y + 26), programa.upper(), font=font(True, 30), fill=(255, 235, 238))

    pill(d, M, H - 190, "Més informació  →", font(True, 40), BLANCO, GRANATE)

    p = os.path.join(OUT, nombre)
    img.save(p, quality=92)
    return p


# fondo=None → degradado de marca. Cuando haya fotos IA, pasar fondo="ruta.png".
JOBS = [
    ("comunicacio_1.png", "Fes que la teva ciència s'entengui.", "Postgrau Comunicació Científica", None),
    ("comunicacio_2.png", "Un bon estudi que ningú llegeix no canvia res.", "Postgrau Comunicació Científica", None),
    ("esportiu_1.png", "Del teu amor per l'esport, una carrera.", "Màster Gestió i Màrqueting Esportiu", None),
    ("esportiu_2.png", "Fes el salt a la indústria de l'esport.", "Màster Gestió i Màrqueting Esportiu", None),
    ("documental_1.png", "Explica històries que importen.", "Postgrau Documental Social", None),
    ("documental_2.png", "Del guió a la pantalla.", "Postgrau Documental Social", None),
]

if __name__ == "__main__":
    for n, hk, pr, bg in JOBS:
        print("generado:", static(n, hk, pr, bg))
    print("\nCarpeta:", OUT)
