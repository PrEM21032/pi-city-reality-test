import cairo, math
from lib import *
import exterior as E

LB = 138  # letterbox bar height (2.39:1) for exterior shots

def letterbox(cr, a=1.0, note=None):
    rgba(cr, (0, 0, 0), a); cr.rectangle(0, 0, W, LB * a); cr.fill(); cr.rectangle(0, H - LB * a, W, LB * a); cr.fill()
    if note: text(cr, note, 80, H - LB * a + 78, 19, MUTED, 0.85 * a, track=2)

def corner_tag(cr, s, a=1.0):
    text(cr, s, W - 80, 64, 17, MUTED, 0.8 * a, align='right', track=2.2, bold=True)

def ui_bg(cr, t, a=1.0, hue=CYAN):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, *BG2); g.add_color_stop_rgb(1, *BG)
    cr.set_source(g); cr.paint()
    # perspective floor grid drifting
    cr.save(); cr.set_line_width(1)
    hy = 640
    for i in range(-24, 25):
        rgba(cr, hue, 0.05); cr.move_to(W / 2 + i * 26, hy); cr.line_to(W / 2 + i * 260, H); cr.stroke()
    off = (t * 0.35) % 1
    for j in range(12):
        z = (j + off); y = hy + (H - hy) * (z / 12) ** 2.2
        rgba(cr, hue, 0.06 * (z / 12)); cr.move_to(0, y); cr.line_to(W, y); cr.stroke()
    cr.restore()
    R = rng(3)
    for i in range(14):  # bokeh
        x = (R.random() * W + t * (6 + R.random() * 14)) % (W + 400) - 200
        y = R.random() * H; r = 60 + R.random() * 160
        glow(cr, x, y, r, CYAN if i % 3 else VIOLET, 0.05 + 0.04 * math.sin(t * .7 + i))

def headline(cr, s, x, y, size, a, rise=None, color=WHITE, align='left', fam='Inter Display', bold=True, track=0.0):
    off = 0 if rise is None else (1 - eout(rise)) * 30
    text(cr, s, x, y + off, size, color, a, fam, bold, align, track)

# ============ SCENE 1: night exterior + challenges (0-15.8) ============
ALERTS = [
    (4.6, AMBER, 'warn', 'PUMP 4', 'Receipt printer offline — customers waiting'),
    (6.4, RED, 'warn', 'COOLER 3', 'Energy drinks: 6 units left'),
    (8.4, AMBER, 'warn', 'REGISTER', '7 customers in line'),
    (9.9, RED, 'warn', 'DRAWER 1', 'Cash count off by $38.50'),
    (11.0, AMBER, 'warn', 'DIESEL TANK', '22% — delivery not scheduled'),
]

def s1(cr, t):
    e = einout(prog(t, 0, 16))
    cam = E.Cam(lerp(-6.5, -2, e), lerp(2.0, 2.9, e), lerp(-14, -6.5, e), 1500, lerp(640, 600, e))
    E.draw(cr, t, cam, 0.0, 1.0)
    # alerts overwhelm
    shake = ease(prog(t, 11.6, 13.5))
    for i, (t0, c, kind, ttl, body) in enumerate(ALERTS):
        a = eout(prog(t, t0, t0 + .5)) * (1 - ease(prog(t, 14.6, 15.4)))
        if a <= 0: continue
        x = 1210 + (1 - eout(prog(t, t0, t0 + .6))) * 220 + math.sin(t * 31 + i * 2) * 3 * shake
        y = 200 + i * 104
        card(cr, x, y, 610, 86, 16, a, glow=c if (t - t0) < 1.0 else None)
        icon_dot(cr, x + 44, y + 43, 20, c, a, kind)
        text(cr, ttl, x + 84, y + 36, 17, c, a, bold=True, track=2)
        text(cr, body, x + 84, y + 66, 23, WHITE, a * .92)
        pulse = (t - t0) % 1.6 / 1.6
        cr.arc(x + 44, y + 43, 20 + pulse * 18, 0, 6.283); rgba(cr, c, a * .5 * (1 - pulse)); cr.set_line_width(2); cr.stroke()
    # location super
    la = fade(t, 1.4, 7.2, .8, .8)
    if la > 0:
        x, y = 120, 740
        rgba(cr, CYAN, la); cr.rectangle(x, y - 62, 70 * eout(prog(t, 1.4, 2.4)), 3); cr.fill()
        text(cr, 'IRVINGTON CHEVRON', x, y - 14, 40, WHITE, la, 'Inter Display', True, track=6)
        text(cr, '9436 Irvington Bayou La Batre Hwy  ·  Irvington, Alabama', x, y + 26, 24, hexc('C8D2E2'), la * .9)
        text(cr, '6:00 AM', x, y + 66, 22, CYAN, la * .9, 'DejaVu Sans Mono', True, track=2)
    # closing headline
    ha = fade(t, 11.8, 15.6, .7, .6)
    if ha > 0:
        g = cairo.LinearGradient(0, 520, 0, 942); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(.55, *BG, .78 * ha); g.add_color_stop_rgba(1, *BG, .9 * ha)
        cr.set_source(g); cr.rectangle(0, 520, W, 422); cr.fill()
    headline(cr, 'Every number in this store', 120, 720, 64, ha, prog(t, 11.8, 12.6))
    headline(cr, 'needs your attention.', 120, 800, 64, ha, prog(t, 12.2, 13.0), CYAN)
    letterbox(cr, 1.0, 'CONCEPT RENDERING — NOT ACTUAL STORE FOOTAGE')

