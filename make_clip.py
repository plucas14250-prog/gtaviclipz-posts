"""Cut a vertical Reel (1080x1920) from a trailer, with text on top.

Example:
  python3 make_clip.py footage/trailer2.mp4 --start 41.2 --dur 8 \
      --tag "VOCÊ VIU?" --top "NINGUÉM PERCEBEU ESSE DETALHE" \
      --line2 "o carro dá seta sozinho" --badge "FALTAM 9 DIAS" \
      --x 0.5 --zoom 1.15 --out posts/2026-11-10-pm.mp4

Options:
  --start / --dur   where in the trailer to cut (seconds)
  --cuts            montage instead: "start:dur:x,start:dur:x,..." (see footage/*-shots.json)
  --x               which part of the wide frame to keep, 0 = left, 0.5 = center, 1 = right
  --zoom            slow push-in over the clip (1.0 = none, 1.2 = 20% closer by the end)
  --slow            playback speed (0.5 = half speed, good for details)
  --tag             small red label above the headline (e.g. NOTÍCIA, VOCÊ VIU?)
  --top             big headline at the top
  --line2           second line right under the headline (smaller, yellow)
  --bottom          (avoid) subtitle box near the bottom; only for people talking
  --badge           pink pill in the top-right corner (e.g. a countdown)
  --keep-audio      keep the trailer's own audio (off by default: the owner adds
                    Instagram music, and trailer music can get the Reel muted)
Every clip gets "Imagens: Rockstar Games" and @gtaviclipz_6 in small text.
"""
import argparse
import re
import os
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
RED = (230, 20, 40)
YELLOW = (255, 212, 40)
BG = (10, 10, 12)
BAR = 720  # height of the top area (profile + text); the video fills the rest
_FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")
F_HEAD = os.path.join(_FONTS, "Anton.woff")            # big headline, same style as the Canva designs
F_SEMI = os.path.join(_FONTS, "Oswald-SemiBold.woff")  # second line and page name
F_REG = os.path.join(_FONTS, "Oswald-Regular.woff")    # handle and credit
NAME = "GTA VI CLIPZ"
HANDLE = "@gtaviclipz_6"
AVATAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "avatar.jpg")
PINK = (255, 40, 140)


def clean(text):
    """Drop emoji and other symbols the font can't draw (they'd show as boxes)."""
    if not text:
        return text
    out = "".join(ch for ch in text if ord(ch) < 0x2190 or 0x2190 <= ord(ch) <= 0x21FF or ch in "•–—…")
    return " ".join(out.split())


def detect_bars(src):
    """Find black letterbox bars (e.g. cinema-style trailers) so they can be cropped off.
    Ignores results that would cut into the picture (dark scenes fool cropdetect)."""
    proc = subprocess.run(["ffmpeg", "-ss", "15", "-i", src, "-t", "30", "-vf", "cropdetect=24:2:0",
                           "-f", "null", "-"], capture_output=True, text=True)
    found = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", proc.stderr)
    size = re.search(r"Stream.*Video.* (\d{3,5})x(\d{3,5})", proc.stderr)
    if not found or not size:
        return None
    sw, sh = int(size.group(1)), int(size.group(2))
    w, h, x, y = map(int, max(set(found), key=found.count))
    if w < sw * 0.95 or h < sh * 0.6:
        return None
    return f"crop={w}:{h}:{x}:{y},"


def wrap(d, text, font, max_w):
    # Keep names like "GTA 6" on one line.
    for name in ("GTA 6", "GTA VI", "GTA 5", "GTA V"):
        text = text.replace(name, name.replace(" ", "\u00a0"))
    lines, cur = [], ""
    for word in [w for w in text.split(" ") if w]:
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


def fit_font(d, text, path, start, max_w, max_lines):
    size = start
    while size > 40:
        f = ImageFont.truetype(path, size)
        lines = wrap(d, text, f, max_w)
        if len(lines) <= max_lines:
            return f, lines
        size -= 6
    f = ImageFont.truetype(path, size)
    return f, wrap(d, text, f, max_w)


def avatar_circle(path, size):
    im = Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size * 4, size * 4], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask.resize((size, size), Image.LANCZOS))
    return out


