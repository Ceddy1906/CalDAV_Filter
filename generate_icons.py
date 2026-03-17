"""
Generate icon PNGs for the caldav_filter integration.
Run once:  python generate_icons.py
Requires:  pip install Pillow
Output:    icon.png, icon@2x.png, dark_icon.png, dark_icon@2x.png
"""
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("Pillow not found. Install it with:  pip install Pillow")


# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
BLUE_BG       = (25, 118, 210, 255)    # #1976D2
BLUE_DARK_BG  = (13,  71, 161, 255)    # #0D47A1  (header / dark-mode bg)
BLUE_LIGHT    = (227, 242, 253, 255)   # #E3F2FD  (day cells)
ORANGE        = (255, 111,   0, 255)   # #FF6F00  (funnel badge)
WHITE         = (255, 255, 255, 255)
TRANSPARENT   = (0, 0, 0, 0)

# dark-mode variant uses a near-black background
DARK_BG       = (30,  30,  30, 255)


# ---------------------------------------------------------------------------
# Drawing helper
# ---------------------------------------------------------------------------
def draw_icon(size: int, dark: bool) -> Image.Image:
    s = size / 256  # scale factor

    img = Image.new("RGBA", (size, size), TRANSPARENT)
    d = ImageDraw.Draw(img)

    bg = DARK_BG if dark else BLUE_BG

    # ── Outer rounded background ────────────────────────────────────────────
    r_bg = int(48 * s)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r_bg, fill=bg)

    # ── Calendar body (white) ───────────────────────────────────────────────
    cx0, cy0 = int(36 * s), int(64 * s)
    cx1, cy1 = int(220 * s), int(216 * s)
    d.rounded_rectangle([cx0, cy0, cx1, cy1], radius=int(16 * s), fill=WHITE)

    # ── Header bar (dark blue) ──────────────────────────────────────────────
    hx0, hy0 = int(36 * s), int(64 * s)
    hx1, hy1 = int(220 * s), int(116 * s)
    d.rounded_rectangle([hx0, hy0, hx1, hy1], radius=int(16 * s), fill=BLUE_DARK_BG)
    # fill bottom half of header rect so it's truly square at the bottom
    d.rectangle([hx0, int(96 * s), hx1, hy1], fill=BLUE_DARK_BG)

    # ── Binding rings ───────────────────────────────────────────────────────
    for rx in (84, 156):
        rr = int(8 * s)
        rx0, ry0 = int(rx * s) - rr, int(44 * s)
        rx1, ry1 = int(rx * s) + rr, int(80 * s)
        d.rounded_rectangle([rx0, ry0, rx1, ry1], radius=rr, fill=WHITE)

    # ── Day cells (3 × 2 grid) ──────────────────────────────────────────────
    cols = [56, 112, 168]
    rows = [136, 174]
    cell_w, cell_h = int(32 * s), int(28 * s)
    cell_r = int(6 * s)

    for ri, ry in enumerate(rows):
        for ci, cx in enumerate(cols):
            x0, y0 = int(cx * s), int(ry * s)
            x1, y1 = x0 + cell_w, y0 + cell_h
            # highlight one cell in blue
            fill = BLUE_BG if (ri == 0 and ci == 2) else BLUE_LIGHT
            d.rounded_rectangle([x0, y0, x1, y1], radius=cell_r, fill=fill)

    # dot on highlighted cell
    dot_cx = int(184 * s)
    dot_cy = int(150 * s)
    dot_r  = int(8 * s)
    d.ellipse([dot_cx - dot_r, dot_cy - dot_r,
               dot_cx + dot_r, dot_cy + dot_r], fill=WHITE)

    # ── Filter funnel badge (orange circle + white funnel) ──────────────────
    bc  = int(192 * s)          # badge centre x & y
    br  = int(40 * s)           # badge radius
    d.ellipse([bc - br, bc - br, bc + br, bc + br], fill=ORANGE)

    # funnel: trapezoid top + rectangle stem
    fw = int(40 * s)
    fy_top    = int(176 * s)
    fy_mid    = int(192 * s)
    fy_bottom = int(210 * s)
    stem_w    = int(20 * s)
    fx_left   = bc - fw // 2
    fx_right  = bc + fw // 2

    d.polygon(
        [
            (fx_left,              fy_top),
            (fx_right,             fy_top),
            (bc + stem_w // 2,     fy_mid),
            (bc + stem_w // 2,     fy_bottom),
            (bc - stem_w // 2,     fy_bottom),
            (bc - stem_w // 2,     fy_mid),
        ],
        fill=WHITE,
    )

    return img


# ---------------------------------------------------------------------------
# Generate all four variants
# ---------------------------------------------------------------------------
HERE = Path(__file__).parent

variants = [
    ("icon.png",        256, False),
    ("icon@2x.png",     512, False),
    ("dark_icon.png",   256, True),
    ("dark_icon@2x.png", 512, True),
]

for filename, size, dark in variants:
    path = HERE / filename
    draw_icon(size, dark).save(path, "PNG")
    print(f"  created  {path.name}  ({size}×{size})")

print("\nDone. Restart Home Assistant to pick up the new icons.")
