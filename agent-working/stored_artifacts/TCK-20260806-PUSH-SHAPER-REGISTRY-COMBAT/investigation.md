---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT
artifact_type: investigation
tags: [observability, engine, combat, simulation-quality]
---

# investigation.md — TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT

## Summary

Builds on the epic-level event-coverage audit and design refinement (both in
`stored_artifacts/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC/investigation.md`, not
re-derived here). This ticket's own investigation resolves the 3 decision points that audit left
open for COMBAT specifically, confirms the SHADOW-mode gating mechanism, and verifies the dispatch
point's exact code location.

## Decision 1: `hazard_drain_applied` / `hero_death_unrecorded` — migrate alongside COMBAT

Both are read from the exact same `e_upd.combat` object as the 4 core COMBAT events, in physically
adjacent code (`event_extractor.py` lines ~423-432 for `hazard_drain_applied`, ~189-200 for
`hero_death_unrecorded`, both inside the same per-entity block the 4 core events live in).
**Decision: migrate both alongside COMBAT in this ticket.** Reasoning: they read the identical
typed record via the identical mechanism (no new logic pattern needed), and migrating them now
means the cutover ticket can remove the *entire* combat-category code block from
`event_extractor.py` in one pass rather than leaving 2 stray branches behind that still need their
own future migration. They are scored by WORLD/NARRATIVE respectively, not COMBAT — this ticket's
shaper produces them as a courtesy alongside the COMBAT events it's built to construct, same as the
current extractor does; ownership for *scoring* is unaffected.

## Decision 2: `demographic_mortality` (despawn branch) — defer

Unlike the two above, this branch fires on ANY despawn (entity removed from `state.entities`
entirely — not merely `lifecycle.active=False`), for causes broader than combat (natural death,
administrative removal, etc.). It reuses `_real_combat_update`-style logic only to decide whether
to *suppress* itself when a combat attacker is present — it does not itself represent a combat
event. Migrating it would require the shaper to also understand every non-combat despawn cause,
which is out of this ticket's COMBAT-specific scope. **Decision: defer to a later phase.** Left on
the existing diffing path; the cutover ticket must not remove this branch when it removes the 6
migrated ones.

## Decision 3: `combat_resolved` / `attrition_threshold_crossed` — re-confirmed dead

Re-ran the grep from the epic-level audit directly, not trusting the citation blindly:

```
$ grep -rn "combat_resolved\|attrition_threshold_crossed" src/observability/ src/engine/
src/simulation_quality/scorers/combat.py:18,23,71,72,95  (scorer's own EVENT_TYPES/score() only)
```

Confirmed: no construction site exists anywhere outside the scorer's own dormant handling code.
**Disclosed as a pre-existing gap, no migration action** — there is nothing to migrate.

## SHADOW-mode gating mechanism

Checked `src/domains/optimization/feature_flags.py`'s 11 flags — none are semantically about
"observability emission path." Reusing `ENABLE_ENHANCED_TRACE_EVENTS` would conflate two unrelated
concerns (trace verbosity vs. emission mechanism) and its own doc description
(`docs/guides/feature_flags.md`: "Enhanced trace/observability event emission") is close but not a
clean match — that flag already has an existing, documented meaning. **Decision: introduce a new
flag, `ENABLE_PUSH_EVENT_SHAPERS`, default `OFF`**, following the same `FeatureFlagManager`
default-OFF policy (DEV-002) as all 11 existing flags. Per `SimQ profile activation`'s existing
mechanism (`docs/guides/feature_flags.md` "SimQ profile activation" section), this can be set to
`SHADOW` per-world via the same `feature_flags:` YAML block calibration profiles already support —
no new plumbing needed, reuses the exact mechanism `hero_guild_routing.yaml`'s
`ENABLE_ADVENTURE_ROUTING: "ON"` already demonstrates.

## Flag-check mechanism verification

