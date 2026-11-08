"""Make a 1080x1350 Instagram image in an original Vice City sunset style.

Usage:
  python3 make_post.py countdown <days> <out.jpg>
  python3 make_post.py card "<KICKER>" "<HEADLINE>" "<SUBTEXT>" <out.jpg>
"""
import math
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1350
F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
F_XBOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"

PINK = (255, 64, 160)
CYAN = (40, 230, 255)
WHITE = (255, 255, 255)


def font(path, size):
    return ImageFont.truetype(path, size)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def background():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    stops = [(0.0, (22, 8, 48)), (0.45, (120, 20, 110)), (0.7, (255, 90, 120)), (1.0, (255, 170, 80))]
    for y in range(H):
        t = y / H
        for i in range(len(stops) - 1):
            if stops[i][0] <= t <= stops[i + 1][0]:
                k = (t - stops[i][0]) / (stops[i + 1][0] - stops[i][0])
                d.line([(0, y), (W, y)], fill=lerp(stops[i][1], stops[i + 1][1], k))
                break

    # Striped sun behind the horizon.
    sun = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(sun)
    cx, cy, r = W // 2, 1010, 330
    sd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    for i in range(7):
        y = cy - 40 + i * 42
        sd.rectangle([0, y, W, y + 6 + i * 3], fill=0)
    sun_col = Image.new("RGB", (W, H), (255, 200, 90))
    glow = sun.filter(ImageFilter.GaussianBlur(40))
    img = Image.composite(Image.new("RGB", (W, H), (255, 120, 140)), img, glow.point(lambda v: v // 3))
    img = Image.composite(sun_col, img, sun)

    # Ocean band and palm silhouettes.
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1130, W, H], fill=(30, 10, 50))
    for i in range(12):
        y = 1145 + i * 18
        d.line([(80 + i * 15, y), (W - 80 - i * 15, y)], fill=(255, 120, 160), width=2)
    palm(d, 90, 1140, 1)
    palm(d, W - 90, 1140, -1)
    return img


def palm(d, x, base, side):
    dark = (14, 4, 28)
    top = (x + side * 60, base - 430)
    pts = []
    for i in range(21):
        t = i / 20
        px = x + side * 60 * t ** 1.6
        py = base - 430 * t
        pts.append((px, py))
    d.line(pts, fill=dark, width=26)
    for ang in [-150, -115, -70, -30, 10, 40]:
        a = math.radians(ang if side == 1 else 180 - ang)
        frond = []
        for j in range(16):
            t = j / 15
            fx = top[0] + math.cos(a) * 200 * t
            fy = top[1] + math.sin(a) * 200 * t + 90 * t * t
            frond.append((fx, fy))
        d.line(frond, fill=dark, width=18)


def centered(d, y, text, f, fill, shadow=None, stroke=0):
    w = d.textlength(text, font=f)
    x = (W - w) / 2
    if shadow:
        d.text((x + 8, y + 8), text, font=f, fill=shadow, stroke_width=stroke, stroke_fill=shadow)
    d.text((x, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=(20, 0, 40))


def wrap(d, text, f, max_w):
    lines, cur = [], ""
    for word in text.split():
        test = (cur + " " + word).strip()
        if d.textlength(test, font=f) <= max_w:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def handle(d):
    centered(d, 1275, "@gtaviclipz_6", font(F_BOLD, 34), WHITE)


def countdown(days, out):
    img = background()
    d = ImageDraw.Draw(img)
    centered(d, 110, "FALTA" if days == 1 else "FALTAM", font(F_BLACK, 110), WHITE, shadow=PINK)
    num = str(days)
    centered(d, 230, num, font(F_BLACK, 400), CYAN, shadow=(120, 0, 90), stroke=6)
    centered(d, 690, "DIA" if days == 1 else "DIAS", font(F_BLACK, 130), WHITE, shadow=PINK)
    centered(d, 850, "PARA VICE CITY", font(F_XBOLD, 56), WHITE, stroke=4)
    centered(d, 925, "19 • 11 • 2026", font(F_XBOLD, 42), WHITE, stroke=4)
    handle(d)
    img.save(out, "JPEG", quality=92)


def card(kicker, headline, sub, out):
    img = background()
    d = ImageDraw.Draw(img)
    kf = font(F_XBOLD, 44)
    kw = d.textlength(kicker, font=kf) + 60
    d.rounded_rectangle([(W - kw) / 2, 120, (W + kw) / 2, 195], radius=38, fill=PINK)
    centered(d, 132, kicker, kf, WHITE)
    size = 120
    while size > 60:
        hf = font(F_BLACK, size)
        lines = wrap(d, headline.upper(), hf, W - 140)
        if len(lines) * size * 1.08 <= 520:
            break
        size -= 6
    y = 250
    for line in lines:
        centered(d, y, line, hf, WHITE, shadow=(120, 0, 90), stroke=3)
        y += int(size * 1.08)
    sf = font(F_XBOLD, 46)
    for line in wrap(d, sub, sf, W - 180):
        centered(d, y + 30, line, sf, WHITE, stroke=4)
        y += 54
    handle(d)
    img.save(out, "JPEG", quality=92)


if __name__ == "__main__":
    kind = sys.argv[1]
    if kind == "countdown":
        countdown(int(sys.argv[2]), sys.argv[3])
    else:
        card(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
