// Translates PI City's database row shapes (missions/<id>, backend/<id>) into
// reference evidence-log events, so the reference judges exactly the same
// inputs as the city. Only data shapes are used here, never city code.
import { EvidenceLog } from "./truth-core.mjs";

// Who granted a permission, from the city's free-text `decided_in`.
// Anything that says it was recorded by an agent is not an owner grant.
const grantedBy = (p) => (/recorded by claude|claude-session|agent/i.test(`${p.decided_in || ""} ${p.by || ""}`) ? "agent" : "owner");

// Legacy reality-001. The city has no permission object for it: accepting
// the mission in the city view is the owner's grant.
export const LEGACY_SCOPE = "Create one issue in PrEM21032/pi-city-reality-test";
export const LEGACY_FACTS = ["number", "html_url", "title"];

export function importLegacy(page, back, log = new EvidenceLog()) {
  const mission = "reality-001";
  if (!page || !page.acceptedAt) return log;
  log.append({ type: "run_started", mission, at: page.acceptedAt });
  log.append({ type: "permission", mission, status: "granted", by: "owner", scope: LEGACY_SCOPE, at: page.acceptedAt });
  const req = page.requests || {};
  if (req.create) log.append({ type: "request", mission, action: "execute", nonce: req.create.nonce, at: req.create.at });
  // The verify requests the mission itself issued: the current one, and the
  // one the passed mission was pinned to.
  if (req.verify) log.append({ type: "request", mission, action: "verify", nonce: req.verify.nonce, at: req.verify.at });
  const pinned = page.completion && page.completion.verify_nonce;
  if (pinned && pinned !== (req.verify && req.verify.nonce)) {
    log.append({ type: "request", mission, action: "verify", nonce: pinned, at: page.completion.checked_at || null });
  }
  if (!back) return log;
  const issue = back.issue || {};
  if (Number(back.api_status) === 201 && issue.number) {
    log.append({
      type: "execution", mission, nonce: back.request_nonce, at: issue.created_at, ok: true, status: 201,
      run: back.executor_run_session ?? null, path: "claude-routine",
      facts: { number: issue.number, html_url: issue.html_url, title: issue.title },
    });
  }
  for (const v of [back.verification, ...(back.previous_verifications || [])].filter(Boolean)) {
    const status = Number(v.http_status);
    log.append({
      type: "verification", mission, nonce: v.request_nonce ?? v.nonce, at: v.checked_at, status, ok: status === 200,
      run: v.run_session ?? null, path: v.path || "claude-routine",
      facts: { number: v.number, html_url: v.html_url, title: v.title },
    });
  }
  return log;
}

// Protocol-2 missions (repo-status-001 and later).
export function importProtocol2(def, page, back, log = new EvidenceLog()) {
  const mission = def.id;
  if (!page || !page.run) return log;
  log.append({ type: "run_started", mission, run: page.run, at: page.started_at || null });
  const p = page.permission;
  if (p && (p.status === "granted" || p.status === "denied")) {
    log.append({ type: "permission", mission, status: p.status, by: grantedBy(p), scope: p.scope, at: p.decided_at || null });
  }
  const ok = (r) => (def.result === "exit_code" ? Number(r.exit_code) === 0 : Number(r.http_status) >= 200 && Number(r.http_status) < 300);
  const status = (r) => (def.result === "exit_code" ? `exit ${r.exit_code}` : r.http_status);
  const reqs = page.requests || {};
  for (const action of ["execute", "verify"]) {
    const r = reqs[action];
    if (!r) continue;
    log.append({ type: "request", mission, action, nonce: r.nonce, at: r.at });
    const rows = back && (action === "execute" ? back.executions : back.verifications);
    const row = rows && rows[r.nonce];
    const err = back && back.errors && back.errors[r.nonce];
    const fire = (r.dispatch && r.dispatch.session) || null;
    if (row) {
      log.append({
        type: action === "execute" ? "execution" : "verification", mission, nonce: r.nonce,
        at: action === "execute" ? row.executed_at : row.checked_at,
        ok: ok(row), status: status(row), run: row.run_session ?? null, fire, path: row.path || "claude-routine", facts: row.data || {},
      });
    } else if (err) {
      log.append({ type: "error", mission, nonce: r.nonce, reason: err.reason, at: err.at });
    }
  }
  return log;
}
