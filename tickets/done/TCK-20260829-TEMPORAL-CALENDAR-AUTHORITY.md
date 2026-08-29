---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY
phase: done
date: 2026-08-29
tags: [temporal, determinism, world]
---

# TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY

## Title
Calendar Authority & Universal Duration Formula — Investigation and Decision Record

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

The temporal-axis brainstorm proposal (`docs/brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md`)
names, but does not resolve, four incompatible tick/calendar conventions live in the codebase today, plus a
lifecycle number (max age vs. elder threshold) that is already broken by 2-3 orders of magnitude under the
documented calendar. This ticket's own investigation (see `investigation.md`) confirmed and quantified those
findings with exact file:line citations and real numbers, and found that no per-action duration system exists
anywhere outside movement to generalize a universal duration formula from. The proposal's own §17 lists
"whether the existing tick remains the final minor time quantum" and related items as design-authority
decisions that must be settled before any M3+ balance ticket can be scoped — this ticket exists to carry that
decision to a documented, evidence-backed recommendation for the plan owner, not to implement it in code.

## Scope

- Confirm and document, with exact citations, every live tick/calendar convention currently in the codebase
  (already done in `investigation.md`: 36s/tick + 2,400 ticks/day per `docs/mechanics/05_world_evolution.md`;
  100 ticks/day in `src/world/raid.py`; a 200-tick cohort/ecology cycle in
  `src/domains/demographics/cohort.py`).
- Document the real, working movement-duration formula (`move_cost`/`readiness_speed`,
  `src/core/state.py`, `src/engine/legality.py`, `src/engine/apply.py`) as the only existing analog for a
  universal duration formula, and confirm no other subsystem (combat, crafting, harvesting) has any
  duration/cost concept to generalize from.
- Lay out the real decision options for calendar authority (which of the four conventions becomes canonical,
  or whether named sub-cadences like the cohort/ecology cycle stay intentionally separate from the "day") and
  for the universal duration formula's shape, with a recommendation for each, for the plan owner to accept or
  redirect.
- Recommend whether the unused `src/lab/metamorphic.py` balance-testing tool should be piloted before any
  numeric threshold from this decision is treated as tuned (mirrors the existing idea-37 metamorphic-pilot
  precedent already established in `rpg_design_roadmap.md`'s Sequencing rules).

## Out of Scope

- Implementing the resolution in code — no `src/` changes in this ticket. The output is a documented
  decision record (in `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`'s "Temporal axis" section, and/or
  a new `docs/mechanics/` entry once a chapter home for this exists) that a future M3+ ticket implements
  against.
- Finalizing exact numeric values for life-stage boundaries, pregnancy/education durations, or any other
  content-balance number — those remain the temporal-axis proposal's own §17 open items, gated behind this
  ticket's calendar-authority decision, not resolved by it.
- Re-litigating the plan-owner decisions already made and recorded in this session (Idea 66 promotion,
  Marriage/Reproduction decoupling, M6 single-contract, `CultureDeriver` ownership, permadeath ownership).

## Acceptance Criteria

- `investigation.md` records every live tick-convention citation and the movement-duration-formula finding
  with exact file:line references (done).
- `plan.md` lays out the concrete decision options (calendar authority, duration-formula shape, metamorphic
  pilot sequencing) with a recommendation for each.
- The plan owner has reviewed and either accepted, redirected, or explicitly deferred each recommendation
  before this ticket moves to `tickets/done/`.
- Once decided, the decision is recorded in `rpg_design_roadmap.md`'s "Temporal axis" section (or a new
  `docs/mechanics/` chapter, if the plan owner decides the decision belongs there instead) — not left only in
  this ticket.

## Related Tickets

- None yet — this is upstream of any M3+ ticket that would depend on a resolved calendar authority.

## Related Docs

- `docs/brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md` — §9 (Conflicts and required
  changes), §17 (Decisions still requiring review)
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — "Temporal axis" section
- `docs/mechanics/05_world_evolution.md` — the authoritative-but-contradicted 2,400-ticks/day convention

