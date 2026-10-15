// Deterministic fixture tests for the attestation adapter. No network, no
// credentials: the GitHub client is a mock serving recorded response shapes.
// Fixture fields follow the official OpenAPI schemas (github/rest-api-description,
// "GitHub v3 REST API" 1.1.4): workflow-run requires id, display_title, event,
// status, conclusion, head_sha, path, created_at, updated_at, repository, …;
// artifact has id, name, expired, digest ("sha256:…", upload-artifact v4+),
// workflow_run {id, head_sha}.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import zlib from "node:zlib";
import { buildAttestation, fetchRunAttestation, normalizeWorkflowPath, readZipEntries, unconfiguredHttp, artifactNameFor, AttestationError } from "./fetch-attestation.mjs";
import { checkRunAttestation } from "../reference/attestation.mjs";
import * as core from "../reference/truth-core.mjs";
import * as imp from "../reference/import-rows.mjs";
import { DEF_RS, p2Rows, SID_A, clone } from "../truth-tests/cases.mjs";

const REPO = "PrEM21032/pi-city-reality-test";
const GHA_ID = `gha:${REPO}/123456789/1`;
const WF_SHA = "a".repeat(40);
const FETCHER = "fetcher:city-trust-service";
const TRUST = { repository: REPO, workflow_path: ".github/workflows/repo-status-verify.yml", workflow_shas: [WF_SHA], fetchers: [FETCHER] };
const DATA = { branch_count: 1, default_branch: "main", head_sha: "3515b3d858afac8ac71a23a585bcd586dcf62006", repo_url: `https://github.com/${REPO}` };
const RECORD = { nonce: "veri0001", checked_at: "2026-10-13T08:02:53Z", exit_code: 0, run_session: GHA_ID, path: "github-action",
  evidence_url: `https://github.com/${REPO}/actions/runs/123456789/attempts/1`, verifier: "verifier/repo-status-verifier.mjs", data: DATA };

// Minimal ZIP writer for fixtures (deflate, no data descriptor).
function zip(files) {
  const locals = [], centrals = []; let off = 0;
  for (const [name, content] of files) {
    const nameB = Buffer.from(name), data = Buffer.from(content), comp = zlib.deflateRawSync(data), crc = zlib.crc32(data);
    const lh = Buffer.alloc(30); lh.writeUInt32LE(0x04034b50, 0); lh.writeUInt16LE(20, 4); lh.writeUInt16LE(8, 8); lh.writeUInt32LE(crc, 14);
    lh.writeUInt32LE(comp.length, 18); lh.writeUInt32LE(data.length, 22); lh.writeUInt16LE(nameB.length, 26);
    const ch = Buffer.alloc(46); ch.writeUInt32LE(0x02014b50, 0); ch.writeUInt16LE(20, 4); ch.writeUInt16LE(20, 6); ch.writeUInt16LE(8, 10); ch.writeUInt32LE(crc, 16);
    ch.writeUInt32LE(comp.length, 20); ch.writeUInt32LE(data.length, 24); ch.writeUInt16LE(nameB.length, 28); ch.writeUInt32LE(off, 42);
    locals.push(lh, nameB, comp); centrals.push(ch, nameB); off += 30 + nameB.length + comp.length;
  }
  const cd = Buffer.concat(centrals), e = Buffer.alloc(22);
  e.writeUInt32LE(0x06054b50, 0); e.writeUInt16LE(files.length, 8); e.writeUInt16LE(files.length, 10); e.writeUInt32LE(cd.length, 12); e.writeUInt32LE(off, 16);
  return Buffer.concat([...locals, cd, e]);
}
const sha = (b) => createHash("sha256").update(b).digest("hex");
const ZIP = zip([["record.json", JSON.stringify(RECORD)]]);
const RUN = () => ({
  id: 123456789, node_id: "WFR_x", run_attempt: 1, run_number: 7, name: "repo-status-verify", head_branch: "main", head_sha: WF_SHA,
  path: `${REPO}/.github/workflows/repo-status-verify.yml@main`, display_title: "repo-status-verify veri0001", event: "workflow_dispatch",
  status: "completed", conclusion: "success", workflow_id: 42, created_at: "2026-10-13T08:02:30Z", updated_at: "2026-10-13T08:03:10Z",
  repository: { full_name: REPO }, head_repository: { full_name: REPO },
});
const ARTS = (zipBuf = ZIP) => ({ total_count: 1, artifacts: [{ id: 555, node_id: "MDg6", name: artifactNameFor("veri0001"), size_in_bytes: zipBuf.length,
  expired: false, digest: `sha256:${sha(zipBuf)}`, created_at: "2026-10-13T08:03:00Z", expires_at: "2027-01-11T08:03:00Z", updated_at: "2026-10-13T08:03:00Z",
  workflow_run: { id: 123456789, head_sha: WF_SHA } }] });
