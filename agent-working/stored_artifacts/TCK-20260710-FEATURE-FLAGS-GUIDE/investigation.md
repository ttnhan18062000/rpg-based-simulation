---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260710-FEATURE-FLAGS-GUIDE
artifact_type: investigation
tags: [feature-flags, documentation, claude-md]
---

# Investigation — TCK-20260710-FEATURE-FLAGS-GUIDE

## Current Behavior

### `FeatureFlagManager` / `FeatureMode` (`src/domains/optimization/feature_flags.py`)
`FeatureMode` (lines 4-8) is a `str, Enum` with exactly 4 members: `OFF`, `SHADOW`, `ON`, `STRICT`.

`FeatureFlagManager.__init__` (lines 12-28) hardcodes `self._flags` with **exactly 10 entries**, all defaulting to `FeatureMode.OFF`:

| # | Flag | Default |
|---|---|---|
| 1 | `ENABLE_WORLD_CAPABILITY_LAYER` | OFF |
| 2 | `ENABLE_SELF_MODEL_COGNITION` | OFF |
| 3 | `ENABLE_ADVENTURE_ROUTING` | OFF |
| 4 | `ENABLE_COMBAT_ENGAGEMENT` | OFF |
| 5 | `ENABLE_BELIEF_ASSIMILATION` | OFF |
| 6 | `ENABLE_PROGRESSION_EVOLUTION` | OFF |
| 7 | `ENABLE_SOCIAL_COOPERATION` | OFF |
| 8 | `ENABLE_WORLD_EMERGENCE` | OFF |
| 9 | `ENABLE_LIFE_ARC_CAMPAIGNS` | OFF |
| 10 | `ENABLE_ENHANCED_TRACE_EVENTS` | OFF |

This confirms the ticket's own claim (Scope, line 34) exactly — 10 flags, not 7.

Other methods on `FeatureFlagManager`: `get_all_flags()` (L30-31, returns `List[str]` of keys), `get_flag_mode(flag)` (L33-34, returns `FeatureMode`, defaults to `OFF` for unknown flags), `set_flag_mode(flag, mode)` (L36-38, no-op if flag unknown — silently ignores, does not raise), `is_enabled(flag)` (L40-41, `True` only for `ON`/`STRICT`), `is_shadow(flag)` (L43-44), `serialize()` (L46-47, returns `Dict[str, str]` of `.value`).

**Gap found, not in ticket scope but worth flagging**: `docs/simulation/domains/optimization_contract.md` line 86 says *"check `FeatureFlagManager.get_flag(flag_name)`"* — there is no method named `get_flag` anywhere in `feature_flags.py`; the actual method is `get_flag_mode()`. This is a second stale citation in the same doc, distinct from the "Known Flags" table undercount the ticket already scopes fixing. It is in the same file the ticket is already editing (`optimization_contract.md`), in the same "FeatureFlagManager" section as the table being corrected. Flagged as a Risk below — not adding it to scope myself since the ticket's Acceptance Criteria #5 only names the "Known Flags" table.

### `RolloutProfile` / `RolloutProfileManager` / `HardwareClass` (`src/domains/optimization/rollout_profiles.py`)
`HardwareClass` (L6-9) is a 3-member `str, Enum`: `CLASS_A` (low spec), `CLASS_B` (mid spec), `CLASS_C` (high spec / full stack).

`RolloutProfile` (L11-32) is a frozen dataclass: `name`, `hardware_class`, `enabled_phases: List[str]`, `shadow_phases: List[str]`, `disabled_phases: List[str]`, `max_ram_mb`, `tick_budget_ms`, `max_trace_events`, plus `.serialize()`.

