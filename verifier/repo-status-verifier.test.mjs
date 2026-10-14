// Tests for the independent repo-status verifier. Runs offline: git is
// replaced by recorded ls-remote output. No credentials, no network.
import { test } from "node:test";
import assert from "node:assert/strict";
import { parseLsRemote, runIdentity, verifyRepoStatus, compare } from "./repo-status-verifier.mjs";
import * as core from "../reference/truth-core.mjs";
import * as imp from "../reference/import-rows.mjs";
import { DEF_RS, p2Rows, SID_A } from "../truth-tests/cases.mjs";

const SHA = "3515b3d858afac8ac71a23a585bcd586dcf62006";
const SHA2 = "1bd1733e0b6589c19eef6c0f87a1cfe650223344";
// Shape of real `git ls-remote --symref` output for the mission repository.
const LS = `ref: refs/heads/main\tHEAD\n${SHA}\tHEAD\n${SHA2}\trefs/heads/claude/practical-ramanujan-n5fydt\n${SHA}\trefs/heads/main\n`;
const GHA = { GITHUB_ACTIONS: "true", GITHUB_REPOSITORY: "PrEM21032/pi-city-reality-test", GITHUB_RUN_ID: "123456789", GITHUB_RUN_ATTEMPT: "1", GITHUB_SERVER_URL: "https://github.com" };
const fakeGit = (stdout, exitCode = 0) => async () => ({ exitCode, stdout, stderr: exitCode ? "fatal: repository not found" : "" });
const fixedNow = () => new Date("2026-10-14T05:10:00.123Z");

// ---- parsing ---------------------------------------------------------------
test("parses default branch, head and branch count", () => {
  assert.deepEqual(parseLsRemote(LS), { default_branch: "main", head_sha: SHA, branch_count: 2 });
});
test("refuses output without a HEAD symref instead of guessing", () => {
  assert.throws(() => parseLsRemote(`${SHA}\tHEAD\n${SHA}\trefs/heads/main\n`), /default branch unknown/);
});
test("refuses a malformed sha", () => {
  assert.throws(() => parseLsRemote(`ref: refs/heads/main\tHEAD\nnot-a-sha\tHEAD\n`), /40 hex/);
});
test("refuses empty and unparseable output", () => {
  assert.throws(() => parseLsRemote(""), /empty/);
  assert.throws(() => parseLsRemote("garbage without tabs"), /unparseable/);
});
test("refuses a duplicated HEAD symref", () => {
  assert.throws(() => parseLsRemote(`ref: refs/heads/main\tHEAD\nref: refs/heads/dev\tHEAD\n${SHA}\tHEAD\n`), /twice/);
});

// ---- identity --------------------------------------------------------------
test("inside GitHub Actions the identity and evidence URL come from run metadata", () => {
  assert.deepEqual(runIdentity(GHA), {
    identity: "gha:PrEM21032/pi-city-reality-test/123456789/1", path: "github-action",
    evidence_url: "https://github.com/PrEM21032/pi-city-reality-test/actions/runs/123456789/attempts/1",
  });
});
test("a local run has no identity, so it can never count as independent", () => {
  assert.deepEqual(runIdentity({}), { identity: null, path: "local", evidence_url: null });
});
test("malformed Actions metadata yields no identity", () => {
  assert.equal(runIdentity({ ...GHA, GITHUB_RUN_ID: "12x" }).identity, null);
});