const input = (m = {}) => ({ identity: GHA_ID, nonce: "veri0001", runAttempt: RUN(), artifactList: ARTS(), artifactZip: ZIP, fetchedBy: FETCHER, fetchedAt: "2026-10-13T08:05:00Z", ...m });
const refuses = (m, re) => assert.throws(() => buildAttestation(input(m)), (e) => e instanceof AttestationError && re.test(e.message));
const CTX = { identity: GHA_ID, verification: { nonce: "veri0001", at: RECORD.checked_at, facts: DATA }, request: { nonce: "veri0001", at: "2026-10-13T08:02:25Z" },
  execution: { at: "2026-10-13T08:01:59Z", facts: DATA }, executorId: SID_A, requestedFacts: DEF_RS.verifier.match, trust: TRUST };

// ---- positive control: adapter output satisfies the reference contract -------------
test("control: recorded API responses become an attestation the reference accepts", () => {
  const att = buildAttestation(input());
  assert.equal(att.run.path, ".github/workflows/repo-status-verify.yml");
  assert.deepEqual(checkRunAttestation(att, CTX), { ok: true, failures: [] });
  const rows = p2Rows({ execRun: SID_A, execFire: SID_A, verRun: GHA_ID, verFire: null });
  const lvl = core.judge(imp.importProtocol2(DEF_RS, rows.page, rows.back), { mission: DEF_RS.id, requestedFacts: DEF_RS.verifier.match, scope: DEF_RS.permission.scope, attestations: [att], trust: TRUST }).level;
  assert.equal(lvl, core.LEVEL.REAL);
});

// ---- run attempt: identity, missing and malformed fields ----------------------------
test("run id, attempt and repository must equal the claimed identity", () => {
  refuses({ runAttempt: { ...RUN(), id: 1 } }, /run id differs/);
  refuses({ runAttempt: { ...RUN(), run_attempt: 2 } }, /attempt differs/);
  refuses({ runAttempt: { ...RUN(), repository: { full_name: "PrEM21032/other" }, path: ".github/workflows/repo-status-verify.yml" } }, /repository differs/);
  refuses({ identity: "gha:PrEM21032/pi-city-reality-test/123456789" }, /not a GitHub Actions run identity/);
});
for (const field of ["id", "run_attempt", "head_sha", "event", "status", "conclusion", "display_title", "created_at", "updated_at"]) {
  test(`missing run.${field} is an explicit failure`, () => {
    const r = RUN(); delete r[field];
    refuses({ runAttempt: r }, new RegExp(`run\\.${field} missing`));
  });
}
test("in-progress run (conclusion null) is refused, not treated as success", () => {
  refuses({ runAttempt: { ...RUN(), status: "in_progress", conclusion: null } }, /run\.conclusion missing/);
});
test("missing repository, malformed sha, bad timestamps and wrong types are refused", () => {
  const r = RUN(); delete r.repository; refuses({ runAttempt: r }, /run\.repository\.full_name missing/);
  refuses({ runAttempt: { ...RUN(), head_sha: "abc" } }, /40-character/);
  refuses({ runAttempt: { ...RUN(), created_at: "yesterday" } }, /not a timestamp/);
  refuses({ runAttempt: { ...RUN(), id: "123456789" } }, /run\.id is not integer/);
  refuses({ runAttempt: null }, /run\.id missing/);
});

// ---- workflow path: exactly two documented forms ------------------------------------
test("workflow path: the documented full form and the bare form normalise; anything else is refused", () => {
  assert.equal(normalizeWorkflowPath(`${REPO}/.github/workflows/repo-status-verify.yml@main`, REPO), ".github/workflows/repo-status-verify.yml");
  assert.equal(normalizeWorkflowPath(".github/workflows/repo-status-verify.yml", REPO), ".github/workflows/repo-status-verify.yml");
  for (const bad of [`PrEM21032/other/.github/workflows/repo-status-verify.yml@main`, `${REPO}/.github/workflows/repo-status-verify.yml`,
    `${REPO}/.github/workflows/repo-status-verify.yml@`, `${REPO}/.github/workflows/a.yml@x@y`, `${REPO}/other/repo-status-verify.yml@main`,
    "repo-status-verify.yml", ".github/workflows/../x.yml"]) {
    assert.throws(() => normalizeWorkflowPath(bad, REPO), /ambiguous or foreign workflow path/, bad);
  }
  refuses({ runAttempt: { ...RUN(), path: undefined } }, /run\.path missing/);
});

