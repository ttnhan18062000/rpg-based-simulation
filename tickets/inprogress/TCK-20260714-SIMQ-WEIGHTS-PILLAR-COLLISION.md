---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION
phase: open
date: 2026-07-14
tags: [simulation-quality, bug, calibration]
---

# TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION

## Title
`ScoringWeights` flattens all 10 pillars' `pillar_rules` into one pillar-unaware
`_flat_rules` dict, silently collapsing same-named rule keys across pillars to
whichever pillar is declared later in `scoring_weights.yaml`

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`src/simulation_quality/weights.py`'s `ScoringWeights._build_flat_index()` (lines 26-33)
iterates `self.pillar_rules.values()` in YAML declaration order and writes every
`(rule_key, weight)` pair into a single shared `_flat_rules: dict[str, float]`, with no
pillar-scoping. Any rule-key name reused across two or more pillar sections silently
collapses to whichever pillar is declared later in `config/simulation_quality/scoring_weights.yaml`
(YAML order: COGNITION → AGENCY → COMBAT → FACTION → ECONOMY → PROGRESSION → SOCIAL →
INFORMATION → WORLD → NARRATIVE — later entries overwrite earlier ones in the dict-build
loop). `__getitem__` (lines 91-98) then reads from this single collapsed dict, so a scorer
querying its own pillar's weight for a colliding key silently receives another pillar's
value instead.

Confirmed independently against the live `config/simulation_quality/scoring_weights.yaml`
(read in full during scoping): 7 colliding keys exist today —

| Key | Declared in | Value used elsewhere | Effective (winner) | Collision |
|---|---|---|---|---|
| `subjective_divergence` | COGNITION | `5.0` | INFORMATION `30.0` | INFORMATION wins, 6x amplification of every `decision_divergence_detected` event scored by `CognitionScorer` |
| `belief_active` | COGNITION | `2.0` | INFORMATION `10.0` | INFORMATION wins, 5x |
| `knowledge_rot` | COGNITION | `-3.0` | INFORMATION `-2.0` | INFORMATION wins |
| `omniscience_collapse` | COGNITION | `-20.0` | INFORMATION `-20.0` | identical value today — latent collision, will silently diverge the moment either side is retuned |
| `ecology_cycling` | ECONOMY `8.0` | — | WORLD `6.0` wins | WORLD overrides ECONOMY's SCORE-CEILING-FIX-recalibrated value |
| `ecology_broken` | ECONOMY `-25.0` | — | WORLD `-20.0` wins | WORLD overrides ECONOMY |
| `knowledge_economy_active` | ECONOMY `8.0` | — | INFORMATION `15.0` wins | INFORMATION overrides ECONOMY |

This is load-independent and always present — it affects every calibration/scoring run of
every scenario that touches any of these 7 keys, not just one scenario. It was discovered
during `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`'s investigation (in progress)
while explaining why an anomalous COGNITION-pillar run scored `raw_score=3521` instead of
an expected ~595-600 for the same `event_count=119`: 119 events × ~30.0 (INFORMATION's
`subjective_divergence`, silently applied instead of COGNITION's own `5.0`) ≈ 3570, which
fully explains the magnitude gap independent of any determinism/load issue. It was made
worse (not introduced) by `TCK-20260713-SIMQ-SCORE-CEILING-FIX` (done), whose per-pillar
×5 rescale raised INFORMATION's `subjective_divergence` from `6.0` to `30.0` without any
cross-pillar collision check — the collision mechanism itself (the shared `_flat_rules`
dict) predates that ticket and is not its fault.

## Scope
- Make `ScoringWeights` pillar-scoped: each pillar must read its own declared weight for a
  rule name, and must never silently receive another pillar's value for a reused name. The
  exact mechanism (e.g. namespacing `_flat_rules` keys by `(pillar, rule_key)`, building one
  flat index per pillar instead of one shared index, or another equivalent approach) is an
  implementation decision for the investigation/plan phase, not decided here.
- `__getitem__` (or its replacement call surface) must resolve unambiguously to the calling
  scorer's own pillar's weight for a given rule key.
- Audit call sites in `src/simulation_quality/scorers/*.py` that use `ScoringWeights.__getitem__`
  (or equivalent) to confirm each call site is updated consistently with whatever pillar-scoped
  mechanism is chosen.
- Preserve `ScoringWeights.load()`'s existing pydantic validation behavior (INFRA-234,
  `docs/parity_ledger/infrastructure.yaml`) — missing/malformed keys must still raise
  `ValidationError` at load time, not silently swallow.
