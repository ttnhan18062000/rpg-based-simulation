---
name: simq-dev
description: 'Development/debugging side of simulation_quality scorers — adding pillars, adding scoring rules, debugging a wrong score.'
---

# SimQ Development (This Repo)

Covers the development/debugging side of `src/simulation_quality/` — adding scorers, adding
scoring rules, and understanding why a pillar's score came out wrong. Sourced from
`docs/simulation_quality/quality_scoring_contract.md`.

**Not this skill**: the recalibration/drift-classification/grade-anchor audit workflow — that's
the `simq-audit` skill (`.claude/workflows/simq-audit.js`). This skill and `simq-audit` cover
different phases of the same subsystem's lifecycle and do not duplicate each other.

## Core Data Model

Source: `quality_scoring_contract.md` §4.1-4.3.

- **`ScoreRecord`** — the atomic, immutable, typed scoring unit: `tick`, `event_id`, `pillar`,
  `delta` (positive = healthy, negative = degenerate), `reason` (traceability only, not stored
  state), `event_type`, `entity_id`, `region_id`, `tags`.
- **`ScoringContext`** — read-only, passed to every `scorer.score()` call. Scorers must not
  mutate it. Exposes `current_tick` (for time-gated penalties), `pillar_scores`,
  `pillar_event_counts`, `window_tag_counts`.
- **`PillarAccumulator`** state (per pillar, maintained by `QualityHub`): `raw_score`,
  `event_count`, `negative_count`, `last_event_tick`, `worst_events` (top N by `abs(delta)`,
  negative only), `window_buffer` (sliding, `maxlen=200`), `loop_flags`.

## Adding a New Pillar

Source: §7.1's real 9-step protocol:

1. Add `NEW_PILLAR_ID` to the `PillarId` enum in `pillars.py`.
2. Add a metadata entry to `PILLAR_METADATA`: name, description, phase anchors, D01 reference.
3. Add a section for the new pillar in `config/simulation_quality/scoring_weights.yaml` with all
   rule keys and initial delta values.
4. Add the pillar's default weight (1.0) to `config/simulation_quality/profiles/default.yaml`.
5. Create `src/simulation_quality/scorers/new_pillar.py` extending `PillarScorer`.
6. Implement `score(envelope, context) -> ScoreRecord | None` using `self.weights["rule_key"]` —
   **no numeric literals in scorer code**, ever.
7. Register in `QualityHub.SCORER_REGISTRY`: `{event_type: [NewPillarScorer(weights)]}`.
8. Add at least one scenario to the Scenario Registry (§6) for each new usage question.
9. Add unit tests for every scoring rule (inject a `ScoringWeights` fixture, not production
   config values).

**Do not** register the same `event_type` in the new pillar and an existing pillar with the same
delta sign for the same condition — check §6's Scenario Registry for overlap first.

## Adding a Scoring Rule to an Existing Pillar

Source: §7.2:

1. Check §6: does the scenario already exist? Is there already a rule for it in this pillar?
2. If no conflict: add the rule's delta key + default value to `scoring_weights.yaml` under the
   relevant pillar section, then add the conditional logic to the scorer using
   `self.weights["new_rule_key"]` — resolves to *this scorer's own pillar's* declared value via
   the `PILLAR_ID`-bound `PillarWeightsView`, not a shared cross-pillar namespace, even if the
   same key string is also declared in another pillar's section.
3. Add the tag to the pillar's tag documentation in §5.
4. If the scenario is new, add a row to §6.
5. Add a unit test (inject a `ScoringWeights` fixture).
6. If a new `event_type` is involved, add it to the pillar's "Event types scored" list in §5.

## Conflict Detection Rules

Source: §7.3 — before adding any scoring rule, verify:
- **No dual-ownership**: the `event_type` isn't already scored in another pillar for the same
  scenario condition.
- **No duplicate signals**: the tag doesn't already exist in another pillar.
- **Scenario mapping**: the rule traces to exactly one primary scenario in §6.
- **Delta polarity consistency**: if `event_type` X scores +N in Pillar A, it must not score −N in
  Pillar B for the same condition.

One legitimate exception: an event can score in two pillars if it maps to two scenarios with
different primary pillars (e.g. `paid_info_transaction` scores +3 in INFORMATION for SQ-16,
documentary-only secondary in ECONOMY). `ScoringWeights.for_pillar()` (§4.8) is what makes each
pillar read its *own* declared delta for a shared rule key, fixed by
`TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`.

**Real, disclosed, unresolved divergence** (not hidden): `EconomyScorer`'s own
`paid_info_transaction` handling returns a real, live-scored `ScoreRecord` added to ECONOMY's
`raw_score` — not the "documentary only" non-contribution the design describes. Flagged as a
candidate follow-up in that same ticket's Implementation Notes, not yet fixed. If you're debugging
an unexpectedly-high ECONOMY score, this is a real, known place to check.

## Debugging a Wrong Score

1. Identify which pillar produced the unexpected score, then read that pillar's real scorer test
   file first: `tests/simulation_quality/test_cognition_scorer.py`,
   `test_economy_scorer.py`, `test_progression_scorer.py`, `test_narrative_scorer.py` (pattern
   generalizes to every pillar — check `tests/simulation_quality/` for the matching name).
2. If the issue looks like a weight-lookup problem (a pillar reading the wrong delta value for a
   shared rule key), read `tests/simulation_quality/test_scorer_pillar_binding.py` — the exact
   regression test for the primary/secondary pillar-scoped weight lookup mechanism.
3. `tests/simulation_quality/test_quality_hub_integration.py` for end-to-end
   event-to-score-record flow issues.
4. `tests/simulation_quality/test_kernel_simq_integration.py` if the issue is specifically about
   how SimQ receives events from the kernel tick loop, not the scoring logic itself.

## Related

- `simq-audit` skill — the audit/governance workflow (recalibration, drift classification, grade
  anchors) this skill deliberately does not cover.
- `TCK-20260628-SIMQ-EPIC` — built this subsystem originally.
