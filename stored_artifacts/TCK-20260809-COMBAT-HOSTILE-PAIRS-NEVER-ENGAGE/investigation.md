---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE
artifact_type: investigation
tags: [combat, simulation-quality]
---

# Investigation — TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE

## Context search (mandatory step, before any grep/file reads)
`search_docs` for "ENABLE_COMBAT_ENGAGEMENT feature flag combat engagement phase dormant
reachability" surfaced `tickets/done/TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY.md`
(the real, deliberate DEV-002 ruling — that flag gates posture assessment, not damage resolution)
and `docs/audits/D21_entity_lifecycle_foundation_layers.md`'s "Combat legality always false"
section (this session's own earlier finding, already partially fixed by
`TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION` /
`TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE`). Both read in full before proceeding.

## Methodology (real, live-instrumented, matching this session's established discipline)
All findings below are from live, monkey-patched `Kernel.tick_once()` runs (2000 ticks) against
the real compiled `dungeon_crawl`/`urban_political` worlds (seed 42) — never assumed or
synthetic-only. Probe scripts lived in the scratchpad, not the repo.

## Starting anomaly
During `TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY`'s own Test-phase real-corpus re-verification,
`combat_damage`/`combat_initiated`/`entity_killed` all recorded **zero** occurrences across a full
2000-tick run of either world — a materially worse picture than the 28.5%/36.6% `is_attack_legal`
probe rate the 2 sibling tickets reported. This ticket traces why.

## Investigation trail (in order, each step ruling out or narrowing the prior one)

1. **`resolve_multi_attack` friendly-fire volume is a red herring, not a bug.** A broad
   instrumentation of `LegalityServiceV2.verify_attack_legality` (all real call sites) showed 1774+
   calls in `urban_political`, 100% `FRIENDLY_FIRE_ILLEGAL`, always role `VANGUARD`. Stack-trace
   capture on the real call showed these originate from `src/engine/combat.py:348`
   (`CombatResolutionSystem.resolve_multi_attack`), called from `MovementSystem.resolve_move()`
   during the `movement_routing` pipeline phase — the real opportunity-attack-during-movement scan,
   which checks legality against every nearby entity regardless of hostility. `hero_guild`↔
   `town_council` (the dominant pair here) is confirmed, via direct real-context replay,
   genuinely non-hostile (`is_hostile_compat` returns `False` at distances 1-10) — this is correct,
   expected rejection of an allied pair encountered during ordinary movement, not a bug.

2. **Real hostile faction pairs do exist in both worlds.** Direct pairwise `is_hostile_compat`
   query against the real compiled entity rosters: `bandit_company` is hostile (`enemy`-labeled,
   unconditional) toward every other faction present in both worlds. `dungeon_crawl`:
   `goblin_warband`↔`undead_remnants` mutual, `undead_remnants`→`bandit_company`. Not a
   faction-content gap.

3. **Real hostile pairs start within perception range.** At tick 0, the closest `bandit_company`-
   to-non-bandit distance is 5 (`dungeon_crawl`) and 4 (`urban_political`) — both within the real
   `radius=10.0` perception scan.

4. **`evaluate_entity_intent` genuinely runs for the relevant entities at real volume**
   (439-982 calls per faction per 2000-tick run) — not a dead/unreached code path.

