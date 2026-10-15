// Read-only GitHub Actions attestation adapter for reference/attestation.mjs.
//
// Turns three official GitHub REST API responses into an attestation:
//   1. GET /repos/{o}/{r}/actions/runs/{run_id}/attempts/{attempt}   (run attempt)
//   2. GET /repos/{o}/{r}/actions/runs/{run_id}/artifacts            (artifact list)
//   3. GET /repos/{o}/{r}/actions/artifacts/{artifact_id}/zip         (artifact archive)
// Endpoint behaviour is taken from GitHub's official OpenAPI description
// (github/rest-api-description, "GitHub v3 REST API" 1.1.4): 1 and 2 are
// readable by "anyone with read access to the repository"; 3 has no such
// sentence and says tokens "need the `repo` scope", so artifact download is
// treated as REQUIRING an authenticated token. This module ships no HTTP
// client and holds no credential: the caller supplies `http`, and the default
// refuses. Everything ambiguous or missing is an explicit failure.
import { createHash, } from "node:crypto";
import zlib from "node:zlib";
import { ATTESTATION_KIND, recordDigest } from "../reference/attestation.mjs";

export class AttestationError extends Error {}
const fail = (msg) => { throw new AttestationError(msg); };

const GHA = /^gha:([A-Za-z0-9-]{1,39})\/([A-Za-z0-9._-]{1,100})\/([0-9]{1,20})\/([0-9]{1,6})$/;
const SHA40 = /^[0-9a-f]{40}$/;
const DIGEST = /^sha256:([0-9a-f]{64})$/;
const WORKFLOW_FILE = /^\.github\/workflows\/[A-Za-z0-9._-]+\.ya?ml$/;
export const artifactNameFor = (nonce) => `repo-status-verification-${nonce}`;

export function parseIdentity(identity) {
  const m = GHA.exec(identity || "");
  if (!m) fail(`not a GitHub Actions run identity: ${JSON.stringify(identity)}`);
  return { owner: m[1], repo: m[2], repository: `${m[1]}/${m[2]}`, runId: Number(m[3]), attempt: Number(m[4]) };
}

// workflow-run.path is documented as "The full path of the workflow", example
// "octocat/octo-repo/.github/workflows/ci.yml@main". Accept exactly that form
// (for this run's own repository) or the bare ".github/workflows/<file>".
// Anything else is ambiguous and refused.
export function normalizeWorkflowPath(path, repository) {
  if (typeof path !== "string") fail("run.path missing");
  if (WORKFLOW_FILE.test(path)) return path;
  const prefix = `${repository}/`;
  if (path.startsWith(prefix)) {
    const rest = path.slice(prefix.length), at = rest.lastIndexOf("@");
    if (at > 0 && rest.indexOf("@") === at && at < rest.length - 1 && WORKFLOW_FILE.test(rest.slice(0, at))) return rest.slice(0, at);
  }
  fail(`ambiguous or foreign workflow path: ${JSON.stringify(path)}`);
}

const need = (obj, key, type, where) => {
  const v = obj == null ? undefined : obj[key];
  if (v === undefined || v === null) fail(`${where}.${key} missing`);
  if (type === "integer" ? !Number.isSafeInteger(v) : typeof v !== type) fail(`${where}.${key} is not ${type}`);
  return v;
};
const needTime = (obj, key, where) => { const v = need(obj, key, "string", where); if (isNaN(Date.parse(v))) fail(`${where}.${key} is not a timestamp`); return v; };

