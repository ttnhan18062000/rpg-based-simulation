---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE
artifact_type: investigation
tags: [core, faction]
---

# Investigation — TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE

## Current Behavior

**The write side is real, typed, and fully idle — confirmed, not assumed.**

- `IdentityComponent.faction: int = 0` (`src/core/state.py:580`) — durable per-entity field, set
  once at construction (`V2EntityBuilder`) and never touched again by any live system.
- `IdentityUpdate.faction_set: Optional[int] = None` (`src/core/updates.py:227`) — the typed
  writer intent. `IdentityUpdate.is_noop()` (`updates.py:245`) and `.merge()` (`updates.py:254-259`)
  both correctly thread `faction_set` through the merge/no-op machinery.
- `ApplyPath` consumes it correctly: `src/engine/patches.py:209` — `if u_id.faction_set is not
  None: fac = u_id.faction_set`, then written into the replacement `IdentityComponent`. This is
  the one and only authoritative apply-path for identity mutation; it is real, correct, and
  tested — it has simply never been called with a non-`None` `faction_set` by any production code.
- `src/engine/apply.py:321` already reacts to a hypothetical faction change:
  `if update.entities_add or any(u.combat is not None or (u.identity is not None and
  u.identity.faction_set is not None) for u in update.entity_updates.values()): pass_hostile =
  None` — invalidates the `_has_hostiles_or_dead_cache` whenever a faction_set write occurs. This
  wiring is real and already correct; it has simply never fired because `faction_set` is never
  populated.
- **Confirmed zero real producers** (`grep -rn "faction_set" src/`): the only 4 hits in `src/` are
  the field declaration (`updates.py:227`), the `is_noop`/`merge` plumbing (`updates.py:245,259`),
  the apply-path consumer (`patches.py:209`), the cache-invalidation check (`apply.py:321`), and
  one *read* of `faction_set` in `src/observability/event_shapers.py:1392` (the `faction_extinct`
  event's `_current_faction()` helper, which reads `id_upd.faction_set` if present, else falls
  back to `prior_ent.identity.faction` — this is a consumer of a hypothetical write, not a
  producer). This exactly reconfirms `tickets/done/TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-
  OBSERVABILITY-GAP`'s own finding (`docs/audits/D21_entity_lifecycle_foundation_layers.md`
  "IDENTITY — hard ceiling" section): "no code anywhere in `src/` ever constructs an
  `IdentityUpdate` with either field set."

**The `entity_faction_changed` observability event genuinely IS wired and diff-based, not
gated on `faction_set` at all** (`src/observability/event_extractor.py:410-416`):
```python
if _is_real_number(ident.faction, prior_ident.faction) and ident.faction != prior_ident.faction:
    events.append(SimulationEvent(event_type="entity_faction_changed", ...))
```
It compares `entity.identity.faction` before/after the tick directly — it will fire correctly the
moment *any* mechanism makes `identity.faction` actually change post-apply, regardless of whether
that change came through `faction_set` or (incorrectly) a direct mutation. This means AC #2
("`entity_faction_changed` fires exactly once per real faction change") is very likely already
satisfiable by the existing extractor with zero changes to it — the real work is entirely on the
producer side, not the observability side. Verified via `tests/unit/observability/
test_event_extractor_identity.py::test_entity_faction_changed_fires_on_real_delta` (hand-built
state pattern, already passing).

**Combat/action-legality blast radius is wider than the ticket's cited 6 sites.** The ticket cites
6 `legality.py` lines (269, 451, 521, 530, 543, 556) — all confirmed real. A full
`identity\.faction\b` grep across all of `src/` (not just `legality.py`) finds **31 real call
sites across 15 files**, not 6:

