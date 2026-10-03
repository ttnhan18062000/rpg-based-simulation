---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES
phase: done
date: 2026-09-06
tags: [simulation-quality, content]
---

# TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES

## Title
M7 step 1-3: name pillars for all 65 ideas, inventory real event types, author missing SimQ signal rules

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
M7 epic (`TCK-20260823-EPIC-RPG-M7-SIMQ-INTEGRATION`) child 1 of 2. Implements the epic doc's Scope
items 1-3: expand the Merit Scorecard's Pillar Reach axis from a count (e.g. "5/10") into named
pillars per idea; for each shipped idea (M1-M6, all confirmed DONE), confirm its real event types
exist and are named; and author a signal rule (following the exact shape already used by the 10
pillars' existing rules in `docs/simulation_quality/quality_scoring_contract.md` §5) for every named
event type that doesn't already have one.

**Confirmed real, not assumed, before this ticket's own Investigate phase re-confirms at
implementation time:**
- The 10 real pillars are: COGNITION, AGENCY & ACTION, COMBAT, FACTION & MILITARY, ECONOMY,
  PROGRESSION, SOCIAL, INFORMATION & BELIEF, WORLD DYNAMICS, NARRATIVE
  (`docs/simulation_quality/quality_scoring_contract.md` §5).
- **A real, concrete complication, not a hypothetical**: at least 3 of the 65 ideas are disclosed as
  "built, not yet visible in play" — idea 57 (`FameDeriver`/`LegendFact`, zero live Perception/
  Motivation pipeline call sites), idea 62 (`FidelityDeriver`, no live consumer), idea 56
  (`LoyaltyDriftService`, the one live per-tick call site never passes its signal). This ticket's own
  event-type inventory (Scope item 2) must check each of these 3 for whether they actually emit any
  real, observable event today — if none do, that is not this ticket's bug to fix, but it must be
  recorded as an explicit "no live event type yet" disposition, not silently mapped to a pillar it
  can't actually signal for, and not silently dropped from the list either.

## Scope
- For all 65 ideas (`docs/brainstorm/design_merit_scorecard.html`'s Pillar Reach axis), name the
  specific pillar(s) each should register with, replacing the current count-only representation.
- For each shipped idea (M1-M6), confirm its real event type(s) exist in code and are named — a
  direct read of what got built, not a redesign.
- Cross-check every named event type against `quality_scoring_contract.md` §5's existing per-pillar
  signal tables. For each event type with no existing rule, author one (a signal, a delta, a tag)
  following the exact existing pattern.
- Explicitly disposition the 3 flagged dormant ideas (57, 62, 56) per the Request Summary above.

## Out of Scope
- Re-running SimQ's calibration workflow or the final completeness cross-check —
  `TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS`, sequenced after this ticket.
- Building any new mechanism to make the 3 dormant ideas' event types live — that is each idea's own
  future follow-up ticket, not this one.
- Designing a signal rule for any event type that doesn't actually exist in shipped code.

## Acceptance Criteria
- [x] All 65 ideas have a named-pillar mapping recorded (not just a count).
- [x] Every real event type introduced by M1-M6 either has a traceable SimQ signal rule, or an
      explicit, written reason it's intentionally excluded (including the 3 flagged dormant ideas).
- [x] New signal rules follow the exact existing shape/pattern in `quality_scoring_contract.md` §5 —
      no new rule-authoring convention invented.
- [x] `docs/simulation_quality/quality_scoring_contract.md` and/or
      `docs/brainstorm/design_merit_scorecard.html` updated to reflect the named-pillar mapping.

## Related Tickets
- `TCK-20260823-EPIC-RPG-M7-SIMQ-INTEGRATION` (parent epic)
- `TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS` (sequenced after this ticket)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m7_simq_pillar_integration_epic.md`
- `docs/simulation_quality/quality_scoring_contract.md`
- `docs/brainstorm/design_merit_scorecard.html`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/simulation_quality/` (`scorers/`, `pillar_accumulator.py`, `quality_report.py`)
- `src/domains/fame/`, `src/domains/fidelity/`, `src/systems/social_systems/loyalty_drift.py`

## Assumptions / Open Questions
- Whether a dormant idea with no live event type gets its own placeholder rule (inert until the
  event exists) or a pure documentation exclusion is left to this ticket's own Investigate/Plan
  phases — not decided here.

## Implementation Notes
Named all 65 ideas' Pillar Reach cells in `design_merit_scorecard.html` with the specific pillars
they touch (short IDs matching `quality_scoring_contract.md`'s own Pillar Metadata table), replacing
the bare count — grounded in first-hand mechanism knowledge for the ~45 M2-M6 ideas this session
directly implemented, title/take-column-based for the ~20 M1 ideas (disclosed lower-confidence
tier). Applied via a scripted, verified regex substitution targeting only the 4th `<td
class="score">` per idea row — confirmed via `html.parser` parse-clean check and a `git diff --stat`
scope check (58 cell edits, matching the 58 non-zero-pillar ideas; the 7 zero-pillar ideas — 8, 9,
15, 16, 17, 18, 19 — correctly stayed unchanged at `0/10`).

Real, corrected finding for the event-type inventory (Scope item 2-3): cross-referencing the real 90
`event_type=` literals in `event_extractor.py` against `quality_scoring_contract.md` §5 found 15
apparently-undocumented event types. Checking each against the pre-existing, authoritative
`docs/simulation_quality/event_type_coverage.md` (not assumed clean) found 14 of the 15 already
fully dispositioned there with a real, evidence-grounded reason — the actual gap was that §5 didn't
cross-reference that doc, not that 14 new rules needed writing. Fixed by adding one cross-reference
note to §5, not 14 duplicated rules. The 15th, `route_new_query`, was a genuine gap missed even by
that authoritative doc since `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE` first emitted it —
real, live-emitted, unscored. Added as `InformationScorer`'s 8th event type (`information_seeking_
active` signal), following the exact shape of its 7 sibling event-type branches.

The 3 flagged dormant ideas (56/57/62) were confirmed via direct grep to emit no
`SimulationEvent`/`ObservabilityEventEnvelope` of any kind at all — a structurally different, more
fundamental gap than the 15 above (those are real-but-unscored engine events; these 3 have no event
to wire in the first place, since `FameDeriver`/`FidelityDeriver`/`LoyaltyDriftService` all operate
outside the per-tick event-extraction machinery entirely). Dispositioned as "no live event type
exists yet, tracked as a known gap" — each still received a real named-pillar mapping (forward-
looking, per the axis's own question text), not silently dropped.

## Test Summary
`tests/simulation_quality/` (full suite): 478 passed, 85 skipped, 0 failed — includes 2 new tests
(`TestRouteNewQuery`) confirming the new `InformationScorer` branch and its `EVENT_TYPES` membership,
plus all pre-existing tests confirmed unmodified in behavior.

## Files Changed
- `docs/brainstorm/design_merit_scorecard.html` (65 Pillar Reach cells + 1 axis-description note)
- `docs/simulation_quality/quality_scoring_contract.md` (§5 coverage note + INFORMATION & BELIEF
  section: new event type, signal row, real-producer note)
- `docs/simulation_quality/event_type_coverage.md` (new §1.1 row, Summary count 84→85, changelog
  entry, `last_verified` bumped)
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-245` amended — `InformationScorer`'s rule list was
  a real, tracked entry that went stale once an 8th rule was added; found during Parity phase, not
  assumed clean)
- `src/simulation_quality/scorers/information.py` (`route_new_query` added to `EVENT_TYPES` + a new
  `score()` branch)
- `config/simulation_quality/scoring_weights.yaml` (`information_seeking_active: 10.0` under
  `INFORMATION`)
- `tests/simulation_quality/test_information_scorer.py` (`TestRouteNewQuery`, 2 new tests)

## Completion Summary
Named all 65 ideas' SimQ Pillar Reach with specific pillars (not just a count), confirmed the real
M1-M6 event-type inventory against ground-truth code, and closed the one genuine unscored gap found
(`route_new_query`) with a real signal rule following the exact existing pattern. A significant real
finding narrowed this ticket's own scope for the better: 14 of 15 apparent event-type gaps were
already fully dispositioned in a pre-existing authoritative doc (`event_type_coverage.md`) that
`quality_scoring_contract.md` simply didn't cross-reference — fixed with one note instead of 14
redundant rules, avoiding a fork of the single source of truth. The 3 flagged dormant ideas (56/57/
62) were confirmed to have no event of any kind (a more fundamental gap than "unscored"), honestly
dispositioned rather than papered over. SimQ itself has zero gameplay/Mechanics-Bible effect, but a
real, pre-existing parity entry (`INFRA-245`, tracking `InformationScorer`'s full rule list by name)
went stale once the 8th rule was added — caught during Parity phase, not assumed clean, and amended
via the sanctioned `tools/parity_ledger_writer.py`.
