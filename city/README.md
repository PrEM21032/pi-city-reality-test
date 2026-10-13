# PI City source: version control and CI (PROVISIONAL)

**Destination status: PROVISIONAL.** This directory is staged on the isolated
branch `claude/practical-ramanujan-n5fydt` of `PrEM21032/pi-city-reality-test`.
That repository is the reality test's external target, not the PI City source
repository. Nothing here designates it as canonical, and `main` is unchanged.

## What is here

| Path | Purpose |
|---|---|
| `snapshots/pins.json` | Immutable pin of the city source: artifact `ffb65760-9daa-4256-b344-18fff633e13b`, version `1791878073-4eb5`, 284,841 bytes, sha256 `ada22e8b785fb4fc95b23f0b8f986ad30465a81275f806371467ada5ec287843` |
| `snapshots/<sha256>.html` | The snapshot itself. **Gitignored, never committed here** (see below) |
| `tools/verify-snapshot.mjs` | Fails unless a file is byte-for-byte the pinned snapshot |
| `tools/verify-snapshot.test.mjs` | Tests for the verifier: good, one-byte change, missing, unpinned |
| `tools/truth-ci.sh` | CI entry: verify the pin, then run the shared attack cases against the city (from the pinned file) and against `reference/`; fails closed on a missing or altered snapshot, a skipped city case, any failure, or any reference todo |
| `ci/truth-tests.yml` | Proposed GitHub Actions workflow. Deliberately outside `.github/workflows/`, so it never runs here |

Run locally, with the snapshot file in place:

```
city/tools/truth-ci.sh
```

## Why the snapshot is not committed

The PI City artifact is private. This repository is **public**. Committing the
snapshot here, even on a side branch, would publish the city source. It holds
no credentials (checked for API-key and token patterns) but does name trigger
IDs and the artifact URL. Obtain the file with a read of the artifact at the
pinned version and check it with `tools/verify-snapshot.mjs`.

## Decision needed before promoting

The owner must choose where PI City source lives:

1. **New private repository** (recommended), e.g. `PrEM21032/pi-city`.
   Commit `city/`, `truth-tests/` and the snapshot file, and move
   `ci/truth-tests.yml` to `.github/workflows/`. Keeps the source private and
   keeps the test target separate from the system under test.
2. **Make an existing private repository canonical.** Same steps.
3. **Make this repository private and canonical.** Not recommended: the
   system's code and its external test target would share one repository, so
   a mission could act on its own source.

Also decide: who may update `pins.json` (the pin is the trust root for CI), and
whether future artifact versions are pinned on every publish or only on
review.

Until then, the snapshot is staged locally and CI runs only by hand.
