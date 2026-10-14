// Independent, deterministic verifier for PI City's repo-status missions.
//
// It reads a public GitHub repository's default branch and head commit with
// `git ls-remote --symref` (no credentials, no AI), and produces a
// verification record in the same shape the protocol-2 backend writes. When
// it runs inside GitHub Actions the record carries an identity and evidence
// URL derived from the platform's own run metadata, so anyone can re-open the
// run and check it; that is a verification path separate from the Claude
// routine that executes the mission.
//
// It never writes to PI City's database. Delivering a record there is a
// separate, owner-approved step (see verifier/README.md).
import { execFile } from "node:child_process";

export const MATCH_FIELDS = ["default_branch", "head_sha"];
const REPO = /^[A-Za-z0-9-]{1,39}\/[A-Za-z0-9._-]{1,100}$/;
const SHA = /^[0-9a-f]{40}$/;

// Parses `git ls-remote --symref <url>` output. Throws on anything ambiguous
// rather than guessing: a verifier that guesses is not a verifier.
export function parseLsRemote(text) {
  if (typeof text !== "string" || !text.trim()) throw new Error("empty ls-remote output");
  let defaultBranch = null, headSha = null, branches = 0;
  for (const line of text.split("\n")) {
    if (!line.trim()) continue;
    const [left, ref] = line.split("\t");
    if (ref === undefined) throw new Error(`unparseable line: ${JSON.stringify(line)}`);
    if (left.startsWith("ref: ")) {
      if (ref !== "HEAD") continue;
      const target = left.slice(5);
      if (!target.startsWith("refs/heads/")) throw new Error(`HEAD points outside refs/heads: ${target}`);
      if (defaultBranch !== null) throw new Error("HEAD symref listed twice");
      defaultBranch = target.slice("refs/heads/".length);
    } else if (ref === "HEAD") {
      if (!SHA.test(left)) throw new Error(`HEAD sha is not 40 hex characters: ${left}`);
      headSha = left;
    } else if (ref.startsWith("refs/heads/")) {
      if (!SHA.test(left)) throw new Error(`branch sha is not 40 hex characters: ${left}`);
      branches++;
    }
  }
  if (!defaultBranch) throw new Error("no HEAD symref: default branch unknown");
  if (!headSha) throw new Error("no HEAD commit");
  return { default_branch: defaultBranch, head_sha: headSha, branch_count: branches };
}

// Who ran this verification. Inside GitHub Actions the identity comes from the
// platform's run metadata; anywhere else it is null, so a local run can never
// count as an independent verifier.
export function runIdentity(env = process.env) {
  if (env.GITHUB_ACTIONS !== "true") return { identity: null, path: "local", evidence_url: null };
  const { GITHUB_REPOSITORY: repo, GITHUB_RUN_ID: run, GITHUB_RUN_ATTEMPT: attempt, GITHUB_SERVER_URL: server } = env;
  if (!REPO.test(repo || "") || !/^[0-9]+$/.test(run || "") || !/^[0-9]+$/.test(attempt || "")) {
    return { identity: null, path: "github-action", evidence_url: null };
  }
  return {
    identity: `gha:${repo}/${run}/${attempt}`,
    path: "github-action",
    evidence_url: `${server || "https://github.com"}/${repo}/actions/runs/${run}/attempts/${attempt}`,
  };
}

export function lsRemote(repo, { timeoutMs = 30_000 } = {}) {
  return new Promise((resolve) => {
    execFile("git", ["ls-remote", "--symref", `https://github.com/${repo}`], { timeout: timeoutMs, env: { ...process.env, GIT_TERMINAL_PROMPT: "0" } },
      (err, stdout, stderr) => resolve({ exitCode: err ? (typeof err.code === "number" ? err.code : 1) : 0, stdout, stderr: String(stderr || "").slice(0, 200) }));
  });
}

// Runs the read and builds the record. `run` and `now` are injectable for tests.
export async function verifyRepoStatus({ repo, nonce, env = process.env, run = lsRemote, now = () => new Date() }) {
  if (!REPO.test(repo || "")) throw new Error(`invalid repo: ${repo}`);
  if (!/^[A-Za-z0-9_-]{6,40}$/.test(nonce || "")) throw new Error("invalid nonce");
  const res = await run(repo);
  const checked_at = now().toISOString().replace(/\.\d{3}Z$/, "Z");
  const who = runIdentity(env);
  const base = { nonce, checked_at, exit_code: res.exitCode, run_session: who.identity, path: who.path, evidence_url: who.evidence_url, verifier: "verifier/repo-status-verifier.mjs" };
  if (res.exitCode !== 0) return { ...base, data: {}, stderr_excerpt: res.stderr };
  try {
    return { ...base, data: { repo_url: `https://github.com/${repo}`, ...parseLsRemote(res.stdout) } };
  } catch (e) {
    return { ...base, exit_code: 3, data: {}, parse_error: e.message };
  }
}

// Compares the verifier's facts with an executor's on the matched fields only.
export function compare(executorData, verifierData, fields = MATCH_FIELDS) {
  const diffs = fields.filter((f) => executorData?.[f] === undefined || executorData[f] !== verifierData?.[f]);
  return { match: diffs.length === 0, diffs };
}

// CLI: node verifier/repo-status-verifier.mjs --repo owner/name --nonce N [--expect executor.json]
// Prints the record. Exit 0 = read ok (and matches --expect, if given),
// 2 = facts differ from --expect, 1 = the read failed or input was invalid.
if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  const arg = (k) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : undefined; };
  try {
    const record = await verifyRepoStatus({ repo: arg("--repo"), nonce: arg("--nonce") });
    let code = record.exit_code === 0 ? 0 : 1;
    if (code === 0 && arg("--expect")) {
      const { readFileSync } = await import("node:fs");
      const exec = JSON.parse(readFileSync(arg("--expect"), "utf8"));
      record.comparison = compare(exec.data || exec, record.data);
      if (!record.comparison.match) code = 2;
    }
    console.log(JSON.stringify(record, null, 2));
    process.exit(code);
  } catch (e) {
    console.error(`verifier error: ${e.message}`);
    process.exit(1);
  }
}
