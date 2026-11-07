"""Run: python tools/make_holiday_art.py static/images/holidays
Draw an original illustration (SVG, 800x600) for each federal holiday."""
import math
import os
import random
import sys

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
W, H = 800, 600


def star(cx, cy, r, fill="#fff", inner=0.42, rotate=-90, extra=""):
    pts = []
    for i in range(10):
        rad = r if i % 2 == 0 else r * inner
        a = math.radians(rotate + i * 36)
        pts.append(f"{cx + rad * math.cos(a):.1f},{cy + rad * math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}" {extra}/>'


def sky(id_, stops):
    s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<linearGradient id="{id_}" x1="0" y1="0" x2="0" y2="1">{s}</linearGradient>'


def stars_field(n, seed, top=0, bottom=380, color="#fff"):
    rnd = random.Random(seed)
    return "".join(
        f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(top, bottom):.0f}" r="{rnd.uniform(0.6, 2.2):.1f}" fill="{color}" opacity="{rnd.uniform(.35, .95):.2f}"/>'
        for _ in range(n))


def firework(cx, cy, r, color, rays=18, seed=0):
    rnd = random.Random(seed)
    parts = []
    for i in range(rays):
        a = 2 * math.pi * i / rays
        r1, r2 = r * 0.25, r * rnd.uniform(0.85, 1.05)
        parts.append(f'<line x1="{cx + r1 * math.cos(a):.1f}" y1="{cy + r1 * math.sin(a):.1f}" x2="{cx + r2 * math.cos(a):.1f}" y2="{cy + r2 * math.sin(a):.1f}" stroke="{color}" stroke-width="3" stroke-linecap="round"/>')
        parts.append(f'<circle cx="{cx + (r2 + 8) * math.cos(a):.1f}" cy="{cy + (r2 + 8) * math.sin(a):.1f}" r="2.6" fill="{color}"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r * 0.12:.1f}" fill="{color}" opacity=".9"/>')
    return f'<g opacity=".95">{"".join(parts)}</g>'


def us_flag(x, y, w, wave=True):
    h = w * 10 / 19
    stripe = h / 13
    parts = []
    for i in range(13):
        color = "#b22234" if i % 2 == 0 else "#ffffff"
        parts.append(f'<rect x="0" y="{i * stripe:.2f}" width="{w}" height="{stripe + .5:.2f}" fill="{color}"/>')
    cw, ch = w * 0.4, stripe * 7
    parts.append(f'<rect x="0" y="0" width="{cw:.1f}" height="{ch:.1f}" fill="#3c3b6e"/>')
    for row in range(9):
        cols = 6 if row % 2 == 0 else 5
        for col in range(cols):
            sx = cw / 12 * (2 * col + 1 + (0 if row % 2 == 0 else 1))
            sy = ch / 10 * (row + 1)
            parts.append(star(sx, sy, ch / 22))
    body = "".join(parts)
    if not wave:
        return f'<g transform="translate({x},{y})">{body}</g>'
    # Gentle wave: clip to a wavy shape and shade with a translucent gradient.
    wave_path = (f"M0,0 C{w * .25},{-h * .08} {w * .5},{h * .08} {w * .75},0 S{w},{-h * .04} {w},0 "
                 f"L{w},{h} C{w * .75},{h - h * .08} {w * .5},{h + h * .08} {w * .25},{h} S0,{h + h * .04} 0,{h} Z")
    return (f'<g transform="translate({x},{y})"><clipPath id="flagclip{x}{y}"><path d="{wave_path}"/></clipPath>'
            f'<g clip-path="url(#flagclip{x}{y})">{body}<rect width="{w}" height="{h}" fill="url(#flagshade)"/></g></g>')


FLAG_SHADE = ('<linearGradient id="flagshade" x1="0" y1="0" x2="1" y2="0">'
              '<stop offset="0" stop-color="#000" stop-opacity=".12"/><stop offset=".3" stop-color="#fff" stop-opacity=".12"/>'
              '<stop offset=".55" stop-color="#000" stop-opacity=".14"/><stop offset=".8" stop-color="#fff" stop-opacity=".1"/>'
              '<stop offset="1" stop-color="#000" stop-opacity=".16"/></linearGradient>')

ISLAND = '<path d="M0,470 C90,440 160,452 250,430 C330,410 400,438 480,428 C560,418 640,440 800,425 L800,600 L0,600 Z" fill="#0d1b2e"/>'
WATER = lambda c="#13335a": f'<rect x="0" y="455" width="800" height="145" fill="{c}"/>'


