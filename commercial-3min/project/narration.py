"""Narration: written text (for captions/transcript) + phonetic text (for TTS)."""
import json, sys
from kokoro_onnx import Kokoro
import soundfile as sf
# id, target start (s), latest end (s), caption text, tts text
LINES = [
 ("v1", 2.0, 24.0, "Night at the pumps. Inside, the counter, the kitchen, the coolers and the aisles keep moving. This is one store, and every hour it asks its owner for another decision."),
 ("v2", 26.0, 49.0, "Most of those decisions arrive separately. Fuel numbers in one place. Shelf counts in another. The register, the kitchen, the shift notes, each with its own story. So the owner ends up chasing problems one at a time, often after they have already cost something."),
 ("v3", 51.0, 62.0, "Start with the cooler. The old way, a shortage gets noticed when the shelf is already empty, and a customer leaves without what they came for."),
 ("v4", 63.5, 89.5, "PI StationOS is designed to change that order of events. In this simulation, it brings sales pace and stock on hand together, sees a drink selling faster than usual, and flags that it is likely to run short before the next delivery. It explains why, and drafts a reorder. Nothing is sent on its own. The owner reviews it, changes the quantity, and approves."),
 ("v5", 91.5, 124.5, "Now step back outside. Fuel and inside sales are usually reviewed apart. Put them in one operating picture, and the decision changes. In this example, evening pump traffic is up, but inside sales have not followed. Looking at food sales alone, you might cut back on prep. With the pumps in view, the better move is to staff the counter, and invite those drivers inside."),
 ("v6", 126.0, 143.5, "Then comes the shift change, where details slip. PI proposes a clear handoff: what was finished, what is still open, and the one exception that matters. Here, the drawer count does not match. The next person gets a specific action, and the owner can see when it is done."),
 ("v7", 144.5, 154.5, "And every recommendation comes to you. Approve it, edit it, or decline it. You stay informed. You stay in control."),
 ("v8", 156.5, 178.5, "PI StationOS is a proposed way to help owners run the whole station, fuel, shelves, counter and shifts, with more clarity and more control. It is not connected to this store today. We want to build it with owners who know the work. See the concept. Shape the pilot. Ask for a demo."),
]
def tts_text(s):
    return (s.replace("PI StationOS", "Pie Station O S").replace("PI proposes", "Pie proposes")
             .replace("it is", "it's").replace("they have", "they've").replace("have not", "haven't")
             .replace("does not", "doesn't").replace("what is", "what's").replace("It is not", "It's not"))
import re, numpy as np
def sentences(t): return [x.strip() for x in re.split(r'(?<=[.!?])\s+', t) if x.strip()]
if __name__ == "__main__":
    k = Kokoro("/tmp/claude-0/voices/kokoro-v1.0.onnx", "/tmp/claude-0/voices/voices-v1.0.bin")
    voice = sys.argv[1] if len(sys.argv) > 1 else "am_michael"
    meta = []
    for (i, st, en, cap) in LINES:
        for sp in (0.95, 0.98, 1.01, 1.04):
            parts, segs, t = [], [], 0.0
            for j, s in enumerate(sentences(cap)):
                a, sr = k.create(tts_text(s), voice=voice, speed=sp, lang="en-us")
                nz = np.where(np.abs(a) > 0.004)[0]; a = a[max(0, nz[0] - 600): nz[-1] + 1800]  # trim edge silence
                segs.append(dict(text=s, start=round(st + t, 3), end=round(st + t + len(a) / sr, 3)))
                parts.append(a); t += len(a) / sr
                gap = 0.62 if i == "v8" and j >= 2 else 0.30
                parts.append(np.zeros(int(gap * sr))); t += gap
            if st + t <= en: break
        audio = np.concatenate(parts[:-1]); sf.write(f"vo_{i}.wav", audio, sr)
        meta.append(dict(id=i, start=st, dur=round(len(audio) / sr, 3), speed=sp, text=cap, tts=tts_text(cap), sentences=segs))
        print(i, st, round(st + len(audio) / sr, 2), "limit", en, "speed", sp)
    json.dump(meta, open("vo.json", "w"), indent=1)