5. **Neighbor detection genuinely finds real hostile targets.** Instrumented
   `SimulationDomainLogic.get_neighbor_view`/`SensoryFilter.filter_saliency` (the real
   candidate-selection chain feeding `evaluate_entity_intent`'s own `neighbors` argument): for
   `bandit_company` entities specifically, a real hostile non-bandit neighbor appears in the final,
   post-saliency-filter `neighbors` list at real, non-trivial volume (78/818 calls in
   `dungeon_crawl`, 1248/406 in `urban_political` — some calls have multiple).

6. **Yet `FactionSemanticsService.is_hostile_compat` is never once called with `bandit_company` as
   either source or target, across either full 2000-tick run.** Direct instrumentation of
   `is_hostile_compat` itself, filtered for any call involving `bandit_company`: **zero matches in
   both worlds.** This means `tactical.py`'s own hostile-detection loop (lines 139-182) never
   reaches its `is_hostile_compat` call for these entities, despite a real hostile neighbor being
   present in the `neighbors` list it iterates.

7. **Root cause, confirmed via manual line-by-line replay of the real loop body against a real
   captured `(state, entity, neighbors)` tuple** (bandit entity 25, single neighbor: entity 12,
   `wild_beast_pack`, real hostile pair per Finding 2): the loop reaches
   `_id_resolver.resolve(entity)` (`EntityIdentityResolver`, `src/entities/identity_resolver.py`)
   for BOTH the bandit and its neighbor. **Both resolve to `faction_id="neutral"`,
   `source="compatibility_projection"`** — not their real, correct `"bandit_company"`/
   `"wild_beast_pack"` (which `get_faction_id_str()`, used everywhere else including this
   session's own faction-semantics tooling, correctly returns for the same entities). The
   subsequent `is_hostile_compat("neutral", "neutral", ctx)` correctly, but uselessly, returns
   `False` — two identical placeholder factions are never hostile to each other.

## The real, precise bug

`EntityIdentityResolver.resolve()` (`src/entities/identity_resolver.py:73-136`) has 4 fallback
paths, tried in order:
- **Path 1 (`clean_metadata`)**: requires **both** `identity.properties["faction_id"]` **and**
  `identity.properties["role_id"]` to be truthy.
- **Path 2 (`runtime_identity_extension`)**: requires both `runtime_faction_id` and
  `runtime_role_id`.
- **Path 3 (`compatibility_projection`)**: maps the entity's raw *legacy* `identity.faction`
  int (the old 4-value `Faction` `IntEnum`: `HERO_GUILD=0`, `MONSTER_HORDE=1`, `TOWN_COUNCIL=2`,
  `NEUTRAL=3`) and raw legacy `identity.role` int through small compat dicts.
- **Path 4 (`legacy_enum`)**: raw enum name, lowest confidence.

**Direct verification against the real corpus**: `EntityIdentityResolver.resolve()` returns
`source="compatibility_projection"` for **100% of entities in both worlds (32/32
`dungeon_crawl`, 30/30 `urban_political`)** — `role_id` is never populated in
`identity.properties` for **any** entity in either corpus, so Path 1 always fails despite
`faction_id` itself being correctly, independently set (confirmed:
`props.get("faction_id") == "goblin_warband"` for a real sampled entity, while
`props.get("role_id")` is `None`).

Path 3 then uses the entity's raw legacy `identity.faction` int — which, for any
content-driven faction that isn't one of the 4 old buckets (`goblin_warband`, `wild_beast_pack`,
`undead_remnants`, `bandit_company` in `dungeon_crawl`; `bandit_company`, `merchant_league` in
`urban_political`), was set to `Faction.NEUTRAL` (`=3`) at spawn time as the closest available
legacy default. Path 3's own `_FACTION_COMPAT` dict then maps `Faction.NEUTRAL → "neutral"`,
**silently discarding the entity's own already-correct `faction_id` string** in favor of this
generic placeholder.

**Real corpus-wide impact, directly measured**: `dungeon_crawl` — all 32/32 entities collapsed to
`faction_id="neutral"` for identity-resolver purposes (100%: `goblin_warband` ×9,
`wild_beast_pack` ×5, `undead_remnants` ×6, `bandit_company` ×12). `urban_political` — 13/30
(43%: `merchant_league` ×9, `bandit_company` ×4) collapsed; the remaining 17/30 (`town_council`
×14, `hero_guild` ×3) happen to map onto 2 of the 4 legacy buckets that still exist, so they
resolve correctly. This is why `urban_political`'s hostile-detection is not *totally* dead (some
real faction identity survives) but `dungeon_crawl`'s is: it has zero entities from any of the 4
legacy-mappable factions.

