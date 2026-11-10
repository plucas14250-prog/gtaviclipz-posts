"""Make a 1080x1350 feed image from a frame of a trailer, with the Reel fonts.

Usage:
  python3 frame_post.py footage/launch-trailer.mp4 --time 40.5 --x 0.5 \
      --top "Faltam 9 dias" --line2 "19 de novembro • PS5 e Xbox Series" --out posts/x.jpg

--x picks which part of the wide frame to keep (0 = left, 1 = right).
Text sits at the bottom over a dark fade; @handle and the Rockstar credit are added.
"""
import argparse
import os
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1080, 1350
HERE = os.path.dirname(os.path.abspath(__file__))
F_HEAD = os.path.join(HERE, "assets", "fonts", "Anton.woff")
F_SEMI = os.path.join(HERE, "assets", "fonts", "Oswald-SemiBold.woff")
F_REG = os.path.join(HERE, "assets", "fonts", "Oswald-Regular.woff")
YELLOW = (255, 212, 40)


def wrap(d, text, font, max_w):
    lines, cur = [], ""
    for word in text.split(" "):
        test = (cur + " " + word).strip()
        if d.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def main():
    p = argparse.ArgumentParser()
    p.add_argument("src")
    p.add_argument("--time", type=float, required=True)
    p.add_argument("--x", type=float, default=0.5)
    p.add_argument("--srccrop", help='crop the source frame first, e.g. "1920:960:0:60"')
    p.add_argument("--top", required=True)
    p.add_argument("--line2")
    p.add_argument("--out", required=True)
    a = p.parse_args()

    tmp = os.path.join(tempfile.mkdtemp(), "f.png")
    vf = (f"crop={a.srccrop}," if a.srccrop else "") + "scale=-2:1350"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a.time), "-i", a.src,
                    "-frames:v", "1", "-vf", vf, tmp], check=True)
    fr = Image.open(tmp).convert("RGB")
    if fr.width < W:
        fr = fr.resize((W, round(fr.height * W / fr.width)), Image.LANCZOS)
    left = round((fr.width - W) * min(max(a.x, 0), 1))
    img = fr.crop((left, 0, left + W, H))
    img = ImageEnhance.Contrast(img).enhance(1.06).filter(ImageFilter.UnsharpMask(2, 60, 2))

    # dark fade at the bottom for the text
    fade = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(fade)
    for y in range(H):
        fd.line([(0, y), (W, y)], fill=int(235 * max(0, (y - 700) / 650) ** 1.3))
    img = Image.composite(Image.new("RGB", (W, H), (8, 8, 10)), img, fade)

    d = ImageDraw.Draw(img)
    hf = ImageFont.truetype(F_HEAD, 150)
    lines = wrap(d, a.top.upper(), hf, W - 120)
    while len(lines) > 2:
        hf = ImageFont.truetype(F_HEAD, hf.size - 10)
        lines = wrap(d, a.top.upper(), hf, W - 120)
    lf = ImageFont.truetype(F_SEMI, 50)
    l2 = wrap(d, a.line2.upper(), lf, W - 140) if a.line2 else []

    block = len(lines) * int(hf.size * 1.05) + (20 + len(l2) * int(lf.size * 1.25) if l2 else 0)
    y = H - 120 - block
    for line in lines:
        d.text(((W - d.textlength(line, font=hf)) / 2, y), line, font=hf, fill="white")
        y += int(hf.size * 1.05)
    if l2:
        y += 20
        for line in l2:
            d.text(((W - d.textlength(line, font=lf)) / 2, y), line, font=lf, fill=YELLOW)
            y += int(lf.size * 1.25)

    sf = ImageFont.truetype(F_REG, 30)
    d.text((50, H - 62), "@gtaviclipz_6", font=sf, fill="white")
    credit = "Imagens: Rockstar Games"
    d.text((W - 50 - d.textlength(credit, font=sf), H - 62), credit, font=sf, fill=(210, 210, 210))
    img.save(a.out, "JPEG", quality=93)
    print("saved", a.out)


if __name__ == "__main__":
    main()