// Minimal ZIP reader (central directory based). Refuses zip64, encryption,
// multi-disk archives and unknown compression; checks sizes and CRC-32.
export function readZipEntries(buf) {
  if (!Buffer.isBuffer(buf) || buf.length < 22) fail("artifact archive missing or truncated");
  let eocd = -1;
  for (let i = buf.length - 22; i >= Math.max(0, buf.length - 22 - 65535); i--) if (buf.readUInt32LE(i) === 0x06054b50) { eocd = i; break; }
  if (eocd < 0) fail("artifact archive has no end-of-central-directory record");
  if (buf.readUInt16LE(eocd + 4) !== 0 || buf.readUInt16LE(eocd + 6) !== 0) fail("multi-disk archives are not supported");
  const count = buf.readUInt16LE(eocd + 10), cdOffset = buf.readUInt32LE(eocd + 16);
  if (count === 0xffff || cdOffset === 0xffffffff) fail("zip64 archives are not supported");
  const entries = [];
  let p = cdOffset;
  for (let n = 0; n < count; n++) {
    if (p + 46 > buf.length || buf.readUInt32LE(p) !== 0x02014b50) fail("corrupt central directory");
    const flags = buf.readUInt16LE(p + 8), method = buf.readUInt16LE(p + 10), crc = buf.readUInt32LE(p + 16);
    const csize = buf.readUInt32LE(p + 20), usize = buf.readUInt32LE(p + 24);
    const nlen = buf.readUInt16LE(p + 28), xlen = buf.readUInt16LE(p + 30), clen = buf.readUInt16LE(p + 32), lho = buf.readUInt32LE(p + 42);
    const name = buf.subarray(p + 46, p + 46 + nlen).toString("utf8");
    if (flags & 1) fail(`encrypted entry: ${name}`);
    if (csize === 0xffffffff || usize === 0xffffffff || lho === 0xffffffff) fail("zip64 entries are not supported");
    if (lho + 30 > buf.length || buf.readUInt32LE(lho) !== 0x04034b50) fail(`corrupt local header: ${name}`);
    const start = lho + 30 + buf.readUInt16LE(lho + 26) + buf.readUInt16LE(lho + 28);
    if (start + csize > buf.length) fail(`truncated entry: ${name}`);
    const raw = buf.subarray(start, start + csize);
    let data;
    if (method === 0) data = Buffer.from(raw);
    else if (method === 8) { try { data = zlib.inflateRawSync(raw); } catch { fail(`corrupt deflate data: ${name}`); } }
    else fail(`unsupported compression method ${method}: ${name}`);
    if (data.length !== usize) fail(`size mismatch: ${name}`);
    if (zlib.crc32(data) !== crc) fail(`CRC mismatch: ${name}`);
    entries.push({ name, data });
    p += 46 + nlen + xlen + clen;
  }
  return entries;
}

