// The attack cases, defined once and run against two implementations:
//   city      PI City's own truth code, extracted from the pinned snapshot
//             (truth-tests/attack.test.mjs; needs PI_CITY_HTML)
//   reference the clean-room reference truth core
//             (reference/reference.test.mjs; runs anywhere)
// Both judge the same database-row fixtures. Fixtures marked "live" are
// copies of real missions/backend rows read read-only on 2026-10-13.
//
// Each case returns an observation per implementation and states what that
// observation must be. `gapInCity` marks a property the audit found the city
// lacks; the city run reports those as known gaps (todo) instead of failing.

export const clone = (o) => JSON.parse(JSON.stringify(o));
const REAL = "REAL-VERIFIED";

// ---- fixtures: legacy reality-001 -----------------------------------------
export const REPO = "PrEM21032/pi-city-reality-test";
const ISSUE = {
  created_at: "2026-10-12T01:40:44Z", html_url: `https://github.com/${REPO}/issues/1`,
  id: 5807154078, node_id: "I_kwDOVFXHvs8AAAABWiIjng", number: 1, state: "open",
  title: "[PI CITY TEST] Reality Mission #001", user_login: "PrEM21032",
};
const ver = (nonce, at, run, status = 200) => ({
  checked_at: at, html_url: ISSUE.html_url, http_status: status, number: status === 200 ? 1 : undefined,
  number_matches: status === 200, request_nonce: nonce, run_session: run,
  source: "github", state: status === 200 ? "open" : undefined, title: ISSUE.title,
});
// The session that created issue #1 and first verified it (prior-session transcript).
export const CREATOR = "session_01Diof3y67Q1zpoUdeY7cHVP";

// live: backend/reality-001 v18 (fields the page reads)
export const BACK_V18 = {
  api_status: 201, issue: ISSUE, recorded_at: "2026-10-12T01:40:44Z", repo: REPO,
  request_nonce: "ba4cab4abd8d3c7fd077279c", source: "github", status: "verified", error: null,
  previous_verifications: [
    ver("0b161beca20a23b5656191de", "2026-10-12T01:52:49Z", `${CREATOR} (manual, not routine-fired)`),
    ver("d00dd0f394b6ed11fe2012af", "2026-10-12T17:10:48Z", CREATOR),
  ],
  verification: ver("4c5e818a06db43afc526b28f", "2026-10-12T17:13:38Z", "cse_01VgDxR55x6eE1MFczoi8Y6u"),
};
// The same rows plus the one fact the live row lacks: who executed the create.
// `executor_run_session` is a proposed field; the city ignores it.
export const BACK_V18_EXEC = { ...clone(BACK_V18), executor_run_session: CREATOR };

// live: missions/reality-001 v18
export const MISSION_V18 = {
  acceptedAt: "2026-10-12T01:10:09.223Z", inspectedAt: "2026-10-12T01:52:08.323Z",
  finalCheck: "2026-10-12T01:52:49Z", passedAt: "2026-10-12T01:53:07.608Z", repo: REPO, status: "passed",
  completion: { checked_at: "2026-10-12T01:52:49Z", pinned_at: "2026-10-12T17:02:59.623Z", verify_nonce: "0b161beca20a23b5656191de" },
  requests: {
    create: { at: "2026-10-12T01:17:21.047Z", nonce: "ba4cab4abd8d3c7fd077279c" },
    verify: { at: "2026-10-12T17:13:09.031Z", nonce: "4c5e818a06db43afc526b28f" },
  },
};
// The state judged at 01:53 (reconstructed from the transcript): the create
// POST and the first verify GET were both run by CREATOR.
export const MISSION_0153 = {
  acceptedAt: MISSION_V18.acceptedAt, inspectedAt: MISSION_V18.inspectedAt, repo: REPO, status: "accepted",
  requests: { create: MISSION_V18.requests.create, verify: { at: "2026-10-12T01:52:13.818Z", nonce: "0b161beca20a23b5656191de" } },
};
export const BACK_0153 = {
  api_status: 201, issue: ISSUE, recorded_at: ISSUE.created_at, repo: REPO, request_nonce: "ba4cab4abd8d3c7fd077279c",
  source: "github", status: "verified", error: null, executor_run_session: CREATOR,
  verification: ver("0b161beca20a23b5656191de", "2026-10-12T01:52:49Z", CREATOR),
};

