// Adversarial tests for the GitHub Actions attestation boundary. A gha:
// identity, path or evidence_url in a row is only a claim; REAL-VERIFIED via
// an Actions run needs an attestation handed to the judge over a separate
// trust path, matching every term of the contract.
import { test } from "node:test";
import assert from "node:assert/strict";
import * as core from "./truth-core.mjs";
import * as imp from "./import-rows.mjs";
import { ATTESTATION_KIND, DEFAULT_TRUST, recordDigest, checkRunAttestation } from "./attestation.mjs";
import { DEF_RS, p2Rows, SID_A, SID_B, clone } from "../truth-tests/cases.mjs";

const { LEVEL } = core;
const GHA_ID = "gha:PrEM21032/pi-city-reality-test/123456789/1";
const WF_SHA = "a".repeat(40);
const FETCHER = "fetcher:city-trust-service";
const TRUST = { repository: "PrEM21032/pi-city-reality-test", workflow_path: ".github/workflows/repo-status-verify.yml", workflow_shas: [WF_SHA], fetchers: [FETCHER] };
const DATA = { branch_count: 1, default_branch: "main", head_sha: "3515b3d858afac8ac71a23a585bcd586dcf62006", repo_url: "https://github.com/PrEM21032/pi-city-reality-test" };

// Rows: executed by a Claude session, verified by a claimed Actions run.
const rows = (mut = (r) => r) => {
  const r = p2Rows({ execRun: SID_A, execFire: SID_A, verRun: GHA_ID, verFire: null });
  Object.assign(r.back.verifications.veri0001, { path: "github-action", evidence_url: "https://github.com/PrEM21032/pi-city-reality-test/actions/runs/123456789/attempts/1" });
  return mut(r);
};
// What a designated fetcher would hand over after reading GitHub's API itself.
const attestation = (mut = (a) => a) => {
  const record = { nonce: "veri0001", checked_at: "2026-10-13T08:02:53Z", exit_code: 0, run_session: GHA_ID, path: "github-action",
    evidence_url: "https://github.com/PrEM21032/pi-city-reality-test/actions/runs/123456789/attempts/1", verifier: "verifier/repo-status-verifier.mjs", data: clone(DATA) };
  const a = {
    kind: ATTESTATION_KIND, fetched_by: FETCHER, fetched_at: "2026-10-13T08:05:00Z",
    run: { id: 123456789, run_attempt: 1, repository: "PrEM21032/pi-city-reality-test", path: ".github/workflows/repo-status-verify.yml", head_sha: WF_SHA,
      event: "workflow_dispatch", status: "completed", conclusion: "success", display_title: "repo-status-verify veri0001",
      created_at: "2026-10-13T08:02:30Z", updated_at: "2026-10-13T08:03:10Z" },
    record,
  };
  a.record_sha256 = recordDigest(a.record);
  return mut(a);
};
const level = (r, opts = {}) => core.judge(imp.importProtocol2(DEF_RS, r.page, r.back),
  { mission: DEF_RS.id, requestedFacts: DEF_RS.verifier.match, scope: DEF_RS.permission.scope, ...opts }).level;
// Change the attested record and re-seal it, so only the targeted check can fail.
const reseal = (f) => (a) => { f(a); a.record_sha256 = recordDigest(a.record); return a; };

// ---- the claim alone ------------------------------------------------------------
test("[A0] a well-formed gha row alone stays EXECUTOR-REPORTED", () => {
  assert.equal(level(rows()), LEVEL.REPORTED);
  assert.equal(level(rows(), { trust: TRUST }), LEVEL.REPORTED);
  assert.equal(level(rows(), { trust: TRUST, policy: { independence: "distinct-path" } }), LEVEL.REPORTED);
});
test("[A0b] an attestation stored inside the database row is ignored", () => {
  assert.equal(level(rows((r) => { r.back.verifications.veri0001.attestation = attestation(); return r; }), { trust: TRUST }), LEVEL.REPORTED);
});
test("[A0c] a valid attestation does not pass under the default (empty) trust", () => {
  assert.equal(level(rows(), { attestations: [attestation()] }), LEVEL.REPORTED);
  assert.equal(DEFAULT_TRUST.workflow_shas.length + DEFAULT_TRUST.fetchers.length, 0);
});

// ---- the positive control --------------------------------------------------------
test("[A1] control: a complete, independently supplied attestation makes it REAL-VERIFIED", () => {
  assert.equal(level(rows(), { attestations: [attestation()], trust: TRUST }), LEVEL.REAL);
  assert.equal(level(rows(), { attestations: [attestation()], trust: TRUST, policy: { independence: "distinct-path" } }), LEVEL.REAL);
  assert.deepEqual(checkRunAttestation(attestation(), {
    identity: GHA_ID, verification: { nonce: "veri0001", at: "2026-10-13T08:02:53Z", facts: DATA }, request: { nonce: "veri0001", at: "2026-10-13T08:02:25Z" },
    execution: { at: "2026-10-13T08:01:59Z", facts: DATA }, executorId: SID_A, requestedFacts: DEF_RS.verifier.match, trust: TRUST }), { ok: true, failures: [] });
});

