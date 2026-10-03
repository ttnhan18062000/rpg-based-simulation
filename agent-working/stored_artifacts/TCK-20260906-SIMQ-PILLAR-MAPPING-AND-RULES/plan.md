---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES
artifact_type: plan
tags: [simulation-quality, content]
---

# Plan — TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES

## Ordered Steps

1. **Named-pillar mapping for all 65 ideas** (`docs/brainstorm/design_merit_scorecard.html`) — replace
   each idea row's Pillar Reach cell (`N/10`) with the named pillar list plus corrected count
   (`PILLAR1, PILLAR2 (N/10)`), using the 10 short pillar IDs from `quality_scoring_contract.md`'s
   own Pillar Metadata table. Grounded in first-hand mechanism knowledge for the ~45 M2-M6 ideas
   this session directly implemented; title/take-column-based for the ~20 M1 ideas (disclosed
   lower-confidence tier in investigation.md). A single scripted, verified regex substitution
   targeting only the 4th `<td class="score">` per `<tr id="score-N">` block — never a full-file
   rewrite — with an `html.parser` parse-clean check and a `git diff --stat` scope check
   (58 cell edits + 1 axis-description sentence, matching the 58 non-zero-pillar ideas) before
   trusting it.
2. **Event-type inventory cross-check** — grep the real 90 `event_type=` literals in
   `src/observability/event_extractor.py` against every backtick term in
   `quality_scoring_contract.md` §5, then cross-check each apparent gap against
   `docs/simulation_quality/event_type_coverage.md` (the existing authoritative disposition audit)
   before assuming any gap is real.
3. **Author the one genuine new rule** (`route_new_query` → `InformationScorer`):
   - `src/simulation_quality/scorers/information.py`: add `"route_new_query"` to `EVENT_TYPES`;
     add a `score()` branch returning a `+information_seeking_active` signal.
   - `config/simulation_quality/scoring_weights.yaml`: add `information_seeking_active: 10.0` under
     `INFORMATION` (same tier as the sibling `belief_active` weight).
   - `tests/simulation_quality/test_information_scorer.py`: add `TestRouteNewQuery` (2 tests,
     mirroring the file's own existing per-event-type test-class convention).
   - `docs/simulation_quality/quality_scoring_contract.md` §5 INFORMATION & BELIEF: add
     `route_new_query` to "Event types scored" and a new signal-table row, plus a "Real producer"
     note.
   - `docs/simulation_quality/event_type_coverage.md`: add a new §1.1 row, bump the Summary's
     `scored` count 84→85, add a "Last updated" changelog entry (existing convention).
4. **Cross-reference the 14 already-dispositioned event types** — add one coverage note near the
   top of `quality_scoring_contract.md` §5 pointing at `event_type_coverage.md` §5 "Unscored
   Intentional" for the 14 real event types that already have a documented exclusion reason there,
   rather than duplicating or re-authoring 14 redundant rules.
5. **Test** — run the full `tests/simulation_quality/` suite; confirm the new test passes and no
   existing test's behavior changed.

## Files to Change

- `docs/brainstorm/design_merit_scorecard.html`
- `docs/simulation_quality/quality_scoring_contract.md`
- `docs/simulation_quality/event_type_coverage.md`
- `src/simulation_quality/scorers/information.py`
- `config/simulation_quality/scoring_weights.yaml`
- `tests/simulation_quality/test_information_scorer.py`

## Explicit Scope Guards (what NOT to touch)

- Do not author new signal rules for the 14 already-dispositioned `unscored_intentional` event
  types — cross-reference only, per investigation.md's finding that this would fork the single
  source of truth `event_type_coverage.md` already is.
- Do not add a *new* `docs/parity_ledger/` entry or claim a Mechanics Bible/gameplay-outcome
  impact — SimQ is explicitly out-of-band instrumentation. (Deviation: a real, pre-existing entry,
  `INFRA-245`, tracked `InformationScorer`'s rule list by name and went stale once an 8th rule was
  added — amended in place during Parity phase; see investigation.md's corrected Parity Ledger
  Overlap section and this file's own Deviations note below.)
- Do not re-run SimQ's calibration workflow or perform the final 65-idea completeness cross-check —
  both are `TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS`'s own scope, sequenced after this
  ticket.
- Do not force every idea's named-pillar count to match its pre-existing raw count when judgment
  disagrees — idea 9's own documented precedent in the same file permits correction.

## Dependency Map

Steps 2-4 (event-type work) are independent of step 1 (pillar naming) — no ordering dependency
between them. Step 5 (Test) depends on step 3's code change landing first.

## Acceptance Criteria → Steps

- AC #1 (all 65 ideas named) → Step 1.
- AC #2 (every M1-M6 event type has a rule or a written exclusion reason) → Steps 2-4.
- AC #3 (new rules follow the exact existing shape) → Step 3 (verified against
  `test_information_scorer.py`'s own existing per-event-type pattern and §5's own
  Signal/Delta/Tag table shape).
- AC #4 (contract doc and/or scorecard updated) → Steps 1, 3, 4 (all three touch
  `quality_scoring_contract.md` and/or the scorecard).

## Deviations

One real deviation from the original "no parity_ledger/ touch" assumption: Parity phase found
`INFRA-245` (`docs/parity_ledger/infrastructure.yaml`), a real, pre-existing entry naming
`InformationScorer`'s full rule list, had gone stale once `route_new_query`/
`information_seeking_active` was added as an 8th rule. Amended in place via
`tools/parity_ledger_writer.py::write_entry()` (never a raw YAML edit) rather than left silently
inaccurate. Everything else matched this plan exactly.
