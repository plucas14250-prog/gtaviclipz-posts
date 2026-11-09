# Playbook: one Instagram post for @gtaviclipz_6

The page is a Brazilian GTA VI fan page. Each scheduled run makes and publishes exactly **one** feed post plus **one** Story. Follow these steps in order.

## 0. What to post in this run

| Slot (US Eastern) | Feed post | Story |
|---|---|---|
| **am** (9:53, ~12h Brasília) | Image post, or a carousel (3 to 5 slides) about every other day | The feed image |
| **pm** (17:53, ~20h Brasília) | **Reel** made with `make_reel.py` | A Story-sized slide from the Reel |

Launch week (2026-11-17 to 2026-11-21): the am slot also posts a Reel instead of an image.

**Pre-approved posts:** if `posts/<today>-<slot>.jpg` (or `.mp4`) and `posts/<today>-<slot>.txt` already exist, the owner already approved them. Publish those as they are (the .txt is the caption) instead of making something new, then do the Story and log as usual.

If `research.md` exists in the repo, read it first and apply what it says works (hooks, formats, caption style, hashtags).

**Reels:** make 3 to 4 vertical slides in Canva (format "Instagram Story", one idea per slide: hook on slide 1, payoff in the middle, "segue pra não perder nada" call to action on the last). Export every page as PNG (`export-design`, type png), download them, then:
```bash
python3 make_reel.py posts/<date>-pm.mp4 slide1.png slide2.png slide3.png
python3 publish.py --reel posts/<date>-pm.mp4 caption.txt
```
Slide 1 must be a strong hook ("PAROU TUDO", "NINGUÉM PERCEBEU ISSO", "VOCÊ TÁ PRONTO?"). If there are tracks in `music/`, `make_reel.py` adds one automatically.

**Reels are NOT auto-published.** The owner adds a trending Instagram song in the phone app, which the API can't do. So for a Reel:
1. Build it with `make_reel.py` and push it to the repo (no music file needed).
2. Do **not** run `publish.py --reel`.
3. Send the owner the video with `SendUserFile` (status "proactive"), and in your message give: the caption ready to copy, and 2 to 3 suggested song vibes that fit (e.g. "funk/phonk agressivo", "synthwave anos 80"). Tell them to pick whatever sound is trending in the Reels audio tab.
4. Still publish the Story automatically (a slide from the Reel).
5. Log it with `"format": "reel-manual"` and `"permalink": "sent to owner"`.

**Carousels:** make a multi-page Canva design (format "Instagram Post (Portrait)"), export each page as JPG, run `fit.py` on each, then `python3 publish.py --carousel caption.txt p1.jpg p2.jpg ...`.

**Stories:** after the feed post is live, publish the Story with `python3 publish.py --story <file>` (a 9:16 slide, or the feed image). Stories have no caption. Push the file before publishing, like any other media.

## 1. Pick the content

1. Read `log.json` to see past posts. Don't repeat a topic or headline from the last 10 posts.
2. Find today's date in US Eastern time.
3. Search the web for what's trending about GTA VI in the last 48 hours (news, viral moments, official Rockstar posts).
4. Choose a format. Rotate so two posts in a row don't use the same one:
   - **countdown**: only before launch (GTA VI launches **2026-11-19**). Days left = launch date minus today.
   - **noticia**: real news from a reliable outlet (IGN, Kotaku, Eurogamer, Insider Gaming, Rockstar Newswire). Use the "RUMOR" label if it's unconfirmed. Never invent news.
   - **enquete**: a question to get comments, e.g. "Lucia ou Jason?" or "Qual carro você vai roubar primeiro?"
   - **curiosidade**: a confirmed fact about the game, Vice City or the series.
   - After launch, swap countdown for tips, "dias desde o lançamento" and player reaction posts.

## 2. Make the image in Canva

1. Use the Canva `create-design` tool, format "Instagram Post (Portrait)". The brief should cover:
   - The exact Portuguese text: a big headline (at most ~8 words), an optional short line under it, and "@gtaviclipz_6" small at the bottom.
   - Style: bold modern gaming news look, neon pink and cyan accents, Miami/Vice City at night or sunset, a dark gradient behind the text so it's readable.
   - No emoji in the image text.
2. **Rockstar's official material may be used as a base** (official trailers, screenshots and artwork from rockstargames.com / Rockstar Newswire). To use one, add it to Canva with `upload-asset-from-url` and pass the asset to the design. When you do, the caption must include "Imagens: Rockstar Games". Never use leaked or datamined material, and never make the post look like an official Rockstar post.
3. Poll `get-create-design-async-job` until it's done, then `export-design` as JPG at width 1080.
4. Download the exported file with curl, then crop it to Instagram size:
   ```bash
   python3 fit.py <downloaded.jpg> posts/<YYYY-MM-DD>-<am|pm>.jpg
   ```
5. Open the image and check it: all text spelled correctly in Portuguese, nothing cut off, readable. If it's bad, generate again (at most 2 more tries).
6. Fallback if Canva fails: `python3 make_post.py card "<KICKER>" "<HEADLINE>" "<SUBTEXT>" posts/<file>.jpg`, or `countdown <days>`.

## 3. Write the caption (in caption.txt, which git ignores)

Follow research.md. Brazilian Portuguese, hype, casual ("mano", "família", "meu consagrado"), emojis like 🔥🤌🏼🌴🚨👀.
- Line 1 is a hook: a number, a detail, or "PAROU TUDO". On posts likely to spread, line 1 can be "Segue @gtaviclipz_6 pra não perder nada de GTA 6 🤝".
- Then 1 to 3 short lines and **exactly one question** at the end ("Qual você escolhe?", "Acertou?").
- Credit the source for news ("Fonte: IGN") and add "Imagens: Rockstar Games" when Rockstar material was used.
- Last line: **2 or 3 hashtags only**: `#GTA6 #GTAVI` plus at most one of `#gta6brasil #vicecity`.

Formats that work best for big GTA 6 pages (see research.md): comparisons ("Qual é o GTA 6 e qual é a vida real?", GTA 5 vs GTA 6), a daily countdown series, and breaking-news carousels with a red "NOTÍCIA" tag and "ARRASTA PRO LADO".

## 4. Publish

1. Commit and push the image to `main` **first**. Instagram downloads it from GitHub.
2. Wait about 10 seconds, then run:

   ```bash
   python3 publish.py posts/<file>.jpg caption.txt
   ```
3. If it fails, try once more. If it fails again, stop and report the error. Don't keep retrying.

## 5. Log it

Append to `log.json`: `{"date", "slot" (am/pm), "format", "headline", "image", "permalink"}`. Then commit and push.

## Rules

- Exactly one post per run. Never publish twice.
- Never repost other creators' clips or images without permission.
- Keep it safe for all ages: no hate, no politics, no misleading claims.
- Don't commit the caption file or anything secret.