| File | Lines | Nature |
|---|---|---|
| `src/engine/legality.py` | 269, 451, 521, 530, 543, 556 | attack/flank/engagement legality (the ticket's cited 6) |
| `src/ai/goals/scorers.py` | 108 | hostile-detection for goal scoring |
| `src/api/presenters/state_presenter.py` | 117, 144, 146 | read-model shaping (API surface) |
| `src/certification/harness.py` | 103, 178, 304 | certification harness alive-faction set |
| `src/content_semantics/faction.py` | 49 | `get_faction_id_str()` fallback path |
| `src/core/state.py` | 1394, 1396 | homogeneity check (likely group/party helper) |
| `src/domains/campaigns/orchestrator.py` | 514 | campaign orchestration |
| `src/domains/cooperation/providers.py` | 50 | cooperation candidate filtering |
| `src/engine/cognition.py` | 44, 117 | in-group/out-group cognition |
| `src/engine/combat.py` | 538 | combat resolution friendly-fire check |
| `src/engine/semantic_entity_index.py` | 163 | faction-bucket index |
| `src/entities/identity_resolver.py` | 96, 112, 119, 125, 132, 145 | legacy/compat faction resolution (5 sites) |
| `src/systems/strategic_systems/intelligence.py` | 149, 327, 328, 413 | strategic intelligence hostile detection |
| `src/systems/world_systems/intake.py` | 30, 44 | world intake faction filtering |
| `src/world/environment.py` | 83 | hero-guild environment check |

None of these 31 sites cache `identity.faction` across ticks in a way that would go stale from a
mid-tick change beyond what `apply.py:321`'s existing `pass_hostile` cache-invalidation already
covers — but `semantic_entity_index.py:163`'s faction-bucket index and any cached spatial/hostile
lookups elsewhere (`_has_hostiles_or_dead_cache`, `SpatialQueryService`) must be re-audited at
implementation time for the same class of staleness `apply.py:321` was already built to prevent
for combat/hostile caches specifically — this ticket's Plan phase should not assume `apply.py:321`
alone covers every cache that reads `identity.faction`.

**No real, live producer with faction-aware semantics exists to reuse.** Candidates investigated:
- `PartyLifecycleService.check_defection()` (`src/systems/social_systems/party_lifecycle.py:143`,
  SOC-230) — **the single most evidence-grounded real, live, wired trigger** found. It is called
  from a real pipeline phase (`src/engine/pipeline_phases/groups.py:135`), fires a real
  `BetrayalDesertionEvent`, and returns a real `EntityUpdate` (currently only `social.
  notoriety_delta=2.0`). However: `GroupRecord` (`src/core/state.py:659-679`) carries **no faction
  field at all** — groups/parties are faction-agnostic coordination units (confirmed via grep,
  zero `faction` references anywhere in `party.py`/`party_composition.py`/`party_lifecycle.py`/
  `group_service.py`). Reusing this trigger for `faction_set` would require new design work to
  decide what faction a defector joins (there is no "rival faction" context available inside
  `check_defection`'s current signature) — real, but not a drop-in reuse.
- `SocialContractSystem.resolve_contract_outcome(betrayal=True, betrayer_id=...)`
  (`src/systems/social_systems/contracts.py:184`) — real, tested, betrayal-aware logic
  (avenge directive, turning point, notoriety). **Confirmed NOT live**: its own docstring
  (`contracts.py:270-280`, `compute_betrayal_clan_reputation_update`) states the sole production
  caller, `process_active_contracts()`, never passes `betrayal=True`/`betrayer_id` — "a
  pre-existing gap this ticket discloses but does not fix." Same dormant class as this ticket's
  own target field, not a real existing trigger to build on.
- `src/engine/faction_decision.py` (`FactionDecisionPhase`) — operates entirely on
  `FactionState`/`FactionDirective` (faction-vs-faction diplomacy, tension, treaties). No path
  from a faction-level directive to an individual entity's `identity.faction` exists or is implied
  by this module.
- `src/domains/culture/applicator.py` (`CulturalBiasApplicator`) — confirmed (per
  `rpg_culture_drift_hardening_plan.md`, cross-referenced via the epic doc) real, live, and tested,
  but it is a **region-level culture-bias reader**, not an entity-affiliation writer; it has no
  connection to `identity.faction` today.
- `FactionInfluenceService.process_conquest_lifecycle()` (`src/world/influence.py:77-116`) — a
  real, live conquest mechanic, but it operates on **region ownership**
  (`WorldUpdate.owner_faction_id_set`) and spawns/despawns stronghold entities. It does not touch
  any existing entity's `identity.faction` — extending it to "reassign resident entities' faction
  on regional conquest" would be a materially larger design decision (which entities, what
  radius, what tick semantics) than this ticket's own scope implies, and is not implied by any
  current code.

**`src/replay/fingerprint.py` does NOT currently cover `identity.faction` or `identity.role` at
all** — a second, distinct gap AC #6 already anticipates. `StateFingerprinter.get_fingerprint()`
(`fingerprint.py:32-72`) builds one string per entity covering `kind`, `position`, `hp`, `gold`,
`current_project`, `current_objective`, `readiness`, `active`, `skills=len(learned_skills)`,
inventory, bonds, reputation — **no `faction` or `role` term anywhere**. This is the lightweight
"is replay-visible gameplay state consistent" fingerprint, used by `src/worldbuilding/
compiler.py:730` and `src/core/state.py:1484-1485` — distinct from the full determinism hash
(`CanonicalStateHasher`, `src/engine/checkpoint.py:38`), which is fed by `IdentityComponent.
to_canonical_dict()` (`state.py:601-620`) and **does** already include `"faction": self.faction`
(line 606) — so full replay/certification determinism is already covered, but the lighter-weight
fingerprint used by the world compiler and `AuthoritativeState`'s own convenience method is not.
This is exactly the failure class the ticket's own AC #6 flags re: PR #128 — a real, currently-
open gap that must be closed by this ticket if `faction_set` becomes live (adding `role=` and
`faction=` terms to the per-entity fingerprint string).

## Mechanics / Engine Constraints

- **No Mechanics Bible chapter exists to constrain this** — confirmed via the roadmap's own audit
  (`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`, "no social/relationship/reputation/
  political chapter" finding) and the ticket's own text. There is no chapter-level formula this
  implementation must match; `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` is the eventual home.
- `docs/engine/authoritative_mutation_pipeline_contract.md`'s general apply-path law still applies:
  durable mutation must go through the typed `IdentityUpdate` → `ApplyPath`/`patches.py` route,
  never a direct `replace(entity.identity, faction=...)` outside that path. This is the same
  architecture rule `tests/architecture/test_social_write_paths.py` already enforces for
  `SocialComponent.public_reputation`/`regional_reputation` (single-authoritative-writer pattern,
  `TCK-20260904-REPUTATION-LOCALITY-SCOPE`) — a directly reusable precedent for a new architecture
  guard test on `faction_set=`/`identity.faction=` write sites (see Anti-Drift Hazards).
- `docs/engine/kernel.md`'s 7-phase deterministic loop and `docs/core/state.md`'s immutability law
  constrain the trigger to be a pure function producing a typed `EntityUpdate`/`IdentityUpdate`,
  consistent with every other social-systems trigger in this codebase (`check_defection`,
  `resolve_contract_outcome` both already follow this pattern exactly).
- `docs/parity_ledger/schema.json` governs the shape of any new parity entries.

## Docs Requiring Update

- `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md`: once idea 39 is implemented,
  the epic's own "3 child tickets scoped... none yet implemented" status line and idea-39 bullet
  must be updated to reflect landed status and the actual trigger chosen (currently describes only
  the pre-implementation state).

Two docs were considered and deliberately excluded from the Format-1 list above, worth naming
explicitly since both are directly implicated by this ticket's own text:

The full Mechanics Bible chapter for social/political mechanics (no `docs/mechanics/0N_*.md` file
exists yet to add a section to) is not required to change here: authoring that chapter is
`TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER`'s own separate scope, and this ticket's own Scope
section explicitly says to cross-reference rather than duplicate it. A minimum-viable contract doc
(e.g. a new `docs/world/affiliation_mutation.md` or an addition to an existing `docs/world/`
contract doc) **is** required by this ticket's own AC #4 ("documented in a real, citable doc") —
that specific new/modified path cannot be named precisely until the Plan phase picks the actual
doc location, so the implementer/doc-updater must add the concrete Format-1 bullet for it once
chosen; it is not omitted from scope, only from this list because the exact path is not yet a
Plan-phase decision.

`docs/event_ledger/entity.yaml`'s `ENTITY-015` entry already carries the correct verdict for
`entity_faction_changed` (wired-but-dormant, per `TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-
OBSERVABILITY-GAP`) and does not need a status change from this ticket's perspective alone: the
event's wiring is not changing, only its trigger rate. Whoever implements should re-check whether
`ENTITY-015`'s status flips from its current dormant framing once a live producer exists, but
that is a fires-at-real-volume question (same class as `docs/audits/D21_...md`'s own distinction
between "wired" vs "fires in practice"), not something this investigation can resolve before a
trigger is chosen.

## Parity Ledger Overlap

The roadmap's own audit (`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`, "Idea 39 ... is
the single widest cross-ledger idea ... (5 of 8 ledger files)") predates a real structural change:
`docs/parity_ledger/faction.yaml` was added as a **9th canonical ledger file**
(`INFRA-399`, `TCK-20260826-PARITY-FACTION-CANONICAL-SCAN`) — the "5 of 8" framing in the roadmap
doc is now stale phrasing (should read "5 of 9" if the same subsystems apply, or the count should
be re-verified against the current 9-file canonical set at Plan time). This investigation did not
find a `faction.yaml` (FAC-XXX) entry that plainly requires a change for an *individual entity's*
`identity.faction` mutation — all 15 `faction.yaml` entries (FAC-001 through FAC-015,
FACTION-TENSION-001) concern `FactionState`-level records (tension, diplomacy, siege, military
conflict), not per-entity affiliation. Whether idea 39's implementation should also touch
`faction.yaml` depends on the trigger chosen at Plan time (e.g. if the mutation intentionally
folds into `FactionState.tension_level`/diplomatic consequences).

Relevant existing entries by ledger file (none require a status change from this investigation
alone; new entries will be needed once the implementation lands):

- `docs/parity_ledger/substrate.yaml` `SUB-378` (`status: verified`) — the existing entry for
  `entity_role_changed`/`entity_faction_changed` observability wiring. Directly adjacent: this
  ticket makes the field this entry's event watches actually live. A new substrate.yaml entry (or
  an amendment to SUB-378's own evidence) covering the real producer is likely needed.
  `SUB-384`/`INFRA-330` (monster-role mistagging fix, cited in `docs/audits/
  D21_entity_lifecycle_foundation_layers.md`) is adjacent context, not directly overlapping.
- `docs/parity_ledger/combat_movement.yaml` — no entry found by name matching `faction` in this
  file's `text:` fields directly, but `LegalityServiceV2`'s 6 cited call sites live in this
  ledger's subsystem; a new entry documenting the chosen mid-tick-vs-next-tick-boundary semantics
  (AC #3) belongs here.
- `docs/parity_ledger/strategic_cognition.yaml` `STRAT-252` (adventure-directive threading, cited
  in `src/engine/faction_decision.py`'s own docstring) — adjacent, not directly overlapping;
  `src/systems/strategic_systems/intelligence.py`'s 4 `identity.faction` read sites are the real
  overlap surface for this ledger and currently have no entry name-matching "faction" that this
  investigation found.
- `docs/parity_ledger/social_narrative.yaml` — `check_defection`/`BetrayalDesertionEvent` (SOC-230)
  and contract betrayal (SOC-268, `compute_betrayal_clan_reputation_update`) both live in this
  ledger's subsystem; if the Plan phase chooses either as (part of) the trigger, a new entry here
  is required. No P0 entries were found directly matching `faction` in this file.
- `docs/parity_ledger/world_dynamics.yaml` — one entry, text "Spawned entity faction is valid"
  (construction-time only, not a mutation concern) — likely the 5th of the roadmap's originally-
  cited 5 files; not a blocking overlap for this ticket's mutation-primitive scope.
- No P0 entries were found anywhere across the 9 ledger files with `text` directly describing
  entity-level `identity.faction` mutation — the closest P0, `faction.yaml`'s `FAC-013`
  (`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`), concerns FACTION observability cutover, a
  different subsystem layer (FactionState-level, not entity-level).

## Prior Work

- `tickets/done/TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP` — already
  investigated and confirmed zero real `role_set`/`faction_set` producers exist, and wired
  `entity_role_changed`/`entity_faction_changed` anyway (future-proof, per explicit prior user
  direction). This ticket's own event-extractor work is DONE and requires no changes — confirmed
  above (diff-based, fires on any real `identity.faction` delta regardless of producer).
- `docs/audits/D21_entity_lifecycle_foundation_layers.md` — "IDENTITY — hard ceiling" section is
  the canonical prior statement of this exact gap: "a genuine missing mechanic (promotion,
  defection-changes-faction, tamed-monster-joins-faction, etc. would all need real design work),
  out of scope for 'make the existing foundation solid.'" This ticket is that real design work.
- `tests/architecture/test_social_write_paths.py` (`TCK-20260904-REPUTATION-LOCALITY-SCOPE`) — a
  directly reusable pattern for a new architecture guard restricting `faction_set=`/direct
  `identity.faction=` writes to the authoritative apply-path only.
- `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md` — parent epic scope and
  sequencing decision (idea 39 first, single contract, not split into primitive/trigger pair).

## Risks and Open Questions

- **Central open design question (not resolved here, per this ticket's own Assumptions section):**
  what concrete trigger populates `faction_set`? No candidate investigated above is a clean,
  already-faction-aware, already-live drop-in. `check_defection` is the most evidence-grounded
  *live* mechanic but needs new design (a destination faction) since `GroupRecord` carries no
  faction context today. This is a real scope decision for the Plan phase, not something
  Investigate should assume an answer to — flagging explicitly rather than guessing.
- **Mid-tick vs next-tick-boundary semantics (AC #3) is unresolved and has real correctness
  consequences.** `apply.py:321` invalidates `pass_hostile`/`_has_hostiles_or_dead_cache` whenever
  `faction_set is not None`, meaning a same-tick reassignment is visible to `legality.py`'s cache
  immediately — but 5 of the 6 cited `legality.py` call sites, plus most of the additional 25
  sites found in this investigation, do not obviously re-check this cache mid-resolution within a
  single tick's action-execution order. The Plan phase must decide and test whether an entity that
  changes faction mid-tick can still be legally attacked (or become newly illegal to attack) by an
  action already queued/resolved earlier in the same tick's phase order.
- **`faction.yaml`'s existence as a 9th canonical ledger file is new** (added 2026-08-26, after
  this ticket's own epic doc was last edited with the "5 of 8" framing) — the Plan/Parity phases
  must re-verify the actual affected-file count against the current 9-file canonical set rather
  than trusting the epic doc's stale "5 of 8" number.
- **`src/replay/fingerprint.py` gap is real and separate from the `CanonicalStateHasher` coverage**
  — `to_canonical_dict()` already includes `faction`, but the lighter `StateFingerprinter` (used
  by `worldbuilding/compiler.py` and `AuthoritativeState`'s own convenience method) does not. Not
  fixing this if `faction_set` goes live would exactly repeat the PR #128 failure class the
  ticket's own AC #6 already names.
- **Blast radius is 31 real call sites across 15 files, not the 6 originally cited** — the Plan
  phase must decide whether all 31 need direct re-verification, or whether a smaller subset
  (identified via which caches/derived structures persist `identity.faction` across a tick vs.
  read it fresh) is sufficient. `src/entities/identity_resolver.py`'s 5 sites in particular
  concern *legacy compatibility resolution*, a different concern from live combat legality, and
  may not need the same mid-tick correctness treatment.

## Anti-Drift Hazards

- **Do not invent a parallel write path.** `patches.py:209` and `apply.py:321` are real, correct,
  and already wired — the entire implementation surface for this ticket is (a) a new trigger that
  constructs `IdentityUpdate(faction_set=...)`, and (b) closing the two disclosed gaps (fingerprint
  coverage, doc citation). Nothing in `apply.py`/`patches.py` itself should need to change.
- **Do not silently expand scope into idea 56 (Drifting Loyalty).** The temptation, given that
  `check_defection` is the most evidence-grounded live trigger and grievance accumulation is
  itself a "drift" mechanism, is to reach toward a loyalty-pressure model. That is explicitly idea
  56's own scope (`TCK-20260905-DRIFTING-LOYALTY-SIGNAL`), sequenced *after* this ticket — this
  ticket must land a real trigger that does **not** require idea 56 to exist first.
  `check_defection`-based or any other trigger chosen here must be self-contained.
- **Do not conflate `FactionState`-level mechanics (`faction.yaml`, `src/engine/
  faction_decision.py`, `src/domains/faction/`) with entity-level `identity.faction`.** They are
  different subsystems today with no code path connecting them; a trigger that reaches into
  `FactionState`/diplomacy to decide an entity's new faction is a much larger design surface than
  this ticket's own scope implies unless deliberately chosen and documented as such.
- **Do not assume the 6 cited `legality.py` sites are the full blast radius** — 25 additional real
  call sites exist (see table above); a regression suite or manual review that only re-checks the
  original 6 will miss real risk surface, particularly `src/engine/combat.py:538`,
  `src/engine/cognition.py:44,117`, and `src/systems/strategic_systems/intelligence.py`'s 4 sites,
  all of which drive live hostile-detection/goal-scoring decisions.
- **Do not skip the `src/replay/fingerprint.py` fix because `to_canonical_dict()` already covers
  `faction`.** They are two distinct hash mechanisms serving different callers
  (`CanonicalStateHasher` vs `StateFingerprinter`) — AC #6 requires the lighter one be fixed too.