// ---- fixtures: protocol 2 (repo-status-001) -------------------------------
// The mission definition as the live rows describe it (scope from
// missions/repo-status-001.permission.scope; compared facts from the
// verifier). reference.test.mjs checks it against the snapshot when present.
export const DEF_RS = {
  id: "repo-status-001", kind: "github_repo_status", result: "exit_code",
  permission: { consequential: false, scope: "Dispatch the PI City backend routine twice: one read-only `git ls-remote --symref https://github.com/PrEM21032/pi-city-reality-test` (executor), then one separate run of the same read (verifier). Nothing is written to GitHub." },
  verifier: { match: ["default_branch", "head_sha"] },
};
export const CFG = { protocol: 2, trigger_id: "trig_01TvxJ59TYdysTNEJRtHB4ws", kinds: ["github_repo_status"] };
const DATA = { branch_count: 1, default_branch: "main", head_sha: "3515b3d858afac8ac71a23a585bcd586dcf62006", repo_url: `https://github.com/${REPO}` };
export const SID_A = "cse_01AaaaaaaaaaaaaaaaaaaaaaA1";
export const SID_B = "cse_01BbbbbbbbbbbbbbbbbbbbbbB2";

export function p2Rows({ execRun = SID_A, verRun = SID_B, execFire = SID_A, verFire = SID_B, vdata = DATA, vAt = "2026-10-13T08:02:53Z", perm = "granted", scope, decidedIn = "Owner Control (this view)" } = {}) {
  return {
    page: {
      run: "689f96071a75", started_at: "2026-10-13T08:01:27.149Z",
      permission: { status: perm, scope: scope ?? DEF_RS.permission.scope, decided_in: decidedIn, decided_at: "2026-10-13T08:01:28.410Z" },
      requests: {
        execute: { nonce: "exec0001", at: "2026-10-13T08:01:32Z", dispatch: { status: "fired", session: execFire } },
        verify: { nonce: "veri0001", at: "2026-10-13T08:02:25Z", dispatch: { status: "fired", session: verFire } },
      },
    },
    back: {
      executions: { exec0001: { exit_code: 0, executed_at: "2026-10-13T08:01:59Z", run_session: execRun, data: DATA } },
      verifications: { veri0001: { exit_code: 0, checked_at: vAt, run_session: verRun, data: vdata } },
    },
  };
}

// ---- adapters --------------------------------------------------------------
// City: builds the city's own mission objects from the rows. `reload` returns
// a fresh page load (with its own tab holder id) for cases that need a second
// open view.
export const cityAdapter = (X, reload) => ({
  X,
  another() {
    if (!reload) throw new Error("cityAdapter needs reload() for multi-view cases");
    return cityAdapter(reload(), reload);
  },
  legacy(page, back) {
    const m = Object.create(X.Legacy.prototype);
    Object.assign(m, { page: page && clone(page), back: back && clone(back), loaded1: true, loaded2: true, status: "ready" });
    return m;
  },
  legacyLevel(page, back) { return this.legacy(page, back).receipt().level; },
  // A legacy mission object wired the way the page wires it: its mission
  // document is `srv` (shared by every view), dispatches are recorded.
  view(srv, back, fires) {
    const m = this.legacy(srv.data(), back);
    Object.assign(m, {
      mref: srv.doc(), cfg: { trigger_id: "trig_01B6ibXq8Cq23pAHZx79HjqP" },
      mcp: { callTool: async (_s, _t, args) => { fires.push(args && args.text); return { payload: {} }; } },
      app: { ui: { toast() {} } }, render() {}, close() {}, openDlg() {},
    });
    return m;
  },
  p2(rows) {
    const def = X.missionDefs.find((d) => d.id === "repo-status-001");
    const g = new X.Generic(def, { db: {}, cfg: CFG, changed() {} });
    g.loaded = [true, true];
    g.page = clone(rows.page);
    g.back = clone(rows.back);
    return g;
  },
  p2Level(rows) { return this.p2(rows).receipt().level; },
});

