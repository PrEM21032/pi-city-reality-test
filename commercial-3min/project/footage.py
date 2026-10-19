"""Real-footage access: per-shot ffmpeg decoders, cover/pillar fitting, punch-ins, placeholder slates."""
import cairo, subprocess, os, json, math, numpy as np
from lib import *

SRC_DIR = os.environ.get("FOOTAGE_DIR", "/tmp/claude-0/v2/src")
DEC_W = 2560  # decode width: headroom for punch-ins up to ~1.33x without upscaling

_probe = {}
def probe(path):
    if path not in _probe:
        o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height:stream_side_data=rotation:format=duration", "-of", "json", path],
                           capture_output=True, text=True).stdout
        j = json.loads(o); s = j["streams"][0]; w, h = s["width"], s["height"]
        rot = 0
        for sd in s.get("side_data_list", []) or []:
            rot = int(sd.get("rotation", 0) or 0)
        if abs(rot) == 90: w, h = h, w
        _probe[path] = (w, h, float(j["format"]["duration"]))
    return _probe[path]

class Decoder:
    """Sequential BGRA frame reader starting at a source time; reopened on seeks."""
    def __init__(self, path, t0):
        sw, sh, _ = probe(path)
        self.w = min(DEC_W, sw) & ~1; self.h = int(round(sh * self.w / sw)) & ~1
        self.path, self.t0, self.n = path, t0, 0
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-i", path, "-an", "-vf",
                                   f"fps={FPS},scale={self.w}:{self.h}:flags=lanczos,format=bgra",
                                   "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=10 ** 8)
        self.last = None
    def at(self, t):
        want = int(round((t - self.t0) * FPS))
        while self.n <= want:
            b = self.p.stdout.read(self.w * self.h * 4)
            if len(b) < self.w * self.h * 4: break  # end of source: hold last frame
            self.last = bytearray(b); self.n += 1
        return self.last
    def close(self):
        try: self.p.kill()
        except Exception: pass

class Pool:
    def __init__(self): self.d = {}
    def frame(self, key, path, t):
        dec = self.d.get(key)
        if dec is None or int(round((t - dec.t0) * FPS)) < dec.n - 1 or (t - dec.t0) * FPS > dec.n + 45:
            if dec: dec.close()
            dec = self.d[key] = Decoder(path, max(0.0, t))
        buf = dec.at(t)
        if buf is None: return None
        return cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, dec.w, dec.h)
    def gc(self, keep):
        for k in list(self.d):
            if k not in keep: self.d.pop(k).close()

def slate(cr, rect, label, t):
    x, y, w, h = rect
    g = cairo.LinearGradient(x, y, x + w, y + h); g.add_color_stop_rgb(0, .16, .17, .2); g.add_color_stop_rgb(1, .08, .09, .11)
    cr.rectangle(x, y, w, h); cr.set_source(g); cr.fill()
    s = min(w / 1920, h / 1080) ** .5
    text(cr, "REAL FOOTAGE SLOT", x + w / 2, y + h / 2 - 20 * s, 22 * s, AMBER, .9, bold=True, align='center', track=3)
    text(cr, label, x + w / 2, y + h / 2 + 30 * s, 34 * s, WHITE, .9, align='center')
    text(cr, "awaiting authentic.mp4", x + w / 2, y + h / 2 + 72 * s, 20 * s, MUTED, .9, align='center')

def draw_shot(cr, pool, key, path, src_t, rect, cx=.5, cy=.5, zoom=1.0, fit='cover', label='', grade=1.0, t=0):
    """Draw source frame into rect. (cx,cy) = normalized focus point in source; zoom >= 1 punches in."""
    x, y, w, h = rect
    if not path or not os.path.exists(path):
        cr.save(); cr.rectangle(x, y, w, h); cr.clip(); slate(cr, rect, label, t); cr.restore(); return
    s = pool.frame(key, path, src_t)
    if s is None: return
    sw, sh = s.get_width(), s.get_height()
    cr.save(); cr.rectangle(x, y, w, h); cr.clip()
    if fit == 'pillar':  # blurred, darkened cover copy behind a contained frame
        sc = max(w / sw, h / sh) * 1.15
        cr.save(); cr.translate(x + w / 2, y + h / 2); cr.scale(sc, sc); cr.translate(-sw / 2, -sh / 2)
        cr.set_source_surface(s, 0, 0); cr.get_source().set_filter(cairo.FILTER_FAST); cr.paint(); cr.restore()
        rgba(cr, (0, 0, 0), .62); cr.rectangle(x, y, w, h); cr.fill()
        sc = min(w / sw, h / sh) * zoom
    else:
        sc = max(w / sw, h / sh) * zoom
    vw, vh = w / sc, h / sc  # visible source window
    fx = clamp(cx * sw, vw / 2, sw - vw / 2) if fit != 'pillar' else sw / 2
    fy = clamp(cy * sh, vh / 2, sh - vh / 2) if fit != 'pillar' else sh / 2
    cr.translate(x + w / 2, y + h / 2); cr.scale(sc, sc); cr.translate(-fx, -fy)
    cr.set_source_surface(s, 0, 0); cr.get_source().set_filter(cairo.FILTER_GOOD); cr.paint()
    cr.restore()
    if grade < 1:
        rgba(cr, (0, 0, 0), 1 - grade); cr.rectangle(x, y, w, h); cr.fill()
