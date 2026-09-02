---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260831-CAPABILITY-DRIVEN-TARGETING
artifact_type: investigation
tags: [cognition, combat]
---

# Investigation — TCK-20260831-CAPABILITY-DRIVEN-TARGETING

## Current Behavior

### `TacticalDecisionSystem.target_score()` — `src/engine/tactical.py:394-426`
A closure defined inside `evaluate_entity_intent()` (`tactical.py:80-764`), used as the `key=` for
`hostiles.sort(key=target_score)` at `tactical.py:431`. Current tuple, sorted ascending (lowest
tuple wins → becomes the pre-legality-filter candidate target):

```python
return (group_bias, is_current_target, h.combat.hp, dist * pressure_dist_mod, h.id)
```

- `group_bias` (`tactical.py:397-411`, "Domain 7 Hardening"): `1.0` unless the group's
  `shared_target_id == h.id`, in which case it is derived from the acting entity's trust in the
  group leader (`(bond.sentiment + 1.0) / 2.0` or `trust_history`); `VANGUARD` role halves the bias
  further. Lower bias = higher priority (focus-fire bonus).
- `is_current_target` (`tactical.py:414`): `0` if `h.id` already equals the entity's current
  `task.payload["target_id"]` (local hysteresis bonus), else `1`.
- `h.combat.hp`: raw hit points — lower HP is prioritized ("finish off weak targets").
- `dist * pressure_dist_mod` (`tactical.py:416-426`): Manhattan distance scaled down by
  `territory_pressure`/`duty_pressure` (more pressure → effectively closer → more urgent).
- `h.id`: final deterministic tie-breaker.

**Confirmed zero `CapabilityEstimateService`/`CapabilityContext` references anywhere in
`src/engine/tactical.py`** — repo-wide grep for `CapabilityEstimate` and `CapabilityContext` inside
that file returns no hits. The ticket's framing is accurate: `target_score()` scores purely on
group-focus-fire bias, HP, distance, and ID — no subjective "can I actually beat this enemy" signal
is read at all.

After the sort, `tactical.py:433-443` (Logic ID **COMB-254**) filters `hostiles` (now sorted) down
to `legal_attack_targets` via `LegalityServiceV2.verify_attack_legality(entity, h, state)`, and picks
`legal_attack_targets[0]` if non-empty else `hostiles[0]`. This post-sort legality filter is
untouched by this ticket's scope (explicitly Out of Scope) — the capability signal only changes
which candidate reaches this filter first, never bypasses or reorders it.

### `CapabilityContext.for_combat()` / `CapabilityEstimateService.estimate()` — `src/cognition/capability_estimate.py`
- `CapabilityContext.for_combat(enemy_ids: List[str], enemy_data: Optional[Dict] = None)`
  (`capability_estimate.py:49-51`) is a `classmethod` returning
  `cls(combat_enemies=tuple(enemy_ids), enemy_data=enemy_data or {})` — exactly shaped for a
  caller that only has enemy-id strings on hand, no full registry lookup needed.
- `CapabilityEstimateService.estimate(entity, state=None, context=None, tick=0)`
  (`capability_estimate.py:85-91`) is a stateless `@staticmethod`. Confirmed (by reading the full
  body, `capability_estimate.py:103-257`) it has no dependency on `SelfModelUpdatePhase`'s
  dirty-check machinery or on `entity.self_model.capabilities` being pre-populated — identical
  characteristic the precedent ticket (`TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING`)
  already confirmed and relied on for its own ad-hoc call-site pattern.
- Combat branch (`capability_estimate.py:121-149`) for each `enemy_id` in `context.combat_enemies`:
  builds key `f"combat.enemy_type.{enemy_id}"`, reads `danger = context.enemy_data.get(enemy_id,
  {}).get("danger_rating", _ENEMY_DANGER.get(enemy_id, 0.5))`, computes
  `base_power = (atk + defense*0.5) / max(1.0, enemy_level*5 + danger*20)`, scales by
  `hp_frac`/`stamina_frac`, and returns a `CapabilityEstimate(estimate, confidence, source=
  "stat_comparison", last_updated_tick)`. The internal `_ENEMY_DANGER` dict
  (`capability_estimate.py:59-66`) has keys `rat`, `wolf`, `goblin`, `goblin_chief`, `bear`,
  `dragon` — with **no `enemy_data` supplied at all**, `estimate()` still produces a real, varying
  result driven by the acting entity's own `atk`/`def_stat`/`hp`/`stamina` vs. this internal default
  danger table (falling back to `danger=0.5` for unrecognized ids), so a caller does not need to
  reconstruct `enemy_data` to get a live, differentiating signal.

