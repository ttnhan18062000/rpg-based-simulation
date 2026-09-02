---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260831-ROLE-MODEL-IMITATION
artifact_type: investigation
tags: [strategy, cognition]
---

# Investigation — TCK-20260831-ROLE-MODEL-IMITATION

## Current Behavior

### `EntityState.cognition` — confirmed real, live, and is the correct nesting target

`EntityState` (`src/core/state.py:711-737`) has **two distinct top-level fields** that could be
confused with each other:

- `self_model: SelfModelBundle = field(default_factory=SelfModelBundle)` (`state.py:734`)
- `cognition: CognitionModel = field(default_factory=CognitionModel)` (`state.py:735`)

These are separate bundles, not aliases. `SelfModelBundle` (`src/core/self_model.py:212-249`)
groups four *inward-facing* components: `self_awareness`, `needs`, `capabilities`, `knowledge`
(self-assessment only). `CognitionModel` (`src/core/cognition.py:524-544`) groups five components:
`subjective` (`SubjectiveModel`: perception/knowledge/risk/time/emotion), `memory` (`MemoryModel`),
`motivation` (`MotivationModel`: doctrine/values/role_fit/ambition/moral), `commitment`
(`CommitmentModel`), and **`relationships`** (`RelationshipModel`, `cognition.py:504-516`:
`private_trust: Mapping[int, TrustEntry]`, `public_reputation`, `known_partners`,
`betrayal_records`).

**Answer to the ticket's own open question: the Scope-cited nesting target (`CognitionModel`, the
class backing `EntityState.cognition`) is correct and is what Scope meant — `SelfModelBundle` is
NOT the right target and does not fit.** `SelfModelBundle` is entirely self-directed (how the
entity assesses itself); a role-model/imitation concept ("who does this entity watch/admire") is
inherently other-directed, like `CognitionModel.relationships`, not like anything in
`SelfModelBundle`. If the ticket text elsewhere is read as suggesting `SelfModelBundle`, that
reading is wrong — confirmed by reading both classes' full field lists.

**Post-`DEAD-COGNITION-SCHEMA-DECISION` state confirmed live, not dead.** That ticket
(`tickets/done/TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION.md`) cut `SubjectiveModel.self` (a
`SelfModel`/dead field) and repointed self-model reads to `entity.self_model.*` via
`src/core/cognition_accessors.py` (confirmed: `get_self_awareness`/`get_need_interpretation`/
`get_capability_estimate` all read `entity.self_model.*`; only `get_knowledge_model` reads
`entity.cognition.subjective.knowledge`, `cognition_accessors.py:12-26`). This cut did **not**
remove `CognitionModel` itself, nor `MotivationModel`/`RelationshipModel`/`MemoryModel`/
`CommitmentModel` — those remain live, populated, canonically-hashed sub-components. Regression
test `test_subjective_model_has_no_self_field` (`tests/unit/entity/test_phase11_cognition_model_schema.py:44-46`)
and `test_cognition_canonical_dict_shape_after_self_model_decision` (same file, lines 48-50) are
the guard tests proving the cut landed and stayed landed — worth re-running as part of this
ticket's regression surface since a new sub-component under `CognitionModel` touches the same file.

### `apply.py` reconstruction path — confirmed wholesale, opaque passthrough at every layer

Traced the full chain from an `EntityUpdate` to the reconstructed `EntityState`:

1. `EntityUpdate.cognition_bundle_set: Optional[Any] = None` (`src/core/updates.py:660`) — the
   update-time field. Its type is `Any`, i.e. it holds a **complete new `CognitionModel` instance**,
   not a per-subfield delta.
2. `extract_patches()` (`src/engine/patches.py:748-749`) wraps a non-`None`
   `cognition_bundle_set` into a `CognitionPatch(entity_id, cognition_bundle_set=...)`.
3. `CognitionPatch.apply()` (`patches.py:685-686`): `if self.cognition_bundle_set is not None:
   changes["cognition"] = self.cognition_bundle_set` — sets the whole `cognition` key in the
   `changes` dict to the new object wholesale.
4. `ApplyPath._fast_replace_entity()` (`src/engine/apply.py:611`):
   `object.__setattr__(res, "cognition", changes.get("cognition", getattr(entity, "cognition",
   None)))` — the *only* place `cognition` is read out of `changes`, and it is a single
   `dict.get()` on the whole object, never enumerated field-by-field.

