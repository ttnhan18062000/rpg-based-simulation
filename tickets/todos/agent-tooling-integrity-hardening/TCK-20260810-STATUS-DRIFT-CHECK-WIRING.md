---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260810-STATUS-DRIFT-CHECK-WIRING
phase: open
date: 2026-08-10
tags: [ai, agent-monitoring, process-improvement, data-quality]
---

# TCK-20260810-STATUS-DRIFT-CHECK-WIRING

## Title
Wire `status_drift_check.py` into real enforcement/reporting and fix the 3 real current
`## Status` drift instances it already found

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`tools/ticket_field_values.py` hard-blocks `## Tier`/`## Priority` at ticket-close time
(`done_checker_static.py::run_static_precheck`), but `## Status`'s equivalent checker,
`tools/gate_checks/status_drift_check.py`, remains exactly what its own docstring says it is:
"ships unwired — no `Makefile` target, no `.claude/workflows/*.js` invocation... a future ticket
decides where/whether to call it." No such ticket existed before this one.

Running it live during a 2026-08-10 ticket-process audit found it is not merely theoretically
useful — it is catching **real, current** drift right now:

```
FAIL: TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER.md: ## Status reads 'OPEN', expected DONE
FAIL: TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE.md: ## Status reads 'OPEN', expected DONE
FAIL: TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC.md: ## Status reads 'OPEN', expected DONE
```

All 3 sit in `tickets/done/` with frontmatter already correctly showing they're closed, but the
ticket-body `## Status` heading was never updated — `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC`
closed only 4 days before this audit. The checker's own docstring documents the real, non-cosmetic
consequence: this exact drift class previously caused `dashboard-frontend/src/components/GanttBar.tsx`'s
`classifyFinalStatus()` (exact string match on `'DONE'`) to render genuinely-successful runs in the
neutral/gray bucket instead of green.

