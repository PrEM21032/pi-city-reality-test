"""Generate SHOT_LIST_EDIT.md, NARRATION_TRANSCRIPT.md, captions.srt from the same data the renderer uses."""
import json, sys
import timeline as TL
def tc(t): m, s = divmod(t, 60); return f"{int(m)}:{s:05.2f}"
def srt_tc(t): h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60; return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}"
RECT = {TL.FULL: "full frame", TL.LEFT: "split · left", TL.RIGHT: "split · right"}
for i, r in enumerate(TL.TILES): RECT[r] = f"quad tile {i + 1}"
SECTIONS = [(0, "A · The real station"), (25.5, "B · The owner's problem"), (50, "C · Inventory: before → after"),
            (90, "D · One operating picture"), (124.5, "E · Shift handoff + owner control"), (156, "F · Invitation")]
out = ["# Exact shot list — PI StationOS film (3:06)", "",
       "Visual source: 11 real photos of Irvington Food Mart supplied by the owner (`photos/`). Each shot is a still with a deliberate camera move (punch-in / pan). "
       "All PI interface graphics are labeled **Concept simulation — illustrative data**. No pump/forecourt photo was supplied, so fuel appears only as labeled illustrative data.", "",
       "## Photo sources", "", "| Slot | File | Content |", "|---|---|---|"]
for k, (f, cx, cy, d) in TL.SLOTS.items(): out.append(f"| `{k}` | `{f}` | {d} |")
out += ["", "## Edit decision list", "", "| # | In | Out | Dur | Photo | Layout | Move |", "|---|---|---|---|---|---|---|"]
SECTIONS = [(0, "A · The real store"), (25.5, "B · The owner's problem"), (50, "C · Inventory: before → after"),
            (90.8, "D · Fuel + store: one operating picture"), (124.5, "E · Shift handoff + owner control"), (156, "F · Invitation")]
sec = 0
for i, s in enumerate(sorted(TL.SHOTS, key=lambda s: (s["t"], str(s["rect"])))):
    while sec < len(SECTIONS) and s["t"] >= SECTIONS[sec][0]: out.append(f"| | **{SECTIONS[sec][1]}** | | | | | |"); sec += 1
    f, cx, cy, d = TL.SLOTS[s["slot"]]
    fx = s["cx"] if s["cx"] is not None else cx; fy = s["cy"] if s["cy"] is not None else cy
    move = f"zoom {s['z0']:.2f}→{s['z1']:.2f} on ({fx:.2f}, {fy:.2f})" + (f", pan {s['dx']:+.2f}" if s['dx'] else "") + (", blurred-surround pillar" if s['fit'] == 'pillar' else "") + (f", dimmed {int((1 - s['grade']) * 100)}% under interface" if s['grade'] < 1 else "") + (f", {s['fade']:.1f}s dissolve in" if s['fade'] else ", cut")
    out.append(f"| {i + 1} | {tc(s['t'])} | {tc(s['t'] + s['d'])} | {s['d']:.1f}s | `{f}` ({s['slot']}) | {RECT.get(s['rect'], 'custom')} | {move} |")
out += ["| | 0:25.5 | 0:50.0 | 24.5s | — (graphic) | quad tile 1 | Fuel totals sheet labeled *Illustrative figures* (no pump photo supplied) |"]
open("SHOT_LIST_EDIT.md", "w").write("\n".join(out) + "\n")

tr = ["# Narration transcript — PI StationOS film (3:06)", "",
      "Voice: Kokoro-82M `am_michael` (offline neural TTS). Spoken spelling “Pie Station O S” is used only for pronunciation; captions use “PI StationOS”.", "",
      "| In | Out | Narration |", "|---|---|---|"]
for m in TL.VO.values():
    for s in m["sentences"]: tr.append(f"| {tc(s['start'])} | {tc(s['end'])} | {s['text']} |")
tr += ["", "## On-screen text (simulation and title cards)", "",
       "- Persistent label on every interface: **CONCEPT SIMULATION — ILLUSTRATIVE DATA** (also inside the phone UI).",
       "- Photo-only scenes carry **REAL STORE PHOTO**.",
       "- Closing: “A proposed way to run the whole station with more clarity and control.” · “Designed to catch earlier: empty shelves / missed inside sales / loose ends — goals of the concept, no results measured yet.” · “CONCEPT STAGE — Not connected to this store today. Built with owners.” · “See the concept. Shape the pilot. Ask for a demo.”",
       "- All figures (fuel gallons, 1.8× pace, ~14 on hand, $14.20, evening visit curves) are fictional sample values."]
open("NARRATION_TRANSCRIPT.md", "w").write("\n".join(tr) + "\n")
srt = []
for i, (a, b, s) in enumerate(TL.caption_units(), 1): srt += [str(i), f"{srt_tc(a)} --> {srt_tc(b)}", s, ""]
open("captions.srt", "w").write("\n".join(srt))
print("docs ok")