This is genuinely different in kind from `IdentityComponent`/`CombatComponent`, which
`_fast_replace_entity`'s sibling helpers (`_fast_replace_identity`, `apply.py:531-555`; the PH8
derived-stats block, `apply.py:474-527`) reconstruct by hand-listing named fields — the exact
mechanism that has already caused 4 silent-drop incidents this batch when a new field was added to
one of those components but not added to the hand-written reconstruction call. **Nothing in this
`cognition` chain enumerates `CognitionModel`'s own subfields (`subjective`/`memory`/`motivation`/
`commitment`/`relationships`) anywhere.** Adding a 6th sub-component (or extending an existing one)
requires zero changes to `apply.py`, `patches.py`, or `updates.py`'s `EntityUpdate.is_noop()`/field
list *for the reconstruction path specifically* — confirming Scope's claim is correct, not just
plausible.

**A real, distinct hazard this trace surfaced that Scope's note did not check: `EntityUpdate.merge()`
also treats `cognition_bundle_set` as an atomic, last-write-wins value, not a mergeable delta.**
`updates.py:719`: `if other.cognition_bundle_set is not None: changes["cognition_bundle_set"] =
other.cognition_bundle_set` — if two `EntityUpdate`s for the same entity are merged in the same
tick and *both* set `cognition_bundle_set` (e.g. one system updates `motivation`, another updates
the new role-model sub-component, each via its own `dataclasses.replace(entity.cognition, ...)`
built off the same pre-merge `entity.cognition` snapshot), the earlier one's *entire* `cognition`
update — including any unrelated sub-component changes it carried — is silently discarded by the
later one, because neither system's snapshot saw the other's change. This is the same class of bug
(a silent drop) but at a different layer (`EntityUpdate.merge()`, not `apply.py` reconstruction) —
it is **inherent to the wholesale-bundle design already in production for `cognition_bundle_set`/
`self_model_bundle_set`**, not introduced by this ticket, but this ticket's implementation must be
written so any system producing a `cognition_bundle_set` update always bases it on the
freshest available `entity.cognition` and avoids emitting two separate `cognition_bundle_set`-bearing
`EntityUpdate`s for the same entity in the same tick if at all avoidable. Flagged as a risk below,
not a blocker — no evidence today that two systems currently both set `cognition_bundle_set` for
the same entity in one tick (only `SelfModelUpdatePhase`/motivation-writing systems appear to
produce it today, per the accessor/consumer trace), so the collision is currently latent.

### `src/strategy/cognition_capacity.py` — full read

`CapacityService.derive_profile(entity: EntityState) -> CognitionProfile` (`cognition_capacity.py:14-56`)
is a `@staticmethod`, pure function of `entity.attributes` (`intelligence`, `wisdom`, `perception`),
`entity.identity.personality` (`industry`), and `entity.biological` (`sleep_debt`, `hunger`). It
derives `CognitionProfile` (`src/core/strategic.py:363-378` — **a third, distinct "cognition"
concept**, separate from both `CognitionModel` (state schema) and `CognitionProfileDefinition`
(content schema, `src/content/schema.py`, referenced by `RaceDefinition.cognition_profile: str`)):
`max_active_projects`, `max_leads`, `max_concerns`, `max_candidate_zones`, `max_hypotheses`,
`max_turning_points`, `interruption_resistance`, `resistance_multiplier`, `detour_breadth`,
`reserved_detour_depth`, `max_committed_intentions`. Confirmed zero references to `intelligence_tier`,
`race`, `race_id`, or any content-catalog import in this file today — matches the ticket's own
claim exactly.

`CapacityService` takes only an `EntityState`; it does not import `CatalogRepository` or resolve
content at all, unlike `src/content_semantics/faction.py`'s `FactionSemanticsService`. Plugging
`intelligence_tier` in here means either (a) adding a `CatalogRepository`/singleton-service
dependency to `CapacityService` for the first time (a real, non-trivial architectural change to a
function currently documented as "Purely deterministic; does not mutate entity state" with no
content-layer coupling), or (b) computing the imitation-sophistication scaling as a separate
function/service in this same file (or a sibling one) that independently resolves `intelligence_tier`
via the pattern below and does not touch `CapacityService.derive_profile`'s existing signature or
`CognitionProfile`'s existing 11 fields. **This is a real design fork Plan must decide — not
resolved here per the ticket's own instruction not to design the exact shape at Investigate time.**
Nothing in `CognitionProfile`'s current field list is imitation-related, so the "sophistication
scaling" is very unlikely to be a new field bolted onto the existing 11 rather than a wholly new,
smaller derivation.

