// Reference truth core for PI City: an independent, clean-room statement of
// the truth rules the audit found missing. It is NOT derived from the city's
// source and does not run in the live city. It exists so the rules can be
// specified and tested before anything is changed in the private artifact.
//
// Rules, each tied to an audit gap:
//   1. Evidence is an append-only, hash-chained log. There is no update or
//      delete; a reset is an appended event, never a removal.
//   2. A read-back counts as independent only if BOTH the executor and the
//      verifier have a recorded, canonical run identity and they differ.
//      Unknown, malformed or conflicting identities never count.
//   3. A read-back must answer a verify request the mission itself issued,
//      be no older than the execution, and match every requested fact.
//   4. The newest observation wins: a newer failed read-back demotes a
//      previously verified outcome.
//   5. Permission counts only when the owner granted it for the exact scope.
//   6. Dispatch takes a lease and refuses while a request is still pending.
import { createHash } from "node:crypto";

export const LEVEL = Object.freeze({
  NOT_STARTED: "NOT STARTED",
  PERMISSION: "PERMISSION REQUIRED",
  DENIED: "DENIED BY OWNER",
  PENDING: "PENDING",
  REPORTED: "EXECUTOR-REPORTED",
  FAILED: "FAILED",
  REAL: "REAL-VERIFIED",
});

// ---- evidence log --------------------------------------------------------

const canonical = (v) =>
  v === null || typeof v !== "object"
    ? JSON.stringify(v)
    : Array.isArray(v)
      ? `[${v.map(canonical).join(",")}]`
      : `{${Object.keys(v).filter((k) => v[k] !== undefined).sort().map((k) => `${JSON.stringify(k)}:${canonical(v[k])}`).join(",")}}`;

const digest = (prev, event) => createHash("sha256").update(prev).update("\n").update(canonical(event)).digest("hex");
const GENESIS = "0".repeat(64);

function deepFreeze(o) {
  if (o && typeof o === "object" && !Object.isFrozen(o)) {
    Object.freeze(o);
    for (const v of Object.values(o)) deepFreeze(v);
  }
  return o;
}

export class EvidenceLog {
  #entries = [];