def svg(defs, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice">'
            f'<defs>{FLAG_SHADE}{defs}</defs>{body}</svg>')


ART = {}

ART["new-years-day"] = svg(
    sky("s", [(0, "#070b2b"), (.6, "#24125c"), (1, "#5a1f6e")]),
    '<rect width="800" height="600" fill="url(#s)"/>' + stars_field(120, 1)
    + firework(220, 150, 95, "#ffd34d", seed=1) + firework(520, 110, 80, "#ff6fb1", 16, seed=2)
    + firework(650, 230, 70, "#5ee7ff", 14, seed=3) + firework(380, 250, 60, "#ffffff", 14, seed=4)
    + WATER("#1a1546") + '<g opacity=".35">' + "".join(
        f'<rect x="{x}" y="{470 + i * 14}" width="{rw}" height="3" fill="{c}" rx="1.5"/>'
        for i, (x, rw, c) in enumerate([(190, 70, "#ffd34d"), (500, 60, "#ff6fb1"), (630, 50, "#5ee7ff"), (360, 40, "#fff"), (210, 50, "#ffd34d")])) + "</g>"
    + '<path d="M0,500 C120,470 200,490 300,465 C380,445 450,480 520,470 C620,455 700,480 800,470 L800,600 L0,600 Z" fill="#0b0f26"/>')

ART["mlk-day"] = svg(
    sky("s", [(0, "#2f6fb5"), (.5, "#f6a65a"), (.75, "#ffd27a"), (1, "#ffe9b0")])
    + '<radialGradient id="sun" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#fff6cf"/><stop offset="1" stop-color="#ffc24d"/></radialGradient>',
    '<rect width="800" height="600" fill="url(#s)"/>'
    + "".join(f'<rect x="398" y="0" width="4" height="420" fill="#fff4c4" opacity=".28" transform="rotate({a} 400 420)"/>' for a in range(-80, 81, 10))
    + '<circle cx="400" cy="420" r="120" fill="url(#sun)"/>'
    + '<path d="M0,430 C150,400 260,420 400,405 C540,390 650,415 800,400 L800,600 L0,600 Z" fill="#7a4b2a" opacity=".55"/>'
    + '<path d="M0,470 C160,440 300,465 430,450 C580,432 690,455 800,445 L800,600 L0,600 Z" fill="#3b2a3d"/>'
    # dove
    + '<g transform="translate(470,170) scale(1.25)" fill="#ffffff">'
      '<path d="M0,40 C30,10 70,0 110,8 C80,14 62,26 52,40 C80,30 110,34 132,50 C100,52 70,60 50,72 C34,80 14,80 0,72 C-14,66 -22,56 -30,58 C-20,48 -10,44 0,40 Z"/>'
      '<path d="M48,42 C40,0 20,-30 -14,-48 C10,-12 18,16 22,44 Z" opacity=".95"/>'
      '<circle cx="-18" cy="54" r="2.5" fill="#3b2a3d"/>'
      '<path d="M-30,58 L-44,60 L-30,63 Z" fill="#f2b04a"/>'
      '<path d="M-44,60 C-56,56 -62,64 -70,62 M-56,58 C-58,52 -64,52 -66,54" stroke="#4f8a3a" stroke-width="3" fill="none" stroke-linecap="round"/></g>')

capitol = ('<g fill="#f6f4ee" stroke="#c9c3b5" stroke-width="1.5">'
           '<rect x="120" y="400" width="560" height="70"/>'
           '<rect x="90" y="455" width="620" height="25"/>'
           + "".join(f'<rect x="{x}" y="408" width="10" height="52" fill="#e2ddd0"/>' for x in range(140, 671, 30)) +
           '<rect x="290" y="330" width="220" height="75"/>'
           + "".join(f'<rect x="{x}" y="338" width="9" height="62" fill="#e2ddd0"/>' for x in range(302, 500, 22)) +
           '<path d="M300,330 C300,230 500,230 500,330 Z"/>'
           '<path d="M318,300 C330,250 470,250 482,300" fill="none" stroke="#c9c3b5"/>'
           '<rect x="380" y="225" width="40" height="22"/>'
           '<path d="M378,227 C380,200 420,200 422,227 Z"/>'
           '<rect x="397" y="185" width="6" height="18"/></g>')
