---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260831-CAPABILITY-DRIVEN-TARGETING
artifact_type: plan
tags: [cognition, combat]
---

# Implementation Plan — TCK-20260831-CAPABILITY-DRIVEN-TARGETING

## Summary

Wire an ad-hoc, read-only `CapabilityEstimateService.estimate()` call into
`TacticalDecisionSystem.target_score()` (`src/engine/tactical.py:394-426`), mirroring the exact
call-site pattern already landed by the precedent ticket
(`src/domains/adventure/scoring.py:289-297`, confirmed by reading the file directly). For each
candidate hostile `h`, the acting `entity`'s own subjective combat capability against `h.kind` is
read via `CapabilityContext.for_combat(enemy_ids=[h.kind])` and inserted into the existing sort
tuple as a new field, **inverted-negated so a higher win-estimate makes the target more
attractive** (Decision 1, below). No `enemy_data` is reconstructed from any registry (Decision 2,
below) — `estimate()` already produces a real, differentiated result from its internal
`_ENEMY_DANGER` fallback table alone. `select_best_target()`, the post-sort COMB-254 legality
filter, and `capability_estimate.py`/`self_model_phase.py` internals are untouched. A new parity
ledger entry `COMB-316` is added to `docs/parity_ledger/combat_movement.yaml` documenting
`target_score()`'s full formula for the first time (no prior entry exists to extend). Four doc
files get the fan-out update the investigation already scoped exactly (`tactical_contract.md`,
`intentional_divergences.md`, `capability_and_knowledge_contract.md`, `cognition/README.md`).

## Design Decisions (resolving investigation.md Risks 1 and 4)

### Decision 1 — Polarity and tuple placement

**A high capability estimate makes a target MORE attractive (higher priority), not less.**
Reasoning: the ticket's own framing (`## Scope`, `## Acceptance Criteria` AC1) describes this as
"a real value" added *alongside* HP/distance/trust as a prioritization signal, not a caution
signal — real RPG tactical logic has an entity press the fight it believes it can win, not avoid
it. This also keeps the term consistent in spirit with `group_bias`/`is_current_target`
(lower-is-more-urgent convention): the new field is `-capability_estimate` (negated), so a higher
raw `estimate` (0.0-1.0, per `capability_estimate.py:132-137` — `raw_estimate = round(min(1.0,
max(0.0, raw_estimate)), 4)`) produces a *lower* (more prioritized) tuple value, matching the
tuple's existing ascending-sort-wins convention (`tactical.py:431`,
`hostiles.sort(key=target_score)`).

**Tuple placement: inserted as a new 3rd field**, between `is_current_target` and `h.combat.hp`:

```python
return (group_bias, is_current_target, -capability_confidence, h.combat.hp, dist * pressure_dist_mod, h.id)
```

Placement reasoning: `group_bias` (focus-fire discipline) and `is_current_target` (hysteresis,
avoids target-flip-flop) are both existing *stability/cohesion* signals the ticket's Out-of-Scope
section protects — they must keep outranking the new term so this ticket cannot regress
COMB-270/COMB-271 (target stickiness) or SOC-185 (focus-fire discipline) behavior. `h.combat.hp`
and `dist*pressure_dist_mod` are the two purely reactive/tactical terms AC1 explicitly names
("instead of purely HP/distance/trust") — placing the new term immediately before them means it is
consulted before HP/distance but only after group cohesion and hysteresis are already satisfied,
i.e., "when the group and my own recent target don't already dictate a choice, prefer a fight I
believe I can win, then fall back to HP/distance/id." This is a genuine new discriminator, not a
tie-breaker buried after `h.id`.

### Decision 2 — No `enemy_data` reconstruction (scope guard)