// ---- every term of the contract is enforced ---------------------------------------
const breaks = {
  "wrong attestation kind": (a) => { a.kind = "something-else"; return a; },
  "fetcher not designated by the owner": (a) => { a.fetched_by = "fetcher:someone-else"; return a; },
  "record altered after fetching (digest mismatch)": (a) => { a.record.data.head_sha = "b".repeat(40); return a; },
  "run id differs from the claimed identity": (a) => { a.run.id = 987654321; return a; },
  "run attempt differs from the claimed identity": (a) => { a.run.run_attempt = 2; return a; },
  "run in another repository": (a) => { a.run.repository = "PrEM21032/other"; return a; },
  "run of another workflow file": (a) => { a.run.path = ".github/workflows/other.yml"; return a; },
  "workflow commit not pinned": (a) => { a.run.head_sha = "c".repeat(40); return a; },
  "run not a manual dispatch": (a) => { a.run.event = "push"; return a; },
  "run still in progress": (a) => { a.run.status = "in_progress"; a.run.conclusion = null; return a; },
  "run failed": (a) => { a.run.conclusion = "failure"; return a; },
  "run dispatched for another nonce": (a) => { a.run.display_title = "repo-status-verify other0001"; return a; },
  "run started before the verify request": (a) => { a.run.created_at = "2026-10-13T08:02:00Z"; return a; },
  "attested record for another nonce": reseal((a) => { a.record.nonce = "other0001"; }),
  "attested record time outside the run": reseal((a) => { a.record.checked_at = "2026-10-13T09:00:00Z"; }),
  "attested read failed": reseal((a) => { a.record.exit_code = 128; }),
  "attested record names another run": reseal((a) => { a.record.run_session = "gha:PrEM21032/pi-city-reality-test/1/1"; }),
  "attested facts differ from the row": reseal((a) => { a.record.data.branch_count = 2; }),
  "attested head differs from row and execution": reseal((a) => { a.record.data.head_sha = "d".repeat(40); }),
};
for (const [name, mutate] of Object.entries(breaks)) {
  test(`[A2] ${name}: stays EXECUTOR-REPORTED`, () => {
    assert.equal(level(rows(), { attestations: [attestation(mutate)], trust: TRUST }), LEVEL.REPORTED);
  });
}
test("[A2] attestation fetched by the executor itself: stays EXECUTOR-REPORTED", () => {
  assert.equal(level(rows(), { attestations: [attestation((a) => { a.fetched_by = SID_A; return a; })], trust: { ...TRUST, fetchers: [FETCHER, SID_A] } }), LEVEL.REPORTED);
});
test("[A2] row time differs from the attested record: stays EXECUTOR-REPORTED", () => {
  assert.equal(level(rows((r) => { r.back.verifications.veri0001.checked_at = "2026-10-13T08:02:54Z"; return r; }), { attestations: [attestation()], trust: TRUST }), LEVEL.REPORTED);
});
test("[A2] attestation for a different claimed run does not cover this row", () => {
  assert.equal(level(rows((r) => { r.back.verifications.veri0001.run_session = "gha:PrEM21032/pi-city-reality-test/555/1"; return r; }), { attestations: [attestation()], trust: TRUST }), LEVEL.REPORTED);
});

// ---- Claude-session verification is unchanged; path strings prove nothing ----------
test("[A3] Claude-session verification keeps the distinct-run rule", () => {
  assert.equal(level(p2Rows()), LEVEL.REAL);
});
test("[A3] distinct-path is never satisfied by a writable path string", () => {
  const r = p2Rows({ execRun: SID_A, verRun: SID_B });
  r.back.verifications.veri0001.path = "github-action";
  assert.equal(level(r, { policy: { independence: "distinct-path" } }), LEVEL.REPORTED);
});

// ---- each term on its own: exactly one failure, so no check hides behind another --------
const CTX = () => ({
  identity: GHA_ID, verification: { nonce: "veri0001", at: "2026-10-13T08:02:53Z", facts: clone(DATA) },
  request: { nonce: "veri0001", at: "2026-10-13T08:02:25Z" }, execution: { at: "2026-10-13T08:01:59Z", facts: clone(DATA) },
  executorId: SID_A, requestedFacts: DEF_RS.verifier.match, trust: TRUST,
});
const only = (att, ctx, msg) => assert.deepEqual(checkRunAttestation(att, ctx).failures, [msg]);
test("[A4] a record changed after fetching, even in an unchecked field, breaks the digest", () => {
  only(attestation((a) => { a.record.verifier = "something-else"; return a; }), CTX(), "record digest does not match the attested record");
});
test("[A4] the verification must answer the mission's own verify request", () => {
  only(attestation(), { ...CTX(), request: { nonce: "other0001", at: "2026-10-13T08:02:25Z" } }, "verification does not answer the mission's verify request");
});
test("[A4] the run must start after the execution", () => {
  const ctx = { ...CTX(), request: { nonce: "veri0001", at: "2026-10-13T08:01:00Z" }, execution: { at: "2026-10-13T08:02:40Z", facts: clone(DATA) } };
  only(attestation(), ctx, "run started before the execution");
});
test("[A4] the attested read must happen inside the run", () => {
  only(attestation((a) => { a.run.updated_at = "2026-10-13T08:02:40Z"; return a; }), CTX(), "record time is outside the run");
});
test("[A4] attested facts must equal the execution's on the matched facts", () => {
  only(attestation(), { ...CTX(), execution: { at: "2026-10-13T08:01:59Z", facts: { ...DATA, head_sha: "e".repeat(40) } } }, "attested facts differ from the execution");
});
