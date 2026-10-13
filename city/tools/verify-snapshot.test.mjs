import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { verify } from "./verify-snapshot.mjs";

const dir = mkdtempSync(join(tmpdir(), "pin-"));
const body = Buffer.from("<!doctype html><p>snapshot</p>");
const sha = createHash("sha256").update(body).digest("hex");
const file = join(dir, "snap.html");
writeFileSync(file, body);
const pins = join(dir, "pins.json");
writeFileSync(pins, JSON.stringify({ current: sha, snapshots: { [sha]: { sha256: sha, bytes: body.length, file } } }));

test("the pinned file verifies", () => {
  assert.equal(verify({ pinsPath: pins }).ok, true);
});
test("a one-byte change is rejected", () => {
  const bad = join(dir, "bad.html");
  writeFileSync(bad, Buffer.concat([body.subarray(0, -1), Buffer.from("!")]));
  const r = verify({ pinsPath: pins, file: bad });
  assert.equal(r.ok, false);
  assert.match(r.reason, /sha256/);
});
test("a missing file is rejected, not skipped", () => {
  const r = verify({ pinsPath: pins, file: join(dir, "nope.html") });
  assert.equal(r.ok, false);
  assert.match(r.reason, /missing/);
});
test("an unpinned hash is rejected", () => {
  assert.equal(verify({ pinsPath: pins, sha: "0".repeat(64) }).ok, false);
});