`RolloutProfileManager.__init__` (L36-86) constructs a `FeatureFlagManager()` internally (L37) purely to derive `valid_flags = set(self.ff_manager.get_all_flags())` (L38, used later in `create_custom_profile` L92, not in `__init__` itself), then builds 3 hardcoded `RolloutProfile` instances keyed by `HardwareClass`:
- **CLASS_A**: 2 enabled (`ENABLE_WORLD_CAPABILITY_LAYER`, `ENABLE_SELF_MODEL_COGNITION`), 1 shadow (`ENABLE_ADVENTURE_ROUTING`), 7 disabled. `max_ram_mb=512`, `tick_budget_ms=10.0`, `max_trace_events=1000`.
- **CLASS_B**: 6 enabled, 2 shadow (`ENABLE_SOCIAL_COOPERATION`, `ENABLE_WORLD_EMERGENCE`), 2 disabled (`ENABLE_LIFE_ARC_CAMPAIGNS`, `ENABLE_ENHANCED_TRACE_EVENTS`). `max_ram_mb=2048`, `tick_budget_ms=25.0`, `max_trace_events=5000`.
- **CLASS_C**: all 10 enabled, 0 shadow, 0 disabled. `max_ram_mb=8192`, `tick_budget_ms=50.0`, `max_trace_events=20000`.

`get_profile(hw_class)` (L88-89) is a plain dict lookup — no fallback, raises `KeyError` for an invalid `HardwareClass` (cannot happen given the enum is closed). `create_custom_profile(name, enabled, shadow=None)` (L91-107) validates flag names against `valid_flags` and raises `ValueError(f"Invalid phase flag: {flag}")` for any unrecognized flag; unlisted flags are placed in `disabled`.

**Note**: `RolloutProfileManager` never actually calls `FeatureFlagManager.set_flag_mode()` to *apply* a profile to a manager instance — there is no `apply_profile()`/`activate()` method. The class only produces `RolloutProfile` descriptor objects; wiring a chosen profile's `enabled_phases`/`shadow_phases` into a live `FeatureFlagManager` instance is left to the caller (this is consistent with the ticket's Related Code Areas note calling it "the profile-driven initializer surface," not the initializer itself — worth being precise about in the guide so readers don't assume `get_profile()` has a side effect).

### `docs/simulation/domains/optimization_contract.md`
Frontmatter: `status: authoritative`, `layer: ai`, `authority: P1`, `last_verified: 2026-06-12`, `tags: [domains, optimization, performance, cache, degradation, feature-flags, contract]`.

"Known Flags" table (L74-84) lists only 7 flags — missing `ENABLE_WORLD_EMERGENCE`, `ENABLE_LIFE_ARC_CAMPAIGNS`, `ENABLE_ENHANCED_TRACE_EVENTS`. This is the table Acceptance Criterion #5 requires fixed to exactly 10.

The "RolloutProfiles" section (L114-116) describes the mechanism as defining *"named rollout configurations ... for different deployment profiles (development, staging, production, benchmark)"* — this does not match the actual source, which defines exactly 3 `HardwareClass`-keyed profiles (`CLASS_A`/`CLASS_B`/`CLASS_C`), not named deployment-stage profiles. This is a second, independent staleness in the same doc section adjacent to the flag-count issue. Not in the ticket's named scope (only the "Known Flags" table is named in AC #5) — flagged as a Risk below since the new guide will need to describe `RolloutProfile`/`HardwareClass` accurately per Scope bullet 5, and copying this doc's current wording verbatim would propagate the staleness into the new guide.

Also L86 has the `get_flag()` vs `get_flag_mode()` staleness noted above.

### `docs/engine/known_limitations.md` §1.5 (lines 32-64)
Exact current text confirmed accurate: lists all 10 flags correctly (matches source exactly), states the default-OFF policy, references the `overrides` constructor arg and `set_flag_mode()`, cites `_build_kernel(enable_routing=True)` in `test_balance_regression.py` as the canonical opt-in pattern, states the "do not change default without re-running `tools/balance_measure.py`" rule, names the sentinel test `test_adventure_routing_defaults_off()`, and closes with a citation to `docs/guidelines/intentional_divergences.md` § DEV-002 — **already using the correct non-`v2_` filename**. This section requires no correction; it is the accurate source the new guide should cite/link, not duplicate.