## Related Stored Artifacts

- `stored_artifacts/TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY/{investigation,plan,test_plan}.md`

## Related Code Areas

- `src/core/state.py` (`max_age_ticks`, `move_cost`, `readiness_speed` defaults)
- `src/engine/legality.py`, `src/engine/apply.py` (real movement-duration formula)
- `src/world/raid.py` (`TICKS_PER_DAY = 100`)
- `src/domains/demographics/cohort.py` (`get_age_bracket()`, `COHORT_INTERVAL`)
- `src/lab/metamorphic.py` (unused balance-testing tool)

## Assumptions / Open Questions

Resolved by plan-owner sign-off, 2026-08-29 (all four recommendations in `plan.md` accepted as written):

- **Which tick convention is canonical:** the World Evolution Bible's 2,400 ticks/day (36s/tick). Raid's
  100-tick alias and the cohort/ecology 200-tick interval are named sub-cadences, not rival calendars.
- **Universal duration formula shape:** generalizes movement's existing `move_cost`/`readiness_speed`
  readiness-cost pattern (`base_cost × modifier / rate`), not a new shape.
- **Authoritative home for the decision:** `rpg_design_roadmap.md`'s "Temporal axis" section — no new
  `docs/mechanics/` chapter needed for this decision record itself; `docs/mechanics/05_world_evolution.md`
  already states the 2,400-ticks/day authority this decision affirms, so a future implementation ticket only
  needs to fix its contradicted cross-references (raid.py, cohort.py), not add new Bible content.

Still genuinely open (not this ticket's scope, downstream of this decision): exact life-stage boundaries and
lifespan distribution, fantasy-calendar duration of pregnancy/recovery/education/apprenticeship,
modifier-stacking rules, and which processes qualify for safe interval advancement — all still flagged in
`rpg_design_roadmap.md`'s "Temporal axis" section under "Still open, per the proposal's own §17."

## Implementation Notes

No `src/` changes in this ticket by design — it is a decision record only. The actual migration (renaming
`src/world/raid.py`'s `TICKS_PER_DAY` constant, documenting `cohort.py`'s `COHORT_INTERVAL` as a named
sub-cadence, cross-reference cleanup in `docs/mechanics/05_world_evolution.md`, and building the universal
duration formula for combat/craft/harvest) is left for a dedicated future ticket, most likely landing inside
M3 once its own ticketing starts.

## Test Summary

No automated tests apply (no code changed). Verification performed:
- All four staging-artifact/ticket frontmatter files passed `tools/validate_frontmatter.py` with zero
  violations.
- `docs/REGISTRY.yaml` regenerated after this ticket and the roadmap edit; `tests/tools/test_generate_registry.py::TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry`
  passed (no drift).
- Every citation in `investigation.md` (file:line references) was pulled directly from the real, current
  repo state at investigation time, not inferred.
- Full `Tests` CI workflow green on the PR this ticket rides in (all jobs passed after an earlier,
  unrelated-to-this-ticket registry-drift fix on the same branch).

## Files Changed

- `tickets/inprogress/TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY.md` → `tickets/done/` (this file)
- `staging_artifacts/TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY/{investigation,plan,test_plan}.md` →
  `stored_artifacts/TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY/`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — "Temporal axis" and "Known open items" sections
  updated with the decision
- `registries/tag_registry.jsonl` — registered `temporal` (subsystem-topic)
- `docs/REGISTRY.yaml` — regenerated
- `tickets/working_log.csv` — closure entry appended

## Completion Summary

Investigated and quantified the temporal-axis proposal's flagged calendar-convention conflict with real
numbers (four incompatible tick conventions, not two; a 4.17-day maximum lifespan under the documented
calendar; movement as the only subsystem with a real duration formula). Presented four decisions as options
with recommendations; plan owner accepted all four recommendations as written on 2026-08-29. Decision
recorded in `rpg_design_roadmap.md`'s "Temporal axis" section as the authoritative home. No code changed —
implementing the migration is explicitly left to a future ticket.