# ============ SCENE 2: introduce PI (15-30.8) ============
MODULES = ['Inventory', 'Fuel', 'Cash', 'Staff', 'Suppliers', 'Approvals']

def s2(cr, t):
    lt = t - 15
    zoom = 1 + ein(prog(t, 28.6, 30.8)) * 1.6
    ui_bg(cr, t, 1.0)
    cr.save(); cr.translate(W / 2, 470); cr.scale(zoom, zoom); cr.translate(-W / 2, -470)
    # converging particles
    R = rng(11)
    pc = eout(prog(t, 15.0, 16.4))
    for i in range(140):
        ang = R.random() * 6.283; d0 = 500 + R.random() * 700
        d = lerp(d0, 150 + R.random() * 8, pc) + (math.sin(t * 2 + i) * 6 if pc >= 1 else 0)
        x = W / 2 + math.cos(ang + lt * 0.15) * d; y = 470 + math.sin(ang + lt * 0.15) * d * 0.85
        a = (0.2 + 0.6 * R.random()) * (1 - ease(prog(t, 16.2, 17.2)) * 0.8)
        rgba(cr, CYAN if i % 4 else VIOLET, a); cr.arc(x, y, 1.5 + R.random() * 2, 0, 6.283); cr.fill()
    ring = eout(prog(t, 15.9, 17.0))
    flash = math.exp(-max(t - 16.9, 0) * 4) * (t > 16.9)
    cr.set_operator(cairo.OPERATOR_ADD); glow(cr, W / 2, 470, 520, CYAN, 0.5 * flash); cr.set_operator(cairo.OPERATOR_OVER)
    pi_mark(cr, W / 2, 470, 130, ring, 1.0 if ring > 0 else 0, ease(prog(t, 16.7, 17.3)))
    wm = eout(prog(t, 17.1, 18.1))
    wordmark(cr, W / 2, 720 + (1 - wm) * 20, 92, wm, track=lerp(14, 2, wm))
    sa = eout(prog(t, 18.6, 19.6))
    text(cr, 'AI-POWERED GAS STATION OPERATIONS MANAGER', W / 2, 790, 26, CYAN, sa, bold=True, align='center', track=6)
    # orbiting module chips
    for i, m in enumerate(MODULES):
        ca = eout(prog(t, 21.0 + i * .35, 21.6 + i * .35))
        if ca <= 0: continue
        ang = math.radians((-150, 180, 150, -30, 0, 30)[i] + math.sin(lt * .4 + i) * 4)
        rx, ry = 470 * ca, 210 * ca
        x = W / 2 + math.cos(ang) * (rx + 0); y = 470 + math.sin(ang) * ry
        cr.move_to(W / 2 + math.cos(ang) * 160, 470 + math.sin(ang) * 140); cr.line_to(x, y)
        rgba(cr, CYAN, 0.18 * ca); cr.set_line_width(1.2); cr.stroke()
        chip(cr, m.upper(), x, y, 19, CYAN if i != 5 else GOLD, ca, 'center', fill_a=0.18)
    la = eout(prog(t, 24.0, 25.0))
    text(cr, 'Built for one store.  Watching every detail.', W / 2, 880, 34, WHITE, la * .9, 'Inter Light', align='center')
    cr.restore()
    corner_tag(cr, 'PI STATIONOS · CONCEPT', 1 - ease(prog(t, 28.6, 29.5)))
    if t < 16.0:  # fade from black
        rgba(cr, (0, 0, 0), 1 - ease(prog(t, 15.0, 16.0))); cr.paint()

# ============ dashboard chrome ============
def topbar(cr, title, t, a=1.0):
    rgba(cr, hexc('0A1020'), 0.85 * a); cr.rectangle(0, 0, W, 92); cr.fill()
    rgba(cr, WHITE, 0.07 * a); cr.rectangle(0, 92, W, 1); cr.fill()
    pi_mark(cr, 70, 46, 20, 1, a)
    text(cr, 'PI', 104, 56, 26, CYAN, a, 'Inter Display', True)
    text(cr, 'StationOS', 140, 56, 26, WHITE, a, 'Inter Display Light')
    text(cr, '/  ' + title, 290, 56, 22, MUTED, a)
    text(cr, 'Irvington Chevron  ·  Mon 6:04 AM', W - 360, 56, 20, hexc('B9C3D4'), a, align='right')
    chip(cr, 'SAMPLE DATA · ILLUSTRATIVE', W - 70, 46, 15, AMBER, a, 'right', fill_a=0.12)

def panel(cr, x, y, w, h, title, sub, a, focus=1.0, accent=CYAN):
    aa = a * lerp(0.35, 1.0, focus)
    card(cr, x, y, w, h, 26, aa, glow=accent if focus > .95 else None)
    rgba(cr, accent, aa); cr.rectangle(x + 34, y + 34, 4, 46); cr.fill()
    text(cr, title, x + 54, y + 62, 34, WHITE, aa, 'Inter Display', True)
    text(cr, sub, x + 54, y + 96, 20, MUTED, aa)
    return aa

