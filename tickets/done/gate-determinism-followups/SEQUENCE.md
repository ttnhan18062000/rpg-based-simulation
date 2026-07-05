# Gate Determinism Follow-ups — Implementation Sequence

Four tickets filed 2026-07-05, implementing `docs/plans/agent_infrastructure/idea_agent_gate_determinism.md`
(unscheduled idea, raised 2026-07-03 from the agent infrastructure audit's lowest-scoring category,
"Determinism of judged gates," 6.5/10) in full — the user explicitly chose "all 4 gates now" over a
narrower done-checker-only first ticket. Each ticket gives one existing LLM-judged gate agent a
companion deterministic pre-check that runs before the LLM verdict, per the idea doc's own design.

| Order | Ticket | Why this order |
|---|---|---|
| 1 | TCK-20260705-GATE-DET-DONE-CHECKER | Simplest checks (file-existence/emptiness), matches the user's own flagged pain point, lowest implementation risk |
| 2 | TCK-20260705-GATE-DET-PARITY-UPDATER | Moderate complexity (git-diff cross-reference against a src/-path→subsystem-YAML mapping) |
| 3 | TCK-20260705-GATE-DET-MECHANICS-AUDITOR | Conceptually adjacent to parity-updater (both read `docs/parity_ledger/`), but independent code path — do after Parity's mapping exists to reuse it rather than deriving a second one |
| 4 | TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER | Hardest (real Python AST parsing for durable-state-mutation detection, not just file/path checks) — do last |

## Shared Design Decisions (resolved here, not re-litigated per ticket)

These four tickets share a common architecture. Each child ticket's own Investigate/Plan phase should
adopt these as decided inputs unless it finds concrete evidence to the contrary — flag any disagreement
explicitly rather than silently diverging.

1. **Module location**: a new `tools/gate_checks/` subpackage, one module per gate
   (`tools/gate_checks/done_checker_static.py`, `parity_updater_static.py`, `mechanics_auditor_static.py`,
   `architecture_reviewer_static.py`). **Not** folded into the existing `lane-architecture` Makefile
   target/pytest marker — confirmed by reading `Makefile:185` that `lane-architecture` runs
   `pytest tests/ -m "architecture"`, a simulation-code (`src/`) architecture-guard lane, a different
   domain from agent-workflow-hygiene checks. Mirrors this session's established
   `tools/registry_query.py`/`tools/parity_ledger_scan.py` pattern (pure functions, no CLI/`argparse`,
   consumed via `python3 -c "..."` from the relevant workflow file or agent prompt).
2. **Failure vocabulary**: a static verifier's `FAIL` result downgrades to the *same* existing
   status the LLM verdict already produces for that gate (`NEEDS_CHANGES`/`BLOCKED` for
   architecture-reviewer, `DOD_BLOCKED` for done-checker, etc.) — no new status strings. One failure
   vocabulary, not two, per the idea doc's own Open Questions.
3. **Verdict provenance**: each gate's return schema gains a `verified_by` array field (e.g.
   `verified_by: ["static:no_raw_domain_return", "llm"]`), so a `PASS` that came from a human-legible
   static rule is distinguishable from one that came only from LLM judgment.
4. **Coverage honesty**: each ticket's own test suite must include at least one test asserting the
   static module actually catches what it claims to catch (a fixture-based positive control), not just
   that it runs without error — per the idea doc's Open Questions ("is there a test asserting 1:1
   coverage between what this doc claims is checked and what's actually implemented").
5. **Token/cost telemetry does NOT ride along.** The idea doc itself frames this as "a separate,
   smaller idea" — do not bundle it into any of these 4 tickets.

## Correction to the Idea Doc's Own `done-checker` Framing (important — read before starting Ticket 1)

The idea doc's table lists `staging_artifacts/{id}/ has all three files, data/runs/ and
reports/release_proof/ are empty` as `done-checker` checks — but `done-checker` runs during the
**Verify** phase, which happens *before* Finalize in the 9-phase pipeline. `done-checker` structurally
cannot verify that `staging_artifacts/` was migrated to `stored_artifacts/`, because that migration is a
Finalize-phase action that hasn't happened yet at the point `done-checker` runs. Ticket 1
(`GATE-DET-DONE-CHECKER`) must split this correctly:
- The genuinely pre-Finalize, `done-checker`-appropriate checks (staging artifacts *exist* with all 3
  files, `data/runs`/`reports/release_proof` are empty, ticket file is in `tickets/inprogress/`,
  `working_log.csv` does *not yet* have this ticket's row) stay as `done-checker`'s own static
  pre-check.
- The **staging→stored migration verification** (did Finalize's own move actually happen: does
  `stored_artifacts/{id}/` now exist with all 3 files, does `staging_artifacts/{id}/` no longer exist)
  must be a **new, separate check added to Finalize's own end-of-phase self-verification** — Finalize
  checking its own work immediately after doing it — not something `done-checker` can gate on.
- Additionally, per this session's own `validate.py` precedent (which retrospectively audits
  `runs.jsonl`/`events.jsonl`/`working_log.csv` for historical gaps), consider a small retrospective
  audit addition scanning all of `tickets/done/*.md` for orphaned `staging_artifacts/{id}/` directories
  that were never migrated — catching *historical* drift, not just preventing new instances. This is a
  genuine, valuable refinement the user's own framing pointed at; Ticket 1's Investigate phase should
  size this precisely (how many historical orphans actually exist today) before committing to build it.

## Dependency Notes

- No hard code dependency between the 4 tickets — each targets a different agent/gate and a different
  static-check module. Order above is a complexity/priority ordering, not a blocking dependency.
- Ticket 3 (mechanics-auditor) should reuse Ticket 2's (parity-updater) `src/`-path → subsystem-YAML
  mapping if one gets built, rather than deriving a second, possibly-inconsistent mapping — check
  Ticket 2's `stored_artifacts/` for a reusable module/function before building a new one.
- All 4 update the same 3 docs this session has repeatedly touched (`docs/ai/workflows.md`,
  `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md`) plus `docs/ai/agents.md` (each gate
  agent's own section gains a note about its new static pre-check) — if multiple land in the same
  session, reconcile these doc updates together rather than each ticket re-deriving current state
  independently.