ART["inauguration-day"] = svg(
    sky("s", [(0, "#4f8fd6"), (1, "#cfe6ff")]),
    '<rect width="800" height="600" fill="url(#s)"/>'
    + '<g fill="#fff" opacity=".85"><ellipse cx="150" cy="120" rx="70" ry="22"/><ellipse cx="200" cy="108" rx="50" ry="22"/><ellipse cx="640" cy="90" rx="80" ry="20"/><ellipse cx="600" cy="80" rx="45" ry="18"/></g>'
    + capitol + '<rect x="401" y="140" width="3" height="50" fill="#555"/>' + us_flag(404, 140, 70)
    + '<rect x="0" y="480" width="800" height="120" fill="#3f7d3a"/>'
    + '<rect x="330" y="480" width="140" height="120" fill="#d9d2c2"/>'
    + "".join(us_flag(x, 380, 46, wave=False) + f'<rect x="{x - 3}" y="380" width="3" height="100" fill="#666"/>' for x in (60, 700)))

ART["washingtons-birthday"] = svg(
    sky("s", [(0, "#22365f"), (.55, "#c46a6a"), (1, "#f2b27a")]),
    '<rect width="800" height="600" fill="url(#s)"/>' + stars_field(40, 7, 0, 180)
    + '<polygon points="380,70 420,70 432,470 368,470" fill="#f3eee4"/><polygon points="380,70 400,40 420,70" fill="#f3eee4"/>'
    + '<polygon points="400,40 420,70 432,470 400,470" fill="#000" opacity=".08"/>'
    + "".join(f'<rect x="{400 + r * math.cos(math.radians(a)):.0f}" y="{455 - 18}" width="3" height="22" fill="#555"/>' for a, r in ((0, 0),))
    + '<rect x="0" y="470" width="800" height="130" fill="#2c3f5e"/>'
    + '<rect x="0" y="470" width="800" height="12" fill="#56708f"/>'
    + '<polygon points="382,482 418,482 412,600 388,600" fill="#f3eee4" opacity=".35"/>'
    + "".join(f'<rect x="{x}" y="425" width="2.5" height="45" fill="#3a3a3a"/>' + us_flag(x + 2.5, 425, 26, wave=False)
              for x in (250, 290, 330, 450, 490, 530))
    + '<g fill="#f6b6c8">' + "".join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in
        [(60, 440, 34), (110, 450, 28), (30, 470, 26), (720, 440, 34), (765, 455, 30), (680, 470, 24)]) + "</g>")

ART["memorial-day"] = svg(
    sky("s", [(0, "#2b2f5c"), (.5, "#a85b5b"), (1, "#f0b071")]),
    '<rect width="800" height="600" fill="url(#s)"/>'
    + '<circle cx="400" cy="300" r="70" fill="#ffd9a0" opacity=".85"/>'
    + '<path d="M0,300 L800,300 L800,600 L0,600 Z" fill="#3e5a34"/>'
    + "".join(
        "".join(
            f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.2f})"><path d="M-10,0 L-10,-26 C-10,-36 10,-36 10,-26 L10,0 Z" fill="#f2f2ee"/>'
            f'<rect x="12" y="-30" width="1.6" height="30" fill="#555"/><rect x="13.6" y="-30" width="11" height="7" fill="#b22234"/>'
            f'<rect x="13.6" y="-30" width="4.5" height="3.6" fill="#3c3b6e"/></g>'
            for x in [400 + (c - 6) * spacing for c in range(13)])
        for y, s, spacing in [(330, .6, 52), (370, .8, 66), (420, 1.05, 86), (485, 1.4, 112), (570, 1.9, 150)]))

nova = "".join(
    f'<polygon points="{" ".join(f"{400 + (110 if i % 2 == 0 else 48) * math.cos(math.radians(-90 + i * 18)):.1f},{280 + (110 if i % 2 == 0 else 48) * math.sin(math.radians(-90 + i * 18)):.1f}" for i in range(20))}" fill="none" stroke="#fff" stroke-width="4"/>'
    for _ in range(1))
ART["juneteenth"] = svg(
    '',
    '<rect width="800" height="600" fill="#1d3f8f"/>'
    + '<path d="M0,360 C200,250 600,250 800,360 L800,600 L0,600 Z" fill="#c8102e"/>'
    + nova + star(400, 280, 52)
    + stars_field(25, 9, 20, 200))