Two more flagged records — `TCK-20260806-PUSH-SHADOW-VALIDATION-PERF.md`,
`TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT.md` — are **not** real drift: their `## Status` line
legitimately reads `DONE` followed by real trailing prose (e.g. "DONE — GO verdict. Found and drove
the fix for 2 real bugs..."), which the checker's own documented, disclosed, exact-match limitation
flags as a false positive. Do not "fix" these by editing their real, accurate completion prose to
satisfy the checker.

## Scope
- **Investigate (mandatory before Plan):** confirm the 3 real drift cases and 2 false positives
  above still hold against current `tickets/done/` state (the corpus changes daily), and read
  `status_drift_check.py`'s full docstring (known limitations section) plus
  `tools/generate_registry.py::parse_body_section` (the shared extraction function it correctly
  reuses) before touching anything.
- Fix the 3 real drift instances: update each ticket's `## Status` body text to `DONE`, matching
  the pattern `implement-ticket.js`'s current Finalize phase already produces reliably for new
  tickets (per `status_drift_check.py`'s own docstring — this is a data-repair, not a new
  mechanism).
- Wire `status_drift_check.py` into a real path — decide (Plan phase) whether that's:
  (a) a new blocking condition in `done_checker_static.py::run_static_precheck`, mirroring
  `ticket_field_values.py`'s `## Tier`/`## Priority` precedent, or
  (b) a recurring `generate_retro.py`/Makefile-driven report-only check (lower blast radius, matches
  this module's own "ships unwired... future ticket decides" framing more literally).
  Either is acceptable; state the reasoning, matching this epic's evidence-driven-decision
  convention (see `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`'s per-skill gate-conversion
  precedent — not a blanket "wire everything to a hard gate" default).
- If wired as a blocking gate: confirm it does not retroactively block any of the 187
  pre-2026-07-04 legacy tickets `validate_frontmatter.py` already excludes on the same
  forward-only-enforcement principle (`docs/guidelines/tag_taxonomy.md`) — this checker has no such
  date exemption today; decide whether it needs one before going live as a blocking gate.
- Do not touch the 2 known false-positive records' real completion prose. If the exact-match
  limitation is itself worth loosening (e.g. prefix-match on `DONE`), that is a separate design
  decision to make explicitly, not a silent side effect of wiring.

## Out of Scope
- Rebuilding or modifying `status_drift_check.py`'s existing detection logic, its
  `parse_body_section` reuse, or its lowercase-`final_status` check in
  `agent-monitoring/runs.jsonl` (currently PASS, no known issue there).
- Revisiting the "6 files corpus-wide, same-line colon-suffixed `## Status: X`" exclusion —
  `TCK-20260718-STATUS-DRIFT-REPAIR`'s plan.md explicitly scoped that out and this ticket does not
  reopen it.
- A blanket sweep of all pre-2026-07-04 tickets for the same drift class — this ticket fixes the 3
  real current instances found; a corpus-wide legacy sweep (if warranted) is a separate,
  separately-scoped decision, matching `TCK-20260720-TAG-CORPUS-REPAIR-SWEEP`'s precedent of
  keeping legacy-debt sweeps report-only and separately ticketed.

## Acceptance Criteria
- [ ] `investigation.md` re-confirms the 3 real drift cases (or documents if the corpus has moved)
      with real, current `status_drift_check.py` output, not the numbers cited in this ticket.
- [ ] The 3 real drift instances have their `## Status` body text corrected to `DONE`.
- [ ] The 2 false-positive records are left untouched (verified by a diff check in Verify).
- [ ] `status_drift_check.py` is wired into a real, decided path (blocking gate or recurring
      report), with the choice justified in `plan.md`.
- [ ] If wired as a blocking gate: a forward-only-enforcement exemption question (per
      `tag_taxonomy.md`'s precedent) is explicitly answered, not left implicit.
- [ ] Scoped pytest run passes (`tests/tools/test_status_drift_check.py` plus any new tests for the
      wiring itself).

## Related Tickets
- TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC (parent)
- TCK-20260718-STATUS-DRIFT-REPAIR (DONE; original 71-file repair + built the checker)
- TCK-20260718-STATUS-MULTILINE-FIX (DONE; fixed the checker's own extraction to use
  `parse_body_section` instead of a first-token-only regex)
- TCK-20260718-STATUS-SUFFIX-TRIM (DONE; sibling drift-class fix, same investigation thread)
- TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM (DONE; built `ticket_field_values.py` and the
  hard-blocking precedent this ticket's gate-wiring option (a) would extend to `## Status`)
- TCK-20260718-STATUS-FACET-CANONICAL (DONE; the dashboard-facet canonical set `## Status`'s
  real-world consequence traces back to)
- TCK-20260720-TAG-CORPUS-REPAIR-SWEEP (DONE; precedent for keeping legacy-debt sweeps report-only
  and separately scoped, referenced by this ticket's Out of Scope)

## Related Docs
- `tools/gate_checks/status_drift_check.py`'s own docstring (known limitations, real consequence
  class, exclusion precedent)
- CLAUDE.md's Definition of Done section

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/gate_checks/status_drift_check.py`
- `tools/generate_registry.py` (`parse_body_section`, reused not reimplemented)
- `tools/gate_checks/done_checker_static.py`
- `tools/ticket_field_values.py` (precedent for the blocking-gate wiring option)
- `dashboard-frontend/src/components/GanttBar.tsx` (reference only — real downstream consumer)
- `tickets/done/TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER.md`,
  `tickets/done/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE.md`,
  `tickets/done/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC.md` (the 3 real drift fixes)

## Assumptions / Open Questions
- Whether wiring should be a hard gate vs. a recurring report is explicitly left to
  Investigate/Plan — the epic's own evidence-driven-decision convention applies here, not a
  default toward maximal enforcement.
- Whether a forward-only-enforcement date exemption is needed for a blocking-gate wiring choice —
  not assumed; Plan must decide with reasoning if option (a) is chosen.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
