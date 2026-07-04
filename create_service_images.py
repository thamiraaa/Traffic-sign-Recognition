"""
create_service_images.py
Generates professional banking service card images for the kiosk.
Uses Pillow to create clean, colourful, icon-style PNG images.
Run once: python create_service_images.py
"""

import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "signboards")
os.makedirs(OUTPUT_DIR, exist_ok=True)

W, H = 400, 300   # canvas size (pixels)

# ── Helper: create a blank gradient canvas ──────────────────────────────────
def make_canvas(top_hex, bot_hex):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    t = tuple(int(top_hex.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    b = tuple(int(bot_hex.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    for y in range(H):
        ratio = y / H
        r = int(t[0] + (b[0] - t[0]) * ratio)
        g = int(t[1] + (b[1] - t[1]) * ratio)
        bv = int(t[2] + (b[2] - t[2]) * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, bv, 255))
    return img, draw

# ── Helper: draw a large emoji-style glyph centred ─────────────────────────
def draw_icon(draw, emoji_char, cy, size=140, fill=(255, 255, 255, 230)):
    """Draw a text glyph; use Segoe UI Emoji on Windows."""
    font_paths = [
        r"C:\Windows\Fonts\seguiemj.ttf",   # Segoe UI Emoji
        r"C:\Windows\Fonts\seguisym.ttf",   # Segoe UI Symbol
        r"C:\Windows\Fonts\arial.ttf",
    ]
    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, size)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), emoji_char, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (W - tw) // 2 - bbox[0]
    y = cy - th // 2 - bbox[1]
    draw.text((x, y), emoji_char, font=font, fill=fill)

# ── Helper: draw centred label text ────────────────────────────────────────
def draw_label(draw, text, cy, size=28, fill=(255, 255, 255, 255)):
    font_paths = [
        r"C:\Windows\Fonts\calibrib.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, size)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2 - bbox[0]
    y = cy - (bbox[3] - bbox[1]) // 2 - bbox[1]
    # subtle shadow
    draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 80))
    draw.text((x, y), text, font=font, fill=fill)

# ── Helper: rounded-rectangle card ─────────────────────────────────────────
def draw_card(draw, radius=30, fill=(255, 255, 255, 30)):
    x0, y0, x1, y1 = 20, 20, W - 20, H - 20
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=(255, 255, 255, 60), width=2)

# ── Service definitions ─────────────────────────────────────────────────────
SERVICES = [
    # (filename_stem, top_gradient, bot_gradient, emoji, label)
    ("sb_fixed_deposit",    "#1565C0", "#0D47A1", "🏦",  "Fixed Deposit"),
    ("sb_recurring_deposit","#1B5E20", "#2E7D32", "📅",  "Recurring Deposit"),
    ("sb_cheque_deposit",   "#4A148C", "#6A1B9A", "📝",  "Cheque Deposit"),
    ("sb_cheque_book",      "#BF360C", "#D84315", "📒",  "Cheque Book"),
    ("sb_passbook_update",  "#006064", "#00838F", "📘",  "Passbook Update"),
    ("sb_check_balance",    "#E65100", "#F57C00", "💰",  "Check Balance"),
    ("sb_cash_deposit",     "#1A6B3A", "#2E7D32", "💵",  "Cash Deposit"),
    ("sb_cash_withdrawal",  "#B71C1C", "#C62828", "💸",  "Cash Withdrawal"),
    ("sb_demand_draft",     "#283593", "#3949AB", "📄",  "Demand Draft"),
    ("sb_account_opening",  "#004D40", "#00695C", "👤",  "Account Opening"),
    ("sb_kyc_update",       "#37474F", "#455A64", "🔄",  "KYC Update"),
]

for stem, top, bot, emoji, label in SERVICES:
    out_path = os.path.join(OUTPUT_DIR, f"{stem}.png")
    if os.path.exists(out_path):
        print(f"  [OK] Already exists -- skipping {stem}.png")
        continue
    img, draw = make_canvas(top, bot)
    draw_card(draw)
    draw_icon(draw, emoji, cy=H // 2 - 20)
    draw_label(draw, label, cy=H - 45)
    # Save as RGB PNG
    final = img.convert("RGB")
    final.save(out_path, "PNG", optimize=True)
    print(f"  [DONE] Created {stem}.png")

print("\nAll service images ready.")