// ---- artifact selection and binding -------------------------------------------------
test("exactly one artifact for this nonce, unexpired, bound to this run and commit", () => {
  const a = ARTS();
  refuses({ artifactList: { total_count: 0, artifacts: [] } }, /no artifact named/);
  refuses({ artifactList: { total_count: 2, artifacts: [a.artifacts[0], { ...a.artifacts[0], id: 556 }] } }, /more than one artifact/);
  refuses({ artifactList: { total_count: 1, artifacts: [{ ...a.artifacts[0], expired: true }] } }, /expired/);
  refuses({ artifactList: { total_count: 1, artifacts: [{ ...a.artifacts[0], expired: undefined }] } }, /expired or expiry unknown/);
  refuses({ artifactList: { total_count: 1, artifacts: [{ ...a.artifacts[0], workflow_run: { id: 1, head_sha: WF_SHA } }] } }, /not from this run/);
  refuses({ artifactList: { total_count: 1, artifacts: [{ ...a.artifacts[0], workflow_run: null }] } }, /not from this run/);
  refuses({ artifactList: { total_count: 1, artifacts: [{ ...a.artifacts[0], workflow_run: { id: 123456789, head_sha: "b".repeat(40) } }] } }, /run's commit/);
  refuses({ artifactList: { total_count: 3, artifacts: a.artifacts } }, /paginated or incomplete/);
  refuses({ artifactList: {} }, /artifact list missing/);
});
test("artifact digest must be present (upload-artifact v4+) and well-formed", () => {
  const a = ARTS().artifacts[0];
  refuses({ artifactList: { total_count: 1, artifacts: [{ ...a, digest: null }] } }, /digest missing or malformed/);
  refuses({ artifactList: { total_count: 1, artifacts: [{ ...a, digest: sha(ZIP) }] } }, /digest missing or malformed/);
});

// ---- archive integrity and contents ----------------------------------------------------
test("archive bytes must match the digest GitHub reports", () => {
  const tampered = Buffer.from(ZIP); tampered[tampered.length - 30] ^= 1;
  refuses({ artifactZip: tampered }, /does not match its reported digest/);
  refuses({ artifactZip: undefined }, /archive missing/);
});
const withZip = (z) => ({ artifactZip: z, artifactList: ARTS(z) });
test("archive must hold exactly one entry, record.json, containing a JSON object", () => {
  refuses(withZip(zip([])), /exactly one entry/);
  refuses(withZip(zip([["record.json", "{}"], ["extra.txt", "x"]])), /exactly one entry/);
  refuses(withZip(zip([["other.json", JSON.stringify(RECORD)]])), /exactly one entry, record\.json/);
  refuses(withZip(zip([["record.json", "not json"]])), /not valid JSON/);
  refuses(withZip(zip([["record.json", "[1,2]"]])), /not an object/);
});
test("corrupt or unsupported archives are refused", () => {
  refuses(withZip(Buffer.from("PK not really a zip, just text that is long enough")), /end-of-central-directory/);
  const crcBad = Buffer.from(ZIP); crcBad.writeUInt32LE(0, crcBad.indexOf(Buffer.from([0x50, 0x4b, 0x01, 0x02])) + 16);
  refuses(withZip(crcBad), /CRC mismatch/);
  const enc = Buffer.from(ZIP); enc.writeUInt16LE(1, enc.indexOf(Buffer.from([0x50, 0x4b, 0x01, 0x02])) + 8);
  refuses(withZip(enc), /encrypted/);
  const z64 = Buffer.from(ZIP); z64.writeUInt16LE(0xffff, z64.length - 22 + 10);
  refuses(withZip(z64), /zip64/);
});
test("each structural ZIP check fails on its own, with an explicit error", () => {
  const cd = ZIP.indexOf(Buffer.from([0x50, 0x4b, 0x01, 0x02])), eocd = ZIP.length - 22;
  const bad = (edit, re) => { const b = Buffer.from(ZIP); edit(b); assert.throws(() => readZipEntries(b), (e) => e instanceof AttestationError && re.test(e.message)); };
  assert.throws(() => readZipEntries(Buffer.alloc(10)), (e) => e instanceof AttestationError && /missing or truncated/.test(e.message));
  assert.throws(() => readZipEntries("PK"), (e) => e instanceof AttestationError && /missing or truncated/.test(e.message));
  bad((b) => b.writeUInt16LE(1, eocd + 4), /multi-disk/);
  bad((b) => b.writeUInt32LE(1, eocd + 16), /corrupt central directory/);
  bad((b) => b.writeUInt32LE(0xffffffff, cd + 20), /zip64 entries/);
  bad((b) => b.writeUInt32LE(0, 0), /corrupt local header/);
  bad((b) => b.writeUInt32LE(1_000_000, cd + 20), /truncated entry/);
  bad((b) => b.writeUInt32LE(ZIP.readUInt32LE(cd + 24) + 1, cd + 24), /size mismatch/);
  assert.equal(readZipEntries(ZIP).length, 1);   // the unmodified fixture still reads
});
test("invalid nonce, fetcher or fetch time is refused before any data is trusted", () => {
  refuses({ nonce: "x" }, /invalid nonce/);
  refuses({ nonce: undefined }, /invalid nonce/);
  refuses({ fetchedBy: "" }, /fetchedBy missing/);
  refuses({ fetchedBy: 7 }, /fetchedBy missing/);
  refuses({ fetchedAt: "not a time" }, /fetchedAt missing/);
  refuses({ fetchedAt: undefined }, /fetchedAt missing/);
});
test("reader also handles an archive written by the system zip tool (data descriptor form), when available", (t) => {
  let real;
  try {
    const dir = mkdtempSync(join(tmpdir(), "ziprec-"));
    writeFileSync(join(dir, "record.json"), JSON.stringify(RECORD));
    execFileSync("zip", ["-X", "-q", "-fd", join(dir, "a.zip"), "record.json"], { cwd: dir });
    real = readFileSync(join(dir, "a.zip"));
  } catch { return t.skip("zip tool not available"); }
  const entries = readZipEntries(real);
  assert.deepEqual(entries.map((e) => e.name), ["record.json"]);
  assert.deepEqual(JSON.parse(entries[0].data.toString()), RECORD);
  assert.deepEqual(checkRunAttestation(buildAttestation(input(withZip(real))), CTX), { ok: true, failures: [] });
});

// ---- the adapter does not decide trust: tampered facts still fail the reference ---------
test("adapter output with altered facts or the wrong nonce is rejected by the reference contract", () => {
  const z = zip([["record.json", JSON.stringify({ ...RECORD, data: { ...DATA, head_sha: "f".repeat(40) } })]]);
  assert.ok(checkRunAttestation(buildAttestation(input(withZip(z))), CTX).failures.includes("row facts differ from the attested record"));
  const t2 = buildAttestation(input({ runAttempt: { ...RUN(), display_title: "repo-status-verify other0001" } }));
  assert.ok(checkRunAttestation(t2, CTX).failures.includes("run was not dispatched for this nonce"));
});

// ---- network boundary --------------------------------------------------------------------
test("orchestration makes exactly the three documented read-only calls, in order", async () => {
  const calls = [];
  const http = {
    async getJSON(p) { calls.push(["GET", p]); return p.includes("/attempts/") ? RUN() : ARTS(); },
    async downloadArtifactZip(p) { calls.push(["ZIP", p]); return ZIP; },
  };
  const att = await fetchRunAttestation({ identity: GHA_ID, nonce: "veri0001", http, fetchedBy: FETCHER, now: () => new Date("2026-10-13T08:05:00.250Z") });
  assert.deepEqual(calls, [
    ["GET", `/repos/${REPO}/actions/runs/123456789/attempts/1`],
    ["GET", `/repos/${REPO}/actions/runs/123456789/artifacts?name=${artifactNameFor("veri0001")}&per_page=100`],
    ["ZIP", `/repos/${REPO}/actions/artifacts/555/zip`],
  ]);
  assert.equal(att.fetched_at, "2026-10-13T08:05:00Z");
  assert.deepEqual(checkRunAttestation(att, CTX), { ok: true, failures: [] });
});
test("the default client refuses: no credential ships, artifact download needs a token", async () => {
  await assert.rejects(fetchRunAttestation({ identity: GHA_ID, nonce: "veri0001", fetchedBy: FETCHER }), /not configured: no credential is provided by design/);
  await assert.rejects(unconfiguredHttp.downloadArtifactZip("/x"), /requires an authenticated GitHub token/);
});
test("orchestration refuses before downloading when the artifact is missing or duplicated", async () => {
  let downloads = 0;
  const mk = (arts) => ({ async getJSON(p) { return p.includes("/attempts/") ? RUN() : arts; }, async downloadArtifactZip() { downloads++; return ZIP; } });
  await assert.rejects(fetchRunAttestation({ identity: GHA_ID, nonce: "veri0001", http: mk({ total_count: 0, artifacts: [] }), fetchedBy: FETCHER }), /no artifact named/);
  const a = ARTS().artifacts[0];
  await assert.rejects(fetchRunAttestation({ identity: GHA_ID, nonce: "veri0001", http: mk({ total_count: 2, artifacts: [a, { ...a, id: 556 }] }), fetchedBy: FETCHER }), /more than one/);
  assert.equal(downloads, 0);
});
