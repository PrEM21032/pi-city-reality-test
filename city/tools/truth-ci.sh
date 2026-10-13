#!/usr/bin/env bash
# CI entry point: verify the pinned PI City snapshot, then run the truth-layer
# attack suite against it. Fails closed: a missing or altered snapshot is a
# failure, never a run where every test silently skips.
set -euo pipefail
cd "$(dirname "$0")/../.."

node --test city/tools/verify-snapshot.test.mjs

SNAP="$(node city/tools/verify-snapshot.mjs "${PI_CITY_SNAPSHOT_SHA:-}")"
echo "verified snapshot: $SNAP"

OUT="$(mktemp)"
PI_CITY_HTML="$SNAP" node --test --test-reporter=tap truth-tests/*.test.mjs | tee "$OUT"

# The harness skips everything when it cannot load the snapshot; treat that
# as a failure so CI can never be green on zero executed tests.
if grep -qE '^# skipped [1-9]' "$OUT"; then
  echo "truth-tests skipped tests: snapshot not loaded" >&2
  exit 1
fi
grep -E '^# (tests|pass|fail|todo)' "$OUT"