  append(event) {
    if (!event || typeof event.type !== "string") throw new TypeError("event.type required");
    const prev = this.#entries.length ? this.#entries[this.#entries.length - 1].hash : GENESIS;
    const ev = deepFreeze(JSON.parse(JSON.stringify(event)));
    const entry = deepFreeze({ seq: this.#entries.length, prev, hash: digest(prev, ev), event: ev });
    this.#entries.push(entry);
    return entry;
  }

  entries() { return this.#entries.slice(); }
  events(type) { return this.#entries.map((e) => e.event).filter((e) => !type || e.type === type); }
  get head() { return this.#entries.length ? this.#entries[this.#entries.length - 1].hash : GENESIS; }

  // Rebuilds a log from exported entries; throws if any entry was altered,
  // dropped, inserted or reordered.
  static fromEntries(entries) {
    const log = new EvidenceLog();
    entries.forEach((e, i) => {
      const expectPrev = i ? entries[i - 1].hash : GENESIS;
      if (e.seq !== i || e.prev !== expectPrev || e.hash !== digest(e.prev, e.event)) {
        throw new Error(`evidence chain broken at entry ${i}`);
      }
      log.append(e.event);
    });
    return log;
  }
}

// ---- identity ------------------------------------------------------------

// A platform-issued run identity, exactly. No trimming, no annotations.
// Either a Claude session id, or a GitHub Actions run as
// gha:<owner>/<repo>/<run_id>/<attempt> (verifier/repo-status-verifier.mjs).
const IDENTITY = /^(?:(?:cse|session)_[A-Za-z0-9]{10,64}|gha:[A-Za-z0-9-]{1,39}\/[A-Za-z0-9._-]{1,100}\/[0-9]{1,20}\/[0-9]{1,6})$/;
export const canonicalIdentity = (s) => (typeof s === "string" && IDENTITY.test(s) ? s : null);

// Identity of a run = its self-reported session and the dispatcher-reported
// session. Either alone is accepted if canonical; if both are canonical they
// must agree, otherwise the identity is unknown.
export function runIdentity({ run, fire } = {}) {
  const a = canonicalIdentity(run), b = canonicalIdentity(fire);
  if (a && b && a !== b) return null;
  return a || b;
}

// ---- judgement -----------------------------------------------------------

const t = (s) => Date.parse(s);
const factsMatch = (requested, expected, observed) =>
  requested.every((k) => expected && observed && expected[k] !== undefined && expected[k] === observed[k]);

// policy.independence:
//   "distinct-run"  (default) recorded, canonical, different run identities
//   "distinct-path" additionally a different verification path, e.g. a
//                   GitHub Action vs a Claude routine
export function judge(log, { mission, requestedFacts, scope, policy = {} }) {
  const ev = log.events().filter((e) => e.mission === mission);
  const why = (level, reason) => ({ level, reason });

  if (!ev.some((e) => e.type === "run_started")) return why(LEVEL.NOT_STARTED, "no run");

  const perms = ev.filter((e) => e.type === "permission");
  const perm = perms[perms.length - 1];
  if (perm && perm.status === "denied" && perm.by === "owner") return why(LEVEL.DENIED, "owner denied");
  if (!perm || perm.status !== "granted" || perm.by !== "owner" || perm.scope !== scope) {
    return why(LEVEL.PERMISSION, !perm ? "no permission" : perm.by !== "owner" ? "permission not granted by the owner" : "permission scope mismatch");
  }

  const execReqs = ev.filter((e) => e.type === "request" && e.action === "execute");
  const execReq = execReqs[execReqs.length - 1];
  const exec = execReq && ev.find((e) => e.type === "execution" && e.nonce === execReq.nonce);
  const execErr = execReq && ev.find((e) => e.type === "error" && e.nonce === execReq.nonce);
  if (!exec && execErr) return why(LEVEL.FAILED, `executor: ${execErr.reason}`);
  if (!exec) return why(LEVEL.PENDING, execReq ? "awaiting executor" : "not dispatched");
  if (!exec.ok) return why(LEVEL.FAILED, `executor failed (${exec.status})`);

  const verifyNonces = new Set(ev.filter((e) => e.type === "request" && e.action === "verify").map((e) => e.nonce));
  const obs = ev.filter((e) => e.type === "verification").sort((a, b) => t(b.at) - t(a.at));
  if (!obs.length) return why(LEVEL.REPORTED, "no read-back yet");

  const ok = (v) => v.ok && factsMatch(requestedFacts, exec.facts, v.facts);
  if (!ok(obs[0])) {
    return why(LEVEL.FAILED, obs[0].ok ? "latest read-back facts differ from the execution" : `latest read-back failed (${obs[0].status})`);
  }

  const execId = runIdentity(exec);
  if (!execId) return why(LEVEL.REPORTED, "executor identity not recorded");
  const independent = obs.find((v) =>
    ok(v) && verifyNonces.has(v.nonce) && v.nonce !== exec.nonce && t(v.at) >= t(exec.at) &&
    runIdentity(v) && runIdentity(v) !== execId &&
    (policy.independence !== "distinct-path" || (v.path && exec.path && v.path !== exec.path)));
  if (!independent) return why(LEVEL.REPORTED, "no independent read-back answering our request");
  return why(LEVEL.REAL, `read back by ${runIdentity(independent)}, executed by ${execId}`);
}

// Reset is an appended event. Evidence of earlier runs is never removed.
export function resetMission(log, { mission, at, by }) {
  return log.append({ type: "run_archived", mission, at, by });
}

// ---- dispatch ------------------------------------------------------------

export class LeaseStore {
  #held = new Map();
  acquire(key, holder, ttlMs, now = Date.now()) {
    const cur = this.#held.get(key);
    if (cur && cur.holder !== holder && cur.until > now) return false;
    this.#held.set(key, { holder, until: now + ttlMs });
    return true;
  }
}

export class Dispatcher {
  constructor({ log, leases, pendingMs = 8 * 60_000, leaseMs = 5_000, now = () => Date.now(), nonce }) {
    Object.assign(this, { log, leases, pendingMs, leaseMs, now, nonce });
  }

  pending(mission, action) {
    const ev = this.log.events().filter((e) => e.mission === mission);
    const answered = new Set(ev.filter((e) => ["execution", "verification", "error"].includes(e.type)).map((e) => e.nonce));
    return ev.some((e) => e.type === "request" && e.action === action && !answered.has(e.nonce) && this.now() - t(e.at) < this.pendingMs);
  }

  // fire(nonce) performs the external dispatch. Returns {fired, reason}.
  async dispatch({ mission, action, holder, fire }) {
    if (!this.leases.acquire(`${mission}:${action}`, holder, this.leaseMs, this.now())) return { fired: false, reason: "lease held by another view" };
    if (this.pending(mission, action)) return { fired: false, reason: "request already pending" };
    const nonce = this.nonce();
    this.log.append({ type: "request", mission, action, nonce, at: new Date(this.now()).toISOString(), by: holder });
    await fire(nonce);
    return { fired: true, nonce };
  }
}