Traced `pipeline.py:69-84`: pipeline phase gating (`ENABLE_COMBAT_ENGAGEMENT` etc.) constructs a
FRESH `FeatureFlagManager()` per tick, local to that refinement function, populated from
`state.feature_flags` (a raw `Dict[str, Any]` field on `AuthoritativeState`) plus rollout-profile
overrides. `Kernel._phase_observability()` is a separate method with no access to that local
`ff_manager` instance — but it DOES have `prior_state.feature_flags` directly (same field,
confirmed on `AuthoritativeState:1147`). **Decision: read `prior_state.feature_flags.get(
"ENABLE_PUSH_EVENT_SHAPERS", "OFF")` directly as a string comparison** (`"ON"`/`"SHADOW"`/`"OFF"`),
matching `calibrate_simq.py`'s own string-value convention — no `FeatureFlagManager` instantiation
needed inside `_phase_observability`, and this flag reaches the state via the exact same
SimQ-profile-YAML injection mechanism (`docs/guides/feature_flags.md` "SimQ profile activation")
every other flag already uses, with zero new plumbing on the profile side. Added
`ENABLE_PUSH_EVENT_SHAPERS` to `FeatureFlagManager.__init__`'s 11-flag dict (documentation/
consistency, defaults OFF per DEV-002) and to `calibrate_simq.py`'s `_KNOWN_FLAGS` list (so
`ENABLE_PUSH_EVENT_SHAPERS=SHADOW python3 tools/calibrate_simq.py ...` works as an env-var override
too, matching the existing 11 flags' dual profile-YAML/env-var support).

## Correctness check: apply-time-only HP mutations that never touch `EntityUpdate.combat`

Before finalizing the shaper's logic, traced `ApplyPath._compute_entity_changes()`
(`src/engine/apply.py:70+`) directly and found **2 more HP-mutation sources beyond hazard drain
and biological.py's own starvation/exhaustion path** — both computed fresh at apply-time, entirely
independent of `EntityUpdate.combat`/`CombatUpdate`, and never written back to it (`changes` is a
local dict; `replace()` returns a new immutable instance — confirmed `u_ent`/`e_upd.combat` is
never mutated by this code):

1. **Passive health decay** (`apply.py:93-110`): hunger≥95/sleep_debt≥98 → up to −2/−1 HP,
   computed directly as `changes["combat"] = replace(comb, hp=new_hp, ...)`, no `CombatUpdate`
   involved. (Note: this looks like it may double-count against `biological.py`'s own separate
   −1/−1 hunger>90/sleep>95 mechanism found in the epic-level audit — same category, different
   thresholds/amounts, computed in 2 different places. Flagging as a possible pre-existing
   redundant-damage bug, **not fixed here, out of this ticket's scope** — worth a future
   investigation ticket, not silently absorbed into this one.)
2. **Level-up full-heal / stats-recompute clamp** (`apply.py:463-495`): on a level-up,
   `new_com.hp = derived["max_hp"]` (a full heal, positive); separately, if a stat/wound/scar
   change reduces `max_hp` below current `hp`, a downward clamp fires with **no attacker** — a 5th
   non-combat HP-decrease source.

**Correctness conclusion**: since both mechanisms mutate `changes["combat"]` (apply-time-local) and
never touch the original `update.entity_updates[eid].combat` object my shaper (and the already-
fixed diffing extractor) both read, `_real_combat_update()`'s `attacker_id is not None` check
correctly excludes both from combat classification in *both* the old and new paths — no
classification divergence.

**Known, disclosed limitation (not fixed here)**: in the narrow case where a *real* combat hit
(driving a real `hp_delta` on `EntityUpdate.combat`) and one of these 2 apply-time-only mechanisms
land on the *same entity in the same tick*, this shaper's `new_hp = prior_hp + hp_delta` estimate
does not include the apply-time-only adjustment, while the old (diffing) extractor's
`entity.combat.hp` read is the fully materialized, correct value. This means the *event types*
fired stay identical between old and new (driven by `hp_delta`'s sign and `attacker_id`, both
consistent), but the numeric `damage`/`is_lethal`/`hp` **payload values** could diverge by the
apply-time-only delta in this specific compounding case. **Carried forward explicitly to
`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`'s scope**: that ticket's event-stream parity check must
specifically look for and quantify this compounding-tick payload divergence pattern across the
real calibration corpus before green-lighting cutover — not just check event-type match rates.

## Dispatch point verification

Confirmed directly: `kernel.py:720` calls `ApplyPath.apply_generation(...)`, producing
`self._state`; `kernel.py:731` calls `self._phase_observability(prior_state, update)` immediately
after. `_phase_observability` (`kernel.py:897+`) internally calls `EventExtractor.extract(
prior_state, self._state, update, obs_mode)`. The new shaper-registry call is added as a sibling
call within `_phase_observability`, reading `prior_state`/`update` only — confirmed sufficient per
the epic-level design refinement (`CombatUpdate.hp_delta`/`alive_set`/`attacker_id`/`outcome_kind`
are all present on `update.entity_updates[eid].combat`, no post-mutation state needed).

## Reopen Notes (2026-08-06) — 2 real bugs found by TCK-20260806-PUSH-SHADOW-VALIDATION-PERF

