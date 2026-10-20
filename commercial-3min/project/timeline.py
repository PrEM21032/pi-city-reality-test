"""Edit decision list + overlay sequences for the 3-minute PI StationOS film.
Visuals = real photos of the store supplied by the owner. Every PI interface is a labeled concept simulation with fictional figures."""
import cairo, json, math, os
from lib import *
from footage import draw_shot, SRC_DIR

PH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "photos")
VO = {m["id"]: m for m in json.load(open(os.path.join(os.path.dirname(__file__), "vo.json")))}
def S(vid, i, frac=0.0):
    """Time of sentence i of narration block vid (+fraction through it)."""
    s = VO[vid]["sentences"][i]; return s["start"] + frac * (s["end"] - s["start"])
TOTAL = 186.0

# ---------------------------------------------------------------- real store photos (supplied by the owner)
# name: (file, default focus cx, cy, description)
SLOTS = {
    "counter":   ("01_7085d44f.jpg", .5, .5, "Front counter and register"),
    "overview":  ("02_fddc8a7d.jpg", .5, .5, "Counter side, freezers, boiled peanuts, ATM"),
    "food":      ("03_967c66ed.jpg", .5, .45, "Hunt Brothers Pizza food-service counter"),
    "coffee":    ("04_e2416f49.jpg", .5, .5, "Coffee and fountain station, aisle to coolers"),
    "jerky":     ("05_41ad01a6.jpg", .5, .5, "Snack aisle, jerky display, 'Irvington Food Mart' cooler banner"),
    "candy":     ("06_1a793f3c.jpg", .5, .5, "Candy aisle and endcap"),
    "coolrun":   ("07_8208a20a.jpg", .5, .5, "Cooler doors along the aisle (portrait)"),
    "cooldoor":  ("08_81b57a92.jpg", .5, .5, "Cooler doors, close angle"),
    "monster":   ("09_ff7d3162.jpg", .5, .5, "Energy-drink cooler wall"),
    "chips":     ("10_043b4174.jpg", .5, .5, "Chips aisle, coolers, back wall"),
    "wide":      ("11_5b64931f.jpg", .5, .5, "Wide aisle view: beer, wine, snacks"),
}
FIT = 'cover'

FULL = (0, 0, W, H)
G = 6
TILES = [(0, 0, W / 2 - G / 2, H / 2 - G / 2), (W / 2 + G / 2, 0, W / 2 - G / 2, H / 2 - G / 2),
         (0, H / 2 + G / 2, W / 2 - G / 2, H / 2 - G / 2), (W / 2 + G / 2, H / 2 + G / 2, W / 2 - G / 2, H / 2 - G / 2)]
LEFT = (0, 0, W / 2 - G / 2, H); RIGHT = (W / 2 + G / 2, 0, W / 2 - G / 2, H)

# ---------------------------------------------------------------- shot list (stills with deliberate camera moves)
# (start, dur, slot, rect, zoom0 -> zoom1, focus cx,cy, pan dx,dy across the shot, dissolve-in, dim)
SHOTS = []
def shot(t, d, slot, rect=FULL, z0=1.0, z1=1.08, cx=None, cy=None, dx=0.0, dy=0.0, fade=0.0, grade=1.0, fit=None):
    SHOTS.append(dict(t=t, d=d, slot=slot, off=0, rect=rect, z0=z0, z1=z1, cx=cx, cy=cy, dx=dx, dy=dy, fade=fade, grade=grade, fit=fit))

# A. 0:00-0:25 the real store
shot(0.0, 5.4, "wide", z0=1.0, z1=1.14, cy=.45, fade=1.2)                 # push down the main aisle
shot(5.4, 3.6, "jerky", z0=1.12, z1=1.2, cx=.55, cy=.3, dx=-.08)          # 'Irvington Food Mart' banner
shot(9.0, 3.4, "counter", z0=1.0, z1=1.07, cy=.55)
shot(12.4, 3.2, "food", z0=1.02, z1=1.1, cy=.42, dx=.05)
shot(15.6, 3.0, "coffee", z0=1.05, z1=1.12, cx=.4, dx=.08)
shot(18.6, 3.0, "candy", z0=1.04, z1=1.1, cx=.55, dx=-.06)
shot(21.6, 4.0, "monster", z0=1.0, z1=1.07, cy=.55)
# B. 0:25-0:50 four separate views (fuel tile is an illustrative data sheet drawn in ov_problem)
shot(25.5, 24.5, "monster", TILES[1], 1.15, 1.22, cx=.62, cy=.6)
shot(25.5, 24.5, "counter", TILES[2], 1.5, 1.6, cx=.62, cy=.55)            # register
shot(25.5, 24.5, "food", TILES[3], 1.25, 1.32, cx=.62, cy=.55)            # food-service case
# C. 0:50-1:31 inventory: before -> after
shot(50.0, 6.0, "cooldoor", z0=1.0, z1=1.12, cx=.55, fade=.6)
shot(56.0, 6.5, "coolrun", z0=1.0, z1=1.06, fit='pillar')
shot(62.5, 28.3, "monster", z0=1.1, z1=1.2, cx=.4, cy=.6, dx=-.08, grade=.62, fade=.8)
# D. 1:31-2:05 fuel + store together
shot(90.8, 3.7, "overview", z0=1.04, z1=1.14, fade=.5)
shot(94.5, 3.0, "counter", z0=1.12, z1=1.22, cx=.68, cy=.55)
shot(97.5, 27.0, "counter", LEFT, 1.15, 1.22, cx=.65, cy=.55, grade=.5)
shot(97.5, 27.0, "food", RIGHT, 1.1, 1.18, cx=.6, cy=.5, grade=.5)
# E. 2:05-2:36 shift handoff, then owner phone
shot(124.5, 5.0, "counter", z0=1.0, z1=1.08, fade=.6)
shot(129.5, 14.5, "counter", z0=1.35, z1=1.45, cx=.3, cy=.55, dx=.05, grade=.55)
shot(144.0, 12.5, "food", z0=1.15, z1=1.22, cx=.45, grade=.42, fade=.6)
# F. 2:36-3:06 invitation
shot(156.0, 4.6, "wide", z0=1.12, z1=1.0, cy=.45, fade=.6)
shot(160.6, 4.0, "chips", z0=1.0, z1=1.08, dx=.05, grade=.7)
shot(164.6, 4.2, "jerky", z0=1.06, z1=1.12, cx=.5, cy=.35, grade=.7)
shot(168.8, 4.2, "coffee", z0=1.0, z1=1.07, grade=.8)
shot(173.0, 13.0, "counter", z0=1.12, z1=1.0, grade=.8, fade=.5)