### Idea 22 (Relationship Roles) — confirmed unrelated code, not reusable as claimed

Idea 22 = `TCK-20260824-RELATIONSHIP-ROLE-FIELD` (done). It added a `RelationshipRole` enum
(`NEUTRAL`/`FRIEND`/`RIVAL`, `NEUTRAL` default) and a `role: RelationshipRole` field
(`src/core/models/social.py:20`) to **`SocialBond`**, which lives under `EntityState.social`
(`SocialComponent`) — a completely different top-level `EntityState` field from `EntityState.cognition`.
It has no relationship to `CognitionModel.relationships` (`RelationshipModel`) beyond both containing
the word "relationship." `DEAD-COGNITION-SCHEMA-DECISION` already investigated and recorded this
exact question ("idea 22 confirmed unrelated/moot", `tickets/done/TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION.md:75`)
for the cognition-schema question specifically — this investigation independently confirms the same
conclusion by reading the actual code.

`SocialBond` requires a `target_id` to already exist as a bond; `RelationshipRole` is a label on an
*existing, bidirectional* social bond record, and the ticket's own Out-of-Scope explicitly forbids
extending that enum. **The only viable "pairing" per the ticket's own scope**: once the new
role-model state exists, an implementation *may* optionally read (or set, using the existing
authoritative `SocialBondUpdate.role_set` path — not a new write path) the watched entity's
existing `SocialBond.role` value to visually surface the role-model relationship as `FRIEND` where
a bond already exists — never inventing a new enum member, never writing to `SocialBond` fields
this ticket doesn't own. This is optional per the ticket text ("suggested pairing, not a hard
dependency") and should stay that way; do not treat it as a hidden requirement.

### `intelligence_tier` consumption path — confirmed to exist and work end-to-end today

Traced from an `EntityState` to `RaceDefinition.intelligence_tier`:

1. `get_race_id_str(entity)` (`src/content_semantics/faction.py:62-66`): `return
   entity.identity.properties.get("race_id")` — reads the race id out of `IdentityComponent.properties`
   (a free-form `Dict[str, Any]`, `state.py:491`). **Note**: `IdentityComponent` has no first-class
   `race`/`race_id` field; race is only reachable via the `properties` dict under the `"race_id"` key,
   confirmed by this function being the only place that reads it this way and by no first-class
   field existing on `IdentityComponent` (full field list read, `state.py:471-493`).
2. `CatalogRepository.get_race(def_id: str) -> Optional[RaceDefinition]` (`src/content/repository.py:435-436`):
   `return self.races.get(def_id)`.
