"""Procedural, perspective-projected gas-station exterior (concept rendering, not footage)."""
import cairo, math
from lib import *

class Cam:
    def __init__(s, x, y, z, f=1250, cy=H / 2): s.x, s.y, s.z, s.f, s.cx, s.cy = x, y, z, f, W / 2, cy
    def p(s, X, Y, Z):
        dz = max(Z - s.z, 0.05)
        return s.cx + (X - s.x) * s.f / dz, s.cy - (Y - s.y) * s.f / dz
    def k(s, Z): return s.f / max(Z - s.z, 0.05)

def poly(cr, cam, pts):
    for i, q in enumerate(pts):
        x, y = cam.p(*q)
        (cr.move_to if i == 0 else cr.line_to)(x, y)
    cr.close_path()

def fillpoly(cr, cam, pts, c, a=1.0):
    poly(cr, cam, pts); rgba(cr, c, a); cr.fill()

def box_faces(cr, cam, x0, x1, y0, y1, z0, z1, front, side, top=None):
    """Draw visible faces of an axis-aligned box (camera in front: z<z0)."""
    if cam.x < x0: fillpoly(cr, cam, [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], side)
    if cam.x > x1: fillpoly(cr, cam, [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)], side)
    if top and cam.y > y1: fillpoly(cr, cam, [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], top)
    fillpoly(cr, cam, [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], front)

_R = rng(7)
STARS = [(_R.random() * W, _R.random() * H * 0.55, _R.random() * 1.4 + 0.3, _R.random() * 6.28) for _ in range(260)]
TREES_FAR = [(x, 7 + _R.random() * 11, 100 + _R.random() * 40) for x in range(-260, 261, 5)]
TREES_MID = [(x, 9 + _R.random() * 9, 52 + _R.random() * 10) for x in list(range(-60, -18, 4)) + list(range(20, 64, 4))]
RAIN = [(_R.random() * W, _R.random() * H, 900 + _R.random() * 900, 14 + _R.random() * 30, 0.05 + _R.random() * 0.13) for _ in range(420)]
# passing traffic: (t0, dir, lane_z, color)
CARS = [(0.6, 1, -2.0, 0.10), (3.4, -1, 2.0, 0.16), (7.2, 1, -2.0, 0.08), (10.0, -1, 2.0, 0.12),
        (12.6, 1, -2.0, 0.14), (106.0, -1, 2.0, 0.12), (110.5, 1, -2.0, 0.10), (115.0, -1, 2.0, 0.13)]

def pine(cr, cam, x, h, z, c):
    k = cam.k(z); bx, by = cam.p(x, 0, z)
    w = h * 0.32 * k
    cr.move_to(bx, by - h * k)
    for i in range(4):
        f = (i + 1) / 4
        cr.line_to(bx + w * f, by - h * k * (1 - f * 0.85) + 0)
        cr.line_to(bx + w * f * 0.45, by - h * k * (1 - f * 0.85) - h * k * 0.05)
    cr.line_to(bx + 0.4 * k, by); cr.line_to(bx - 0.4 * k, by)
    for i in reversed(range(4)):
        f = (i + 1) / 4
        cr.line_to(bx - w * f * 0.45, by - h * k * (1 - f * 0.85) - h * k * 0.05)
        cr.line_to(bx - w * f, by - h * k * (1 - f * 0.85))
    cr.close_path(); rgba(cr, c); cr.fill()

def sky(cr, cam, dawn, t):
    top = mix(hexc('03060E'), hexc('2A3E66'), dawn)
    mid = mix(hexc('0B1530'), hexc('7C6E8E'), dawn)
    hor = mix(hexc('2B2340'), hexc('F3A867'), dawn)
    g = cairo.LinearGradient(0, 0, 0, cam.cy + 10)
    g.add_color_stop_rgb(0, *top); g.add_color_stop_rgb(0.62, *mid); g.add_color_stop_rgb(1, *hor)
    cr.set_source(g); cr.rectangle(0, 0, W, cam.cy + 12); cr.fill()
    glow(cr, W * 0.72, cam.cy + 30, 900, mix(hexc('C2683A'), hexc('FFB070'), dawn), 0.18 + 0.45 * dawn, 0.35)
    sa = 1 - dawn * 1.2
    if sa > 0:
        for (x, y, r, ph) in STARS:
            if y < cam.cy - 40:
                rgba(cr, WHITE, sa * (0.35 + 0.3 * math.sin(t * 1.3 + ph)) * (1 - y / cam.cy))
                cr.arc(x, y, r, 0, 6.283); cr.fill()

