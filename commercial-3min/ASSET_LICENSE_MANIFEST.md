# Asset & license manifest: PI StationOS film (Irvington Food Mart, 3:06)

Total spend: **$0**. No paid tools, stock footage, stock music, or subscriptions.

| Asset | Source | License / rights | Used for |
|---|---|---|---|
| 11 store photos (`project/photos/`) | Supplied by the store owner: real photos of Irvington Food Mart | Owner's own photos, used with the owner's permission | Every real-store shot |
| Narration voice | Kokoro-82M via `kokoro-onnx` (voice `am_michael`), run offline | Apache-2.0 | All narration |
| Score, sound design, room tone | Synthesized from scratch in `audio.py` (numpy/scipy) | Original work; no samples | Music, UI sounds, ambience |
| Interface graphics, PI mark, captions | Drawn in code with pycairo | Original work | Simulations, titles, captions |
| Fonts | Inter / Inter Display · DejaVu | SIL OFL 1.1 · DejaVu license | All on-screen type |
| Speech check | Whisper small.en via sherpa-onnx (offline) | MIT · Apache-2.0 | QA only (intelligibility of the final mix) |
| Software | Python, pycairo, numpy/scipy, Pillow, FFmpeg/libx264 | Open source | Rendering and encoding |

Brands visible in the photos (Coca-Cola, Monster, Hunt Brothers Pizza, and others) are the store's real signage and merchandise as photographed. They're not endorsements, and none of them are used in PI graphics.

## Truth controls
- Every PI interface shows **CONCEPT SIMULATION — ILLUSTRATIVE DATA** for its whole time on screen, including inside the phone UI. Photo-only scenes carry **REAL STORE PHOTO**.
- No pump or forecourt imagery was supplied, so none is shown. Fuel appears only as data labeled *illustrative figures*.
- All figures are fictional. Nothing claims a live POS, pump, supplier, payroll, or other integration, predictive accuracy, placed orders, or measured savings.
- "Saves" is framed only as what the concept is designed to catch earlier: empty shelves, missed inside sales, and loose ends. On screen: "Goals of the concept — no results measured yet."
- The reorder is a **DRAFT · NOT SENT** until the owner edits and approves it; it then goes to *the owner's* order list.
- The close says: "Concept stage. Not connected to this store today." No 30-day pilot is offered, and the film makes no claims about competitors.
- No people are shown or invented.