def draw_footage(cr, pool, t):
    keep = set()
    for i, s in enumerate(SHOTS):
        if not (s["t"] <= t < s["t"] + s["d"]): continue
        f, cx, cy, label = SLOTS[s["slot"]]
        cx = s["cx"] if s["cx"] is not None else cx; cy = s["cy"] if s["cy"] is not None else cy
        k = (t - s["t"]) / s["d"]; e = einout(k)
        z = lerp(s["z0"], s["z1"], e)
        src_t = 0.0
        key = f"shot{i}"; keep.add(key)
        fa = ease(prog(t, s["t"], s["t"] + s["fade"])) if s["fade"] else 1.0
        cr.push_group()
        draw_shot(cr, pool, key, os.path.join(PH, f), src_t, s["rect"], cx + s["dx"] * (e - .5), cy + s["dy"] * (e - .5),
                  z, s["fit"] or FIT, label, s["grade"], t)
        cr.pop_group_to_source(); cr.paint_with_alpha(fa)
    pool.gc(keep)

# ================================================================ shared UI
SIM = "CONCEPT SIMULATION — ILLUSTRATIVE DATA"
def sim_badge(cr, a):
    if a <= 0: return
    font(cr, 22, 'Inter', True); w = text_w(cr, SIM, 2) + 70; x, y = 48, 40
    rrect(cr, x, y, w, 50, 25); rgba(cr, hexc('1A1406'), .88 * a); cr.fill_preserve(); rgba(cr, AMBER, .9 * a); cr.set_line_width(2); cr.stroke()
    cr.arc(x + 28, y + 25, 7, 0, 6.283); rgba(cr, AMBER, a); cr.fill()
    text(cr, SIM, x + 46, y + 33, 22, AMBER, a, bold=True, track=2)

def real_tag(cr, a, s="REAL STORE PHOTO"):
    if a <= 0: return
    font(cr, 18, 'Inter', True); w = text_w(cr, s, 2.5)
    text(cr, s, W - 52 - w, 70, 18, WHITE, .78 * a, bold=True, track=2.5)
    rgba(cr, RED, .9 * a); cr.arc(W - 70 - w, 63, 6, 0, 6.283); cr.fill()

def scrim(cr, x, y, w, h, a, side='right'):
    if a <= 0: return
    if side == 'right': g = cairo.LinearGradient(x, 0, x + w, 0); g.add_color_stop_rgba(0, *BG, 0); g.add_color_stop_rgba(.35, *BG, .72 * a); g.add_color_stop_rgba(1, *BG, .86 * a)
    elif side == 'left': g = cairo.LinearGradient(x + w, 0, x, 0); g.add_color_stop_rgba(0, *BG, 0); g.add_color_stop_rgba(.35, *BG, .72 * a); g.add_color_stop_rgba(1, *BG, .86 * a)
    else: g = cairo.LinearGradient(0, y, 0, y + h); g.add_color_stop_rgba(0, *BG, 0); g.add_color_stop_rgba(.4, *BG, .72 * a); g.add_color_stop_rgba(1, *BG, .9 * a)
    cr.set_source(g); cr.rectangle(x, y, w, h); cr.fill()

def wrap(cr, s, size, maxw, fam='Inter', bold=False):
    font(cr, size, fam, bold); out, line = [], ''
    for wd in s.split():
        if line and text_w(cr, line + ' ' + wd) > maxw: out.append(line); line = wd
        else: line = (line + ' ' + wd).strip()
    return out + [line]

def para(cr, s, x, y, size, color, a, maxw, lh=1.3, fam='Inter', bold=False):
    for i, ln in enumerate(wrap(cr, s, size, maxw, fam, bold)): text(cr, ln, x, y + i * size * lh, size, color, a, fam, bold)
    return len(wrap(cr, s, size, maxw, fam, bold)) * size * lh

def stepcard(cr, x, y, w, h, tag, tagc, a, active, body_fn):
    if a <= 0: return
    oy = (1 - eout(a)) * 24
    card(cr, x, y + oy, w, h, 18, a * (1 if active else .78), glow=tagc if active else None, shadow_a=.3)
    text(cr, tag, x + 28, y + oy + 40, 19, tagc, a, bold=True, track=2.2)
    body_fn(x + 28, y + oy + 40, a * (1 if active else .72))

def headline_on(cr, s, x, y, size, a, color=WHITE, align='left', fam='Inter Display', bold=True, shadow=True):
    if a <= 0: return
    oy = (1 - eout(a)) * 18
    if shadow: text(cr, s, x + 2, y + oy + 3, size, (0, 0, 0), a * .55, fam, bold, align)
    text(cr, s, x, y + oy, size, color, a, fam, bold, align)