def campan(cr, focuses, t):
    """Pan/zoom virtual camera between (time, cx, cy, zoom) keys."""
    ks = focuses
    for i in range(len(ks) - 1):
        if ks[i][0] <= t < ks[i + 1][0]:
            k = einout(prog(t, ks[i][0], ks[i + 1][0]))
            c = [lerp(ks[i][j], ks[i + 1][j], k) for j in (1, 2, 3)]; break
    else:
        c = list(ks[0][1:]) if t < ks[0][0] else list(ks[-1][1:])
    cr.translate(W / 2, H / 2 + 46); cr.scale(c[2], c[2]); cr.translate(-c[0], -c[1])

# ============ SCENE 3: sales, forecast, supplier order (30-50.8) ============
SALES = [('Energy drinks', 0.92, '+41%', RED), ('Bagged ice', 0.78, '+38%', AMBER), ('Bottled water', 0.66, '+12%', CYAN),
         ('Hot food', 0.55, '+4%', CYAN), ('Coffee', 0.48, '−2%', CYAN), ('Snacks', 0.42, '+3%', CYAN)]
ORDER = [('Energy drink 16oz (24ct)', '6', '58', '3 cases'), ('Bagged ice 10 lb', '14', '96', '90 bags'),
         ('Bottled water 16.9oz (24pk)', '9', '31', '2 cases'), ('Sweet tea 18.5oz (12ct)', '11', '20', '1 case')]

def s3(cr, t):
    ui_bg(cr, t)
    a_in = ease(prog(t, 30.0, 31.0))
    cr.save()
    campan(cr, [(30.0, 560, 520, 1.25), (31.5, 560, 520, 1.18), (35.2, 560, 520, 1.12), (36.6, 1360, 520, 1.12),
                (40.2, 1360, 520, 1.1), (41.6, 960, 830, 1.0), (47.5, 960, 810, 0.98), (50.8, 960, 700, 0.8)], t)
    fA = 1 - ease(prog(t, 35.4, 36.4)) * 0.9 + ease(prog(t, 47.0, 48.0)) * 0.9
    fB = ease(prog(t, 35.4, 36.4)) - ease(prog(t, 40.4, 41.4)) * 0.9 + ease(prog(t, 47.0, 48.0)) * 0.9
    fC = ease(prog(t, 40.4, 41.4))
    # Panel A: product sales
    x, y, w, h = 130, 200, 820, 560
    aa = panel(cr, x, y, w, h, 'Product sales', 'Units sold · last 7 days vs. normal', a_in, fA)
    for i, (n, v, d, c) in enumerate(SALES):
        by = y + 160 + i * 64; g = eout(prog(t, 31.2 + i * .25, 32.6 + i * .25))
        text(cr, n, x + 54, by + 26, 22, WHITE, aa)
        rrect(cr, x + 270, by + 6, 420, 26, 13); rgba(cr, WHITE, .06 * aa); cr.fill()
        rrect(cr, x + 270, by + 6, max(26, 420 * v * g), 26, 13)
        lg = cairo.LinearGradient(x + 270, 0, x + 690, 0); lg.add_color_stop_rgba(0, *c, .5 * aa); lg.add_color_stop_rgba(1, *c, aa)
        cr.set_source(lg); cr.fill()
        text(cr, d, x + w - 50, by + 27, 22, c if c != CYAN else MUTED, aa * g, bold=True, align='right')
    hl = fade(t, 33.6, 36.0, .4, .4) * aa
    if hl > 0:
        rrect(cr, x + 36, y + 150, w - 72, 132, 14); rgba(cr, RED, .5 * hl); cr.set_line_width(2.5); cr.stroke()
        chip(cr, 'SELLING FASTER THAN USUAL', x + w - 54, y + 128, 15, RED, hl, 'right')
    # Panel B: forecast
    x, y, w, h = 1010, 200, 780, 560
    ab = panel(cr, x, y, w, h, 'Shortage forecast', 'Energy drink 16oz · on-hand units', a_in, fB, RED)
    gx, gy, gw, gh = x + 60, y + 150, w - 120, 300
    cr.set_line_width(1)
    for j in range(5):
        rgba(cr, WHITE, .06 * ab); cr.move_to(gx, gy + gh * j / 4); cr.line_to(gx + gw, gy + gh * j / 4); cr.stroke()
    hist = [72, 66, 61, 58, 51, 47, 42, 36, 31, 26, 20, 15, 10, 6]
    fc = [6, 2, 0]
    def pt(i, v): return gx + gw * i / 16, gy + gh * (1 - v / 80)
    rp = gy + gh * (1 - 18 / 80)  # reorder point
    cr.set_dash([8, 8]); rgba(cr, AMBER, .6 * ab); cr.move_to(gx, rp); cr.line_to(gx + gw, rp); cr.stroke(); cr.set_dash([])
    text(cr, 'Reorder point', gx + gw, rp - 10, 16, AMBER, .8 * ab, align='right')
    dp = prog(t, 36.2, 38.4)
    cr.save(); cr.rectangle(gx - 10, gy - 20, (gw + 20) * eout(dp), gh + 40); cr.clip()
    for i, v in enumerate(hist): (cr.move_to if i == 0 else cr.line_to)(*pt(i, v))
    rgba(cr, CYAN, ab); cr.set_line_width(4); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke()
    cr.move_to(*pt(13, 6))
    for i, v in enumerate(fc): cr.line_to(*pt(13 + i + 1, v))
    cr.set_dash([10, 8]); rgba(cr, RED, ab); cr.stroke(); cr.set_dash([])
    cr.restore()
    for lab, i in (('Mon', 0), ('Wed', 4), ('Fri', 8), ('Sun', 12), ('Thu', 16)):
        text(cr, lab, pt(i, 0)[0], gy + gh + 34, 17, MUTED, ab, align='center')
    sa = eout(prog(t, 38.4, 39.0)) * ab
    if sa > 0:
        px, py = pt(16, 0); pulse = (t * 1.2) % 1
        cr.arc(px, py, 10 + 22 * pulse, 0, 6.283); rgba(cr, RED, sa * (1 - pulse) * .7); cr.set_line_width(2); cr.stroke()
        cr.arc(px, py, 9, 0, 6.283); rgba(cr, RED, sa); cr.fill()
        card(cr, gx + gw - 420, gy - 10, 380, 96, 16, sa, fill=hexc('2A1018'), glow=RED, shadow_a=.2)
        text(cr, 'PREDICTED STOCKOUT', gx + gw - 396, gy + 26, 16, RED, sa, bold=True, track=2)
        text(cr, 'Thursday, ~2:00 PM', gx + gw - 396, gy + 66, 30, WHITE, sa, 'Inter Display', True)
    # Panel C: supplier order draft
    x, y, w, h = 230, 820, 1460, 430
    ac = panel(cr, x, y, w, h, 'Supplier order — prepared by PI', 'Suggested quantities from sales velocity and forecast', a_in * ease(prog(t, 39.5, 41)), fC, GOLD)
    if ac > 0:
        chip(cr, 'DRAFT · AWAITING OWNER APPROVAL', x + w - 50, y + 64, 17, GOLD, ac * eout(prog(t, 44.5, 45.3)), 'right')
        cols = [x + 54, x + 760, x + 960, x + 1210]
        for j, hd in enumerate(('ITEM', 'ON HAND', '7-DAY FORECAST', 'SUGGESTED ORDER')):
            text(cr, hd, cols[j], y + 160, 16, MUTED, ac, bold=True, track=2)
        for i, row in enumerate(ORDER):
            ra = eout(prog(t, 41.6 + i * .55, 42.2 + i * .55)) * ac
            ry = y + 190 + i * 56 + (1 - ra) * 16
            rgba(cr, WHITE, .05 * ra); cr.rectangle(x + 40, ry - 4, w - 80, 1); cr.fill()
            text(cr, row[0], cols[0], ry + 38, 24, WHITE, ra)
            text(cr, row[1], cols[1], ry + 38, 24, RED if i == 0 else WHITE, ra, 'DejaVu Sans Mono')
            text(cr, row[2], cols[2], ry + 38, 24, WHITE, ra, 'DejaVu Sans Mono')
            text(cr, row[3], cols[3], ry + 38, 24, GOLD, ra, bold=True)
    cr.restore()
    topbar(cr, 'Inventory & Ordering', t, a_in)