`tactical.py`'s hostile-detection loop uses `_id_resolver.resolve(entity).faction_id` (via
`EntityIdentityResolver`), **not** the more direct `get_faction_id_str()` helper used everywhere
else (this session's own faction-semantics tooling, `content_semantics/faction.py`, and every
probe in this investigation) — so this bug is invisible to any check that uses the more common
helper, which is presumably why it survived the 2 sibling legality tickets' own investigation.

## What this is NOT
- Not a `resolve_attack()`/`calculate_damage()` bug — combat resolution itself is untouched and
  unreachable by this finding; the block is entirely upstream, in target *detection*.
- Not the `ENABLE_COMBAT_ENGAGEMENT` flag (already ruled out, `TCK-20260806-...-CORPUS-VALIDITY`).
- Not the readiness/`intruding=False` issues already fixed this session — those affect the
  legality check *after* a hostile is already correctly identified; this bug prevents hostile
  identification in the first place, for the majority of the real corpus roster.
- Not a world-content/spatial-pacing limitation — real hostile pairs are real, close, and
  perceived; the block is a pure identity-resolution defect.

## Real fix candidate (for Plan phase)
Path 1 should not require `role_id` to accompany `faction_id` before trusting the entity's own,
independently-correct `faction_id` string. The minimal, additive fix: when `faction_id` is present
but `role_id` is absent, derive `role_id` from `_ROLE_COMPAT.get(entity.identity.role)` (the same
compat map Path 3 already uses) while keeping the real `faction_id` — instead of falling through to
Path 3, which discards `faction_id` too. This preserves Path 1's existing behavior for entities that
already have both fields, and does not touch Path 2/3/4's own behavior for entities with neither
field present.

## Real fix verification (post-Implement)
Applied the Plan-phase fix to `EntityIdentityResolver.resolve()`'s Path 1. Direct before/after
comparison against the same real compiled worlds: **100% of `dungeon_crawl`'s roster and 43% of
`urban_political`'s** now resolve `source="clean_metadata"` with their real, correct `faction_id`
(previously 100%/43% silently collapsed to `"neutral"` via Path 3).

**Real corpus re-verification, 2000 ticks, corpus-default flags** (same live-instrumented
methodology): `verify_attack_legality` is now genuinely called for real hostile pairs that were
**never once checked before this fix** — `goblin_warband`→`undead_remnants` (26 real checks),
`bandit_company`↔`wild_beast_pack` (3), `bandit_company`↔`merchant_league` (2). This is the real,
concrete, falsifiable improvement this ticket exists to produce, and it is confirmed.

**Honest disclosure — the fix does not (yet) produce non-zero `combat_damage`/`entity_killed`
in this specific 2000-tick window.** Every one of the newly-reachable legality checks failed with
`ReasonCode.OUT_OF_RANGE` (attacker `combat.range=1`, i.e. melee/adjacency-only, checked at real
distances of 2-12). `readiness=100.0` in every sampled case — not readiness-blocked. This is a
**different, downstream bottleneck**: entities now correctly detect a real hostile and attempt to
engage, but the pursuit/movement mechanism that should close the distance to melee range does not
appear to converge within this run — a real, separate, further-reaching finding, not swept under
this ticket's own scope. **Not investigated further here** (see Related Tickets for the follow-up
this finding is filed under) — per this ticket's own Acceptance Criteria, this is disclosed
honestly rather than forced into a "fully resolved, non-zero combat volume" claim that the real
data does not support.

## Docs Requiring Update
- `docs/audits/D21_entity_lifecycle_foundation_layers.md` — add a finding documenting this as the
  real, deeper cause behind the "Combat legality always false" section's own residual gap after the
  2 sibling tickets' fixes, and the newly-surfaced pursuit/range-closing bottleneck this fix
  exposed underneath it.
