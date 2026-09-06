---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260905-CHRONICLE-FIDELITY-DRIFT
artifact_type: investigation
tags: [social, strategy]
---

# Investigation — TCK-20260905-CHRONICLE-FIDELITY-DRIFT

## Current Behavior

**CultureDeriver — the pattern this ticket must mirror** (`src/domains/culture/deriver.py:42-116`):
a stateless `classmethod derive(hierarchy, entity_names=None) -> Dict[str, CultureState]`
(`deriver.py:48-111`) that iterates `hierarchy.events` (a flat `tuple[NarrativeLedgerEntry, ...]`),
classifies `entry.event_type` against fixed frozensets (`_FATALISM_EVENTS`, `_CONFLICT_EVENTS`,
`_SCARCITY_EVENTS`, plus a compound `entity_death` payload branch, `deriver.py:82-94`), accumulates
`entry.significance` additively per grouping key (`entry.payload.get("region_id", "__global__")`,
`deriver.py:78`), then normalises via `min(1.0, raw / NORMALISE_DENOMINATOR)` with
`NORMALISE_DENOMINATOR = 3.0` (`deriver.py:35,113-115`).

**CultureState/CultureCarryForward — the model shape to mirror** (`src/domains/culture/model.py`):
`CultureState` is a `@dataclass(frozen=True, slots=True)` (`model.py:24`) with float axes defaulting
to `0.0`, plus `to_dict()`/`from_dict()`. `CultureCarryForward` (`model.py:69`) wraps
`region_id: str`, `culture: CultureState`, `derived_episode: int`.

**CultureDriftExporter/Importer — the exporter shape to mirror, and a critical divergence from
what this ticket's own Scope text claims** (`src/domains/culture/exporter.py`):
`CultureDriftExporter.export(campaign_state, hierarchy, episode_index, entity_names=None)`
(`exporter.py:30-61`) calls `CultureDeriver.derive()` then writes
`campaign_state.region_cultures[region_id] = CultureCarryForward(...)` **directly, in a plain
Python `for` loop, mutating the dict in place** (`exporter.py:56-61`). There is no typed Update
object and no `src/engine/patches.py` involvement anywhere in this write path.
`CultureDriftImporter.get_culture()` (`exporter.py:64-79`) is a thin `None`-safe dict lookup.

**Episode-boundary call site** (`src/domains/campaigns/orchestrator.py:242-246`, inside
`_advance_state()`): after `narrative_ledger.extend()` and social-memory/grief/nemesis updates,
`ChronicleGrouper().group(list(self._state.narrative_ledger))` builds the hierarchy, then
`CultureDriftExporter.export(self._state, _hierarchy, summary.episode_index)` is called, immediately
before `self._state.episode_index += 1`. This is the exact call site AC3 requires the new
`FidelityExporter.export()` to run alongside.

