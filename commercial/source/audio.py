import numpy as np, json, soundfile as sf
from scipy import signal
SR = 48000; DUR = 120.0; N = int(SR * DUR)
rng = np.random.default_rng(1)
L = np.zeros(N); R = np.zeros(N)          # music bus
FX_L = np.zeros(N); FX_R = np.zeros(N)    # sfx bus
BPM = 90; BEAT = 60 / BPM

def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def env_adsr(n, a, d, s, r, sr=SR):
    a, d, r = int(a * sr), int(d * sr), int(r * sr); sus = max(n - a - d - r, 0)
    e = np.concatenate([np.linspace(0, 1, a, False), np.linspace(1, s, d, False), np.full(sus, s), np.linspace(s, 0, r)])
    return e[:n] if len(e) >= n else np.pad(e, (0, n - len(e)))
def add(bus, t, x, gain=1.0, pan=0.0):
    i = int(t * SR); x = x[:max(0, min(len(x), N - i))]
    if i < 0 or len(x) == 0: return
    gl, gr = gain * np.sqrt((1 - pan) / 2), gain * np.sqrt((1 + pan) / 2)
    (L if bus == 'm' else FX_L)[i:i + len(x)] += x * gl
    (R if bus == 'm' else FX_R)[i:i + len(x)] += x * gr
def lp(x, fc, order=2): b, a = signal.butter(order, fc / (SR / 2), 'low'); return signal.lfilter(b, a, x)
def hp(x, fc, order=2): b, a = signal.butter(order, fc / (SR / 2), 'high'); return signal.lfilter(b, a, x)
def bp(x, f1, f2): b, a = signal.butter(2, [f1 / (SR / 2), f2 / (SR / 2)], 'band'); return signal.lfilter(b, a, x)
def tvec(d): return np.arange(int(d * SR)) / SR

def saw_pad(freqs, dur, bright=1800, det=(-7, 0, 7)):
    t = tvec(dur); out = np.zeros(len(t))
    for f in freqs:
        for c in det:
            ff = f * 2 ** (c / 1200); ph = rng.random()
            out += signal.sawtooth(2 * np.pi * (ff * t + ph))
    out = lp(out, bright, 2); return out / (len(freqs) * len(det))
def pluck(f, dur=0.9, bright=4000):
    t = tvec(dur); x = (np.sin(2 * np.pi * f * t) + .45 * np.sin(4 * np.pi * f * t) + .2 * signal.square(2 * np.pi * f * t))
    return lp(x * np.exp(-t * 6), bright)
def kick(g=1.0):
    t = tvec(0.5); f = 45 + 90 * np.exp(-t * 30); ph = 2 * np.pi * np.cumsum(f) / SR
    return g * np.sin(ph) * np.exp(-t * 7) + 0.15 * hp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 80)
def hat(g=1.0, d=0.06): t = tvec(d); return g * hp(rng.standard_normal(len(t)), 7000) * np.exp(-t * 60)
def snare(): t = tvec(0.35); return .6 * bp(rng.standard_normal(len(t)), 900, 6000) * np.exp(-t * 14) + .3 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 20)
def impact(g=1.0):
    t = tvec(4.0); f = 32 + 60 * np.exp(-t * 6); ph = 2 * np.pi * np.cumsum(f) / SR
    boom = np.sin(ph) * np.exp(-t * 1.3)
    nz = lp(rng.standard_normal(len(t)), 1200) * np.exp(-t * 3) * .5
    return g * (boom + nz)
def riser(d, g=1.0):
    t = tvec(d); n = rng.standard_normal(len(t)); out = np.zeros(len(t)); blk = 2400
    for i in range(0, len(t), blk):
        fc = 300 + 7000 * (i / len(t)) ** 2
        out[i:i + blk] = bp(n[max(0, i - 4800):i + blk], fc * .7, min(fc * 1.3, 20000))[-len(out[i:i + blk]):]
    tone = signal.sawtooth(2 * np.pi * np.cumsum(110 * 2 ** (2 * t / d)) / SR) * .15
    return g * (out + lp(tone, 3000)) * (t / d) ** 2
def whoosh(d=1.2, g=1.0):
    t = tvec(d); n = rng.standard_normal(len(t)); e = np.sin(np.pi * t / d) ** 2
    out = np.zeros(len(t)); blk = 1200
    for i in range(0, len(t), blk):
        fc = 400 + 3000 * np.sin(np.pi * i / len(t))
        out[i:i + blk] = bp(n[max(0, i - 2400):i + blk], fc * .6, fc * 1.4)[-len(out[i:i + blk]):]
    return g * out * e
def blip(f=1320, d=0.18, g=1.0):
    t = tvec(d); return g * (np.sin(2 * np.pi * f * t) + .3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 28)
