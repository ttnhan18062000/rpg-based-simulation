---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE
phase: done
date: 2026-09-30
tags: [data-quality, process-improvement]
---

# TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE

## Title
Mechanism-registry absence verdicts made by code reading are wrong; re-verify them and require runtime evidence

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
rpg-implementer (2) reported this on 2026-09-30, from the unreachable-mechanism-classification
epic (see `docs/plans/unreachable_mechanism_classification.md`, follow-up F6, on that branch). Two
of two tickets that cited a `registries/mechanisms.yaml` verdict as their premise were false the
day they were filed:
- `camp`: `verdict: contradicted`, 2026-09-16, "no compiled or procedurally-generated world seeds
  state.camps". A real compile of `frontier_living_world` yields 2 `CampState`. The content that
  declares `creature_kind` landed 2026-09-08. Premise of
  `TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION`.
- `demographic_cohort_cycle`: `verdict: contradicted`, 2026-09-16, "no ... world seeds
  population_cohorts". 6 of 7 regions of the same compile have cohorts. The seeding shipped
  2026-08-31 in `TCK-20260831-POPULATION-COHORT-SEEDING`. rpg-feature-planning reproduced this
  independently. Premise of `TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED`.

**Design's root-cause correction to the reporter's suggestion.** The suggested rule was "re-check
when `verified.date` is older than the newest commit to `implemented_by`". It would **not** have
caught either case. Both contradicting changes (08-31, 09-08) **predate** the 09-16 verdict, and
neither lives in the entry's `implemented_by` (`CampState` and `DemographicCycleService`). The
verdicts weren't stale. They were wrong when written. Both carry `instrument: code_trace`, yet
both assert something about **runtime world data** ("no world seeds X"). Reading code can't prove
that data is absent. Only compiling or running a world can.

Registry scale on origin/main: 84 verified blocks, split 59 `code_trace` / 22 `scenario` / 3
`corpus_run`. **7 are `code_trace` + `contradicted`**, and 2 of those 7 are now known to be
false. The others haven't been checked.

## Scope
1. **Re-verify all 7 `code_trace` + `contradicted` entries** with a runtime instrument: a real
   compile of the shipped worlds (`scenario` or `corpus_run`). Update each entry's `verified`
   block to the real instrument, date and verdict. For `camp` and `demographic_cohort_cycle`,
   record the correction and the evidence. Update the dependent views/pages through their
   existing generators (`generate_mechanism_*`, the atlas/capabilities regenerate tools), never
   by hand.
2. **Registry rule:** a `contradicted` verdict that asserts world-data or runtime absence must use
   a runtime instrument. Enforce it where the registry schema/validators already live, e.g. a
   field on the verified block such as `claim: runtime_absence`, or a validator rule keyed on
   verdict + instrument. Choose the mechanism in plan.md. Make it a validator error for new
   entries. Don't grandfather existing entries, since Scope 1 fixes them all.
