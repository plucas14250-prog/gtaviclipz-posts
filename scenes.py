"""List the scene changes in a trailer and make a contact sheet to pick moments from.

Usage: python3 scenes.py footage/trailer2.mp4 [out_dir]

Prints one line per scene (start time, length) and saves
<out_dir>/<name>-scenes.jpg with a labelled thumbnail of every scene.
Open the sheet, pick an interesting shot, and pass its time to make_clip.py.
"""
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont


def duration(src):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", src], capture_output=True, text=True).stdout
    return float(out.strip())


def cuts(src, threshold=0.3):
    proc = subprocess.run(["ffmpeg", "-i", src, "-vf",
                           f"scale=320:-2,select='gt(scene,{threshold})',showinfo",
                           "-f", "null", "-"], capture_output=True, text=True)
    return [float(t) for t in re.findall(r"pts_time:([0-9.]+)", proc.stderr)]


def main():
    src = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    os.makedirs(out_dir, exist_ok=True)
    total = duration(src)
    starts = [0.0] + [t for t in cuts(src) if t > 0.5]
    scenes = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else total
        if e - s >= 1.0:
            scenes.append((s, e - s))

    thumbs = []
    for s, length in scenes:
        t = s + min(length / 2, 1.5)
        png = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", src, "-frames:v", "1",
                              "-vf", "scale=320:-2", "-f", "image2pipe", "-vcodec", "png", "-"],
                             capture_output=True).stdout
        path = os.path.join(out_dir, f"_t{len(thumbs)}.png")
        open(path, "wb").write(png)
        thumbs.append(path)
        print(f"{s:7.2f}s  ({length:4.1f}s)")

    if not thumbs:
        return
    cols = 6
    tw, th = 320, 180 + 28
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), "black")
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 20)
    for k, (path, (s, length)) in enumerate(zip(thumbs, scenes)):
        im = Image.open(path)
        im.thumbnail((tw, 180))
        x, y = (k % cols) * tw, (k // cols) * th
        sheet.paste(im, (x, y))
        d.text((x + 6, y + 182), f"{s:.1f}s  ({length:.1f}s)", font=f, fill="white")
        os.remove(path)
    name = os.path.splitext(os.path.basename(src))[0]
    sheet_path = os.path.join(out_dir, f"{name}-scenes.jpg")
    sheet.save(sheet_path, quality=85)
    print("sheet:", sheet_path)


if __name__ == "__main__":
    main()