### Enemy-id source for a hostile `h`: `h.kind`, not `get_race_id_str(h)`
`EntityState.kind: str` (`src/core/state.py:669`) is the field that content-driven monster
construction uses as the archetype identifier — confirmed live at
`src/systems/world_systems/generator.py:103` (`.kind("goblin")`), `src/core/registries.py:690`
(`EnemyDef("goblin", "MEDIUM", ...)`), and `src/world/spawn_config.py:33`
(`"FOREST": ["goblin", "wolf", "bear"]`) — these are the exact same string literals as
`capability_estimate.py`'s `_ENEMY_DANGER` keys.

`tactical.py:214` already computes `get_race_id_str(n)` for a *different* purpose
(`RelationContext.target_race`, used only for faction-hostility resolution) via
`src/content_semantics/faction.py:62-66`, which reads `entity.identity.properties.get("race_id")`.
**`IdentityComponent.properties` defaults to `{}`** (`src/core/state.py:490`,
`field(default_factory=dict)`), so `get_race_id_str()` returns `None` for any entity that never had
`race_id` explicitly set in `properties` — confirmed this is the case for essentially every
existing tactical-combat test fixture (none of `tests/unit/combat/*.py`'s `.kind("monster")`
builders call `.properties({"race_id": ...})`). `h.kind` is therefore the only evidence-backed,
reliably-populated enemy-id source for `CapabilityContext.for_combat()`, not `get_race_id_str(h)`.

### `SelfModelUpdatePhase` — prerequisite gap, re-confirmed unchanged since the precedent ticket
`SelfModelUpdatePhase.apply()` (`src/cognition/self_model_phase.py:32-74`) calls `run()`
(`self_model_phase.py:57-62`) without `capability_context=`, so it defaults to `None`
(`self_model_phase.py:82`); Step 4 (`self_model_phase.py:198-213`) only calls
`CapabilityEstimateService.estimate()` when `capability_context is not None`, otherwise
`new_capabilities = old_bundle.capabilities` (stays whatever it was, empty by default —
`SelfModelBundle`/`CapabilityEstimateComponent` defaults, `src/core/self_model.py`). Re-verified via
repo-wide grep for `capability_context=`: the only non-default call sites today are still
`tests/unit/cognition/test_phase2_self_model_phase.py:109` and
`tests/integration/scenarios/test_phase2_self_model_scenarios.py:111,122,145,157` — zero
production call sites, identical finding to
`stored_artifacts/TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING/investigation.md`. This gap
is unchanged since that ticket landed and remains out of this ticket's scope per its own Out of
Scope section.

### The precedent pattern is already live in production
`grep -rn "CapabilityEstimateService.estimate(" src/` confirms `src/domains/adventure/scoring.py`
now calls it ad hoc for `GATHER_RESOURCE`/`CRAFT_UPGRADE` routes (landed by the precedent ticket),
alongside the one definition-adjacent call inside `self_model_phase.py:201` itself. This ticket
would be the **second** ad-hoc call site, following the same accepted shape: read-only, throwaway,
scorer-local, never written back to `entity.self_model`.

## Mechanics / Engine Constraints

- **Target Selection Rules** (`docs/engine/contracts/tactical_contract.md` §2, "GAP-T01"):
  documents the priority chain as "Lowest HP > Closest Distance > Lowest Entity ID" —
  **already stale relative to the current code** even before this ticket (it omits `group_bias`,
  `is_current_target` hysteresis, and `pressure_dist_mod`, all of which already exist in
  `target_score()` today). This ticket's own change (adding a capability-driven signal) will widen
  that gap further unless §2 is updated in the same session.