// Reference: imports the same rows into an evidence log and judges it.
export const refAdapter = (R) => ({
  legacyLog(page, back) { return R.importLegacy(page, back); },
  legacyLevel(page, back) {
    return R.judge(this.legacyLog(page, back), { mission: "reality-001", requestedFacts: R.LEGACY_FACTS, scope: R.LEGACY_SCOPE }).level;
  },
  p2Level(rows) {
    return R.judge(R.importProtocol2(DEF_RS, rows.page, rows.back), { mission: DEF_RS.id, requestedFacts: DEF_RS.verifier.match, scope: DEF_RS.permission.scope }).level;
  },
});

let seq = 0;
const nonce = () => `n${(++seq).toString().padStart(10, "0")}`;

// ---- the cases ---------------------------------------------------------------
export const CASES = [
  {
    id: "1", title: "live reality-001 rows (baseline)",
    note: "The live row does not record who executed the create, so the reference cannot confirm independence.",
    city: (c) => c.legacyLevel(MISSION_V18, BACK_V18),
    ref: (r) => r.legacyLevel(MISSION_V18, BACK_V18),
    expect: { city: REAL, ref: "EXECUTOR-REPORTED" },
  },
  {
    id: "1b", title: "live reality-001 rows + executor identity from the transcript",
    city: (c) => c.legacyLevel(MISSION_V18, BACK_V18_EXEC),
    ref: (r) => r.legacyLevel(MISSION_V18, BACK_V18_EXEC),
    expect: { city: REAL, ref: REAL },
  },
  {
    id: "2", title: "executor and verifier in the same session must not count as REAL", gapInCity: true,
    city: (c) => c.legacyLevel(MISSION_0153, BACK_0153) !== REAL,
    ref: (r) => r.legacyLevel(MISSION_0153, BACK_0153) !== REAL,
    expect: { city: true, ref: true },
  },
  {
    id: "3", title: "a verification row with no run identity must not count as REAL", gapInCity: true,
    rows() {
      const b = clone(BACK_0153);
      delete b.executor_run_session;
      b.verification = { http_status: 200, number: 1, request_nonce: "0b161beca20a23b5656191de", checked_at: "2026-10-12T01:52:49Z", html_url: ISSUE.html_url, title: ISSUE.title };
      return b;
    },
    city(c) { return c.legacyLevel(MISSION_0153, this.rows()) !== REAL; },
    ref(r) { return r.legacyLevel(MISSION_0153, this.rows()) !== REAL; },
    expect: { city: true, ref: true },
  },
  {
    id: "4", title: "read-back older than the issue is rejected",
    rows() { const b = clone(BACK_0153); b.verification.checked_at = "2026-10-12T01:30:00Z"; b.verification.run_session = "cse_01VgDxR55x6eE1MFczoi8Y6u"; return b; },
    city(c) { return c.legacyLevel(MISSION_0153, this.rows()) !== REAL; },
    ref(r) { return r.legacyLevel(MISSION_0153, this.rows()) !== REAL; },
    expect: { city: true, ref: true },
  },
  {
    id: "5", title: "read-back answering an older verify request is rejected",
    rows() { const b = clone(BACK_0153); b.verification.request_nonce = "someOlderNonce01"; b.verification.run_session = "cse_01VgDxR55x6eE1MFczoi8Y6u"; return b; },
    city(c) { return c.legacy(MISSION_0153, this.rows()).stage() !== "verified_pass"; },
    ref(r) { return r.legacyLevel(MISSION_0153, this.rows()) !== REAL; },
    expect: { city: true, ref: true },
  },
  {
    id: "6", title: "read-back 404 makes the mission fail, not pass",
    rows() { const b = clone(BACK_0153); b.verification = ver("0b161beca20a23b5656191de", "2026-10-12T01:52:49Z", "cse_01VgDxR55x6eE1MFczoi8Y6u", 404); return b; },
    city(c) { return c.legacy(MISSION_0153, this.rows()).stage() === "verified_fail"; },
    ref(r) { return r.legacyLevel(MISSION_0153, this.rows()) === "FAILED"; },
    expect: { city: true, ref: true },
  },
  {
    id: "7", title: "a newer read-back that finds the issue gone must demote a passed mission", gapInCity: true,
    rows() {
      const b = clone(BACK_V18_EXEC);
      b.previous_verifications.push(b.verification);
      b.verification = ver("4c5e818a06db43afc526b28f", "2026-10-13T09:00:00Z", "cse_01YyyyyyyyyyyyyyyyyyyyyY9", 404);
      return b;
    },
    city(c) { return c.legacyLevel(MISSION_V18, this.rows()) !== REAL; },
    ref(r) { return r.legacyLevel(MISSION_V18, this.rows()) !== REAL; },
    expect: { city: true, ref: true },
  },
  {
    id: "8", title: "resetting the mission must not erase the verified outcome", gapInCity: true,
    // City: drives the page's real Reset against a shared mission document.
    // Kept = no delete, and the archived run still judges REAL-VERIFIED.
    async city(c) {
      const srv = server(MISSION_V18);
      const m = c.view(srv, BACK_V18_EXEC, []);
      const before = m.receipt().level;
      await m.restart();
      const kept = (srv.data() || {}).archived_runs && srv.data().archived_runs[0];
      const outcomeKept = !srv.ops.some((o) => o === "delete") && !!kept && kept.level === REAL && c.legacyLevel(kept, BACK_V18_EXEC) === REAL;
      return { before, outcomeKept };
    },
    // Reference: there is no delete; a reset is appended and the chain stays valid.
    ref: (r, R) => {
      const log = r.legacyLog(MISSION_V18, BACK_V18_EXEC);
      const opts = { mission: "reality-001", requestedFacts: R.LEGACY_FACTS, scope: R.LEGACY_SCOPE };
      const before = R.judge(log, opts).level;
      R.resetMission(log, { mission: "reality-001", at: "2026-10-13T10:00:00Z", by: "owner" });
      const rebuilt = R.EvidenceLog.fromEntries(log.entries());
      const outcomeKept = typeof log.delete === "undefined" && typeof log.update === "undefined" && R.judge(rebuilt, opts).level === REAL;
      return { before, outcomeKept };
    },
    expect: { city: { before: REAL, outcomeKept: true }, ref: { before: REAL, outcomeKept: true } },
  },
  {
    id: "9", title: "p2: live-shaped run with separate sessions (baseline)",
    city: (c) => c.p2Level(p2Rows()), ref: (r) => r.p2Level(p2Rows()),
    expect: { city: REAL, ref: REAL },
  },
  {
    id: "10", title: "p2: same run session for executor and verifier is not REAL",
    city: (c) => c.p2Level(p2Rows({ verRun: SID_A, verFire: SID_A })) !== REAL,
    ref: (r) => r.p2Level(p2Rows({ verRun: SID_A, verFire: SID_A })) !== REAL,
    expect: { city: true, ref: true },
  },
  {
    id: "11", title: "p2: verifier facts that differ make it FAILED",
    city: (c) => c.p2Level(p2Rows({ vdata: { ...DATA, head_sha: "deadbeef" } })) === "FAILED",
    ref: (r) => r.p2Level(p2Rows({ vdata: { ...DATA, head_sha: "deadbeef" } })) === "FAILED",
    expect: { city: true, ref: true },
  },
  {
    id: "12", title: "p2: verifier older than executor is not REAL",
    city: (c) => c.p2Level(p2Rows({ vAt: "2026-10-13T08:00:00Z" })) !== REAL,
    ref: (r) => r.p2Level(p2Rows({ vAt: "2026-10-13T08:00:00Z" })) !== REAL,
    expect: { city: true, ref: true },
  },
  {
    id: "13", title: "p2: denied permission reads DENIED",
    city: (c) => c.p2Level(p2Rows({ perm: "denied" })), ref: (r) => r.p2Level(p2Rows({ perm: "denied" })),
    expect: { city: "DENIED BY OWNER", ref: "DENIED BY OWNER" },
  },
  {
    id: "14", title: "p2: permission scope drift blocks the run",
    city: (c) => c.p2Level(p2Rows({ scope: "something broader" })), ref: (r) => r.p2Level(p2Rows({ scope: "something broader" })),
    expect: { city: "PERMISSION REQUIRED", ref: "PERMISSION REQUIRED" },
  },
  {
    id: "15", title: "p2: unknown run identities on both sides must not count as REAL", gapInCity: true,
    rows: () => p2Rows({ execRun: "unrecorded", verRun: "unrecorded", execFire: null, verFire: null }),
    city(c) { return c.p2Level(this.rows()) !== REAL; },
    ref(r) { return r.p2Level(this.rows()) !== REAL; },
    expect: { city: true, ref: true },
  },
  {
    id: "16", title: "p2: a near-identical session id must not count as a different verifier", gapInCity: true,
    rows: () => p2Rows({ verRun: `${SID_A} `, verFire: `${SID_A} ` }),
    city(c) { return c.p2Level(this.rows()) !== REAL; },
    ref(r) { return r.p2Level(this.rows()) !== REAL; },
    expect: { city: true, ref: true },
  },
  {
    id: "17", title: "p2: a second view that loses the lease fires nothing (and does not crash)",
    async city(c) { return p2Dispatch(c, { leaseHeld: true }); },
    async ref(r, R) { return refDispatchP2(R, { leaseHeld: true }); },
    expect: { city: { fires: 0, crashed: false }, ref: { fires: 0, crashed: false } },
  },
  {
    id: "17c", title: "control: a lone view with a free lease fires exactly once",
    async city(c) { return p2Dispatch(c, {}); },
    async ref(r, R) { return refDispatchP2(R, {}); },
    expect: { city: { fires: 1, crashed: false }, ref: { fires: 1, crashed: false } },
  },
  {
    id: "18", title: "p2: a repeat click while a request is pending fires nothing (and does not crash)",
    async city(c) { return p2Dispatch(c, { pendingAgeMs: 0 }); },
    async ref(r, R) { return refDispatchP2(R, { pendingAgeMs: 0 }); },
    expect: { city: { fires: 0, crashed: false }, ref: { fires: 0, crashed: false } },
  },
  {
    id: "18c", title: "control: a request older than the 8-minute pending window does not block",
    async city(c) { return p2Dispatch(c, { pendingAgeMs: 9 * 60_000 }); },
    async ref(r, R) { return refDispatchP2(R, { pendingAgeMs: 9 * 60_000 }); },
    expect: { city: { fires: 1, crashed: false }, ref: { fires: 1, crashed: false } },
  },
  {
    id: "19", title: "legacy: two views completing the mission at once fire one verify, not two", gapInCity: true,
    async city(c) {
      const srv = server(READY), fires = [];
      const v1 = c.view(srv, BACK_0153, fires), v2 = c.another().view(srv, BACK_0153, fires);
      await Promise.all([v1.complete(), v2.complete()]);
      return { fires: fires.length, crashed: crashed(v1.note) || crashed(v2.note) };
    },
    async ref(r, R) {
      const log = r.legacyLog(READY, BACK_0153), leases = new R.LeaseStore();
      let fires = 0;
      const tab = (holder) => new R.Dispatcher({ log, leases, nonce }).dispatch({ mission: "reality-001", action: "verify", holder, fire: async () => { fires++; } });
      await Promise.all([tab("tab_one"), tab("tab_two")]);
      return { fires, crashed: false };
    },
    expect: { city: { fires: 1, crashed: false }, ref: { fires: 1, crashed: false } },
  },
  {
    id: "19c", title: "control: one view completing the mission fires exactly one verify",
    async city(c) {
      const srv = server(READY), fires = [];
      const v = c.view(srv, BACK_0153, fires);
      await v.complete();
      return { fires: fires.length, crashed: crashed(v.note) };
    },
    async ref(r, R) {
      let fires = 0;
      await new R.Dispatcher({ log: r.legacyLog(READY, BACK_0153), leases: new R.LeaseStore(), nonce }).dispatch({ mission: "reality-001", action: "verify", holder: "tab_one", fire: async () => { fires++; } });
      return { fires, crashed: false };
    },
    expect: { city: { fires: 1, crashed: false }, ref: { fires: 1, crashed: false } },
  },
  {
    id: "19e", title: "control: retry after the previous verify was answered with a recorded error fires",
    async city(c) {
      const at = new Date().toISOString();
      const srv = server({ ...READY, requests: { ...READY.requests, verify: { nonce: "verify00001", at } } }), fires = [];
      const back = { ...clone(BACK_0153), status: "blocked", error: { action: "verify", nonce: "verify00001", reason: "repo_not_attached", at } };
      const v = c.view(srv, back, fires);
      await v.retry("verify");
      return { fires: fires.length, crashed: crashed(v.note) };
    },
    async ref(r, R) {
      const at = new Date().toISOString();
      const log = r.legacyLog(READY, BACK_0153);
      log.append({ type: "request", mission: "reality-001", action: "verify", nonce: "verify00001", at });
      log.append({ type: "error", mission: "reality-001", nonce: "verify00001", reason: "repo_not_attached", at });
      let fires = 0;
      await new R.Dispatcher({ log, leases: new R.LeaseStore(), nonce }).dispatch({ mission: "reality-001", action: "verify", holder: "tab_one", fire: async () => { fires++; } });
      return { fires, crashed: false };
    },
    expect: { city: { fires: 1, crashed: false }, ref: { fires: 1, crashed: false } },
  },
];

