---
status: authoritative
layer: world
authority: P2
audience: agent
last_verified: 2026-09-06
tags: [world, faction]
---

# Affiliation Mutation Contract

**Ticket:** TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE (M6 idea 39, `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY`).

**Status**: AUTHORITATIVE — the write-side primitive and its first real, live producer.

No Mechanics Bible chapter for social/political mechanics exists yet
(`TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` tracks authoring one). This doc is the
minimum-viable contract for the mechanism described below until that chapter lands; it should
be folded into that chapter rather than duplicated once it exists.

---

## Write-Path Contract

`IdentityComponent.faction: int` (`src/core/state.py:580`) is durable per-entity state, normally
set once at construction and otherwise immutable. The only authoritative way to change it after
construction is:

```
IdentityUpdate.faction_set: Optional[int]   (src/core/updates.py:227)
    -> IdentityPatch.apply()                (src/engine/patches.py:209)
    -> ApplyPath                            (src/engine/apply.py)
```

This path pre-dates this ticket and is unchanged by it — this ticket's job was supplying the
first real producer, not modifying the apply-path. `dataclasses.replace(entity.identity,
faction=...)` outside `IdentityPatch.apply()` is never legal; enforced by
`tests/architecture/test_faction_mutation_write_paths.py`.

`src/engine/apply.py`'s hostile/dead cache (`_has_hostiles_or_dead_cache`) is invalidated
whenever any `EntityUpdate.identity.faction_set is not None` is present in a tick's `StateUpdate`
— this wiring also pre-dates this ticket.

## Trigger: Defection (SOC-230)

`PartyLifecycleService.check_defection()` (`src/systems/social_systems/party_lifecycle.py:143`)
is the first live producer of `faction_set`. When an entity defects from its group (grievance
log at or above `effective_defection_threshold()`), the returned `EntityUpdate` now includes:

```python
identity=IdentityUpdate(faction_set=Faction.NEUTRAL)
```

This is a **NEUTRAL-sentinel design, not rival-faction selection** — a defector always lands in
`Faction.NEUTRAL` (`src/core/enums.py:28`), never a specific destination faction, because
`GroupRecord` carries no faction context to choose one from and no rival-faction-selection logic
exists (or is in scope here). `TCK-20260905-DRIFTING-LOYALTY-SIGNAL` (idea 56) is the anticipated
future consumer that may request a specific non-neutral destination faction once it lands;
nothing in this ticket depends on idea 56 existing first, and idea 56 is expected to extend
this trigger's destination logic, not replace it.

`check_defection()` remains a pure function of its 3 arguments (`group`, `entity`, `tick`) — it
does not mutate `group` or `entity` itself, only returns the typed update.

## Observability

`entity_faction_changed` (`src/observability/event_extractor.py:410-416`) is a plain
before/after diff on `entity.identity.faction` — pre-existing and unchanged by this ticket. It
fires exactly once per real faction delta regardless of which producer caused it. Confirmed via
`tests/unit/observability/test_event_extractor_identity.py::
test_entity_faction_changed_fires_once_on_real_defection_trigger`, which runs the real
`check_defection()` -> `ApplyPath` -> `EventExtractor` sequence end-to-end.

## Combat/Action-Legality Semantics: Next-Tick Boundary

`identity.faction` is read live (no caching beyond the hostile/dead cache noted above) by
`LegalityServiceV2` (`src/engine/legality.py`, 6 call sites) and 35 other call sites across
`src/` (41 total `.identity.faction` reads repo-wide, re-counted 2026-09-06 during an external
pre-merge review — the original 31 undercounted by 10; the correction doesn't change the safety
conclusion below, since every missed site, `src/engine/town_resolution.py:129,140` included, is an
immediate per-tick read, not a cross-tick cache). `src/engine/town_resolution.py`'s two sites
(`entity.identity.faction != region.owner_faction_id`, taxation and suppression) are structurally
identical to `legality.py`'s own reads — same frozen-`state`-within-one-`refine()`-pass timing
safety applies, they were simply not enumerated by this ticket's original investigation. The
relevant ordering guarantee comes from `AuthoritativeApplyPipeline.refine()`'s fixed
phase order (`src/engine/pipeline.py`):

```
"action_routing"  (pipeline.py:297)  -- LegalityServiceV2 evaluated here
    ... (other phases) ...
"groups"          (pipeline.py:402)  -- check_defection()'s faction_set trigger lives here
```

Both phases read the same frozen `state` argument for the whole `refine()` pass and accumulate
into the same `update`/`refined_entity_updates`. Because `"action_routing"` runs strictly before
`"groups"`, a same-tick defection cannot retroactively change a legality decision that
`"action_routing"` already made earlier in the same tick — that decision reflects the
pre-defection faction. The new faction only becomes visible to legality reads starting with the
next tick's `"action_routing"` pass (or, equivalently, any check performed directly against the
post-apply `AuthoritativeState`).

This is a structural consequence of `refine()`'s existing phase order, not a new guard — no
`src/engine/legality.py` code change was made or is required. The ordering is currently an
**implicit** consequence of call order, not an enforced invariant: if `refine()`'s phase order is
ever refactored, re-check this semantics against
`tests/unit/engine/test_legality_faction_mutation.py::
test_faction_change_mid_tick_legality_semantics`, which is the regression guard for exactly this
behavior.

## Replay Fingerprint Coverage

`StateFingerprinter.get_fingerprint()` (`src/replay/fingerprint.py`) — the lighter-weight
fingerprint used by `worldbuilding/compiler.py` and `AuthoritativeState`'s own convenience
method — did not include `identity.role`/`identity.faction` in its per-entity string prior to
this ticket, meaning a faction mutation would have been invisible to replay-parity checks that
rely on it. Both fields are now included. This is distinct from `CanonicalStateHasher`
(`src/engine/checkpoint.py`), which already covered `faction` via
`IdentityComponent.to_canonical_dict()` and required no change.

## Out of Scope Here

- Rival-faction selection logic (which faction a defector *joins*, rather than becoming
  NEUTRAL) — future scope, likely idea 56's.
- Any loyalty/pressure-accumulation field on `IdentityComponent`/`EntityState` — idea 56's scope.
- `SocialContractSystem.resolve_contract_outcome(betrayal=True)` — confirmed dormant, not wired
  live by this ticket.
- `FactionState`-level mechanics (`FactionInfluenceService`, `FactionDecisionPhase`,
  `docs/parity_ledger/faction.yaml`) — a separate subsystem layer with no code path to
  entity-level `identity.faction` today.

## Related

- `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY` — parent epic.
- `TCK-20260905-DRIFTING-LOYALTY-SIGNAL` — idea 56, anticipated future consumer.
- `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` — eventual Mechanics Bible chapter home.
- `docs/parity_ledger/social_narrative.yaml`, `docs/parity_ledger/combat_movement.yaml`,
  `docs/parity_ledger/substrate.yaml` (`SUB-378`).
