"""Generate SHOT_LIST_EDIT.md, NARRATION_TRANSCRIPT.md, captions.srt from the same data the renderer uses."""
import json, sys
import timeline as TL
def tc(t): m, s = divmod(t, 60); return f"{int(m)}:{s:05.2f}"
def srt_tc(t): h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60; return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}"
RECT = {TL.FULL: "full frame", TL.LEFT: "split · left", TL.RIGHT: "split · right"}
for i, r in enumerate(TL.TILES): RECT[r] = f"quad tile {i + 1}"
SECTIONS = [(0, "A · The real station"), (25.5, "B · The owner's problem"), (50, "C · Inventory: before → after"),
            (90, "D · One operating picture"), (124.5, "E · Shift handoff + owner control"), (156, "F · Invitation")]
out = ["# Exact shot list — PI StationOS 3-minute film", "",
       "Source: `authentic.mp4` (real store footage). Source in/out = slot in-point + offset. "
       "All interface graphics are labeled **Concept simulation — illustrative data**.", ""]
pending = any(v[0] is None for v in TL.SLOTS.values())
if pending: out += ["> **Status:** footage slot in-points are not set yet (authentic.mp4 not received). Timeline positions, crops and durations are final; source times are filled in after inspection.", ""]
out += ["## Footage slots", "", "| Slot | Source in (s) | Usable length (s) | Content |", "|---|---|---|---|"]
for k, (a, ln, cx, cy, d) in TL.SLOTS.items(): out.append(f"| `{k}` | {'—' if a is None else f'{a:.2f}'} | {ln} | {d} |")
out += ["", "## Edit decision list", "", "| # | Film in | Film out | Dur | Slot | Source in → out | Layout | Move |", "|---|---|---|---|---|---|---|---|"]
sec = 0
for i, s in enumerate(sorted(TL.SHOTS, key=lambda s: (s["t"], str(s["rect"])))):
    while sec < len(SECTIONS) and s["t"] >= SECTIONS[sec][0]: out.append(f"| | **{SECTIONS[sec][1]}** | | | | | | |"); sec += 1
    a = TL.SLOTS[s["slot"]][0]; src = f"{a + s['off']:.2f} → {a + s['off'] + s['d']:.2f}" if a is not None else f"+{s['off']:.1f} → +{s['off'] + s['d']:.1f}"
    move = f"zoom {s['z0']:.2f}→{s['z1']:.2f}" + (f", pan {s['dx']:+.2f}" if s['dx'] else "") + (f", dimmed {int((1 - s['grade']) * 100)}% for overlay" if s['grade'] < 1 else "") + (f", {s['fade']:.1f}s dissolve in" if s['fade'] else ", cut")
    out.append(f"| {i + 1} | {tc(s['t'])} | {tc(s['t'] + s['d'])} | {s['d']:.1f}s | `{s['slot']}` | {src} | {RECT.get(s['rect'], 'custom')} | {move} |")
open("SHOT_LIST_EDIT.md", "w").write("\n".join(out) + "\n")

tr = ["# Narration transcript — PI StationOS 3-minute film", "",
      "Voice: Kokoro-82M `am_michael` (offline neural TTS). Spoken spelling “Pie Station O S” is used only for pronunciation; captions use “PI StationOS”.", "",
      "| In | Out | Narration |", "|---|---|---|"]
for m in TL.VO.values():
    for s in m["sentences"]: tr.append(f"| {tc(s['start'])} | {tc(s['end'])} | {s['text']} |")
tr += ["", "## On-screen text (simulation and title cards)", "",
       "- Persistent label on every interface: **CONCEPT SIMULATION — ILLUSTRATIVE DATA** (also inside the phone UI).",
       "- Footage-only scenes carry **REAL STORE FOOTAGE**.",
       "- Closing: “A proposed way to run the whole station with more clarity and control.” · “CONCEPT STAGE — Not connected to this store today. Built with owners.” · “See the concept. Shape the pilot. Ask for a demo.”",
       "- All figures (1.8× pace, ~14 on hand, $14.20, evening visit curves) are fictional sample values."]
open("NARRATION_TRANSCRIPT.md", "w").write("\n".join(tr) + "\n")
srt = []
for i, (a, b, s) in enumerate(TL.caption_units(), 1): srt += [str(i), f"{srt_tc(a)} --> {srt_tc(b)}", s, ""]
open("captions.srt", "w").write("\n".join(srt))
print("docs ok")
