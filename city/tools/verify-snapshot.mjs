// Checks that a PI City snapshot file is byte-for-byte the pinned one.
// Usage: node city/tools/verify-snapshot.mjs [sha256] [--file path] [--pins path]
// Prints the verified file path on success; exits 1 on any mismatch or absence.
import { readFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

export function verify({ pinsPath = resolve(root, "city/snapshots/pins.json"), sha, file } = {}) {
  const pins = JSON.parse(readFileSync(pinsPath, "utf8"));
  sha = sha || pins.current;
  const pin = pins.snapshots && pins.snapshots[sha];
  if (!pin) return { ok: false, reason: `no pin for ${sha}` };
  if (pin.sha256 !== sha) return { ok: false, reason: "pin entry sha256 does not match its key" };
  const path = resolve(root, file || pin.file);
  if (!existsSync(path)) return { ok: false, reason: `snapshot file missing: ${path}` };
  const bytes = readFileSync(path);
  const got = createHash("sha256").update(bytes).digest("hex");
  if (bytes.length !== pin.bytes) return { ok: false, reason: `size ${bytes.length} != pinned ${pin.bytes}` };
  if (got !== sha) return { ok: false, reason: `sha256 ${got} != pinned ${sha}` };
  return { ok: true, path, pin };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const a = process.argv.slice(2), opt = (k) => (a.includes(k) ? a[a.indexOf(k) + 1] : undefined);
  const r = verify({ sha: a[0] && !a[0].startsWith("--") ? a[0] : undefined, file: opt("--file"), pinsPath: opt("--pins") });
  if (!r.ok) { console.error("snapshot verification FAILED: " + r.reason); process.exit(1); }
  console.log(r.path);
}