ART["independence-day"] = svg(
    sky("s", [(0, "#060b26"), (1, "#1c2a63")]),
    '<rect width="800" height="600" fill="url(#s)"/>' + stars_field(90, 11, 0, 360)
    + firework(190, 140, 90, "#ff4d5e", seed=5) + firework(420, 95, 75, "#ffffff", 16, seed=6)
    + firework(620, 160, 95, "#4d8bff", seed=7) + firework(320, 250, 55, "#ffd34d", 14, seed=8)
    + '<rect x="96" y="300" width="4" height="300" fill="#bbb"/>' + us_flag(100, 300, 600))

gear = lambda cx, cy, r, teeth, color: (
    f'<g fill="{color}">' + "".join(
        f'<rect x="{cx - r * .14:.1f}" y="{cy - r * 1.18:.1f}" width="{r * .28:.1f}" height="{r * .36:.1f}" rx="3" transform="rotate({i * 360 / teeth:.1f} {cx} {cy})"/>'
        for i in range(teeth)) + f'<circle cx="{cx}" cy="{cy}" r="{r}"/><circle cx="{cx}" cy="{cy}" r="{r * .42:.1f}" fill="#f6a03c"/></g>')
ART["labor-day"] = svg(
    sky("s", [(0, "#2a5ea8"), (.6, "#f6a03c"), (1, "#ffd27a")]),
    '<rect width="800" height="600" fill="url(#s)"/>'
    + '<circle cx="400" cy="430" r="140" fill="#ffe3a3" opacity=".7"/>'
    + gear(330, 300, 95, 12, "#1f2f4d") + gear(500, 350, 60, 10, "#2c4266")
    + '<g transform="rotate(-35 400 470)"><rect x="390" y="330" width="20" height="230" rx="6" fill="#7a4a24"/><rect x="350" y="318" width="100" height="38" rx="6" fill="#4b5563"/></g>'
    + '<g transform="rotate(35 400 470)"><rect x="392" y="340" width="16" height="220" rx="6" fill="#9aa3ad"/><path d="M372,300 a34,34 0 1,0 56,0 l-12,22 h-32 z" fill="#9aa3ad"/></g>'
    + '<path d="M0,520 C200,500 600,500 800,520 L800,600 L0,600 Z" fill="#1f2f4d"/>')

ART["columbus-day"] = svg(
    sky("s", [(0, "#38597f"), (.55, "#e7905a"), (1, "#ffcf8a")]),
    '<rect width="800" height="600" fill="url(#s)"/>'
    + '<circle cx="610" cy="380" r="70" fill="#ffe2a0"/>'
    + '<rect x="0" y="400" width="800" height="200" fill="#1e4b74"/>'
    + "".join(f'<path d="M{x},{y} q20,-8 40,0 t40,0" stroke="#7fb0d8" stroke-width="3" fill="none" opacity=".6"/>' for x, y in
              [(60, 470), (220, 500), (520, 480), (650, 530), (360, 560), (120, 560)])
    + '<g transform="translate(260,180)" fill="#2b1d14">'
      '<path d="M20,250 L300,250 L270,300 L50,300 Z"/>'
      '<rect x="90" y="20" width="6" height="235"/><rect x="170" y="0" width="7" height="255"/><rect x="245" y="40" width="5" height="215"/>'
      '<path d="M98,40 C140,60 140,120 98,140 Z M98,150 C150,170 150,230 98,240 Z" fill="#f4ead6"/>'
      '<path d="M179,20 C235,45 235,115 179,135 Z M179,145 C240,170 240,230 179,240 Z" fill="#f4ead6"/>'
      '<path d="M252,60 C290,80 290,140 252,160 Z" fill="#f4ead6"/>'
      '<path d="M20,250 L-20,230 L30,245 Z"/><path d="M170,0 l24,8 l-24,8 z" fill="#c8102e"/></g>')

ART["veterans-day"] = svg(
    sky("s", [(0, "#14284b"), (.6, "#3d6aa8"), (1, "#a9c7ea")]),
    '<rect width="800" height="600" fill="url(#s)"/>'
    + '<rect x="146" y="80" width="6" height="520" fill="#d9d9d9"/><circle cx="149" cy="78" r="9" fill="#d4af37"/>'
    + us_flag(152, 96, 520)
    + '<path d="M0,500 C200,480 600,485 800,500 L800,600 L0,600 Z" fill="#0f1f3a"/>'
    + "".join(star(x, 528, 13, "#d4af37") for x in (260, 330, 400, 470, 540)))

