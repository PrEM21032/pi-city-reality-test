# PI City truth-layer attack tests

Local/test proof only. Nothing here calls GitHub, fires a routine, or reads or
writes the live PI City database.

The PI City source lives in a private claude.ai artifact, not in this repo, so
it is not committed. `extract.mjs` pulls the truth-layer code (the `C` labels,
`Xt`/`Mt`, the legacy `reality-001` mission class and the protocol-2 mission
class) out of a saved copy of the artifact HTML and runs it in Node.

```
PI_CITY_HTML=/path/to/saved/pi-city.html node --test truth-tests/*.test.mjs
```

Without `PI_CITY_HTML` every test is skipped.

The cases live in `cases.mjs` and are shared with the reference truth core
(`../reference/`): each case is run against the city here and against the
reference in `reference/reference.test.mjs`, on the same row fixtures.

Cases marked `gapInCity` state a property PI City should have and currently
lacks. Here they are reported as known gaps (`todo`) and do not fail the run;
when a fix lands in the city, drop `gapInCity` so the property is enforced.

Result against artifact version `1791878073-4eb5`
(sha256 `ada22e8b785fb4fc95b23f0b8f986ad30465a81275f806371467ada5ec287843`),
2026-10-13: 20 cases (the original 19 plus 1b), 13 pass, 7 known gaps.
The reference passes all 20.

| Known gap | Why |
|---|---|
| [2] Same session executes and verifies, still REAL-VERIFIED (legacy) | the legacy receipt never records the executor's run, so the same-run check is skipped |
| [3] Hand-typed verification row with no run identity is REAL-VERIFIED (legacy) | the row's text is the only evidence |
| [7] A newer read-back that finds the issue gone leaves the mission REAL-VERIFIED | the passed state is pinned to the first good read; there is no reconciliation |
| [8] Resetting the mission turns a verified mission into NOT STARTED | the outcome lives in a deletable row |
| [15] Both runs `unrecorded` and no dispatch session: REAL-VERIFIED (protocol 2) | the independence check is skipped when the ids are unknown |
| [16] A session id with a trailing space counts as independent (protocol 2) | independence means two agent-written strings differ |
| [19] Two views completing the legacy mission fire two verify runs | the legacy path has only a per-view busy flag, no lease |
