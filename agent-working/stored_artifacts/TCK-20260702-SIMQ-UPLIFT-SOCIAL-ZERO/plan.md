# Plan — TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO

**Ticket:** TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO  
**Date:** 2026-07-02  
**Tier:** standard  
**Phase:** plan (seq 3)

---

## Scope Summary

Fix SOCIAL (c2) and FACTION (c1) zero-activation root causes so that at least one of the three
pillars records ≥1 calibration_hit in ≥1 calibration run post-fix.  
INFORMATION (c3) is out of scope — documented in §7 below and in investigation.md.

---

## Dependency Map

```
Step 1  (SOCIAL: wire feature flag into calibration runner via profile YAML)
  └── Step 2  (verify CooperationPhase test passes with flag ON)
       └── Step 4  (run calibration; SOCIAL hit confirmed)
            └── Step 6  (update grade_anchors.json)
                 └── Step 7  (update event_type_coverage.md)

Step 3  DEFERRED — WorldCompiler does not construct FactionState objects
        (confirmed: grep found no FactionState( in compiler.py; only faction_id string
        assignment to entities). Fixing FACTION requires compiler + schema extension
        which exceeds minimal scope. SOCIAL alone satisfies the AC.
        Defer to follow-up ticket.

Step 5  (regression: scoped pytest suite) — depends on Steps 1–2 complete
Step 6  depends on Step 4 calibration output
Step 7  depends on Steps 4 + 6
Step 8  (INFORMATION + FACTION defer doc) — independent, can run any time
```

## Implementation Scope (after UQ-1 resolution)

**In scope:** Steps 1, 2, 4, 5, 6, 7, 8 — SOCIAL activation via feature flag in calibration profile.

**Deferred:** Step 3 (FACTION) — requires WorldCompiler extension; follow-up ticket needed.

**FACTION deferral rationale:** `WorldCompiler.compile()` processes `spec.factions` (L177) but only initializes vault gold — confirmed by grep showing no `FactionState(` constructor and no `state.factions` dict population in `compiler.py`. Seeding `tension_level` in world YAML would have zero effect without a compiler code path to read and apply it. Extending the compiler is out of scope for this minimal-fix ticket.

---

## Ordered Steps

### Step 1 — Enable ENABLE_SOCIAL_COOPERATION in the calibration runner via env var wiring (code change: calibrate_simq.py)

**Why:** `calibrate_simq.py` already reads env vars and injects them as `state.feature_flags` (lines 159–180). The simplest, least-invasive activation path is to pass `ENABLE_SOCIAL_COOPERATION=ON` as a documented env override for the urban_political calibration runs. However, we want this to be automatic in calibration rather than requiring the caller to remember the env var. The correct approach is to add a `social_cooperation` flag to the `urban_political` calibration profile YAML so it is active every time that scenario is run.

**Files to change:**
- `config/simulation_quality/profiles/urban_political.yaml`

**Change:** Add a `feature_flags` section to the urban_political profile YAML that sets `ENABLE_SOCIAL_COOPERATION: ON`.

**Constraint:** `calibrate_simq.py`'s `_load_weights()` reads profile YAMLs via `ScoringWeights.load()` — this is for scoring weights only, not feature flags. The feature flags in this YAML would need a separate read path. Check whether `ScoringWeights` ignores unknown keys or errors. If it errors, the cleaner approach is:
- Add a separate `config/simulation_quality/profiles/urban_political_flags.yaml` file, OR
- Patch `calibrate_simq.py` to read a `feature_flags:` section from the profile YAML and inject them into `env_flag_overrides` before building state.

**Preferred path (minimal change):** Patch `calibrate_simq._run_engine()` to accept an optional `extra_flags` dict, and have `main()` read an optional `feature_flags:` key from the resolved scoring profile YAML (after `ScoringWeights.load()`, parse the raw YAML separately for `feature_flags:`). Inject into `env_flag_overrides`. This keeps all calibration configuration in one file per scenario.

**Scope guard:** Do NOT change the default `FeatureFlagManager` defaults. Do NOT change the `RolloutProfileManager` class_B/class_C profiles. The flag must be ON only for the calibration runner invocation, not globally.

**Acceptance:** `ENABLE_SOCIAL_COOPERATION` is active when `calibrate_simq.py --name urban_political` is run, without requiring a manual env var export.

---

### Step 2 — Verify CooperationPhase unit test passes as-is

**Why:** Before relying on CooperationPhase to produce SOCIAL events, confirm the existing unit test in `tests/unit/domains/cooperation/test_cooperation_phase.py` passes with the flag ON. The test plan (T-4) specifies this test; it may already exist or need a small addition.

**Files to change:**
- `tests/unit/domains/cooperation/test_cooperation_phase.py` — add `test_cooperation_phase_sets_property_when_enabled()` if the test does not already assert `last_cooperation_decision` in property_updates with the flag ON (see test_plan.md T-4).

