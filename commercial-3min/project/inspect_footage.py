"""Inspect authentic.mp4: technical probe, scene-cut detection, motion/brightness per second, and contact sheets
so exact in/out points can be chosen for SLOTS in timeline.py.
Usage: python3 inspect_footage.py /path/to/authentic.mp4 outdir"""
import subprocess, sys, os, json, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", src], capture_output=True, text=True).stdout)
open(os.path.join(out, "probe.json"), "w").write(json.dumps(info, indent=1))
v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
dur = float(info["format"]["duration"])
print("video", v["width"], "x", v["height"], v.get("r_frame_rate"), "dur", round(dur, 2), "audio" if any(s["codec_type"] == "audio" for s in info["streams"]) else "no audio")

# scene cuts
log = subprocess.run(["ffmpeg", "-v", "info", "-i", src, "-vf", "select='gt(scene,0.2)',showinfo", "-an", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
cuts = [0.0] + [float(m) for m in re.findall(r"pts_time:([\d.]+)", log)] + [dur]
json.dump(cuts, open(os.path.join(out, "cuts.json"), "w"))
print("detected segments:", len(cuts) - 1)

# per-frame stats at 4 fps on small frames: brightness, sharpness, motion
w, h = 160, 90
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps=4,scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(float)
bright = fr.mean((1, 2))
sharp = np.array([np.abs(np.diff(f, axis=1)).mean() + np.abs(np.diff(f, axis=0)).mean() for f in fr])
motion = np.concatenate([[0], np.abs(np.diff(fr, axis=0)).mean((1, 2))])
with open(os.path.join(out, "stats.csv"), "w") as f:
    f.write("t,brightness,sharpness,motion\n")
    for i in range(len(fr)): f.write(f"{i / 4:.2f},{bright[i]:.1f},{sharp[i]:.2f},{motion[i]:.2f}\n")

# contact sheets: one tile every 1 s with timecode
step = 1.0; times = np.arange(0, dur, step)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
tiles = []
for t in times:
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", "-vf", "scale=384:-2", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    if not b: continue
    from io import BytesIO
    im = Image.open(BytesIO(b)).convert("RGB"); d = ImageDraw.Draw(im)
    i = int(t * 4) if int(t * 4) < len(fr) else -1
    d.rectangle([0, 0, 230, 26], fill=(0, 0, 0)); d.text((6, 3), f"{t:6.1f}s  m{motion[i]:.0f} s{sharp[i]:.0f}", fill=(255, 220, 80), font=font)
    tiles.append(im)
cols = 6
for k in range(0, len(tiles), 36):
    group = tiles[k:k + 36]; tw, th = group[0].size
    sheet = Image.new("RGB", (cols * tw, ((len(group) + cols - 1) // cols) * th), (20, 20, 20))
    for j, im in enumerate(group): sheet.paste(im.resize((tw, th)), ((j % cols) * tw, (j // cols) * th))
    sheet.save(os.path.join(out, f"contact_{k // 36:02d}.jpg"), quality=88)
print("contact sheets:", (len(tiles) + 35) // 36)
