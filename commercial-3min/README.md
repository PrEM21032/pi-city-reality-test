# PI StationOS: 3-minute business-opportunity film

## Status: **real footage not received**
`authentic.mp4`, `SHOT_LIST.md` and `earlier.mp4` were not available in the production environment: not in the repo, and not in the upload folder. The film is built around the store's real footage, and it won't be finished with substitute imagery.

Everything that doesn't depend on the footage is done:

| Deliverable | File | State |
|---|---|---|
| Animatic, 3:00, 1080p, full narration, score and captions; footage shown as labeled slots | `PI_StationOS_3min_ANIMATIC_footage_pending.mp4` | Done (pacing and sync reference, **not** the final film) |
| Editable project / render scripts | `project/` | Done |
| Exact shot list (timeline, crops and moves final; source in-points after inspection) | `SHOT_LIST_EDIT.md` | Generated from `project/timeline.py` |
| Narration transcript | `NARRATION_TRANSCRIPT.md` | Done |
| Captions | `captions.srt` (also burned in) | Done |
| Asset / license manifest | `ASSET_LICENSE_MANIFEST.md` | Done |
| Final MP4 using `authentic.mp4` | — | **Blocked on footage** |

## Structure (3:00)
| Time | Sequence | Cause → decision → outcome |
|---|---|---|
| 0:00–0:25 | The real station: night pumps → entrance → counter → food service → aisles → coolers | One store, constant decisions |
| 0:25–0:50 | Owner's problem: four real views split apart; attention jumps tile to tile | Separate problems, chased one at a time |
| 0:50–1:31 | Inventory: **old way** (shortage found on an empty shelf) → **PI concept** rail: sales-pace signal + stock signal → flag → why + draft reorder (*not sent*) → owner edits 2→3 cases and approves → added to the owner's order list | Full loop, owner decides |
| 1:31–2:05 | One operating picture: pumps → inside → split screen → combined fuel/inside chart; "food sales alone: cut prep" vs "with pumps in view: staff the counter" | Context changes the decision |
| 2:05–2:24 | Shift handoff: done / open / exception (drawer $14.20 under) → specific next action → Assigned → Seen → Done | Follow-through the owner can see |
| 2:24–2:36 | Owner control: phone recommendation, Approve / Edit / Decline, approved | Emotional payoff: informed and in control |
| 2:36–3:00 | Real store and pumps; "a proposed way…"; "Concept stage: not connected to this store today"; end card **See the concept. Shape the pilot. Ask for a demo.** | Invitation (no 30-day pilot offered) |

## Finishing once the footage arrives
1. Put the files in `project/src/` (or set `FOOTAGE_DIR`).
2. `python3 inspect_footage.py src/authentic.mp4 inspect/`: probe, cut detection, per-second motion and sharpness, and timecoded contact sheets. Read these together with `SHOT_LIST.md`.
3. Set each `SLOTS` in-point (and its focus point) in `timeline.py`. Adjust crops and layouts if the footage is vertical (`FIT='pillar'` gives a blurred surround).
4. `python3 audio.py` (adds the footage's own location sound as an ambience bed), then `python3 make_docs.py` and `python3 compose.py video film.mp4`, then mux with loudnorm (see the animatic build).
5. QA: `review.py` (timecoded contact sheets), `mix_check.py` (speech recognition on the final mix), ffprobe and ebur128.

## QA results on the animatic
- 180.000 s, 1920×1080, 30 fps (5,400 frames), H.264 plus AAC 48 kHz stereo; full decode with no errors.
- Loudness -13.9 LUFS integrated, -1.1 dBFS peak.
- Narration intelligibility, measured by an offline Whisper-small transcription of the **final mix**: 1.97% word error rate. The only misses are the brand name, written as "PiStation OS". This measures intelligibility, not how natural the voice sounds; a person should still listen to it.