**Files NOT to change:** `src/domains/cooperation/phase.py` — CooperationPhase logic is not being modified; only verifying it behaves correctly when the flag is ON.

**Scope guard:** No changes to the cooperation domain implementation.

**Acceptance:** `pytest tests/unit/domains/cooperation/test_cooperation_phase.py -v` passes, including a test confirming `last_cooperation_decision` is set in property_updates for eligible entities when flag is ON, and NOT set when flag is OFF (guard G-3 from test_plan.md).

---

### Step 3 — Seed faction tension in urban_political world spec (world content change)

**Why:** The resolved world YAML for urban_political (`data/worlds/urban_political/resolved/world.resolved.yaml`) has a `factions:` list with 16 factions (hero_guild, town_council, merchant_league, bandit_company, etc.) but no `tension_level`, `territory`, or `diplomatic_relations` fields on any faction entry. `WorldCompiler.compile()` processes `spec.factions` (line 177) but only initializes vault gold — `FactionState` is not constructed from the YAML spec at all; `AuthoritativeState.factions` is populated elsewhere (or is empty dict).

**Investigation required before writing (Step 3a):** Confirm whether `WorldCompiler.compile()` constructs `FactionState` objects and populates `state.factions`, or whether `state.factions` is always empty after compilation. Grep `compiler.py` for `factions` dict population and `FactionState(` construction.

**If `state.factions` is NOT populated by WorldCompiler (most likely per investigation.md AQ1):**
- Add a `factions_state:` section to `data/worlds/urban_political/world.yaml` (the source YAML) with at minimum two faction entries that have `tension_level: 0.5` and mutual `diplomatic_relations: {<other>: NEUTRAL}`.
- Factions to seed: `bandit_company` and `town_council` — they are naturally adversarial per world description, both have entities in the world.
- Then re-run the world resolver/compiler to regenerate `resolved/world.resolved.yaml`. If recompilation is automated (via `make` or a tool), use that. If manual, update the resolved YAML directly with the compiled FactionState entries.
- Also: update `WorldCompiler.compile()` to actually construct `FactionState` objects from a `factions_state:` spec block and add them to `AuthoritativeState.factions`. Without this code path, adding YAML content has no effect.

**If `state.factions` IS populated by WorldCompiler:** Add `tension_level: 0.5` and `diplomatic_relations: {town_council: NEUTRAL}` to the `bandit_company` faction entry in the resolved YAML directly. This is the simpler path.

**Files to change (expected):**
- `data/worlds/urban_political/world.yaml` — add `factions_state:` block (or extend `factions:` entries with tension/diplomatic fields)
- `data/worlds/urban_political/resolved/world.resolved.yaml` — regenerate or manually update with seeded FactionState entries
- `src/worldbuilding/compiler.py` — add FactionState construction from spec if not present (likely needed)
- `src/worldbuilding/schema.py` — add `FactionStateSpec` model or extend existing `FactionSpec` if tension/territory fields are not already in schema

**Scope guard:** Only change two factions. Do NOT add territory (which triggers `FactionAwarenessService` + P0-C navigation risk). Do NOT change `military_strength` defaults (keeps HOSTILE→WAR impossible — WAR events are out of scope for this ticket). The goal is NEUTRAL→TENSE transition (pair_tension > 0.4), which is achievable with `tension_level=0.5` on both factions.

**Acceptance:** `state.factions` for `urban_political` contains at least `bandit_company` and `town_council` with `tension_level=0.5`. `DiplomaticStateMachine.compute_transitions()` returns a non-empty list when called with these factions.

---

### Step 4 — Run calibration for urban_political_seed42_500t and verify non-zero hits

**Why:** This is the primary acceptance criterion — ≥1 calibration run shows non-zero event_count for at least one of the three pillars.

**Command:**
```bash
ENABLE_SOCIAL_COOPERATION=ON python3 tools/calibrate_simq.py \
    --name urban_political --seed 42 --ticks 500
```
(Or without the env var if Step 1 wired it into the profile YAML.)

**Expected outcomes:**
- **SOCIAL:** `cooperation_event` events fire within ~50 ticks once CooperationPhase is ON. The pillar should show event_count ≥ 1 and grade ≥ C (non-zero raw_score). Expected first-event tick: ≤ 50 per investigation.md §SOCIAL activation notes.
- **FACTION:** `diplomatic_transition` events fire when `pair_tension > 0.4` → NEUTRAL→TENSE transition. If Step 3 seeded `tension_level=0.5` on both factions, this should fire on tick 1 (the transition is evaluated every tick in Phase 8d). Grade may still be C (single transition event), but event_count ≥ 1.
- **INFORMATION:** Expected to remain 0. This is correct per scope (INFORMATION deferred).

