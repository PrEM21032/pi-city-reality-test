"""Original score + sound design + narration mix for the 3-minute film (all synthesized locally; no third-party audio).
If authentic.mp4 is present, its location sound is used as a low ambience bed under each shot."""
import numpy as np, json, os, subprocess, soundfile as sf
from scipy import signal
import timeline as TL
SR = 48000; DUR = TL.TOTAL; N = int(SR * DUR); rng = np.random.default_rng(3)
MUS = np.zeros((N, 2)); FX = np.zeros((N, 2)); AMB = np.zeros((N, 2))
def tv(d): return np.arange(int(d * SR)) / SR
def lp(x, f, o=2): b, a = signal.butter(o, f / (SR / 2)); return signal.lfilter(b, a, x)
def hp(x, f, o=2): b, a = signal.butter(o, f / (SR / 2), 'high'); return signal.lfilter(b, a, x)
def put(bus, t, x, g=1.0, pan=0.0):
    i = int(t * SR); x = x[:max(0, N - i)]
    if i < 0 or not len(x): return
    bus[i:i + len(x), 0] += x * g * np.sqrt((1 - pan) / 2) * 1.414; bus[i:i + len(x), 1] += x * g * np.sqrt((1 + pan) / 2) * 1.414
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def env(n, a, r):
    e = np.ones(n); A = int(a * SR); R = int(r * SR); e[:A] = np.linspace(0, 1, A); e[-R:] *= np.linspace(1, 0, R); return e
def pad(notes, d, bright=1200):
    t = tv(d); x = np.zeros(len(t))
    for m in notes:
        for c in (-6, 0, 6):
            x += signal.sawtooth(2 * np.pi * (mtof(m) * 2 ** (c / 1200) * t + rng.random()))
    return lp(x / (3 * len(notes)), bright) * env(len(t), 1.5, 1.8)
def pluck(f, d=1.2):
    t = tv(d); return lp((np.sin(2 * np.pi * f * t) + .35 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 5), 3500)
def kick(g=1.):
    t = tv(.45); ph = 2 * np.pi * np.cumsum(45 + 70 * np.exp(-t * 32)) / SR; return g * np.sin(ph) * np.exp(-t * 8)
def tick(f=2400, d=.05): t = tv(d); return np.sin(2 * np.pi * f * t) * np.exp(-t * 90)
def blip(f, d=.22): t = tv(d); return (np.sin(2 * np.pi * f * t) + .25 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 22)
def chime(fs): return np.concatenate([blip(f, .16 if i < len(fs) - 1 else .45) for i, f in enumerate(fs)])
def swell(d):
    t = tv(d); n = lp(hp(rng.standard_normal(len(t)), 300), 2500); return n * np.sin(np.pi * t / d) ** 2
def tap(): t = tv(.06); return hp(rng.standard_normal(len(t)), 1800) * np.exp(-t * 160) + .6 * np.sin(2 * np.pi * 260 * t) * np.exp(-t * 80)
def hit(): t = tv(3.0); ph = 2 * np.pi * np.cumsum(38 + 40 * np.exp(-t * 5)) / SR; return np.sin(ph) * np.exp(-t * 1.6) + .2 * lp(rng.standard_normal(len(t)), 900) * np.exp(-t * 4)

# ---- score: D major/B minor, 84 BPM, restrained. Sections follow the edit.
BEAT = 60 / 84; BAR = 4 * BEAT
PROG = [[50, 54, 57, 61], [47, 50, 54, 57], [43, 47, 50, 54], [45, 49, 52, 57]]  # Dmaj7 Bm G A
BASS = [38, 35, 31, 33]
def section(t0, t1, level, arp=True, pulse=False, bright=1200):
    k = 0; t = t0
    while t < t1 - .5:
        d = min(2 * BAR, t1 - t) + 1.5; ch = PROG[k % 4]
        put(MUS, t, pad(ch, d, bright), .16 * level, -.25); put(MUS, t + .011, pad(ch, d, bright), .16 * level, .25)
        bt = tv(min(2 * BAR, t1 - t)); put(MUS, t, lp(np.sin(2 * np.pi * mtof(BASS[k % 4]) * bt), 300) * env(len(bt), .3, .6), .12 * level)
        if arp:
            for j in range(int(min(2 * BAR, t1 - t) / (BEAT / 2))):
                m = ch[[0, 2, 1, 3, 2, 1, 3, 2][j % 8]] + 12
                put(MUS, t + j * BEAT / 2, pluck(mtof(m)), .055 * level, .3 if j % 2 else -.3)
        if pulse:
            for j in range(int(min(2 * BAR, t1 - t) / BEAT)): put(MUS, t + j * BEAT, kick(), .16 * level)
        t += 2 * BAR; k += 1