### `docs/guidelines/intentional_divergences.md` DEV-002 (lines 522-530)
Exact current text confirmed. Subsystem: Engine / Feature Rollout. States all 10 flags default OFF (correctly says "all 10 Phase 10 flags" — matches source), decision to keep OFF, rationale class **Stabilized**, required action for scenario/test authors, unblock condition (re-run `balance_measure.py` with the flag ON), verification path `tests/integration/scenarios/test_balance_regression.py::test_adventure_routing_defaults_off`, Status: ACTIVE. This entry is correct and complete; the ticket's plan to cite/link rather than duplicate it is the right call — no edits needed to DEV-002 itself.

### SimQ profile `feature_flags:` YAML convention (`config/simulation_quality/profiles/*.yaml`)
Confirmed by sampling: `default.yaml` and `dungeon_crawl.yaml` have no `feature_flags:` block (only `pillar_weights:`) — the block is optional. `urban_political.yaml` demonstrates the convention:
```yaml
pillar_weights:
  FACTION: 1.5
  ECONOMY: 1.5
  SOCIAL: 1.5
  COMBAT: 0.3

feature_flags:
  ENABLE_SOCIAL_COOPERATION: "ON"
  ENABLE_BELIEF_ASSIMILATION: "ON"
```
11 of the 15 profile files under `config/simulation_quality/profiles/` have a `feature_flags:` block (`frontier_extended.yaml`, `hero_guild_routing.yaml`, `swamp_border_world.yaml`, `frontier_marches.yaml`, `sandbox_world.yaml`, `generated_frontier_3_42.yaml`, `simq_routing_test.yaml`, `urban_political.yaml`, `highland_traverse.yaml`, `unit_selfmodel_pilot.yaml`, `frontier_living_world.yaml`, `unit_information_source.yaml`); `default.yaml` and `dungeon_crawl.yaml` (and others) omit it. Values are string-typed in YAML (`"ON"`, not `ON`).

### `tools/calibrate_simq.py::_load_profile_feature_flags()` (lines 44-64)
Reads `config/simulation_quality/profiles/{profile}.yaml`, returns `{}` if the file doesn't exist, otherwise `{str(k): str(v) for k, v in (raw.get("feature_flags") or {}).items()}` — coerces both keys and values to `str`, tolerant of a missing key. Exceptions are caught and logged as a warning, returning `{}`.

Consumption chain, confirmed by reading `_run_engine()` (L142-254): `main()` (L339) loads `profile_feature_flags` via `_load_profile_feature_flags(profile)`, passes it as `extra_flags` into `_run_engine()`. Inside `_run_engine`, a `_KNOWN_FLAGS` list (L187-193, matching the 10 real flag names) and `_parse_flag_value()` (L195-203, maps `"ON"/"TRUE"/"1"/"YES"` → `FeatureMode.ON`, `"STRICT"` → `FeatureMode.STRICT`, `"SHADOW"` → `FeatureMode.SHADOW`, anything else → `None`/ignored) are used to build `combined_flag_overrides`. **Precedence order, confirmed**: profile YAML values are applied first (L207-212, "lower priority"), then env-var overrides of the same flag names are applied second and win (L214-220, "higher priority — can override profile"). The combined overrides are injected via `dc_replace(state, feature_flags=existing)` (L222-226) onto the compiled `AuthoritativeState` before `Kernel` construction (L232) — this is a state-level override, separate from `FeatureFlagManager`/`RolloutProfileManager` construction paths entirely (no `FeatureFlagManager` instance appears anywhere in `calibrate_simq.py`).

### `docs/combat/rollout_hardening_rulebook.md`
Full file read (34 lines). Frontmatter: `layer: combat`, `authority: P1`, `audience: developer`. Describes `SimulationConfig.overhaul_features` gating 4 flags: `use_legality_v2`, `use_combat_interaction_v2`, `use_movement_model_v2`, `use_tactical_evaluator_v2`, each with a stated "legacy fallback" behavior, a "Safe Degradation Contract" (defaults should be `True`, fail-safe reversion, no toggling mid-run), and "Rollout Validation Criteria" tied to `docs/archive/combat/arena_regression_test_matrix.md`.