// The legacy mission ready for COMPLETE: accepted, evidence inspected, no verify request yet.
const READY = { ...MISSION_0153, requests: { create: MISSION_0153.requests.create } };

// A thrown JavaScript error caught by the city and shown as a note. A case
// that expects "nothing fired" must not pass this way.
const crashed = (note) => /is not defined|is not a function|Cannot read propert|reading '/.test(String(note || ""));

// One mission document as the database holds it, shared by every view:
// a single lease holder per TTL, merge update, set, delete. Records writes.
export function server(initial) {
  let data = initial == null ? null : clone(initial), lease = null;
  const ops = [];
  const merge = (a, b) => { for (const [k, v] of Object.entries(b)) a[k] = v && typeof v === "object" && !Array.isArray(v) && a[k] && typeof a[k] === "object" ? merge(a[k], v) : v; return a; };
  return {
    ops,
    data: () => data && clone(data),
    holdLease(holder, ms = 5000) { lease = { holder, until: Date.now() + ms }; },
    doc: () => ({
      async acquire({ holder, ttlMs }) {
        const now = Date.now();
        if (lease && lease.holder !== holder && lease.until > now) return { acquired: false };
        lease = { holder, until: now + ttlMs };
        return { acquired: true };
      },
      async get() { return { exists: data != null, data: () => clone(data) }; },
      async update(p) { ops.push("update"); data = merge(data || {}, clone(p)); },
      async set(p) { ops.push("set"); data = clone(p); },
      async delete() { ops.push("delete"); data = null; },
    }),
  };
}

