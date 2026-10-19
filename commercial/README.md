# PI StationOS — 120-second commercial

**File:** `PI_StationOS_Commercial_120s_1080p.mp4`: H.264 1920×1080, 30 fps (3,600 frames), AAC stereo 48 kHz, exactly 120.000 s, about -14 LUFS integrated, -1.4 dBTP.

## What's in the video
| Time | Scene |
|---|---|
| 0:00–0:15 | Pre-dawn station exterior in the rain; location caption for Irvington Chevron; operational alerts stacking up |
| 0:15–0:30 | The PI StationOS logo is revealed, with its module ring |
| 0:30–0:50 | Product sales → shortage forecast → draft supplier order (awaiting owner approval) |
| 0:50–1:10 | Fuel sales and tank levels by grade, cash-drawer reconciliation with a flagged variance, shift tasks |
| 1:10–1:30 | Phone app: the owner reviews the reasoning behind each recommendation, then approves or assigns it |
| 1:30–1:45 | Workflow: Detect → Analyze → Recommend → **You approve** → Execute → Verify → Log |
| 1:45–2:00 | Dawn exterior with the end card: **"PI StationOS — One Store. 30-Day Pilot."** |

## Honesty and disclosure
- No real footage of the store was available. Every exterior shot is a procedural **concept rendering**, labeled on screen as "Concept rendering — not actual store footage". It doesn't use any Chevron logo or trade dress.
- Every number on screen is **sample data**, and the dashboard and app screens carry that label.
- An on-screen card states that POS, fuel-system and supplier integrations are **proposed and not yet connected**, and are confirmed during the pilot.

## How it was made ($0, free and local tools only)
- Visuals: Python with pycairo. The scenes are drawn frame by frame, including a 3D-projected station with camera dolly and parallax, rain, wet-road reflections, bloom, film grain and letterboxing. Encoded with ffmpeg/libx264.
- Narration: the Kokoro-82M neural TTS (Apache-2.0, `am_michael` voice), run locally with kokoro-onnx.
- Music and sound design: synthesized from scratch in numpy/scipy (an original D-minor score, impacts, risers, rain, car pass-bys, UI sounds), with voice ducking. Loudness-normalized with ffmpeg.

## Rebuild
Run these from `source/`, after `pip install pycairo kokoro-onnx soundfile scipy` and downloading `kokoro-v1.0.onnx` and `voices-v1.0.bin` from the kokoro-onnx GitHub releases. Update the model paths in `voice.py` to wherever you saved them.
```
python3 voice.py                          # narration -> vo_*.wav, vo.json
python3 audio.py                          # score + sfx + mix -> mix.wav
python3 render.py video video_only.mp4    # 3,600 frames
ffmpeg -i video_only.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 256k -movflags +faststart out.mp4
```