# ============ SCENE 4: fuel, cash, tasks (50-70.8) ============
TANKS = [('Regular', 0.64, 3182, CYAN), ('Plus', 0.48, 612, CYAN), ('Premium', 0.41, 488, CYAN), ('Diesel', 0.22, 1145, RED)]
TASKS = [('Restock cooler 3', 'Maria · 6:15 AM', 58.8), ('Clean restrooms', 'James · 6:20 AM', 60.0),
         ('Pump 4 printer', 'Service call · shift lead', None), ('Refresh coffee station', 'Maria · 6:45 AM', None)]

def money(v): return f"${v:,.2f}"

def s4(cr, t):
    ui_bg(cr, t, 1, VIOLET)
    a_in = ease(prog(t, 50.0, 51.0))
    cr.save()
    campan(cr, [(50.0, 470, 560, 1.2), (53.8, 470, 560, 1.16), (55.0, 1110, 560, 1.16), (58.6, 1110, 560, 1.14),
                (59.8, 1650, 560, 1.12), (64.5, 1650, 560, 1.1), (66.0, 1000, 600, 0.86), (70.8, 1000, 600, 0.83)], t)
    f1 = 1 - ease(prog(t, 54.0, 55.0)) * .9 + ease(prog(t, 64.6, 65.6)) * .9
    f2 = ease(prog(t, 54.0, 55.0)) - ease(prog(t, 59.0, 60.0)) * .9 + ease(prog(t, 64.6, 65.6)) * .9
    f3 = ease(prog(t, 59.0, 60.0))
    # Fuel panel
    x, y, w, h = 80, 200, 780, 720
    a1 = panel(cr, x, y, w, h, 'Fuel sales by grade', 'Gallons today · tank level', a_in, f1)
    for i, (n, lvl, gal, c) in enumerate(TANKS):
        tx = x + 70 + i * 178; ty = y + 170; tw, th = 120, 340
        g = eout(prog(t, 50.6 + i * .2, 52.4 + i * .2))
        rrect(cr, tx, ty, tw, th, 22); rgba(cr, WHITE, .05 * a1); cr.fill_preserve(); rgba(cr, WHITE, .12 * a1); cr.set_line_width(1.5); cr.stroke()
        fh = th * lvl * g; cr.save(); rrect(cr, tx, ty, tw, th, 22); cr.clip()
        cr.move_to(tx, ty + th)
        for k in range(0, 41):
            xx = tx + tw * k / 40; cr.line_to(xx, ty + th - fh + math.sin(k / 40 * 6.28 + t * 2.4 + i) * 4)
        cr.line_to(tx + tw, ty + th); cr.close_path()
        lg = cairo.LinearGradient(0, ty, 0, ty + th); lg.add_color_stop_rgba(0, *c, .9 * a1); lg.add_color_stop_rgba(1, *c, .35 * a1)
        cr.set_source(lg); cr.fill(); cr.restore()
        text(cr, f"{int(lvl * 100 * g)}%", tx + tw / 2, ty + 50, 30, WHITE, a1, 'Inter Display', True, 'center')
        text(cr, n, tx + tw / 2, ty + th + 44, 22, WHITE, a1, bold=True, align='center')
        text(cr, f"{int(gal * g):,} gal", tx + tw / 2, ty + th + 78, 20, MUTED, a1, 'DejaVu Sans Mono', align='center')
    da = eout(prog(t, 52.8, 53.4)) * a1
    chip(cr, 'DIESEL LOW · DELIVERY SUGGESTED', x + 54, y + h - 60, 17, RED, da)
    # Cash panel
    x, y, w, h = 920, 200, 400, 720
    a2 = panel(cr, x, y, w, h, 'Cash drawer', 'Shift 2 · Drawer 1', a_in, f2, AMBER)
    c = eout(prog(t, 54.6, 56.4))
    rows = [('Expected', 4812.40 * c, WHITE), ('Counted', 4773.90 * eout(prog(t, 55.2, 57.0)), WHITE)]
    for i, (lab, v, col) in enumerate(rows):
        text(cr, lab.upper(), x + 54, y + 180 + i * 130, 16, MUTED, a2, bold=True, track=2)
        if v > 0: text(cr, money(v), x + 54, y + 232 + i * 130, 46, col, a2, 'Inter Display', True)
    va = eout(prog(t, 57.0, 57.6)) * a2
    if va > 0:
        vy = y + 450
        card(cr, x + 36, vy, w - 72, 190, 18, va, fill=hexc('2A1E0C'), glow=AMBER, shadow_a=.15)
        text(cr, 'VARIANCE', x + 64, vy + 46, 16, AMBER, va, bold=True, track=2)
        text(cr, '−$38.50', x + 64, vy + 104, 50, AMBER, va, 'Inter Display', True)
        text(cr, 'Flagged for owner review', x + 64, vy + 150, 20, WHITE, va * .85)
    # Tasks panel
    x, y, w, h = 1380, 200, 540, 720
    a3 = panel(cr, x, y, w, h, 'Shift tasks', 'Morning shift · 6:00 AM – 2:00 PM', a_in, f3, GREEN)
    for i, (n, who, done) in enumerate(TASKS):
        ra = eout(prog(t, 59.4 + i * .3, 60.0 + i * .3)) * a3; ty = y + 160 + i * 120
        card(cr, x + 34, ty, w - 68, 100, 16, ra, shadow_a=0)
        dp = prog(t, done, done + .5) if done else 0
        cr.arc(x + 82, ty + 50, 20, 0, 6.283); rgba(cr, GREEN if dp > 0 else MUTED, (.25 + .6 * (dp > 0)) * ra); cr.set_line_width(2); cr.stroke()
        if dp > 0:
            cr.arc(x + 82, ty + 50, 20, 0, 6.283); rgba(cr, GREEN, .2 * ra); cr.fill()
            check(cr, x + 82, ty + 52, 20, GREEN, ra, eout(dp))
        text(cr, n, x + 124, ty + 46, 23, WHITE, ra * (1 - .4 * clamp(dp)))
        text(cr, who, x + 124, ty + 76, 18, MUTED, ra)
        if i == 2 and t > 61.4: chip(cr, 'ESCALATED', x + w - 60, ty + 50, 13, AMBER, ra * ease(prog(t, 61.4, 61.9)), 'right')
    pa = eout(prog(t, 61.8, 62.6)) * a3
    text(cr, '2 done  ·  1 escalated  ·  1 upcoming', x + 54, y + h - 50, 22, GREEN, pa, bold=True)
    cr.restore()
    topbar(cr, 'Fuel · Cash · Staff', t, a_in)
    # overview caption
    oa = fade(t, 66.2, 70.8, .7, .5)
    if oa > 0:
        g = cairo.LinearGradient(0, H - 260, 0, H); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, *BG, .95 * oa)
        cr.set_source(g); cr.rectangle(0, H - 260, W, 260); cr.fill()
        headline(cr, 'One view of the whole store — every shift.', W / 2, H - 80, 48, oa, prog(t, 66.2, 67.0), align='center')