section(0.0, 25.5, .7, arp=False, bright=700)          # night, real store
section(25.5, 50.0, .8, arp=True, bright=900)           # the problem
section(50.0, 62.5, .55, arp=False, bright=700)         # old way: sparse
section(62.5, 90.8, .9, arp=True, pulse=True, bright=1500)
section(90.8, 124.5, .9, arp=True, pulse=True, bright=1600)
section(124.5, 143.6, .8, arp=True, pulse=False, bright=1400)
section(143.6, 156.2, 1.0, arp=True, pulse=False, bright=1900)
section(156.2, 180.0, .95, arp=True, pulse=False, bright=1700)
put(MUS, TL.S("v8", 3) - .1, hit(), .35)

# ---- sound design cued to on-screen events
S = TL.S
for t in (25.5, 50.0, 62.4, 90.8, 97.5, 124.5, 143.8, 156.0): put(FX, t - .5, swell(1.0), .05)
for i in range(4): put(FX, S("v2", 1) - .3 + i * 1.6, tick(1800), .12, -.5 + i * .33)
t0 = S("v2", 4)
for k in range(int((49.6 - t0) / .62)): put(FX, t0 + k * .62, tick(2600, .04), .08, (-1) ** k * .4)
for t in (S("v4", 1) + .4, S("v4", 1, .42)): put(FX, t, blip(1175), .09, .4)
put(FX, S("v4", 1, .72), chime([880, 698]), .12, .4)            # flag
put(FX, S("v4", 2), blip(1319), .09, .4)                          # proposal
put(FX, S("v4", 3), blip(587, .3), .08, .4)                       # draft, not sent
td = S("v4", 4)
E0 = td - .6 + .3; A0 = td - .6 + 2.0
put(FX, E0, tap(), .25, .4); put(FX, A0, tap(), .25, .4); put(FX, A0 + .3, chime([1047, 1568]), .13, .4)
put(FX, S("v5", 2), chime([784, 988, 1175]), .07)                 # one picture merges
put(FX, S("v5", 3) + .8, blip(698, .3), .07)
put(FX, S("v5", 5), blip(1175), .08, .3)
put(FX, S("v6", 2), chime([880, 698]), .1, .4)
for j, dt in enumerate((.6, 1.8, 3.2)): put(FX, S("v6", 3) + dt, blip(1047 + 200 * j, .15), .09, .4)
put(FX, 143.9, chime([988, 1319]), .1, .3)                        # phone notification
s3 = S("v7", 3); put(FX, s3 + .3, tap(), .3, .3); put(FX, s3 + .55, chime([1047, 1568]), .13, .3)

# ---- location sound from the real footage (if available)
if os.path.exists(TL.SRC):
    for s in TL.SHOTS:
        a = TL.SLOTS[s["slot"]][0]
        if a is None or s["rect"] not in (TL.FULL, TL.TILES[0], TL.LEFT): continue
        src_t = a + s["off"]
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{src_t:.3f}", "-t", f"{s['d'] + .1:.3f}", "-i", TL.SRC, "-vn", "-ac", "2", "-ar", str(SR),
                              "-f", "f32le", "-"], capture_output=True).stdout
        x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(float)
        if len(x) < 100: continue
        e = env(len(x), .08, .08)[:, None]; i = int(s["t"] * SR); x = x[:N - i]
        AMB[i:i + len(x)] += x * e[:len(x)]
    AMB = hp(AMB.T, 70).T

# ---- narration
VO = np.zeros(N)
for m in TL.VO.values():
    x, sr = sf.read(os.path.join(os.path.dirname(__file__), f"vo_{m['id']}.wav"))
    x = hp(signal.resample_poly(x, SR, sr), 80); i = int(m["start"] * SR); VO[i:i + len(x)] += x[:N - i]
rms = np.sqrt(np.convolve(VO ** 2, np.ones(960) / 960, 'same')) + 1e-9
lvl = 20 * np.log10(rms); VO *= 10 ** (np.where(lvl > -24, (lvl + 24) * (1 / 3 - 1), 0) / 20)
VO *= .5 / np.max(np.abs(VO))
act = np.convolve((np.abs(VO) > 1e-3).astype(float), np.ones(int(.3 * SR)), 'same') > 0
duck = np.convolve(np.where(act, .32, 1.0), np.ones(int(.35 * SR)) / int(.35 * SR), 'same')[:, None]
amb_peak = np.max(np.abs(AMB)) or 1
mix = MUS * .55 * duck + FX * .8 + AMB / amb_peak * .12 * (.5 + .5 * duck) + VO[:, None]
f = np.ones(N); f[:int(1.2 * SR)] = np.linspace(0, 1, int(1.2 * SR)); f[-int(1.2 * SR):] = np.linspace(1, 0, int(1.2 * SR))
mix *= f[:, None]; mix /= np.max(np.abs(mix)) / .89
sf.write("mix.wav", mix.astype(np.float32), SR, subtype="FLOAT"); sf.write("stem_vo.wav", VO.astype(np.float32), SR, subtype="FLOAT")
sf.write("stem_music_fx.wav", (MUS * .55 * duck + FX * .8).astype(np.float32), SR, subtype="FLOAT")
print("ok")