def button(cr, x, y, w, h, s, c, a, filled=False, press=0.0, hl=0.0):
    sc = 1 - .06 * press
    cx, cy = x + w / 2, y + h / 2; w2, h2 = w * sc, h * sc
    rrect(cr, cx - w2 / 2, cy - h2 / 2, w2, h2, h2 / 2)
    rgba(cr, c, (.95 if filled else .14 + .2 * hl) * a); cr.fill_preserve(); rgba(cr, c, (.6 + .4 * hl) * a); cr.set_line_width(2 + 2 * hl); cr.stroke()
    text(cr, s, cx, cy + h * .17, h * .42, BG if filled else c, a, bold=True, align='center')

def ripple(cr, x, y, t, t0):
    p = prog(t, t0, t0 + .6)
    if 0 < p < 1:
        cr.arc(x, y, 16 + 60 * eout(p), 0, 6.283); rgba(cr, WHITE, .7 * (1 - p)); cr.set_line_width(3); cr.stroke()

# ================================================================ A. opening
def ov_open(cr, t):
    real_tag(cr, fade(t, .8, 25.2, .8, .4))
    la = fade(t, 2.5, 9.5, .8, .8)
    if la > 0:
        scrim(cr, 0, 640, W, 440, la, 'bottom')
        rgba(cr, CYAN, la); cr.rectangle(110, 742, 80 * eout(prog(t, 2.5, 3.4)), 4); cr.fill()
        headline_on(cr, "IRVINGTON FOOD MART", 110, 800, 50, la)
        text(cr, "9436 Irvington Bayou La Batre Hwy  ·  Irvington, Alabama", 110, 850, 30, hexc('D9E1EE'), la)
    ha = fade(t, 21.4, 25.3, .6, .5)
    if ha > 0:
        scrim(cr, 0, 560, W, 520, ha, 'bottom')
        headline_on(cr, "One store.", 110, 760, 72, eout(prog(t, 21.4, 22.1)) * (1 - ease(prog(t, 24.8, 25.3))))
        headline_on(cr, "Every hour, another decision.", 110, 845, 72, eout(prog(t, 22.0, 22.7)) * (1 - ease(prog(t, 24.8, 25.3))), CYAN)

# ================================================================ B. the owner's problem
PROB = [("FUEL", "Its own numbers", 0), ("SHELF", "Its own counts", 1), ("COUNTER", "Its own register", 2), ("SHIFT", "Its own notes", 3)]
def ov_problem(cr, t):
    if not (25.0 <= t < 50.5): return
    out = 1 - ease(prog(t, 49.4, 50.2))
    real_tag(cr, out)
    x, y, w, h = TILES[0]
    g = cairo.LinearGradient(x, y, x, y + h); g.add_color_stop_rgb(0, *BG2); g.add_color_stop_rgb(1, *BG); cr.set_source(g); cr.rectangle(x, y, w, h); cr.fill()
    fa = eout(prog(t, 25.6, 26.4)) * out
    cx0, cy0 = x + 330, y + 70
    card(cr, cx0, cy0, 560, 380, 18, fa, shadow_a=.3)
    text(cr, "FUEL TOTALS · TODAY", cx0 + 30, cy0 + 48, 18, CYAN, fa, bold=True, track=2)
    for j, (g_, v) in enumerate((("Regular", "1,412 gal"), ("Plus", "268 gal"), ("Premium", "201 gal"), ("Diesel", "655 gal"))):
        text(cr, g_, cx0 + 30, cy0 + 112 + j * 58, 28, WHITE, fa); text(cr, v, cx0 + 530, cy0 + 112 + j * 58, 28, WHITE, fa, 'DejaVu Sans Mono', align='right')
    text(cr, "Illustrative figures", cx0 + 30, cy0 + 352, 18, AMBER, fa, bold=True)
    for (lab, sub, i) in PROB:
        a = eout(prog(t, S("v2", 1) - .3 + i * 1.6, S("v2", 1) + .3 + i * 1.6)) * out
        x, y, w, h = TILES[i]
        g = cairo.LinearGradient(0, y, 0, y + 190); g.add_color_stop_rgba(0, 0, 0, 0, .75 * a); g.add_color_stop_rgba(1, 0, 0, 0, 0)
        cr.set_source(g); cr.rectangle(x, y, w, 190); cr.fill()
        ly = y + 70
        headline_on(cr, lab, x + 44, ly, 50, a)
        text(cr, sub, x + 46, ly + 44, 30, hexc('D9E1EE'), a)
    # attention jumping tile to tile: chasing one problem at a time
    t0 = S("v2", 4)
    if t0 - .2 < t < 49.6:
        order = [1, 2, 0, 3, 1, 3, 2, 0]
        k = int((t - t0) / .62); kk = order[k % len(order)] if t >= t0 else None
        for i in range(4):
            if i != kk:
                x, y, w, h = TILES[i]; rgba(cr, (0, 0, 0), .45 * out * ease(prog(t, t0, t0 + .4))); cr.rectangle(x, y, w, h); cr.fill()
        if kk is not None:
            x, y, w, h = TILES[kk]; rrect(cr, x + 10, y + 10, w - 20, h - 20, 14); rgba(cr, AMBER, .95 * out); cr.set_line_width(6); cr.stroke()
    ca = fade(t, 45.4, 50.3, .5, .5)
    if ca > 0:
        rrect(cr, W / 2 - 520, H / 2 - 70, 1040, 140, 24); rgba(cr, BG, .9 * ca); cr.fill()
        headline_on(cr, "Separate problems. Chased one at a time.", W / 2, H / 2 + 20, 52, ca, align='center', shadow=False)

