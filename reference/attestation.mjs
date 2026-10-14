// GitHub Actions run attestation contract (reference, fail-closed).
//
// A verification row that names a GitHub Actions run (run_session
// "gha:<owner>/<repo>/<run_id>/<attempt>", path, evidence_url) is only a
// CLAIM: anyone who can write the database can type it, and the verifier's
// own identity can be simulated with environment variables. Such a row alone
// never makes an outcome REAL-VERIFIED.
//
// It counts only when the judge is ALSO handed an attestation obtained over a
// separate trust path: a designated fetcher reads the run and its uploaded
// record from GitHub's API itself and passes them to the judge directly. An
// attestation found inside the evidence log or a database row is ignored.
//
// Trust is explicit and empty by default: until the owner pins the workflow
// file, the workflow commit(s) and the fetcher identity, no attestation can
// pass.
import { createHash } from "node:crypto";
import { canonical } from "./truth-core.mjs";

export const ATTESTATION_KIND = "github-actions-run-attestation/v1";

// Default trust: nothing pinned, so nothing passes.
export const DEFAULT_TRUST = Object.freeze({
  repository: "PrEM21032/pi-city-reality-test",
  workflow_path: ".github/workflows/repo-status-verify.yml",
  workflow_shas: Object.freeze([]),   // verifier workflow commits the owner has reviewed
  fetchers: Object.freeze([]),        // identities allowed to fetch and hand over attestations
});

export const recordDigest = (record) => createHash("sha256").update(canonical(record)).digest("hex");
const GHA = /^gha:([A-Za-z0-9-]{1,39}\/[A-Za-z0-9._-]{1,100})\/([0-9]{1,20})\/([0-9]{1,6})$/;
const t = (s) => Date.parse(s);
const deepEqual = (a, b) => canonical(a) === canonical(b);

// Checks one attestation against the claimed identity, the verification event
// it is supposed to back, the mission's verify request and the execution.
// Returns { ok, failures[] }; ok only if every condition holds.
export function checkRunAttestation(att, { identity, verification, request, execution, executorId, requestedFacts, trust = DEFAULT_TRUST }) {
  const f = [];
  const fail = (m) => f.push(m);
  const id = GHA.exec(identity || "");
  if (!id) return { ok: false, failures: ["claimed identity is not a GitHub Actions run"] };
  const [, idRepo, idRun, idAttempt] = id;
  if (!att || att.kind !== ATTESTATION_KIND) return { ok: false, failures: ["no attestation of the expected kind"] };
  const run = att.run || {}, rec = att.record || {};

  // separate trust path
  if (!trust.fetchers.includes(att.fetched_by)) fail("attestation fetched by an identity the owner has not designated");
  if (att.fetched_by && att.fetched_by === executorId) fail("attestation fetched by the executor");
  if (att.record_sha256 !== recordDigest(rec)) fail("record digest does not match the attested record");

  // the run: exists, right repository, right workflow file, pinned commit, right attempt
  if (String(run.id) !== idRun || String(run.run_attempt) !== idAttempt) fail("run id/attempt differ from the claimed identity");
  if (run.repository !== trust.repository || idRepo !== trust.repository) fail("run is not in the mission repository");
  if (run.path !== trust.workflow_path) fail("run is not the verifier workflow");
  if (!trust.workflow_shas.includes(run.head_sha)) fail("workflow commit is not one the owner pinned");
  if (run.event !== "workflow_dispatch") fail("run was not a manual dispatch");
  if (run.status !== "completed" || run.conclusion !== "success") fail("run did not complete successfully");

  // bound to this mission request
  const nonce = verification && verification.nonce;
  if (!request || request.nonce !== nonce) fail("verification does not answer the mission's verify request");
  if (run.display_title !== `repo-status-verify ${nonce}`) fail("run was not dispatched for this nonce");
  if (rec.nonce !== nonce) fail("attested record answers a different nonce");
  if (!(t(run.created_at) >= t(request && request.at))) fail("run started before the verify request");
  if (!(t(run.created_at) >= t(execution && execution.at))) fail("run started before the execution");
  if (!(t(rec.checked_at) >= t(run.created_at) && t(rec.checked_at) <= t(run.updated_at))) fail("record time is outside the run");

  // exact facts: the database row must say exactly what the run recorded
  if (rec.exit_code !== 0) fail("attested read did not succeed");
  if (rec.run_session !== identity) fail("attested record names a different run");
  if (rec.checked_at !== verification.at) fail("row time differs from the attested record");
  if (!deepEqual(rec.data, verification.facts)) fail("row facts differ from the attested record");
  if (!requestedFacts.every((k) => execution && execution.facts && rec.data && execution.facts[k] !== undefined && rec.data[k] === execution.facts[k])) fail("attested facts differ from the execution");

  return { ok: f.length === 0, failures: f };
}
