"""Review a render: timecoded contact sheets every STEP seconds (for watching the whole film frame by frame)."""
import sys, subprocess, os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
src, out, step = sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
os.makedirs(out, exist_ok=True); font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True).stdout)
tiles = []; t = 0.5
while t < dur:
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", "-vf", "scale=640:-2", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    im = Image.open(BytesIO(b)).convert("RGB"); d = ImageDraw.Draw(im); m, s = divmod(t, 60)
    d.rectangle([0, 0, 110, 30], fill=(0, 0, 0)); d.text((6, 3), f"{int(m)}:{s:04.1f}", fill=(255, 220, 80), font=font); tiles.append(im); t += step
for k in range(0, len(tiles), 12):
    g = tiles[k:k + 12]; sh = Image.new("RGB", (3 * 640, 4 * 360), (30, 30, 30))
    for j, im in enumerate(g): sh.paste(im, ((j % 3) * 640, (j // 3) * 360))
    sh.save(os.path.join(out, f"review_{k // 12:02d}.jpg"), quality=85)
print(len(tiles), "frames reviewed")
