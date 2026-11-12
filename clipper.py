r"""Auto-clipper: turn a long video (podcast, stream, interview) into vertical
short clips with word-by-word captions, ready for TikTok / Reels / Shorts.

Does the same job as Ssemble in the "clipping" workflow, locally and with no
watermark:
  1. transcribes the video (faster-whisper, word timestamps, cached)
  2. scores every 20-60 s stretch of speech and picks the best ones
     (strong first line, numbers/money/questions, fast talking, ends on a
     full sentence)
  3. crops to 9:16 following the speaker's face
  4. burns in big word-by-word captions (current word in yellow)
  5. optional headline box on top ("N3on REVEALS ...")

Usage:
  python3 clipper.py SOURCE.mp4 --name n3on                 # 5 best clips
  python3 clipper.py SOURCE.mp4 --name n3on --count 8 --min 15 --max 45
  python3 clipper.py SOURCE.mp4 --name n3on --list          # only list candidates
  python3 clipper.py SOURCE.mp4 --name n3on --at 754.2:38 --hook "HE SPENDS \$1M ON CLIPPERS"
  python3 clipper.py SOURCE.mp4 --name n3on --only 3 --hook "..."   # re-render pick #3

Needs: pip install faster-whisper "opencv-python-headless<5"
(the speech model downloads from huggingface.co on first run).

Output goes to clips/<name>/: clip-01.mp4 ..., transcript.json, clips.md
(times, score, transcript and a caption idea for each clip).
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "assets", "fonts")
F_CAPTION = os.path.join(FONTS, "Anton.woff")
F_HOOK = os.path.join(FONTS, "Oswald-SemiBold.woff")
W, H = 1080, 1920

HOOK_WORDS = set("""
never nobody secret million millions billion thousand crazy insane truth
worst best why how what actually money paid pay fired banned broke rich
lost quit hate love dead died real lie lied scam illegal free first last
only biggest every everyone stop wrong mistake regret shocking honestly
cheated arrested sued famous viral
""".split())
WEAK_STARTS = ("and ", "so ", "but ", "um", "uh", "like ", "yeah", "because ",
               "or ", "then ", "e ", "mas ", "então ", "tipo ")


def run(cmd):
    subprocess.run(cmd, check=True)


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height:format=duration", "-of", "json", path],
        check=True, capture_output=True, text=True).stdout
    j = json.loads(out)
    s = j["streams"][0]
    return s["width"], s["height"], float(j["format"]["duration"])


# ---------------------------------------------------------------- transcribe

def transcribe(src, cache, model_size, lang):
    if os.path.exists(cache):
        with open(cache) as f:
            return json.load(f)
    from faster_whisper import WhisperModel
    print(f"Transcribing with whisper-{model_size} (first run is slow)...")
    import numpy as np
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    # decode with ffmpeg (faster-whisper's own loader breaks on some PyAV versions)
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], check=True, capture_output=True).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
    segs, info = model.transcribe(audio, word_timestamps=True, language=lang,
                                  vad_filter=True)
    data = {"language": info.language, "segments": []}
    for s in segs:
        words = [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)}
                 for w in (s.words or []) if w.word.strip()]
        if not words:
            continue
        data["segments"].append({"s": words[0]["s"], "e": words[-1]["e"],
                                 "text": s.text.strip(), "words": words})
        print(f"  [{s.start:7.1f}] {s.text.strip()[:90]}")
    with open(cache, "w") as f:
        json.dump(data, f, ensure_ascii=False)
    return data


# ---------------------------------------------------------------- pick clips

def hook_score(text):
    t = text.lower()
    words = re.findall(r"[a-zà-ú']+", t)
    score = 0.0
    if re.search(r"\d|\$|%", t):
        score += 2
    if "?" in t:
        score += 1.5
    score += min(3, sum(w in HOOK_WORDS for w in words))
    if 4 <= len(words) <= 20:
        score += 1
    if t.startswith(WEAK_STARTS):
        score -= 2
    return score


def candidates(segs, lo, hi):
    out = []
    for i in range(len(segs)):
        if segs[i]["text"].lower().startswith(WEAK_STARTS):
            continue
        for j in range(i, len(segs)):
            dur = segs[j]["e"] - segs[i]["s"]
            if dur > hi:
                break
            if dur < lo:
                continue
            chunk = segs[i:j + 1]
            text = " ".join(s["text"] for s in chunk)
            nwords = sum(len(s["words"]) for s in chunk)
            words = re.findall(r"[a-zà-ú']+", text.lower())
            # gaps of silence kill retention
            gaps = sum(max(0, chunk[k + 1]["s"] - chunk[k]["e"]) for k in range(len(chunk) - 1))
            score = (2.0 * hook_score(chunk[0]["text"])
                     + min(4, nwords / dur * 1.3)                 # talking speed
                     + min(4, 0.6 * sum(w in HOOK_WORDS for w in words))
                     + min(2, 0.5 * len(re.findall(r"\d|\$", text)))
                     + (1 if re.search(r"[.!?]$", chunk[-1]["text"]) else -1)
                     - 0.5 * gaps)
            out.append({"s": chunk[0]["s"], "e": chunk[-1]["e"], "score": round(score, 2),
                        "text": text, "first": chunk[0]["text"]})
    return out


def pick(cands, count):
    chosen = []
    for c in sorted(cands, key=lambda c: -c["score"]):
        if all(c["e"] <= p["s"] - 2 or c["s"] >= p["e"] + 2 for p in chosen):
            chosen.append(c)
        if len(chosen) == count:
            break
    return chosen


# ---------------------------------------------------------------- face crop

def crop_plan(src, start, dur, vw, vh):
    """Return an ffmpeg crop filter for 9:16 that follows the face.
    The crop holds still and only jumps (like a camera cut) when the face moves far."""
    cw = int(vh * 9 / 16) // 2 * 2
    if cw >= vw:            # already vertical or narrower
        return None
    centre = (vw - cw) // 2
    try:
        import cv2
    except ImportError:
        print("  (opencv not installed: center crop)")
        return f"crop={cw}:{vh}:{centre}:0"
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(src)
    step = 0.5
    xs = []
    t = 0.0
    while t < dur:
        cap.set(cv2.CAP_PROP_POS_MSEC, (start + t) * 1000)
        ok, frame = cap.read()
        x = None
        if ok:
            small = cv2.resize(frame, (vw // 2, vh // 2))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            faces = casc.detectMultiScale(gray, 1.1, 6, minSize=(vh // 14, vh // 14))
            if len(faces):
                fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                x = (fx + fw / 2) * 2
        xs.append(x)
        t += step
    cap.release()
    found = [x for x in xs if x is not None]
    if not found:
        return f"crop={cw}:{vh}:{centre}:0"
    # fill gaps with the last known position
    last = found[0]
    filled = []
    for x in xs:
        last = x if x is not None else last
        filled.append(last)
    # hold-and-jump: median of runs, jump when the face moves > 20% of crop width
    keys = []          # (time, left)
    cur = None
    for i, x in enumerate(filled):
        window = filled[i:i + 3]
        target = statistics.median(window)
        left = int(min(max(target - cw / 2, 0), vw - cw))
        if cur is None or abs(left - cur) > cw * 0.2:
            cur = left
            keys.append((round(i * step, 2), cur))
    expr = str(keys[-1][1])
    for t0, left in reversed(keys[:-1]):
        nxt = keys[keys.index((t0, left)) + 1][0]
        expr = f"if(lt(t\\,{nxt})\\,{left}\\,{expr})"
    return f"crop={cw}:{vh}:{expr}:0"


# ---------------------------------------------------------------- captions

def ass_time(t):
    t = max(0, t)
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f"{h}:{m:02d}:{t % 60:05.2f}"


def write_ass(words, start, end, path):
    """Groups of up to 3 words, upper case, current word yellow."""
    groups, cur = [], []
    for w in words:
        if w["e"] < start or w["s"] > end:
            continue
        cur.append(w)
        text = " ".join(x["w"] for x in cur)
        if len(cur) == 3 or len(text) > 16 or re.search(r"[.!?,]$", w["w"]):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    lines = []
    for gi, g in enumerate(groups):
        g_end = groups[gi + 1][0]["s"] if gi + 1 < len(groups) else g[-1]["e"] + 0.3
        for wi, w in enumerate(g):
            s = w["s"] - start
            e = (g[wi + 1]["s"] if wi + 1 < len(g) else g_end) - start
            parts = []
            for k, x in enumerate(g):
                word = re.sub(r"[^\w$%'.,!?-]", "", x["w"].upper()).rstrip(".,")
                parts.append(("{\\c&H28D4FF&}" + word + "{\\c&HFFFFFF&}") if k == wi else word)
            lines.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Cap,,0,0,0,,{' '.join(parts)}")
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Anton,112,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,1,0,1,7,3,2,60,60,{int(H * 0.36)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(path, "w") as f:
        f.write(head + "\n".join(lines) + "\n")


def hook_png(text, path):
    """White rounded box with black text, like the 'N3on REVEALS...' headline."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(F_HOOK, 62)
    words, lines, line = text.split(), [], ""
    # balanced lines: split the width evenly instead of filling the first line
    n = max(1, -(-int(d.textlength(text, font=font)) // (W - 220)))
    limit = min(W - 220, d.textlength(text, font=font) / n * 1.25)
    for w in words:
        test = (line + " " + w).strip()
        if d.textlength(test, font=font) > limit and line:
            lines.append(line)
            line = w
        else:
            line = test
    lines.append(line)
    lh = 78
    top = 300
    widths = [d.textlength(l, font=font) for l in lines]
    box_w = max(widths) + 70
    box = ((W - box_w) / 2, top - 22, (W + box_w) / 2, top + lh * len(lines) + 22)
    d.rounded_rectangle(box, radius=26, fill=(255, 255, 255, 245))
    for i, l in enumerate(lines):
        d.text((W / 2, top + i * lh + lh / 2), l, font=font, fill=(0, 0, 0), anchor="mm")
    img.save(path)


# ---------------------------------------------------------------- render

def render(src, words, clip, out, hook, vw, vh):
    start, end = clip["s"] - 0.15, clip["e"] + 0.35
    dur = end - start
    tmp = tempfile.mkdtemp()
    ass = os.path.join(tmp, "cap.ass")
    write_ass(words, start, end, ass)
    crop = crop_plan(src, start, dur, vw, vh)
    vf = (crop + "," if crop else "") + \
        f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
    inputs = ["-ss", f"{start:.2f}", "-t", f"{dur:.2f}", "-i", src]
    if hook:
        png = os.path.join(tmp, "hook.png")
        hook_png(hook, png)
        inputs += ["-i", png]
        fc = f"[0:v]{vf}[b];[b][1:v]overlay=0:0,ass={ass}:fontsdir={FONTS}[v]"
    else:
        fc = f"[0:v]{vf},ass={ass}:fontsdir={FONTS}[v]"
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc,
         "-map", "[v]", "-map", "0:a?", "-r", "30", "-c:v", "libx264", "-crf", "20",
         "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
         "-movflags", "+faststart", out])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("--name", required=True, help="folder name under clips/")
    ap.add_argument("--count", type=int, default=5)
    ap.add_argument("--min", type=float, default=20)
    ap.add_argument("--max", type=float, default=60)
    ap.add_argument("--list", action="store_true", help="only print the best candidates")
    ap.add_argument("--only", type=int, help="render only pick number N")
    ap.add_argument("--at", help="manual cut START:DURATION in seconds")
    ap.add_argument("--hook", help="headline box text (same on every clip unless --only/--at)")
    ap.add_argument("--model", default="small", help="whisper size: tiny, base, small, medium")
    ap.add_argument("--lang", default=None, help="force language, e.g. en, pt")
    a = ap.parse_args()

    outdir = os.path.join(HERE, "clips", a.name)
    os.makedirs(outdir, exist_ok=True)
    vw, vh, _ = probe(a.src)
    data = transcribe(a.src, os.path.join(outdir, "transcript.json"), a.model, a.lang)
    segs = data["segments"]
    words = [w for s in segs for w in s["words"]]

    if a.at:
        s, d = (float(x) for x in a.at.split(":"))
        clips = [{"s": s, "e": s + d, "score": 0,
                  "text": " ".join(w["w"] for w in words if s <= w["s"] < s + d), "first": ""}]
    else:
        clips = pick(candidates(segs, a.min, a.max), a.count)
        clips.sort(key=lambda c: c["s"])
    if not clips:
        raise SystemExit("No stretch of speech fits --min/--max. Try --min 10.")

    for i, c in enumerate(clips, 1):
        print(f"#{i}  {c['s']:.1f}-{c['e']:.1f}s ({c['e'] - c['s']:.0f}s)  score {c['score']}\n    {c['text'][:160]}")
    if a.list:
        return

    report = [f"# Clips from {os.path.basename(a.src)}\n"]
    for i, c in enumerate(clips, 1):
        if a.only and i != a.only:
            continue
        n = a.only or i
        out = os.path.join(outdir, f"clip-{n:02d}.mp4")
        print(f"Rendering {out} ...")
        render(a.src, words, c, out, a.hook, vw, vh)
        report.append(f"## clip-{n:02d}.mp4  ({c['s']:.1f}s to {c['e']:.1f}s, score {c['score']})\n\n"
                      f"First line (use it for the hook/caption): \"{c['first']}\"\n\n{c['text']}\n")
    if not a.only and not a.at:
        with open(os.path.join(outdir, "clips.md"), "w") as f:
            f.write("\n".join(report))
    print("Done:", outdir)


if __name__ == "__main__":
    main()
