---
status: active
layer: world
authority: P1
audience: agent
artifact_type: test_plan
tags: [simulation-quality, self-model, corpus, calibration, cognition]
---

# Test Plan — TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT

## Regression Surface

- This ticket is **content-authoring + calibration**, not a code change — no `src/` file is modified.
  The regression surface is therefore: (a) confirm nothing about the new world/profile breaks any
  existing calibration anchor, and (b) confirm the new world itself behaves as characterized in
  `investigation.md`.
- `src/cognition/self_model_phase.py`, `src/engine/pipeline.py:152`, `src/engine/patches.py` — the 3
  BRANCH-B fixes this pilot exercises at scale for the first time. Not touched by this ticket, but
  their existing test coverage (§6 of `investigation.md`) must stay green throughout.
- `data/worlds/<new_world>/world.yaml` + `config/simulation_quality/profiles/<new_world>.yaml` — new
  files this ticket adds.
- `tests/simulation_quality/fixtures/grade_anchors.json` / `test_grade_regression.py`'s
  `FAST_ANCHOR_KEYS` — additive only.
- `docs/simulation_quality/eval_matrix_results.md`, `docs/parity_ledger/strategic_cognition.yaml` —
  additive doc updates.

## Pre-Implementation Regression Baseline (already run this session)

- `pytest tests/unit/cognition/test_phase2_self_model_phase.py tests/unit/optimization/test_component_patches.py -q`
  → **14 passed**.
- `pytest tests/integration/domains/test_fused_loop.py -q -k "self_model or branch_b or belief"`
  → **7 passed**.
Both confirm the 3 BRANCH-B fixes are intact and unregressed **before** this ticket's content changes
land. Re-run identically after implementation — 0 change expected (no `src/` edit).

## New Verification Required (implementation phase)

1. **World compiles with 0 warnings.** `python -m src.worldbuilding.cli resolve <new_world>` then
   `compile --seed <seed> --from-resolved` — confirm `world_compile_report.json` shows 0 warnings and
   the `pending_self_model_information_events` entry resolves to a real `actor_id` (not skipped with a
   "matched no compiled entity" warning — this is the exact failure mode `compiler.py:466-469` guards
   against if the module composition's actual `pop_N` naming doesn't match what's assumed in
   `investigation.md` §2; re-verify the resolved YAML's `entities:` section shows the expected
   `pop_0`/`pop_1`/`pop_2` ids from `hero_adventurers` before relying on it).