# ============ SCENE 5: phone approvals (70-90.8) ============
RECS = [('SUPPLIER ORDER', '4 items · $1,284.60', GOLD, 'Energy drinks selling 2.1× normal; stockout predicted Thursday 2 PM.'),
        ('CASH VARIANCE', 'Drawer 1 · −$38.50', AMBER, 'Count is $38.50 below expected for shift 2.'),
        ('DIESEL DELIVERY', 'Tank at 22%', RED, 'At current pace, below 10% by Wednesday.'),
        ('PUMP 4 PRINTER', 'Service call', CYAN, 'Offline since 5:42 AM; 11 receipts reprinted.')]

def phone_screen(t):
    sw, sh = 400, 860
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw * 2, sh * 2); cr = cairo.Context(s); cr.set_font_options(lib_fo())
    cr.scale(2, 2)
    g = cairo.LinearGradient(0, 0, 0, sh); g.add_color_stop_rgb(0, *hexc('0E1730')); g.add_color_stop_rgb(1, *hexc('070B16'))
    cr.set_source(g); cr.paint()
    text(cr, '6:07', 34, 34, 16, WHITE, 1, bold=True)
    text(cr, '•••  100%', sw - 30, 34, 13, WHITE, .8, align='right')
    pi_mark(cr, 46, 92, 16, 1, 1)
    text(cr, 'Good morning', 72, 88, 15, MUTED)
    text(cr, 'Irvington Chevron', 72, 108, 18, WHITE, 1, 'Inter Display', True)
    pending = 4 - (t > 80.0) - (t > 84.6)
    text(cr, f'{pending} recommendations need you', 26, 160, 17, CYAN, 1, bold=True)
    y = 184
    for i, (ttl, sub, c, why) in enumerate(RECS):
        ca = eout(prog(t, 72.6 + i * .3, 73.2 + i * .3))
        if ca <= 0: continue
        expanded = i == 0 and 74.6 < t
        ex = eout(prog(t, 74.6, 75.3)) if i == 0 else 0
        h = 92 + 170 * ex
        approved = (i == 0 and t > 80.0) or (i == 1 and t > 84.6)
        cc = GREEN if approved else c
        card(cr, 16, y + (1 - ca) * 20, sw - 32, h, 16, ca, glow=cc if (i == 0 and 74.6 < t < 81.5) or (i == 1 and 82.5 < t < 85.6) else None, shadow_a=.2)
        rgba(cr, cc, ca); rrect(cr, 16, y + 18, 4, 56, 2); cr.fill()
        text(cr, ttl, 36, y + 38, 12, cc, ca, bold=True, track=1.6)
        text(cr, sub, 36, y + 66, 19, WHITE, ca, 'Inter Display', True)
        if approved:
            ap = eout(prog(t, 80.0 if i == 0 else 84.6, (80.0 if i == 0 else 84.6) + .4))
            chip(cr, 'APPROVED' if i == 0 else 'REVIEW ASSIGNED', sw - 30, y + 46, 11, GREEN, ca * ap, 'right', pad=10)
        if ex > 0:
            cr.save(); cr.rectangle(16, y + 80, sw - 32, h - 80); cr.clip()
            text(cr, 'WHY PI RECOMMENDS THIS', 36, y + 108, 11, MUTED, ex, bold=True, track=1.5)
            words = why.split(); line = ''; ly = y + 134
            font(cr, 15)
            for wd in words:
                if text_w(cr, line + ' ' + wd) > sw - 90: text(cr, line.strip(), 36, ly, 15, WHITE, ex * .9); ly += 22; line = ''
                line += ' ' + wd
            text(cr, line.strip(), 36, ly, 15, WHITE, ex * .9)
            for j, (lab, bc) in enumerate((('Approve', GREEN), ('Edit', CYAN), ('Decline', MUTED))):
                bx = 32 + j * 118; by = y + 196
                press = 1 - .08 * math.exp(-abs(t - 79.8) * 12) if j == 0 else 1
                rrect(cr, bx, by, 106 * press, 44, 22)
                rgba(cr, bc, (.95 if j == 0 else .16) * ex); cr.fill()
                text(cr, lab, bx + 53, by + 28, 15, BG if j == 0 else bc, ex, bold=True, align='center')
            cr.restore()
        y += h + 12
    # notification banner
    na = fade(t, 72.0, 74.4, .4, .5)
    if na > 0:
        by = -80 + 104 * eback(prog(t, 72.0, 72.5))
        card(cr, 12, by, sw - 24, 72, 18, na, fill=hexc('1C2742'), shadow_a=.4)
        pi_mark(cr, 44, by + 36, 14, 1, na)
        text(cr, 'PI StationOS', 70, by + 30, 13, MUTED, na, bold=True)
        text(cr, '4 recommendations ready for review', 70, by + 52, 15, WHITE, na)
    return s

