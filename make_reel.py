"""Turn 1-6 images into a vertical Reel (1080x1920 MP4) with slow zooms and crossfades.

Usage: python3 make_reel.py out.mp4 img1 [img2 ...] [--sec 3.5] [--music music/track.mp3]

Each image becomes a slide. Portrait 4:5 images are centered on a blurred copy of
themselves so the 9:16 frame is filled. Without --music, a random track from music/
is used if one exists; otherwise the Reel has silent audio.
"""
import glob
import os
import random
import subprocess
import sys
import tempfile

W, H, FPS, FADE = 1080, 1920, 30, 0.5


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def slide(img, sec, out, zoom_in):
    frames = int(sec * FPS)
    z = "min(1+0.0012*on,1.12)" if zoom_in else "max(1.12-0.0012*on,1)"
    vf = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:5,eq=brightness=-0.15[bg];"
        f"[0:v]scale={W}:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,"
        f"scale={W*2}:{H*2},zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},format=yuv420p"
    )
    run(["ffmpeg", "-y", "-loop", "1", "-i", img, "-filter_complex", vf, "-t", str(sec),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out])


def main():
    args = sys.argv[1:]
    sec, music = 3.5, None
    if "--sec" in args:
        i = args.index("--sec"); sec = float(args[i + 1]); del args[i:i + 2]
    if "--music" in args:
        i = args.index("--music"); music = args[i + 1]; del args[i:i + 2]
    out, imgs = args[0], args[1:]
    if not music:
        tracks = glob.glob("music/*.mp3") + glob.glob("music/*.m4a")
        music = random.choice(tracks) if tracks else None

    tmp = tempfile.mkdtemp()
    parts = []
    for k, img in enumerate(imgs):
        p = os.path.join(tmp, f"s{k}.mp4")
        slide(img, sec + (FADE if k < len(imgs) - 1 else 0), p, k % 2 == 0)
        parts.append(p)

    # Chain crossfades between slides.
    inputs, chain, last = [], [], "[0:v]"
    for p in parts:
        inputs += ["-i", p]
    # Every slide but the last is FADE longer, so transition k starts at k * sec.
    for k in range(1, len(parts)):
        tag = f"[v{k}]"
        chain.append(f"{last}[{k}:v]xfade=transition=fade:duration={FADE}:offset={round(k * sec, 3)}{tag}")
        last = tag
    total = sec * len(parts)
    video = os.path.join(tmp, "v.mp4")
    if chain:
        run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(chain), "-map", last,
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", video])
    else:
        video = parts[0]

    audio = ["-i", music] if music else ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    afilter = ["-af", f"afade=t=out:st={max(total - 1.5, 0)}:d=1.5"] if music else []
    run(["ffmpeg", "-y", "-i", video, *audio, "-map", "0:v", "-map", "1:a", *afilter,
         "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out])
    print("saved", out, f"({total:.1f}s)")


if __name__ == "__main__":
    main()
