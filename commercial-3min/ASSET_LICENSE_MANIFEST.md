# Asset & license manifest — PI StationOS 3-minute film

Total spend: **$0**. No paid tools, stock footage, stock music, or subscriptions.

| Asset | Source | License / rights | Used for |
|---|---|---|---|
| `authentic.mp4` | Supplied by the store owner (real footage of the store) | Owner's own footage; used with the owner's permission | All footage (**pending: not yet received in this session**) |
| `earlier.mp4` | Earlier PI StationOS concept film (procedural illustration) | Created in this project | Reference only for the PI mark and product ideas; **no frames used** |
| Narration voice | Kokoro-82M via `kokoro-onnx` (voice `am_michael`), run offline | Apache-2.0 (model weights and code) | All narration |
| Score, sound design | Synthesized from scratch in `audio.py` (numpy/scipy) | Original work for this project; no samples | Music, UI sounds, swells, taps |
| Location sound | Audio track of `authentic.mp4` (if present) | Owner's own footage | Low ambience bed under shots |
| Interface graphics, PI mark, captions | Drawn in code with pycairo (`timeline.py`, `lib.py`) | Original work for this project | All simulations, titles, captions |
| Fonts | Inter / Inter Display (rsms) · DejaVu | SIL Open Font License 1.1 · Bitstream Vera/DejaVu license | All on-screen type |
| Speech check | Whisper small.en via sherpa-onnx (offline) | MIT (model) · Apache-2.0 (sherpa-onnx) | QA only: transcribes narration to check intelligibility; not in the film |
| Software | Python, pycairo (LGPL-2.1/MPL-1.1), numpy/scipy (BSD), FFmpeg + libx264 (GPL), Pillow (HPND) | Free / open source | Rendering, encoding, analysis |

## Truth controls built into the film
- Every PI interface shows **CONCEPT SIMULATION — ILLUSTRATIVE DATA** for its whole time on screen, including inside the phone UI.
- Footage-only scenes are tagged **REAL STORE FOOTAGE**. No synthetic imagery is presented as real.
- All figures are fictional samples. Nothing claims a live POS, pump, supplier, payroll, or other integration, predictive accuracy, placed orders, or measured savings.
- The reorder is shown as **DRAFT · NOT SENT**, then approved by the owner and added to *the owner's* order list. PI does not place the order.
- The close says: "Concept stage. Not connected to this store today." No 30-day pilot is offered.
- The film makes no claims about competitors.
- No people are invented: roles ("evening lead", "overnight lead") appear only as text inside the simulated interface.