leaf = ('M0,-30 L6,-14 L20,-20 L14,-4 L28,0 L12,6 L16,22 L2,12 L0,30 L-2,12 L-16,22 L-12,6 L-28,0 L-14,-4 L-20,-20 L-6,-14 Z')
rnd = random.Random(21)
leaves = "".join(
    f'<path d="{leaf}" fill="{rnd.choice(["#d9531e", "#f2a42c", "#b5341c", "#e07b22", "#8f2d12"])}" '
    f'transform="translate({rnd.uniform(0, 800):.0f},{rnd.uniform(0, 380):.0f}) rotate({rnd.uniform(0, 360):.0f}) scale({rnd.uniform(.6, 1.3):.2f})" opacity=".9"/>'
    for _ in range(26))
pumpkin = lambda cx, cy, s: (
    f'<g transform="translate({cx},{cy}) scale({s})"><ellipse cx="-30" cy="0" rx="34" ry="46" fill="#e8741c"/><ellipse cx="30" cy="0" rx="34" ry="46" fill="#e8741c"/>'
    f'<ellipse cx="0" cy="0" rx="36" ry="50" fill="#f28c28"/><path d="M0,-48 C0,-64 8,-72 16,-76" stroke="#5b3a1a" stroke-width="7" fill="none" stroke-linecap="round"/></g>')
ART["thanksgiving-day"] = svg(
    sky("s", [(0, "#f7d9a8"), (1, "#e9a65f")]),
    '<rect width="800" height="600" fill="url(#s)"/>' + leaves
    + '<path d="M0,430 C200,410 600,410 800,430 L800,600 L0,600 Z" fill="#8a5a2b"/>'
    + "".join(f'<path d="M{x},440 C{x - 6},400 {x + 4},360 {x - 2},330" stroke="#d8b25c" stroke-width="4" fill="none"/>'
              + "".join(f'<ellipse cx="{x - 2 + (k % 2) * 8 - 4}" cy="{340 + k * 12}" rx="5" ry="10" fill="#e3c06a"/>' for k in range(6))
              for x in (120, 150, 650, 690))
    + pumpkin(330, 430, 1.25) + pumpkin(470, 450, .95) + pumpkin(230, 470, .8)
    + '<g transform="translate(560,470)"><ellipse rx="40" ry="16" fill="#b5341c"/><ellipse cx="0" cy="-10" rx="30" ry="22" fill="#c9442a"/></g>')

tree = ('<g><polygon points="400,90 300,260 345,260 260,380 330,380 230,500 570,500 470,380 540,380 455,260 500,260" fill="#1f6b3a"/>'
        '<polygon points="400,90 455,260 500,260 470,380 540,380 570,500 400,500" fill="#000" opacity=".12"/>'
        '<rect x="380" y="500" width="40" height="45" fill="#6b3f1d"/>'
        + star(400, 88, 32, "#ffd34d")
        + "".join(f'<circle cx="{x}" cy="{y}" r="11" fill="{c}"/>' for x, y, c in
                  [(360, 220, "#e63946"), (430, 240, "#ffd34d"), (330, 330, "#4dabf7"), (420, 320, "#e63946"), (470, 350, "#ffd34d"),
                   (300, 440, "#ffd34d"), (380, 430, "#4dabf7"), (460, 450, "#e63946"), (520, 470, "#4dabf7"), (260, 480, "#e63946")])
        + '<path d="M330,270 C380,300 430,290 470,262 M290,390 C360,420 460,415 520,385" stroke="#ffe8a3" stroke-width="4" fill="none" opacity=".8"/></g>')
gifts = ('<rect x="200" y="505" width="80" height="60" fill="#e63946"/><rect x="235" y="505" width="10" height="60" fill="#ffd34d"/>'
         '<rect x="520" y="515" width="70" height="50" fill="#4dabf7"/><rect x="550" y="515" width="10" height="50" fill="#fff"/>'
         '<rect x="600" y="530" width="55" height="35" fill="#ffd34d"/><rect x="623" y="530" width="9" height="35" fill="#e63946"/>')