**Independently re-verified** (not just trusting the ticket's own claim): ran `grep -rn "overhaul_features\|SimulationConfig" src/` — zero matches. Ran `grep -rn "use_legality_v2\|use_combat_interaction_v2\|use_movement_model_v2\|use_tactical_evaluator_v2" src/` — zero matches. **Confirmed: this construct has no implementation anywhere in `src/`.** It is a distinct, differently-named flag family from `FeatureFlagManager`/`FeatureMode` (which uses `ENABLE_*` names and `FeatureMode` enum values, not `use_*_v2` booleans defaulting `True`). The ticket's Assumption/finding on this point is correct and independently reproduced.

### `docs/README.md` Developer Guides table (lines 198-211)
Confirmed exact current format — 7 rows, each `[guides/{name}.md](guides/{name}.md) | one-line description`: `simulation.md`, `observability.md`, `testing.md`, `simulation_quality.md`, `content_authoring.md`, `bounded_cognition_tuning.md`, `agent_monitoring.md`. New row for `guides/feature_flags.md` should follow the identical `| [guides/feature_flags.md](guides/feature_flags.md) | <one-line description> |` pattern.

### Structural reference guides
`docs/guides/simulation_quality.md` frontmatter: `title`, `layer: observability`, `authority: P1`, `audience: developer`, `tags: [simq, quality, observability, guide]` — **note this uses a `title:` field and lacks `status:`**, which differs from the doc frontmatter schema shown in `docs/README.md` (`status`/`layer`/`authority`/`tags`/`last_verified`). `docs/guides/observability.md` has the identical pattern (`title`, `layer`, `authority`, `audience`, `tags`, no `status`). Both open with a one-line description + "For the authoritative spec, see..." link pattern, then a "What X does" section, then practical how-to sections. The new guide should follow this guides/ convention (title + layer/authority/audience/tags, no status field) rather than the generic doc frontmatter shown in README's schema block — **this is a divergence worth flagging** since `validate_frontmatter.py` is content-type-inferred from path and may enforce a specific field set for `docs/guides/*.md`; confirmed by inspecting existing files that `status` is absent and validation still presumably passes for them (they're existing, presumably-valid files in the tree).

### Stale citation grep confirmation
Exact occurrence counts and lines (re-verified independently via `grep -n`):
- `CLAUDE.md`: 2 occurrences — line 227 (`## Authoritative Mechanics Rule` / "Divergence" bullet) and line 285 (`### Intentional Divergences — ` heading).
- `docs/plans/audit_fix_plan.md`: 2 occurrences — line 55 and line 480.
- `docs/plans/idea_simq_near_perfect_roadmap.md`: 1 occurrence — line 246.
- `docs/audits/D06_longrun_health.md`: **0 occurrences** — confirmed the ticket's claim that this file does NOT contain the stale citation; it is correctly excluded from scope.

### Prior tickets (`tickets/done/`)
Both confirmed present and read in full:
- `TCK-20260627-P0A-ADVENTURE-FLAG` (hotfix, P0, DONE) — originated the DEV-002 decision, added `known_limitations.md` §1.5, added DEV-002, added `INFRA-221` to `docs/parity_ledger/infrastructure.yaml`. Its own "Implementation Notes" independently states "all 10 flags" (not 7), consistent with source.
- `TCK-20260627-P2E-FEATURE-FLAG-TEST` (standard, P2, DONE) — added `tests/integration/test_scenario_feature_flag_defaults.py` (45 tests across 9 functions), confirmed all 10 flags OFF by default across 14 scenario definitions, updated `INFRA-221`'s test_path.

## Mechanics / Engine Constraints
This is a documentation-only ticket with no behavior change — no Mechanics Bible chapter or Engine Contract directly constrains the *content* of a new guide. The one relevant constraint is `docs/engine/known_limitations.md` §1.5's own rule: **"Do not change the default to `ON` without first re-running `tools/balance_measure.py`"** — the new guide must not imply or suggest changing any flag default; it documents the existing OFF-by-default policy, it does not revisit or challenge it. `optimization_contract.md`'s own "Constraints" section (L126-132) states `FeatureFlagManager` flag values "must not be changed after kernel initialization — flags are set once per run" — this constraint should be carried into the new guide's description of the `FeatureMode`/flag system, since it governs correct usage (e.g., the `calibrate_simq.py` override-before-`Kernel()`-construction pattern found above depends on it).