3. `RaceDefinition.intelligence_tier: str` (`src/content/schema.py:141`, required, validated to
   `{"high", "low"}` by `validate_intelligence_tier`, `schema.py:146-151`) — landed by
   `TCK-20260831-SPECIES-INTELLIGENCE-TIER` (confirmed done, all 13 races authored per that
   ticket's own investigation table).

The repository itself is reached via a process-level singleton pattern already established for the
same kind of read (`get_faction_semantics_service()`, `faction.py:21-28`, builds `CatalogRepository`
from `ContentPathConfig().content_root` and calls `repo.load_all()` once). No equivalent
`get_race_semantics_service()` singleton exists yet, but the pattern is directly reusable — this is
the established idiom for resolving catalog data off an entity without re-loading the catalog per
call, and is what `CapacityService` (if it takes on this dependency) or a new imitation-sophistication
service should follow rather than inventing a new access pattern.

This confirms the path is real, exists today, and requires zero new plumbing to *read*
`intelligence_tier` for a given entity — only a decision (Plan's) about where the read is wired in.

### Round-trip serialization precedent for `EntityState`/`CognitionModel` sub-components

There is no discrete "deserialize from dict" step anywhere for these frozen dataclasses — they are
reconstructed only via the constructor or `dataclasses.replace(...)`. The established "round trip"
test idiom for a new `CognitionModel` sub-component, demonstrated by
`tests/unit/entity/test_phase11_cognition_model_schema.py`:
- `test_entity_state_has_default_cognition_model` (lines 23-30): default-construct an `EntityState`
  and assert `isinstance` checks on every `cognition.*` sub-component.
- `test_cognition_model_default_is_empty_and_safe` (32-35): `CognitionModel.empty()` produces safe
  defaults.
- `test_cognition_model_serializes_deterministically` (37-40): two independently empty-constructed
  instances produce `==` `to_canonical_dict()` output — this is the operative "round trip" proxy:
  determinism/stability of the canonical dict, since `to_canonical_dict()` is the single code path
  used both for the canonical hash (`CanonicalStateHasher.to_canonical_data`,
  `src/engine/checkpoint.py:63`, per `SelfModelBundle`'s own docstring, `self_model.py:217-222`) and
  for inspection/debug exports.
- `test_subjective_model_has_no_self_field` / `test_cognition_canonical_dict_shape_after_self_model_decision`
  (44-50): shape assertions (field/key presence or absence) as regression guards against schema
  drift.

`RaceDefinition.intelligence_tier`'s own "round trip" test (`tests/unit/content/test_catalog.py:291-334`,
already shipped) is a *different* pattern (Pydantic model: construct-with-value → read-back-equal,
plus `ValidationError` on missing/invalid) — that pattern applies to the already-landed content
field, not to the new `EntityState`-side state this ticket adds, which should follow the
dataclass/`to_canonical_dict()` pattern above instead.

### Existing tests found (build on these, don't duplicate)

- `tests/unit/strategic/test_cognition_capacity.py` — `CapacityService.derive_profile` tests: base
  derivation, high-intelligence scaling, fatigue penalty, determinism. Uses
  `V2EntityBuilder` (`src/core/builder.py`) for entity construction — the established builder
  pattern for constructing test entities with specific attribute/identity values.
- `tests/unit/entity/test_phase11_cognition_model_schema.py` — `CognitionModel` and all sub-component
  schema/shape/determinism tests, described above.
- `tests/unit/entity/test_phase2_self_model_components.py` — `SelfModelBundle` component tests
  (different bundle, but same test-authoring pattern precedent).
- `tests/unit/content/test_catalog.py` — `intelligence_tier` field tests (291-334) and
  `test_all_13_races_have_documented_intelligence_tier` (359+) — confirms all 13 races are already
  authored with a valid tier; no gap here.

## Mechanics / Engine Constraints

`docs/mechanics/04_strategic_cognition.md` §3 ("Strategic Memory: Leads & Blockers") and its many
`### <Title> (TCK-...)` subsections are the established pattern for documenting a landed
strategic-cognition feature tied to a specific ticket (e.g. `### Lead Contradiction Testing (E42D;
TCK-20260824-LEAD-CONTRADICTION-WIRING)`, line 95; `### Grief Urgency & Nemesis Relations
(TCK-20260824-GRIEF-NEMESIS-REACHABILITY)`, line 133). A new role-model/imitation mechanic —
genuinely new durable per-entity state plus a new intelligence-tier-modulated behavior — is squarely
the kind of addition this chapter documents; no existing section covers it. `SelfModelBundle`'s own
docstring (`self_model.py:217-222`) records that `to_canonical_dict()` output feeds the canonical
hash used for determinism/replay/certification (`CanonicalStateHasher`, `src/engine/checkpoint.py:63`,
per the `docs/engine/kernel.md` 7-phase loop's Persistence phase) — any new sub-component under
`CognitionModel` participates in that hash unconditionally, so its `to_canonical_dict()` must be
implemented and deterministic (sorted iteration, no unstable ordering) from day one, matching every
existing sibling sub-component's pattern.

No chapter of the Mechanics Bible currently documents `RaceDefinition.intelligence_tier` either
(confirmed by `TCK-20260831-SPECIES-INTELLIGENCE-TIER`'s own investigation: zero mentions across all
6 chapters) — this ticket is the first real *consumer*, so documenting the read/modulation behavior
in Chapter 4 is this ticket's responsibility, not something to assume already covered elsewhere.

## Docs Requiring Update

- `docs/mechanics/04_strategic_cognition.md`: this ticket adds genuinely new durable per-entity
  state (who an entity watches/admires as a role model) and a new intelligence-tier-modulated
  imitation-sophistication behavior — neither exists in the Mechanics Bible today. Per the
  established `### <Title> (TCK-...)` subsection pattern under §3/§4 of this chapter (see Mechanics
  / Engine Constraints above), add a new subsection describing the mechanic, its data shape at a
  narrative level, and the `intelligence_tier` modulation rule, once Plan fixes the exact formula.
- `docs/parity_ledger/strategic_cognition.yaml`: no existing entry covers role-model/imitation
  state or behavior (grepped all `text:`/`id:` lines; nearest neighbors are the `STRAT-208..212`
  cognition-profile-capacity entries and the `STRAT-122..127` intel-capacity entries, both unrelated
  subjects). Add a new entry once the implementation lands, with a real `test_path` pointing at the
  new round-trip/behavior tests below (P1 priority per the ticket's own frontmatter, not P0 — no
  existing P0 entry in this file references imitation/role-model content).

The `docs/brainstorm/rpg_expected_schemas.html` (path: `docs/brainstorm/rpg_expected_schemas.html`,
under `docs/`) is not required to change for this ticket, despite being named in the ticket's own
"Related Docs" and despite line 1010 explicitly flagging that idea 27 ("Learning by Watching &
Choosing Role Models" — this ticket) "needs a schema and doesn't have one yet." This file is a
forward-looking brainstorm/proposal atlas, not a ship-status tracker: `TCK-20260831-SPECIES-INTELLIGENCE-TIER`'s
own investigation (same session, `stored_artifacts/TCK-20260831-SPECIES-INTELLIGENCE-TIER/investigation.md`)
checked this precisely — searching for two other fields that shipped after being proposed in this
same file family (`supports_adventure_routing`, `hazard_immunities`) and finding zero retroactive
mentions of either in `rpg_expected_schemas.html` after they shipped. That precedent holds here too:
this file does not get updated when a proposed idea ships; `docs/mechanics/04_strategic_cognition.md`
is the authoritative doc that should carry the landed behavior instead (see Format-1 bullet above).

The `docs/engine/known_limitations.md` (path: `docs/engine/known_limitations.md`, under `docs/`) is
not required to change for this ticket *unless* the AC #4 stub/defer branch is actually taken (i.e.
the ticket ships before `intelligence_tier` scaling is wired in for some reason). Since the
dependency (`TCK-20260831-SPECIES-INTELLIGENCE-TIER`) is already confirmed landed per the ticket's
own Assumptions section, this branch should not be needed — flagged only for completeness, not as a
required doc change under the current facts.

## Parity Ledger Overlap

No existing `docs/parity_ledger/strategic_cognition.yaml` entry references role-model, imitation, or
watching/admiring behavior — this is genuinely new ground, not an update to an existing entry.
Nearest-neighbor entries by subject (for Plan's ID-numbering reference, not because they need
changing): `STRAT-208`–`STRAT-212` (cognition-profile capacity limits, `strategic_cognition.yaml`
lines 2284-2324+) and `STRAT-122`–`STRAT-127` (intel-capacity replay/determinism/overload,
lines 1332-1389+). No P0 entries touched by this ticket; the new entry should be P1 or P2, matching
the ticket's own P1 priority and its "weakest implementability fit" framing — not a P0 correctness
guarantee.

## Prior Work

- `tickets/done/TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION.md` — confirms the current
  `CognitionModel`/`SelfModelBundle` split is intentional and stable, and independently confirms
  idea 22 is unrelated to the cognition schema.
- `tickets/done/TCK-20260831-SPECIES-INTELLIGENCE-TIER.md` +
  `stored_artifacts/TCK-20260831-SPECIES-INTELLIGENCE-TIER/investigation.md` — the field this ticket
  consumes; confirmed landed with all 13 races authored, zero existing consumers (this ticket is the
  first).
- `tickets/done/TCK-20260824-RELATIONSHIP-ROLE-FIELD.md` +
  `stored_artifacts/TCK-20260824-RELATIONSHIP-ROLE-FIELD/` — idea 22; confirmed unrelated code path
  (`SocialBond.role` under `EntityState.social`, not `EntityState.cognition`), useful only as the
  optional visual-pairing surface described above.
- `tests/unit/strategic/test_committed_intention_model.py` — precedent for how a new
  `CognitionProfile`-adjacent typed record (`CommittedIntentionEntry`) was added and tested with
  `dataclasses.replace()`-based immutable-update tests (not a literal serialize/deserialize, despite
  surface similarity to "round trip" language) — useful as a secondary pattern reference if the new
  role-model state needs a capacity-cap-style test (e.g. "max tracked role models enforced").

## Risks and Open Questions

- **`EntityUpdate.merge()`'s last-write-wins `cognition_bundle_set` behavior** (see "apply.py
  reconstruction path" above) is a real, currently-latent silent-drop risk one layer above the one
  Scope already ruled out. Not a blocker, but Plan/Implement must ensure whatever system writes the
  new role-model sub-component always rebuilds `cognition_bundle_set` off the freshest
  `entity.cognition`, and should avoid emitting a second `cognition_bundle_set`-bearing
  `EntityUpdate` for the same entity in the same tick alongside any other cognition-writing system.
- **Where imitation-sophistication scaling plugs in is a genuine open design fork**, not resolved
  here per the ticket's own instruction: either (a) `CapacityService.derive_profile` in
  `cognition_capacity.py` takes on a new `CatalogRepository`-derived dependency it doesn't have
  today, or (b) a separate, smaller function/service resolves `intelligence_tier` independently and
  never touches `CapacityService`'s existing signature/`CognitionProfile`'s existing 11 fields. Plan
  must decide and justify; both are architecturally viable given the confirmed
  `get_race_id_str`→`CatalogRepository.get_race`→`intelligence_tier` path. Both forks require the
  `docs/mechanics/04_strategic_cognition.md` update above regardless of which is chosen, so that
  Format-1 bullet is unconditional, not contingent on this open question.
- **No `get_race_semantics_service()` singleton exists yet** — whichever fork Plan picks, if it
  needs the repository, it will either add one (mirroring `get_faction_semantics_service()`) or
  reuse `get_faction_semantics_service()`'s underlying `CatalogRepository` instance if accessible.
  Worth Plan checking whether `FactionSemanticsService`/its cached `repo` is reachable for a
  `get_race()` call without instantiating a second `CatalogRepository` (double catalog load cost).

## Anti-Drift Hazards

- Do not extend `RelationshipRole` (`src/core/models/social.py`) with a new enum member for role
  models — ticket's Out of Scope explicitly forbids touching idea 22's own field definition; the
  optional pairing must use only the existing `FRIEND`/`RIVAL`/`NEUTRAL` values via the existing
  `SocialBondUpdate.role_set` authoritative path.
  Never invent a new write path to `SocialBond`.
- Do not modify `RaceDefinition`/`intelligence_tier`'s own definition or the 13-race data —
  read-only consumption only, per ticket's Out of Scope.
  Only touch `src/content/schema.py`/`data/content/living/races.yaml` if evidence emerges that field
  is wrong or incomplete, which this investigation did not find.
- Do not conflate `CognitionModel` (`src/core/cognition.py`, `EntityState.cognition`),
  `SelfModelBundle` (`src/core/self_model.py`, `EntityState.self_model`), `CognitionProfile`
  (`src/core/strategic.py`, derived by `CapacityService`), and `CognitionProfileDefinition`
  (`src/content/schema.py`, content catalog) — four distinct "cognition" concepts confirmed to
  coexist in this codebase today. The new role-model state belongs in the first
  (`CognitionModel`); the scaling logic reads from the fourth (`RaceDefinition.intelligence_tier`,
  which itself references but is distinct from the fourth's sibling
  `CognitionProfileDefinition`/`cognition_profile` field — do not confuse `intelligence_tier` with
  `cognition_profile`, they are separate `RaceDefinition` fields with separate purposes, confirmed
  by `TCK-20260831-SPECIES-INTELLIGENCE-TIER`'s own investigation).
- Any new sub-component under `CognitionModel` must implement `to_canonical_dict()` with fully
  deterministic ordering (sorted dict iteration, no set iteration) — it participates in the
  authoritative canonical hash unconditionally; a non-deterministic implementation would silently
  break replay/certification, not just this ticket's own tests.
- Keep the new state read-only-derived scaling logic free of entity-state mutation —
  `CapacityService.derive_profile` and any sibling imitation service must stay "purely
  deterministic; does not mutate entity state" (existing docstring convention in
  `cognition_capacity.py`), consistent with the project's Decision-logic-reads-state /
  Durable-changes-through-typed-updates architecture rule.
