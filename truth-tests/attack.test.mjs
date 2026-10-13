// Adversarial tests for PI City's truth layer (local/test proof only).
// Run: PI_CITY_HTML=/path/to/saved/artifact.html node --test
// Fixtures marked "live" are copies of the real missions/backend rows read
// read-only on 2026-10-13; everything else is a constructed attack.
// A test with `todo` states the property PI City SHOULD have and currently
// lacks: it reports as a known gap without failing the suite.
import { test } from "node:test";
import assert from "node:assert/strict";
import { load } from "./extract.mjs";

const X = load();
const skip = X ? false : "set PI_CITY_HTML to a saved copy of the PI City artifact";
const clone = (o) => JSON.parse(JSON.stringify(o));

// ---- legacy reality-001 -------------------------------------------------
const REPO = "PrEM21032/pi-city-reality-test";
const ISSUE = {
  created_at: "2026-10-12T01:40:44Z", html_url: `https://github.com/${REPO}/issues/1`,
  id: 5807154078, node_id: "I_kwDOVFXHvs8AAAABWiIjng", number: 1, state: "open",
  title: "[PI CITY TEST] Reality Mission #001", user_login: "PrEM21032",
};
const ver = (nonce, at, run, status = 200) => ({
  checked_at: at, html_url: ISSUE.html_url, http_status: status, number: 1,
  number_matches: status === 200, request_nonce: nonce, run_session: run,
  source: "github", state: status === 200 ? "open" : undefined, title: ISSUE.title,
});
// live: backend/reality-001 v18 (trimmed to the fields the page reads)
const BACK_V18 = {
  api_status: 201, issue: ISSUE, recorded_at: "2026-10-12T01:40:44Z", repo: REPO,
  request_nonce: "ba4cab4abd8d3c7fd077279c", source: "github", status: "verified", error: null,
  previous_verifications: [
    ver("0b161beca20a23b5656191de", "2026-10-12T01:52:49Z", "session_01Diof3y67Q1zpoUdeY7cHVP (manual, not routine-fired)"),
    ver("d00dd0f394b6ed11fe2012af", "2026-10-12T17:10:48Z", "session_01Diof3y67Q1zpoUdeY7cHVP"),
  ],
  verification: ver("4c5e818a06db43afc526b28f", "2026-10-12T17:13:38Z", "cse_01VgDxR55x6eE1MFczoi8Y6u"),
};
// live: missions/reality-001 v18
const MISSION_V18 = {
  acceptedAt: "2026-10-12T01:10:09.223Z", inspectedAt: "2026-10-12T01:52:08.323Z",
  finalCheck: "2026-10-12T01:52:49Z", passedAt: "2026-10-12T01:53:07.608Z", repo: REPO, status: "passed",
  completion: { checked_at: "2026-10-12T01:52:49Z", pinned_at: "2026-10-12T17:02:59.623Z", verify_nonce: "0b161beca20a23b5656191de" },
  requests: {
    create: { at: "2026-10-12T01:17:21.047Z", nonce: "ba4cab4abd8d3c7fd077279c" },
    verify: { at: "2026-10-12T17:13:09.031Z", nonce: "4c5e818a06db43afc526b28f" },
  },
};
// The state the page judged at 01:53 (reconstructed from the prior session's
// transcript): create POST 201 at 01:40:44 and verify GET 200 at 01:52:49 were
// BOTH run by session_01Diof3y67Q1zpoUdeY7cHVP on owner chat instructions.
const MISSION_0153 = {
  acceptedAt: MISSION_V18.acceptedAt, inspectedAt: MISSION_V18.inspectedAt, repo: REPO, status: "accepted",
  requests: { create: MISSION_V18.requests.create, verify: { at: "2026-10-12T01:52:13.818Z", nonce: "0b161beca20a23b5656191de" } },
};
const BACK_0153 = {
  api_status: 201, issue: ISSUE, recorded_at: ISSUE.created_at, repo: REPO, request_nonce: "ba4cab4abd8d3c7fd077279c",
  source: "github", status: "verified", error: null,
  verification: ver("0b161beca20a23b5656191de", "2026-10-12T01:52:49Z", "session_01Diof3y67Q1zpoUdeY7cHVP"),
};

