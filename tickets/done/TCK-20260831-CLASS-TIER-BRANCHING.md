---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260831-CLASS-TIER-BRANCHING
phase: done
date: 2026-08-31
tags: [progression]
---

# TCK-20260831-CLASS-TIER-BRANCHING

## Title
Design and build mutually-exclusive class-tier branch choices

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Build Diversity is, in the atlas's own words, a genuine gap, not a disconnection — "the one place on this list where the honest answer is design and build it, not wire it up." class_id is never reassigned anywhere in the live codebase, BreakthroughService perks are always-additive (not mutually-exclusive branches) and nothing in production ever grants one, and EvolutionSystem's kind_set mutation is a single linear chain, not a branching pattern — idea 11 needs to generalize that pattern, not copy it.

## Scope
- Define a class-tier registry with >=2 mutually-exclusive next-tier options per base class.
- Add a new typed update field (e.g. class_id_set on IdentityUpdate, mirroring EvolutionSystem's kind_set pattern) that authoritatively mutates class_id at a defined milestone via the apply path.
- Record the divergence from PROG-108's spawn-only class_id assignment law in docs/guidelines/intentional_divergences.md.
- Verify a tier's stat bonuses do not decrease average combat win-rate via a metamorphic-style comparison.
- Add a test analogous to test_goblin_evolution proving two entities with identical starting class/race but different branch-selection inputs diverge in class_id/tier state.

## Out of Scope
- Re-fixing BreakthroughService's bonus application — already closed by TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION; the atlas's older 'needs a real body' note is stale, do not re-fix.
- Making breakthroughs mutually exclusive — they remain always-additive perks, a separate concept from this ticket's branch tiers.

## Acceptance Criteria
- [x] A class-tier registry exists defining >=2 mutually-exclusive next-tier options per base class (not a single linear chain).
- [x] A new typed update field (e.g. class_id_set on IdentityUpdate, mirroring EvolutionSystem's kind_set pattern) authoritatively mutates class_id at a defined milestone via the apply path, with the divergence from PROG-108's spawn-only law recorded in docs/guidelines/intentional_divergences.md.
- [x] Two entities with identical starting class/race but different branch-selection inputs end up with different class_id/tier state, verified by a test analogous to test_goblin_evolution.
- [x] A tier's stat bonuses do not decrease average combat win-rate, verified via a metamorphic-style comparison.

## Related Tickets
- TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION
- TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION
- TCK-20260824-ALLOCATE-AP-BRANCH-DECISION

## Related Docs
- docs/parity_ledger/progression.yaml
- docs/mechanics/attribute_progression_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/progression/breakthroughs.py
- src/engine/evolution.py
- src/engine/rpg_depth.py
- src/core/classes.py
- src/core/updates.py

## Assumptions / Open Questions
- No numeric anchor exists anywhere for branch-tier stat bonuses — genuinely free creative territory needing explicit authored values per Content & Balance Requirements.
- The first real sub-scope may need to be defining the choice-surface shape itself before any application logic.
- `layer: core` was chosen over `engine` or a new `progression` layer because the affected code spans src/core/ (classes.py, updates.py), src/engine/ (evolution.py, rpg_depth.py), and src/progression/ (breakthroughs.py); no `progression` layer is currently registered in registries/layer_registry.jsonl, and `core` best matches the entity/class-identity primitive this ticket adds (class_id_set on IdentityUpdate). Revisit if a dedicated `progression` layer gets registered later.

## Implementation Notes

Implemented all 10 steps of `staging_artifacts/TCK-20260831-CLASS-TIER-BRANCHING/plan.md` in
order, no deviations to the code-level steps (1-6). Two interpretive notes on the doc-level steps
(7-8) are recorded below and in the staging plan's "Deviations" section.

1. **`CLASS_TIER_REGISTRY`** (`src/core/classes.py`) — new `ClassTierOption` frozen dataclass
   (`tier_id`, `name`, `attribute_bonuses: Dict[str, int]`) and `CLASS_TIER_REGISTRY: Dict[str,
   List[ClassTierOption]]` with 2 options each for `WARRIOR` (`WARRIOR_CHAMPION` — offense-lean,
   `WARRIOR_GUARDIAN` — defense-lean) and `MAGE` (`MAGE_ARCHMAGE`, `MAGE_STORMWEAVER`).
   `CLASS_REGISTRY`'s existing 4 entries untouched.
2. **`IdentityUpdate.class_id_set`** (`src/core/updates.py`) — new `Optional[str] = None` field,
   last-write-wins, wired into `is_noop()` and `merge()` following the exact `life_stage_set`
   pattern. No other field's semantics touched.
3. **`IdentityPatch.apply()`** (`src/engine/patches.py`) — reads `new_id.class_id` into a local
   `cls_id`, overrides it if `u_id.class_id_set is not None`, and adds `class_id=cls_id` to the
   final `replace(...)` call (previously the only `IdentityComponent` field that call omitted, so
   `class_id` always survived unchanged before this ticket).
4. **`ClassTierService`** (new `src/progression/class_tiers.py`) — `apply_bonuses(class_id,
   current_attributes)` looks up `class_id` across `CLASS_TIER_REGISTRY`'s values and applies the
   matching option's `attribute_bonuses` via `dataclasses.replace()`, mirroring
   `BreakthroughService.apply_bonuses()`'s exact live-recompute shape (never a stored delta).
   Wired into `SkillScalingService.get_effective_stats()` (`src/engine/rpg_depth.py`) as a new
   `class_id: Optional[str] = None` kwarg, chained immediately after the breakthrough-bonus
   application. `src/engine/apply.py`'s `stats_dirty` OR-clause gained a `class_id_set is not
   None` branch, and the one live call site now passes `class_id=new_id.class_id`.
5. **`tests/unit/progression/test_class_tiers.py`** (new, 4 tests, all passing) — registry
   branching shape, apply-path wiring + `is_noop()`/`merge()`, cross-entity divergence (identical
   starting `WARRIOR` entities diverging in `class_id` and derived `atk`/`max_hp` purely from
   different `class_id_set` inputs), and a guard proving the tier bonus survives a subsequent
   unrelated `stats_dirty` event.
6. **`tests/integration/combat/test_class_tier_win_rate.py`** (new, 1 test, passing) — deterministic
   sweep (`CombatResolutionSystem.calculate_damage()` is pure/RNG-free, so no statistical sampling
   was needed) across a 10-opponent roster comparing win totals for a pre-tier vs.
   `WARRIOR_CHAMPION`-branched attacker; `wins(post) >= wins(pre)` holds.
7. **Parity ledger** — used the sanctioned `tools/parity_ledger_writer.py::write_entry()` write
   path (schema-validating, rebuilds the derived index in-process) rather than a raw `Edit` on the
   YAML, per this project's documented parity-ledger-write-safety precedent. `PROG-108` keeps
   `status: verified` and gained a `divergence_note` cross-referencing DEV-006/§2.49; its
   `test_path` is unchanged (that test only exercises `WorldCompiler.compile()`, no ticks, so it
   cannot observe `class_id_set`). New `PROG-122` entry records the branching mechanism itself,
   `status: verified`, `test_path` pointing at `test_class_id_set_applies_via_identity_patch`. Also
   ran the visible `python3 tools/parity_index.py build` Bash call per that tool's own documented
   convention for retro-metric visibility.
8. **`docs/guidelines/intentional_divergences.md`** — added `### 2.49 ... — cross-referenced as
   DEV-006` as one merged entry (Section 2, following `### 2.48`'s format) rather than two separate
   entries in two different doc sections. The plan's own phrasing treated "DEV-006 / #2.49" as one
   identifier pairing rather than prescribing two separate doc locations; this reading keeps the
   record in the section that matches its subject area (Section 2's general divergence log,
   consistent with where recent entries like `#2.47`/`#2.48` live) while still giving it the
   `DEV-006` alias the parity-ledger cross-reference (`PROG-108`'s `divergence_note`) already uses.
   Added a matching row to the Section 1 summary table and updated the "Last updated" footer.
   Rationale class: Intentional Gameplay Change. Status: ACTIVE (a real, live, apply-path-wired
   mutation ships with this ticket, unlike `#2.48`'s DEFERRED schema-only precedent).
9. **`docs/core/attributes_and_classes.md` §5** — added `Guardian`/`Stormweaver` rows to the "Tier
   2" table, a supersession note above it, and two new branch edges in the mermaid diagram
   (`Warrior --> Guardian`, `Mage --> Stormweaver`). Ranger/Rogue rows and all of Tier 3 left
   untouched (out of scope, unimplemented aspirational content).
10. **`docs/mechanics/attribute_progression_contract.md`** — added `class_id_set` to the
    `stats_dirty` trigger-condition enumeration in the Lifecycle section. No other section touched.

**Not done, matching plan's explicit Scope Guards**: no fix to the pre-existing
`get_effective_stats()` un-sourced `base_hp`/`base_atk`/`base_def` defaults bug; no live
AI/decision producer that calls `class_id_set` in production gameplay code (same accepted
wired-but-uninvoked precedent as `breakthroughs_add`); `EvolutionSystem`/`_get_evolved_kind`/
`KindPatch` untouched; `BreakthroughService` untouched; no `NOVICE`/`ROGUE` entries added to
`CLASS_TIER_REGISTRY`.

`graphify update .` was not run from this worktree — this worktree has no local `graphify-out/`
(per investigation's Context Search Note); the main repo checkout's graph should be refreshed in a
later phase if needed. `make knowledge-index-update` was run successfully (3 files re-embedded, 0
deleted) since `docs/` files changed.

## Test Summary

All new and regression-scoped tests run via `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3
-m pytest` (this worktree's bare `python3` lacks `pydantic`; the project `.venv` is required):

- `tests/unit/progression/test_class_tiers.py` — 4/4 passed (new).
- `tests/integration/combat/test_class_tier_win_rate.py` — 1/1 passed (new).
- `tests/unit/progression/ tests/unit/core/test_class_registry.py` — 75/75 passed (regression).
- `tests/unit/core/ -k "identity or class or update or rpg_depth"` — 71/71 passed (regression).
- `tests/unit/entity/test_entity_archetypes.py` (PROG-108's test) — 1/1 passed, unchanged.
- `tests/integration/pipeline/test_recovery_gaps.py` — 4/4 passed (regression).
- Full sweep: `tests/unit/progression/ tests/unit/core/ tests/integration/pipeline/test_recovery_gaps.py tests/integration/combat/ -m "not slow"` — 335/335 passed, zero regressions.
- `tools/validate_frontmatter.py` — OK on all 3 touched doc files (`docs/core/attributes_and_classes.md`, `docs/guidelines/intentional_divergences.md`, `docs/mechanics/attribute_progression_contract.md`).

## Files Changed

- `src/core/classes.py` — `ClassTierOption` dataclass + `CLASS_TIER_REGISTRY`.
- `src/core/updates.py` — `IdentityUpdate.class_id_set` field, `is_noop()`, `merge()`.
- `src/engine/patches.py` — `IdentityPatch.apply()` reads/writes `class_id`.
- `src/engine/rpg_depth.py` — `get_effective_stats()` gains `class_id` kwarg, chains `ClassTierService`.
- `src/engine/apply.py` — `stats_dirty` OR-clause + `get_effective_stats()` call site.
- `src/progression/class_tiers.py` — new, `ClassTierService`.
- `tests/unit/progression/test_class_tiers.py` — new, 4 tests.
- `tests/integration/combat/test_class_tier_win_rate.py` — new, 1 test.
- `docs/parity_ledger/progression.yaml` — `PROG-108` divergence_note, new `PROG-122` entry.
- `docs/guidelines/intentional_divergences.md` — new `### 2.49` / DEV-006 entry + summary table row.
- `docs/core/attributes_and_classes.md` — §5 Tier-2 table + mermaid diagram + supersession note.
- `docs/mechanics/attribute_progression_contract.md` — `stats_dirty` enumeration.
- `tickets/inprogress/TCK-20260831-CLASS-TIER-BRANCHING.md` — this file.
- `staging_artifacts/TCK-20260831-CLASS-TIER-BRANCHING/investigation.md` — created earlier this run (Investigate phase).
- `staging_artifacts/TCK-20260831-CLASS-TIER-BRANCHING/plan.md` — created earlier this run (Plan phase); Deviations section added by this Implement phase.
- `staging_artifacts/TCK-20260831-CLASS-TIER-BRANCHING/test_plan.md` — created earlier this run (Plan phase).
- `agent-monitoring/tools.jsonl` — auto-updated by the monitoring hook across this run's tool calls.

## Completion Summary

Implemented mutually-exclusive class-tier branching: a new `CLASS_TIER_REGISTRY` (2 branch
options each for `WARRIOR` and `MAGE`), a new `IdentityUpdate.class_id_set` typed field that
authoritatively mutates `class_id` post-spawn through `IdentityPatch.apply()`, and a new
`ClassTierService` that live-recomputes each tier's attribute bonuses on every derived-stat
recalculation (mirroring `BreakthroughService`'s mechanism), so bonuses survive later unrelated
`stats_dirty` events. All 4 acceptance criteria are verified by new tests (`test_class_tiers.py`,
`test_class_tier_win_rate.py`), the PROG-108 spawn-only divergence is recorded in both the parity
ledger (`PROG-108` divergence_note + new `PROG-122`) and `intentional_divergences.md` (DEV-006 /
§2.49, status ACTIVE), and `docs/core/attributes_and_classes.md` §5 / `attribute_progression_contract.md`
are updated to match. Full regression sweep (335 tests across progression/core/apply-path/combat)
is green with zero drift in existing behavior.