// Pure: official API responses -> attestation, or AttestationError.
export function buildAttestation({ identity, nonce, runAttempt, artifactList, artifactZip, fetchedBy, fetchedAt }) {
  const id = parseIdentity(identity);
  if (!/^[A-Za-z0-9_-]{6,40}$/.test(nonce || "")) fail("invalid nonce");
  if (typeof fetchedBy !== "string" || !fetchedBy) fail("fetchedBy missing");
  if (typeof fetchedAt !== "string" || isNaN(Date.parse(fetchedAt))) fail("fetchedAt missing");

  // 1. run attempt
  const W = "run";
  const runId = need(runAttempt, "id", "integer", W), attempt = need(runAttempt, "run_attempt", "integer", W);
  const repository = need(runAttempt && runAttempt.repository, "full_name", "string", `${W}.repository`);
  const headSha = need(runAttempt, "head_sha", "string", W);
  if (!SHA40.test(headSha)) fail("run.head_sha is not a 40-character commit sha");
  const run = {
    id: runId, run_attempt: attempt, repository,
    path: normalizeWorkflowPath(runAttempt.path, repository), path_raw: runAttempt.path,
    head_sha: headSha, event: need(runAttempt, "event", "string", W),
    status: need(runAttempt, "status", "string", W), conclusion: need(runAttempt, "conclusion", "string", W),
    display_title: need(runAttempt, "display_title", "string", W),
    created_at: needTime(runAttempt, "created_at", W), updated_at: needTime(runAttempt, "updated_at", W),
  };
  if (runId !== id.runId) fail("run id differs from the claimed identity");
  if (attempt !== id.attempt) fail("run attempt differs from the claimed identity");
  if (repository !== id.repository) fail("run repository differs from the claimed identity");

  // 2. exactly one artifact for this nonce, bound to this run and commit
  const list = artifactList && artifactList.artifacts;
  if (!Array.isArray(list)) fail("artifact list missing");
  if (Number.isSafeInteger(artifactList.total_count) && artifactList.total_count !== list.length) fail("artifact list is paginated or incomplete");
  const named = list.filter((a) => a && a.name === artifactNameFor(nonce));
  if (named.length === 0) fail(`no artifact named ${artifactNameFor(nonce)}`);
  if (named.length > 1) fail(`more than one artifact named ${artifactNameFor(nonce)}`);
  const art = named[0];
  need(art, "id", "integer", "artifact");
  if (art.expired !== false) fail("artifact expired or expiry unknown");
  const wr = art.workflow_run;
  if (!wr || wr.id !== runId) fail("artifact is not from this run");
  if (wr.head_sha !== headSha) fail("artifact is not from this run's commit");
  const dm = DIGEST.exec(art.digest || "");
  if (!dm) fail("artifact digest missing or malformed (requires upload-artifact v4 or newer)");

  // 3. the archive bytes must match the digest GitHub reports; exactly one record.json inside
  if (!Buffer.isBuffer(artifactZip)) fail("artifact archive missing");
  if (createHash("sha256").update(artifactZip).digest("hex") !== dm[1]) fail("artifact archive does not match its reported digest");
  const entries = readZipEntries(artifactZip);
  if (entries.length !== 1 || entries[0].name !== "record.json") fail("artifact must contain exactly one entry, record.json");
  let record;
  try { record = JSON.parse(entries[0].data.toString("utf8")); } catch { fail("record.json is not valid JSON"); }
  if (!record || typeof record !== "object" || Array.isArray(record)) fail("record.json is not an object");

  return {
    kind: ATTESTATION_KIND, fetched_by: fetchedBy, fetched_at: fetchedAt, run,
    artifact: { id: art.id, name: art.name, digest: art.digest },
    record, record_sha256: recordDigest(record),
  };
}

// The network boundary. No implementation ships: artifact download needs an
// authenticated GitHub token, and this repository holds none by design.
export const unconfiguredHttp = Object.freeze({
  async getJSON() { fail("GitHub client not configured: no credential is provided by design"); },
  async downloadArtifactZip() { fail("artifact download requires an authenticated GitHub token (official API: tokens need the `repo` scope); none is provided by design"); },
});

// Orchestration over an injected client: exactly these three read-only calls.
export async function fetchRunAttestation({ identity, nonce, http = unconfiguredHttp, fetchedBy, now = () => new Date() }) {
  const id = parseIdentity(identity);
  const base = `/repos/${id.owner}/${id.repo}/actions`;
  const runAttempt = await http.getJSON(`${base}/runs/${id.runId}/attempts/${id.attempt}`);
  const artifactList = await http.getJSON(`${base}/runs/${id.runId}/artifacts?name=${encodeURIComponent(artifactNameFor(nonce))}&per_page=100`);
  const named = (artifactList && Array.isArray(artifactList.artifacts) ? artifactList.artifacts : []).filter((a) => a && a.name === artifactNameFor(nonce));
  if (named.length !== 1 || !Number.isSafeInteger(named[0].id)) fail(named.length ? "more than one artifact named for this nonce" : `no artifact named ${artifactNameFor(nonce)}`);
  const artifactZip = await http.downloadArtifactZip(`${base}/artifacts/${named[0].id}/zip`);
  return buildAttestation({ identity, nonce, runAttempt, artifactList, artifactZip, fetchedBy, fetchedAt: now().toISOString().replace(/\.\d{3}Z$/, "Z") });
}