**`CapabilityContext.for_combat(enemy_ids=[h.kind])` is called with no `enemy_data` argument.**
`EnemyDef` (`src/core/registries.py`) stores `danger_hint: str` (e.g. `"MEDIUM"`), not a numeric
`danger_rating`, and no string→float mapping utility exists anywhere in the repo (investigation.md
Risk 4, grep-confirmed). `capability_estimate.py:126-127` already falls back to
`_ENEMY_DANGER.get(enemy_id, 0.5)` internally when `enemy_data` is empty, producing a real,
entity-stat-driven, differentiated estimate with zero registry reads. Reconstructing `enemy_data`
would require importing `EnemyRegistry` into `tactical.py` (currently imports no registry module —
confirmed via `grep -n "^from\|^import" src/engine/tactical.py`, lines 4-18, no registry import
present) and inventing a new hint→float mapping with no existing precedent — both would break the
no-registry-reads, minimal-plumbing pattern the precedent ticket established
(`stored_artifacts/TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING/plan.md` Design Decision
4) and widen this ticket's blast radius well past its scope. **This is a hard scope guard, not an
optimization deferred to later**: do not add `EnemyRegistry`/`EnemyDef`/any registry import to
`tactical.py` under this ticket.

## Steps

### Step 1 — Import capability-estimate types into tactical.py

**Files:** `src/engine/tactical.py`

**Change:** Add two imports near the existing `src/engine/...`/`src/core/...` import block
(`tactical.py:11-18`):
```python
from src.cognition.capability_estimate import CapabilityEstimateService, CapabilityContext
```
No other import changes. Confirmed current import block ends at `tactical.py:18`
(`from src.engine.rpg_depth import WoundService`) with no existing capability-estimate import
(grep-confirmed, zero hits for `CapabilityEstimate` in the file per investigation.md).

**Do NOT touch:** Any other import line; do not add `src.core.registries` (Decision 2).

**Verify:** `python3 -c "import src.engine.tactical"` succeeds with no `ImportError`; no test
change needed for this step alone (covered implicitly by every test in Step 2's Verify).

### Step 2 — Wire the ad-hoc `CapabilityEstimateService.estimate()` call inside `target_score()`

**Files:** `src/engine/tactical.py` (function `target_score`, currently `tactical.py:394-426`)

**Change:** Inside the `target_score(h: EntityState)` closure, after the existing `dist = ...`
line (`tactical.py:395`) and before the `group_bias` block (`tactical.py:397`), or anywhere before
the `return`, add:

```python
cap_component = CapabilityEstimateService.estimate(
    entity,
    context=CapabilityContext.for_combat(enemy_ids=[h.kind]),
)
cap_estimate = cap_component.estimates.get(f"combat.enemy_type.{h.kind}")
capability_confidence = cap_estimate.estimate if cap_estimate is not None else 0.0
```

Then change the `return` line (`tactical.py:426`) from:
```python
return (group_bias, is_current_target, h.combat.hp, dist * pressure_dist_mod, h.id)
```
to:
```python
return (group_bias, is_current_target, -capability_confidence, h.combat.hp, dist * pressure_dist_mod, h.id)
```

Update the function's type annotation from `Tuple[float, int, float, int, int]`
(`tactical.py:394`) to `Tuple[float, int, float, float, float, int]` (6 fields now; `h.combat.hp`
and `dist*pressure_dist_mod` are floats, matching existing usage — the pre-existing annotation
`Tuple[float, int, float, int, int]` was already slightly imprecise about `h.combat.hp`/`dist`
being floats, but this plan only adds the one new field's type, `float`, without otherwise
"fixing" the pre-existing imprecision beyond what's needed to keep the annotation internally
consistent).

**Enemy-id source**: `h.kind`, not `get_race_id_str(h)` — confirmed in investigation.md
(`src/core/state.py:669`, `EntityState.kind: str`, always populated vs.
`IdentityComponent.properties` defaulting to `{}` at `src/core/state.py:490`, making
`get_race_id_str()` return `None` for nearly every fixture).

**Call-site pattern citation**: mirrors `src/domains/adventure/scoring.py:289-297` exactly (read
directly to confirm shape) — `CapabilityEstimateService.estimate(entity, context=CapabilityContext(...))`
then `.estimates.get(f"<domain-key>")`, `None`-guarded before use. The only difference here is
`CapabilityContext.for_combat(enemy_ids=[h.kind])` (a classmethod, `capability_estimate.py:49-51`)
instead of hand-building `CapabilityContext(gather_resources=(...), resource_data=...)`, since the
combat branch needs no `enemy_data`.

**Other writers to `target_score`'s output / the `hostiles` list this closure feeds**: `target_score`
itself is a pure local closure with no external readers except `hostiles.sort(key=target_score)`
(`tactical.py:431`, unchanged by this step) and the debug-logging loop immediately above it
(`tactical.py:429-430`, `logger.debug(f"DEBUG: target {h.id} score: {target_score(h)}")` — this
already calls `target_score(h)` a second time per hostile for logging; this step does not change
that double-call pattern, and `CapabilityEstimateService.estimate()` is stateless/deterministic per
its own docstring (`capability_estimate.py:6-7`, "Stateless, deterministic, read-only"), so the
debug-log's extra call produces identical results with no side effects, no double-counting, and no
ordering hazard). No other writer touches `hostiles` or `target_score` between definition
(`tactical.py:394`) and the sort (`tactical.py:431`).

**Do NOT touch:** `group_bias`, `is_current_target`, `pressure_dist_mod` computation logic
(unchanged, per investigation.md Anti-Drift Hazards); `select_best_target()`
(`tactical.py:819-836`, separate method); the debug-logging block itself beyond what naturally
follows from `target_score`'s new return shape (no separate edit needed there — it already just
prints whatever `target_score` returns).