def lib_fo():
    import lib; return lib._FO

def s5(cr, t):
    ui_bg(cr, t, 1, GOLD)
    enter = eout(prog(t, 70.2, 72.0)); exit_ = ein(prog(t, 88.5, 90.8))
    px = lerp(1240, 1180, ease(prog(t, 72, 88))) ; py = 120 + (1 - enter) * 700 - exit_ * 60
    rot = lerp(0.10, -0.035, enter) + math.sin(t * .6) * .008
    sc = lerp(0.98, 1.0, ease(prog(t, 72, 88))) * (1 + exit_ * .25)
    pw, ph = 440, 900
    cr.save()
    cr.translate(px + pw / 2, py + ph / 2); cr.rotate(rot); cr.scale(sc, sc); cr.translate(-pw / 2, -ph / 2)
    shadow(cr, 0, 0, pw, ph, 64, .6 * enter, 60, 40)
    rrect(cr, 0, 0, pw, ph, 64); g = cairo.LinearGradient(0, 0, pw, ph)
    g.add_color_stop_rgb(0, *hexc('3A4152')); g.add_color_stop_rgb(.5, *hexc('15181F')); g.add_color_stop_rgb(1, *hexc('2B303C'))
    cr.set_source(g); cr.fill()
    rrect(cr, 8, 8, pw - 16, ph - 16, 57); rgba(cr, (0, 0, 0)); cr.fill()
    scr = phone_screen(t)
    cr.save(); rrect(cr, 20, 20, 400, 860, 48); cr.clip(); cr.translate(20, 20); cr.scale(.5, .5)
    cr.set_source_surface(scr, 0, 0); cr.get_source().set_filter(cairo.FILTER_GOOD); cr.paint(); cr.restore()
    rrect(cr, pw / 2 - 62, 34, 124, 34, 17); rgba(cr, (0, 0, 0)); cr.fill()
    # glass reflection
    rg = cairo.LinearGradient(0, 0, pw, ph * .6); rg.add_color_stop_rgba(0, 1, 1, 1, .10); rg.add_color_stop_rgba(.45, 1, 1, 1, 0)
    rrect(cr, 20, 20, 400, 860, 48); cr.set_source(rg); cr.fill()
    # tap ripples (screen coordinates: approve button)
    for (tt0, bx, by) in ((79.75, 20 + 32 + 53, 20 + 184 + 196 + 22), (84.4, 20 + 200, 20 + 184 + 262 + 12 + 46)):
        rp = prog(t, tt0, tt0 + .6)
        if 0 < rp < 1:
            cr.arc(bx, by, 14 + 50 * eout(rp), 0, 6.283); rgba(cr, WHITE, .6 * (1 - rp)); cr.set_line_width(3); cr.stroke()
            cr.arc(bx, by, 16, 0, 6.283); rgba(cr, WHITE, .35 * (1 - rp)); cr.fill()
    cr.restore()
    # left copy
    a = 1 - ease(prog(t, 88.4, 89.6))
    rows = [(71.4, 'It comes to you.', WHITE, 80), (73.8, 'See what PI found — and why.', hexc('C8D2E2'), 40),
            (77.6, 'Approve.  Edit.  Decline.', GOLD, 58), (81.2, 'One tap. Your call.', WHITE, 40)]
    yy = 380
    for (t0, s, c, sz) in rows:
        ra = eout(prog(t, t0, t0 + .7)) * a
        headline(cr, s, 140, yy, sz, ra, prog(t, t0, t0 + .7), c, fam='Inter Display' if sz > 50 else 'Inter Light', bold=sz > 50)
        yy += sz + 46
    corner_tag(cr, 'CONCEPT APP SCREENS · SAMPLE DATA', ease(prog(t, 70.5, 71.5)) * a)