- Identify (not necessarily fix in this ticket — see Assumptions) every anchor in
  `tests/simulation_quality/fixtures/grade_anchors.json` whose committed grade/score would
  change once the 7 known collisions are resolved to pillar-correct values.

## Out of Scope
- `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`'s own scope: the load-sensitive
  nondeterminism in COGNITION's self-model loop-detection path. That ticket's magnitude
  anomaly (raw_score=3521 vs expected ~595-600) is explained by this collision, but the
  separate question of *why that one live-mode sweep run produced `event_count=119` instead
  of the anchor's `event_count=2`* is that ticket's own root-cause question, not this one's.
  This ticket only fixes the weight-collapse mechanism; it does not investigate or fix
  event-count nondeterminism.
- Re-tuning or re-deriving the actual weight *values* in `scoring_weights.yaml` — this
  ticket fixes the lookup mechanism so each pillar's already-declared value is honored, it
  does not change what any pillar's intended weight should be.
- `TCK-20260713-SIMQ-SCORE-CEILING-FIX`'s per-pillar ×N rescale methodology or its other
  3 pillars' (WORLD, PROGRESSION, ECONOMY) rescale values — not reopened here.
- Any change to `src/engine/kernel.py`'s tick-budget watchdog/throttle — unrelated to this
  ticket's scope entirely.
- Full re-anchoring of every `grade_anchors.json` entry touching the 7 colliding keys.
  Whether that re-anchoring work happens inside this ticket or as its own dedicated
  follow-up ticket is an open question for the planner (see Assumptions / Open Questions) —
  but a full recalibration pass across the corpus is not assumed in-scope by default given
  the blast-radius warning in the request.

## Acceptance Criteria
- [ ] `ScoringWeights` (or its replacement) resolves rule-key weights on a per-pillar basis:
      a unit test instantiates `ScoringWeights` from a fixture YAML containing two pillars
      that declare the same rule key with different values, and asserts that querying the
      weight for each pillar independently returns that pillar's own declared value (not the
      other pillar's, regardless of YAML declaration order).
- [ ] A regression test using the real `config/simulation_quality/scoring_weights.yaml`
      confirms all 7 identified colliding keys (`subjective_divergence`, `belief_active`,
      `knowledge_rot`, `omniscience_collapse`, `ecology_cycling`, `ecology_broken`,
      `knowledge_economy_active`) now resolve to each pillar's own declared value when
      queried through that pillar's scorer path.
- [ ] `ScoringWeights.load()` still raises `pydantic.ValidationError` on missing/malformed
      YAML keys (existing behavior per INFRA-234 must not regress) —
      `tests/simulation_quality/test_weights.py::test_missing_key_raises_validation_error`
      and `::test_malformed_value_raises_validation_error` still pass.
- [ ] All existing `src/simulation_quality/scorers/*.py` call sites are updated to the new
      pillar-scoped lookup and their existing unit tests
      (`tests/simulation_quality/test_*_scorer.py`) pass, adjusted only where a test's
      expected value depended on the buggy collapsed weight (each such adjustment
      documented in Test Summary).
- [ ] `tests/simulation_quality/test_grade_regression.py` is run and every resulting
      diff (anchor now scores differently) is enumerated and recorded — either fixed via
      re-anchoring in this ticket or explicitly deferred to a named follow-up ticket per
      the Assumptions section's resolution.
- [ ] `docs/simulation_quality/quality_scoring_contract.md` §4.8 and/or §7.2 updated if the
      pillar-scoping mechanism changes anything documented there about how weights are
      declared/looked-up.
- [ ] `docs/parity_ledger/infrastructure.yaml` INFRA-234 (and any other affected entries)
      updated to reflect the new pillar-scoped lookup behavior.

## Related Tickets
- `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM` (in progress) — where this collision
  was discovered while explaining an anomalous COGNITION raw_score; that ticket's own
  determinism investigation continues independently of this fix.
