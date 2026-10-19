"""QA: transcribe the narration windows from the FINAL muxed film audio (music + fx + ambience included)."""
import sys, subprocess, numpy as np, json
from asr_check import rec, norm, wer
import timeline as TL
src = sys.argv[1]
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
a = np.frombuffer(raw, np.float32); ws = []
for m in TL.VO.values():
    i0, i1 = int((m["start"] - .2) * 16000), int((m["start"] + m["dur"] + .4) * 16000)
    s = rec.create_stream(); s.accept_waveform(16000, a[i0:i1].copy()); rec.decode_stream(s)
    w = wer(norm(m["tts"]), norm(s.result.text)); ws.append(w); print(f"{m['id']} WER {w:.1%} | {s.result.text.strip()[:110]}")
print("MEAN WER IN MIX", f"{np.mean(ws):.2%}")
