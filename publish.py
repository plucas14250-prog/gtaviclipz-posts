"""Publish to Instagram @gtaviclipz_6 from files in this repo.

The access token is added by the session's network proxy, so it never
appears here. Files must be pushed to GitHub (main) before publishing,
because Instagram downloads them from there.

Usage:
  python3 publish.py posts/<file>.jpg caption.txt              # photo post
  python3 publish.py --reel posts/<file>.mp4 caption.txt       # Reel (video)
  python3 publish.py --story posts/<file>.jpg|.mp4             # Story (no caption)
  python3 publish.py --carousel caption.txt img1.jpg img2.jpg  # 2-10 images
Add --dry-run to check that Instagram accepts the media without posting.
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.facebook.com/v21.0"
IG_ID = "17841416039005621"
RAW = "https://raw.githubusercontent.com/plucas14250-prog/gtaviclipz-posts/main/"


def call(method, path, params=None):
    data = urllib.parse.urlencode(params or {}).encode() if method == "POST" else None
    url = f"{API}/{path}"
    if method == "GET" and params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"API error {e.code}: {e.read().decode()}")


def is_video(path):
    return path.lower().endswith((".mp4", ".mov"))


def media_field(path):
    return ("video_url" if is_video(path) else "image_url"), RAW + path


def wait_ready(cid, video):
    # Videos can take a few minutes for Instagram to process.
    for _ in range(100 if video else 20):
        status = call("GET", cid, {"fields": "status_code,status"})
        code = status.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            sys.exit(f"Instagram could not process the media: {status}")
        time.sleep(5 if video else 3)
    sys.exit("Timed out waiting for Instagram to process the media")


def caption_of(path):
    """Read a caption and drop invisible format characters (zero-width spaces, etc.)
    that AI-written text sometimes carries. Emoji and accents are kept."""
    import unicodedata
    text = open(path, encoding="utf-8").read().strip()
    keep = ("\u200d", "\ufe0f")  # needed to build some emoji
    return "".join(c for c in text if unicodedata.category(c) != "Cf" or c in keep)


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry = "--dry-run" in sys.argv

    quota = call("GET", f"{IG_ID}/content_publishing_limit", {"fields": "quota_usage,config"})
    print("quota:", quota["data"][0])

    if args[0] == "--reel":
        media, cap = args[1], args[2]
        params = {"media_type": "REELS", "video_url": RAW + media,
                  "caption": caption_of(cap), "share_to_feed": "true"}
        video = True
    elif args[0] == "--story":
        media = args[1]
        key, url = media_field(media)
        params = {"media_type": "STORIES", key: url}
        video = is_video(media)
    elif args[0] == "--carousel":
        cap, items = args[1], args[2:]
        if not 2 <= len(items) <= 10:
            sys.exit("A carousel needs 2 to 10 items")
        children = []
        for item in items:
            key, url = media_field(item)
            child = {"is_carousel_item": "true", key: url}
            if is_video(item):
                child["media_type"] = "VIDEO"
            c = call("POST", f"{IG_ID}/media", child)["id"]
            wait_ready(c, is_video(item))
            children.append(c)
        params = {"media_type": "CAROUSEL", "children": ",".join(children),
                  "caption": caption_of(cap)}
        video = False
    else:
        media, cap = args[0], args[1]
        params = {"image_url": RAW + media, "caption": caption_of(cap)}
        video = False

    cid = call("POST", f"{IG_ID}/media", params)["id"]
    print("container:", cid)
    wait_ready(cid, video)

    if dry:
        print("dry run OK: Instagram accepted the media; nothing was published")
        return

    result = call("POST", f"{IG_ID}/media_publish", {"creation_id": cid})
    media_info = call("GET", result["id"], {"fields": "permalink"})
    print("published:", media_info.get("permalink") or result["id"])


if __name__ == "__main__":
    main()
