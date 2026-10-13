# Reference truth core

A clean-room statement of the truth rules the PI City audit found missing,
written from the audit's findings, not from the city's source. It does not run
in the live city. It specifies the fix and proves it on the same inputs before
anything changes in the private artifact.

| File | Purpose |
|---|---|
| `truth-core.mjs` | Append-only, hash-chained evidence log; the judge; lease-guarded dispatcher |
| `import-rows.mjs` | Turns PI City's database row shapes into evidence-log events, so the reference judges exactly what the city judges |
| `reference.test.mjs` | The shared attack cases (`../truth-tests/cases.mjs`) plus reference-only checks R1–R7 |

## Rules

1. Evidence is append-only and hash-chained. There is no update or delete; a
   reset is an appended event.
2. A read-back is independent only if the executor and the verifier both have
   a recorded, canonical run identity and the two differ. Unknown, malformed or
   conflicting identities never count. Optional `distinct-path` policy also
   requires a different verification path (for example a GitHub Action).
3. A read-back must answer a verify request the mission issued, be no older
   than the execution, and match every requested fact.
4. The newest observation wins: a newer failed read-back demotes the outcome.
5. Permission counts only if the owner granted it for the exact scope.
6. Dispatch takes a lease and refuses while a request is still pending.

## Run

```
node --test reference/reference.test.mjs          # no snapshot needed (R7 skips)
city/tools/truth-ci.sh                            # both suites, with the pinned snapshot
```

## What this proves, and what it does not

**Reference proof:** these rules, applied to the same row fixtures as the city,
hold all 20 shared cases, including the 7 the city fails. Breaking any single
rule turns at least one test red; the mutation check is in the commit message
that added this directory.

**Not live proof:** nothing here changed or was run in the live city, database
or routines. The live city still has all 7 gaps. Case 1 also shows a limit
of the live data: the live `backend/reality-001` row never recorded who
executed the create, so under these rules it stays EXECUTOR-REPORTED until
that identity is recorded (case 1b adds it from the prior session's
transcript).