**`src/engine/patches.py` scope — confirmed unrelated to `CampaignState`**
(`src/engine/patches.py:1-806`): this module defines `ComponentPatch` and its 16 subclasses
(`KindPatch`, `LifecyclePatch`, `BiologicalPatch`, ... `CognitionPatch`), each operating on a
per-entity `EntityState`/`changes: Dict[str, Any]` pair inside the Kernel's tick-level
Resolution/Cleanup phases (`extract_patches()`, `patches.py:740-805`, consumes an `EntityUpdate`).
**Nothing in `patches.py` reads or writes `CampaignState` at all** — confirmed by reading the full
file and cross-checking `TCK-20260518-COMPONENT-PATCH-MODEL` (the ticket that created this module,
scoped explicitly to `EntityUpdate`→`ComponentPatch`, no `CampaignState` mention) and
`TCK-20260904-LINEAGE-DEATH-DISPATCH` (a same-epic sibling ticket that *does* use `patches.py`
correctly — but for a per-entity `EntityState` write via `CognitionPatch`/`StrategicPatch` inside
`resolve_lifecycle`'s Kernel-tick code path, not for a `CampaignState` field). Every existing
`CampaignState` field (`region_cultures`, `grief_urgencies`, `nemesis_relations`,
`persistent_entities`, `persistent_factions`, `progression_plans`, `social_memories`,
`narrative_ledger`) is written via direct dict/list mutation inside `CampaignOrchestrator`
methods (`orchestrator.py:216-247` `_advance_state()`, confirmed line-by-line) — **none** go
through `patches.py` or any equivalent typed-apply mechanism, because `CampaignState` lives entirely
outside the Kernel's per-tick authoritative pipeline (it is populated once per completed episode,
from the episode's already-finalized `AuthoritativeState`). See Risks below — this is a direct
contradiction inside the ticket's own Scope text.

**ChronicleGrouper era structure — a non-obvious detail for `FidelityDeriver`'s own
implementation** (`src/domains/chronicle/grouper.py:170-227`): `Era.episodes` is a batch of
`ERA_EPISODE_MIN=3` **consecutive elements of the already-filtered `episodes` list** (i.e., only
episodes that contain at least one chronicle-worthy incident), not a batch of 3 consecutive raw
episode-index values (`_group_eras()`, `grouper.py:199-227`, `range(0, len(episodes),
ERA_EPISODE_MIN)`). If an episode produced zero chronicle-worthy events, it is absent from
`episodes` entirely and does not consume an era "slot." A naive `era_ordinal = entry.episode //
ERA_EPISODE_MIN` computation would silently diverge from the real era membership whenever any
episode in the campaign has zero chronicle-worthy events — `FidelityDeriver` must walk
`hierarchy.eras` → `Era.episodes` → `Episode.index` to find the real era ordinal containing a given
event's `episode`, not compute it arithmetically.

**BeliefEntry — confirmed structurally mismatched, per the ticket's own Out-of-Scope claim**
(`src/systems/strategic_systems/belief.py:23-34`): `BeliefEntry` is a
`@dataclass(frozen=True, slots=True)` stored on `StrategicComponent.beliefs: Dict[str, Any]`
(per-entity, `src/core/strategic.py:425`), with fields `certainty`, `source`
(`observation`/`rumor`/`deduction`), `contradictions`, and a `last_refreshed_tick`/
`ticks_since_discovered` decay model (`BeliefCycleSystem.decay_stale_beliefs()`,
`belief.py:42-79`). Real live consumers confirmed: `src/domains/cooperation/evaluators.py`,
`src/systems/strategic_systems/detour.py` (`_score_detour()` reads
`matching_belief.contradictions`), and guild rumor propagation. This is a per-entity,
tick-granularity record — there is no population/generation-scale grouping concept anywhere in this
class. Confirms the ticket's Out-of-Scope claim: do not repurpose it.

**No existing code implements any fidelity/distortion/misremember-style degradation** — confirmed:
zero matches for `fidelity`, `distortion`, `misremember` anywhere in `src/`, and the new
`campaign_state.historical_drift`-shaped field does not exist yet in
`src/domains/campaigns/state.py` (read in full — only `region_cultures`, `grief_urgencies`,
`nemesis_relations`, and the other fields listed above exist).

## Mechanics / Engine Constraints

- `docs/simulation/domains/chronicle_contract.md` (§Pipeline Overview): "All stages are stateless."
  `FidelityDeriver` must uphold the same no-durable-state, deterministic-given-sorted-input
  contract Chronicle itself is held to — directly matches AC2 (determinism guard).
- `docs/mechanics/05_world_evolution.md` §7 "Cultural Drift (E62)" (lines 555-599): documents
  `CultureDeriver`'s exact axis-derivation/normalisation/persistence/motivation-overlay shape as a
  Certified Level-1 chapter. `FidelityDeriver` is a direct structural sibling operating at the same
  episode-boundary cadence over the same `ChronicleHierarchy` substrate — the precedent this
  section sets (a dedicated numbered subsection per Deriver-pattern mechanism) is the correct home
  for documenting this new mechanism, per the Authoritative Mechanics Rule ("all logic changes MUST
  be consistent with... and documented in... the Mechanics Bible").
- `docs/world/culture_drift_contract.md`: standalone per-mechanism contract file (not folded into
  `chronicle_contract.md`) documenting `CultureDeriver`'s Model/Derivation/Persistence/Overlay/
  Integration-Points sections. This is the direct structural precedent for a new
  `docs/world/chronicle_fidelity_contract.md`-shaped doc (see Docs Requiring Update).
- `src/domains/culture/model.py`'s own docstring constraint, restated by the ticket's Scope: "MUST
  NOT import from `src.engine` or `src.core.state` at module level" — the new `FidelityState`/
  `FidelityCarryForward` model must uphold the same constraint `CultureState`/`CultureCarryForward`
  do, confirmed live in the actual file header.
- Durable State Rule (project CLAUDE.md): "If something survives beyond the current tick or current
  function call, it must have a typed model... a defined lifecycle... and tests." The new
  `campaign_state.historical_drift` field satisfies this if built exactly like `region_cultures`.

## Docs Requiring Update

- `docs/mechanics/05_world_evolution.md`: new subsection (e.g. "8. Chronicle Fidelity Drift")
  mirroring §7 "Cultural Drift (E62)"'s own structure (axis/value definitions, derivation trigger,
  persistence, acceptance signal) — required per the Authoritative Mechanics Rule, since this ships
  new simulation logic with no existing chapter coverage.
- `docs/world/chronicle_fidelity_contract.md` (new file): a dedicated per-mechanism contract
  mirroring `docs/world/culture_drift_contract.md`'s own structure (Model / Derivation / Persistence
  / Integration Points / Parity Ledger References) — the established precedent for this exact
  Deriver-pattern-sibling shape, not folded into `chronicle_contract.md` (which documents the
  Chronicle domain's own pipeline, not its downstream consumers — see excluded doc below).
- `docs/parity_ledger/world_dynamics.yaml`: new entries (e.g. `WORLD-FIDELITY-001`+) covering
  fidelity-decreases-with-era-distance derivation and the determinism guarantee — mirrors the
  `WORLD-CULT-001..003` precedent set by `CultureDeriver`, the direct sibling this ticket mirrors;
  new mechanisms require ledger coverage per the Authoritative Mechanics Rule's Parity section.

The following were considered and are **not** required to change:

The `docs/simulation/domains/chronicle_contract.md` doc (path:
`docs/simulation/domains/chronicle_contract.md`) is not required to change for this ticket: it
documents the Chronicle domain's own five-stage pipeline (significance → grouper → naming →
renderer → compiler → REST) and explicitly does not list downstream consumers of its output —
confirmed by direct read: `CultureDeriver`, an already-shipped, live downstream consumer of
`hierarchy.events`, is not mentioned anywhere in this file either. `FidelityDeriver` is another
downstream consumer following that same established non-listing precedent.