rnd2 = random.Random(31)
snow = "".join(f'<circle cx="{rnd2.uniform(0, 800):.0f}" cy="{rnd2.uniform(0, 560):.0f}" r="{rnd2.uniform(1.5, 4.5):.1f}" fill="#fff" opacity="{rnd2.uniform(.5, .95):.2f}"/>' for _ in range(140))
ART["christmas-day"] = svg(
    sky("s", [(0, "#0b1f4a"), (1, "#2c5a8c")]),
    '<rect width="800" height="600" fill="url(#s)"/>' + snow
    + '<path d="M0,520 C200,500 600,500 800,520 L800,600 L0,600 Z" fill="#eef4fb"/>' + tree + gifts)


heart = lambda cx, cy, r, color, rot=0, op=1: (
    f'<path d="M0,{r * .35:.1f} C{-r * 1.1:.1f},{-r * .45:.1f} {-r * .45:.1f},{-r * 1.15:.1f} 0,{-r * .45:.1f} '
    f'C{r * .45:.1f},{-r * 1.15:.1f} {r * 1.1:.1f},{-r * .45:.1f} 0,{r * .35:.1f} Z" fill="{color}" opacity="{op}" '
    f'transform="translate({cx:.0f},{cy:.0f}) rotate({rot:.0f}) scale(1.6)"/>')
rv = random.Random(41)
ART["valentines-day"] = svg(
    sky("s", [(0, "#ffd1dc"), (1, "#ff8fab")]),
    '<rect width="800" height="600" fill="url(#s)"/>'
    + "".join(heart(rv.uniform(0, 800), rv.uniform(0, 600), rv.uniform(14, 30), rv.choice(["#ff4d6d", "#ffffff", "#c9184a"]), rv.uniform(-25, 25), .55) for _ in range(34))
    + heart(400, 300, 120, "#e63946") + heart(400, 300, 120, "#ffffff", 0, .15)
    + '<path d="M180,420 L620,180" stroke="#7a4a24" stroke-width="7"/><polygon points="620,180 590,182 606,206" fill="#d4af37"/>'
    + '<path d="M180,420 l-22,-6 l8,20 z M196,412 l-22,-6 l8,20 z" fill="#ffffff"/>')


def shamrock(cx, cy, s, color="#2e9e4f"):
    leaves = "".join(f'<g transform="rotate({a})"><circle cx="-14" cy="-30" r="20"/><circle cx="14" cy="-30" r="20"/><path d="M-30,-24 L0,0 L30,-24 Z"/></g>' for a in (0, 120, 240))
    return (f'<g transform="translate({cx:.0f},{cy:.0f}) scale({s:.2f})" fill="{color}">{leaves}'
            f'<path d="M0,0 C6,30 14,50 30,70" stroke="{color}" stroke-width="7" fill="none" stroke-linecap="round"/></g>')


rs = random.Random(51)
coins = "".join(f'<circle cx="{x}" cy="{y}" r="15" fill="#f4c542" stroke="#c9971c" stroke-width="3"/>' for x, y in ((-30, -8), (0, -18), (30, -6), (-10, -30), (18, -32)))
ART["st-patricks-day"] = svg(
    sky("s", [(0, "#0f5132"), (1, "#198754")]),
    '<rect width="800" height="600" fill="url(#s)"/>'
    + "".join(shamrock(rs.uniform(0, 800), rs.uniform(0, 600), rs.uniform(.35, .7), rs.choice(["#2fb36a", "#5fd38d", "#157347"])) for _ in range(22))
    + shamrock(400, 280, 2.6, "#7ee2a8") + shamrock(400, 280, 2.3, "#2fb36a")
    + f'<g transform="translate(590,420)"><path d="M-70,0 C-70,90 70,90 70,0 Z" fill="#1b1b1b"/><ellipse cx="0" cy="0" rx="72" ry="16" fill="#2b2b2b"/>{coins}</g>')


def egg(cx, cy, s, base, stripe):
    dots = "".join(f'<circle cx="{x}" cy="-26" r="5" fill="{stripe}"/>' for x in (-18, 0, 18))
    return (f'<g transform="translate({cx},{cy}) scale({s})"><path d="M0,-60 C34,-60 48,-10 48,14 C48,44 26,62 0,62 C-26,62 -48,44 -48,14 C-48,-10 -34,-60 0,-60 Z" fill="{base}"/>'
            f'<path d="M-46,0 Q-23,-14 0,0 T46,0" stroke="{stripe}" stroke-width="7" fill="none"/>'
            f'<path d="M-44,26 Q-22,14 0,26 T44,26" stroke="#ffffff" stroke-width="5" fill="none" opacity=".8"/>{dots}</g>')


