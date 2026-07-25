# Phase 5 Bounded-Pilot Authorization

- Date: 2026-07-25
- Prerequisite gate: Gate 4 recorded `PASSED` in `docs/phase-state.md`
- Authorized target: the pinned, user-controlled PwnzzAI Option 2 lab at
  `http://127.0.0.1:18080` with local Ollama
- Authorization source: the user's 2026-07-25 instruction to complete Phase 5
  after Gate 4 and run only the explicitly approved small pilot
- Authorization scope: Phase 5 bounded adversarial pilot only
- Phase 6/full-run authorization: not granted

## Approved pilot ceiling

- Nine selected catalog cases, including one offline detector positive control
- At most 17 target HTTP requests
- One prompt repetition per selected prompt case
- One RAG refresh from the unchanged clean corpus
- Poison budgets `0` and targeted `1` only
- Four-item frozen clean holdout
- One request per second maximum and one concurrent request
- At most 65,536 bytes per QR upload
- Zero automatic retries
- 1,200 seconds maximum wall-clock time
- Three consecutive infrastructure errors stop the affected surface

## Data and safety boundary

Only declared synthetic canaries, application-generated simulated customer
patterns, benign pizza text, and synthetic sentiment samples are authorized.
The pilot excludes public or third-party targets, cloud-model requests, real
personal data or credentials, host compromise, command execution, denial of
service, direct database manipulation as an attack path, destructive reset,
external evidence upload, and all unselected full-protocol cases.

The frozen scope is recorded in
`configs/phase-05-pilot-protocol.v1.0.0.json`. Any broader request count,
poison budget, target, model, detector threshold, or case selection requires a
new authorization decision.
