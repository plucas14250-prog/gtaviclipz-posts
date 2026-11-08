# Playbook: one Instagram post for @gtaviclipz_6

Each scheduled run makes and publishes exactly **one** post. Follow these steps in order.

## 1. Pick the content

1. Read `log.json` to see past posts. Don't repeat a topic or headline from the last 10 posts.
2. Find today's date in US Eastern time.
3. Choose a format, rotating so two posts in a row don't use the same one:
   - **countdown**: only before launch (GTA VI launches **2026-11-19**). Days left = launch date minus today's date.
   - **noticia**: search the web for GTA VI news from the last 48 hours. Use only facts reported by at least one reliable outlet (IGN, Kotaku, Eurogamer, Insider Gaming, Rockstar Newswire, etc.). If it's only a rumor, say "RUMOR" in the kicker. Never invent news.
   - **enquete**: a question to get comments, like "Qual carro você vai roubar primeiro?" or "Lucia ou Jason?"
   - **curiosidade**: a confirmed fact about the game, Vice City, or the series.
   - After launch, swap countdown for tips, "dias desde o lançamento", and player reaction posts.

## 2. Make the image

```bash
python3 make_post.py countdown <days> posts/<YYYY-MM-DD>-<am|pm>.jpg
python3 make_post.py card "<KICKER>" "<HEADLINE>" "<SUBTEXT>" posts/<YYYY-MM-DD>-<am|pm>.jpg
```

- Text on the image is Brazilian Portuguese, short (headline at most ~12 words), and has **no emoji** because the font can't render them.
- Kicker examples: `NOTÍCIA`, `RUMOR`, `VOCÊ DECIDE`, `VOCÊ SABIA?`, `URGENTE`.
- Open the image and check it: no cut-off text and nothing unreadable. Fix it and regenerate if needed.
- Never use Rockstar's artwork, logos, screenshots or footage.

## 3. Write the caption

Match the page's style: Brazilian Portuguese, hype, casual ("mano", "família", "meu consagrado"), with emojis like 🔥🤌🏼🌴🚨👀. Write 1 to 4 short lines, end with a question or call to comment, then a blank line and 4 to 6 hashtags taken from:
`#gta6 #gtavi #jogosbr #gamerbr #gta6brasil #rockstargames #vicecity #gamingbr`

For news posts, name the source in the caption (e.g. "Fonte: IGN").

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
- Keep it safe for all ages: no hate, no politics, no misleading claims.
- Don't put the caption file or anything secret in the repo.