// Protocol-2 dispatch through the city's real code against a shared document.
async function p2Dispatch(c, { leaseHeld = false, pendingAgeMs } = {}) {
  const rows = p2Rows(); rows.back = {};
  rows.page.requests = pendingAgeMs === undefined ? {} :
    { execute: { nonce: "exec0002", at: new Date(Date.now() - pendingAgeMs).toISOString(), dispatch: { status: "fired" } } };
  const g = c.p2(rows), srv = server(g.page);
  if (leaseHeld) srv.holdLease("tab_other");
  let fires = 0;
  g.rt.mcp = { callTool: async () => { fires++; return { payload: {} }; } };
  g.mref = srv.doc();
  await g.dispatch("execute");
  return { fires, crashed: crashed(g.note) };
}

async function refDispatchP2(R, { leaseHeld = false, pendingAgeMs } = {}) {
  const rows = p2Rows(); rows.back = {};
  rows.page.requests = pendingAgeMs === undefined ? {} :
    { execute: { nonce: "exec0002", at: new Date(Date.now() - pendingAgeMs).toISOString(), dispatch: { status: "fired" } } };
  const log = R.importProtocol2(DEF_RS, rows.page, rows.back), leases = new R.LeaseStore();
  if (leaseHeld) leases.acquire("repo-status-001:execute", "tab_other", 5000);
  let fires = 0;
  await new R.Dispatcher({ log, leases, nonce }).dispatch({ mission: "repo-status-001", action: "execute", holder: "tab_me", fire: async () => { fires++; } });
  return { fires, crashed: false };
}
