"""Turn any post image (4:5, square, etc.) into a 1080x1920 Story without cropping it.

The full artwork sits in the middle with rounded corners and a shadow, on a blurred,
darkened copy of itself that fills the rest of the screen. It stays clear of the
top and bottom areas that Instagram covers with its own buttons.

Usage: python3 make_story.py <in.jpg> <out.jpg>
"""
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

W, H = 1080, 1920
MAX_W, MAX_H = 980, 1500  # leaves room for Instagram's top bar and reply box

src = Image.open(sys.argv[1]).convert("RGB")

bg = src.copy()
scale = max(W / bg.width, H / bg.height)
bg = bg.resize((round(bg.width * scale), round(bg.height * scale)), Image.LANCZOS)
bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(40))).enhance(0.45)

scale = min(MAX_W / src.width, MAX_H / src.height)
art = src.resize((round(src.width * scale), round(src.height * scale)), Image.LANCZOS)
x, y = (W - art.width) // 2, (H - art.height) // 2

radius = 36
mask = Image.new("L", (art.width * 2, art.height * 2), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, art.width * 2, art.height * 2], radius=radius * 2, fill=255)
mask = mask.resize(art.size, Image.LANCZOS)

shadow = Image.new("L", (W, H), 0)
ImageDraw.Draw(shadow).rounded_rectangle([x, y + 18, x + art.width, y + art.height + 18], radius=radius, fill=200)
shadow = shadow.filter(ImageFilter.GaussianBlur(30))
bg = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), bg, shadow)

bg.paste(art, (x, y), mask)
bg.save(sys.argv[2], "JPEG", quality=93)
print("saved", sys.argv[2])