ART["easter"] = svg(
    sky("s", [(0, "#bfe3ff"), (1, "#fff4d6")]),
    '<rect width="800" height="600" fill="url(#s)"/><circle cx="650" cy="110" r="55" fill="#ffe08a"/>'
    + '<g fill="#fff" opacity=".9"><ellipse cx="170" cy="110" rx="70" ry="20"/><ellipse cx="220" cy="98" rx="45" ry="20"/></g>'
    + '<path d="M0,400 C200,360 600,360 800,400 L800,600 L0,600 Z" fill="#7cc36b"/>'
    + egg(250, 390, 1.15, "#ffadd2", "#c2185b") + egg(400, 370, 1.45, "#a5d8ff", "#1971c2") + egg(550, 395, 1.1, "#ffe066", "#e67700")
    + egg(320, 450, .8, "#d0bfff", "#6741d9") + egg(480, 455, .85, "#b2f2bb", "#2b8a3e")
    + "".join(f'<path d="M{x},470 l6,-26 l6,26" fill="#5aa64c"/>' for x in range(0, 800, 18))
    + "".join(f'<g transform="translate({x},{y})"><circle r="9" fill="#fff"/><circle r="4" fill="#ffd43b"/></g>' for x, y in ((90, 440), (150, 500), (680, 450), (730, 510), (620, 520))))


def flower(cx, cy, r, petal, center="#ffd43b"):
    petals = "".join(f'<ellipse cx="0" cy="{-r:.0f}" rx="{r * .55:.0f}" ry="{r:.0f}" fill="{petal}" transform="rotate({a})"/>' for a in range(0, 360, 60))
    return f'<g transform="translate({cx},{cy})">{petals}<circle r="{r * .55:.0f}" fill="{center}"/></g>'


stems = "".join(f'<path d="M400,450 C{400 + dx * .4:.0f},380 {400 + dx},330 {400 + dx},{y}" stroke="#2f9e44" stroke-width="6" fill="none"/>'
                for dx, y in ((-150, 230), (-80, 170), (0, 140), (80, 170), (150, 230), (-40, 260), (40, 260)))
ART["mothers-day"] = svg(
    sky("s", [(0, "#ffe3ec"), (1, "#ffc2d4")]),
    '<rect width="800" height="600" fill="url(#s)"/>' + stems
    + flower(250, 230, 40, "#ff6b9a") + flower(320, 170, 42, "#f783ac") + flower(400, 140, 46, "#e64980")
    + flower(480, 170, 42, "#ffa8c5") + flower(550, 230, 40, "#ff6b9a") + flower(360, 260, 34, "#fcc2d7") + flower(440, 260, 34, "#f06595")
    + '<path d="M330,430 L470,430 L440,560 L360,560 Z" fill="#9775fa"/><path d="M330,430 L470,430 L455,470 L345,470 Z" fill="#b197fc"/>'
    + heart(400, 505, 16, "#ffffff"))

tie_stripes = "".join(f'<path d="M{335 + i * 4},{240 + i * 60} L{465 - i * 2},{210 + i * 60}" stroke="#ffd43b" stroke-width="10" opacity=".85"/>' for i in range(4))
ART["fathers-day"] = svg(
    sky("s", [(0, "#1c3d6e"), (1, "#4a7fc1")]),
    '<rect width="800" height="600" fill="url(#s)"/>'
    + "".join(f'<rect x="{x}" y="0" width="40" height="600" fill="#fff" opacity=".04"/>' for x in range(0, 800, 80))
    + '<path d="M300,60 L500,60 L560,140 L400,190 L240,140 Z" fill="#f1f3f5"/><path d="M300,60 L400,120 L500,60" fill="none" stroke="#ced4da" stroke-width="4"/>'
    + '<path d="M370,120 L430,120 L445,160 L400,180 L355,160 Z" fill="#c92a2a"/>'
    + '<clipPath id="tie"><path d="M375,175 L425,175 L470,440 L400,520 L330,440 Z"/></clipPath>'
    + f'<path d="M375,175 L425,175 L470,440 L400,520 L330,440 Z" fill="#e03131"/><g clip-path="url(#tie)">{tie_stripes}</g>'
    + '<g transform="translate(150,420) rotate(-12)"><rect x="-45" y="-30" width="90" height="60" rx="6" fill="#3b2a1e"/><rect x="-45" y="-30" width="90" height="16" fill="#5c4033"/></g>'
    + '<g transform="translate(660,430)"><rect x="-38" y="-26" width="76" height="70" rx="8" fill="#f8f9fa"/><path d="M38,-6 c26,0 26,34 0,34" stroke="#f8f9fa" stroke-width="9" fill="none"/><rect x="-38" y="-26" width="76" height="14" fill="#c92a2a"/></g>')