**Scope guard:** Do not run the full 25-scenario calibration corpus. Run only `urban_political_seed42_500t`. Check output `data/calibration/urban_political_seed42_500t/quality_report.json` for SOCIAL and FACTION pillar event_counts.

**Acceptance:** `quality_report.json` shows `event_count ≥ 1` for SOCIAL OR FACTION (both is better). Console output from calibrate_simq confirms "Replayed N events through QualityHub" with N > 0 for these pillars.

**Dormancy penalty risk (R4):** If FACTION's first `diplomatic_transition` event arrives after `zero_diplomacy_by_tick` gate in FactionScorer, the `_diplomacy_dormant_fired` path may fire a negative delta instead of positive. Check `FactionScorer._diplomacy_dormant_fired` gate tick vs. expected first-event tick (tick ~1 for seeded tension). If gate is e.g. tick 100 and first event fires at tick 1, dormancy path does NOT fire (gate not yet crossed). If gate is 0 or very low, dormancy fires immediately. Verify and adjust if needed.

---

### Step 5 — Run scoped regression test suite

**Why:** Confirm no existing tests are broken by the changes in Steps 1–3.

**Commands (from test_plan.md Phase 1 + Phase 3):**
```bash
pytest tests/unit/observability/test_event_extractor_social_faction.py \
       tests/unit/observability/test_event_extractor_lead_beliefs.py \
       tests/simulation_quality/test_quality_hub_event_translation.py \
       tests/simulation_quality/test_faction_scorer.py \
       tests/simulation_quality/test_social_scorer.py \
       tests/simulation_quality/test_information_scorer.py \
       tests/unit/domains/cooperation/test_cooperation_phase.py \
       tests/unit/engine/test_faction_decision.py \
       -v --tb=short -x
```