## Parity Ledger Overlap
- `docs/parity_ledger/infrastructure.yaml::INFRA-221` — status `verified`, priority **P1** (not P0). Text and `v2_evidence` (`src/domains/optimization/feature_flags.py:13-24`) both accurately describe the current 10-flag-OFF-default state; no update required by this ticket since no behavior changes.
- A companion `infrastructure.yaml` entry (visible in the grep context, unlabeled ID captured mid-block, immediately follows INFRA-221 in file order) covers `config/simulation_quality/profiles/<world>.yaml` calibration-profile flag overrides via `_load_profile_feature_flags()` — explicitly stated as "Companion to INFRA-221, not a duplicate." This is the SimQ profile mechanism the new guide's Scope bullet 4 covers; worth citing in the guide as the parity evidence for that mechanism, though not required to be edited.
- No P0 parity ledger entries were found overlapping this ticket's scope (`INFRA-221` is P1). **Confirms the ticket's own claim of no parity ledger impact.**
- Both `infrastructure.yaml` and `social_narrative.yaml` citations of `intentional_divergences.md` (spot-checked via grep) already use the correct non-`v2_` filename — confirms the ticket's Out of Scope claim that no ledger edit is needed for the filename fix either.

## Prior Work
- `TCK-20260627-P0A-ADVENTURE-FLAG` and `TCK-20260627-P2E-FEATURE-FLAG-TEST` — read in full above; both confirm the 10-flag, OFF-default, DEV-002 history the new guide will consolidate. No conflicting information found.
- `TCK-20260701-SIMQ-AGENCY-ROUTING-DOC` (hotfix, P2, DONE, tags include `documentation`, `feature-flag`) — a closed investigation confirming AGENCY zero-score in SimQ was a legitimate consequence of `ENABLE_ADVENTURE_ROUTING` defaulting OFF (not a bug), tracing the same `feature_flags.py:16` → `adventure/phase.py` → `pipeline.py` gating chain. Not a documentation-consolidation attempt itself, but corroborates the default-OFF policy's real behavioral consequences — useful supporting context for the new guide's "why OFF matters" framing, not required reading for scope compliance.
- Registry query (`docs/REGISTRY.yaml`, 1352 entries) for `related_code_areas` overlapping `feature_flags.py`/`rollout_profiles.py`/`calibrate_simq.py` or `tags` containing `feature-flags` surfaced ~20 SimQ calibration/corpus tickets (e.g. `TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL`, `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE`) — all are behavioral/calibration work reading or asserting on flag state, not documentation-consolidation attempts. None conflict with or duplicate this ticket's scope. Confirms the ticket's own "Related Stored Artifacts: None found" claim for documentation-consolidation precedent specifically.

