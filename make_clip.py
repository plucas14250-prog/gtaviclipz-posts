"""Cut a vertical Reel (1080x1920) from a trailer, with text on top.

Example:
  python3 make_clip.py footage/trailer2.mp4 --start 41.2 --dur 8 \
      --tag "VOCÊ VIU?" --top "NINGUÉM PERCEBEU ESSE DETALHE" \
      --bottom "o carro dá seta sozinho" --badge "FALTAM 9 DIAS" \
      --x 0.5 --zoom 1.15 --out posts/2026-11-10-pm.mp4

Options:
  --start / --dur   where in the trailer to cut (seconds)
  --x               which part of the wide frame to keep, 0 = left, 0.5 = center, 1 = right
  --zoom            slow push-in over the clip (1.0 = none, 1.2 = 20% closer by the end)
  --slow            playback speed (0.5 = half speed, good for details)
  --tag             small red label above the headline (e.g. NOTÍCIA, VOCÊ VIU?)
  --top             big headline at the top
  --bottom          subtitle box near the bottom
  --badge           pink pill in the top-right corner (e.g. a countdown)
  --keep-audio      keep the trailer's own audio (off by default: the owner adds
                    Instagram music, and trailer music can get the Reel muted)
Every clip gets "Imagens: Rockstar Games" and @gtaviclipz_6 in small text.
"""
import argparse
import os
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
RED = (230, 20, 40)
PINK = (255, 40, 140)


def wrap(d, text, font, max_w):
    lines, cur = [], ""
    for word in text.split():
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


def overlay_png(args, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Dark gradient at the top so the headline is always readable.
    if args.top or args.tag:
        for y in range(700):
            a = int(200 * (1 - y / 700) ** 1.5)
            d.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    y = 150
    if args.tag:
        tf = ImageFont.truetype(F_BOLD, 46)
        tw = d.textlength(args.tag.upper(), font=tf)
        d.rounded_rectangle([60, y, 60 + tw + 44, y + 72], radius=10, fill=RED)
        d.text((82, y + 9), args.tag.upper(), font=tf, fill="white")
        y += 100
    if args.top:
        f, lines = fit_font(d, args.top.upper(), F_BLACK, 112, W - 120, 3)
        for line in lines:
            d.text((60, y), line, font=f, fill="white", stroke_width=6, stroke_fill="black")
            y += int(f.size * 1.05)

    if args.badge:
        bf = ImageFont.truetype(F_BOLD, 40)
        bw = d.textlength(args.badge.upper(), font=bf)
        x0 = W - 60 - bw - 48
        d.rounded_rectangle([x0, 60, W - 60, 128], radius=34, fill=PINK)
        d.text((x0 + 24, 72), args.badge.upper(), font=bf, fill="white")

    if args.bottom:
        sf, lines = fit_font(d, args.bottom.upper(), F_BOLD, 58, W - 200, 2)
        lh = int(sf.size * 1.25)
        box_h = lh * len(lines) + 50
        top = 1500 - box_h // 2
        d.rounded_rectangle([60, top, W - 60, top + box_h], radius=24, fill=(0, 0, 0, 190))
        for i, line in enumerate(lines):
            lw = d.textlength(line, font=sf)
            d.text(((W - lw) / 2, top + 25 + i * lh), line, font=sf, fill="white")

    small = ImageFont.truetype(F_BOLD, 30)
    d.text((60, H - 110), "Imagens: Rockstar Games", font=small, fill=(255, 255, 255, 200),
           stroke_width=2, stroke_fill=(0, 0, 0, 160))
    hw = d.textlength("@gtaviclipz_6", font=small)
    d.text((W - 60 - hw, H - 110), "@gtaviclipz_6", font=small, fill="white",
           stroke_width=2, stroke_fill=(0, 0, 0, 160))
    img.save(path)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("src")
    p.add_argument("--start", type=float, required=True)
    p.add_argument("--dur", type=float, default=8)
    p.add_argument("--x", type=float, default=0.5)
    p.add_argument("--zoom", type=float, default=1.1)
    p.add_argument("--slow", type=float, default=1.0)
    p.add_argument("--tag")
    p.add_argument("--top")
    p.add_argument("--bottom")
    p.add_argument("--badge")
    p.add_argument("--keep-audio", action="store_true")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    out_dur = args.dur / args.slow
    tmp = tempfile.mkdtemp()
    ov = os.path.join(tmp, "overlay.png")
    overlay_png(args, ov)

    z = max(args.zoom, 1.0)
    x = min(max(args.x, 0.0), 1.0)
    vf = (
        f"[0:v]setpts=(PTS-STARTPTS)/{args.slow},"
        f"scale=w=-2:h='trunc({H}*(1+({z}-1)*t/{out_dur})/2)*2':eval=frame,"
        f"crop={W}:{H}:'(iw-{W})*{x}':'(ih-{H})/2',fps=30,format=yuv420p[v];"
        f"[v][1:v]overlay=0:0[out]"
    )
    cmd = ["ffmpeg", "-y", "-ss", str(args.start), "-t", str(args.dur), "-i", args.src,
           "-i", ov]
    if args.keep_audio:
        cmd += ["-filter_complex", vf + f";[0:a]atempo={max(args.slow, 0.5)}[a]",
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