function legacy(page, back) {
  const m = Object.create(X.Legacy.prototype);
  Object.assign(m, { page: clone(page), back: back && clone(back), loaded1: true, loaded2: true, status: "ready" });
  return m;
}

test("live reality-001 rows replay as passed / REAL-VERIFIED (baseline)", { skip }, () => {
  const m = legacy(MISSION_V18, BACK_V18);
  assert.equal(m.stage(), "passed");
  assert.equal(m.receipt().level, X.C.REAL);
});

test("executor and verifier in the same session must not count as REAL", {
  skip, todo: "legacy receipt never records executor run_session, so Xt's same-run check is skipped",
}, () => {
  const m = legacy(MISSION_0153, BACK_0153);
  assert.equal(m.stage(), "verified_pass"); // page would write status:passed
  assert.notEqual(m.receipt().level, X.C.REAL);
});

test("a verification row with no run identity at all must not count as REAL", {
  skip, todo: "any writer of backend/ can mint REAL-VERIFIED with a hand-typed row",
}, () => {
  const b = clone(BACK_0153);
  b.verification = { http_status: 200, number: 1, request_nonce: "0b161beca20a23b5656191de", checked_at: "2026-10-12T01:52:49Z" };
  assert.notEqual(legacy(MISSION_0153, b).receipt().level, X.C.REAL);
});

test("read-back older than the issue is rejected", { skip }, () => {
  const b = clone(BACK_0153);
  b.verification.checked_at = "2026-10-12T01:30:00Z";
  assert.notEqual(legacy(MISSION_0153, b).receipt().level, X.C.REAL);
});

test("read-back answering an older verify request is rejected", { skip }, () => {
  const b = clone(BACK_0153);
  b.verification.request_nonce = "someOlderNonce01";
  assert.notEqual(legacy(MISSION_0153, b).stage(), "verified_pass");
});

test("read-back 404 makes the mission fail, not pass", { skip }, () => {
  const b = clone(BACK_0153);
  b.verification = ver("0b161beca20a23b5656191de", "2026-10-12T01:52:49Z", "cse_x", 404);
  b.verification.number = undefined;
  assert.equal(legacy(MISSION_0153, b).stage(), "verified_fail");
});

test("a newer read-back that finds the issue gone must demote a passed mission", {
  skip, todo: "passed state is pinned to the first good read; no reconciliation loop",
}, () => {
  const b = clone(BACK_V18);
  b.previous_verifications.push(b.verification);
  b.verification = { ...ver("4c5e818a06db43afc526b28f", "2026-10-13T09:00:00Z", "cse_y", 404), number: undefined };
  assert.notEqual(legacy(MISSION_V18, b).receipt().level, X.C.REAL);
});

test("deleting the mission row must not erase the verified outcome", {
  skip, todo: "'Reset mission' deletes missions/reality-001; the receipt falls back to NOT STARTED",
}, () => {
  assert.equal(legacy(null, BACK_V18).receipt().level, X.C.REAL);
});

// ---- protocol 2 (generic missions) ---------------------------------------
const defRS = () => X.missionDefs.find((d) => d.id === "repo-status-001");
const CFG = { protocol: 2, trigger_id: "trig_01TvxJ59TYdysTNEJRtHB4ws", kinds: ["github_repo_status"] };
const DATA = { branch_count: 1, default_branch: "main", head_sha: "3515b3d858afac8ac71a23a585bcd586dcf62006", repo_url: `https://github.com/${REPO}` };
function p2({ execRun = "cse_A", verRun = "cse_B", execFire = "cse_A", verFire = "cse_B", vdata = DATA, vAt = "2026-10-13T08:02:53Z", perm = "granted", scope } = {}) {
  const d = defRS();
  const g = new X.Generic(d, { db: {}, cfg: CFG, changed() {} });
  g.loaded = [true, true];
  g.page = {
    run: "689f96071a75", permission: { status: perm, scope: scope ?? d.permission.scope },
    requests: {
      execute: { nonce: "exec0001", at: "2026-10-13T08:01:32Z", dispatch: { status: "fired", session: execFire } },
      verify: { nonce: "veri0001", at: "2026-10-13T08:02:25Z", dispatch: { status: "fired", session: verFire } },
    },
  };
  g.back = {
    executions: { exec0001: { exit_code: 0, executed_at: "2026-10-13T08:01:59Z", run_session: execRun, data: DATA } },
    verifications: { veri0001: { exit_code: 0, checked_at: vAt, run_session: verRun, data: vdata } },
  };
  return g;
}