## Risks and Open Questions
1. **`optimization_contract.md` line 86 `get_flag()` vs actual `get_flag_mode()`** — a second stale API-name citation in the same "FeatureFlagManager" section the ticket is already editing for the flag-count fix. Not named in Acceptance Criteria #5 (which only covers the "Known Flags" table). **Open question for Plan**: fix this too while already editing this section (low-cost, same file, same section), or leave out-of-scope per the ticket's literal AC wording? Flagging rather than assuming — the ticket's own Out of Scope section doesn't mention this specific line, so it may simply not have been noticed during Scope.
2. **`optimization_contract.md` "RolloutProfiles" section (L114-116) describes a "development/staging/production/benchmark" profile model that does not match the actual `HardwareClass` (`CLASS_A`/`CLASS_B`/`CLASS_C`) implementation.** This is adjacent staleness in the same doc, in the exact section (`RolloutProfiles`) the new guide's Scope bullet 5 needs to describe accurately. If the new guide's `RolloutProfile`/`HardwareClass` section is written by copying this doc's current wording, the staleness propagates. Recommend Plan treat this as: the new guide describes the real `CLASS_A`/`CLASS_B`/`CLASS_C` structure from source (already done accurately in this investigation's Current Behavior section above), independent of whatever `optimization_contract.md`'s prose currently says — not silently copy it. Whether `optimization_contract.md`'s own prose is also corrected is a scope call for Plan (ticket's AC #5 only requires the *table* fixed, not this prose paragraph).
3. **`docs/guides/*.md` frontmatter convention diverges from `docs/README.md`'s stated doc-frontmatter schema** (title instead of/without status; no `status:` field on either sampled guide). If Plan copies the generic `docs/` schema from README instead of matching the actual `guides/` convention, `validate_frontmatter.py` may reject it, or may silently accept a schema the rest of `guides/` doesn't follow. Recommend Plan match the two sampled files' actual field set exactly, not README's generic schema block, and run `validate_frontmatter.py` against the new file before considering AC #6 satisfied.
4. **Layer choice (`engine` vs `ai`)** — the ticket's own Assumptions section already flags this as open (engine chosen to match `known_limitations.md`; `optimization_contract.md` itself uses `layer: ai`). Not resolved by this investigation; a reviewer/Plan-stage decision, not a fact-finding gap.
5. `RolloutProfileManager` has no method to actually *apply* a `RolloutProfile`'s `enabled_phases`/`shadow_phases` to a `FeatureFlagManager` instance (no `activate()`/`apply_profile()` — see Current Behavior). If the new guide's activation-matrix section implies profiles are "used by `FeatureFlagManager` initialization" (as `optimization_contract.md` L116 currently states), that overstates what the code does — `RolloutProfileManager.__init__` only constructs a throwaway `FeatureFlagManager()` to validate flag names, and no shipped runtime path was found (via the `calibrate_simq.py`/config profile flow) that actually consumes `RolloutProfile.enabled_phases`/`shadow_phases` to construct a live `FeatureFlagManager`. Recommend the guide state this precisely: `RolloutProfile` objects are declarative rollout-tier descriptors, not an automatic wiring mechanism into a running `FeatureFlagManager`.

## Anti-Drift Hazards
- **Do not "fix" the flag count by changing `src/domains/optimization/feature_flags.py`.** This ticket is documentation-only (ticket Out of Scope, confirmed correct — no source changes needed; the doc is what's wrong, not the code).
- **Do not fold `rollout_hardening_rulebook.md`'s `overhaul_features`/`use_*_v2` content into the new guide as if it's the same system.** Confirmed independently: zero implementation in `src/`. A cross-reference with an explicit "distinct, unimplemented-as-of-this-writing" caveat is correct; presenting it as part of the same flag matrix would misinform future readers.
- **Do not silently "correct" `optimization_contract.md`'s `RolloutProfiles`/`get_flag()` staleness beyond what AC #5 requires** without flagging the scope decision (see Risks #1, #2) — either explicitly include it in Plan's scope with rationale, or explicitly leave it and note it as a known residual gap, so a future doc-parity pass isn't surprised to find it.
- **Do not duplicate DEV-002's full rationale/unblock-condition text into the new guide.** Ticket Scope explicitly requires cite-by-link, not duplication — duplication risks the two copies drifting out of sync on a future default-policy change.
- **Editing `CLAUDE.md`, `docs/plans/audit_fix_plan.md`, `docs/plans/idea_simq_near_perfect_roadmap.md` for the citation fix must touch only the exact `v2_intentional_divergences.md` → `intentional_divergences.md` string** — confirmed exact line numbers above (CLAUDE.md:227,285; audit_fix_plan.md:55,480; idea_simq_near_perfect_roadmap.md:246) so Implement can target them precisely without touching unrelated content on those lines.
- **`docs/audits/D06_longrun_health.md` must remain untouched** — confirmed 0 matches; any edit to this file is out of scope per the ticket and this investigation's independent re-verification.
- Since `docs/` files are created/modified, `make knowledge-index-update` must run and `docs/REGISTRY.yaml` must be regenerated and staged at close, per the standing project rule — already correctly named in the ticket's Scope (last bullet) and AC #7.
