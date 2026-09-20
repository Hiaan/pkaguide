# -*- coding: utf-8 -*-
"""Peças visuais do PKA GUIDE Overlay: ícones desenhados e fundos arredondados (PIL)."""
import os
from PIL import Image, ImageDraw, ImageFont

SS = 4  # supersampling: desenha grande e reduz, para as bordas ficarem suaves
_cache = {}

FONTS = ('C:/Windows/Fonts/segoeuib.ttf', 'C:/Windows/Fonts/seguisb.ttf', 'C:/Windows/Fonts/segoeui.ttf')

def font(size, bold=True):
    key = ('f', size, bold)
    if key not in _cache:
        f = None
        for p in (FONTS if bold else FONTS[::-1]):
            if os.path.exists(p):
                try: f = ImageFont.truetype(p, size); break
                except Exception: pass
        _cache[key] = f or ImageFont.load_default()
    return _cache[key]

def _rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def _a(h, alpha=255):
    return _rgb(h) + (alpha,)

def _pts(coords, s):
    return [(x * s, y * s) for x, y in coords]

# ---------------- ícones ----------------
def _flame(d, s, c):
    body = [(.50, .03), (.68, .26), (.79, .50), (.76, .74), (.60, .93), (.40, .96), (.24, .84), (.20, .62),
            (.30, .38), (.38, .50), (.40, .28)]
    d.polygon(_pts(body, s), fill=_a(c))
    inner = [(.50, .40), (.62, .58), (.60, .76), (.50, .86), (.39, .77), (.37, .60)]
    d.polygon(_pts(inner, s), fill=_a('#fff7ed', 235))

def _gem(d, s, c):
    top, mid, bot = .10, .40, .94
    d.polygon(_pts([(.30, top), (.70, top), (.94, mid), (.50, bot), (.06, mid)], s), fill=_a(c))
    light = _a('#ffffff', 90)
    d.polygon(_pts([(.30, top), (.50, top), (.42, mid), (.06, mid)], s), fill=light)
    d.polygon(_pts([(.50, top), (.70, top), (.94, mid), (.58, mid)], s), fill=_a('#000000', 55))
    d.line(_pts([(.06, mid), (.94, mid)], s), fill=_a('#ffffff', 110), width=int(s * .035))
    d.line(_pts([(.42, mid), (.50, bot)], s), fill=_a('#ffffff', 80), width=int(s * .03))
    d.line(_pts([(.58, mid), (.50, bot)], s), fill=_a('#000000', 60), width=int(s * .03))

def _sparkle(d, s, c):
    d.polygon(_pts([(.50, .02), (.60, .40), (.98, .50), (.60, .60), (.50, .98), (.40, .60), (.02, .50), (.40, .40)], s), fill=_a(c))
    d.polygon(_pts([(.50, .26), (.55, .45), (.74, .50), (.55, .55), (.50, .74), (.45, .55), (.26, .50), (.45, .45)], s), fill=_a('#ffffff', 170))

def _coin(d, s, c):
    d.ellipse([s * .06, s * .06, s * .94, s * .94], fill=_a(c))
    d.ellipse([s * .18, s * .18, s * .82, s * .82], outline=_a('#000000', 70), width=int(s * .05))
    d.ellipse([s * .30, s * .12, s * .70, s * .38], fill=_a('#ffffff', 70))

def _target(d, s, c):
    w = int(s * .10)
    d.ellipse([s * .06, s * .06, s * .94, s * .94], outline=_a(c), width=w)
    d.ellipse([s * .28, s * .28, s * .72, s * .72], outline=_a(c, 190), width=w)
    d.ellipse([s * .44, s * .44, s * .56, s * .56], fill=_a(c))

def _hex(d, s, c):
    d.polygon(_pts([(.50, .04), (.90, .27), (.90, .73), (.50, .96), (.10, .73), (.10, .27)], s), fill=_a(c))
    d.polygon(_pts([(.50, .22), (.74, .36), (.74, .64), (.50, .78), (.26, .64), (.26, .36)], s), fill=_a('#ffffff', 75))