2. **Population stability**: >=60% alive floor through at least 200-300 ticks at seed 42, following
   `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s pattern (mirrors both
   `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO` worlds, which held 100% through 300 ticks with
   the same `frontier_village_core`/`hero_adventurers` module pair — no reason to expect worse here,
   since no new hazard/combat content is added).
3. **`ENABLE_BELIEF_ASSIMILATION` confirmed OFF**: `grep -n "feature_flags" -A3
   config/simulation_quality/profiles/<new_world>.yaml` shows only `ENABLE_SELF_MODEL_COGNITION: "ON"`
   — no `ENABLE_BELIEF_ASSIMILATION` key at all (defaults OFF per
   `src/domains/optimization/feature_flags.py:18`). Confirm no `information_source_profiles`/
   `pending_information_responses` key exists anywhere in the new `world.yaml` (Scope item 3's
   isolation guard).
4. **3-seed, 200-300+ tick calibration run** (seeds 42/123/456 minimum, following
   `tools/calibrate_simq.py --ticks <N> --seed <S> --name <new_world> --profile <new_world>`).
   Record, per §5/§7 of `investigation.md`, and **expect**:
   - `self_model_updated` calibration_hits: **> 0, and large** (roughly `alive_entities × ticks`,
     since it fires every tick for every alive/active entity once `ENABLE_SELF_MODEL_COGNITION` is
     ON — not just once for the seeded actor). If this comes back 0 or near-0, that is itself a
     genuine, reportable anomaly (would mean `ENABLE_SELF_MODEL_COGNITION` did not actually take
     effect for this world/profile — check profile-loading precedence per
     `tools/calibrate_simq.py`'s `_load_profile_feature_flags`/`_resolve_profile` first).
   - COGNITION pillar grade: expected to move off whatever inert baseline it currently shows for a
     comparable inert-content world, driven by `self_model_active` tag volume. Record the actual grade
     honestly, whatever it is (per Scope item 4c) — do not assume a specific letter grade in advance.
   - INFORMATION pillar grade: **expected to stay at its current baseline (`C`, 0 events)** — per
     `investigation.md` §4/§5, `InformationScorer`'s event types are all gated behind
     `ENABLE_BELIEF_ASSIMILATION`, which this world never turns on. **If INFORMATION unexpectedly
     shows non-zero signal, STOP and investigate before recording** — that would mean either (a) the
     profile YAML accidentally also enabled `ENABLE_BELIEF_ASSIMILATION` (config error, not a code
     bug), or (b) some other code path feeds `InformationScorer`'s event types independent of that
     flag, which would contradict this investigation's own direct-code-read conclusion and needs
     re-verification before being trusted.
   - The specific seeded actor's `self_model.knowledge.unknowns["material.moon_resin.source"]` (or
     whatever subject is chosen) should be inspectable via a debug/replay dump at any tick ≥1 (proves
     durability across the run, not just tick 0 — mirrors
     `test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`'s own
     tick-N/tick-N+1 check, at calibration scale rather than hand-built scale).
5. **Grade-anchor entries**: add the 3-seed matrix to `grade_anchors.json` and `FAST_ANCHOR_KEYS`,
   purely additive (mirrors `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`'s +6-entry pattern
   exactly).
6. **`make evaluate --dry-run`**: must exit 0 with 0 regressions on the **pre-existing** corpus
   (`urban_political`, `dungeon_crawl`, `sandbox_world`, `simq_routing_test`,
   `unit_faction_tension`, `unit_information_source`) — none of those profiles touch
   `ENABLE_SELF_MODEL_COGNITION`, so 0 regression is expected and required.
7. **Existing self-model/Branch-B test suite unchanged** (§6 of `investigation.md`'s full list) — must
   pass unmodified; this ticket adds no new `src/`-level test since it makes no `src/` change.

## Anti-Drift Test Guards

- Do not hand-edit `data/worlds/<new_world>/resolved/world.resolved.yaml` — always regenerate via
  `python -m src.worldbuilding.cli resolve <new_world>`, per Pattern 6 / the BRANCH-B and
  FACTION-INFO precedents.
- Do not seed `information_source_profiles` or `pending_information_responses` in this world under
  any circumstance — that would silently convert this from a Step-1-isolation pilot into an
  (unscoped) Branch-A+Branch-B combination pilot, defeating Scope item 3 and item (b) of the ticket's
  own Scope section.
- Do not add `ENABLE_BELIEF_ASSIMILATION` to this world's profile YAML, even temporarily for local
  testing — if a genuine need arises to prove query-routing at scale, that is out of this ticket's
  scope per its own Out-of-Scope section and needs a separately-scoped follow-up ticket, not a
  same-ticket scope expansion.
- Before recording any grade in `eval_matrix_results.md`, cross-check the calibration run's raw event
  counts (not just the letter grade) against the §5/§7 expectations above — a grade alone can mask
  whether the expected mechanism (vs. some other, unrelated event) produced it.
- `self_model_updated`'s expected high volume (every entity, every tick) means this world's
  calibration output will look structurally different from every other world in the corpus (which
  have 0 hits for this event type) — do not mistake this for an anomaly when reviewing the run; it is
  the expected, correct consequence of turning the flag on.
- Canonical-hash baseline churn (per `SUB-374`) is expected and acceptable for this **one new** world
  only — do not let it block the grade-anchor commit; do not attempt to "fix" the hash to match a
  stale expectation.

## Scoped Pytest / CLI Commands

```bash
# Pre-existing regression baseline (already confirmed green this session; re-run post-implementation)
pytest tests/unit/cognition/test_phase2_self_model_phase.py tests/unit/optimization/test_component_patches.py -q
pytest tests/integration/domains/test_fused_loop.py -q -k "self_model or branch_b or belief"

# New world compile/resolve
python -m src.worldbuilding.cli resolve <new_world>
python -m src.worldbuilding.cli compile <new_world> --seed 42 --from-resolved

# Population stability + 3-seed calibration matrix
python3 tools/calibrate_simq.py --ticks 200 --seed 42  --name <new_world> --profile <new_world>
python3 tools/calibrate_simq.py --ticks 200 --seed 123 --name <new_world> --profile <new_world>
python3 tools/calibrate_simq.py --ticks 200 --seed 456 --name <new_world> --profile <new_world>

# Corpus-wide regression gate (AC requirement)
make evaluate --dry-run
```