# ============ SCENE 6: workflow + verification (90-105.8) ============
NODES = [('Detect', CYAN), ('Analyze', CYAN), ('Recommend', CYAN), ('You approve', GOLD), ('Execute', VIOLET), ('Verify', GREEN), ('Log', GREEN)]

def s6(cr, t):
    ui_bg(cr, t, 1, VIOLET)
    a_in = ease(prog(t, 90.0, 91.0))
    sc = lerp(1.06, 1.0, ease(prog(t, 90, 104)))
    cr.save(); cr.translate(W / 2, H / 2); cr.scale(sc, sc); cr.translate(-W / 2, -H / 2)
    headline(cr, 'Automated workflows. Owner in control.', W / 2, 190, 52, a_in * (1 - ease(prog(t, 98.8, 99.4))), prog(t, 90.2, 91.0), align='center')
    xs = [240 + i * 240 for i in range(7)]; ny = 430
    for i in range(6):  # connectors with travelling pulses
        ca = eout(prog(t, 91.0 + i * .5, 91.6 + i * .5))
        x0, x1 = xs[i] + 62, xs[i + 1] - 62
        rgba(cr, WHITE, .14 * ca); cr.set_line_width(3); cr.move_to(x0, ny); cr.line_to(lerp(x0, x1, ca), ny); cr.stroke()
        if ca >= 1:
            gate = i >= 3 and t < 95.6  # nothing moves past approval until approved
            if not gate:
                for k in range(2):
                    p = ((t * 0.9 + k * .5 + i * .13) % 1)
                    cr.set_operator(cairo.OPERATOR_ADD); glow(cr, lerp(x0, x1, p), ny, 22, NODES[i + 1][1], .8); cr.set_operator(cairo.OPERATOR_OVER)
    for i, (lab, c) in enumerate(NODES):
        na = eback(prog(t, 90.8 + i * .5, 91.4 + i * .5)) ; aa = clamp(prog(t, 90.8 + i * .5, 91.2 + i * .5))
        if aa <= 0: continue
        r = (70 if i == 3 else 52) * na
        if i == 3:
            pr = (t * .8) % 1
            cr.arc(xs[i], ny, r + pr * 40, 0, 6.283); rgba(cr, GOLD, .5 * (1 - pr) * aa); cr.set_line_width(2); cr.stroke()
        glow(cr, xs[i], ny, r * 2.2, c, .25 * aa)
        cr.arc(xs[i], ny, r, 0, 6.283); rgba(cr, mix(BG2, c, .18), aa); cr.fill_preserve(); rgba(cr, c, aa); cr.set_line_width(3); cr.stroke()
        if i == 3:
            ok = eout(prog(t, 95.4, 95.9))
            # lock -> check
            if ok < 1:
                rgba(cr, GOLD, aa * (1 - ok)); cr.set_line_width(5)
                cr.arc(xs[i], ny - 8, 15, math.pi, 0); cr.stroke()
                rrect(cr, xs[i] - 22, ny - 8, 44, 34, 6); cr.fill()
            check(cr, xs[i], ny + 2, 40, GOLD, aa * ok, ok)
        else:
            text(cr, str(i + 1 if i < 3 else i), xs[i], ny + 14, 36, c, aa, 'Inter Display', True, 'center')
        text(cr, lab, xs[i], ny + (r + 50), 26 if i != 3 else 30, c if i == 3 else WHITE, aa, 'Inter Display', True, 'center')
    ga = fade(t, 92.6, 99.2, .5, .5)
    text(cr, 'Nothing moves past this step without you', xs[3], ny - 110, 20, GOLD, ga, bold=True, align='center', track=1.5)
    # verification list
    va = ease(prog(t, 96.2, 97.0)) * (1 - ease(prog(t, 98.8, 99.4)))
    items = [('Supplier order submitted', 96.6), ('Supplier confirmation received', 97.2), ('Delivery scheduled · Thu 9:00 AM', 97.8), ('Action logged with timestamp', 98.4)]
    if va > 0:
        card(cr, 560, 640, 800, 300, 22, va)
        text(cr, 'VERIFICATION', 600, 690, 16, GREEN, va, bold=True, track=2.5)
        for j, (s, t0) in enumerate(items):
            p = prog(t, t0, t0 + .4)
            check(cr, 612, 742 + j * 52, 22, GREEN, va * (p > 0), eout(p))
            text(cr, s, 650, 750 + j * 52, 25, WHITE, va * (.35 + .65 * (p > 0)))
    cr.restore()
    # big statements
    b1 = fade(t, 99.4, 106.0, .6, .6)
    if b1 > 0:
        rgba(cr, BG, .94 * b1); cr.paint()
        headline(cr, 'Nothing happens', W / 2, 470, 96, b1, prog(t, 99.4, 100.1), align='center')
        headline(cr, 'without your approval.', W / 2, 580, 96, b1, prog(t, 99.7, 100.4), GOLD, align='center')
        b2 = eout(prog(t, 101.4, 102.1)) * b1
        text(cr, 'You stay in control.', W / 2, 690, 44, WHITE, b2 * .9, 'Inter Light', align='center')
        b3 = eout(prog(t, 102.4, 103.2)) * b1
        rrect(cr, W / 2 - 560, 790, 1120, 92, 18); rgba(cr, WHITE, .05 * b3); cr.fill_preserve(); rgba(cr, WHITE, .15 * b3); cr.set_line_width(1.2); cr.stroke()
        text(cr, 'PROPOSED CAPABILITIES', W / 2, 826, 15, AMBER, b3, bold=True, align='center', track=3)
        text(cr, 'POS, fuel-system and supplier integrations are not yet connected; they are confirmed during the pilot.', W / 2, 860, 21, hexc('C8D2E2'), b3, align='center')