**Verify:** New tests 1-4, 6, 7 from `test_plan.md` (`tests/unit/combat/test_capability_driven_targeting.py`,
not yet created — created in Step 3) plus full regression run:
```
.venv/bin/python3 -m pytest tests/unit/combat/ tests/unit/tactical/ tests/unit/movement/test_tactical_movement.py tests/unit/movement/test_mob_leashing.py -v
```

### Step 3 — Add the new test file

**Files:** `tests/unit/combat/test_capability_driven_targeting.py` (new)

**Change:** Implement all 7 tests specified in `test_plan.md` under "New Tests Required":
1. `test_target_score_reflects_capability_estimate_for_differentiated_enemy_kinds`
2. `test_target_score_unaffected_when_all_hostiles_share_the_same_kind`
3. `test_target_score_capability_estimate_derived_from_acting_entitys_own_stats`
4. `test_target_score_does_not_mutate_entity_self_model`
5. `test_comb254_legality_filter_still_runs_after_capability_scored_sort`
6. `test_target_score_reads_only_entity_owned_and_hostile_kind_data`
7. `test_target_score_capability_signal_is_deterministic`

Each test's exact assertions are specified in `staging_artifacts/TCK-20260831-CAPABILITY-DRIVEN-TARGETING/test_plan.md`
(section "New Tests Required", items 1-7) — implement against the actual tuple shape from Step 2
(`(group_bias, is_current_target, -capability_confidence, h.combat.hp, dist*pressure_dist_mod,
h.id)`), not a hardcoded index assumption; assert on directional/behavioral outcome (does
differentiated `.kind()` change sort order; does same-`.kind()` leave order unchanged) rather than
peeking at internal tuple values where practical, per `test_plan.md`'s own framing ("tests below
assert on the *presence and directionality* of the new signal's effect, not a hardcoded tuple
index"). For test 1, use `.kind("goblin")` vs `.kind("dragon")` (both `_ENEMY_DANGER`-known,
`capability_estimate.py:59-66`, danger `0.5` vs `0.95` — a large enough spread to reliably flip
ordering at identical HP/distance/group-bias). For test 5, construct a scenario where the
capability-preferred candidate is positioned to fail `LegalityServiceV2.verify_attack_legality()`
(e.g., out of weapon range) while a lower-scored candidate is legal, and assert the final acted-on
target is the legal one.

