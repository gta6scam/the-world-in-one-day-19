#!/usr/bin/env python3
"""THE WORLD IN ONE DAY — Thursday 19 November 2026.

Draws a complete newspaper front page (1024x1024 PNG) summing up one day of
world news. Every illustration is a flat vector-style drawing made from PIL
primitives; no external images are used. Output is deterministic.
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "entry.png")
FONTS = os.path.join(HERE, "fonts")

W = 1024
M = 24                      # page margin
CW = W - 2 * M              # content width = 976

PAPER = (246, 240, 226)
INK = (20, 33, 61)          # navy
RED = (179, 32, 44)
BLACK = (26, 26, 26)
GREY = (92, 92, 92)
RULE = (20, 33, 61)
PANEL_LINE = (178, 168, 148)

_font_cache = {}


def F(kind, size):
    """kind: 'serif', 'serifb', 'sans', 'sansb'."""
    key = (kind, size)
    if key not in _font_cache:
        name = {
            "serif": "DejaVuSerif.ttf",
            "serifb": "DejaVuSerif-Bold.ttf",
            "sans": "DejaVuSans.ttf",
            "sansb": "DejaVuSans-Bold.ttf",
        }[kind]
        _font_cache[key] = ImageFont.truetype(os.path.join(FONTS, name), size)
    return _font_cache[key]


def tw(d, s, font):
    return d.textlength(s, font=font)


def wrap(d, s, font, maxw):
    """Greedy word wrap; returns list of lines that each fit maxw."""
    words = s.split()
    lines, cur = [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if tw(d, t, font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def fit_font(d, s, kind, start, maxw, min_size=10):
    """Largest font (<= start) whose single line fits maxw."""
    size = start
    while size > min_size and tw(d, s, F(kind, size)) > maxw:
        size -= 1
    return F(kind, size)


def italic_line(base, d, cx, y, s, font, fill):
    """Draw one line of fake-italic text (shear transform) centred at cx."""
    w_ = int(tw(d, s, font)) + 30
    h_ = font.size + 18
    layer = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.text((12, 6), s, font=font, fill=fill + (255,))
    s_coef = 0.22
    layer = layer.transform(
        (w_ + int(h_ * s_coef) + 4, h_),
        Image.AFFINE,
        (1, s_coef, -s_coef * h_, 0, 1, 0),
    )
    base.paste(layer, (int(cx - layer.width / 2), int(y)), layer)


def chip(d, x, y, text, fill, font_size=9, txt=(255, 255, 255)):
    f = F("sansb", font_size)
    w_ = int(tw(d, text, f)) + 10
    d.rectangle([x, y, x + w_, y + font_size + 7], fill=fill)
    d.text((x + 5, y + 3), text, font=f, fill=txt)
    return w_


# ----------------------------------------------------------------------------
# Page furniture
# ----------------------------------------------------------------------------

def header(d, img):
    f = F("sansb", 16)
    d.text((M, 13), "THE WORLD IN ONE DAY", font=f, fill=INK)
    r = "ONE PAGE · 36 STORIES · EVERY CONTINENT"
    fr = F("sansb", 12)
    d.text((W - M - tw(d, r, fr), 16), r, font=fr, fill=RED)
    d.line([M, 40, W - M, 40], fill=RULE, width=3)
    d.line([M, 45, W - M, 45], fill=RULE, width=1)

    # Giant date headline
    title = "Thursday 19 November 2026"
    f = fit_font(d, title, "serifb", 63, CW)
    d.text(((W - tw(d, title, f)) / 2, 52), title, font=f, fill=INK)

    # Red italic strap
    strap = ("Trump, Xi and Putin share one table • The World Court finds "
             "genocide in Myanmar • COP31's draft drops fossil fuels")
    f = fit_font(d, strap, "serif", 18, CW)
    italic_line(img, d, W / 2, 122, strap, f, RED)
    d.line([M, 150, W - M, 150], fill=RULE, width=1)


def stat_strip(d):
    stats = [
        ("3", "presidents at one table in Shenzhen"),
        ("9–6", "World Court genocide vote on Myanmar"),
        ("$81.3bn", "Anthropic's record IPO raise"),
        ("109–0", "Danish vote on the Arctic pact"),
        ("48–51", "Senate rejects Iran war curb"),
        ("4.9%", "Australia's jobless rate, 2024 high"),
    ]
    x0, y0, h = M, 156, 46
    colw = CW / 6.0
    fn = F("serifb", 25)
    fc = F("sans", 10)
    for i, (num, cap) in enumerate(stats):
        cx = x0 + i * colw
        wnum = tw(d, num, fn)
        d.text((cx + (colw - wnum) / 2, y0), num, font=fn,
               fill=RED if i in (1, 4) else INK)
        for j, line in enumerate(wrap(d, cap, fc, colw - 10)[:2]):
            wl = tw(d, line, fc)
            d.text((cx + (colw - wl) / 2, y0 + 28 + j * 11), line,
                   font=fc, fill=GREY)
        if i:
            d.line([cx, y0 + 2, cx, y0 + h - 2], fill=PANEL_LINE, width=1)
    d.line([M, 208, W - M, 208], fill=RULE, width=1)


def region_chips(d):
    chips = ["ASIA 7", "EUROPE 9", "MIDDLE EAST 3", "AFRICA 6",
             "AMERICAS 4", "OCEANIA 5", "GLOBAL 2"]
    x, y = M, 215
    for c in chips:
        x += chip(d, x, y, c, INK, font_size=11) + 7
    note = "ALL STORIES: THU 19 NOV 2026, ANY TIME ZONE"
    fn = F("sans", 10)
    d.text((W - M - tw(d, note, fn), y + 4), note, font=fn, fill=GREY)


# ----------------------------------------------------------------------------
# Card illustrations — flat shapes drawn with PIL primitives.
# Each takes (d, x, y, w, h) for its panel and draws inside it.
# ----------------------------------------------------------------------------

def ill_summit(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(24, 38, 66))
    # flags: US (blue canton + stripes), China (red), Russia (3 stripes)
    fy = y + 5
    d.rectangle([x + 14, fy, x + 44, fy + 18], fill=(178, 34, 52))
    d.rectangle([x + 14, fy, x + 26, fy + 9], fill=(60, 59, 110))
    for i in range(3):
        d.rectangle([x + 14, fy + 3 + i * 5, x + 44, fy + 5 + i * 5],
                    fill=(240, 240, 240))
    d.rectangle([x + w - 76, fy, x + w - 46, fy + 18], fill=(222, 41, 57))
    d.ellipse([x + w - 72, fy + 3, x + w - 68, fy + 7], fill=(255, 222, 0))
    d.rectangle([x + w - 44, fy, x + w - 14, fy + 18], fill=(240, 240, 240))
    d.rectangle([x + w - 44, fy + 6, x + w - 14, fy + 12], fill=(0, 57, 166))
    d.rectangle([x + w - 44, fy + 12, x + w - 14, fy + 18], fill=(213, 0, 50))
    # table + three heads
    ty = y + h - 15
    d.rectangle([x + w / 2 - 52, ty, x + w / 2 + 52, ty + 6], fill=(150, 110, 70))
    for i, dx in enumerate((-34, 0, 34)):
        cx = x + w / 2 + dx
        d.ellipse([cx - 8, ty - 17, cx + 8, ty - 1],
                  fill=(232, 190, 150), outline=(10, 10, 10))
        d.rectangle([cx - 10, ty - 2, cx + 10, ty + 1], fill=(40, 40, 60))


def ill_court(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(216, 226, 236))
    cx = x + w / 2
    # Peace Palace: roof + columns
    d.polygon([(cx - 46, y + 14), (cx + 46, y + 14), (cx, y + 3)], fill=INK)
    d.rectangle([cx - 46, y + 15, cx + 46, y + 18], fill=INK)
    for i in range(5):
        lx = cx - 40 + i * 20
        d.rectangle([lx, y + 19, lx + 5, y + h - 12], fill=(90, 110, 140))
    d.rectangle([cx - 48, y + h - 11, cx + 48, y + h - 7], fill=INK)
    # scales of justice on the right
    sx = x + w - 34
    d.line([sx, y + 8, sx, y + h - 10], fill=RED, width=2)
    d.line([sx - 13, y + 12, sx + 13, y + 12], fill=RED, width=2)
    for sgn in (-1, 1):
        px = sx + sgn * 13
        d.line([px, y + 12, px - 5, y + 22], fill=RED, width=1)
        d.line([px, y + 12, px + 5, y + 22], fill=RED, width=1)
        d.arc([px - 7, y + 18, px + 7, y + 27], 0, 180, fill=RED, width=2)


def ill_cop(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(250, 243, 222))
    # globe (small, high in the panel so the label chip stays clear of it)
    gx, gy, r = x + 24, y + 13, 10
    d.ellipse([gx - r, gy - r, gx + r, gy + r], fill=(110, 170, 220),
              outline=INK)
    d.arc([gx - r, gy - r, gx + r, gy + r], 90, 270, fill=INK)
    d.line([gx - r, gy, gx + r, gy], fill=INK, width=1)
    # struck-through words
    f = F("sansb", 12)
    s = "FOSSIL FUELS"
    d.text((x + 52, y + h / 2 - 8), s, font=f, fill=INK)
    d.line([x + 50, y + h / 2 + 0, x + 56 + tw(d, s, f), y + h / 2 - 4],
           fill=RED, width=3)
    # thermometer at the right edge
    tx = x + w - 24
    d.rectangle([tx, y + 3, tx + 6, y + h - 11], outline=INK, fill=(255, 255, 255))
    d.rectangle([tx + 2, y + h - 18, tx + 4, y + h - 11], fill=RED)
    d.ellipse([tx - 2, y + h - 12, tx + 8, y + h - 2], fill=RED, outline=INK)


def ill_ipo(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(18, 30, 34))
    pts = [(x + 10, y + h - 8), (x + 40, y + h - 14), (x + 66, y + h - 12),
           (x + 96, y + h - 24), (x + 128, y + h - 20), (x + 160, y + 8)]
    d.line(pts, fill=(64, 200, 120), width=3)
    for px, py in pts:
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(64, 200, 120))
    d.polygon([(pts[-1][0], pts[-1][1]), (pts[-1][0] - 10, pts[-1][1] + 1),
               (pts[-1][0] - 1, pts[-1][1] + 9)], fill=(64, 200, 120))
    f = F("serifb", 17)
    d.text((x + w - 62, y + 6), "+17%", font=f, fill=(64, 200, 120))


def ill_gta(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(38, 22, 58))
    cx, cy = x + w / 2, y + h / 2
    # gamepad body
    d.rounded_rectangle([cx - 46, cy - 14, cx + 46, cy + 14], 12,
                        fill=(16, 16, 22), outline=(200, 170, 255))
    d.line([cx - 32, cy - 5, cx - 32, cy + 5], fill=(200, 200, 200), width=3)
    d.line([cx - 37, cy, cx - 27, cy], fill=(200, 200, 200), width=3)
    for i, c in enumerate([(255, 90, 90), (90, 200, 255), (255, 210, 90),
                           (120, 230, 120)]):
        bx = cx + 22 + (i % 2) * 11
        by = cy - 6 + (i // 2) * 11
        d.ellipse([bx, by, bx + 7, by + 7], fill=c)
    f = F("serifb", 20)
    s = "VI"
    d.text((x + 10, y + 5), s, font=f, fill=(255, 190, 80))


def ill_cyclone(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(196, 220, 235))
    # coast
    d.polygon([(x + w - 52, y), (x + w, y), (x + w, y + h),
               (x + w - 30, y + h), (x + w - 44, y + h / 2)],
              fill=(214, 198, 150))
    cx, cy = x + w / 2 - 12, y + h / 2
    for r in (16, 11, 6):
        d.arc([cx - r, cy - r, cx + r, cy + r], 300, 210, fill=INK, width=2)
        d.arc([cx - r, cy - r, cx + r, cy + r], 120, 30, fill=INK, width=2)
    d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=RED)
    f = F("sansb", 9)
    d.text((x + w - 46, y + h - 13), "INDIA", font=f, fill=(120, 100, 60))


def ill_riyadh(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(30, 34, 58))
    base = y + h
    for i, (bw, bh) in enumerate([(16, 16), (13, 22), (20, 30), (12, 14),
                                  (15, 20)]):
        bx = x + 8 + i * 26
        d.rectangle([bx, base - bh, bx + bw, base], fill=(12, 14, 26))
        d.point((bx + 4, base - bh + 5), fill=(255, 220, 120))
    # PIF tower (tallest)
    tx = x + w - 34
    d.rectangle([tx, y + 8, tx + 12, base], fill=(16, 18, 34))
    # missile arc + debris burst
    d.arc([x + 20, y - 6, x + w - 6, y + 34], 200, 330, fill=(255, 120, 90),
          width=2)
    bx, by = tx + 2, y + 12
    for dx, dy in ((-6, 4), (0, 8), (7, 5), (-3, -4), (5, -3)):
        d.line([bx, by, bx + dx, by + dy], fill=(255, 190, 90), width=2)


def ill_hormuz(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(170, 205, 225))
    base = y + h - 8
    d.line([x, base + 4, x + w, base + 4], fill=(70, 130, 180), width=3)
    # supertanker
    hx = x + w / 2 - 48
    d.polygon([(hx, base - 10), (hx + 96, base - 10), (hx + 84, base),
               (hx + 10, base)], fill=(40, 40, 46))
    d.rectangle([hx + 8, base - 17, hx + 74, base - 10], fill=RED)
    d.rectangle([hx + 78, base - 20, hx + 88, base - 10], fill=(230, 230, 230))
    # mine + flame
    mx, my = hx + 108, base - 4
    d.ellipse([mx - 5, my - 5, mx + 5, my + 5], fill=(30, 30, 30))
    for dx, dy in ((-7, -3), (7, -3), (0, -8), (-5, 5), (5, 5)):
        d.line([mx, my, mx + dx, my + dy], fill=(30, 30, 30), width=1)
    d.polygon([(hx + 84, base - 20), (hx + 90, base - 30), (hx + 95, base - 20)],
              fill=(255, 140, 40))


def ill_seoul(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(240, 240, 238))
    # Korean flag: white field, red/blue disc
    fx, fy = x + 12, y + 6
    d.rectangle([fx, fy, fx + 52, fy + h - 12], fill=(255, 255, 255),
                outline=(150, 150, 150))
    cx, cy, r = fx + 26, fy + (h - 12) / 2, 9
    d.pieslice([cx - r, cy - r, cx + r, cy + r], 0, 180, fill=(205, 46, 58))
    d.pieslice([cx - r, cy - r, cx + r, cy + r], 180, 360, fill=(0, 71, 160))
    # stamp
    sx, sy = x + 84, y + h / 2 - 10
    f = F("sansb", 12)
    s = "OVERTURNED"
    sw = tw(d, s, f) + 10
    d.rectangle([sx, sy, sx + sw, sy + 19], outline=RED, width=2)
    d.text((sx + 5, sy + 3), s, font=f, fill=RED)


def ill_arctic(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(205, 228, 240))
    # ice
    d.polygon([(x, y + h - 8), (x + 40, y + h - 14), (x + 90, y + h - 9),
               (x + w, y + h - 13), (x + w, y + h), (x, y + h)],
              fill=(245, 250, 252))
    # Denmark flag
    fx, fy = x + 16, y + 6
    d.rectangle([fx, fy, fx + 34, fy + 22], fill=(200, 30, 45))
    d.rectangle([fx + 10, fy, fx + 14, fy + 22], fill=(255, 255, 255))
    d.rectangle([fx, fy + 9, fx + 34, fy + 13], fill=(255, 255, 255))
    d.line([fx, fy + 22, fx, y + h - 10], fill=INK, width=2)
    # US flag simplified
    ux, uy = x + 62, y + 6
    d.rectangle([ux, uy, ux + 34, uy + 22], fill=(178, 34, 52))
    for i in range(3):
        d.rectangle([ux, uy + 4 + i * 6, ux + 34, uy + 7 + i * 6],
                    fill=(240, 240, 240))
    d.rectangle([ux, uy, ux + 15, uy + 11], fill=(60, 59, 110))
    d.line([ux, uy + 22, ux, y + h - 10], fill=INK, width=2)


def ill_jobs(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(250, 246, 235))
    pts = [(x + 10, y + 10), (x + 38, y + 13), (x + 64, y + 18),
           (x + 92, y + 26), (x + 118, y + h - 8)]
    d.line(pts, fill=RED, width=3)
    d.polygon([(pts[-1][0], pts[-1][1]), (pts[-1][0] - 9, pts[-1][1] - 2),
               (pts[-1][0] - 2, pts[-1][1] - 9)], fill=RED)
    f = F("serifb", 18)
    d.text((x + w - 62, y + 5), "4.9%", font=f, fill=RED)


def ill_somalia(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(235, 240, 245))
    # Somalia flag (light blue, white star)
    fx, fy = x + 12, y + 7
    d.rectangle([fx, fy, fx + 44, fy + h - 14], fill=(65, 137, 203))
    cx, cy = fx + 22, fy + (h - 14) / 2
    d.polygon([(cx, cy - 7), (cx + 2, cy - 2), (cx + 7, cy - 2), (cx + 3, cy + 1),
               (cx + 4, cy + 6), (cx, cy + 3), (cx - 4, cy + 6), (cx - 3, cy + 1),
               (cx - 7, cy - 2), (cx - 2, cy - 2)], fill=(255, 255, 255))
    # UAE flag
    ux, uy = x + 66, y + 7
    d.rectangle([ux, uy, ux + 44, uy + (h - 14) / 3], fill=(0, 122, 61))
    d.rectangle([ux, uy + (h - 14) / 3, ux + 44, uy + 2 * (h - 14) / 3],
                fill=(255, 255, 255))
    d.rectangle([ux, uy + 2 * (h - 14) / 3, ux + 44, uy + h - 14],
                fill=(20, 20, 20))
    d.rectangle([ux, uy, ux + 12, uy + h - 14], fill=(200, 16, 46))
    # broken link between them
    d.line([fx + 46, cy, ux - 2, cy], fill=RED, width=2)
    d.line([fx + 52, cy - 4, fx + 58, cy + 4], fill=RED, width=2)
    d.line([fx + 52, cy + 4, fx + 58, cy - 4], fill=RED, width=2)


def ill_runner(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(240, 232, 210))
    d.line([x, y + h - 4, x + w, y + h - 4], fill=(170, 140, 90), width=2)
    # runner silhouette mid-stride, scaled to the panel and kept right of
    # the label chip; coordinates are a 40px-tall design scaled by s
    s = h / 40.0
    ox = x + w - 104

    def P(px, py):
        return (ox + px * s, y + py * s)

    hx, hy = P(58, 10)
    r = max(3, int(5 * s))
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=INK)
    lw = max(2, int(4 * s))
    d.line([P(58, 15), P(66, 21)], fill=INK, width=lw)        # torso
    d.line([P(66, 21), P(78, 27)], fill=INK, width=lw)        # front leg
    d.line([P(78, 27), P(77, 36)], fill=INK, width=lw)
    d.line([P(66, 21), P(54, 29)], fill=INK, width=lw)        # back leg
    d.line([P(54, 29), P(61, 35)], fill=INK, width=lw)
    d.line([P(60, 13), P(72, 18)], fill=INK, width=max(2, lw - 1))  # arm fwd
    d.line([P(60, 13), P(50, 19)], fill=INK, width=max(2, lw - 1))  # arm back
    # red ban circle + slash around the runner
    cx, cy = P(63, 20)
    rr = 19 * s
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=RED, width=3)
    d.line([P(51, 32), P(75, 8)], fill=RED, width=3)


# ----------------------------------------------------------------------------
# Cards
# ----------------------------------------------------------------------------

CARDS = [
    (1, "SHENZHEN · SUMMIT", "Trump, Xi and Putin hold first three-way summit",
     "Met for 90 minutes at APEC and issued a “Declaration on Peace” on "
     "nuclear risk and UN reform. (Reuters, AP, Xinhua)",
     ill_summit, "APEC 2026 · SHENZHEN", False),
    (2, "THE HAGUE · JUSTICE", "World Court: Myanmar committed genocide",
     "By 9 votes to 6, the ICJ found Myanmar guilty of genocide against the "
     "Rohingya and ordered reparations. (Al Jazeera, UN News)",
     ill_court, "ICJ VERDICT · 9–6", False),
    (3, "ANTALYA · CLIMATE", "COP31 draft drops fossil fuels and $120bn aid goal",
     "The slimmer second text has no figure for adaptation aid; talks are "
     "due to end on Friday. (Reuters, AFP)", ill_cop, "SECOND DRAFT", False),
    (4, "NEW YORK · MARKETS", "Anthropic debuts with the largest IPO on record",
     "Priced at $83, it raised $81.3bn and closed day one up 17% at $97.17; "
     "the Dow fell 1,101 points on AI fears. (AP, NPR)", ill_ipo,
     "ANT · NASDAQ · FIRST DAY", False),
    (5, "WORLDWIDE · GAMES", "GTA VI goes on sale after 13 years",
     "The midnight launch draws rave reviews; $79.99 on PS5 and Xbox; "
     "estimates put sales near 19 million. (ABC, Sensor Tower)", ill_gta,
     "13 YEARS ON", False),
    (6, "ODISHA · STORM", "Cyclone Akvan nears India's coast",
     "Over 100,000 people in shelters before Friday's landfall, due between "
     "Narsapur and Puri. (IMD)", ill_cyclone, "LANDFALL FRIDAY", False),
    (7, "RIYADH · WAR", "Houthi missile reaches Riyadh; debris hits tower",
     "Saudi air defences engaged it; debris fell on the financial district's "
     "PIF tower, no injuries reported. (Reuters)", ill_riyadh,
     "PIF TOWER", False),
    (8, "HORMUZ · SHIPPING", "Iran says tankers hit mines and caught fire",
     "IRGC says two supertankers with 4m+ barrels struck mines; no ships "
     "named. (Al Jazeera)", ill_hormuz, "2 SUPERTANKERS", True),
    (9, "SEOUL · JUSTICE", "Korea's top court clears ex-PM Han",
     "Han Duck-soo's martial-law conviction is overturned. (AP)", ill_seoul,
     "SUPREME COURT", False),
    (10, "GREENLAND · SECURITY", "Denmark backs Arctic pact with US",
     "Parliament approves the Greenland security deal 109–0. (AP)",
     ill_arctic, "GREENLAND DEAL", False),
    (11, "CANBERRA · ECONOMY", "Australia's jobless rate hits 4.9%",
     "Highest since 2024; 43,500 jobs lost, shares and the dollar slide. "
     "(ABC)", ill_jobs, "JOBS REPORT", False),
    (12, "MOGADISHU · DIPLOMACY", "Somalia expels the UAE's ambassador",
     "Given 72 hours to leave; Mogadishu calls UAE actions an “open "
     "invasion”. (Al Jazeera)", ill_somalia, "72 HOURS TO LEAVE", False),
    (13, "NAIROBI · SPORT", "Marathon champion banned for doping",
     "Kenya's Peres Jepchirchir gets three years. (ABC)", ill_runner,
     "BANNED · 3 YEARS", False),
]


def draw_card(d, x, y, w, h, card, small=False):
    num, kicker, head, body, illus, chip_text, claim = card
    d.rectangle([x, y, x + w, y + h], outline=PANEL_LINE, fill=(250, 247, 238))
    ph = 30 if small else 36
    illus(d, x + 1, y + 1, w - 2, ph)
    # label chip on the panel + optional CLAIM flag
    cw_ = chip(d, x + 6, y + ph - 14, chip_text, INK,
               font_size=8 if small else 9)
    if claim:
        chip(d, x + 12 + cw_, y + ph - 14, "CLAIM", RED,
             font_size=8 if small else 9)
    ty = y + ph + 4
    fk = F("sansb", 9 if small else 10)
    d.text((x + 7, ty), f"{num} · {kicker}", font=fk, fill=RED)
    ty += 12 if small else 13
    fh = F("sansb", 13 if small else 15)
    hlines = wrap(d, head, fh, w - 14)[:2]
    for ln in hlines:
        d.text((x + 7, ty), ln, font=fh, fill=BLACK)
        ty += 15 if small else 16
    # body: shrink the font until the wrapped text fits the space left
    avail = y + h - 3 - ty
    sizes = (9.5, 9) if small else (10.5, 10, 9.5, 9)
    blines = []
    for sz in sizes:
        fb = F("sans", sz)
        lh = sz + 2
        blines = wrap(d, body, fb, w - 14)
        if len(blines) * lh <= avail:
            break
    for ln in blines:
        if ty + lh > y + h - 2:
            break
        d.text((x + 7, ty), ln, font=fb, fill=(40, 40, 40))
        ty += lh


def cards_grid(d):
    y = 240
    gap = 6
    rows = [(CARDS[0:3], 3, 114), (CARDS[3:6], 3, 114),
            (CARDS[6:9], 3, 114), (CARDS[9:13], 4, 102)]
    for cards, ncols, rh in rows:
        colw = (CW - (ncols - 1) * gap) / ncols
        for i, card in enumerate(cards):
            draw_card(d, M + i * (colw + gap), y, colw, rh, card,
                      small=(ncols == 4))
        y += rh + gap


# ----------------------------------------------------------------------------
# Bottom section: map, also-list, date check, footer
# ----------------------------------------------------------------------------

def world_map(d, x, y, w, h):
    f = F("sansb", 13)
    d.text((x, y), "WHERE IT HAPPENED", font=f, fill=INK)
    py = y + 18
    d.rectangle([x, py, x + w, py + h], fill=(203, 220, 230),
                outline=PANEL_LINE)
    land = (58, 84, 118)
    blobs = [
        [(28, 26), (70, 12), (120, 16), (140, 32), (128, 50), (105, 56),
         (96, 76), (84, 82), (70, 64), (52, 58), (36, 46)],            # N America
        [(128, 8), (152, 6), (156, 20), (138, 26), (128, 20)],          # Greenland
        [(96, 90), (116, 84), (128, 98), (122, 126), (108, 146),
         (96, 130), (90, 106)],                                         # S America
        [(196, 28), (214, 18), (238, 22), (246, 34), (232, 44),
         (214, 46), (200, 42)],                                         # Europe
        [(206, 62), (238, 54), (262, 64), (266, 90), (254, 120),
         (232, 130), (214, 110), (206, 86)],                            # Africa
        [(246, 20), (300, 12), (356, 18), (392, 32), (398, 50),
         (372, 56), (352, 74), (330, 82), (316, 64), (300, 56),
         (282, 48), (262, 42), (248, 34)],                              # Asia
        [(330, 94), (352, 90), (368, 98), (344, 104), (326, 102)],      # SE Asia
        [(352, 114), (388, 108), (402, 120), (392, 138), (362, 138),
         (350, 126)],                                                   # Australia
    ]
    sy = h / 150.0
    for b in blobs:
        d.polygon([(x + px, py + qy * sy) for px, qy in b], fill=land)
    pins = {1: (360, 56), 2: (214, 32), 3: (250, 46), 4: (102, 42),
            6: (320, 64), 7: (270, 56), 8: (284, 52), 9: (372, 48),
            10: (140, 14), 11: (386, 126), 12: (264, 92), 13: (254, 104)}
    fp = F("sansb", 8)
    for n, (px, qy) in pins.items():
        cx, cy = x + px, py + qy * sy
        d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=RED,
                  outline=(255, 255, 255))
        s = str(n)
        d.text((cx - tw(d, s, fp) / 2, cy - 4), s, font=fp,
               fill=(255, 255, 255))
    # pin 5: worldwide badge
    cx, cy = x + 18, py + 14
    d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=RED,
              outline=(255, 255, 255))
    d.text((cx - tw(d, "5", fp) / 2, cy - 4), "5", font=fp, fill=(255, 255, 255))
    fl = F("sans", 8)
    d.text((cx + 11, cy - 4), "WORLDWIDE", font=fl, fill=INK)


ALSO = [
    (14, "SHENZHEN", "Xi urges ban on all nuclear arms (Al Jazeera)"),
    (15, "APEC", "Albanese to Putin: “End your war, end it now” (ABC)"),
    (16, "SEOUL", "Half a million sit college entrance exam (Sedaily)"),
    (17, "JAKARTA", "Asset-seizure law passes after 18 years (Kompas)"),
    (18, "GAZA", "Israel ends tank raid past truce line (BBC)"),
    (19, "KRASNODAR", "Kyiv says it hit two oil refineries (Euronews)"),
    (20, "BRUSSELS", "EU delays methane rules two years (Euronews)"),
    (21, "LONDON", "Inquiry: yacht Bayesian was vulnerable to wind (RNZ)"),
    (22, "ZURICH", "Two rivals to challenge FIFA's Infantino (ABC)"),
    (23, "ROME", "Author Corrado Augias dies at 91 (Euronews)"),
    (24, "SUDAN", "Court sentences absent RSF chief to death (AP)"),
    (25, "PRETORIA", "Central bank holds rate at 7.25% (SABC)"),
    (26, "CANARIES", "Record 11,000 migrants in 15 days (Africanews)"),
    (27, "FLORIDA", "Floods shut Broward, Miami schools again (CBS)"),
    (28, "WELLINGTON", "Court: pay equity cuts broke rights law (RNZ)"),
    (29, "TONGA", "Drought emergency takes effect (RNZ)"),
    (30, "COOK ISLANDS", "Cyclone Xavier weakens to category 4 (RNZ)"),
    (31, "SPACE", "Red giant seen eating a Sun-sized star (Nature)"),
    (32, "BOGOTÁ", "Colombia's unions hold national strike (Infobae)"),
    (33, "BERLIN", "Europe seeks a winter truce; Putin says no (Euronews)"),
    (34, "JOHANNESBURG", "South Africa beat Bangladesh by 9 wickets (AP)"),
    (35, "NORTHLAND, NZ", "19 sperm whales die in mass stranding (RNZ)"),
    (36, "WASHINGTON", "Weekly jobless claims rise to 203,000 (Reuters)"),
]


def also_list(d, x, y, w):
    f = F("sansb", 13)
    d.text((x, y), "ALSO ON THURSDAY 19 NOVEMBER", font=f, fill=INK)
    fr = F("sansb", 10)
    s = "23 MORE STORIES"
    d.text((x + w - tw(d, s, fr), y + 2), s, font=fr, fill=RED)
    fn = F("sansb", 9.5)
    fb = F("sans", 9.5)
    ly = y + 20
    for num, place, text in ALSO:
        head = f"{num} {place} "
        d.text((x, ly), head, font=fn, fill=INK)
        off = tw(d, head, fn)
        line = text
        while tw(d, line, fb) > w - off and len(line) > 4:
            line = line[:-1]
        d.text((x + off, ly), line, font=fb, fill=(40, 40, 40))
        ly += 9.4


def date_check(d, x, y, w):
    d.rectangle([x, y, x + w, y + 62], outline=RED, width=2,
                fill=(250, 244, 232))
    f = F("sans", 9.5)
    fb = F("sansb", 9.5)
    text = ("First reported Wednesday 18 Nov, so NOT shown as Thursday's "
            "news: the Crimean Bridge strike · Van Gogh's $190.4m sale · "
            "Voyager 1 one light-day from Earth · Gemini 3 & Neon launch · "
            "EU's €45bn Ukraine loan plan · Nvidia results. Not yet news: "
            "Cyclone Akvan's landfall and COP31's close (Fri 20 Nov).")
    lines = wrap(d, text, f, w - 76)
    d.text((x + 8, y + 6), "DATE", font=fb, fill=RED)
    d.text((x + 8, y + 18), "CHECK", font=fb, fill=RED)
    ly = y + 5
    for ln in lines[:5]:
        d.text((x + 62, ly), ln, font=f, fill=(40, 40, 40))
        ly += 11


def footer(d):
    d.line([M, 950, W - M, 950], fill=RULE, width=1)
    f1 = F("sans", 10)
    s1 = ("Every story here happened, or was first reported, on Thursday "
          "19 November 2026 in at least one time zone. Claims are "
          "attributed, not stated as fact.")
    d.text(((W - tw(d, s1, f1)) / 2, 958), s1, font=f1, fill=GREY)
    f2 = F("sans", 9.5)
    s2 = ("Sources: Reuters, AP, AFP, BBC, Al Jazeera, UN News, Euronews, "
          "ABC, RNZ, Xinhua, Nature. Original vector drawings.")
    d.text(((W - tw(d, s2, f2)) / 2, 974), s2, font=f2, fill=GREY)


def build():
    img = Image.new("RGB", (W, W), PAPER)
    d = ImageDraw.Draw(img)
    header(d, img)
    stat_strip(d)
    region_chips(d)
    cards_grid(d)
    world_map(d, M, 710, 452, 132)
    also_list(d, 492, 710, 508)
    date_check(d, M, 866, 452)
    footer(d)
    img.save(OUT, optimize=True)
    print("wrote", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    build()
