# PI StationOS: Irvington Food Mart film (3:06, 1080p)

**Watch:** `PI_StationOS_Irvington_Food_Mart_3min_1080p_share.mp4` (H.264, about 4 Mbps, 93 MB). A higher-bitrate master (CRF 16, 239 MB) is rendered by the project; it's too large for GitHub.

Built on 11 real photos of the store, with narration, original score, captions, and labeled concept simulations.

| Time | Sequence | Cause → decision → outcome |
|---|---|---|
| 0:00–0:25 | The real store: main aisle, Food Mart banner, counter, pizza counter, coffee bar, candy aisle, energy-drink coolers | One store, constant decisions |
| 0:25–0:50 | Four separate views: fuel totals sheet (illustrative), cooler wall, register, food counter; attention jumps between them | Separate problems, chased one at a time |
| 0:50–1:31 | Inventory: old way (shortage found on an empty shelf), then the PI concept: sales-pace and stock signals, flag, why and draft reorder (*not sent*), owner edits 2→3 cases and approves | Full loop; the owner decides |
| 1:31–2:05 | Fuel and store in one operating picture: evening fuel visits up, inside visits flat. "Food sales alone: cut prep" vs "with fuel in view: staff the counter 5–8 PM" | Context changes the decision |
| 2:05–2:24 | Shift handoff: done / open / exception (drawer $14.20 under), a specific next action, Assigned → Seen → Done | Follow-through the owner can see |
| 2:24–2:36 | Owner control on a phone: Approve / Edit / Decline; approved | Informed and in control |
| 2:36–3:06 | Invitation: a proposed way to run the whole station; what it's designed to catch earlier; concept stage, not connected today; **See the concept. Shape the pilot. Ask for a demo.** | Call to action |

## Files
- `SHOT_LIST_EDIT.md`: exact shot list (every photo, crop, move and timing)
- `NARRATION_TRANSCRIPT.md`: narration with timecodes, plus on-screen text
- `captions.srt`: captions (also burned into the video)
- `ASSET_LICENSE_MANIFEST.md`: assets, licenses and truth controls
- `project/`: editable render pipeline (Python/pycairo/FFmpeg)

## QA (final render)
- 186.000 s, 1920×1080, 30 fps (5,580 frames), AAC 48 kHz stereo; full decode with no errors.
- Loudness -13.9 LUFS integrated, -0.9 dBTP.
- Narration intelligibility, measured by an offline Whisper transcription of the final mix: 1.73% word error. The only misses are the brand name, written as "PiStation OS".
- Reviewed frame by frame in timecoded contact sheets every 3 s: labels, captions, spelling and layout.

## Rebuild
From `project/` (needs `pip install pycairo kokoro-onnx soundfile scipy` and the Kokoro model files for `narration.py`):
```
python3 narration.py && python3 audio.py && python3 make_docs.py
python3 compose.py video film_video.mp4
ffmpeg -i film_video.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 256k film.mp4
```
To add pump footage later, put it in `project/photos/` (stills or video) and point the slots in `timeline.py` at it.