// ---- record ------------------------------------------------------------------
test("a successful read produces a backend-shaped verification record", async () => {
  const rec = await verifyRepoStatus({ repo: "PrEM21032/pi-city-reality-test", nonce: "veri0001", env: GHA, run: fakeGit(LS), now: fixedNow });
  assert.deepEqual(rec, {
    nonce: "veri0001", checked_at: "2026-10-14T05:10:00Z", exit_code: 0,
    run_session: "gha:PrEM21032/pi-city-reality-test/123456789/1", path: "github-action",
    evidence_url: "https://github.com/PrEM21032/pi-city-reality-test/actions/runs/123456789/attempts/1",
    verifier: "verifier/repo-status-verifier.mjs",
    data: { repo_url: "https://github.com/PrEM21032/pi-city-reality-test", default_branch: "main", head_sha: SHA, branch_count: 2 },
  });
});
test("a failed read is recorded as failed with empty data, never as facts", async () => {
  const rec = await verifyRepoStatus({ repo: "PrEM21032/pi-city-reality-test", nonce: "veri0001", env: GHA, run: fakeGit("", 128), now: fixedNow });
  assert.equal(rec.exit_code, 128);
  assert.deepEqual(rec.data, {});
  assert.match(rec.stderr_excerpt, /not found/);
});
test("unparseable output is a failure (exit 3), not facts", async () => {
  const rec = await verifyRepoStatus({ repo: "PrEM21032/pi-city-reality-test", nonce: "veri0001", env: GHA, run: fakeGit("junk"), now: fixedNow });
  assert.equal(rec.exit_code, 3);
  assert.deepEqual(rec.data, {});
});
test("invalid repo or nonce is rejected before any read", async () => {
  let reads = 0; const run = async () => { reads++; return { exitCode: 0, stdout: LS }; };
  await assert.rejects(verifyRepoStatus({ repo: "../etc", nonce: "veri0001", run }), /invalid repo/);
  await assert.rejects(verifyRepoStatus({ repo: "PrEM21032/pi-city-reality-test", nonce: "x", run }), /invalid nonce/);
  assert.equal(reads, 0);
});

// ---- comparison --------------------------------------------------------------
test("compares only the mission's matched facts", () => {
  const exec = { default_branch: "main", head_sha: SHA, branch_count: 1 };
  assert.deepEqual(compare(exec, { default_branch: "main", head_sha: SHA, branch_count: 2 }), { match: true, diffs: [] });
  assert.deepEqual(compare(exec, { default_branch: "main", head_sha: SHA2, branch_count: 1 }), { match: false, diffs: ["head_sha"] });
  assert.equal(compare({}, { default_branch: "main", head_sha: SHA }).match, false);
});

// ---- the reference rules accept it as independent only when it should --------
const judgeWith = async (env, opts = {}) => {
  const rec = await verifyRepoStatus({ repo: "PrEM21032/pi-city-reality-test", nonce: "veri0001", env, run: fakeGit(LS), now: () => new Date("2026-10-13T08:02:53Z") });
  const rows = p2Rows({ execRun: SID_A, execFire: SID_A, verFire: null });
  rows.back.verifications.veri0001 = { exit_code: rec.exit_code, checked_at: rec.checked_at, run_session: rec.run_session, path: rec.path, data: rec.data };
  return core.judge(imp.importProtocol2(DEF_RS, rows.page, rows.back), { mission: DEF_RS.id, requestedFacts: DEF_RS.verifier.match, scope: DEF_RS.permission.scope, policy: opts.policy });
};
test("an Actions-run record is REAL-VERIFIED even under the distinct-path policy", async () => {
  assert.equal((await judgeWith(GHA, { policy: { independence: "distinct-path" } })).level, core.LEVEL.REAL);
});
test("a local run of the same verifier is not REAL-VERIFIED (no identity)", async () => {
  assert.equal((await judgeWith({})).level, core.LEVEL.REPORTED);
});
test("a forged near-miss Actions identity is not accepted", () => {
  assert.equal(core.canonicalIdentity("gha:PrEM21032/pi-city-reality-test/123456789/1 "), null);
  assert.equal(core.canonicalIdentity("gha:PrEM21032/pi-city-reality-test/abc/1"), null);
  assert.equal(core.canonicalIdentity("gha:PrEM21032/pi-city-reality-test/123456789/1"), "gha:PrEM21032/pi-city-reality-test/123456789/1");
});
