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

## The attestation fetcher (read-only adapter, not connected)

`verifier/fetch-attestation.mjs` turns three official GitHub REST API responses into an attestation for `reference/attestation.mjs`:

1. `GET /repos/{o}/{r}/actions/runs/{run_id}/attempts/{attempt}`: the run attempt.
2. `GET /repos/{o}/{r}/actions/runs/{run_id}/artifacts?name=repo-status-verification-<nonce>`: the artifact list.
3. `GET /repos/{o}/{r}/actions/artifacts/{artifact_id}/zip`: the artifact archive.

**What the official API says.** This comes from GitHub's OpenAPI description (`github/rest-api-description`, v1.1.4). The docs site was not reachable from the build environment.

- Endpoints 1 and 2 are documented as readable by "anyone with read access to the repository".
- Endpoint 3 has no such sentence. It says OAuth and classic personal access tokens "need the `repo` scope", and it answers with a redirect that expires after one minute. The adapter therefore treats download as **requiring a token**.

**Fails closed.** `buildAttestation` is pure and throws `AttestationError` on anything missing or ambiguous:

- **Run attempt:** a missing or mistyped run field. A run whose id, attempt or repository differs from the claimed identity. A run that has not concluded (`conclusion: null`). A workflow path that is not exactly `.github/workflows/<file>` or `<this repo>/.github/workflows/<file>@<ref>`.
- **Artifact list:** `total_count` missing or not a safe integer, or not equal to the number of entries returned. Either way the list may be paginated or truncated, and a duplicate could sit on a page that was not read.
- **Artifact:** none for the nonce, or more than one. `size_in_bytes` missing or over the archive bound. An expired artifact, or one whose expiry is unknown. An artifact from another run or commit. A missing digest (`upload-artifact` older than v4 reports none).
- **Archive:** archive bytes that differ from GitHub's `sha256:` digest. An archive that is not exactly one `record.json` JSON object. A ZIP that is zip64, encrypted, multi-disk or fails its CRC check. A ZIP that is ambiguous: bytes after the end record, or local and central headers that disagree.
- **Size:** nothing unbounded is hashed, inflated or parsed. The archive is at most 256 KiB, with at most one entry. That entry (and so `record.json`) is at most 64 KiB both compressed and uncompressed, and inflation stops at its declared size.
- **Timestamps:** run times must be RFC 3339, the API's documented `date-time` format. Loose forms that `Date.parse` would accept are refused.

The adapter checks that the data is consistent. Trust (the pinned workflow commit, the designated fetcher), the nonce and the exact facts are still judged by `reference/attestation.mjs`.

**The network boundary.**

- `fetchRunAttestation` makes exactly those three calls, in order, through an injected `http` client.
- It checks the nonce and fetcher before the first call. It checks the whole artifact list (completeness, uniqueness, size) before the download.
- It passes the byte bound to the client (`downloadArtifactZip(path, { maxBytes })`), and still refuses an archive over it if the client ignores the bound.
- The default client (`unconfiguredHttp`) refuses every call.

**Proof limit.** The tests use fixtures shaped from the OpenAPI schemas. No real run or artifact has been fetched. The workflow is not active, and this repository has no workflow runs.

## Run

```
node --test verifier/repo-status-verifier.test.mjs verifier/fetch-attestation.test.mjs reference/attestation.test.mjs
node verifier/repo-status-verifier.mjs --repo PrEM21032/pi-city-reality-test --nonce <nonce> [--expect executor.json]
```

Exit codes: 0 = the read succeeded (and matches `--expect`); 2 = facts differ; 1 = the read failed or the input was invalid.

## Future work (not done; each needs owner approval)

1. **Activate the workflow.** Move `ci/repo-status-verify.yml` into `.github/workflows/` on the default branch (a reviewed merge). It uses no secrets and `permissions: {}`.
2. **Pin trust.** Record the reviewed workflow commit SHA(s) and the designated fetcher identity.
3. **Connect the fetcher.** The adapter exists (`verifier/fetch-attestation.mjs`, below) but ships no HTTP client and holds no credential. Downloading the artifact needs an authenticated token, which would be a new credential and needs approval. Nothing here fetches from GitHub's API.
4. **Wire the live city.** The live city does not implement this rule; adopting it means changing and republishing the artifact.
