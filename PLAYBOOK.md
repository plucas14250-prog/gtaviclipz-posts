# Playbook: one Instagram post for @gtaviclipz_6

The page is a Brazilian GTA VI fan page. Each scheduled run makes and publishes exactly **one** feed post. **No API Stories.** The owner reshares each post to their Story in the app (the API can't share a post to a Story, and separate Story art is not wanted). Follow these steps in order.

## 0. What to post in this run

| Slot (US Eastern) | Feed post |
|---|---|
| **am** (9:53, ~12h Brasília) | **Reel** with `make_clip.py`. A carousel (3 to 5 slides) instead only when there is real news from the last 24 hours. No single-image posts. |
| **pm** (17:53, ~20h Brasília) | **Reel** with `make_clip.py` |

Why (insights from 2026-11-10, see research.md 7.8): a Reel reached about 140 non-followers; an image post reached 10 followers and no one else. Only Reels reach new people at this size.

**Approval flow (owner's request):** each post is prepared about 1 hour early by a separate "prepare" run (owner is 2 hours behind Brasília, US Eastern; give times in both), saved as `posts/<date>-<slot>-preview.*` (image `.jpg`, carousel `-preview-1.jpg`…, or Reel `.mp4`) plus `posts/<date>-<slot>-preview.txt` (caption), and sent to the owner with SendUserFile and a PushNotification asking for approval.
- When the owner approves in the chat ("ok", "aprovado", picks an option), rename the preview files to the approved names (`posts/<date>-<slot>.jpg` / `.mp4` / `-1.jpg`… and `.txt`), commit and push. If they ask for changes, make them, send again, and wait.
- At post time: if approved files exist, publish/send those. **If only the preview exists (no answer in time), use the preview as is** (the owner agreed to this fallback) and say so in the summary.
- If there's no preview at all (the prepare run failed), make the post as usual.

**Pre-approved posts:** if `posts/<today>-<slot>.jpg` (or `.mp4`, or a carousel `posts/<today>-<slot>-1.jpg`, `-2.jpg`, ...) and `posts/<today>-<slot>.txt` already exist, the owner already approved them. Publish those as they are (the .txt is the caption) instead of making something new, then send the Story reshare reminder and log as usual.

If `research.md` exists in the repo, read it first and apply what it says works (hooks, formats, caption style, hashtags).

**Reels:** see the Reel rules below (real footage only, no slides, no zoom).
The Reel headline must be a strong hook ("NINGUÉM PERCEBEU ISSO", "EU DIA 19 ÀS 00:01", "VOCÊ TÁ PRONTO?").

**What the insights say so far (updated 2026-11-11):**
- Best Reel: the meme "Eu ligando pro chefe dia 19" (11/11 am): ~170 views in 9h (typical ~110 in 12h), 82% non-followers, **share rate 3.1%** (4 sends), skip rate 45.8% (better than usual, still above the 40% target).
- The audience is mostly **25-34 (46-58%)**, then 18-24. Jokes about adult life (trabalho, chefe, boletos, faltar no trabalho, "minha mulher/namorada", sono) and nostalgia (GTA San Andreas, Vice City 2002, GTA V 2013) fit this audience. Prefer memes in this style, with a send ask.
- About 64% of views come from the Reels tab, so the first second decides everything.

**The first second decides the Reel (always):**
- Instagram ranks skip rate first for reach. Our 2026-11-09 Reel opened on an empty boat under a black header and 47.8% of viewers swiped away.
- **No black header band.** Never use `--header` (the old black band with the avatar). Gameplay and trailer footage fill the whole 1080x1920 frame with the headline over it; screen recordings use `--fit` (see the Reel rules below).
- **Frame 0 must show a face or something moving.** A shot from the shot map can start a moment before the person appears, so move the cut start forward until frame 0 has the subject. Extract frame 0 of the finished file and look at it before sending.
- The headline must be readable on frame 0 and make sense without the caption.

**Every Reel must have something of ours in it (always):** Instagram replaces near-identical copies of a clip with the original in recommendations, and a headline, speed change or credit does not count as an edit. A bare montage of trailer shots is not allowed. Pick one of these, in this order of preference:
1. **Owner's own footage** in `footage/` (screen recordings, console, gameplay from 2026-11-19 on). Use `--credit ""`.
2. **Detail breakdown:** one or two trailer shots, slowed or held on the detail, with our own explanation as headline + second line ("NINGUÉM PERCEBEU ISSO" / what to look at).
3. **Meme:** one trailer shot as the reaction, with a first-person situation as the headline ("EU CHEGANDO NO TRABALHO DIA 20 SEM DORMIR").
4. **Owner's voice:** if the owner sent a voice note, lay it over the clip.
If none of these is possible today, ask the owner for a recording instead of posting a montage.

**Reel rules from the owner (always):**
- **No slideshows.** Never build a Reel from still slides or images (`make_reel.py` is retired). Reels are real moving footage only: trailer clips, the owner's own recordings, gameplay.
- **No zoom.** Never use `--zoom` (default is off). Framing is a static crop.
- **No repeated shots on the same day (owner's rule).** Before building a Reel, read today's `log.json` entries (their `source` field) and don't use any shot that already went out today. Avoid repeating a shot within 3 days when possible. Always log every cut start in `source`.
- **No slow motion.** Never play trailer footage below normal speed (`--slow` or a cut speed under 1.0): the source has no extra frames, so it stutters. Speed-ups (over 1.0) are fine for boring stretches.
- Edit like a real video: keep continuous stretches that have movement (screens changing, a countdown ticking, characters moving), cut dead parts, and fast-forward boring stretches with the per-cut speed (`start:dur:x:speed`, e.g. 1.8). Reframe the same moment with a second cut only when the subject moves out of frame.
- **Screen recordings (PS5, store, phone): always use `--fit`** so the whole screen is visible, centered on a blurred copy of itself, with the headline over the blurred part above it (owner's choice, 2026-11-10). Never crop a screen recording down to part of the screen. Remove the recording's own black borders first with `--srccrop` (find them with `ffmpeg -i <file> -t 30 -vf cropdetect=24:2:0 -f null -`; for `footage/buying-gta6.mp4` it is `1904:1080:14:124`).

**Reels from real footage (required):** if `footage/` has trailers, make Reels from them.
1. Use the shot map `footage/<trailer>-shots.json`. Use **1 to 3 "characters" shots** (Jason, Lucia, faces, action) that serve the breakdown or the meme. Never a clip with only cars, buildings or empty streets.
2. Order: open on the strongest face shot. Total 5 to 9 seconds.
3. Check `log.json` and don't repeat the same opening shot within 7 days (log `"source": "<file> cuts <starts>"`).
4. `python3 make_clip.py footage/<file>.mp4 --cuts "start:dur:x,start:dur:x,..." --top "<hook>" --line2 "<detail>" --out posts/<date>-<slot>.mp4`
   Layout: footage fills the whole screen; centered headline in Anton with a black outline (max ~8 words) and a yellow second line in Oswald sit over the picture, below Instagram's top buttons. Full screen keeps only about a third of the trailer's width, so set each cut's x on the subject. Letterbox bars and emoji are removed automatically. Put emoji in the caption, not on screen.
5. Open frame 0 and 4 to 6 more frames of the result. Frame 0 must show the subject; every shot shows a person; the text fits and doesn't cover the face.
6. Caption must include "Imagens: Rockstar Games" when Rockstar footage is used.
7. Never use `--bottom` unless someone in the clip is talking.
8. If a trailer has no shot map yet, make one first with `scenes.py` (look at every shot, list the ones with people and the subject's x position).

**Reels are NOT auto-published.** The owner adds a trending Instagram song in the phone app, which the API can't do. So for a Reel:
1. Build it with `make_clip.py` (real footage, no zoom) and push it to the repo (no music file needed).
2. Do **not** run `publish.py --reel`.
3. Send the owner the video with `SendUserFile` (status "proactive"), and in your message give: the caption ready to copy, and 2 to 3 suggested song vibes that fit (e.g. "funk/phonk agressivo", "synthwave anos 80"). Tell them to pick whatever sound is trending in the Reels audio tab.
4. Remind the owner to turn on "Compartilhar no story" when posting the Reel.
6. **Send a push notification** with the `PushNotification` tool (status "proactive") right after sending the video, e.g. "Hora de postar o Reel 🎬 Vídeo e legenda prontos no chat. Põe uma música em alta e posta!" The owner asked to be alerted when it's time to post.
5. Log it with `"format": "reel-manual"` and `"permalink": "sent to owner"`.
7. **Ask for yesterday's numbers.** The API can't read insights, so in the same message ask the owner for a screenshot of the previous Reel's insights ("What impacts your views" and "Top sources of views"). When they send it, add `"insights": {"views", "viewers", "skip_rate", "share_rate", "nonfollower_pct"}` to that Reel's entry in `log.json`. Before choosing today's Reel, read the logged insights and repeat the type with the lowest skip rate. Working target: skip rate under 40%, then share rate above 1%.

**Carousels:** make a multi-page Canva design (format "Instagram Post (Portrait)"), export each page as JPG, run `fit.py` on each, then `python3 publish.py --carousel caption.txt p1.jpg p2.jpg ...`.

**Stories:** do NOT publish Stories with `publish.py --story`. After the feed post is live, send the owner (SendUserFile is not needed, a message is enough) the post link and this reminder: "Compartilha no story: abre o post → ✈️ → Adicionar ao story". For Reels, remind them to tap "Compartilhar também no story" when they post.

## 1. Pick the content

1. Read `log.json` to see past posts. Don't repeat a topic or headline from the last 10 posts.
2. **All dates and times are in Brasília time (America/Sao_Paulo, UTC−3, no daylight saving).** The audience is in Brazil. Get today's date with `TZ=America/Sao_Paulo date`. Countdowns ("FALTAM N DIAS") = 2026-11-19 minus today's Brasília date. Convert every time in news to Brasília before writing it (e.g. 00:00 GMT = 21:00 Brasília the day before), and say "hoje/amanhã" only if it's true in Brasília at the moment the post goes out (am ≈ 11:53, pm ≈ 19:53 Brasília). If a time can't be converted with certainty, leave the time out.
3. Search the web for what's trending about GTA VI in the last 48 hours (news, viral moments, official Rockstar posts).
4. Choose a format. Rotate so two posts in a row don't use the same one:
   - **countdown**: only before launch (GTA VI launches **2026-11-19**). Days left = launch date minus today.
   - **noticia**: real news from a reliable outlet (IGN, Kotaku, Eurogamer, Insider Gaming, Rockstar Newswire). Use the "RUMOR" label if it's unconfirmed. Never invent news.
   - **enquete**: a question to get comments, e.g. "Lucia ou Jason?" or "Qual carro você vai roubar primeiro?"
   - **curiosidade**: a confirmed fact about the game, Vice City or the series.
   - After launch, swap countdown for tips, "dias desde o lançamento" and player reaction posts.

## 2. Make the image in Canva

**Canva AI credits:** `create-design` uses AI credits, and they can run out (it fails with "quota_exceeded"). When that happens, don't stop: **copy one of these template designs with `copy-design`, then change the text with `read-design` (open_transaction) + `edit-design` (replace_text, resize/format if the text wraps), commit, and export.** Editing and copying don't use AI credits. Check every page's thumbnail for wrapped or overlapping text before committing.

| Template | Design ID | Use for |
|---|---|---|
| 6-slide carousel (cover + 5 numbered slides) | DAHaYlaqb0w | Carousels |
| 4 vertical slides (hook, 2 lists, call to action) | DAHaXjj1jro | Not for Reels (no slideshows) |
| 3 vertical slides | DAHaXrOksi0 | Not for Reels (no slideshows) |
| Single portrait post (big headline at bottom) | DAHaYQC5TdY | Image posts |
| Single portrait post (headline + date) | DAHaXYRb8gw | Image posts |


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

### Caption structure (from the instagram-agent skills)

- **Only the first ~125 characters show** before "… mais". Write them for that.
  - **Reels:** the video is already the hook, so line 1 is the context plus the ask ("Comenta aí qual você escolhe 👇"). Don't repeat the on-screen headline.
  - **Images and carousels:** line 1 is the hook. Concrete, short, ends on a cliff, never a greeting, never starting with an emoji or hashtag.
- **Search phrases:** put 1 or 2 phrases Brazilians actually type into the text naturally, e.g. "pré-download do GTA 6", "data de lançamento do GTA 6", "mapa do GTA 6", "trailer do GTA 6". Instagram search reads caption text; hashtags are just labels now.
- **Hashtags:** 2 or 3 (Instagram allows at most 5 since Dec 2025). Never #viral, #fyp, #explorepage.
- **One ask per post:** comment, save, or share. Pick one. On memes and relatable Reels make it a send ("manda pra quem vai jogar com você"); keep the comment question for polls and choices.
- **Hooks:** for headlines, vary the formula using `.claude/skills/ig-reel/hooks.json` (26 formulas), adapted to Portuguese and GTA, e.g. "Ninguém te conta que…", "GTA 5 vs GTA 6: um deles não chega nem perto", "X coisas sobre Y. A número 4 ninguém percebeu", "Isso muda dia 19. Faça X antes". Don't use the same formula twice in a row.

### Humanizer pass (required, every caption)

Before publishing, run the caption through the `humanizer` skill (in `.claude/skills/humanizer`) in embedded mode: return only the final caption. Rules for this page:
- **Keep the page's voice:** Brazilian Portuguese, casual slang ("mano", "família", "PAROU TUDO"), the emojis, the ALL-CAPS hook on line 1, the question at the end, the source credit and the hashtags. Those are the style, not AI tells.
- **Remove:** "não é só X, é Y" / "não é X, mas Y" contrasts, dramatic one-line closers that repeat the point, em dashes (—) and en dashes (–), forced lists of three, hype words with no fact behind them ("épico", "revolucionário", "incrível" stacked together), staged openers ("Bora falar sobre…", "Se liga nisso:" when it adds nothing), and chatbot phrases.
- **Never add or change facts, numbers, dates or times.** The Brasília time rule still applies.
- Keep it short: 1 to 4 lines plus hashtags.

Also apply the same pass to the on-screen text (headline and second line) of Reels and carousels.

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