# ============ SCENE 7: dawn ending (105-120) ============
def s7(cr, t):
    e = einout(prog(t, 105, 120))
    cam = E.Cam(lerp(-1.5, -2.5, e), lerp(2.6, 3.6, e), lerp(-6, -15, e), 1500, lerp(600, 640, e))
    E.draw(cr, t, cam, lerp(0.45, 0.95, ease(prog(t, 105, 116))), 0.0)
    d = ease(prog(t, 106.4, 108.0))
    g = cairo.RadialGradient(W / 2, H / 2, 200, W / 2, H / 2, 1100)
    g.add_color_stop_rgba(0, *BG, .78 * d); g.add_color_stop_rgba(1, *BG, .9 * d)
    cr.set_source(g); cr.paint()
    la = eout(prog(t, 106.4, 107.4))
    pi_mark(cr, W / 2, 360, 92, la, la)
    wordmark(cr, W / 2, 560, 120, eout(prog(t, 106.8, 107.8)), track=lerp(10, 0, eout(prog(t, 106.8, 108))))
    a1 = eout(prog(t, 108.4, 109.1)); a2 = eout(prog(t, 109.3, 110.0))
    font(cr, 64, 'Inter Display', True); w1 = text_w(cr, 'One Store.  ')
    font(cr, 64, 'Inter Display', True); w2 = text_w(cr, '30-Day Pilot.')
    x0 = W / 2 - (w1 + w2) / 2
    text(cr, 'One Store.', x0, 680 + (1 - a1) * 20, 64, WHITE, a1, 'Inter Display', True)
    text(cr, '30-Day Pilot.', x0 + w1, 680 + (1 - a2) * 20, 64, GOLD, a2, 'Inter Display', True)
    rgba(cr, CYAN, a2); cr.rectangle(W / 2 - 60 * a2, 726, 120 * a2, 3); cr.fill()
    a3 = eout(prog(t, 111.5, 112.5))
    text(cr, 'Starting at Irvington Chevron  ·  Irvington, Alabama', W / 2, 790, 26, hexc('D5DCE8'), a3 * .9, align='center')
    letterbox(cr, 1.0, 'CONCEPT RENDERING · PROPOSED CAPABILITIES · SAMPLE DATA')
    end = ease(prog(t, 118.6, 120.0))
    if end > 0: rgba(cr, (0, 0, 0), end); cr.paint()

# scene table: (start, end, fn). Overlaps produce crossfades.
SCENES = [(0.0, 15.8, s1), (15.0, 30.8, s2), (30.0, 50.8, s3), (50.0, 70.8, s4), (70.0, 90.8, s5), (90.0, 105.8, s6), (105.0, 120.0, s7)]
