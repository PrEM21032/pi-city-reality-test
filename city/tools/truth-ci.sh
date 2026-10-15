#!/usr/bin/env bash
# CI entry point: verify the pinned PI City snapshot, then run the shared
# attack cases against both the city's truth code (from the snapshot) and the
# reference truth core. Fails closed: a missing or altered snapshot, any
# skipped city case, any failure, or any todo in the reference is a failure.
set -euo pipefail
cd "$(dirname "$0")/../.."

node --test --test-reporter=tap city/tools/verify-snapshot.test.mjs >/dev/null
node --test --test-reporter=tap verifier/repo-status-verifier.test.mjs >/dev/null
node --test --test-reporter=tap verifier/fetch-attestation.test.mjs >/dev/null

SNAP="$(node city/tools/verify-snapshot.mjs "${PI_CITY_SNAPSHOT_SHA:-}")"
echo "verified snapshot: $SNAP"

CITY="$(mktemp)" REF="$(mktemp)"
PI_CITY_HTML="$SNAP" node --test --test-reporter=tap truth-tests/*.test.mjs > "$CITY"
PI_CITY_HTML="$SNAP" node --test --test-reporter=tap reference/*.test.mjs > "$REF"

# The city harness skips everything when it cannot load the snapshot.
if grep -qE '^# skipped [1-9]' "$CITY"; then echo "city cases skipped: snapshot not loaded" >&2; exit 1; fi
# The reference must hold every property outright.
if ! grep -qE '^# todo 0$' "$REF" || ! grep -qE '^# skipped 0$' "$REF"; then echo "reference has todo or skipped tests" >&2; exit 1; fi

summary() { echo "$1: $(grep -E '^# (tests|pass|fail|todo|skipped)' "$2" | sed 's/^# //' | tr '\n' ' ')"; }
summary "city      " "$CITY"
summary "reference " "$REF"
echo "known gaps in the city (todo):"
grep -E '^not ok .* # TODO' "$CITY" | sed -E 's/^not ok [0-9]+ - /  /; s/ # TODO.*//'