test("p2: live-shaped run with separate sessions is REAL (baseline)", { skip }, () => {
  assert.equal(p2().receipt().level, X.C.REAL);
});
test("p2: same run session for executor and verifier is not REAL", { skip }, () => {
  assert.notEqual(p2({ verRun: "cse_A", verFire: "cse_A" }).receipt().level, X.C.REAL);
});
test("p2: verifier facts that differ make it FAILED", { skip }, () => {
  assert.equal(p2({ vdata: { ...DATA, head_sha: "deadbeef" } }).receipt().level, X.C.FAILED);
});
test("p2: verifier older than executor is not REAL", { skip }, () => {
  assert.notEqual(p2({ vAt: "2026-10-13T08:00:00Z" }).receipt().level, X.C.REAL);
});
test("p2: denied permission dispatches nothing and reads DENIED", { skip }, () => {
  assert.equal(p2({ perm: "denied" }).receipt().level, X.C.DENIED);
});
test("p2: permission scope drift blocks the run", { skip }, () => {
  assert.equal(p2({ scope: "something broader" }).receipt().level, X.C.PERMISSION);
});
test("p2: unknown run identities on both sides must not count as REAL", {
  skip, todo: "'unrecorded' + missing dispatch session skips the independence check entirely",
}, () => {
  assert.notEqual(p2({ execRun: "unrecorded", verRun: "unrecorded", execFire: null, verFire: null }).receipt().level, X.C.REAL);
});
test("p2: same session id hidden by a typo-level variant must not count as REAL", {
  skip, todo: "independence is string inequality of agent-written ids, not a property of the verifier",
}, () => {
  assert.notEqual(p2({ verRun: "cse_A ", verFire: "cse_A " }).receipt().level, X.C.REAL);
});

// ---- duplicate dispatch / two tabs ---------------------------------------
function fakeDoc(initial, { lease = true } = {}) {
  let data = clone(initial), holder = null;
  const merge = (a, b) => { for (const [k, v] of Object.entries(b)) a[k] = v && typeof v === "object" && !Array.isArray(v) && a[k] && typeof a[k] === "object" ? merge(a[k], v) : v; return a; };
  return {
    get data() { return data; },
    async acquire({ holder: h }) { if (!lease || (holder && holder !== h)) return { acquired: false }; holder = h; return { acquired: true }; },
    async get() { return { exists: true, data: () => clone(data) }; },
    async update(patch) { merge(data, patch); },
  };
}

test("p2: a second tab that loses the lease fires nothing", { skip }, async () => {
  const g = p2(); g.page.requests = {}; g.back = {};
  let fires = 0;
  g.rt.mcp = { callTool: async () => { fires++; return { payload: {} }; } };
  g.mref = fakeDoc(g.page, { lease: false });
  await g.dispatch("execute");
  assert.equal(fires, 0);
});

test("p2: a repeat click while a request is pending fires nothing", { skip }, async () => {
  const g = p2(); g.back = {};
  g.page.requests = { execute: { nonce: "exec0002", at: new Date().toISOString(), dispatch: { status: "fired" } } };
  let fires = 0;
  g.rt.mcp = { callTool: async () => { fires++; return { payload: {} }; } };
  g.mref = fakeDoc(g.page);
  await g.dispatch("execute");
  assert.equal(fires, 0);
});

test("legacy: two tabs completing the mission at once fire one verify, not two", {
  skip, todo: "legacy retry()/complete() has only a per-tab busy flag; no lease or pending check",
}, async () => {
  let fires = 0;
  const tab = () => {
    const m = legacy({ ...MISSION_0153, requests: { create: MISSION_0153.requests.create } }, BACK_0153);
    m.mref = { update: async () => {} };
    m.fire = async () => { fires++; return true; };
    m.render = () => {};
    return m;
  };
  await Promise.all([tab().complete(), tab().complete()]);
  assert.equal(fires, 1);
});