def car_side(cr, cam, xc, lane, d, body, t, beam=True):
    """Passing car seen from the side, moving along x (d=+1 right)."""
    L, Wd = 4.6, 1.8; z0 = lane - Wd / 2
    x0, x1 = xc - L / 2, xc + L / 2
    k = cam.k(z0)
    # body + cabin
    fillpoly(cr, cam, [(x0, 0.35, z0), (x1, 0.35, z0), (x1, 1.05, z0), (x0, 1.05, z0)], (body, body, body * 1.2))
    cx0, cx1 = (x0 + 1.1, x1 - 1.4) if d > 0 else (x0 + 1.4, x1 - 1.1)
    fillpoly(cr, cam, [(x0 + 0.5, 1.05, z0), (x1 - 0.5, 1.05, z0), (cx1, 1.5, z0), (cx0, 1.5, z0)], (body * .7, body * .7, body * .9))
    fillpoly(cr, cam, [(cx0 + 0.15, 1.1, z0), (cx1 - 0.15, 1.1, z0), (cx1 - 0.25, 1.42, z0), (cx0 + 0.25, 1.42, z0)], hexc('1B2A44'), 0.9)
    for wx in (x0 + 0.95, x1 - 0.95):
        px, py = cam.p(wx, 0.33, z0); cr.arc(px, py, 0.33 * k, 0, 6.283); rgba(cr, hexc('050608')); cr.fill()
    # lights (additive)
    cr.set_operator(cairo.OPERATOR_ADD)
    fx = x1 if d > 0 else x0; rx = x0 if d > 0 else x1
    hx, hy = cam.p(fx, 0.75, z0); glow(cr, hx, hy, 1.6 * k, hexc('FFF3D6'), 0.9, 0.5)
    rx_, ry_ = cam.p(rx, 0.8, z0); glow(cr, rx_, ry_, 0.9 * k, RED, 0.8, 0.6)
    if beam:  # headlight pool on road ahead
        bx, by = cam.p(fx + d * 6, 0, lane); glow(cr, bx, by, 7 * k, hexc('FFF0D0'), 0.22, 0.18)
    cr.set_operator(cairo.OPERATOR_OVER)

