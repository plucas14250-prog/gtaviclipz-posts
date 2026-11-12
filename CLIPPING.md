# Clipping: getting started

How the clipping side hustle works (from the Zach.sidehustle Reel, 2026-11-12):
pick a campaign that pays per view, cut short clips from that creator's long
videos, post them, submit the links, get paid for the views.

## What pays

- Campaigns live on **Content Rewards** (contentrewards.com, also inside Whop).
- Typical pay: **$1 to $5 per 1,000 approved views**. Music campaigns can pay far less.
- Reality check: Content Rewards' own figure for the median earner is about **$24 total**.
  The money comes from views, so the first weeks are about learning what gets views.

## Owner's setup (only you can do these)

1. Sign up at contentrewards.com. Browse campaigns and pick 1 or 2 with:
   - a creator you'd actually watch (podcasts, streamers, interviews are easiest)
   - a clear rate per 1,000 views and budget left
   - rules you can follow (length, required tags or caption text, allowed platforms)
2. Make a **new** TikTok account for clips (and optionally new Instagram / YouTube Shorts accounts).
   Don't post campaign clips on @gtaviclipz_6: off-topic clips would hurt the GTA page.
   Warm the new account up for 2-3 days first: scroll and like videos in that niche.
3. Download the creator's video (or use the source files the campaign gives you)
   and upload it into the chat. YouTube is blocked in this cloud environment.

## Claude's part: cutting clips

```
python3 clipper.py footage/<video>.mp4 --name <campaign> --count 5
python3 clipper.py footage/<video>.mp4 --name <campaign> --list         # only see the picks
python3 clipper.py footage/<video>.mp4 --name <campaign> --only 2 --hook "HEADLINE TEXT"
```

Clips land in `clips/<campaign>/` (not committed, too big), with `clips.md` listing
each clip's time, transcript and first line. Each clip is 1080x1920, follows the
speaker's face, and has word-by-word captions. `--hook` adds the white headline box.

## Posting and getting paid

1. Post 2-4 clips a day on the clip account(s), following the campaign rules.
2. Submit each post link in the campaign on Content Rewards.
3. Views are counted for several days. Payouts go to your balance once approved.
4. Log each clip (link, campaign, views, payout) so we can see what works.