That ticket built a real, non-mocked comparison tool running the old diffing extractor and the new
shaper side-by-side against 6 real worlds, 500 ticks each. It found 2 confirmed bugs in this
ticket's original implementation — recorded here rather than only in the validation ticket, since
the fixes landed in this ticket's own code.

### Bug 1: `entity_killed` false positive on hazard-caused "death"

Original implementation derived `entity_killed` from `alive_set`/HP arithmetic
(`prior_ent.lifecycle.active and not new_alive` where `new_alive` came from `alive_set`). Direct
pipeline tracing (real kernel run, `hero_guild_routing_seed42`, entities 26/28/30) found:
`CombatUpdate.alive_set` maps to `CombatComponent.alive` (`src/engine/patches.py:301`:
`alive=(new_hp > 0) if u_com.alive_set is None else u_com.alive_set`) — a **different field** from
`LifecycleComponent.active`. `LifecycleSystem.resolve_lifecycle()`
(`src/systems/lifecycle_systems/lifecycle.py:43`) only transitions `lifecycle.active` on
`outcome_kind == "KILL"` or old-age (`age_ticks >= max_age_ticks`) — **never on `alive_set` alone**.
Hazard drain (`outcome_kind="HAZARD"`) legitimately sets `combat.alive=False` while
`lifecycle.active` stays `True` for the rest of that tick. Real, empirical confirmation via a
direct kernel state trace: at tick 4, `combat.alive` flips `True→False` for these 3 entities
(hazard hit); `lifecycle.active` stays `True` through tick 4 and only flips at tick 5 — one tick
later, with **zero `EntityUpdate.combat` present at tick 5** for any of the 3 entities (confirmed
by tracing `LifecycleSystem.resolve_lifecycle()`'s own inputs directly: at the tick 5 invocation,
`entity.lifecycle.active` is already `False` on *entry*, meaning the transition happened even
earlier in that tick's pipeline, upstream of `resolve_lifecycle` itself, via a path this
investigation did not fully trace to its exact origin — the precise upstream mechanism doesn't
change the conclusion: no per-tick update record exists at the tick this shaper could observe it).

**Fix**: gate `entity_killed`/`hero_death_unrecorded` on `getattr(combat_upd, "outcome_kind", None)
== "KILL"` directly. This correctly narrows the shaper's `entity_killed` coverage to same-tick,
combat-caused kills only — **disclosed, not silently accepted**: old-age deaths and delayed
hazard-transition deaths (both non-`KILL`-tagged lifecycle transitions) are not covered by this
shaper, a narrower scope than the old extractor's kill-events branch (fires on ANY
`lifecycle.active` transition regardless of cause or timing). Real-corpus frequency of the
delayed-hazard-transition sub-case: 1 occurrence across 6 worlds × 500 ticks in
`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`'s validation run — accepted as a rare, disclosed
limitation, not a blocker.

### Bug 2: missing volumization rule

Original implementation never ported `event_extractor.py`'s volumization rule ("skip routine,
non-lethal `combat_damage` in `LIGHT`/`LONG_RUN` observability mode") — a straightforward omission,
not a subtle edge case. Since `ObservabilityConfig`'s default mode is `LIGHT`
(`src/observability/config.py:25`) and no calibration run overrides it, this caused `combat_damage`
to over-fire in every sustained-combat sequence across every world tested (`urban_political`,
`crowded_frontier` showed this most clearly — up to 19 of 24 active ticks diverging in
`crowded_frontier` before the fix).

**Fix**: added `mode: ObservabilityMode` to the `EventShaper` protocol and `CombatShaper.shape()`,
applying the identical `is_lethal or mode not in (LIGHT, LONG_RUN)` check the old extractor uses.
Threaded through `run_shadow_shapers()` and `kernel.py`'s call site (`obs_mode`, already computed
where `_phase_observability` runs — no new plumbing). `EconomyShaper`/`FactionShaper` also gained
the `mode` parameter for `EventShaper` protocol conformance, confirmed via source (only 3
volumization checks exist total in `event_extractor.py`: movement, `combat_damage`, and
`gold_transaction` — the last already on the DEFERRED list, not migrated — so no equivalent gap
exists in ECONOMY/FACTION).

### Post-fix re-verification

15/15 `CombatShaper` unit tests pass (5 new: hazard-death exclusion, volumization suppression in
LIGHT mode, volumization override for lethal damage, no suppression in NORMAL mode, default-mode
consistency check). Full `tests/unit/observability/` suite: 798 passed, 6 skipped. Real-world
comparison (`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`'s own tooling) re-run across all 6 worlds
post-fix: 130/131 active ticks match exactly, 0 payload-value mismatches.