# ================================================================ C. inventory
def ov_inventory(cr, t):
    if not (50.0 <= t < 91.3): return
    real_tag(cr, fade(t, 50.0, 62.6, .4, .4))
    # BEFORE
    ba = fade(t, 50.6, 62.4, .6, .5)
    if ba > 0:
        chip(cr, "THE OLD WAY", 110, 150, 24, MUTED, ba, fill_a=.35)
        scrim(cr, 0, 560, W, 520, ba, 'bottom')
        headline_on(cr, "The shortage is found", 110, 770, 64, eout(prog(t, S("v3", 1), S("v3", 1) + .7)) * ba)
        headline_on(cr, "when the shelf is already empty.", 110, 848, 64, eout(prog(t, S("v3", 1, .4), S("v3", 1, .4) + .7)) * ba, AMBER)
    if t < 62.3: return
    # AFTER: PI concept workflow rail
    pa = ease(prog(t, 62.4, 63.2)) * (1 - ease(prog(t, 90.5, 91.2)))
    sim_badge(cr, pa)
    chip(cr, "THE PI CONCEPT", 110, 150, 24, CYAN, eout(prog(t, 62.6, 63.4)) * pa, fill_a=.2)
    scrim(cr, 820, 0, W - 820, H, pa, 'right')
    X, Wd = 1010, 860
    s1 = S("v4", 1); s1e = S("v4", 1, 1.0); s2 = S("v4", 2); s3 = S("v4", 3); s4 = S("v4", 4)
    t_sig, t_stock, t_flag, t_prop, t_dec = s1 + .4, S("v4", 1, .42), S("v4", 1, .72), s2, s4 - .6
    act = [t_sig, t_stock, t_flag, t_prop, t_dec]
    global E0, A0, OK
    E0 = t_dec + .3; A0 = t_dec + 2.0; OK = A0 + .3
    def active(i): return act[i] <= t < (act[i + 1] if i + 1 < len(act) else 99)
    def b1(x, y, a):
        text(cr, "16 oz energy drinks: selling 1.8× usual pace", x, y + 46, 30, WHITE, a)
        pts = [3, 3, 4, 3, 4, 5, 7, 8, 9, 11]; sx, sy = x + 640, y - 10
        for j, v in enumerate(pts[:max(2, int(len(pts) * eout(prog(t, t_sig, t_sig + 1.2))))]):
            (cr.move_to if j == 0 else cr.line_to)(sx + j * 17, sy + 40 - v * 3.2)
        rgba(cr, CYAN, a); cr.set_line_width(3); cr.stroke()
    def b2(x, y, a):
        text(cr, "About 14 on hand  ·  next delivery Thursday", x, y + 46, 30, WHITE, a)
    def b3(x, y, a):
        text(cr, "Likely to run short before Thursday", x, y + 48, 34, AMBER, a, 'Inter Display', True)
    def b4(x, y, a):
        para(cr, "At this pace, stock covers about 1.5 days. Proposal: add cases to Thursday's order.", x, y + 44, 28, WHITE, a, Wd - 70)
        qty = 2 if t < E0 + .7 else 3
        ea = eout(prog(t, t_prop + 1.0, t_prop + 1.6)) * a
        rrect(cr, x, y + 104, 360, 54, 12); rgba(cr, GOLD, .14 * ea); cr.fill()
        text(cr, f"+{qty} cases · 16 oz energy", x + 18, y + 141, 28, GOLD, ea, bold=True)
        ns = eout(prog(t, s3, s3 + .5)) * a
        chip(cr, "DRAFT · NOT SENT", x + Wd - 80, y + 128, 22, AMBER, ns * (1 if t < OK else 0), 'right')
    def b5(x, y, a):
        appr = t >= OK
        if not appr:
            hl_e = fade(t, E0, A0 - .1, .2, .2)
            button(cr, x, y + 22, 220, 62, "Approve", GREEN, a, True, math.exp(-abs(t - (A0 + .1)) * 10) * (t > A0 - .2))
            button(cr, x + 240, y + 22, 180, 62, "Edit", CYAN, a, hl=hl_e)
            button(cr, x + 440, y + 22, 200, 62, "Decline", MUTED, a)
            if E0 < t < OK:
                text(cr, "Edited: 2 → 3", x + 664, y + 63, 22, CYAN, a * ease(prog(t, E0 + .2, E0 + .6)), bold=True)
            ripple(cr, x + 330, y + 53, t, E0); ripple(cr, x + 110, y + 53, t, A0)
        else:
            k = eout(prog(t, OK, OK + .5))
            cr.arc(x + 30, y + 52, 28, 0, 6.283); rgba(cr, GREEN, .2 * a * k); cr.fill()
            check(cr, x + 30, y + 54, 30, GREEN, a * k, k)
            text(cr, "Approved by the owner", x + 78, y + 50, 32, GREEN, a * k, 'Inter Display', True)
            text(cr, "Added to Thursday's order list for the owner to place", x + 78, y + 86, 24, hexc('D9E1EE'), a * k)
    ha = eout(prog(t, 62.8, 63.6)) * pa
    pi_mark(cr, X + 26, 152, 22, ha, ha)
    text(cr, "PI StationOS", X + 62, 146, 22, CYAN, ha, 'Inter Display', True)
    text(cr, "Inventory watch · energy-drink cooler · simulated", X + 62, 174, 22, MUTED, ha)
    rows = [("SIGNAL · SALES PACE", CYAN, t_sig, 92, b1), ("SIGNAL · STOCK", CYAN, t_stock, 92, b2), ("FLAG", AMBER, t_flag, 92, b3),
            ("WHY + PROPOSAL", GOLD, t_prop, 196, b4), ("OWNER DECISION", GREEN, t_dec, 142, b5)]
    y = 206
    for i, (tag, c, t0, h, fn) in enumerate(rows):
        a = eout(prog(t, t0, t0 + .5)) * pa
        stepcard(cr, X, y, Wd, h, tag, c, a, active(i), fn)
        y += h + 16

