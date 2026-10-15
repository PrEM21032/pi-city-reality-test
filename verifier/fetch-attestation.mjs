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
// RFC 3339 date-time, the OpenAPI `format` of every run timestamp.
const DATE_TIME = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?(?:Z|[+-]\d{2}:\d{2})$/;
const NONCE = /^[A-Za-z0-9_-]{6,40}$/;
export const artifactNameFor = (nonce) => `repo-status-verification-${nonce}`;

// Size bounds, checked before hashing, inflating or parsing. The expected
// artifact is one small record.json (well under 1 KiB), so these are generous.
export const LIMITS = Object.freeze({
  zipBytes: 256 * 1024,     // whole artifact archive, and the artifact's reported size
  entries: 1,               // central-directory entries
  entryBytes: 64 * 1024,    // each entry, compressed and uncompressed (bounds record.json)
});

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
const needTime = (obj, key, where) => { const v = need(obj, key, "string", where); if (!DATE_TIME.test(v) || isNaN(Date.parse(v))) fail(`${where}.${key} is not a timestamp`); return v; };

// Minimal ZIP reader (central directory based). Refuses zip64, encryption,
// multi-disk archives and unknown compression; checks sizes and CRC-32.
// Every size is bounded before anything is inflated, and inflation itself
// stops at the declared size.
export function readZipEntries(buf, { maxBytes = LIMITS.zipBytes, maxEntries = LIMITS.entries, maxEntryBytes = LIMITS.entryBytes } = {}) {
  if (!Buffer.isBuffer(buf) || buf.length < 22) fail("artifact archive missing or truncated");
  if (buf.length > maxBytes) fail(`archive exceeds ${maxBytes} bytes`);
  let eocd = -1;
  for (let i = buf.length - 22; i >= Math.max(0, buf.length - 22 - 65535); i--) if (buf.readUInt32LE(i) === 0x06054b50) { eocd = i; break; }
  if (eocd < 0) fail("artifact archive has no end-of-central-directory record");
  if (eocd + 22 + buf.readUInt16LE(eocd + 20) !== buf.length) fail("end-of-central-directory record is ambiguous (comment length does not reach the end)");
  if (buf.readUInt16LE(eocd + 4) !== 0 || buf.readUInt16LE(eocd + 6) !== 0) fail("multi-disk archives are not supported");
  const count = buf.readUInt16LE(eocd + 10), cdOffset = buf.readUInt32LE(eocd + 16);
  if (count === 0xffff || cdOffset === 0xffffffff) fail("zip64 archives are not supported");
  if (count > maxEntries) fail(`archive has ${count} entries; at most ${maxEntries} allowed`);
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
    if (csize > maxEntryBytes || usize > maxEntryBytes) fail(`entry exceeds ${maxEntryBytes} bytes: ${name}`);
    if (lho + 30 > buf.length || buf.readUInt32LE(lho) !== 0x04034b50) fail(`corrupt local header: ${name}`);
    const lnlen = buf.readUInt16LE(lho + 26), start = lho + 30 + lnlen + buf.readUInt16LE(lho + 28);
    if (buf.readUInt16LE(lho + 8) !== method || !buf.subarray(lho + 30, lho + 30 + lnlen).equals(buf.subarray(p + 46, p + 46 + nlen))) fail(`local and central headers disagree: ${name}`);
    if (start + csize > buf.length) fail(`truncated entry: ${name}`);
    const raw = buf.subarray(start, start + csize);
    let data;
    if (method === 0) data = Buffer.from(raw);
    else if (method === 8) {
      try { data = zlib.inflateRawSync(raw, { maxOutputLength: Math.max(usize, 1) }); }
      catch (e) { fail(e && e.code === "ERR_BUFFER_TOO_LARGE" ? `entry inflates beyond its declared size: ${name}` : `corrupt deflate data: ${name}`); }
    }
    else fail(`unsupported compression method ${method}: ${name}`);
    if (data.length !== usize) fail(`size mismatch: ${name}`);
    if (zlib.crc32(data) !== crc) fail(`CRC mismatch: ${name}`);
    entries.push({ name, data });
    p += 46 + nlen + xlen + clen;
  }
  return entries;
}

function checkRequest({ nonce, fetchedBy }) {
  if (!NONCE.test(nonce || "")) fail("invalid nonce");
  if (typeof fetchedBy !== "string" || !fetchedBy) fail("fetchedBy missing");
}

// The one artifact for this nonce, from a list that must be complete: the
// API's total_count is required, and must equal the entries returned, so a
// duplicate cannot hide on a page we did not read. Used before any download.
export function selectArtifact(artifactList, nonce) {
  const list = artifactList && artifactList.artifacts;
  if (!Array.isArray(list)) fail("artifact list missing");
  if (!Number.isSafeInteger(artifactList.total_count)) fail("artifact list total_count missing or not an integer");
  if (artifactList.total_count !== list.length) fail("artifact list is paginated or incomplete");
  const named = list.filter((a) => a && a.name === artifactNameFor(nonce));
  if (named.length === 0) fail(`no artifact named ${artifactNameFor(nonce)}`);
  if (named.length > 1) fail(`more than one artifact named ${artifactNameFor(nonce)}`);
  const art = named[0];
  need(art, "id", "integer", "artifact");
  const size = need(art, "size_in_bytes", "integer", "artifact");
  if (size < 0 || size > LIMITS.zipBytes) fail(`artifact size ${size} is outside 0..${LIMITS.zipBytes} bytes`);
  return art;
}

// Pure: official API responses -> attestation, or AttestationError.
export function buildAttestation({ identity, nonce, runAttempt, artifactList, artifactZip, fetchedBy, fetchedAt }) {
  const id = parseIdentity(identity);
  checkRequest({ nonce, fetchedBy });
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
  const art = selectArtifact(artifactList, nonce);
  if (art.expired !== false) fail("artifact expired or expiry unknown");
  const wr = art.workflow_run;
  if (!wr || wr.id !== runId) fail("artifact is not from this run");
  if (wr.head_sha !== headSha) fail("artifact is not from this run's commit");
  const dm = DIGEST.exec(art.digest || "");
  if (!dm) fail("artifact digest missing or malformed (requires upload-artifact v4 or newer)");

  // 3. the archive bytes must match the digest GitHub reports; exactly one record.json inside
  if (!Buffer.isBuffer(artifactZip)) fail("artifact archive missing");
  if (artifactZip.length > LIMITS.zipBytes) fail(`artifact archive exceeds ${LIMITS.zipBytes} bytes`);
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
// Inputs are checked before the first call, and the artifact list fully
// (selectArtifact) before the download; the client is told the byte bound.
export async function fetchRunAttestation({ identity, nonce, http = unconfiguredHttp, fetchedBy, now = () => new Date() }) {
  const id = parseIdentity(identity);
  checkRequest({ nonce, fetchedBy });
  const base = `/repos/${id.owner}/${id.repo}/actions`;
  const runAttempt = await http.getJSON(`${base}/runs/${id.runId}/attempts/${id.attempt}`);
  const artifactList = await http.getJSON(`${base}/runs/${id.runId}/artifacts?name=${encodeURIComponent(artifactNameFor(nonce))}&per_page=100`);
  const art = selectArtifact(artifactList, nonce);
  const artifactZip = await http.downloadArtifactZip(`${base}/artifacts/${art.id}/zip`, { maxBytes: LIMITS.zipBytes });
  return buildAttestation({ identity, nonce, runAttempt, artifactList, artifactZip, fetchedBy, fetchedAt: now().toISOString().replace(/\.\d{3}Z$/, "Z") });
}