def draw(cr, t, cam, dawn=0.0, rain=1.0, traffic_t=None):
    tt = t if traffic_t is None else traffic_t
    sky(cr, cam, dawn, t)
    # far treeline
    tc = mix(hexc('060912'), hexc('2A2E3E'), dawn)
    for (x, h, z) in TREES_FAR: pine(cr, cam, x, h, z, tc)
    # ground
    gy = cam.cy
    g = cairo.LinearGradient(0, gy, 0, H)
    g.add_color_stop_rgb(0, *mix(hexc('121520'), hexc('4A4650'), dawn))
    g.add_color_stop_rgb(1, *mix(hexc('07080C'), hexc('1E1F25'), dawn))
    cr.set_source(g); cr.rectangle(0, gy - 2, W, H); cr.fill()
    haze = cairo.LinearGradient(0, gy - 120, 0, gy + 60)
    hz = mix(hexc('2A3550'), hexc('F0B48A'), dawn)
    haze.add_color_stop_rgba(0, *hz, 0); haze.add_color_stop_rgba(0.7, *hz, 0.28 + 0.1 * dawn); haze.add_color_stop_rgba(1, *hz, 0)
    cr.set_source(haze); cr.rectangle(0, gy - 120, W, 180); cr.fill()
    mc = mix(hexc('04060B'), hexc('1F222C'), dawn)
    for (x, h, z) in TREES_MID: pine(cr, cam, x, h, z, mc)
    # lot surface
    fillpoly(cr, cam, [(-45, 0, 5), (45, 0, 5), (45, 0, 46), (-45, 0, 46)], mix(hexc('15171E'), hexc('3B3A40'), dawn))
    # store building
    sx0, sx1, sz, sh = -16, 16, 34, 5.6
    fillpoly(cr, cam, [(sx0, 0, sz), (sx1, 0, sz), (sx1, sh, sz), (sx0, sh, sz)], mix(hexc('1A1D26'), hexc('5A5552'), dawn))
    fillpoly(cr, cam, [(sx0 - .3, 4.1, sz - .2), (sx1 + .3, 4.1, sz - .2), (sx1 + .3, sh + .3, sz - .2), (sx0 - .3, sh + .3, sz - .2)], mix(hexc('101521'), hexc('3A3F4C'), dawn))
    k = cam.k(sz)
    for (wx0, wx1) in ((-14.5, -2.2), (2.8, 14.5)):
        poly(cr, cam, [(wx0, 0.45, sz), (wx1, 0.45, sz), (wx1, 3.3, sz), (wx0, 3.3, sz)])
        x0, y0 = cam.p(wx0, 3.3, sz); x1, y1 = cam.p(wx0, 0.45, sz)
        wg = cairo.LinearGradient(0, y0, 0, y1)
        wg.add_color_stop_rgb(0, *hexc('FFE6B8')); wg.add_color_stop_rgb(1, *hexc('D99A55'))
        cr.set_source(wg); cr.fill()
        for sy in (1.0, 1.7, 2.4):  # shelf lines
            a0 = cam.p(wx0 + .3, sy, sz); a1 = cam.p(wx1 - .3, sy, sz)
            cr.move_to(*a0); cr.line_to(*a1); rgba(cr, hexc('7A5432'), 0.6); cr.set_line_width(max(1, .12 * k)); cr.stroke()
        for mx in range(int(wx0) + 1, int(wx1), 3):  # mullions
            a0 = cam.p(mx, .45, sz); a1 = cam.p(mx, 3.3, sz)
            cr.move_to(*a0); cr.line_to(*a1); rgba(cr, hexc('2A2D36')); cr.set_line_width(max(1, .14 * k)); cr.stroke()
    fillpoly(cr, cam, [(-1.6, 0, sz), (2.2, 0, sz), (2.2, 2.9, sz), (-1.6, 2.9, sz)], hexc('F5D29A'))
    # silhouettes in the store (queue at register)
    for i, px in enumerate((-9.5, -8.6, -7.8, -7.0, -6.1)):
        bob = math.sin(t * 1.5 + i) * 0.03
        bx, by = cam.p(px, 0.45, sz - 0.01); hx, hy = cam.p(px, 1.75 + bob, sz - 0.01)
        rgba(cr, hexc('3B2716'), 0.75); cr.arc(hx, hy, 0.2 * k, 0, 6.283); cr.fill()
        rrect(cr, bx - 0.25 * k, hy + 0.2 * k, 0.5 * k, by - hy - 0.2 * k, 0.15 * k); cr.fill()
    mx, my = cam.p(0.3, 4.75, sz - .25)
    text(cr, 'MARKET', mx, my + 0.32 * k, 0.75 * k, hexc('FFF1D8'), 0.95, 'Inter Display', True, 'center', 0.25 * k)
    cr.set_operator(cairo.OPERATOR_ADD)
    glow(cr, mx, my, 5 * k, hexc('FFD9A0'), 0.12, 0.4)
    gx, gy2 = cam.p(0, 0, sz - 3); glow(cr, gx, gy2, 18 * k, hexc('FFB060'), 0.16, 0.22)
    cr.set_operator(cairo.OPERATOR_OVER)
    # price pylon (generic, no brand marks)
    px0, px1, pz = -24.5, -20.5, 9
    fillpoly(cr, cam, [(-22.8, 0, pz), (-22.2, 0, pz), (-22.2, 7, pz), (-22.8, 7, pz)], hexc('15171C'))
    fillpoly(cr, cam, [(px0, 7, pz), (px1, 7, pz), (px1, 11.2, pz), (px0, 11.2, pz)], hexc('0E1118'))
    fillpoly(cr, cam, [(px0 + .2, 9.6, pz), (px1 - .2, 9.6, pz), (px1 - .2, 11.0, pz), (px0 + .2, 11.0, pz)], mix(hexc('E9EEF5'), hexc('FFFFFF'), dawn))
    k9 = cam.k(pz); cx_, cy_ = cam.p(-22.5, 10.3, pz)
    text(cr, 'FUEL', cx_, cy_ + .32 * k9, .85 * k9, hexc('1B2B4A'), 1, 'Inter Display', True, 'center', .1 * k9)
    for i, lab in enumerate(('UNLEADED', 'PLUS', 'PREMIUM', 'DIESEL')):
        lx, ly = cam.p(px0 + .4, 9.0 - i * .5, pz)
        text(cr, lab, lx, ly + .14 * k9, .3 * k9, hexc('D7DEE9'), .9, bold=True)
        rx_, _ = cam.p(px1 - .4, 9.0, pz)
        text(cr, '- . - -', rx_, ly + .14 * k9, .3 * k9, hexc('FF6A3A') if i < 3 else hexc('6CFF9A'), .95, 'DejaVu Sans Mono', True, 'right')
    # ---- canopy area ----
    cz0, cz1, cy0, cy1, cxh = 12, 24, 5.2, 6.4, 12
    # light pool on ground + wet reflections
    cr.set_operator(cairo.OPERATOR_ADD)
    gx, gy2 = cam.p(0, 0, 18); kk = cam.k(18)
    glow(cr, gx, gy2, 16 * kk, hexc('CFE3FF'), 0.55 * (1 - dawn * 0.4), 0.22)
    for ix in (-8, -4, 0, 4, 8):
        for iz in (13.5, 16.5, 19.5, 22.5):
            rx_, ry_ = cam.p(ix, -cy0, iz); bx, by = cam.p(ix, 0, iz)
            g = cairo.LinearGradient(0, by, 0, ry_)
            g.add_color_stop_rgba(0, *hexc('D8E8FF'), 0.0); g.add_color_stop_rgba(0.6, *hexc('D8E8FF'), 0.07 * rain + 0.02)
            g.add_color_stop_rgba(1, *hexc('D8E8FF'), 0)
            wdt = 1.3 * cam.k(iz); cr.set_source(g); cr.rectangle(bx - wdt / 2, by, wdt, max(ry_ - by, 1)); cr.fill()
    cr.set_operator(cairo.OPERATOR_OVER)
    # back-to-front: islands, pumps, columns
    for z in (21, 15):
        for x in (-cxh * .5, cxh * .5):
            fillpoly(cr, cam, [(x - .22, 0, z), (x + .22, 0, z), (x + .22, cy0, z), (x - .22, cy0, z)], hexc('D9DEE6') if dawn < .5 else hexc('E8ECF2'), 0.92)
    for ix in (-6, 6):
        box_faces(cr, cam, ix - .75, ix + .75, 0, .22, 15.6, 20.4, hexc('8A8F99'), hexc('6A6F78'), hexc('9AA0AA'))
        for pz_ in (19.2, 16.6):
            box_faces(cr, cam, ix - .45, ix + .45, .22, 2.05, pz_ - .32, pz_ + .32, hexc('E6E9EE'), hexc('B7BCC6'), hexc('F2F4F7'))
            fillpoly(cr, cam, [(ix - .45, 1.7, pz_ - .33), (ix + .45, 1.7, pz_ - .33), (ix + .45, 2.05, pz_ - .33), (ix - .45, 2.05, pz_ - .33)], hexc('2A6FD6'))
            fillpoly(cr, cam, [(ix - .28, 1.15, pz_ - .33), (ix + .28, 1.15, pz_ - .33), (ix + .28, 1.55, pz_ - .33), (ix - .28, 1.55, pz_ - .33)], hexc('7FE3FF'))
            sx_, sy_ = cam.p(ix, 1.35, pz_ - .33)
            cr.set_operator(cairo.OPERATOR_ADD); glow(cr, sx_, sy_, .7 * cam.k(pz_), CYAN, .35); cr.set_operator(cairo.OPERATOR_OVER)
    # customer car parked at pump (rear view)
    cxz = 15.2
    box_faces(cr, cam, 7.4, 9.3, .3, 1.25, cxz, cxz + 4.4, hexc('1E2433'), hexc('141926'), hexc('2A3142'))
    box_faces(cr, cam, 7.65, 9.05, 1.25, 1.8, cxz + .7, cxz + 3.2, hexc('2C3B57'), hexc('1A2232'), hexc('222A3A'))
    cr.set_operator(cairo.OPERATOR_ADD)
    for lx in (7.6, 9.1):
        a, b = cam.p(lx, 1.0, cxz); glow(cr, a, b, .55 * cam.k(cxz), RED, .9, .55)
    cr.set_operator(cairo.OPERATOR_OVER)
    # canopy: underside then fascia
    poly(cr, cam, [(-cxh, cy0, cz0), (cxh, cy0, cz0), (cxh, cy0, cz1), (-cxh, cy0, cz1)])
    rgba(cr, mix(hexc('BFCCDA'), hexc('C9D2DC'), dawn)); cr.fill()
    for ix in (-8, -4, 0, 4, 8):
        for iz in (13.5, 16.5, 19.5, 22.5):
            fillpoly(cr, cam, [(ix - .9, cy0 - .01, iz - .5), (ix + .9, cy0 - .01, iz - .5), (ix + .9, cy0 - .01, iz + .5), (ix - .9, cy0 - .01, iz + .5)], WHITE)
    fillpoly(cr, cam, [(-cxh, cy0, cz0), (cxh, cy0, cz0), (cxh, cy1, cz0), (-cxh, cy1, cz0)], mix(hexc('E9EDF3'), hexc('F4F6F9'), dawn))
    fillpoly(cr, cam, [(-cxh, cy0, cz0 - .01), (cxh, cy0, cz0 - .01), (cxh, cy0 + .12, cz0 - .01), (-cxh, cy0 + .12, cz0 - .01)], hexc('3A6FD8'))
    # bloom + anamorphic streak
    cr.set_operator(cairo.OPERATOR_ADD)
    bx, by = cam.p(0, cy0, 17); kb = cam.k(17)
    glow(cr, bx, by, 15 * kb, hexc('DDEBFF'), 0.30 * (1 - dawn * 0.5), 0.35)
    sg = cairo.LinearGradient(bx - 1100, 0, bx + 1100, 0)
    for o, a in ((0, 0), (0.5, 0.22 * (1 - dawn * 0.6)), (1, 0)): sg.add_color_stop_rgba(o, *hexc('7FD8FF'), a)
    cr.set_source(sg); cr.rectangle(bx - 1100, by - 2, 2200, 4); cr.fill()
    cr.set_operator(cairo.OPERATOR_OVER)
    # road + shoulder (closest to camera)
    fillpoly(cr, cam, [(-400, 0, -5), (400, 0, -5), (400, 0, 5), (-400, 0, 5)], mix(hexc('0D0F14'), hexc('2C2D33'), dawn))
    for (z, c) in ((-4.6, hexc('C8CCD4')), (4.6, hexc('C8CCD4'))):
        fillpoly(cr, cam, [(-400, 0, z - .07), (400, 0, z - .07), (400, 0, z + .07), (-400, 0, z + .07)], c, .55)
    for xd in range(-120, 121, 9):
        fillpoly(cr, cam, [(xd, 0, -.1), (xd + 3.5, 0, -.1), (xd + 3.5, 0, .1), (xd, 0, .1)], hexc('E7B53C'), .7)
    if cam.z < -6:
        fillpoly(cr, cam, [(-400, 0, cam.z + 1.2), (400, 0, cam.z + 1.2), (400, 0, -5), (-400, 0, -5)], mix(hexc('07090C'), hexc('23261F'), dawn))
    # wet-road reflections of the canopy, store and sign
    cr.set_operator(cairo.OPERATOR_ADD)
    for (X, Y, Z, c, a, r) in ((0, -5.8, 17, hexc('CFE3FF'), .16, 9), (0, -2.0, 34, hexc('FFC880'), .10, 12), (-22.5, -10.3, 9, hexc('E9EEF5'), .08, 2.2)):
        x_, y_ = cam.p(X, Y, Z); top = cam.p(X, 0, -4.9)[1]
        if y_ > top:
            k_ = cam.k(Z); g = cairo.LinearGradient(0, top, 0, y_ + r * k_ * .6)
            g.add_color_stop_rgba(0, *c, 0); g.add_color_stop_rgba(.6, *c, a * rain + a * .3); g.add_color_stop_rgba(1, *c, 0)
            cr.set_source(g); cr.rectangle(x_ - r * k_ * .5, top, r * k_, y_ - top + r * k_ * .6); cr.fill()
    cr.set_operator(cairo.OPERATOR_OVER)
    # passing cars
    for (t0, d, lane, body) in CARS:
        xc = -d * 70 + d * 24 * (tt - t0)
        if -80 < xc < 80 and lane - .9 > cam.z + 1: car_side(cr, cam, xc, lane, d, body, t)
    # rain
    if rain > 0:
        cr.set_line_width(1.2)
        for (x, y0, sp, ln, a) in RAIN:
            y = (y0 + sp * t) % (H + 60) - 30; xx = (x + 0.12 * sp * t) % W
            cr.move_to(xx, y); cr.line_to(xx + ln * 0.12, y + ln)
            rgba(cr, hexc('C9DAF0'), a * rain); cr.stroke()