# ================================================================ D. one operating picture
def ov_picture(cr, t):
    if not (90.8 <= t < 124.9): return
    real_tag(cr, fade(t, 90.9, 97.8, .4, .4))
    s1, s2, s3, s4, s5 = (S("v5", i) for i in range(1, 6))
    out = 1 - ease(prog(t, 124.0, 124.8))
    # separate labels while views are apart
    sa = fade(t, 97.6, s2 + .6, .5, .5) * out
    if sa > 0:
        for (x, lab) in ((W / 4, "FUEL REPORT — REVIEWED HERE"), (3 * W / 4, "STORE REPORT — REVIEWED THERE")):
            chip(cr, lab, x, H / 2, 26, WHITE, sa, 'center', fill_a=.25)
        cr.set_line_width(4); rgba(cr, WHITE, .5 * sa); cr.set_dash([12, 12]); cr.move_to(W / 2, 140); cr.line_to(W / 2, H - 180); cr.stroke(); cr.set_dash([])
    pa = ease(prog(t, s2, s2 + .8)) * out
    sim_badge(cr, ease(prog(t, s2 - .4, s2 + .2)) * out)
    if pa <= 0: return
    x, y, w, h = 300, 128, 1320, 520
    card(cr, x, y, w, h, 24, pa, glow=CYAN, shadow_a=.45)
    text(cr, "ONE OPERATING PICTURE", x + 40, y + 58, 22, CYAN, pa, bold=True, track=3)
    text(cr, "Evening · fuel visits and inside visits, together", x + 40, y + 100, 32, WHITE, pa, 'Inter Display', True)
    gx, gy, gw, gh = x + 60, y + 140, 860, 300
    for j in range(4):
        rgba(cr, WHITE, .07 * pa); cr.rectangle(gx, gy + gh * j / 3, gw, 1); cr.fill()
    hrs = ["3 PM", "4", "5", "6", "7", "8", "9 PM"]
    for j, hlab in enumerate(hrs): text(cr, hlab, gx + gw * j / 6, gy + gh + 36, 22, MUTED, pa, align='center')
    fuel = [.35, .38, .55, .72, .78, .7, .5]; inside = [.33, .35, .38, .4, .39, .37, .3]
    dp = eout(prog(t, s2 + .5, s2 + 2.5))
    def path(vals):
        for j, v in enumerate(vals): (cr.move_to if j == 0 else cr.line_to)(gx + gw * j / 6, gy + gh * (1 - v))
    ga = ease(prog(t, s3 + .8, s3 + 1.6)) * pa
    if ga > 0:  # gap between fuel and inside visits
        path(fuel)
        for j in reversed(range(7)): cr.line_to(gx + gw * j / 6, gy + gh * (1 - inside[j]))
        cr.close_path(); rgba(cr, AMBER, .22 * ga); cr.fill()
        text(cr, "Drivers fueling,", gx + gw * .52, gy + gh * .36, 26, AMBER, ga, bold=True, align='center')
        text(cr, "not coming inside", gx + gw * .52, gy + gh * .36 + 32, 26, AMBER, ga, bold=True, align='center')
    cr.save(); cr.rectangle(gx - 10, gy - 20, (gw + 20) * dp, gh + 40); cr.clip()
    path(fuel); rgba(cr, CYAN, pa); cr.set_line_width(5); cr.stroke()
    path(inside); rgba(cr, VIOLET, pa); cr.set_line_width(5); cr.stroke()
    cr.restore()
    lx = gx + gw + 50
    for j, (lab, c) in enumerate((("Fuel visits", CYAN), ("Inside visits", VIOLET))):
        rgba(cr, c, pa); cr.rectangle(lx, gy + 20 + j * 56, 34, 6); cr.fill()
        text(cr, lab, lx + 50, gy + 30 + j * 56, 26, WHITE, pa)
    text(cr, "Sample evening —", lx, gy + 170, 22, MUTED, pa); text(cr, "fictional figures", lx, gy + 200, 22, MUTED, pa)
    # decision: context changes the next move
    oa = eout(prog(t, s4, s4 + .6)) * out
    if oa > 0:
        bx, by, bw, bh = 300, 670, 640, 210
        strike = eout(prog(t, s5 + .2, s5 + .8))
        card(cr, bx, by, bw, bh, 20, oa * (1 - .35 * strike), shadow_a=.3)
        text(cr, "FOOD SALES ALONE", bx + 32, by + 48, 20, MUTED, oa, bold=True, track=2)
        text(cr, "Cut back on prep", bx + 32, by + 104, 40, WHITE, oa * (1 - .5 * strike), 'Inter Display', True)
        text(cr, "Treats the symptom", bx + 32, by + 150, 26, MUTED, oa * strike)
        if strike > 0:
            rgba(cr, MUTED, oa); cr.set_line_width(4); cr.move_to(bx + 30, by + 90); cr.line_to(bx + 30 + 330 * strike, by + 90); cr.stroke()
    ob = eout(prog(t, s5, s5 + .6)) * out
    if ob > 0:
        bx, by, bw, bh = 980, 670, 640, 210
        card(cr, bx, by, bw, bh, 20, ob, glow=GOLD, shadow_a=.3)
        text(cr, "WITH FUEL IN VIEW", bx + 32, by + 48, 20, GOLD, ob, bold=True, track=2)
        text(cr, "Staff the counter 5–8 PM", bx + 32, by + 104, 40, WHITE, ob, 'Inter Display', True)
        text(cr, "Invite drivers inside · owner's call", bx + 32, by + 150, 26, hexc('D9E1EE'), ob)
        chip(cr, "PROPOSED · OWNER DECIDES", bx + bw - 30, by + bh - 34, 17, GOLD, eout(prog(t, s5 + 1.5, s5 + 2.1)) * ob, 'right')

