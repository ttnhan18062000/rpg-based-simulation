---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED
artifact_type: investigation
date: 2026-10-30
tags: [determinism]
---

# Investigation: set-order sites that reach state or decisions (audit phase, no code written)

Head audited: origin/main de5a223ca. Method: read each site, trace the producer and every reader, then classify. Nothing was run except one registry listing (`SKILL_REGISTRY`). `state.py` read only.

## Classes
- **DECISION**: the order changes which branch the simulation takes.
- **STATE-ORDER**: the order lands in a durable ordered container; it reaches the canonical hash only if the canonical dict does not sort it.
- **LATENT**: the order would matter, but no shipped content or live caller can trigger it today.
- **EMISSION/NONE**: order reaches nothing but a local container or an event list.

## Audit table (Scope 1-5)

| # | file:line | iterates / builds | reaches | positional readers | proposed fix (stable key) |
|---|---|---|---|---|---|
| 1 | `src/engine/tactical.py:704-722` | iterates `entity.identity.learned_skills` (a `frozenset[str]`, `patches.py:251`), collects ready skills, stable-sorts by `power` desc, takes `[0]` | **DECISION** when two ready skills tie on power. **LATENT with shipped content**, see "Tie reachability" below | `available_skills[0]` only | sort key `(-power, skill.id)`; no behaviour change when no tie |
| 2 | `src/progression/leveling.py:137-143` | loops `learned_skills`; the body adds `skill.power` to `evasion` only for `skill_id == "swift_reflexes"` | **NONE**. At most one addend (`swift_reflexes`, 0.1) is ever added, so float addition order cannot differ. See "Float order" | none | none needed. Optional hygiene: `for skill_id in sorted(learned_skills)`; no hash claim |
| 3 | `src/domains/combat_engagement/learning.py:45` and `:~82` | `known_skills = list(set(list(memory.known_skill_ids) + list(observed_skills)))`, then truncated to the first 10 (`known_skills[:10]`), stored as tuple `OpponentModel.known_skill_ids` | **LATENT**. The only live caller (`learning_outcome.py:86`) passes `observed_skills=()`, so the list is always empty. `CombatMemory.to_canonical_dict` is `{"opponents_tracked": len(...)}` (`cognition.py:326`), so the tuple is not in the canonical hash. If a caller ever passes skills, which 10 survive the truncation would follow the hash seed | `known_skill_ids` is copied (`phase.py:160, 442`), never indexed. No positional reader | `sorted(set(...))` (string ids); truncation then takes the first 10 sorted |
| 4a | `src/core/updates.py:269` `recipes_learned`, `:276` `breakthroughs_add`, `:279` `learned_skills`, `:280` `traits_add`, `:281` `traits_remove` (`IdentityUpdate.merge`) | `list(set(a + b))` | **NONE for state order**. Apply folds each into a set: `patches.py:217` (`rec \|= set(...)`), `:230-232` (`sk \|=`, `tr = (tr \| set(add)) - set(remove)`, `brk \|=`), and the result is stored as `frozenset` (`patches.py:251`). Readers before apply only test truthiness (`apply.py:639-642`) | none found (grep of `src/` outside `observability/` and the merge line itself: `patches.py`, `apply.py` only) | `sorted(set(...))` for hygiene, no behaviour claim, as ruled |
| 4b | `src/engine/evolution.py:120` | `learned_skills=list(set(id_upd.learned_skills + skills_to_learn))` | **NONE**. Same apply path as 4a; the list only feeds `IdentityUpdate.learned_skills` | none | `sorted(set(...))`; ticket A already recorded why this is not an emission-only edit. B may take it now: `evolution.py` is not on u24's open branches (per the ruling) |
| 4c | `src/core/updates.py:882-883` (`RegionUpdate.merge`) `modifiers_add`, `modifiers_remove` | `list(set(a + b))` | **NONE** for state order: consumed by `apply_plan.py:153` as `m not in r_upd.modifiers_remove` and `+ r_upd.modifiers_add` | none | `sorted(set(...))` hygiene |
| 5a | `src/engine/apply_plan.py:153` | `mods = list(set([...existing active_modifiers...] + r_upd.modifiers_add))` then stored as `RegionState.active_modifiers: List[str]` | **STATE-ORDER**. The list order in state follows the hash seed. `RegionState.to_canonical_dict` sorts it (`state.py:330`), so the canonical hash is unaffected. Readers (`environment.py:38,111-115`, `transformation.py:65`) test membership only | none positional | `sorted(set(...))`. Needs `state.py`? No: only `apply_plan.py` is edited |
| 5b | `src/systems/strategic_systems/intelligence.py:928` | `new_concerns = list(set(strat_up.concerns_add_or_update + concerns))` over **ConcernState objects** (hash by value, so by strings) | **DECISION, via dict insertion order**. `patches.py:458-466 merge_dict` inserts in list order, so `strategic.concerns` dict order follows the seed. `detour.py:176-180` then does a stable `sorted(concerns.values(), key=urgency, reverse=True)` and removes the excess beyond `max_concerns`: when concerns tie on urgency, which are dropped depends on dict order | `detour.py:176`, `capacity_enforcement.py:68` (rebuilds a dict, same order dependence), `belief.py:254` (sums, order-free), `cognition_export.py:109` (not read) | dedupe by id with a stable order: `sorted({c.id: c for c in ...}.values(), key=lambda c: c.id)` or `sorted(..., key=id)` over the list; key = `concern.id` |
| 5c | `src/systems/strategic_systems/intelligence.py:558` `blockers_remove`; `:940` `concerns_remove`; `:1811` `leads_remove` | `list(set(ids...))` | **NONE** for order: removal lists are popped by id (`merge_dict` remove loop) | none | `sorted(set(...))` hygiene |
| 5d | `src/engine/pipeline_phases/capacity_enforcement.py:157-162` | six `list(set(a) \| set(b))` removal lists (leads, concerns, projects, hypotheses, zones, committed intentions) | **NONE** for order (ids popped from dicts / filtered from tuples by membership; `merge_committed_intentions` checked by membership) | none found; not traced for `committed_intentions` tuple removal beyond membership | `sorted(set(...))` hygiene |
| 5e | `src/worldgeneration/generator.py:220` | `resource_types = list(set(r.resource_type ...))` then `rng.choice(..., resource_types, ...)` per node | **DECISION in world generation**: the picked type per node follows the hash seed for the same seed and catalog. Applies only to the intent-driven `WorldGenerator` path (not the declarative worlds in `data/worlds`) | indexed by the RNG | `sorted(set(...))`. Changes generated worlds from that path; needs rpg-planner's call on whether any pinned generator output exists |
| 5f | `src/platform/spatial_hash.py:65` | `sorted(list(set(results)))` | none, already sorted | | none |
| 5g | `src/domains/adventure/scoring.py:239` | set comprehension of trait stems | NONE (intersection count) | | none |
| 5h | `src/observability/**`, `src/lab/**` `list(set(` | report/anomaly/lab manifest code | NONE for simulation state (`lab/workflows` write manifests; observability is ticket A's) | | out of scope, listed for completeness |

Not found: any other iteration over a set/frozenset in decision code outside `tactical.py:706` and `leveling.py:138` (grep of `for ... in ...learned_skills|traits|active_breakthroughs|known_recipes` and `for ... in ...set(` over `src/` excluding `observability/` and `lab/`).

### Tie reachability (tactical.py)
`SKILL_REGISTRY` (`src/core/skills.py`), active skills:

| id | kind | power | range | cost |
|---|---|---|---|---|
| HEAVY_STRIKE | ACTIVE | 2.0 | 1 | 15 |
| fireball | ACTIVE | 2.0 | 1 | 25 |
| power_strike | ACTIVE | 1.5 | 1 | 10 |
| swift_reflexes | PASSIVE | 0.1 | 1 | 0 |

The only equal-power pair is **HEAVY_STRIKE and fireball (both 2.0)**. A tie needs an entity that has learned both and has stamina >= 25 with the target in range 1.
- Skill sources in shipped content: class `starting_skills` (`classes.py`: power_strike, fireball, swift_reflexes) and level unlocks (`leveling.py:49-53`: 2 power_strike, 5 swift_reflexes, 10 fireball). **HEAVY_STRIKE appears in no class, no level unlock and no data file**; it appears only in `skills.py` and in `tests/integration/pipeline/test_combat_legality_matrix.py:497-545` (a constructed entity).
- So with shipped content the tie is **not reachable today**. It is reachable for any entity built with both skills (tests, future content). The fix is a latent-bug fix; the paired run should show no change (expected: identical hash), which is also the prediction to check.
- Note for rpg-planner: ruling 1 calls this "a live behaviour divergence in every ordinary run". The audit finds it live only in the code path, not in current content.

### Float order (leveling.py:137)
`recalculate_combat_stats` adds `skill.power` once, for `swift_reflexes` only; other passives add nothing (comment: "Add other passives here as they are added"). One addend means no order dependence. If more passives are added later, the sum would become order-dependent; sorting the loop then would be the guard.

## Hash expectations
- Items 1, 2, 3, 4a-4c, 5a, 5c, 5d: **no change** to the seed-0 final state hash predicted (no tie, no state-order that the canonical form keeps).
- 5b: the dict insertion order of `strategic.concerns` can change at seed 0 (the canonical dict sorts by id, so the hash is predicted unchanged, but the decision path through `detour.py:176` can change when urgencies tie and the cap is hit). **This is the one item that can move behaviour at seed 0**, so it is the one to pair-run.
- 5e: changes generated worlds on the generator path only.

## Positional readers summary
None of the lists in 4a-4c, 5c, 5d has a positional reader. `known_skill_ids` has none. The concerns dict order (5b) is read by a stable sort (`detour.py`) and by `capacity_enforcement.py:68`.

## Open questions for rpg-planner
1. Is 5b (concerns dedupe) in B's scope? It is the only item found that reaches a decision at seed 0; the ruling's list does not name it.
2. 5e (worldgeneration): fix here, or file separately? It changes generated worlds.
3. Ruling 1 wording ("live in every ordinary run") vs the finding that the tie is unreachable with shipped content: keep the Bible/parity wording as "deterministic tie-break" (no behaviour claim) and the divergence class Bug Fix?
4. Hygiene sorts (4a-4c, 5c, 5d): do them all (about 12 lines) or only 4a/4b as ruled?

## Probes run after the quiet window (light, no sim; 2026-10-30)
- **Tie order depends on the seed (positive control for AC3).** `list(frozenset(["HEAVY_STRIKE", "fireball"]))[0]` over `PYTHONHASHSEED` 0-40: `fireball` first at 27 seeds (first at seed 1), `HEAVY_STRIKE` first at 14 seeds (first at seed 4). A two-element frozenset is not identical to the real `learned_skills` frozenset (which holds the entity's other skills as well), so the AC3 test must build the real entity and compare picks across seeds, e.g. 1 and 4, not rely on this standalone order.
- **5b is real (the order, not yet the decision).** Four `ConcernState` objects with equal urgency, `list(set(...))` at seeds 0-3: `[c0,c1,c3,c2]`, `[c1,c2,c3,c0]`, `[c2,c0,c1,c3]`, `[c2,c3,c0,c1]`. The list order, and so the `strategic.concerns` dict insertion order, follows the seed. Whether the cap-hit path in `detour.py:176` then drops different concerns is still to be shown by a test that sets up a tie at the cap (not run).
- Still unverified, to check when code is allowed: all hash predictions in the table, and the `generator.py:220` effect (needs a generator run).