def notif(g=1.0): return np.concatenate([blip(988, .12, g), blip(1319, .3, g)])
def tap(g=1.0): t = tvec(.05); return g * hp(rng.standard_normal(len(t)), 2000) * np.exp(-t * 200) + g * .5 * np.sin(2 * np.pi * 300 * t) * np.exp(-t * 90)

# ---------- harmony ----------
# D minor: Dm - Bb - F - C   (each 2 bars = 8 beats)
CH = [[50, 53, 57, 62], [46, 50, 53, 58], [45, 48, 53, 57], [48, 52, 55, 60]]
BASS = [38, 34, 41, 36]
CL = 8 * BEAT

# Intro drone 0-16
t = tvec(16.5); dr = lp(signal.sawtooth(2 * np.pi * mtof(26) * t) + signal.sawtooth(2 * np.pi * mtof(33) * t * 1.002), 320)
add('m', 0, dr * np.minimum(t / 3, 1) * np.minimum((16.5 - t) / .5, 1), .16)
# heartbeat pulse 4-15
for b in np.arange(4.0, 15.0, BEAT * 2): add('m', b, kick(.5), .5 * (.4 + .6 * (b - 4) / 11))
for b in np.arange(6.0, 15.0, BEAT / 2): add('m', b, hat(.4), .18 * (b - 6) / 9, rng.uniform(-.3, .3))
add('m', 12.0, riser(4.9), .45)
# impacts
for (ti, g) in ((16.9, .9), (99.35, .8), (106.4, 1.0)): add('m', ti, impact(), g)

# pads 16-120
start = 16.0
for k, c0 in enumerate(np.arange(start, 120, CL)):
    ch = CH[k % 4]; d = CL + 1.5
    if c0 >= 99.4 and c0 < 106: pass
    bright = 900 if c0 < 30 else (1600 if c0 < 90 else 2200)
    p = saw_pad([mtof(m) for m in ch], d, bright)
    e = env_adsr(len(p), 1.2, .5, .9, 1.4)
    g = .22 if c0 < 30 else .2
    add('m', c0, p * e, g, -.2); add('m', c0 + .013, p * e, g, .2)