# ================================================================ E. shift handoff
def ov_shift(cr, t):
    if not (124.5 <= t < 144.6): return
    real_tag(cr, fade(t, 124.5, S("v6", 1) + .2, .4, .4))
    s1, s2, s3 = S("v6", 1), S("v6", 2), S("v6", 3)
    pa = ease(prog(t, s1 - .3, s1 + .4)) * (1 - ease(prog(t, 143.6, 144.4)))
    sim_badge(cr, pa)
    if pa <= 0: return
    scrim(cr, 820, 0, W - 820, H, pa, 'right')
    x, y, w = 1000, 130, 870
    card(cr, x, y, w, 610, 22, pa, shadow_a=.4)
    text(cr, "SHIFT HANDOFF", x + 34, y + 52, 21, CYAN, pa, bold=True, track=3)
    text(cr, "Evening lead → Overnight lead", x + 34, y + 96, 34, WHITE, pa, 'Inter Display', True)
    items = [("DONE", "Coolers restocked", GREEN, s1 + .35), ("DONE", "Coffee station cleaned", GREEN, s1 + .85),
             ("OPEN", "Restroom check due 11 PM", CYAN, S("v6", 1, .55))]
    for j, (k, s, c, t0) in enumerate(items):
        a = eout(prog(t, t0, t0 + .4)) * pa; yy = y + 160 + j * 66
        if k == "DONE":
            check(cr, x + 52, yy - 8, 26, GREEN, a, 1)
        else:
            cr.arc(x + 52, yy - 9, 12, 0, 6.283); rgba(cr, CYAN, a); cr.set_line_width(3); cr.stroke()
        text(cr, s, x + 88, yy, 30, WHITE, a)
        text(cr, k, x + w - 34, yy, 20, c, a, bold=True, align='right', track=2)
    ea = eout(prog(t, s2, s2 + .5)) * pa
    if ea > 0:
        yy = y + 370
        rrect(cr, x + 24, yy, w - 48, 104, 16); rgba(cr, hexc('2A1E0C'), .95 * ea); cr.fill_preserve(); rgba(cr, AMBER, .9 * ea); cr.set_line_width(2.5); cr.stroke()
        text(cr, "EXCEPTION", x + 52, yy + 38, 20, AMBER, ea, bold=True, track=2)
        text(cr, "Drawer 1 count is $14.20 under expected", x + 52, yy + 80, 30, WHITE, ea, bold=True)
    aa = eout(prog(t, s3, s3 + .5)) * pa
    if aa > 0:
        yy = y + 500
        text(cr, "NEXT ACTION", x + 34, yy + 10, 20, GOLD, aa, bold=True, track=2)
        text(cr, "Overnight lead recounts Drawer 1 at shift start", x + 34, yy + 54, 29, WHITE, aa)
        # tracker
        stages = [("Assigned", s3 + .6), ("Seen", s3 + 1.8), ("Done", s3 + 3.2)]
        tx, ty = x, y + 650
        card(cr, tx, ty, w, 120, 20, aa, shadow_a=.3)
        for j, (lab, t0) in enumerate(stages):
            on = eout(prog(t, t0, t0 + .4)); cx = tx + 110 + j * 320
            if j < 2:
                rgba(cr, WHITE, .15 * aa); cr.rectangle(cx + 30, ty + 48, 260, 4); cr.fill()
                rgba(cr, GREEN, aa); cr.rectangle(cx + 30, ty + 48, 260 * eout(prog(t, t0 + .2, stages[j + 1][1])), 4); cr.fill()
            cr.arc(cx, ty + 50, 20, 0, 6.283); rgba(cr, GREEN if on > 0 else MUTED, (.25 + .7 * on) * aa); cr.fill()
            if on > 0: check(cr, cx, ty + 52, 20, BG, aa * on, on)
            text(cr, lab, cx, ty + 100, 24, WHITE if on > 0 else MUTED, aa, bold=True, align='center')
        text(cr, "Owner sees each step", tx + w - 30, ty - 16, 20, MUTED, aa, align='right')