- **Priority-Based Tactical Targeting divergence** (`docs/guidelines/intentional_divergences.md`
  §2.6): records "Old Behavior: Nearest enemy was always selected" → "New Behavior: `Lowest HP` >
  `Closest Distance` > `Lowest Entity ID`", citing `tests/parity/test_tactical_parity.py` as
  Verification. **That test file does not exist** (`tests/parity/` contains only an `oracles/`
  subdirectory, confirmed via `find`) — a pre-existing, disclosed-here gap, not introduced by this
  ticket. §2.6 is the authoritative divergence-log record for this exact mechanism and needs
  updating to describe the capability-driven addition, independent of the broken Verification
  pointer (fixing that pointer is not in this ticket's scope).
- **Information opacity / subjective-estimate boundary** (implicit in
  `docs/cognition/capability_and_knowledge_contract.md` "Purpose" section, and explicit in the
  precedent's `scoring.py` docstring pattern): `CapabilityEstimateService.estimate()`'s inputs are
  all entity-owned fields (`entity.combat`, `entity.stamina`, `entity.identity`) — calling it from
  `target_score()` with the acting `entity` as the estimating subject and `h.kind` as the enemy id
  stays inside this boundary; it does not read any world-omniscient field.
- **Durable-state / read-only rule** (CLAUDE.md Hard Rules): `target_score()` is a pure sort-key
  function inside `evaluate_entity_intent()`; the closure and the whole method must not write back
  to `entity.self_model` — `CapabilityEstimateService.estimate()`'s result must be used only as a
  local, per-candidate scoring input, mirroring AC3 and the precedent's identical constraint
  (Design Decision 6 / Scope Guards in `stored_artifacts/TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING/plan.md`).
- **COMB-254 / SOC-185 invariant** (`docs/parity_ledger/combat_movement.yaml:2655-2664`,
  `docs/parity_ledger/social_narrative.yaml:1961-1970`; both `status: verified`, `priority: P0`):
  "Tactical action choice uses only legal candidate actions" / "Group focus fire does not override
  individual legality constraints." Both remain satisfied only if the post-sort legality filter
  (`tactical.py:433-443`) keeps running unchanged after the new sort key is introduced — this is
  explicitly guaranteed by the ticket's own Out of Scope section, but must be verified, not assumed,
  at implementation time (the filter reads `hostiles` — the now-differently-ordered list — so its
  own logic is unaffected regardless of sort key changes, but this should be confirmed by a
  regression test, not just code inspection).

## Docs Requiring Update

- `docs/engine/contracts/tactical_contract.md`: §2 "Target Selection Rules (GAP-T01)" documents the
  priority chain as HP > Distance > ID only; must be extended to state that, for hostiles resolvable
  into `CapabilityContext.combat_enemies` (via `h.kind`), a capability-driven signal from
  `CapabilityEstimateService.estimate(...).combat.enemy_type` now also factors into the sort, per
  whatever formula/placement Plan decides (see Risks below).
- `docs/guidelines/intentional_divergences.md`: §2.6 "Priority-Based Tactical Targeting" is the
  canonical divergence-log record for this exact mechanism ("New Behavior" chain) and must be
  updated to describe the capability-driven addition, consistent with CLAUDE.md's Authoritative
  Mechanics Rule requiring intentional behavior changes to be recorded here with a rationale class.
- `docs/cognition/capability_and_knowledge_contract.md`: the "How adventure routing uses capability
  estimates" section (lines 75-77) currently only documents the one existing consumer
  (`AdventureRouteScorer.score()`). A sibling paragraph/section ("How tactical targeting uses
  capability estimates") must be added describing `TacticalDecisionSystem.target_score()`'s new
  ad-hoc `CapabilityEstimateService.estimate()` call (combat domain only, via `h.kind`), stating
  plainly that `entity.self_model.capabilities.estimates` remains empty in production either way
  (same disclosure pattern as the existing adventure-routing paragraph).
- `docs/cognition/README.md`: the "Relationship to other subsystems" table (lines 69-77) has no row
  for `src/engine/tactical.py`/`TacticalDecisionSystem` at all — a new row must be added, mirroring
  the existing `src/domains/adventure/` row's exact disclosure style (ad-hoc call, not via
  `entity.self_model.capabilities`).
- `docs/parity_ledger/combat_movement.yaml` (or `docs/parity_ledger/strategic_cognition.yaml`, see
  Parity Ledger Overlap below): no existing entry documents `target_score()`'s own sort-key formula
  — a new entry must be added recording the capability-driven signal's presence, mirroring how the
  precedent ticket extended STRAT-227 for the analogous adventure-scoring change (here there is no
  existing entry to extend, so this is a new entry, not an extension).

The following docs were considered and are **not** required to change by this ticket's scope:

`docs/mechanics/04_strategic_cognition.md` (the ticket's own listed "Related Docs" entry) — read in
full; its entire Chapter 6 ("Adventure Route Scoring Constants", including the precedent's own new
§6.12) documents `AdventureRouteScorer.score()` formulas in the strategic/adventure-route domain
(`src/domains/adventure/scoring.py`), not `TacticalDecisionSystem.target_score()` (combat domain,
`src/engine/tactical.py`) — confirmed zero mentions of `TacticalDecisionSystem`, `target_score`, or
`tactical.py` anywhere in this file. The combat-tactical target-selection mechanism is documented
instead in `docs/engine/contracts/tactical_contract.md` and
`docs/guidelines/intentional_divergences.md` (both listed above). The ticket's citation of this doc
in "Related Docs" appears to be a keyword-adjacency mismatch ("strategic cognition" vs. "tactical
decision") rather than an actual dependency; no edit to it is required by this ticket's own scope.

`docs/mechanics/02_combat_laws.md` §2 "Tactical Modifiers" — read in full; documents pre-damage
Atk/Def modifiers (High Ground, Flanking, Cover, etc.), an entirely different mechanism from target
*selection*. No change needed.

`docs/simulation/domains/combat_engagement_contract.md` — read in full; documents the separate
`src/domains/combat_engagement/` pre-combat `CombatPosture` assessment domain, not
`TacticalDecisionSystem`. No change needed.

`docs/compliance/checklist.md` — this ticket does not introduce a new Logic ID (COMB-2xx); whether
to register one for the capability-driven signal is a Plan-level judgment call, not something this
investigation can decide without guessing. Left unresolved for Plan (see Risks).

## Parity Ledger Overlap

- **COMB-254** (`docs/parity_ledger/combat_movement.yaml:2655-2664`), status `verified`, priority
  `P0`, `test_path: null` — "Tactical action choice uses only legal candidate actions." Directly
  overlaps: AC4 requires this filter to keep running unchanged after the re-scored sort. Note this
  P0 entry's `test_path` is already `null` in the ledger itself (pre-existing gap, not introduced
  here) even though `docs/compliance/checklist.md:2878` cites a real test
  (`tests/integration/pipeline/test_combat_legality_matrix.py`) for the same Logic ID — the parity
  ledger and compliance checklist have drifted apart for this entry, pre-existing and out of this
  ticket's scope to reconcile, but flagged per CLAUDE.md's P0-requires-passing-test_path rule.
- **SOC-185** (`docs/parity_ledger/social_narrative.yaml:1961-1970`), status `verified`, priority
  `P0`, `test_path: null` — "Group focus fire does not override individual legality constraints."
  Same overlap and same pre-existing `test_path: null` gap.
- **No existing parity ledger entry documents `target_score()`'s own sort-key formula** (searched
  `combat_movement.yaml`, `strategic_cognition.yaml`, `social_narrative.yaml` for `target_score`,
  `group_bias`, `hysteresis`, `pressure_dist_mod` — no hits besides unrelated hysteresis entries for
  reroute/role-transition). This ticket's new capability-driven signal has no entry to extend
  (unlike the precedent's STRAT-227 extension) — a brand-new entry is needed.

## Prior Work

- `stored_artifacts/TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING/`: direct structural
  precedent, cited by this ticket. Established: (1) `CapabilityEstimateService.estimate()` is safe
  to call ad hoc from a scoring/decision function without touching `SelfModelUpdatePhase`; (2) the
  disclosure pattern ("this bypasses, not fixes, the upstream `capability_context`-never-populated
  gap") that must be repeated verbatim-in-spirit here; (3) the doc-update fan-out shape (mechanics
  chapter/contract, contract doc, `capability_and_knowledge_contract.md`, `README.md`, parity
  ledger) that this ticket's own doc list mirrors, adapted for the combat/tactical domain instead of
  the adventure/strategic domain.
- `tests/unit/cognition/test_phase2_capability_estimate_service.py`: confirms
  `CapabilityContext.for_combat()`/`CapabilityContext(combat_enemies=...)` construction patterns and
  that `estimate()` is safe to call directly with a hand-built context — same template the precedent
  used, reusable here for the combat branch specifically.
- `docs/REGISTRY.yaml` query (filtered on `related_code_areas` overlapping
  `src/engine/tactical.py`/`src/cognition/capability_estimate.py`/`src/cognition/self_model_phase.py`,
  plus `tags` intersecting `cognition`+`combat`): surfaced ~24 prior tickets touching
  `tactical.py`, none of which previously wired `CapabilityEstimateService` into it. Most relevant
  non-precedent hits: `TCK-20260613-DOC-COGNITION-SUBSYSTEM` (originated
  `capability_and_knowledge_contract.md`/`docs/cognition/README.md`, the docs this ticket must now
  extend), `TCK-20260809-COMBAT-ACTIONSTYLE-WIRING` (a prior `tactical.py` bias-wiring precedent,
  unrelated mechanism — `ActionStyle`/kiting, not target-selection scoring).

## Risks and Open Questions

1. **[BLOCKING for Plan] Exact placement/formula of the capability-driven signal inside the
   `target_score()` tuple is not determined by evidence and is a genuine design decision.** Options
   observed in the existing code's own style: (a) a new leading/near-leading tuple field (e.g.
   `-capability_estimate`, so a *higher* subjective win-estimate against this specific enemy makes
   it a higher-priority target — "attack what I'm confident I can beat"); (b) a multiplier on the
   existing `dist` term, mirroring how `pressure_dist_mod` already scales distance
   (`tactical.py:419-424`) — capability-driven "effective distance," lower urgency for feared
   enemies without touching HP/ID ordering at all; (c) a tie-breaker inserted between `h.combat.hp`
   and `dist*pressure_dist_mod`. AC1's wording ("priority reflects a real ... value instead of
   purely HP/distance/trust") only establishes that the term must be non-trivial and observable —
   it does not establish sort-key polarity (does a *high* capability estimate mean "prioritize this
   target" or "deprioritize — I might lose"?) or exact tuple position. This must not be guessed;
   Plan must decide and justify.
2. **[Not blocking, must be disclosed, mirrors precedent Risk 2] This ticket does not fix
   `entity.self_model.capabilities.estimates` being empty in production** — it is the same
   bypass-not-resolve pattern as the precedent. After this ticket, `entity.self_model.capabilities`
   is still empty at every real tick; only `target_score()`'s own local, throwaway read changes.
   Every doc update listed above must state this plainly.
3. **Every existing `tactical.py` test fixture uses a single, generic hostile `kind`** (almost
   always `"monster"`, confirmed via grep across `tests/unit/combat/*.py` — no fixture uses
   differentiated per-species kinds like `"goblin"`/`"wolf"`/`"dragon"` for multiple simultaneous
   hostiles). This means the new capability-driven signal will be a **constant across all candidates
   in every existing regression test** (same `entity`, same `h.kind` for every hostile in a given
   scenario → identical `CapabilityEstimate.estimate` for all of them), so it cannot discriminate
   between candidates in any existing fixture and is very unlikely to change any existing test's
   sort outcome regardless of where in the tuple it's placed. This is a reassuring regression-risk
   finding, but it also means: (a) new tests MUST use differentiated `.kind(...)` values across
   multiple hostiles to prove the mechanism actually does something, and (b) this finding should not
   be read as "safe to place anywhere in the tuple without care" — it only means today's *specific*
   fixtures happen not to exercise the discriminating case.
4. **`enemy_data` reconstruction is optional, not required.** `CapabilityContext.for_combat(
   enemy_ids=[h.kind])` with no `enemy_data` already produces a real, entity-stat-driven estimate by
   falling back to `_ENEMY_DANGER.get(enemy_id, 0.5)` internally (`capability_estimate.py:126-127`).
   `EnemyRegistry.get(enemy_id)`/`EnemyDef` (`src/core/registries.py`) exists but stores
   `danger_hint: str` (e.g. `"MEDIUM"`), not a numeric `danger_rating` — there is no existing
   string→float mapping utility for it anywhere in the repo (grep confirmed). Introducing a registry
   read here would also break the "no registry reads" pattern the precedent explicitly preserved
   (Design Decision 4 of that plan) and `tactical.py` today imports no registry module. Recommended
   (not yet a Plan decision): skip `enemy_data` entirely, matching the precedent's minimal-plumbing
   philosophy — but this should be an explicit Plan choice, not silently assumed.
5. **`tests/parity/test_tactical_parity.py`, cited by `intentional_divergences.md` §2.6's own
   "Verification" field, does not exist.** Pre-existing gap, not caused by this ticket, and out of
   this ticket's scope to create — but Plan should decide whether the §2.6 doc update points at a
   real, currently-passing test file instead of perpetuating a dead reference (e.g. point at the new
   test file this ticket adds, per New Tests Required in `test_plan.md`).
6. **Whether to register a new Logic ID** (e.g. `COMB-278`) in `docs/compliance/checklist.md` for
   "Subjective capability estimate affects tactical target choice" is a judgment call this
   investigation does not resolve — the existing `COMB-263`–`COMB-277` range documents other
   tactical-choice inputs (weapon range, skill range/cost, readiness, exhaustion, threat level) with
   this exact granularity, so a new ID would be consistent with that pattern, but adding one is not
   required by any AC and should be an explicit Plan decision, not an unrequested addition.

## Anti-Drift Hazards

- **Do not touch `select_best_target()`** (`tactical.py:819-836`) — a separate, unrelated public
  static method ("Matches legacy 'TacticalEvaluator.SelectTarget'") with its own simple `(hp, dist,
  id)` tuple and its own dedicated test (`tests/unit/combat/test_target_selection_contract.py`).
  This ticket's scope is `target_score()` inside `evaluate_entity_intent()` only.
- **Do not modify the post-sort legality filter** (`tactical.py:433-443`, COMB-254) or its ordering
  relative to the sort — explicitly Out of Scope (AC4). The capability signal must only influence
  which candidate is tried first, never bypass `LegalityServiceV2.verify_attack_legality()`.
- **Do not write back to `entity.self_model` or any other durable entity field from inside
  `target_score()` or `evaluate_entity_intent()`.** `CapabilityEstimateService.estimate()`'s result
  must be used only as a local per-candidate scoring input for this tick's sort, never persisted via
  `EntityUpdate`/`dataclasses.replace` on `entity` itself (only the existing `EntityUpdate` return
  value for task/navigation changes is legitimate).
- **Do not silently claim `entity.self_model.capabilities.estimates` is now populated in
  production** anywhere (code comments, doc updates, Completion Summary) — it remains empty; only
  `target_score()`'s own ad-hoc, throwaway read changes.
- **Do not attempt to fix `SelfModelUpdatePhase.apply()`'s upstream `capability_context`-never-passed
  gap** — explicitly Out of Scope, matching the precedent's identical exclusion.
- **Do not modify `src/cognition/capability_estimate.py`** unless a genuinely new capability domain
  or field is required — AC3 depends on its existing unit tests
  (`tests/unit/cognition/test_phase2_capability_estimate_service.py`) passing unchanged, and no
  evidence gathered here shows a need to change `CapabilityEstimateService`'s internals.
- **Do not confuse `get_race_id_str(h)` with `h.kind`** — they are different fields
  (`identity.properties.get("race_id")`, usually unset/`None`, vs. `EntityState.kind`, always
  populated) serving different existing purposes; only `h.kind` is the evidence-backed enemy-id
  source for this ticket.
- **Do not add an `EnemyRegistry`/other registry import to `tactical.py`** for `enemy_data`
  reconstruction unless Plan explicitly decides it's needed (see Risk 4) — the no-registry-reads,
  minimal-plumbing pattern is what the precedent ticket established and what keeps this an ad-hoc,
  low-blast-radius change.
- **Do not change `group_bias`, `is_current_target`, or `pressure_dist_mod`'s own formulas** — this
  ticket adds a new signal to `target_score()`, it does not touch the existing terms' computation.
