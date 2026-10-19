import cairo, sys, subprocess, numpy as np, multiprocessing as mp
from lib import *
from scenes import SCENES

_grain = None
def grain():
    global _grain
    if _grain is None:
        r = np.random.default_rng(5); _grain = []
        for i in range(6):
            n = (r.normal(128, 40, (H // 2, W // 2))).clip(0, 255).astype(np.uint8)
            n = np.repeat(np.repeat(n, 2, 0), 2, 1)
            a = np.dstack([n, n, n, np.full_like(n, 255)]).copy()
            s = cairo.ImageSurface.create_for_data(memoryview(a), cairo.FORMAT_ARGB32, W, H)
            _grain.append((s, a))
    return _grain

def frame(t):
    out, cr = new_surface()
    rgba(cr, (0, 0, 0)); cr.paint()
    for (a, b, fn) in SCENES:
        if a <= t < b or (b == 120.0 and t >= a):
            s, c2 = new_surface(); fn(c2, t)
            prev = [x for x in SCENES if x[0] < a and x[1] > t]
            alpha = ease(prog(t, a, prev[0][1])) if prev and fn is not SCENES[0][2] else 1.0
            cr.set_source_surface(s, 0, 0); cr.paint_with_alpha(alpha)
    # vignette
    g = cairo.RadialGradient(W / 2, H / 2, 500, W / 2, H / 2, 1250)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.55)
    cr.set_source(g); cr.paint()
    # film grain (overlay)
    gs, _ = grain()[int(t * FPS) % 6]
    cr.set_operator(cairo.OPERATOR_OVERLAY); cr.set_source_surface(gs, 0, 0); cr.paint_with_alpha(0.07)
    out.flush()
    return out

def raw(i):
    s = frame(i / FPS); return bytes(s.get_data())

if __name__ == '__main__':
    if sys.argv[1] == 'still':
        for ts in sys.argv[2:]:
            frame(float(ts)).write_to_png(f'still_{float(ts):06.1f}.png')
    else:
        out = sys.argv[2]; n = int(DUR * FPS)
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                               '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p',
                               '-tune', 'film', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        with mp.Pool(4) as p:
            for i, b in enumerate(p.imap(raw, range(n), chunksize=4)):
                ff.stdin.write(b)
                if i % 300 == 0: print('frame', i, flush=True)
        ff.stdin.close(); ff.wait(); print('done', ff.returncode)