# ================================================================ E2. owner control (phone)
def phone_screen(t, s1, s2, s3):
    sw, sh = 420, 880
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw * 2, sh * 2); cr = cairo.Context(s)
    import lib; cr.set_font_options(lib._FO); cr.scale(2, 2)
    g = cairo.LinearGradient(0, 0, 0, sh); g.add_color_stop_rgb(0, *hexc('0F1830')); g.add_color_stop_rgb(1, *hexc('070B16'))
    cr.set_source(g); cr.paint()
    text(cr, "9:41", 36, 38, 17, WHITE, 1, bold=True)
    rrect(cr, 16, 66, sw - 32, 40, 12); rgba(cr, AMBER, .16); cr.fill()
    text(cr, "CONCEPT SIMULATION · ILLUSTRATIVE DATA", sw / 2, 92, 12.5, AMBER, 1, bold=True, align='center', track=.6)
    pi_mark(cr, 42, 142, 16, 1, 1)
    text(cr, "PI StationOS", 68, 138, 15, MUTED, 1, bold=True); text(cr, "Recommendation", 68, 160, 20, WHITE, 1, 'Inter Display', True)
    card(cr, 16, 190, sw - 32, 430, 18, 1, shadow_a=.2)
    text(cr, "SHIFT EXCEPTIONS", 38, 228, 13, GOLD, 1, bold=True, track=1.5)
    y = 262
    for ln in wrap(cr, "Add a 6 PM drawer check on Fridays and Saturdays", 25, sw - 80, 'Inter Display', True):
        text(cr, ln, 38, y, 25, WHITE, 1, 'Inter Display', True); y += 32
    text(cr, "WHY", 38, y + 22, 13, MUTED, 1, bold=True, track=1.5); y += 50
    for ln in wrap(cr, "Two of the last three drawer exceptions were on weekend evenings (sample).", 17, sw - 80):
        text(cr, ln, 38, y, 17, hexc('D9E1EE'), 1); y += 24
    text(cr, "Nothing changes until you decide.", 38, y + 18, 16, CYAN, 1, bold=True)
    # buttons highlight as narration names them
    hl = [fade(t, S("v7", 1, 0), S("v7", 1, .33), .1, .15), fade(t, S("v7", 1, .33), S("v7", 1, .62), .1, .15), fade(t, S("v7", 1, .62), S("v7", 1, 1.0) + .2, .1, .2)]
    by = 520; done = t >= s3 + .55
    if not done:
        button(cr, 32, by, 116, 52, "Approve", GREEN, 1, True, math.exp(-abs(t - (s3 + .35)) * 10) * (t > s3), )
        button(cr, 158, by, 100, 52, "Edit", CYAN, 1, hl=hl[1])
        button(cr, 268, by, 118, 52, "Decline", MUTED, 1, hl=hl[2])
        if hl[0] > 0:
            rrect(cr, 28, by - 4, 124, 60, 30); rgba(cr, WHITE, .8 * hl[0]); cr.set_line_width(3); cr.stroke()
    else:
        k = eout(prog(t, s3 + .55, s3 + 1.0))
        rrect(cr, 32, by, sw - 64, 56, 28); rgba(cr, GREEN, .18 * k); cr.fill()
        check(cr, 64, by + 29, 24, GREEN, k, k)
        text(cr, "Approved by you · 9:41 PM", 90, by + 36, 19, GREEN, k, bold=True)
    text(cr, "Also: energy-drink reorder draft (approved)", 30, 680, 15, MUTED, 1)
    text(cr, "Evening staffing proposal · review", 30, 708, 15, MUTED, 1)
    return s

def ov_phone(cr, t):
    if not (143.6 <= t < 156.6): return
    s1, s2, s3 = S("v7", 1), S("v7", 2), S("v7", 3)
    a = ease(prog(t, 143.8, 144.8)) * (1 - ease(prog(t, 155.6, 156.4)))
    sim_badge(cr, a)
    enter = eout(prog(t, 143.8, 145.4))
    pw, ph = 460, 920; px = 1200; py = 66 + (1 - enter) * 500
    cr.save(); cr.translate(px + pw / 2, py + ph / 2); cr.rotate(lerp(.08, -.02, enter)); cr.scale(.9, .9); cr.translate(-pw / 2, -ph / 2)
    cr.push_group()
    shadow(cr, 0, 0, pw, ph, 66, .7, 60, 40)
    rrect(cr, 0, 0, pw, ph, 66); g = cairo.LinearGradient(0, 0, pw, ph)
    g.add_color_stop_rgb(0, *hexc('454C5E')); g.add_color_stop_rgb(.5, *hexc('171A22')); g.add_color_stop_rgb(1, *hexc('30353F')); cr.set_source(g); cr.fill()
    rrect(cr, 8, 8, pw - 16, ph - 16, 58); rgba(cr, (0, 0, 0)); cr.fill()
    scr = phone_screen(t, s1, s2, s3)
    cr.save(); rrect(cr, 20, 20, 420, 880, 50); cr.clip(); cr.translate(20, 20); cr.scale(.5, .5)
    cr.set_source_surface(scr, 0, 0); cr.get_source().set_filter(cairo.FILTER_GOOD); cr.paint(); cr.restore()
    rrect(cr, pw / 2 - 62, 32, 124, 34, 17); rgba(cr, (0, 0, 0)); cr.fill()
    rg = cairo.LinearGradient(0, 0, pw, ph * .6); rg.add_color_stop_rgba(0, 1, 1, 1, .08); rg.add_color_stop_rgba(.5, 1, 1, 1, 0)
    rrect(cr, 20, 20, 420, 880, 50); cr.set_source(rg); cr.fill()
    ripple(cr, 20 + 90, 20 + 546, t, s3 + .3)
    cr.pop_group_to_source(); cr.paint_with_alpha(a); cr.restore()
    for (s, c, t0, y, sz) in (("Approve.", GREEN, S("v7", 1, 0), 380, 84), ("Edit.", CYAN, S("v7", 1, .33), 480, 84),
                              ("Decline.", WHITE, S("v7", 1, .62), 580, 84)):
        headline_on(cr, s, 130, y, sz, eout(prog(t, t0, t0 + .5)) * a, c)
    headline_on(cr, "You stay informed.", 130, 720, 52, eout(prog(t, s2, s2 + .5)) * a, WHITE, fam='Inter Light', bold=False)
    headline_on(cr, "You stay in control.", 130, 790, 52, eout(prog(t, s3, s3 + .5)) * a, GOLD, fam='Inter Display', bold=True)

