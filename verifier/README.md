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

## A record is a claim, not proof

- **The record proves nothing on its own.** `run_session`, `path` and `evidence_url` are strings: anyone who can write the database can type them, and the Actions environment variables the verifier reads can be set by hand.
- **The reference therefore fails closed.** A well-formed `gha:` record on its own stays **EXECUTOR-REPORTED**, under every policy (`reference/attestation.test.mjs`, A0). A writable `path` string never satisfies the `distinct-path` policy (A3).
- **The parser does not guess.** It refuses ambiguous output (no HEAD symref, malformed SHAs, a duplicate HEAD).

## When it can count: the run attestation contract

An Actions-run verification counts as REAL-VERIFIED only when the judge is also handed an **attestation** (`reference/attestation.mjs`). The attestation:

1. **comes over a separate trust path.** It is passed to the judge directly, never read from a database row (A0b). It is fetched by an identity the owner has designated, and not by the executor. Its record digest must match the attested record.
2. **names the exact run.** The run id and attempt match the claimed identity. The run is in the mission repository and runs the pinned workflow file (`.github/workflows/repo-status-verify.yml`) at a workflow commit the owner has reviewed and pinned. It is a `workflow_dispatch` run, `completed`, with conclusion `success`.
3. **is bound to the mission request.** The run title is `repo-status-verify <nonce>`, the record's nonce matches the mission's own verify request, and the run started after both that request and the execution. The read happened inside the run's time window.
4. **carries exact facts.** The read succeeded, and the record names the same run. The database row's time and facts equal the attested record exactly, and the attested facts equal the execution's on the matched fields.

The default trust is empty (no pinned workflow commit, no designated fetcher), so **nothing passes until the owner configures it**. Every term is covered by a test that breaks only that term, and removing any single check makes the suite fail (22/22 mutations caught).

## Run

```
node --test verifier/repo-status-verifier.test.mjs reference/attestation.test.mjs
node verifier/repo-status-verifier.mjs --repo PrEM21032/pi-city-reality-test --nonce <nonce> [--expect executor.json]
```

Exit codes: 0 = the read succeeded (and matches `--expect`); 2 = facts differ; 1 = the read failed or the input was invalid.

## Future work (not done; each needs owner approval)

1. **Activate the workflow.** Move `ci/repo-status-verify.yml` into `.github/workflows/` on the default branch (a reviewed merge). It uses no secrets and `permissions: {}`.
2. **Pin trust.** Record the reviewed workflow commit SHA(s) and the designated fetcher identity.
3. **Build the fetcher.** It reads `GET /repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{attempt}` and the run's uploaded `record.json`, computes the digest, and hands the attestation to the judge over a channel the database cannot write. Downloading run artifacts may require a GitHub token, which would be a new credential and needs approval. Nothing here fetches from GitHub's API.
4. **Wire the live city.** The live city does not implement this rule; adopting it means changing and republishing the artifact.
