import cairo, math, random

W, H, FPS, DUR = 1920, 1080, 30, 120.0

# ---------- math / easing ----------
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def lerp(a, b, t): return a + (b - a) * t
def prog(t, a, b): return clamp((t - a) / (b - a)) if b != a else float(t >= a)
def ease(t): t = clamp(t); return t * t * (3 - 2 * t)
def eout(t): t = clamp(t); return 1 - (1 - t) ** 3
def ein(t): t = clamp(t); return t ** 3
def einout(t):
    t = clamp(t)
    return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2
def eback(t):
    t = clamp(t); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def fade(t, a, b, fi=0.5, fo=0.5):
    """1 inside [a,b] with fade-in/out ramps."""
    return ease(prog(t, a, a + fi)) * (1 - ease(prog(t, b - fo, b)))

def hexc(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def mix(c1, c2, t): return tuple(lerp(a, b, t) for a, b in zip(c1, c2))

# palette
BG = hexc('070B14'); BG2 = hexc('0C1324'); PANEL = hexc('101A2E')
CYAN = hexc('35D3FF'); VIOLET = hexc('8B7BFF'); GOLD = hexc('F5B544')
GREEN = hexc('3DDC97'); AMBER = hexc('FFB547'); RED = hexc('FF5A64')
WHITE = (1, 1, 1); MUTED = hexc('8A96AD'); DIM = hexc('5A6680')

# ---------- drawing ----------
_FO = cairo.FontOptions()
_FO.set_hint_style(cairo.HINT_STYLE_NONE)
_FO.set_hint_metrics(cairo.HINT_METRICS_OFF)
_FO.set_antialias(cairo.ANTIALIAS_GRAY)

def new_surface():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cr = cairo.Context(s); cr.set_font_options(_FO)
    return s, cr

def rgba(cr, c, a=1.0): cr.set_source_rgba(c[0], c[1], c[2], a)

def font(cr, size, family='Inter', bold=False):
    cr.select_font_face(family, cairo.FONT_SLANT_NORMAL,
                        cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(size)

def text_w(cr, s, track=0.0):
    if not track: return cr.text_extents(s).x_advance
    return sum(cr.text_extents(ch).x_advance for ch in s) + track * (len(s) - 1)

def text(cr, s, x, y, size, color=WHITE, alpha=1.0, family='Inter', bold=False,
         align='left', track=0.0):
    if alpha <= 0.003 or not s: return 0
    font(cr, size, family, bold)
    w = text_w(cr, s, track)
    if align == 'center': x -= w / 2
    elif align == 'right': x -= w
    rgba(cr, color, alpha)
    if not track:
        cr.move_to(x, y); cr.show_text(s)
    else:
        for ch in s:
            cr.move_to(x, y); cr.show_text(ch); x += cr.text_extents(ch).x_advance + track
    return w

def rrect(cr, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    cr.close_path()

def shadow(cr, x, y, w, h, r, alpha=0.35, spread=28, dy=14):
    for i in range(6):
        k = (i + 1) / 6
        rrect(cr, x - spread * k, y - spread * k + dy, w + 2 * spread * k, h + 2 * spread * k, r + spread * k)
        cr.set_source_rgba(0, 0, 0, alpha / 6 * (1 - k * 0.7))
        cr.fill()

def card(cr, x, y, w, h, r=20, alpha=1.0, fill=PANEL, border=WHITE, balpha=0.10, glow=None, shadow_a=0.35):
    if alpha <= 0.003: return
    if shadow_a: shadow(cr, x, y, w, h, r, shadow_a * alpha)
    rrect(cr, x, y, w, h, r)
    g = cairo.LinearGradient(0, y, 0, y + h)
    g.add_color_stop_rgba(0, *mix(fill, WHITE, 0.05), 0.92 * alpha)
    g.add_color_stop_rgba(1, *fill, 0.88 * alpha)
    cr.set_source(g); cr.fill_preserve()
    rgba(cr, glow or border, (balpha if not glow else 0.55) * alpha)
    cr.set_line_width(1.5 if not glow else 2.0); cr.stroke()

def glow(cr, x, y, r, color, a=0.5, sy=1.0):
    if a <= 0.003: return
    cr.save(); cr.translate(x, y); cr.scale(1, sy)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, r)
    g.add_color_stop_rgba(0, *color, a)
    g.add_color_stop_rgba(0.35, *color, a * 0.35)
    g.add_color_stop_rgba(1, *color, 0)
    cr.set_source(g); cr.arc(0, 0, r, 0, 2 * math.pi); cr.fill(); cr.restore()

def check(cr, x, y, s, color=GREEN, a=1.0, p=1.0, lw=None):
    """Check mark with stroke progress p."""
    if p <= 0 or a <= 0: return
    pts = [(x - s * .5, y), (x - s * .15, y + s * .35), (x + s * .5, y - s * .35)]
    l1 = math.dist(pts[0], pts[1]); l2 = math.dist(pts[1], pts[2]); L = (l1 + l2) * p
    cr.move_to(*pts[0])
    if L <= l1:
        cr.line_to(lerp(pts[0][0], pts[1][0], L / l1), lerp(pts[0][1], pts[1][1], L / l1))
    else:
        cr.line_to(*pts[1]); k = (L - l1) / l2
        cr.line_to(lerp(pts[1][0], pts[2][0], k), lerp(pts[1][1], pts[2][1], k))
    rgba(cr, color, a); cr.set_line_width(lw or s * 0.18)
    cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke()

def icon_dot(cr, x, y, r, color, a=1.0, kind='dot', t=0.0):
    """Status icon: tinted circle + glyph."""
    if a <= 0: return
    cr.arc(x, y, r, 0, 2 * math.pi); rgba(cr, color, 0.18 * a); cr.fill()
    cr.arc(x, y, r, 0, 2 * math.pi); rgba(cr, color, 0.6 * a); cr.set_line_width(1.5); cr.stroke()
    if kind == 'warn':
        cr.set_line_width(r * 0.18); cr.set_line_cap(cairo.LINE_CAP_ROUND); rgba(cr, color, a)
        cr.move_to(x, y - r * .45); cr.line_to(x, y + r * .1); cr.stroke()
        cr.arc(x, y + r * .42, r * .1, 0, 2 * math.pi); cr.fill()
    elif kind == 'check':
        check(cr, x, y + r * 0.05, r * 0.9, color, a)
    else:
        cr.arc(x, y, r * 0.35, 0, 2 * math.pi); rgba(cr, color, a); cr.fill()

def chip(cr, s, x, y, size, color, a=1.0, align='left', fill_a=0.14, pad=14, bold=True):
    if a <= 0: return 0
    font(cr, size, 'Inter', bold); w = text_w(cr, s, 1.2) + 2 * pad; h = size + pad * 1.1
    if align == 'center': x -= w / 2
    elif align == 'right': x -= w
    rrect(cr, x, y - h / 2, w, h, h / 2); rgba(cr, color, fill_a * a); cr.fill_preserve()
    rgba(cr, color, 0.55 * a); cr.set_line_width(1.2); cr.stroke()
    text(cr, s, x + pad, y + size * 0.36, size, color, a, bold=bold, track=1.2)
    return w

def pi_mark(cr, cx, cy, R, p=1.0, a=1.0, glyph_a=None):
    """PI StationOS logo: gradient ring drawn with progress p plus a geometric pi glyph."""
    if a <= 0: return
    glyph_a = a if glyph_a is None else glyph_a
    glow(cr, cx, cy, R * 2.6, CYAN, 0.22 * a)
    g = cairo.LinearGradient(cx - R, cy - R, cx + R, cy + R)
    g.add_color_stop_rgba(0, *CYAN, a); g.add_color_stop_rgba(1, *VIOLET, a)
    cr.set_source(g); cr.set_line_width(R * 0.11); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    st = -math.pi / 2
    if p > 0.001:
        cr.arc(cx, cy, R, st, st + 2 * math.pi * clamp(p)); cr.stroke()
    if glyph_a > 0:
        g = cairo.LinearGradient(cx - R, cy - R, cx + R, cy + R)
        g.add_color_stop_rgb(0, *CYAN); g.add_color_stop_rgb(1, *VIOLET)
        s = R * 0.5
        cr.save(); cr.push_group(); cr.set_source(g); cr.set_line_width(R * 0.15)
        cr.move_to(cx - s * 1.05, cy - s * 0.55)
        cr.curve_to(cx - s * 0.6, cy - s * 0.78, cx + s * 0.4, cy - s * 0.62, cx + s * 1.05, cy - s * 0.66)
        cr.stroke()
        cr.move_to(cx - s * 0.42, cy - s * 0.6); cr.curve_to(cx - s * 0.42, cy, cx - s * 0.5, cy + s * 0.6, cx - s * 0.78, cy + s * 0.9); cr.stroke()
        cr.move_to(cx + s * 0.38, cy - s * 0.62); cr.line_to(cx + s * 0.38, cy + s * 0.55)
        cr.curve_to(cx + s * 0.38, cy + s * 0.95, cx + s * 0.75, cy + s * 0.95, cx + s * 0.9, cy + s * 0.72); cr.stroke()
        cr.pop_group_to_source(); cr.paint_with_alpha(glyph_a); cr.restore()

def wordmark(cr, cx, y, size, a=1.0, track=0.0):
    """'PI StationOS' wordmark centred at cx."""
    if a <= 0: return
    font(cr, size, 'Inter Display', True); w1 = text_w(cr, 'PI ', track)
    font(cr, size, 'Inter Display Light'); w2 = text_w(cr, 'StationOS', track)
    x = cx - (w1 + w2) / 2
    text(cr, 'PI ', x, y, size, CYAN, a, 'Inter Display', True, track=track)
    text(cr, 'StationOS', x + w1, y, size, WHITE, a, 'Inter Display Light', track=track)

def rng(seed): return random.Random(seed)