# ================================================================ F. invitation
def ov_close(cr, t):
    if t < 156.0: return
    real_tag(cr, fade(t, 156.3, S("v8", 4) - .4, .4, .4))
    s = [S("v8", i) for i in range(7)]
    la = fade(t, s[0] + .2, s[1] - .1, .6, .5)
    if la > 0:
        scrim(cr, 0, 560, W, 520, la, 'bottom')
        headline_on(cr, "A proposed way to run the whole station", 110, 760, 58, la)
        headline_on(cr, "with more clarity and control.", 110, 834, 58, la, CYAN)
    # where PI is designed to help: recap of the three stories (goals, not measured results)
    ra = fade(t, s[1] - .1, s[2] - .1, .5, .5)
    if ra > 0:
        scrim(cr, 0, 0, 1500, H, ra, 'left')
        text(cr, "DESIGNED TO CATCH EARLIER", 110, 300, 22, GOLD, ra, bold=True, track=3)
        rows = [("Empty shelves", "flagged before the cooler runs out"), ("Missed inside sales", "seen next to fuel traffic"), ("Loose ends", "tracked from handoff to done")]
        for j, (a_, b_) in enumerate(rows):
            k = eout(prog(t, s[1] + .3 + j * .9, s[1] + .8 + j * .9)) * ra; y = 350 + j * 130
            card(cr, 110, y, 900, 106, 18, k, shadow_a=.35)
            check(cr, 160, y + 54, 30, GREEN, k, k)
            text(cr, a_, 210, y + 48, 36, WHITE, k, 'Inter Display', True); text(cr, b_, 210, y + 84, 24, hexc('D9E1EE'), k)
        text(cr, "Goals of the concept — no results measured yet", 110, 770, 22, MUTED, ra)
    na = fade(t, s[2], s[4] - .1, .5, .5)
    if na > 0:
        rrect(cr, 110, 700, 1060, 150, 20); rgba(cr, BG, .88 * na); cr.fill_preserve(); rgba(cr, AMBER, .7 * na); cr.set_line_width(2); cr.stroke()
        text(cr, "CONCEPT STAGE", 146, 748, 22, AMBER, na, bold=True, track=3)
        text(cr, "Not connected to this store today. Built with owners.", 146, 808, 36, WHITE, na, 'Inter Display', True)
    ea = ease(prog(t, s[4] - .4, s[4] + .4))
    if ea > 0:
        g = cairo.RadialGradient(W / 2, H / 2, 200, W / 2, H / 2, 1100); g.add_color_stop_rgba(0, *BG, .72 * ea); g.add_color_stop_rgba(1, *BG, .9 * ea)
        cr.set_source(g); cr.paint()
        pi_mark(cr, W / 2, 250, 70, ea, ea)
        wordmark(cr, W / 2, 420, 84, ea)
        for j, (s_, t0, c) in enumerate((("See the concept.", s[4], WHITE), ("Shape the pilot.", s[5], WHITE), ("Ask for a demo.", s[6], GOLD))):
            headline_on(cr, s_, W / 2, 570 + j * 100, 76, eout(prog(t, t0, t0 + .5)), c, 'center', shadow=False)
        text(cr, "Concept stage  ·  interfaces shown are simulations with illustrative data", W / 2, 920, 24, MUTED, ea * .9, align='center')
    end = ease(prog(t, TOTAL - 1.0, TOTAL))
    if end > 0: rgba(cr, (0, 0, 0), end); cr.paint()

OVERLAYS = [ov_open, ov_problem, ov_inventory, ov_picture, ov_shift, ov_phone, ov_close]

# ================================================================ captions (from narration sentences)
def caption_units():
    units = []
    for m in VO.values():
        for s in m["sentences"]:
            words = s["text"].split(); n = len(words)
            if n <= 14: chunks = [words]
            else:  # split at the comma/colon nearest the middle, else at the middle
                cands = [i + 1 for i, w in enumerate(words[:-2]) if w[-1] in ",:;" and i >= 3]
                k = min(cands, key=lambda i: abs(i - n / 2)) if cands and abs(min(cands, key=lambda i: abs(i - n / 2)) - n / 2) < n * .3 else math.ceil(n / 2)
                chunks = [words[:k], words[k:]]
            tot = sum(len(' '.join(c)) for c in chunks); t = s["start"]
            for c in chunks:
                d = (s["end"] - s["start"]) * len(' '.join(c)) / tot
                units.append((t, t + d, ' '.join(c))); t += d
    return units
def _mirrored(a):
    return any(S(v, i) - .05 <= a < VO[v]["sentences"][i]["end"] for (v, i) in (("v7", 1), ("v7", 2), ("v7", 3), ("v8", 0), ("v8", 2), ("v8", 4), ("v8", 5), ("v8", 6)))
CAPS = [c for c in caption_units() if not _mirrored(c[0])]

def draw_captions(cr, t):
    for (a, b, s) in CAPS:
        if a - .05 <= t < b + .15:
            al = min(1, (t - a + .05) / .12, (b + .15 - t) / .15)
            lines = wrap(cr, s, 44, 1500, 'Inter SemiBold')
            font(cr, 44, 'Inter SemiBold'); wmax = max(text_w(cr, l) for l in lines)
            hh = len(lines) * 58 + 26; y0 = H - 44 - hh
            rrect(cr, W / 2 - wmax / 2 - 28, y0, wmax + 56, hh, 14); rgba(cr, (0, 0, 0), .66 * al); cr.fill()
            for i, l in enumerate(lines): text(cr, l, W / 2, y0 + 56 + i * 58, 44, WHITE, al, 'Inter SemiBold', align='center')
            break