# arpeggio 17.3-120
step = BEAT / 2
for i, tt in enumerate(np.arange(17.3, 118.0, step)):
    k = int((tt - start) // CL); ch = CH[k % 4]
    pat = [0, 2, 1, 3, 2, 1, 3, 2]
    m = ch[pat[i % 8]] + 12
    gain = .10 if tt < 30 else .13
    if 99.4 < tt < 106.4: gain *= .4
    add('m', tt, pluck(mtof(m)), gain, .35 if i % 2 else -.35)
# groove 30-99 : kick, bass 8ths, hats, snare backbeat
for i, tt in enumerate(np.arange(30.0, 99.3, BEAT)):
    k = int((tt - start) // CL); soft = .6 if 70 <= tt < 90 else 1.0
    add('m', tt, kick(), .5 * soft)
    if i % 2 == 1 and tt >= 50: add('m', tt, snare(), .16 * soft)
    for h in (0, .5):
        add('m', tt + h * BEAT, hat(.6 if h else .35), .1 * soft, .25)
    for h in (0, .5):
        bt = tvec(BEAT / 2 * .95); f = mtof(BASS[k % 4])
        b = lp(signal.sawtooth(2 * np.pi * f * bt) + np.sin(2 * np.pi * f / 2 * bt), 380) * env_adsr(len(bt), .005, .1, .7, .05)
        add('m', tt + h * BEAT, b, .2 * soft)
# build 90-99.3: snare roll riser
for j, tt in enumerate(np.arange(96.0, 99.3, BEAT / 4)): add('m', tt, snare(), .05 + .2 * j / 20)
add('m', 95.4, riser(3.95), .4)
# finale chord stack + soft hits
for ti in (108.4, 109.3): add('m', ti, kick(.8), .45)
t = tvec(12); fin = saw_pad([mtof(m) for m in (38, 50, 57, 62, 65, 69)], 12, 2000) * env_adsr(len(t), .2, 1.0, .8, 6)
add('m', 106.4, fin, .32)

# ---------- SFX ----------
# rain bed 0-16 and dawn ambience 105-120
t = tvec(16.5); rain = lp(hp(rng.standard_normal(len(t)), 400), 6000) * np.minimum(t / 1.5, 1) * np.minimum((16.5 - t) / 1.2, 1)
add('f', 0, rain, .05, -.3); add('f', 0, lp(hp(rng.standard_normal(len(t)), 400), 6000) * np.minimum(t / 1.5, 1) * np.minimum((16.5 - t) / 1.2, 1), .05, .3)
t = tvec(15); amb = lp(rng.standard_normal(len(t)), 500) * np.minimum(t / 2, 1) * np.minimum((15 - t) / 2, 1)
add('f', 105, amb, .06)
# car pass-bys (pass camera at t0 + 70/24 s)
for (t0, d) in ((0.6, 1), (3.4, -1), (7.2, 1), (10.0, -1), (12.6, 1), (106.0, -1), (110.5, 1), (115.0, -1)):
    tc = t0 + 70 / 24; dd = 3.0; t = tvec(dd * 2)
    x = (t - dd) * 24; dist = np.sqrt(x ** 2 + 64); g = 8 / dist
    eng = lp(rng.standard_normal(len(t)), 900) + .3 * lp(signal.sawtooth(2 * np.pi * np.cumsum(70 * (1 - .06 * np.tanh(x / 10))) / SR), 400)
    for i, side in enumerate((-1, 1)):
        pan_g = np.clip(.5 + .5 * d * np.tanh(x / 12) * side, .1, 1)
        seg = eng * g * pan_g * .5
        st = int((tc - dd) * SR)
        if st >= 0: (FX_L if side < 0 else FX_R)[st:st + len(seg)] += seg[:N - st]
# alerts
for ta in (4.6, 6.4, 8.4, 9.9, 11.0): add('f', ta, notif(), .22, .5)
# transitions
for tw in (29.6, 49.6, 69.6, 89.6, 104.6, 14.6): add('f', tw, whoosh(1.4), .5)
for tw in (35.4, 40.4, 54.0, 59.0, 64.6, 41.5): add('f', tw, whoosh(.9), .22)
# UI events
for tu in (31.2, 31.45, 31.7, 31.95, 32.2, 32.45): add('f', tu, blip(1760, .1), .08)
add('f', 38.4, blip(660, .4), .25); add('f', 38.55, blip(880, .4), .2)
for i in range(4): add('f', 41.6 + i * .55, blip(1175, .12), .12)
add('f', 44.5, blip(1568, .25), .15)
add('f', 52.8, blip(660, .3), .2); add('f', 57.0, blip(587, .35), .25)
for tc in (58.8, 60.0): add('f', tc, np.concatenate([blip(1320, .08), blip(1760, .2)]), .2)
add('f', 61.4, blip(740, .3), .18)
add('f', 72.0, notif(), .3)
for tt_ in (79.75, 84.4): add('f', tt_, tap(), .5); add('f', tt_ + .25, np.concatenate([blip(1047, .1), blip(1568, .25)]), .25)
for i in range(7): add('f', 90.8 + i * .5, blip(880 * 2 ** (i / 12 * 2), .15), .1)
add('f', 95.4, np.concatenate([blip(784, .1), blip(1175, .3)]), .3)
for tc in (96.6, 97.2, 97.8, 98.4): add('f', tc, blip(1568, .12), .14)

# ---------- voice ----------
VO = np.zeros(N); meta = json.load(open('vo.json'))
for m in meta:
    x, sr = sf.read(f"vo_{m['i']}.wav")
    x = signal.resample_poly(x, SR, sr)
    x = hp(x, 80)
    i = int(m['start'] * SR); VO[i:i + len(x)] += x[:N - i]
# gentle compression on voice (RMS follower, 3:1 above -24 dBFS)
rms = np.sqrt(np.convolve(VO ** 2, np.ones(960) / 960, 'same')) + 1e-9
lvl = 20 * np.log10(rms); gr = np.where(lvl > -24, (lvl + 24) * (1 / 3 - 1), 0)
VO = VO * 10 ** (gr / 20); VO *= 0.5 / np.max(np.abs(VO))
# ducking envelope from voice activity
act = np.abs(VO) > 1e-3
win = int(.25 * SR); act = np.convolve(act.astype(float), np.ones(win) / win, 'same') > 0
duck = np.where(act, .30, 1.0)
duck = np.convolve(duck, np.ones(int(.3 * SR)) / int(.3 * SR), 'same')
# simple reverb on music
ir_t = tvec(2.2); ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 3.2); ir = lp(ir, 5000) / 40
Lw = signal.fftconvolve(L, ir)[:N]; Rw = signal.fftconvolve(R, np.roll(ir, 37))[:N]
ML = (L + .6 * Lw) * duck; MR = (R + .6 * Rw) * duck
FL = FX_L * (.6 + .4 * duck); FR = FX_R * (.6 + .4 * duck)
# fade in/out
fade = np.ones(N); fade[:int(.3 * SR)] = np.linspace(0, 1, int(.3 * SR)); fade[-int(1.5 * SR):] = np.linspace(1, 0, int(1.5 * SR)) ** 2
outL = (ML * .5 + FL * .7 + VO) * fade; outR = (MR * .5 + FR * .7 + VO) * fade
st = np.stack([outL, outR], 1); st /= np.max(np.abs(st)) / 0.89
sf.write('mix.wav', st.astype(np.float32), SR, subtype='FLOAT')
sf.write('stem_vo.wav', VO.astype(np.float32), SR, subtype='FLOAT')
print('peak ok', st.shape, np.sqrt(np.mean(st ** 2)))