Also run the diagnostic tests from Step 2:
```bash
pytest tests/simulation_quality/test_faction_activation_diagnostic.py -v 2>/dev/null || true
```
(Create this file if it doesn't exist, per test_plan.md T-1 and T-2.)

**Scope guard:** Do NOT run `pytest tests/` (full suite). Do NOT run slow tests. Do NOT run the integration test for Step 5 — that is covered in Step 4 via direct calibration run.

**Acceptance:** 0 failures in the scoped suite. Warnings about missing fixture files for new tests are acceptable if the test file doesn't exist yet (will be created in the same commit).

---

### Step 6 — Update grade_anchors.json with new calibration grades

**Why:** After Step 4 confirms SOCIAL and/or FACTION events fire, the grades for `urban_political_seed42_500t` may shift. If SOCIAL or FACTION move from C (with event_count=0, raw_score=0) to C (with event_count > 0, positive raw_score), the grade may not change (C → C is still within band), but `evaluate_simq.py` must not regress. If a grade moves up to B, the anchor must be updated.

**Files to change:**
- `tests/simulation_quality/fixtures/grade_anchors.json` — update only the `urban_political_seed42_500t` entry if grades changed. Do NOT update entries for runs that were not re-run.

**How to determine new anchors:** Read `data/calibration/urban_political_seed42_500t/quality_report.json` after Step 4. If any pillar grade is higher than the current anchor + 1 band, update the anchor to the new grade. Current anchor for `urban_political_seed42_500t`: FACTION=C, SOCIAL=C, INFORMATION=C.

**Scope guard:** Only update anchors for the scenario(s) actually re-run in Step 4. If other scenarios in the corpus are NOT re-run, their anchors must not change. Do not run `make evaluate` for all 25 scenarios — only the targeted one.

**Verify regression guard:**
```bash
python3 tools/evaluate_simq.py --scenario urban_political_seed42_500t --dry-run
```
Must exit 0.

**Acceptance:** `evaluate_simq.py --dry-run` exits 0 for `urban_political_seed42_500t`. No REGRESS rows in output.

---

### Step 7 — Update event_type_coverage.md with revised calibration_hits

**Why:** The doc currently shows `calibration_hits=0` for all SOCIAL and FACTION events. After Step 4 confirms non-zero hits, the table must be updated to reflect the new ground truth. Per CLAUDE.md docs rule: any doc change requires `make knowledge-index-update`.

**Files to change:**
- `docs/simulation_quality/event_type_coverage.md` — update §1.1 table rows for:
  - `cooperation_event` — update `calibration_hits` from 0 to observed count; add note: "urban_political_seed42_500t with ENABLE_SOCIAL_COOPERATION=ON (TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO)"
  - `diplomatic_transition` — update `calibration_hits` from 0 to observed count if FACTION fix fired; add note referencing this ticket and world/flag config
  - Other events that fired (e.g. `social_memory_created`, `faction_tension_delta`) — update similarly
  - Events that remain 0 (all INFORMATION events, FACTION events that didn't fire) — leave as 0 with no note change
- Update §6 Summary table: `calibration_hits=0` entries for SOCIAL/FACTION that changed

**Do NOT change:**
- Classification of any event (scored / engine_emission_gap / etc.)
- INFORMATION section entries — they remain 0 and are documented in investigation.md as deferred
- Any §3.x (engine emission gaps) entries — none changed by this ticket

**After doc update:**
```bash
make knowledge-index-update
```

**Acceptance:** event_type_coverage.md §1.1 accurately reflects post-fix calibration_hits for SOCIAL and FACTION events. `make knowledge-index-update` completes without error.

---

### Step 8 — Document INFORMATION (c3) as deferred in investigation.md

**Why:** investigation.md already explains the c3 root cause thoroughly (§INFORMATION section). This step formalizes the deferral note so the ticket can be closed with a clear handoff.

**Files to change:**
- `staging_artifacts/TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO/investigation.md` — add a "## INFORMATION Deferral" section (if not already present) stating:
  - Root cause c3 confirmed: `ENABLE_BELIEF_ASSIMILATION=OFF` AND `state.information_source_profiles=[]` in all calibration worlds.
  - Enabling the flag alone is insufficient — `state.pending_information_responses` and `information_source_profiles` must also be seeded.
  - This is a dual-gate problem (flag + data), requiring a non-trivial data seeding mechanism in world specs or the calibration runner.
  - A follow-up ticket is required. Suggested scope: (1) add `information_source_profiles` to at least one world spec; (2) enable `ENABLE_BELIEF_ASSIMILATION` for that world's calibration profile; (3) verify `belief_assimilated` fires.
  - Not addressed in this ticket per plan scope.

**Scope guard:** Do not attempt to enable INFORMATION in this ticket. Do not create the follow-up ticket here (create via `create-tickets` skill in a separate session if desired).

**Acceptance:** investigation.md has a clear, self-contained INFORMATION deferral section that a future agent can act on without re-reading the full investigation.

---

## Scope Guards (Global)

- **DO NOT** change `FeatureFlagManager` defaults (the `_flags` dict in `feature_flags.py`). Global defaults must remain OFF.
- **DO NOT** enable `ENABLE_BELIEF_ASSIMILATION`. INFORMATION is out of scope.
- **DO NOT** add `territory` to any FactionState (avoids P0-C navigation region_id=None interaction).
- **DO NOT** change `military_strength` defaults (avoids triggering WAR transitions).
- **DO NOT** modify any scorer (FactionScorer, SocialScorer, InformationScorer) logic.
- **DO NOT** modify EventExtractor emission code — all emitters are confirmed correct.
- **DO NOT** modify QualityHub translation table.
- **DO NOT** run `pytest tests/` (full suite) — use scoped commands only.
- **DO NOT** touch calibration runs for any world other than `urban_political_seed42_500t` unless a regression is detected.
- **DO NOT** change the `RolloutProfileManager` class definitions — the calibration runner uses `PROD_SMALL` (class_C maps to full stack; verify this does not conflict).

---

## Acceptance Criteria Mapped to Steps

| AC | Step | Verifiable by |
|---|---|---|
| Diagnostic run confirms engine-level events fire | Step 4 | `quality_report.json` event_count for SOCIAL/FACTION ≥ 1 |
| Root cause classified (c) with evidence | — | investigation.md (already done, seq 2) |
| Fix implemented: ≥1 calibration run shows non-zero event_count | Step 4 | `quality_report.json` SOCIAL or FACTION event_count > 0 |
| event_type_coverage.md updated with revised calibration_hits | Step 7 | §1.1 table entries for fired events updated |
| If (c): document which worlds/configs activate mechanics | Step 8 (INFORMATION) + Steps 1–3 (SOCIAL/FACTION) | investigation.md deferral note; urban_political profile YAML with flag ON |

---

## §7 — INFORMATION Deferral (Out of Scope)

Root cause c3 has two independent gates:

1. `ENABLE_BELIEF_ASSIMILATION=OFF` (flag gate)
2. `state.information_source_profiles=[]` and `state.pending_information_responses=[]` in all calibration worlds (data gate)

Enabling the flag alone (analogous to the SOCIAL fix) is insufficient — `InformationBeliefPhase.apply()` calls `InformationQueryRouter.route()` which returns no candidates when `information_source_profiles` is empty. No intent is produced, no `last_assimilated_tick` is set, no `belief_assimilated` event fires.

The data gate requires either:
- Adding `InformationSourceProfile` objects to world specs (new schema/compiler work), or
- Seeding `state.pending_information_responses` in the calibration runner (synthetic injection, less authentic)

This is tracked as a follow-up. The fix in this ticket does NOT address INFORMATION.

**Expected post-fix state:** INFORMATION pillar remains at `event_count=0`, `grade=C` in all calibration runs. This is documented and intentional — not a regression.