The `docs/parity_ledger/social_narrative.yaml` doc (path:
`docs/parity_ledger/social_narrative.yaml`) is not required to change for this ticket: its
`SOC-CHRON-*` entries document the Chronicle domain's own pipeline stages, not downstream derivers
that read `ChronicleHierarchy` output — `CultureDeriver`'s own parity coverage
(`WORLD-CULT-001..003`) already precedent-sets that downstream Deriver-pattern siblings get their
entries in `world_dynamics.yaml` instead of here.

The `docs/brainstorm/rpg_feature_atlas.html` doc (path: `docs/brainstorm/rpg_feature_atlas.html`)
is not required to change for this ticket: idea 62's card already accurately frames the proposal as
"Aspirational — design only... sequence alongside idea 57." This ticket's own Scope explicitly
discloses it ships with no live consumer yet (idea 63 is the real eventual consumer, not yet built)
— the atlas card's framing remains accurate after this ticket lands, unlike a ticket that fully
closes the gap the card describes.

The `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` doc (path:
`docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`) is not required to change for
this ticket: its idea-62 section was already corrected as of 2026-09-05 (the two premise errors
this ticket's own Request Summary re-confirms) — this ticket implements what that corrected text
already describes, it does not change the epic-level scoping/correction narrative itself.

The `docs/guidelines/intentional_divergences.md` doc (path:
`docs/guidelines/intentional_divergences.md`) is not required to change for this ticket: this adds
new functionality (a Deriver-pattern sibling with no existing mechanic to diverge from), not an
intentional behavior shift away from a previously documented V2 law.

## Parity Ledger Overlap

- `WORLD-CULT-001`, `WORLD-CULT-002`, `WORLD-CULT-003` (`docs/parity_ledger/world_dynamics.yaml`,
  all `status: verified`, `priority: P1`) — cover `CultureDeriver`'s own derivation/overlay/
  acceptance-signal behavior. Not modified by this ticket (`CultureDeriver` is explicitly untouched
  per Scope/Out-of-Scope and AC5), but the closest existing precedent for how this ticket's own new
  entries should be shaped and where they belong.
- `SOC-CHRON-001` through `SOC-CHRON-005` (`docs/parity_ledger/social_narrative.yaml`, all
  `status: verified`, `priority: P1`) — cover Chronicle's own significance/grouping/naming/
  rendering/REST pipeline stages. Not modified by this ticket (Out of Scope explicitly excludes
  `grouper.py`/`significance.py` changes).
- No `P0` entries overlap this ticket's scope — no blocking "must have a passing `test_path`"
  requirement inherited from existing ledger entries.
- No existing entry anywhere in the parity ledger describes fidelity/distortion/generational-drift
  behavior — confirmed via grep across `docs/parity_ledger/*.yaml`. This is a genuine coverage gap
  this ticket's own new entries must fill (see Docs Requiring Update).

## Prior Work

- `TCK-20260619-E62A-CULTURE-MODEL`, `TCK-20260619-E62B-CULTURE-DERIVER` — shipped the exact
  3-layer pattern (`Model`/`Deriver`/`Exporter-Importer`) this ticket mirrors. `E62B`'s own
  investigation (`stored_artifacts/TCK-20260619-E62B-CULTURE-DERIVER/investigation.md`) confirms
  `ChronicleGrouper.group(entries)` was already live at that point — the same substrate this ticket
  reads.
- `TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION` — confirmed `BeliefEntry` and
  `KnowledgeFact` are a deliberate, non-duplicative two-track split (raw observations →
  `BeliefEntry`; structured/queried info → `KnowledgeFact`), both per-entity. Directly supports this
  ticket's Out-of-Scope reasoning: neither is the right shape for population-scale historical drift,
  and this ticket must introduce zero changes to either (AC5).
- `TCK-20260904-LINEAGE-DEATH-DISPATCH` — the same-epic sibling ticket that actually does use
  `src/engine/patches.py` (via `CognitionPatch`/`StrategicPatch`) correctly, but for a per-entity
  `EntityState` write inside `LifecycleSystem.resolve_lifecycle`'s Kernel-tick code path — not a
  `CampaignState` write. Useful contrast: it demonstrates what a genuine `patches.py`-mediated write
  looks like in this codebase, reinforcing that `CampaignState` writes (this ticket's own target)
  are a structurally different, always-direct-mutation path.
- `docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md` — idea 57's own design
  doc for `FameDeriver`, the sibling this ticket must not conflict with. Confirms `FameExporter`
  would be called from the same `_advance_state()` call site "immediately alongside
  `CultureDriftExporter.export()`" — the same call site this ticket's `FidelityExporter` must also
  join, per AC3. No conflict found: `FameDeriver` keys by `subject_id`, this ticket's own Scope
  suggests per-event/per-subject keying is itself a Plan-phase decision, so the exact grouping key
  shape should be picked with an eye to not colliding with `FameCarryForward`'s field naming if both
  land into `CampaignState` around the same time.

## Risks and Open Questions

- **AC4/Scope's "authoritative apply path (`src/engine/patches.py`)" requirement is not achievable
  as literally written, and contradicts the ticket's own "matching CultureDriftExporter's own
  established write pattern" clause in the same sentence.** Confirmed by reading the full
  `patches.py` file and every existing `CampaignState` write site: `patches.py` operates
  exclusively on per-entity `EntityState` inside the Kernel's tick loop; `CampaignState` (including
  `CultureDriftExporter`'s own precedent) is written by direct in-place dict mutation from
  `CampaignOrchestrator._advance_state()`, with zero exceptions found. This is a real, blocking
  open question for Plan, not a nuance to silently paper over: either (a) AC4 should be reworded to
  require "the same direct-mutation-inside-`_advance_state()` pattern `CultureDriftExporter`,
  `GriefUrgencyModifier`, and `NemesisRelation` all already use" (matching real precedent, and
  matching the ticket's own "mirroring CultureCarryForward's exact shape" instruction elsewhere), or
  (b) if a genuinely new `CampaignState`-level typed-apply mechanism is wanted, that is new
  infrastructure work far outside this ticket's stated scope (a new module, not a `patches.py`
  reuse) and needs its own explicit sign-off before Plan proceeds. Do not guess an answer during
  Plan — this must be resolved explicitly, since AC4's own guard test ("no direct state mutation
  exists outside that path") is unimplementable against real precedent as literally worded.
- **Era-distance computation is non-trivial**, per the ChronicleGrouper era-membership finding
  above (era ordinals batch the *filtered* episode list, not raw episode-index arithmetic). Plan
  must specify exactly how `FidelityDeriver` maps an event's `episode` to its real era ordinal
  (walking `hierarchy.eras` → `Era.episodes` → `Episode.index`), and how "current Era" is defined
  when `hierarchy.eras` is empty or has only one era (fidelity of the *only* era's events — should
  it be 1.0, since there's no distance yet, or should a same-era event carry a small non-zero decay
  from its own tick position? AC1 only requires "strictly lower the further... Era is from the
  current Era" across ≥2 Eras — same-era decay is unconstrained by AC1 and must be a Plan decision).
- **Exact fidelity-decay formula (linear/stepped/exponential) is undecided** — flagged already by
  the ticket's own Assumptions section; confirmed still open after investigation, no code precedent
  determines it (`CultureDeriver`'s own normalisation formula, `min(1.0, raw/3.0)`, is a
  saturation curve for a different purpose — accumulating axis strength, not decaying certainty
  over distance — so it is not a directly reusable formula, only a stylistic precedent for "define
  one constant, one pure function").
- **Grouping key granularity (per-event / per-subject / per-region) is undecided** — the ticket's
  own Assumptions flags this as a Plan-phase decision. Investigation confirms `NarrativeLedgerEntry`
  has both `entry_id` (deterministic, globally unique) and `subject_id` (used by `FameDeriver`'s own
  design) available as candidate keys; per-event via `entry_id` is the most literal match to the
  design intent ("a specific recorded event's story degrading") and avoids any key collision with
  `FameCarryForward`'s planned `entity_fame: Dict[str, FameCarryForward]` (keyed by `subject_id`).

## Anti-Drift Hazards

- Do not let `FidelityDeriver` import from `src.engine` or `src.core.state` at module level — same
  constraint `CultureState`/`ChronicleGrouper` are held to; a stateless Deriver reading only
  `ChronicleHierarchy` should never need either.
- Do not let this ticket's new module touch `src/domains/chronicle/grouper.py` or
  `significance.py` — Out of Scope explicitly forbids changing Chronicle's own grouping/scoring
  logic; `FidelityDeriver` must only *read* `ChronicleHierarchy`, exactly like `CultureDeriver`
  does today.
- Do not let the new `campaign_state.historical_drift` field's `to_dict()`/`from_dict()` wiring be
  skipped in `CampaignState.to_dict()`/`from_dict()` (`src/domains/campaigns/state.py:315-404`) —
  `region_cultures` required explicit sorted-key serialization entries in both methods; forgetting
  the equivalent for `historical_drift` would silently break checkpoint round-tripping without any
  test catching it unless a round-trip test is added (mirroring
  `test_exporter_round_trips_through_campaign_state_serialization` in
  `tests/unit/domains/culture/test_culture_exporter.py`).
- Do not let `FidelityExporter.export()`'s call in `_advance_state()` run *before*
  `ChronicleGrouper().group(...)` is (re)computed for the current ledger state, or run against a
  stale/partial hierarchy — it must consume the exact same `_hierarchy` local `CultureDriftExporter`
  already consumes at `orchestrator.py:245-246`, not a separately (and possibly differently) grouped
  copy.
- Do not repurpose `BeliefEntry.contradictions` or `LeadCertainty` naming/shape for `FidelityState`
  — confirmed structurally unrelated (tick-granularity per-entity decay vs. Era-granularity
  population-scale derivation); a superficially similar "certainty degrades over time" framing must
  not tempt copy-pasting fields from `belief.py`.
