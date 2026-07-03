---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-DUAL-GATE-AUDIT
phase: open
date: 2026-07-03
tags: [simulation_quality, economy, social, investigation, worldbuilding]
---

# TCK-20260703-SIMQ-UPLIFT3-DUAL-GATE-AUDIT

## Title
Investigate whether ECONOMY (and any other still-C pillar) shares the "compiler never seeds the field" bug class found for FACTION and INFORMATION

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Two independent SimQ Uplift Batch 2 tickets (`TCK-20260702-SIMQ-UPLIFT2-FACTION`,
`TCK-20260702-SIMQ-UPLIFT2-INFORMATION`) each found the same root-cause pattern behind a
pillar stuck at C across all 30 calibration runs: the original diagnosis assumed a "structural
gap, needs feature-flag or content work," but the actual bug was that `WorldCompiler.compile()`
never constructed the relevant `AuthoritativeState` field at all — not a content gap, not a
feature-flag gap, a straightforward compiler omission. Given this pattern hit 2-for-2 so far, it
is worth checking whether ECONOMY (still C in 25/30 runs per `docs/audits/D20_simq_integration.md`)
or SOCIAL's non-`urban_political` C grades (23/30, flag-gated by `ENABLE_SOCIAL_COOPERATION`,
already understood as a flag issue not a compiler issue) hide the same class of bug, before
assuming ECONOMY's C ceiling is "just" a duration/content issue (per
`docs/plans/audit_fix_plan.md`'s "Finding 1: Systemic C ceiling ... 100% attributable to ... 27
engine emission gaps").

This ticket is investigation-only. If it finds a matching bug, the fix itself becomes a new
ticket following the pattern documented in `TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC`. If it finds
nothing (ECONOMY's C ceiling really is duration/content, as the existing audit trail already
claims), the value is confirming that with fresh eyes rather than assuming the pre-existing
"structural gap" diagnosis is still correct — exactly the kind of assumption that was wrong twice
already this batch.

## Scope
1. Read `docs/simulation_quality/quality_scoring_contract.md`'s ECONOMY section and
   `src/simulation_quality/scorers/economy.py` to enumerate ECONOMY's actual scoring conditions
   and the `AuthoritativeState` fields they read.
2. For each field ECONOMY's scorer reads (e.g. trade ledgers, shop transaction records, resource
   conservation counters, Gini coefficient inputs), grep `WorldCompiler.compile()`'s single
   `AuthoritativeState(...)` constructor call to confirm whether that field is actually
   constructed/passed, or silently defaults to empty/zero for every world — the exact check that
   found the FACTION and INFORMATION bugs.
3. If a matching gap is found, do NOT fix it in this ticket — write up the finding with the same
   rigor as the FACTION/INFORMATION investigations (file:line evidence, confirm no existing
   catalog/collision hazard) and recommend a follow-up ticket using
   `TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC`'s pattern.
4. If no matching gap is found, document why ECONOMY's C ceiling is confirmed to be genuinely
   duration/content-driven (not a compiler bug) with the same level of evidence, so this question
   doesn't need re-asking next batch.
5. Time-box: this is investigation-only, not a full engine audit — 1-2 days of investigation
   effort, not an open-ended search.

## Out of Scope
- Implementing any fix found (spin out a new ticket instead)
- Auditing COGNITION/AGENCY/PROGRESSION/WORLD/NARRATIVE/COMBAT (these already have confirmed,
  understood root causes per `docs/audits/D20_simq_integration.md` and are not "still C for
  unexplained reasons")
- Re-auditing SOCIAL's `urban_political`-only activation (already understood as a feature-flag
  gate, `ENABLE_SOCIAL_COOPERATION`, not a compiler-seeding bug — confirmed different root cause
  class than FACTION/INFORMATION)

## Acceptance Criteria
- [ ] ECONOMY's scorer-read `AuthoritativeState` fields enumerated with file:line references
- [ ] Each field checked against `WorldCompiler.compile()`'s constructor call for actual
      construction (not silent default)
- [ ] A clear verdict per field: "compiler-seeded correctly" or "silently defaults, matches the
      FACTION/INFORMATION bug class" — no ambiguous findings
- [ ] If a bug is found: a recommended follow-up ticket scope is written (not implemented)
- [ ] If no bug is found: the existing "structural gap" diagnosis in `docs/audits/D20_simq_integration.md`
      and `docs/plans/audit_fix_plan.md` is explicitly reconfirmed with this investigation's evidence,
      not just left as an old, unverified claim

## Related Tickets
- TCK-20260702-SIMQ-UPLIFT2-FACTION (done) — first instance of this bug class
- TCK-20260702-SIMQ-UPLIFT2-INFORMATION (done) — second instance of this bug class
- TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC — pattern doc to apply if a matching bug is found

## Related Docs
- `docs/audits/D20_simq_integration.md` §SimQ Uplift Batch 2 grade distribution table (ECONOMY
  status)
- `docs/plans/audit_fix_plan.md` §SimQ Re-evaluation, Finding 1 (the claim to re-verify)
- `docs/simulation_quality/quality_scoring_contract.md` — ECONOMY scoring conditions
- `docs/simulation_quality/event_type_coverage.md` — ECONOMY-related event calibration_hits

## Related Stored Artifacts
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-FACTION/investigation.md` — methodology template
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-INFORMATION/investigation.md` — methodology template

## Related Code Areas
- `src/simulation_quality/scorers/economy.py`
- `src/worldbuilding/compiler.py::WorldCompiler.compile()` — the single `AuthoritativeState(...)`
  constructor call to check against
- `src/core/state.py` — `AuthoritativeState` field definitions relevant to ECONOMY

## Assumptions / Open Questions
- UQ-1: Is ECONOMY's C ceiling actually one root cause, or several independent ones (e.g. trade
  ledger seeding vs. shop transaction wiring vs. Gini-input population)? The investigation should
  not assume a single unified fix if evidence points to multiple independent gaps.

## Implementation Notes
(to be filled during investigation)

## Test Summary
(to be filled during investigation — likely N/A if no code changes result)

## Files Changed
(to be filled during investigation — likely just investigation.md/docs updates)

## Completion Summary
(to be filled on done)
