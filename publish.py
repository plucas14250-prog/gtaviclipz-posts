"""Publish an image from this repo to Instagram @gtaviclipz_6.

The access token is added by the session's network proxy, so it never
appears here.

Usage:
  python3 publish.py posts/<file>.jpg caption.txt           # publish
  python3 publish.py posts/<file>.jpg caption.txt --dry-run # check only, no post
"""
import json
import sys
import time
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
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"API error {e.code}: {e.read().decode()}")


def main():
    image, caption_file = sys.argv[1], sys.argv[2]
    dry = "--dry-run" in sys.argv
    caption = open(caption_file, encoding="utf-8").read().strip()
    image_url = RAW + image

    quota = call("GET", f"{IG_ID}/content_publishing_limit", {"fields": "quota_usage,config"})
    print("quota:", quota["data"][0])

    container = call("POST", f"{IG_ID}/media", {"image_url": image_url, "caption": caption})
    cid = container["id"]
    print("container:", cid)

    for _ in range(20):
        status = call("GET", cid, {"fields": "status_code,status"})
        if status.get("status_code") == "FINISHED":
            break
        if status.get("status_code") == "ERROR":
            sys.exit(f"Instagram could not process the image: {status}")
        time.sleep(3)
    else:
        sys.exit("Timed out waiting for Instagram to process the image")

    if dry:
        print("dry run OK: Instagram accepted the image; nothing was published")
        return

    result = call("POST", f"{IG_ID}/media_publish", {"creation_id": cid})
    media = call("GET", result["id"], {"fields": "permalink"})
    print("published:", media.get("permalink"))


if __name__ == "__main__":
    main()
