---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-TEST-PLAN-PROOF-FIELDS-AND-TRIAGE-PROCEDURE
artifact_type: investigation
tags: [testing]
---

# Investigation

## Current Behavior
`test_plan.md` records only level, regression surface, new tests and commands (`investigator.md`). No phase reviews test quality. Triage is split across `regression_policy.md` §4–7, `delivery_process.md` "CI Failure Triage" and CLAUDE.md gate integrity.

## Mechanics / Engine Constraints
None; process documents only. Roadmap principles 1, 5, 8 (behaviour source, no red-to-green by weakening, advisory first).

## Docs Requiring Update
- `docs/testing/regression_policy.md`: new §13 triage procedure and §6 pending pointer.
- `docs/guides/delivery_process.md`: CI triage step 3 links to §13.

## Parity Ledger Overlap
None.

## Coordination
agent-working-design confirmed (2026-09-30): investigator.md, architecture-reviewer.md and implement-epic.js prose are free; done_checker_static.py, done-checker.md and ticket-scoper.md belong to an unpushed batch (`retro-hardening-and-mechanism-verdict-evidence`) and are untouched.

## Triage Drill (Epic C criterion 3)
Classifying with `regression_policy.md` §13 only:

| Case | Evidence | Class | Routed to | Closure |
|---|---|---|---|---|
| Real: Epic A leak (`TCK-20260929-CATALOG-REGISTRY-TEST-LEAK`) — 7 progression tests fail after 8 catalog/registry test files, pass alone | Passes alone, fails combined; teardown probe showed 4 registries not reset | Order dependence / nondeterminism | test infrastructure (fix root cause in `tests/conftest.py`; no xfail) | combined, isolated and random-order runs pass |
| Synthetic: a corpus anchor test fails after a feature flag flips a subsystem on; the anchor file is 3 weeks old | Fails at one SHA reproducibly; a feature change touches the path; the spec (Bible) is unchanged | Product regression only if the Bible says the old value is right; otherwise Intentional spec change | feature team decides from the oracle document; the test author does not edit the anchor | Bible/ledger (and divergence entry) change first, or the code is fixed |
| Synthetic: a test fails only in one CI job, TLS error fetching logs | Fails in one environment only | Environment / fixture | CI / infrastructure | green in that environment |

The second synthetic row shows why the class column needs evidence: the same red test is one of two classes until the oracle document is consulted. Until then it stays Unknown.

## Risks and Open Questions
- The Proof Plan is advisory; whether it becomes required is the post-pilot decision (roadmap §6).
- Proof Plan enforcement is not in scope; raise with agent-working-design only if the pilot shows fields missing.
