"""Offline intelligibility check: Whisper-small (sherpa-onnx) transcribes each narration clip; report word error rate vs script."""
import sherpa_onnx, soundfile as sf, numpy as np, json, re, sys
from scipy import signal
M = "/tmp/claude-0/voices/sherpa-onnx-whisper-small.en/small.en-"
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M + "encoder.int8.onnx", decoder=M + "decoder.int8.onnx", tokens=M + "tokens.txt", num_threads=4)
def norm(s):
    s = s.lower().replace("pi stationos", "pie station o s").replace("stationos", "station o s")
    s = re.sub(r"[^a-z0-9' ]", " ", s); return s.split()
def wer(r, h):
    d = np.arange(len(h) + 1)
    for i, rw in enumerate(r, 1):
        p = d.copy(); d[0] = i
        for j, hw in enumerate(h, 1): d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (rw != hw))
    return d[-1] / max(len(r), 1)
def transcribe(path):
    a, sr = sf.read(path, dtype="float32")
    if a.ndim > 1: a = a.mean(1)
    if sr != 16000: a = signal.resample_poly(a, 16000, sr).astype(np.float32)
    s = rec.create_stream(); s.accept_waveform(16000, a); rec.decode_stream(s); return s.result.text.strip()
if __name__ == "__main__":
    prefix = sys.argv[1] if len(sys.argv) > 1 else "vo_"
    meta = json.load(open("vo.json")); tot = []
    for m in meta:
        hyp = transcribe(f"{prefix}{m['id']}.wav"); w = wer(norm(m["tts"]), norm(hyp)); tot.append(w)
        print(f"{m['id']} WER {w:.2%} | {hyp}")
    print("MEAN WER", f"{np.mean(tot):.2%}")