- `TCK-20260713-SIMQ-SCORE-CEILING-FIX` (done) — its independent per-pillar ×5 rescale of
  INFORMATION's `subjective_divergence` (6.0 → 30.0) widened the blast radius of this
  pre-existing collision without introducing the collision mechanism itself.

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §4.8 "Data-Driven Scoring Weights"
  and §7.2 "Adding a Scoring Rule to an Existing Pillar" — describe the config-driven weight
  design; neither section documents the shared-flat-namespace behavior as an intentional
  design choice, so this is treated as a genuine bug, not a design decision to unwind.
- `docs/guides/simulation_quality.md` "Configuration" — general config file overview.
- `docs/parity_ledger/infrastructure.yaml` INFRA-234 — documents `ScoringWeights`'
  pydantic validation behavior (must be preserved); no existing entry documents or
  attributes the cross-pillar collision behavior.

## Related Stored Artifacts
None found covering this specific collision. `stored_artifacts/TCK-20260713-SIMQ-SCORE-CEILING-FIX/`
(investigation.md, plan.md, test_plan.md) documents the per-pillar rescale work that
widened this bug's impact but does not address the flat-namespace mechanism itself.

## Related Code Areas
- `src/simulation_quality/weights.py` — `ScoringWeights._build_flat_index()` (lines 26-33),
  `ScoringWeights.__getitem__` (lines 91-98): the collision mechanism.
- `config/simulation_quality/scoring_weights.yaml` — the 10 pillar sections and the 7
  confirmed colliding keys.
- `src/simulation_quality/scorers/cognition.py` — `CognitionScorer`, affected by
  `subjective_divergence`, `belief_active`, `knowledge_rot`, `omniscience_collapse`.
- `src/simulation_quality/scorers/information.py` — `InformationScorer` (community 222 per
  graphify), the other side of the COGNITION/INFORMATION collisions and sole owner of the
  correct higher-magnitude values for those 4 keys.
- ECONOMY/WORLD scorers (`src/simulation_quality/scorers/economy.py`,
  `src/simulation_quality/scorers/world.py` — exact filenames to confirm in investigation)
  for the `ecology_cycling`/`ecology_broken`/`knowledge_economy_active` collisions.
- `tests/simulation_quality/fixtures/grade_anchors.json` — anchors likely requiring
  re-calibration once the fix lands.
- `tests/simulation_quality/test_weights.py`, `tests/simulation_quality/test_grade_regression.py`.

## Assumptions / Open Questions
- **Re-anchoring scope**: fixing the collision will change the effective scoring weight for
  every anchor in `grade_anchors.json` that exercises any of the 7 colliding keys — those
  anchors' committed grades/scores were calibrated against the buggy collapsed weights and
  will very likely need re-calibration. Whether that re-anchoring work is done inside this
  same ticket or spun out as its own dedicated follow-up ticket is left to the
  investigation/plan phase to decide, based on how many anchors are actually affected once
  enumerated. If deferred, this ticket's Acceptance Criteria requires the deferral to be
  named explicitly (a real follow-up ticket ID), not left as an unstated gap.
- **Exact pillar-scoping mechanism** (namespaced keys vs. one dict per pillar vs. other) is
  intentionally left open — an implementation decision for planning, not scoping.
- **`layer: simulation`** was inferred from this being SimQ scoring-tooling logic (not a
  gameplay mechanic); confirmed consistent with sibling SimQ tickets
  (`TCK-20260713-SIMQ-SCORE-CEILING-FIX` also uses `layer: simulation`).
- Confirmed during scoping: this is SimQ *tooling* (quality-scoring infrastructure), not a
  gameplay mechanic — no `docs/mechanics/` chapter or `docs/parity_ledger/` gameplay-domain
  file (combat_movement, faction, progression, social_narrative, strategic_cognition,
  substrate, town_resource) references `scoring_weights.yaml` or `ScoringWeights`; only
  `docs/parity_ledger/infrastructure.yaml` (SimQ infra) and `world_dynamics.yaml` (one
  incidental v2_evidence citation of the WORLD section's rescale, unrelated to this bug)
  do. No Mechanics Bible or Engine Contract law is implicated.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
