"""Resize and crop any image to Instagram portrait size (1080x1350), keeping the center.

Usage: python3 fit.py <in> <out.jpg>
"""
import sys

from PIL import Image

W, H = 1080, 1350

im = Image.open(sys.argv[1]).convert("RGB")
scale = max(W / im.width, H / im.height)
im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
left = (im.width - W) // 2
top = (im.height - H) // 2
im.crop((left, top, left + W, top + H)).save(sys.argv[2], "JPEG", quality=93)
print("saved", sys.argv[2])
