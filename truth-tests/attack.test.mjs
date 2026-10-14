// Runs the shared attack cases (truth-tests/cases.mjs) against PI City's own
// truth code, extracted from a saved copy of the artifact (local/test proof
// only). Run: PI_CITY_HTML=/path/to/saved/artifact.html node --test truth-tests/*.test.mjs
// A case marked gapInCity states a property the city should have and lacks:
// it is reported as todo (a known gap) and does not fail the run.
import { test } from "node:test";
import assert from "node:assert/strict";
import { load } from "./extract.mjs";
import { CASES, cityAdapter } from "./cases.mjs";

const X = load();
const skip = X ? false : "set PI_CITY_HTML to a saved copy of the PI City artifact";
const c = X && cityAdapter(X, () => load());

for (const k of CASES) {
  const opts = { skip, todo: k.gapInCity ? "known gap in the city (see truth-tests/README.md)" : undefined };
  test(`[${k.id}] ${k.title}`, opts, async () => {
    assert.deepEqual(await k.city(c), k.expect.city);
  });
}
