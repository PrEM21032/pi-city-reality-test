# Independent verifier: repo-status missions

A deterministic, non-AI verifier for `repo-status-001`. It reads the public
mission repository with `git ls-remote --symref` (no credentials) and emits
a verification record in the shape the protocol-2 backend writes to
`backend/repo-status-001.verifications.<nonce>`:

```json
{ "nonce": "…", "checked_at": "…Z", "exit_code": 0,
  "run_session": "gha:<owner>/<repo>/<run_id>/<attempt>", "path": "github-action",
  "evidence_url": "https://github.com/<owner>/<repo>/actions/runs/<run_id>/attempts/<attempt>",
  "data": { "repo_url": "…", "default_branch": "main", "head_sha": "…", "branch_count": 2 } }
```

## Why it is independent

- **It is not an AI.** It is a fixed parser that refuses ambiguous output (no HEAD symref, malformed SHAs, duplicate HEAD) instead of guessing.
- **It runs on a different path.** Inside GitHub Actions, its identity and evidence URL come from the platform's own run metadata. Anyone can open the run and its log, so the record can be re-checked without trusting whoever stored it.
- **The reference rules agree.** `reference/` accepts `gha:` identities, so a record from an Actions run is REAL-VERIFIED even under the stricter `distinct-path` policy. A local run has no identity and never counts.

## Run

```
node --test verifier/repo-status-verifier.test.mjs      # offline, recorded git output
node verifier/repo-status-verifier.mjs --repo PrEM21032/pi-city-reality-test --nonce <nonce> [--expect executor.json]
```

Exit codes: 0 = the read succeeded (and matches `--expect`); 2 = facts differ; 1 = the read failed or the input was invalid.

## What is not done (needs owner decisions)

1. **Activate the workflow.** Move `ci/repo-status-verify.yml` into `.github/workflows/` on the default branch (a reviewed merge). It needs no secrets and `permissions: {}`.
2. **Deliver records into PI City.** Nothing here writes to the artifact database; that needs a writer with database access. One option: the existing protocol-2 routine (or the page) copies the record *and* its `evidence_url`, and the city's truth check re-reads the run. That changes a live routine or the artifact, so it needs separate approval. No new credential is needed for the read side.
3. **Adopt the policy.** The live city does not yet require a distinct verification path; `reference/` shows the rule.