def overlay_png(args, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, BAR], fill=BG)

    # Profile row: avatar with a gradient ring, name and handle, centered.
    av, ring = 112, 6
    name_f = ImageFont.truetype(F_SEMI, 44)
    handle_f = ImageFont.truetype(F_REG, 34)
    text_w = max(d.textlength(NAME, font=name_f), d.textlength(HANDLE, font=handle_f))
    row_w = av + 2 * ring + 28 + text_w
    x0, y0 = int((W - row_w) / 2), 96
    grad = Image.new("RGBA", (av + 2 * ring, av + 2 * ring))
    gd = ImageDraw.Draw(grad)
    for i in range(av + 2 * ring):
        t = i / (av + 2 * ring)
        col = tuple(int(PINK[k] * (1 - t) + (255, 170, 0)[k] * t) for k in range(3))
        gd.line([(i, 0), (i, av + 2 * ring)], fill=col + (255,))
    ring_mask = Image.new("L", grad.size, 0)
    ImageDraw.Draw(ring_mask).ellipse([0, 0, grad.size[0] - 1, grad.size[1] - 1], fill=255)
    img.paste(grad, (x0, y0), ring_mask)
    d.ellipse([x0 + ring - 3, y0 + ring - 3, x0 + ring + av + 2, y0 + ring + av + 2], fill=BG)
    if os.path.exists(AVATAR):
        img.alpha_composite(avatar_circle(AVATAR, av), (x0 + ring, y0 + ring))
    tx = x0 + av + 2 * ring + 28
    d.text((tx, y0 + 14), NAME, font=name_f, fill="white")
    d.text((tx, y0 + 70), HANDLE, font=handle_f, fill=(150, 150, 150))
    top_of_text = y0 + av + 2 * ring + 40

    # Build the text block, then center it in the space left above the video.
    block = []
    pills = []  # tags/badges removed: keep the top clean
    pill_f = ImageFont.truetype(F_BOLD, 32)
    head_f, head_lines = (None, [])
    if args.top:
        head_f, head_lines = fit_font(d, args.top.upper(), F_HEAD, 96, W - 140, 3)
    l2_f, l2_lines = (None, [])
    if args.line2:
        l2_f, l2_lines = fit_font(d, args.line2.upper(), F_SEMI, 48, W - 160, 2)
    h = 0
    if pills:
        h += 58 + 28
    if head_lines:
        h += int(head_f.size * 1.12) * len(head_lines)
    if l2_lines:
        h += 18 + int(l2_f.size * 1.3) * len(l2_lines)
    y = top_of_text + max(0, (BAR - 50 - top_of_text - h) // 2)

    if pills:
        gap = 16
        widths = [d.textlength(t, font=pill_f) + 44 for t, _ in pills]
        px = (W - sum(widths) - gap * (len(pills) - 1)) / 2
        for (t, c), w in zip(pills, widths):
            d.rounded_rectangle([px, y, px + w, y + 58], radius=29, fill=c)
            d.text((px + 22, y + 11), t, font=pill_f, fill="white")
            px += w + gap
        y += 58 + 28
    for line in head_lines:
        lw = d.textlength(line, font=head_f)
        d.text(((W - lw) / 2, y), line, font=head_f, fill="white")
        y += int(head_f.size * 1.12)
    if l2_lines:
        y += 18
        for line in l2_lines:
            lw = d.textlength(line, font=l2_f)
            d.text(((W - lw) / 2, y), line, font=l2_f, fill=YELLOW)
            y += int(l2_f.size * 1.3)

    # Rounded top corners on the video, and a soft fade at the bottom for the credit.
    r = 44
    corner = Image.new("L", (r * 4, r * 4), 255)
    ImageDraw.Draw(corner).pieslice([0, 0, r * 8, r * 8], 180, 270, fill=0)
    corner = corner.resize((r, r), Image.LANCZOS)
    bgc = Image.new("RGBA", (r, r), BG + (255,))
    img.paste(bgc, (0, BAR), corner)
    img.paste(bgc, (W - r, BAR), corner.transpose(Image.FLIP_LEFT_RIGHT))
    for i in range(160):
        a = int(150 * (i / 160) ** 2)
        d.line([(0, H - 160 + i), (W, H - 160 + i)], fill=(0, 0, 0, a))
    cf = ImageFont.truetype(F_REG, 30)
    credit = "Imagens: Rockstar Games"
    d.text(((W - d.textlength(credit, font=cf)) / 2, H - 72), credit, font=cf, fill=(220, 220, 220, 230))

    if args.bottom:
        sf, lines = fit_font(d, args.bottom.upper(), F_BOLD, 54, W - 200, 2)
        lh = int(sf.size * 1.25)
        box_h = lh * len(lines) + 50
        top = H - 420
        d.rounded_rectangle([60, top, W - 60, top + box_h], radius=24, fill=(0, 0, 0, 190))
        for i, line in enumerate(lines):
            lw = d.textlength(line, font=sf)
            d.text(((W - lw) / 2, top + 25 + i * lh), line, font=sf, fill="white")
    img.save(path)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("src")
    p.add_argument("--start", type=float)
    p.add_argument("--cuts")
    p.add_argument("--dur", type=float, default=8)
    p.add_argument("--x", type=float, default=0.5)
    p.add_argument("--zoom", type=float, default=1.1)
    p.add_argument("--slow", type=float, default=1.0)
    p.add_argument("--tag")
    p.add_argument("--top")
    p.add_argument("--line2")
    p.add_argument("--bottom")
    p.add_argument("--badge")
    p.add_argument("--keep-audio", action="store_true")
    p.add_argument("--srccrop", help='crop the source first, e.g. "1920:1080:0:124" (overrides bar detection)')
    p.add_argument("--fit", action="store_true",
                   help="show the whole frame (for screen recordings with text) on a blurred copy instead of cropping")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    for k in ("tag", "top", "line2", "bottom", "badge"):
        setattr(args, k, clean(getattr(args, k)))
    bars = f"crop={args.srccrop}," if args.srccrop else (detect_bars(args.src) or "")
    tmp = tempfile.mkdtemp()
    ov = os.path.join(tmp, "overlay.png")
    overlay_png(args, ov)
    z = max(args.zoom, 1.0)

    if args.cuts:
        segs = []
        for part in args.cuts.split(","):
            a = part.split(":")
            segs.append((float(a[0]), float(a[1]), float(a[2]) if len(a) > 2 else args.x))
    else:
        if args.start is None:
            p.error("give --start or --cuts")
        segs = [(args.start, args.dur, args.x)]

    chains, labels, total = [], [], 0.0
    for i, (st, du, xx) in enumerate(segs):
        od = du / args.slow
        xx = min(max(xx, 0.0), 1.0)
        if args.fit:
            vh = H - BAR
            chains.append(
                f"[0:v]trim=start={st}:duration={du},setpts=(PTS-STARTPTS)/{args.slow},{bars}split[a{i}][b{i}];"
                f"[a{i}]scale=-2:{vh},crop={W}:{vh},boxblur=25:4,eq=brightness=-0.25[bg{i}];"
                f"[b{i}]scale={W}:-2[fg{i}];"
                f"[bg{i}][fg{i}]overlay=0:(H-h)/2,pad={W}:{H}:0:{BAR}:0x0A0A0C,fps=30,format=yuv420p,setsar=1[s{i}]")
            labels.append(f"[s{i}]")
            total += od
            continue
        chains.append(
            f"[0:v]trim=start={st}:duration={du},setpts=(PTS-STARTPTS)/{args.slow},{bars}"
            f"scale=w=-2:h='trunc({H - BAR}*(1+({z}-1)*t/{od})/2)*2':eval=frame,"
            f"crop={W}:{H - BAR}:'(iw-{W})*{xx}':'(ih-{H - BAR})/2',"
            f"pad={W}:{H}:0:{BAR}:0x0A0A0C,fps=30,format=yuv420p,setsar=1[s{i}]")
        labels.append(f"[s{i}]")
        total += od
    vf = ";".join(chains) + ";" + "".join(labels) + f"concat=n={len(segs)}:v=1:a=0[v];[v][1:v]overlay=0:0[out]"
    out_dur = total

    cmd = ["ffmpeg", "-y", "-i", args.src, "-i", ov]
    if args.keep_audio and len(segs) == 1:
        st, du, _ = segs[0]
        cmd += ["-filter_complex", vf + f";[0:a]atrim=start={st}:duration={du},asetpts=PTS-STARTPTS,atempo={max(args.slow, 0.5)}[a]",
                "-map", "[out]", "-map", "[a]"]
    else:
        cmd += ["-f", "lavfi", "-t", str(out_dur), "-i", "anullsrc=r=44100:cl=stereo",
                "-filter_complex", vf, "-map", "[out]", "-map", "2:a"]
    cmd += ["-t", str(out_dur), "-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", args.out]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    print("saved", args.out, f"({out_dur:.1f}s)")


if __name__ == "__main__":
    main()
