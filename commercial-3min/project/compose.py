"""Render the film: real footage + simulated-interface overlays + captions -> H.264 segments -> concat."""
import cairo, sys, os, subprocess, multiprocessing as mp
from lib import *
from footage import Pool
import timeline as TL

N = int(TL.TOTAL * FPS)

def frame(cr, pool, t, captions=True):
    rgba(cr, (0, 0, 0)); cr.paint()
    TL.draw_footage(cr, pool, t)
    g = cairo.RadialGradient(W / 2, H / 2, 600, W / 2, H / 2, 1300)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, .35); cr.set_source(g); cr.paint()
    for ov in TL.OVERLAYS: ov(cr, t)
    if captions: TL.draw_captions(cr, t)

def render_range(args):
    a, b, out, captions = args
    pool = Pool(); s, cr = new_surface()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-g", "60", out], stdin=subprocess.PIPE)
    for i in range(a, b):
        cr.save(); frame(cr, pool, i / FPS, captions); cr.restore(); s.flush()
        ff.stdin.write(bytes(s.get_data()))
    ff.stdin.close(); ff.wait(); pool.gc(set()); return out

if __name__ == "__main__":
    if sys.argv[1] == "still":
        pool = Pool()
        for ts in sys.argv[2:]:
            s, cr = new_surface(); frame(cr, pool, float(ts)); s.write_to_png(f"still_{float(ts):06.1f}.png")
    else:
        out = sys.argv[2]; captions = "--nocap" not in sys.argv; nj = 4
        os.makedirs("seg", exist_ok=True)
        cuts = [round(N * k / nj) for k in range(nj + 1)]
        jobs = [(cuts[k], cuts[k + 1], f"seg/part{k}.mp4", captions) for k in range(nj)]
        with mp.Pool(nj) as p: parts = p.map(render_range, jobs)
        open("seg/list.txt", "w").write("".join(f"file '{os.path.basename(x)}'\n" for x in parts))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seg/list.txt", "-c", "copy", out], check=True)
        print("done", out)
