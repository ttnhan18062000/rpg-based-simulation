---
status: active
layer: simulation
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS
date: 2026-09-06
---

# Plan: TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS

## Steps
1. Run 2 real calibration attempts against `urban_political_selfmodel_execution_probe` (seed
   42/500t, seed 137/300t) to confirm whether `route_new_query` fires in the current corpus.
   (Done in Investigate — result: 0 occurrences in both.)
2. Build a deterministic before/after proof through the real `QualityHub`/`InformationScorer`
   (`route_new_query_isolated_calibration.py`) using the real, engine-captured envelope shape, to
   satisfy the "meaningful, non-flat grade signal" AC honestly given (1)'s real-corpus result.
3. Run the completeness cross-check (`completeness_check.py`) against ticket 1's own 65-row
   named-pillar mapping.
4. Record both results in `docs/simulation_quality/event_type_coverage.md` (calibration finding) and
   a new `quality_scoring_contract.md` §7.7 (completeness cross-check), following the §7.5/§7.6
   precedent format exactly — no new documentation convention invented.
5. Since no real, undisclosed gap was found, no fix and no follow-up ticket are filed (matches the
   ticket's own Acceptance Criteria: "no idea silently unaccounted for" — none are).
6. Close ticket 2, and since it's the last of 2 M7 child tickets, close the parent epic
   (`TCK-20260823-EPIC-RPG-M7-SIMQ-INTEGRATION`) and move `tickets/todos/m7-simq-pillar-integration/`
   to `tickets/done/m7-simq-pillar-integration/` in the same batch, per the M5/M6 precedent.

## Scope Guard
- No new signal rule, no new pillar mapping — ticket 1's own scope, not touched here beyond
  read-only verification.
- No fix to the "does not fire in shipped corpus" finding — that would mean authoring new content
  (a new calibration world/profile guaranteed to route Branch 3), out of this ticket's scope per its
  own Out-of-Scope ("this ticket verifies, it does not extend the rule set further").

## Acceptance-Criteria Map
| AC | Satisfied by |
|---|---|
| Real calibration run against >=1 corpus profile, results recorded | Step 1 — 2 real runs, both recorded in investigation.md and event_type_coverage.md |
| New rule produces a meaningful, non-flat grade signal | Step 2 — isolated proof: raw_score 0.0 -> 10.0, grade C -> S |
| Completeness cross-check recorded with explicit pass/gap list, all 65 ideas | Step 3-4 — 65/65 accounted for, 0 undisclosed gaps |
| Any real gap fixed or ticketed | No real gap found — explicitly stated, not silently omitted |

## Note: Internal Ticket-Text Tension, Resolved
The ticket's own Acceptance Criteria says a gap should be "fixed in this same ticket (if small) or
...ticketed (if not)", while its own Out-of-Scope says "this ticket verifies, it does not extend the
rule set further" (no in-ticket fixes at all). Moot here since no real gap was found either way, but
for the record: the Out-of-Scope text is the more specific, unambiguous statement and would govern
had a real gap existed — any real future gap should be ticketed separately, never patched in-line in
a calibration/verification ticket.