**Do NOT touch:** `tests/unit/combat/test_target_selection_contract.py` (guards
`select_best_target()`, untouched by this ticket); any existing test file in the Regression
Surface list of `test_plan.md`.

**Verify:**
```
.venv/bin/python3 -m pytest tests/unit/combat/test_capability_driven_targeting.py -v
```
All 7 new tests pass.

### Step 4 — Run full regression surface and confirm capability-estimate/self-model tests are byte-unchanged

**Files:** none (verification-only step; touches no source)

**Change:** Run all four scoped pytest commands from `test_plan.md`:
```
.venv/bin/python3 -m pytest tests/unit/combat/ tests/unit/tactical/ tests/unit/movement/test_tactical_movement.py tests/unit/movement/test_mob_leashing.py -v
.venv/bin/python3 -m pytest tests/unit/cognition/test_phase2_capability_estimate_service.py tests/unit/cognition/test_phase2_self_model_phase.py -v
.venv/bin/python3 -m pytest tests/unit/social/test_domain_7_social.py tests/unit/core/test_read_only_guard.py -v
.venv/bin/python3 -m pytest tests/integration/combat/test_relation_combat_integration.py tests/integration/strategic/test_occupation_change_reachability.py tests/integration/scenarios/test_phase2_self_model_scenarios.py -v
```
Additionally confirm via `git diff --stat src/cognition/capability_estimate.py
tests/unit/cognition/test_phase2_capability_estimate_service.py` that both files show **zero**
diff lines (AC3's "existing ... unit tests pass unchanged" literally, per `test_plan.md`'s New
Test 8 framing, not just "still green").

**Do NOT touch:** `src/cognition/capability_estimate.py`, `src/cognition/self_model_phase.py` —
neither file is modified by this plan at all (Step 1-3 touch only `tactical.py` and the new test
file).

**Verify:** All four commands pass with zero new failures; the `git diff --stat` check above shows
no changes to `capability_estimate.py` or its existing test file.

### Step 5 — Add parity ledger entry COMB-316

**Files:** `docs/parity_ledger/combat_movement.yaml`

**Change:** `combat_movement.yaml` currently ends at `id: COMB-315` (`combat_movement.yaml`, last
entry, confirmed via `grep -n "^- id: COMB-" docs/parity_ledger/combat_movement.yaml | sed -E
's/.*COMB-([0-9]+).*/\1/' | sort -n | tail -1` → `315`). Append a new entry with the next
sequential ID, `COMB-316`, following the exact field shape of the immediately preceding entries
(e.g. `COMB-315`, which documents the sibling wound/scar tactical-wiring ticket in the same file):

```yaml
- id: COMB-316
  text: Tactical target-selection sort (TacticalDecisionSystem.target_score()) incorporates a
    subjective capability-estimate signal -- an entity that reads itself as more capable of
    beating a specific hostile kind prioritizes that hostile higher, ahead of raw HP/distance but
    behind group focus-fire bias and target-selection hysteresis.
  status: verified
  priority: P2
  legacy_evidence: null
  v2_evidence: TacticalDecisionSystem.target_score() (src/engine/tactical.py:394-426, before this
    ticket carried no CapabilityEstimateService/CapabilityContext reference at all -- confirmed
    zero hits via repo-wide grep) now calls CapabilityEstimateService.estimate(entity,
    context=CapabilityContext.for_combat(enemy_ids=[h.kind])) per candidate hostile and folds the
    resulting combat.enemy_type.<kind> estimate into the sort tuple as
    -capability_confidence, negated so a higher subjective win-estimate yields higher target
    priority. Ad-hoc, call-site-local, read-only -- entity.self_model.capabilities.estimates
    remains empty in production (SelfModelUpdatePhase.apply() still never passes
    capability_context=, unchanged by this ticket). Landed in
    TCK-20260831-CAPABILITY-DRIVEN-TARGETING.
  proof_type: unit
  test_path: tests/unit/combat/test_capability_driven_targeting.py
  divergence_note: null
  support_boundary: null
```