def bat(cx, cy, s):
    return (f'<path d="M0,0 C-10,-14 -24,-16 -40,-8 C-32,-4 -30,4 -34,10 C-26,4 -18,6 -14,12 C-10,6 -4,4 0,8 C4,4 10,6 14,12 '
            f'C18,6 26,4 34,10 C30,4 32,-4 40,-8 C24,-16 10,-14 0,0 Z" fill="#14081f" transform="translate({cx},{cy}) scale({s})"/>')


ART["halloween"] = svg(
    sky("s", [(0, "#1b0b33"), (.7, "#4a1d6b"), (1, "#f76707")]),
    '<rect width="800" height="600" fill="url(#s)"/>' + stars_field(50, 61, 0, 300)
    + '<circle cx="610" cy="140" r="80" fill="#fff3bf"/><circle cx="585" cy="120" r="12" fill="#ffe8a3"/><circle cx="635" cy="165" r="9" fill="#ffe8a3"/>'
    + bat(200, 120, 1.4) + bat(300, 80, 1) + bat(480, 150, 1.2) + bat(700, 260, .9)
    + '<path d="M0,470 C140,440 260,470 400,455 C540,440 660,470 800,455 L800,600 L0,600 Z" fill="#14081f"/>'
    + '<g transform="translate(400,400)"><ellipse cx="-55" cy="0" rx="60" ry="75" fill="#e8590c"/><ellipse cx="55" cy="0" rx="60" ry="75" fill="#e8590c"/><ellipse cx="0" cy="0" rx="70" ry="82" fill="#fd7e14"/>'
      '<path d="M0,-80 C0,-100 10,-112 22,-116" stroke="#2b8a3e" stroke-width="10" fill="none" stroke-linecap="round"/>'
      '<polygon points="-60,-20 -25,-20 -42,-50" fill="#ffd43b"/><polygon points="60,-20 25,-20 42,-50" fill="#ffd43b"/><polygon points="-10,0 10,0 0,-18" fill="#ffd43b"/>'
      '<path d="M-60,20 Q0,70 60,20 L45,30 L35,18 L22,34 L10,20 L-2,36 L-14,20 L-26,34 L-38,18 L-48,30 Z" fill="#ffd43b"/></g>')

rc = random.Random(71)
confetti = "".join(
    f'<rect x="{rc.uniform(0, 800):.0f}" y="{rc.uniform(0, 600):.0f}" width="{rc.uniform(6, 12):.0f}" height="{rc.uniform(3, 6):.0f}" '
    f'fill="{rc.choice(["#ffd43b", "#ff6b9a", "#4dabf7", "#ffffff", "#b197fc"])}" opacity=".9"/>'
    for _ in range(120))
ticks = "".join(f'<rect x="397" y="132" width="{6 if i % 3 == 0 else 3}" height="{20 if i % 3 == 0 else 10}" fill="#1b1b3a" transform="rotate({i * 30} 400 280)"/>' for i in range(12))
ART["new-years-eve"] = svg(
    sky("s", [(0, "#0b0b2e"), (1, "#3b1d6e")]),
    '<rect width="800" height="600" fill="url(#s)"/>' + stars_field(60, 81) + confetti
    + '<circle cx="400" cy="280" r="160" fill="#d4af37"/><circle cx="400" cy="280" r="146" fill="#fff8e1"/>' + ticks
    + '<rect x="396" y="160" width="8" height="125" rx="4" fill="#1b1b3a" transform="rotate(-3 400 280)"/>'
    + '<rect x="395" y="205" width="10" height="80" rx="5" fill="#1b1b3a" transform="rotate(-8 400 280)"/>'
    + '<circle cx="400" cy="280" r="10" fill="#d4af37"/>'
    + firework(130, 130, 70, "#ffd43b", 16, seed=91) + firework(680, 120, 65, "#ff6b9a", 14, seed=92))

for slug, content in ART.items():
    with open(os.path.join(OUT, f"{slug}.svg"), "w", encoding="utf-8") as f:
        f.write(content)
    print(slug, len(content))
