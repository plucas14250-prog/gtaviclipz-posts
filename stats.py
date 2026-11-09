"""Weekly stats for @gtaviclipz_6.

Saves a snapshot to stats.json and prints a report comparing with the previous
snapshot: follower change, and likes/comments for every post from the last 7 days.

Usage: python3 stats.py
"""
import datetime as dt
import json
import os
import urllib.parse
import urllib.request

API = "https://graph.facebook.com/v21.0"
IG_ID = "17841416039005621"


def get(path, **params):
    url = f"{API}/{path}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def main():
    now = dt.datetime.now(dt.timezone.utc)
    profile = get(IG_ID, fields="followers_count,media_count")
    media = get(f"{IG_ID}/media", fields="caption,media_product_type,media_type,timestamp,like_count,comments_count,permalink", limit=50)["data"]

    week = [m for m in media if dt.datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00")) > now - dt.timedelta(days=7)]

    history = json.load(open("stats.json")) if os.path.exists("stats.json") else []
    prev = history[-1] if history else None
    snap = {"date": now.date().isoformat(), "followers": profile["followers_count"], "posts": profile["media_count"]}
    history.append(snap)
    json.dump(history, open("stats.json", "w"), indent=1)

    print(f"Followers: {snap['followers']}", end="")
    if prev:
        print(f" ({snap['followers'] - prev['followers']:+d} since {prev['date']})")
    else:
        print(" (first snapshot)")
    print(f"Posts in the last 7 days: {len(week)}")
    if week:
        tot_l = sum(m.get("like_count", 0) for m in week)
        tot_c = sum(m.get("comments_count", 0) for m in week)
        print(f"Likes: {tot_l} total, {tot_l / len(week):.1f} per post | Comments: {tot_c} total")
        print("\nPosts, best first (likes + 3x comments):")
        for m in sorted(week, key=lambda m: m.get("like_count", 0) + 3 * m.get("comments_count", 0), reverse=True):
            kind = "REEL" if m.get("media_product_type") == "REELS" else m.get("media_type", "")
            cap = (m.get("caption") or "").split("\n")[0][:70]
            print(f"  {m.get('like_count', 0):>4} likes {m.get('comments_count', 0):>3} comments  {kind:<14} {m['timestamp'][:10]}  {cap}  {m['permalink']}")


if __name__ == "__main__":
    main()
