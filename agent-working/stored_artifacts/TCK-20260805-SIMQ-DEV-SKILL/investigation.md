---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-DEV-SKILL
artifact_type: investigation
tags: [skills, simulation-quality]
---

# Investigation — TCK-20260805-SIMQ-DEV-SKILL

## Confirmed: `simq-audit/SKILL.md` is entirely audit/governance
Read in full — Recalibrate → diff against grade anchors → classify drift → sync docs/parity →
finalize. Zero coverage of scorer internals, adding a new pillar, or debugging a wrong score. This
ticket's coverage is additive, not overlapping.

## Real Content Grounded (`docs/simulation_quality/quality_scoring_contract.md`)
- **§4.1 `ScoreRecord`**: the atomic, immutable, typed scoring unit (`tick`, `event_id`, `pillar`,
  `delta`, `reason`, `event_type`, `entity_id`, `region_id`, `tags`).
- **§4.2 `ScoringContext`**: read-only, passed to every `scorer.score()` call — scorers must not
  mutate it.
- **§4.3 `PillarAccumulator` state**: `raw_score`, `event_count`, `negative_count`,
  `last_event_tick`, `worst_events`, `window_buffer` (sliding, maxlen=200), `loop_flags`.
- **§7.1 Adding a new pillar**: a real 9-step protocol (enum entry → `PILLAR_METADATA` → scoring
  weights YAML → default profile weight → new `PillarScorer` subclass → `SCORER_REGISTRY`
  registration → Scenario Registry entry → unit tests) with a hard rule: **no numeric literals in
  scorer code**, always `self.weights["rule_key"]`.
- **§7.3 Conflict Detection Rules**: no dual-ownership, no duplicate signals, delta-polarity
  consistency across pillars — plus a real, disclosed, unresolved divergence
  (`EconomyScorer.paid_info_transaction` returns a live-scored contribution where the design says
  "documentary only," flagged not fixed by the ticket that otherwise closed this gap class,
  `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`) — worth citing so a dev-side skill doesn't claim
  the doc's ideal design is 100% actually true in code.
- Real `src/simulation_quality/*.py` files confirmed via `find`: `pillar_accumulator.py`,
  `pillars.py`, `quality_hub.py`, `score_record.py`, `weights.py`, `feed.py`, `worker.py`.
- Real test files confirmed via `find`: `tests/simulation_quality/test_scorer_pillar_binding.py`
  (the exact test for the primary/secondary pillar-scoped weight lookup fix),
  `test_cognition_scorer.py`/`test_economy_scorer.py`/`test_progression_scorer.py`/
  `test_narrative_scorer.py` (real per-pillar scorer test examples), `test_quality_hub_integration.py`.

## Scope Decision: standalone new skill, not a companion doc
A companion doc bolted onto `simq-audit/SKILL.md` would blur that skill's own clean, single-purpose
audit-workflow scope (matching this session's earlier finding that narrow, single-purpose skills
are easier to reason about than merged ones). Standalone skill named `simq-dev` (matching the
sibling ticket's own naming), cross-referencing `simq-audit` for the audit-side workflow rather
than duplicating any of its content.

## Unresolved Questions
None — all cited content verified against the real contract doc and real file paths.