3. **Ticket-filing rule:** when a ticket quotes a registry verdict as its premise, the ticket
   must name the verdict's instrument and date. A `code_trace` absence verdict must be re-checked
   by a runtime run before it's quoted. Put this once in the ticket-scoper / create-tickets
   guidance (ticket-scoper.md's premise handling), and don't duplicate it elsewhere.
4. **Downstream tickets:** mark the two premise-false tickets above (and any others that quote
   the Scope 1 entries) with a dated premise-correction note. Close or re-scope them per their
   owners; that's RPG remit. Record the hand-off, and don't implement their fixes here.
   **Update 2026-09-30:** rpg-feature-planning is closing both premise-false tickets as STALE-PREMISE itself. Cite that closure (commit SHA pending) rather than re-annotating them. It left `registries/mechanisms.yaml` untouched on purpose, and this ticket owns the `camp` and `demographic_cohort_cycle` verdict corrections (epic F4 and F6 both).

## Out of Scope
- The RPG fixes those tickets proposed (world composition, cohort seeding). Seeding already
  works, per the report.
- `make premise-staleness-check`'s citation-resolution scope. It checks that citations resolve,
  not whether claims are true, and it stays that way. Mention the gap in its doc only if it's
  cheap.
- Re-verifying `observed` or `code_trace` + `observed` verdicts. That's a different error
  direction; file a follow-up if Scope 1 finds a pattern.

## Acceptance Criteria
1. All 7 `code_trace` + `contradicted` entries now carry a runtime instrument, a date of
   2026-09-30 or later, and a verdict backed by recorded evidence (compile output counts). `camp`
   and `demographic_cohort_cycle` no longer claim "no world seeds".
2. The validator rejects a new `contradicted` runtime-absence verdict whose instrument is
   `code_trace`. It's tested with a planted fixture, and the full real registry passes.
3. The ticket-filing guidance carries the rule exactly once.
4. Both premise-false tickets are closed STALE-PREMISE by rpg-feature-planning, and the closure SHA is cited here: `791e6bf6b` on `rpg-planning-post-258` (groundwork `f70f58706`).
5. All generated registry views pass `--check` after the update.

## Related Tickets
- TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION,
  TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED (premise-false; RPG-owned)
- TCK-20260831-POPULATION-COHORT-SEEDING (done; the seeding the verdict missed)
- TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION (done; produced the cohort verdict)
- TCK-20260915-MECHANISM-VERIFICATION-AXIS (done; introduced `verified`/instrument)
- TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION (done; the earlier precedent that a
  registry state class was unreliable)
- TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE (done; the premise-staleness
  tooling this doesn't replace)
- TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE (done; the date/commit-based
  advisory, which can't catch wrong-at-birth verdicts)

## Related Docs
- `docs/plans/unreachable_mechanism_classification.md` (F6; on branch
  `unreachable-mechanism-classification`, not yet on main)
- `docs/plans/world_composition_precondition_gap_finding.md` (cited by the `camp` verdict)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE/` (investigation.md, plan.md, test_plan.md, runtime_probe.py + output, compile_census.py + output)

## Related Code Areas
- `registries/mechanisms.yaml`
- `tools/mechanism_registry/registry.py` and the schema validator
- `tools/mechanism_registry/generate_mechanism_*.py`, `mechanism_atlas_regenerate.py`,
  `mechanism_capabilities_regenerate.py`
- `.claude/agents/ticket-scoper.md`

## Assumptions / Open Questions
- The 7-entry count comes from origin/main at 2026-09-30. Recount at Investigate.
- A world compile is enough runtime evidence for "seeded or not" claims. Claims about behavior
  over ticks may need `scenario`. Decide per entry.

## Implementation Notes
- **Scope 1:** counting probe over all 21 corpus worlds x 300 ticks (seed 42). All 7 entries now
  carry `corpus_run`/`2026-09-30`: 6 `observed`, 1 `contradicted` (`demographic_cohort_cycle`). The 2
  world-data claims (`camp`, `demographic_cohort_cycle`) had false premises; the 5 static
  call/construction claims were confirmed. `camp` is fully live (19 camps in 14/21 worlds, all
  changed state). `demographic_cohort_cycle` is seeded in 21/21 worlds but 0 birth/death events
  ever fire. Views regenerated through their generators; 1 capabilities-page tier (`camp`) moved
  `built` -> `live` via `make mechanism-capabilities-regenerate`. Details: investigation.md.
- **Scope 2:** validator invariant 12 (`contradicted` + static instrument is an error), keyed on
  verdict + instrument, because the registry header already defined `contradicted` as runtime-only.
  No `claim:` field. Make-target description updated.
- **Scope 3:** one new Mandatory Scan item in `.claude/agents/ticket-scoper.md`; once-only test.
- **Scope 4:** cites `791e6bf6b`; those tickets are not re-annotated.
- **Standing-rule follow-up check:** the "file a follow-up if a pattern shows in the observed
  direction" clause: Scope 1 found no such pattern (5/5 static claims confirmed), so nothing filed.
- **Probe correction:** the first run mis-tallied 30 `POPULATION_MIGRATION` events as births/deaths;
  rpg-feature-planning caught it and the probe now counts exact categories. The corrected data
  agrees with their `TCK-20260930-DEMOGRAPHIC-COHORT-NET-DELTA-TRUNCATES-TO-ZERO` (0 birth/death
  events, largest bracket 8).
- `mechanism-state-caller-check` still flags `chronicle` `orphan_with_callers` (pre-existing,
  report-only, state field untouched here).

## Test Summary
`tests/unit/tools` (the CI lane that failed on the first push): 426 passed after regenerating two more generated views and updating one verdict pin. 184 passed across the nine mechanism-registry unit-test files plus
`tests/tools/test_ticket_scoper_relevance_check.py` (incl. 5 new tests). `make
mechanism-registry-validate`, `mechanism-registry-html-check`, `mechanism-atlas-check`,
`mechanism-capabilities-check`, `mechanism-wiring-map-classdef-check` all OK after regeneration.

## Files Changed
- `registries/mechanisms.yaml` (7 verified blocks)
- `tools/mechanism_registry/registry.py`, `Makefile`
- `tests/unit/tools/test_mechanism_registry.py`, `tests/tools/test_ticket_scoper_relevance_check.py`
- `.claude/agents/ticket-scoper.md`
- `docs/brainstorm/mechanism_verification_view.md`, `mechanism_registry_view.md`,
  `mechanism_system_rollup_view.md`, `mechanism_registry.html`, `simulation_capabilities.html`
- `docs/brainstorm/cross_domain_management_view.md`, `docs/brainstorm/territory_control_management_view.md` (generated views that also embed verdicts; found stale by CI, regenerated via `make cross-domain-management-view` / `make territory-control-view`)
- `tests/unit/tools/test_terr_mapping_mechanism_state_stability.py` (pin for `betrayal_siege_war` updated to the new, deliberately evidenced `observed` verdict)
- `stored_artifacts/TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE/`

## Completion Summary
All 7 absence verdicts now rest on a runtime run; the validator rejects a static-instrument
`contradicted` verdict; the ticket scoper must name a quoted verdict's instrument and date.