def _link(d, s, c):
    w = int(s * .12)
    d.rounded_rectangle([s * .06, s * .32, s * .56, s * .68], radius=s * .18, outline=_a(c), width=w)
    d.rounded_rectangle([s * .44, s * .32, s * .94, s * .68], radius=s * .18, outline=_a(c), width=w)

def _pencil(d, s, c):
    d.polygon(_pts([(.70, .06), (.94, .30), (.38, .86), (.10, .92), (.16, .64)], s), fill=_a(c))
    d.polygon(_pts([(.10, .92), (.16, .64), (.30, .78)], s), fill=_a('#ffffff', 200))
    d.line(_pts([(.62, .16), (.86, .40)], s), fill=_a('#000000', 80), width=int(s * .05))

def _plus(d, s, c):
    d.ellipse([s * .04, s * .04, s * .96, s * .96], fill=_a(c))
    w, a, b = s * .09, s * .28, s * .72
    d.line([(a, s * .5), (b, s * .5)], fill=_a('#ffffff'), width=int(w))
    d.line([(s * .5, a), (s * .5, b)], fill=_a('#ffffff'), width=int(w))

def _shield(d, s, c):
    d.polygon(_pts([(.50, .04), (.90, .20), (.86, .60), (.50, .96), (.14, .60), (.10, .20)], s), fill=_a(c))
    d.polygon(_pts([(.50, .18), (.76, .28), (.73, .57), (.50, .80), (.27, .57), (.24, .28)], s), fill=_a('#ffffff', 60))

def _search(d, s, c):
    w = int(s * .11)
    d.ellipse([s * .10, s * .10, s * .68, s * .68], outline=_a(c), width=w)
    d.line([(s * .62, s * .62), (s * .92, s * .92)], fill=_a(c), width=int(s * .13))

DRAW = {'flame': _flame, 'gem': _gem, 'sparkle': _sparkle, 'coin': _coin, 'target': _target,
        'hex': _hex, 'link': _link, 'pencil': _pencil, 'plus': _plus, 'shield': _shield, 'search': _search}

def icon(name, size, color):
    """devolve um PIL.Image RGBA do ícone"""
    key = ('i', name, size, color)
    if key not in _cache:
        s = size * SS
        im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
        DRAW.get(name, _sparkle)(ImageDraw.Draw(im), s, color)
        _cache[key] = im.resize((size, size), Image.LANCZOS)
    return _cache[key]

# ---------------- fundos ----------------
def panel(w, h, radius, fill, border=None, border_w=2, magic='#181819'):
    """cartão arredondado; o que fica fora do cartão recebe a cor 'magic' (vira transparente na janela)"""
    s = 3
    im = Image.new('RGB', (w * s, h * s), _rgb(magic))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=radius * s, fill=_rgb(fill),
                        outline=_rgb(border) if border else None, width=border_w * s if border else 0)
    return im.resize((w, h), Image.LANCZOS)

def pill(text, icon_name, color, h=22, fg='#ffffff', pad=9, gap=6, fsize=11):
    """etiqueta arredondada com ícone + texto, já renderizada (fica lisa em qualquer fundo)"""
    key = ('p', text, icon_name, color, h, fg, fsize)
    if key in _cache: return _cache[key]
    f = font(fsize * SS)
    tw = int(ImageDraw.Draw(Image.new('RGB', (1, 1))).textlength(text, font=f) / SS)
    isz = int(h * .62)
    w = pad + (isz + gap if icon_name else 0) + tw + pad
    s = SS
    im = Image.new('RGBA', (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=h * s // 2, fill=_a(color))
    x = pad * s
    if icon_name:
        ic = icon(icon_name, isz * s, '#ffffff')
        im.alpha_composite(ic, (x, (h * s - isz * s) // 2))
        x += (isz + gap) * s
    d.text((x, h * s / 2), text, font=f, fill=_a(fg), anchor='lm')
    _cache[key] = im.resize((w, h), Image.LANCZOS)
    return _cache[key]