Use `priority: P2` (not P0) — this is a new prioritization heuristic, not a legality/conservation
invariant like the adjacent COMB-254/SOC-185 P0 entries; it does not gate correctness, only sort
ordering among already-legal candidates. Use the project's YAML-writing tooling
(`tools/parity_ledger_writer.py`) rather than a raw `Edit` to the YAML file if available, per
CLAUDE.md memory guidance on avoiding ad-hoc full-file YAML rewrites — a targeted `Edit` appending
one entry block is acceptable if the tool path is unavailable, since this is a single-entry
append, not a full-file rewrite.

**Other writers to this file**: `tools/parity_ledger_writer.py` is the sanctioned writer; other
tickets append entries to this same file over time (most recently `COMB-314`/`COMB-315` from
`TCK-20260824-WOUND-PENALTY-FORMULA-WIRING`/`TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`) but never
concurrently within a single ticket's implementation — append at the end of the file, after
`COMB-315`, to avoid any merge collision with those already-landed entries.

**Do NOT touch:** `COMB-254`, `SOC-185`, or any other existing entry's `status`/`v2_evidence`/
`test_path` fields — this ticket does not change their formulas, only adds a new, previously
undocumented one (investigation.md "Parity Ledger Overlap" confirms no existing entry covers
`target_score()`'s formula).

**Verify:** `python3 tools/parity_ledger_writer.py validate` (or equivalent schema check per
`docs/parity_ledger/schema.json`) passes; `test_path` points at a real, passing test file (Step 3's
new file, confirmed passing in Step 3's Verify).

### Step 6 — Update the four docs identified by investigation.md's "Docs Requiring Update"

**Files:**
- `docs/engine/contracts/tactical_contract.md` (§2 "Target Selection Rules (GAP-T01)")
- `docs/guidelines/intentional_divergences.md` (§2.6 "Priority-Based Tactical Targeting")
- `docs/cognition/capability_and_knowledge_contract.md` (new sibling section/paragraph after the
  existing "How adventure routing uses capability estimates" section, ~lines 75-77)
- `docs/cognition/README.md` ("Relationship to other subsystems" table, ~lines 69-77 — new row for
  `src/engine/tactical.py`/`TacticalDecisionSystem`)

**Change:**
- `tactical_contract.md` §2: extend the documented priority chain from "Lowest HP > Closest
  Distance > Lowest Entity ID" to the actual current chain (group focus-fire bias > hysteresis >
  capability-driven signal > HP > pressure-scaled distance > ID), stating plainly that hostiles
  resolve into `CapabilityContext.combat_enemies` via `h.kind` and that a higher subjective
  win-estimate raises priority (cite Decision 1's polarity explicitly). Note in the same edit that
  this section was already stale before this ticket (omitted `group_bias`/`is_current_target`/
  `pressure_dist_mod`) — this ticket brings it fully current, not just adds one more line to an
  already-accurate doc.
- `intentional_divergences.md` §2.6: update "New Behavior" to describe the capability-driven
  addition, with a rationale class of **Intentional Gameplay Change** (a deliberate new
  prioritization heuristic, not a bug fix or hardening of an existing rule). Point "Verification"
  at `tests/unit/combat/test_capability_driven_targeting.py` (Step 3's new, real, passing file)
  instead of the currently-dead `tests/parity/test_tactical_parity.py` reference — investigation.md
  confirms that file does not exist; fixing this dead pointer for §2.6 specifically (the entry this
  ticket is editing anyway) is in scope, but do not go create/fix `tests/parity/test_tactical_parity.py`
  itself or touch any other divergence-log entry that also cites it (out of scope — see Scope
  Guards).
- `capability_and_knowledge_contract.md`: add a new paragraph mirroring the existing adventure-
  routing paragraph's disclosure style exactly — state that `TacticalDecisionSystem.target_score()`
  now makes an ad-hoc `CapabilityEstimateService.estimate()` call (combat domain only, via
  `h.kind`), and that `entity.self_model.capabilities.estimates` remains empty in production either
  way (`SelfModelUpdatePhase.apply()` still never passes `capability_context=`).
- `README.md`: add one new row to the "Relationship to other subsystems" table for
  `src/engine/tactical.py`/`TacticalDecisionSystem`, matching the existing `src/domains/adventure/`
  row's exact disclosure style (ad-hoc call, not via `entity.self_model.capabilities`).

**Do NOT touch:** `docs/mechanics/04_strategic_cognition.md` (confirmed by investigation.md to be
a keyword-adjacency mismatch, not an actual dependency — zero mentions of `TacticalDecisionSystem`/
`target_score`/`tactical.py` anywhere in that file); `docs/mechanics/02_combat_laws.md` §2
(documents pre-damage tactical modifiers, a different mechanism); `docs/simulation/domains/
combat_engagement_contract.md` (documents `src/domains/combat_engagement/`, a different subsystem);
`docs/compliance/checklist.md` (registering a new Logic ID there is explicitly not required by any
AC — investigation.md Risk 6 flags this as a judgment call and this plan declines to add one, since
`COMB-316` in the parity ledger already gives the change a durable, traceable identifier without
needing a second, checklist-specific ID).

**Verify:** Manual read-through confirming each doc's new/updated text accurately describes Step 2's
actual implementation (tuple position, polarity, `h.kind` as enemy-id source, no `enemy_data`). If
any file under `docs/` changed, run `make knowledge-index-update` per CLAUDE.md's "After Work"
rule.

## Scope Guards

- Do not modify `select_best_target()` (`tactical.py:819-836`) or its own `(hp, dist, id)` tuple —
  separate method, separate test (`tests/unit/combat/test_target_selection_contract.py`), out of
  scope.
- Do not modify the post-sort legality filter (`tactical.py:433-443`, COMB-254) or its ordering
  relative to the sort. The capability signal only changes which candidate is tried first; it must
  never bypass `LegalityServiceV2.verify_attack_legality()`.
- Do not write back to `entity.self_model` (or any other durable entity field) from inside
  `target_score()` or `evaluate_entity_intent()`. The `CapabilityEstimateService.estimate()` result
  is a local, throwaway, per-candidate scoring input only.
- Do not modify `src/cognition/capability_estimate.py` or `tests/unit/cognition/
  test_phase2_capability_estimate_service.py` — AC3 requires these byte-unchanged (verified in
  Step 4).
- Do not modify `src/cognition/self_model_phase.py` or attempt to fix `SelfModelUpdatePhase.apply()`'s
  never-passes-`capability_context=` gap — explicitly out of scope, matching the precedent ticket.
- Do not add `EnemyRegistry`/`EnemyDef`/any other registry import to `tactical.py`, and do not
  reconstruct a numeric `danger_rating`/`enemy_data` dict from any source — Decision 2 above; the
  no-`enemy_data` call shape is a hard requirement of this plan, not a placeholder.
- Do not use `get_race_id_str(h)` as the enemy-id source for `CapabilityContext.for_combat()` — use
  `h.kind` only (Decision documented in investigation.md, restated in Step 2).
- Do not change `group_bias`, `is_current_target`, or `pressure_dist_mod`'s own computation logic —
  this ticket adds one new tuple field; it does not touch the existing terms.
- Do not register a new Logic ID in `docs/compliance/checklist.md` — `COMB-316` in the parity
  ledger is the durable identifier for this change; investigation.md Risk 6 leaves this as a
  judgment call and this plan declines it.
- Do not create `tests/parity/test_tactical_parity.py` or fix any *other* divergence-log entry that
  cites it — only §2.6's own "Verification" pointer (the entry this ticket is directly editing) is
  redirected to the new real test file.
- Do not touch `COMB-254`, `SOC-185`, or any other pre-existing parity ledger entry's fields.

## Dependency Map

- Step 1 (imports) must land before Step 2 (call-site wiring) — Step 2 uses the imported names.
- Step 2 (implementation) must land before Step 3 (tests) — tests assert against the real return
  shape.
- Step 3 (new tests) must land before Step 4 (full regression + byte-diff confirmation) — Step 4's
  first pytest command includes the new test file's directory.
- Step 5 (parity ledger entry) depends on Step 3's test file existing and passing — its
  `test_path` must point at a real, green test.
- Step 6 (docs) depends on Step 2's actual implementation shape (tuple position/polarity) being
  final — docs describe what Step 2 actually built, not a plan-time guess.
- Steps 1-4 are otherwise independent of Steps 5-6; Steps 5 and 6 can proceed in either order or in
  parallel once Step 3 is green.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: For a hostile mapped into `CapabilityContext.combat_enemies`, `target_score()`'s priority reflects a real `CapabilityEstimateService.estimate(...).combat.enemy_type` value instead of purely HP/distance/trust. | Step 2 | `test_target_score_reflects_capability_estimate_for_differentiated_enemy_kinds`, `test_target_score_capability_estimate_derived_from_acting_entitys_own_stats` |
| AC2: The `capability_context`-never-populated prerequisite is explicitly disclosed and resolved via an ad-hoc call-site-local `CapabilityContext` inside `tactical.py`, mirroring the precedent ticket. | Step 2 (implementation), Step 6 (disclosure in docs) | `tests/unit/cognition/test_phase2_self_model_phase.py` (unchanged, confirms `capability_context` still defaults to `None` in production) |
| AC3: `target_score()` stays read-only — no write-back into `entity.self_model`, existing `CapabilityEstimateService` unit tests pass unchanged. | Step 2 (no write-back), Step 4 (byte-diff confirmation) | `test_target_score_does_not_mutate_entity_self_model`; `tests/unit/cognition/test_phase2_capability_estimate_service.py` (byte-unchanged) |
| AC4: COMB-254's post-sort legality filter still runs unchanged after the re-scored sort. | Step 2 (filter code untouched) | `test_comb254_legality_filter_still_runs_after_capability_scored_sort` |

## Anti-Drift Notes

- Every existing `tactical.py` test fixture uses a uniform hostile `.kind(...)` value, so the new
  signal is a provable constant (no-op on ordering) across all pre-existing regression tests —
  `test_target_score_unaffected_when_all_hostiles_share_the_same_kind` (Step 3, test 2) is the
  concrete guard proving this; if it fails, the implementation is reading something other than
  `h.kind`/entity-owned stats and has drifted from Decision 2's scope.
- `CapabilityEstimateService.estimate()` is stateless and deterministic
  (`capability_estimate.py:6-7`); the existing debug-logging loop
  (`tactical.py:429-430`) already calls `target_score(h)` a second time per hostile purely for
  logging — this means the capability-estimate call happens twice per hostile per tick after this
  change (once for the debug log, once for the real sort). This is not a correctness bug (no side
  effects, deterministic, cheap stat-comparison math) but is worth flagging so a future performance
  pass isn't surprised by the doubled call count; not something to "fix" under this ticket since it
  pre-dates this ticket's change and touching the debug-log call pattern is not in scope.
- `entity.self_model.capabilities.estimates` remains empty in production after this ticket ships —
  every doc update in Step 6 and the Completion Summary must state this plainly, never imply the
  upstream gap was fixed.
- The parity ledger entry (`COMB-316`) is a brand-new entry, not an extension of an existing one
  (unlike the precedent's `STRAT-227` extension) — confirmed via investigation.md's "Parity Ledger
  Overlap" section, no existing entry documents `target_score()`'s formula at all.
- `docs/engine/contracts/tactical_contract.md` §2 and `docs/guidelines/intentional_divergences.md`
  §2.6 were both already stale *before* this ticket (missing `group_bias`/`is_current_target`/
  `pressure_dist_mod` documentation, and a dead `tests/parity/test_tactical_parity.py` reference,
  respectively) — Step 6 brings both fully current as part of this ticket's own doc-parity
  obligation, not as an unrelated drive-by fix.
