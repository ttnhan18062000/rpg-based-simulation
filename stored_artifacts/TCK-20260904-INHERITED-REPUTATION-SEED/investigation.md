---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260904-INHERITED-REPUTATION-SEED
artifact_type: investigation
tags: [lifecycle, social]
---

# Investigation — TCK-20260904-INHERITED-REPUTATION-SEED

## Current Behavior

**`SocialComponent` (`src/core/models/social.py:31-58`)**: `public_reputation: float = 1.0`
(line 52) is still a flat, unscoped scalar clamped `[0.0, 2.0]` — confirmed directly against
source, not assumed from the prerequisite ticket's summary. `TCK-20260904-REPUTATION-LOCALITY-SCOPE`
(DONE, landed same day) added a **new, additive** field alongside it:
`regional_reputation: Dict[str, float] = field(default_factory=dict)` (line 48, RegionID →
local reputation, same `[0.0, 2.0]` clamp). `public_reputation` itself was explicitly untouched
by that ticket ("Step 1... `public_reputation` itself is untouched — retained as the global
scalar," `tickets/done/TCK-20260904-REPUTATION-LOCALITY-SCOPE.md` Implementation Notes). Every
`regional_reputation` entry starts as an **empty dict** for every entity, including newborns —
there is no existing per-region history for a brand-new entity to seed from.

**`RelationshipService.process_update()` (`src/systems/social_systems/relationships.py:16-100`)**
is the sole authoritative writer of both fields (SOC-217). The `public_reputation` write
(lines 93-95) is unchanged by the locality ticket:
`public_reputation=update.reputation_set if update.reputation_set is not None else
max(0.0, min(2.0, social.public_reputation + update.heroism_delta - update.notoriety_delta))`.
There is **no passive decay term anywhere** on `public_reputation` — confirmed by reading the
full method body; it is written only via `SocialUpdate.reputation_set` (full overwrite, line
299 of `src/core/updates.py`) or `heroism_delta`/`notoriety_delta` (additive, clamped). This
confirms the ticket's own premise: a birth-seeded value is naturally swamped by ordinary play
with zero new decay logic required.

**`SocialUpdate` (`src/core/updates.py:287-370`)**: `reputation_set: Optional[float] = None`
(line 299) already exists and needs no new field. `regional_reputation_delta: Dict[str, float]`
(line 310) also already exists (added by the locality ticket) but this ticket's scope explicitly
does not require it (see Assumptions/Risks below for the targeting recommendation).

**`V2EntityBuilder.social()` (`src/core/builder.py:498-546`)** already accepts a
`public_reputation: Optional[float] = None` kwarg (line 512) and writes it via direct
`_component(SocialComponent, **current)` construction (line 545) — **not** through
`RelationshipService.process_update()`. This is already an allowlisted exception in
`tests/architecture/test_social_write_paths.py` (`ALLOWED_FILES` includes
`"src/core/builder.py"`, comment: "V2EntityBuilder's initial-construction seeding (pre-tick, not
a live mutation)"). So a birth-seed write via `.social(public_reputation=seed)` inside
`birth_record()` requires **no change** to that guard test — it is already covered.

**`V2EntityBuilder.birth_record()` (`src/core/builder.py:624-675`)** is the exact structural
precedent this ticket is scoped to mirror. Current signature (lines 624-637) takes
`parent_a_entity_id`, `parent_b_entity_id`, `birth_tick`, `birth_city_id`, `seed_familiarity`,
`seed_sentiment`, `parent_a_genetic_profile`, `parent_b_genetic_profile`, `parent_a_role`,
`parent_b_role` (all `Optional`, `None`-default). When at least one genetic profile is supplied
(line 657), it computes `combat_lean` from both roles, resolves missing profiles via
`GeneticsSystem.generate_profile_from_seed()`, calls `GeneticsSystem.combine_profiles()`, and
writes the result via a second `self.lifecycle(genetic_profile=combined)` call (line 663) — a
second direct-construction write, same shape this ticket should follow for `.social(...)`.

**`GeneticsSystem.combine_profiles()` (`src/systems/lifecycle_systems/genetics.py:105-133`)** is
the pure-combine-function precedent: a `@staticmethod` taking both parent values plus
`combat_lean`/`seed`, doing a per-attribute convex combination with a seeded perturbation term,
explicit clamp to `[0.8, 1.3]`. No equivalent pure function exists yet for reputation.

**Real call chain (only live two-parent birth caller)**:
`HumanoidReproductionService.process_reproduction()` (`src/world/reproduction_humanoid.py:28-115`)
resolves each parent's genetic profile at the call site (lines 84-85:
`a_profile = a.lifecycle.genetic_profile or GeneticsSystem.generate_profile_from_seed(a.id)`)
because a first-generation parent may have no stored profile of its own — then calls
`generator.spawn_humanoid_offspring(...)` (line 87), which in turn calls
`V2EntityBuilder(...).birth_record(parent_a_genetic_profile=a_profile,
parent_b_genetic_profile=b_profile, parent_a_role=a.identity.role,
parent_b_role=b.identity.role, ...)` (`src/systems/world_systems/generator.py:188-210`).
`public_reputation` has **no equivalent missing-value problem** — every entity's
`SocialComponent.public_reputation` always has a real value (default `1.0` at minimum,
never `None`), so the reputation-seed kwargs can be resolved directly at the call site as
`a.social.public_reputation` / `b.social.public_reputation` with no fallback-generation
function needed (unlike genetics' `generate_profile_from_seed()` fallback).

**Parentless spawn paths** (`EntityGenerator.spawn_natural_creature_offspring()`,
`spawn_magical_demonic_entity()`, `src/systems/world_systems/generator.py:92-160`) call
`.birth_record(parent_a_entity_id=None, parent_b_entity_id=None, ...)` with no genetic-profile
or role kwargs — they inherit the class-default `public_reputation=1.0` today, and must continue
to after this change (no new kwargs passed on those paths).

**`StateFingerprinter.get_fingerprint()` (`src/replay/fingerprint.py:69`)** already includes
`f"reputation={ent.social.public_reputation:.3f}:"` unconditionally, for every entity regardless
of how the value was populated. A birth-seeded `public_reputation` therefore requires **no
change** to fingerprint/canonical-hash determinism coverage — it rides the existing scalar
coverage. (Contrast with the genetics ticket, which had to add a whole new field to
`to_canonical_dict()`/fingerprint because `genetic_profile` was itself new.)

**AC5's exclusion target**: `ReputationUpdateService` (`src/domains/commitment/reputation.py:11`,
method `process_witnessed_event(profile: PublicReputationProfile, event_kind: str)`) and
`PublicReputationProfile` (`src/core/cognition.py:516`) are confirmed structurally separate —
`PublicReputationProfile` lives on `RelationshipModel`/`entity.cognition.relationships`, not on
`SocialComponent`. This is the same "structurally distinct, unrelated field that only shares a
name" finding the locality ticket already made and locked into
`tests/architecture/test_social_write_paths.py`'s `ALLOWED_FILES` comment for `src/engine/quests.py`.

## Mechanics / Engine Constraints

- `docs/mechanics/01_entity_anatomy.md` §5 "Birth Record (Reproduction Schema)" (lines 142-163)
  and "Genetic Inheritance (Combination)" (lines 165-199) are the two directly analogous sections
  — this ticket adds a third, parallel "Reputation Seed" subsection following the same shape
  (field type, when populated, the pure combine function, how `birth_record()` wires it, the
  parentless-path exclusion).
- SOC-193 (`docs/parity_ledger/social_narrative.yaml:2049`, "Public reputation and private
  relationship/bond are separate state") and SOC-217 (line 2301, the authoritative-writer law)
  both directly constrain this: the birth-seed write must not blur `public_reputation` with
  private bond/trust state, and must stay inside the allowlisted construction-time exception
  rather than opening a second live-mutation path.
- `RelationshipService.process_update()`'s existing `[0.0, 2.0]` clamp on `public_reputation`
  (relationships.py:94-95) is the authoritative valid-range law the combine function's own clamp
  must match exactly — do not invent a different range.
- The Reproduction epic's "no marriage/contract precondition" rule
  (`docs/mechanics/01_entity_anatomy.md:162-163`, `SOC-`-adjacent reproduction rules) applies
  identically here: no new precondition may gate the reputation-seed write.

## Docs Requiring Update

- `docs/mechanics/01_entity_anatomy.md`: add a "Reputation Seed" subsection to §5, parallel to
  the existing "Birth Record" and "Genetic Inheritance (Combination)" subsections (lines 142-199),
  documenting the new combine function, its both-parents-required trigger condition, the
  `[0.0, 2.0]` clamp, and the parentless-path exclusion.
- `docs/parity_ledger/social_narrative.yaml`: add a new entry (next available id is `SOC-267`,
  following `SOC-266` at line 4015 which documented `regional_reputation` itself) documenting the
  Inherited Reputation birth-seed mechanism, cross-referencing `SOC-260` (the genetics-inheritance
  entry, same shape) and `SOC-217`/`SOC-193` (authoritative-writer/separation laws this write
  respects). Must be written via `tools/parity_ledger_writer.py`, never hand-edited YAML, per
  project convention and the locality ticket's own precedent.

The `docs/simulation/lifecycle_systems_contract.md` doc (path:
`docs/simulation/lifecycle_systems_contract.md`, under `docs/simulation/`) is not required to
change for this ticket: its "Genetics — `genetics.py`" section (lines 94-173) documents the
`GeneticsSystem` module's own public API surface specifically; the reputation-seed combine
function is a `SocialComponent`/`RelationshipService`-domain concern (per this ticket's own scope
guard against touching `ReputationUpdateService`/`PublicReputationProfile`), and no equivalent
"social systems contract" doc section currently documents `RelationshipService.process_update()`'s
individual field-write rules in this file-level granularity for the Plan phase to extend
symmetrically — confirm at Plan time whether `docs/simulation/social_systems_contract.md` (a
distinct file, already touched by the locality ticket per its Files Changed list) is the correct
doc-update target instead if a Plan-phase decision routes the combine function through
`RelationshipService`.

The `docs/brainstorm/rpg_expected_schemas.html` doc (path:
`docs/brainstorm/rpg_expected_schemas.html`, under `docs/brainstorm/`) is not required to change
for this ticket: its schema-53 section proposes a `BirthEvent` class and a
`reputation_decay_rate` field, both of which the ticket's own Out of Scope explicitly rejects as
contradicting the epic's verified "no decay logic needed" correction — this ticket does not adopt
that schema shape, so the doc is not brought into parity with the (rejected) proposal.

## Parity Ledger Overlap

- **SOC-217** (`process_update()` is the sole authoritative writer, line 2301) — this ticket's
  write path must stay inside the allowlisted `builder.py` construction-time exception; does not
  require a `status` change, but the new SOC-267 entry should cross-reference it.
- **SOC-193** (public reputation vs. private relationship separation, line 2049) — overlap only
  in that the birth-seed must not conflate the two; no status change expected.
- **SOC-266** (`regional_reputation` mechanism, line 4015, added by the locality ticket) — overlap
  is definitional only: confirms `regional_reputation` exists and is additive, informing the
  public_reputation-vs-regional_reputation targeting decision below. No status change.
- **SOC-260** (genetic-inheritance combination, line 3821) — the direct structural precedent for
  the new SOC-267 entry's shape and cross-reference.
- None of these are P0; no `test_path` regression risk identified beyond the new tests this ticket
  itself adds.

## Prior Work

- `stored_artifacts/TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE/` (investigation.md, plan.md,
  test_plan.md) — the exact structural precedent this ticket copies: optional parent kwargs on
  `birth_record()`, a pure combine `@staticmethod`, a construction-time write, a parentless-path
  anti-drift test, one new parity ledger entry, one new Mechanics Bible subsection.
- `stored_artifacts/TCK-20260904-REPUTATION-LOCALITY-SCOPE/` (referenced in the ticket but not
  separately re-read here beyond `tickets/done/TCK-20260904-REPUTATION-LOCALITY-SCOPE.md`'s own
  Implementation Notes, which already carry the load-bearing evidence: `public_reputation` stays a
  flat float, `regional_reputation` is new and additive, and both are now covered by
  `tests/architecture/test_social_write_paths.py`'s allowlist guard including `builder.py`).
- `tests/unit/world/test_reproduction_humanoid_cadence.py` — existing test file for the real
  humanoid-birth call chain (`test_social_bond_seeded_between_each_parent_and_child_at_high_familiarity_sentiment`,
  `test_genetics_uses_real_parent_role_data_for_combat_lean`,
  `test_humanoid_reproduction_commits_through_authoritative_apply_path`) is the natural home for
  an equivalent `test_reputation_seeded_from_both_parents_averaged_public_reputation`-style
  integration-level test exercising the real call chain, not just `birth_record()` in isolation.
- `tests/unit/world/test_natural_creature_reproduction.py::test_natural_creature_and_magical_demonic_paths_never_attach_genetic_profile`
  (lines 262-280) — the exact anti-drift test shape to mirror for AC3 (parentless paths keep the
  class-default `public_reputation`).

## Risks and Open Questions

- **Targeting question (explicitly asked by the task, resolved with recommendation)**: should the
  birth-seed write target only `public_reputation` (the ticket's original scope, written before
  `regional_reputation` existed) or also seed `regional_reputation`? **Recommendation: target
  `public_reputation` only, as scoped.** Rationale: `regional_reputation` is a brand-new,
  always-empty-at-construction `Dict[RegionID, float]` — a newborn has no prior presence in any
  region to seed a per-region value *from* (there is no "the parents' region-scoped standing"
  concept established anywhere in the locality ticket's landed shape; parents' own
  `regional_reputation` dicts may be empty, sparse, or keyed to regions the child has no
  connection to yet). Seeding `regional_reputation` would require inventing a region-selection
  rule (which region(s) to seed?) that has no design-doc precedent and was not raised by either
  this ticket's Scope or the locality ticket's Out of Scope — doing so would be scope creep beyond
  what idea 53's card text ("seed a small fraction of the newborn's public_reputation from the
  parents' averaged standing") specifies. `public_reputation` is the only field idea 53's own card
  text names, and it is the only field always populated for both parents with no missing-data
  edge case. This should still be flagged to the Plan phase as a confirmed judgment call, not
  silently assumed — if the Plan phase disagrees, extending to `regional_reputation` is a
  larger, separate design decision (region-selection rule) that would expand scope.
- **Combine-function trigger semantics ambiguity**: the ticket's Scope text ("weighted average of
  whichever parent value(s) are supplied") reads as allowing a single-parent partial seed, but
  AC2 explicitly requires that "zero or exactly one parent reputation value supplied falls back to
  the class default" — i.e., seeding must require **both** parent values to be present, not
  "however many are supplied." At the one real call site
  (`HumanoidReproductionService.process_reproduction()`), both parents always exist and always
  have a real `public_reputation` value, so this ambiguity never manifests in production — it only
  matters for `birth_record()`'s own unit-level contract. The Plan phase must lock in
  AC2's stricter "both-required" reading; do not implement Scope's looser "any number" wording,
  since that would fail AC2's own test.
- Exact weighting formula (simple average vs. some other weighting) is explicitly left as a
  Plan-phase decision per the ticket's own Assumptions section — not resolved here.
- Location of the new pure combine function is undecided: genetics precedent put
  `combine_profiles()` in `src/systems/lifecycle_systems/genetics.py` (a systems module, not
  `builder.py` itself). A reputation-domain equivalent would more naturally live in or near
  `src/systems/social_systems/relationships.py` (already the reputation-domain authoritative
  module) — but relationships.py is also the file allowlisted specifically as *the* authoritative
  live-mutation writer; adding a pure birth-time-only helper there should not blur that file's
  "sole authoritative writer" identity if inspected by a future guard test. Flag for Plan-phase
  decision; a small new pure function directly in `builder.py` near the `GeneticsSystem` import
  (or a lifecycle_systems-adjacent module) is also a reasonable, lower-risk alternative.

## Anti-Drift Hazards

- **Do not route the birth-seed write through `RelationshipService.process_update()`.** The
  precedent (`genetic_profile`) and the existing architecture guard both establish
  construction-time direct writes as correct for `birth_record()`; routing through
  `process_update()` at birth time would be unnecessary indirection and risks tripping the "sole
  authoritative writer" guard's intent if a future stricter guard is added, even though the
  current guard already allowlists `builder.py`.
  the current guard's `ALLOWED_FILES` already includes `builder.py`, so it will not
  immediately break the guard — but keep the write direct/`_component`-based, matching
  `genetic_profile`'s pattern, not a live-mutation-shaped call.
- **Do not seed `regional_reputation`** unless the Plan phase makes an explicit, justified
  decision to expand scope (see Risks above) — this is the single most likely
  scope-creep vector given `regional_reputation`'s newness and topical adjacency.
- **Do not build `BirthEvent` or `reputation_decay_rate`** — explicitly Out of Scope, and
  contradicted by the epic's own verified "no decay logic needed" finding.
- **Do not import or reference `ReputationUpdateService`/`PublicReputationProfile`** anywhere in
  the new write path — AC5 requires a source-text guard test for this, mirroring
  `test_natural_creature_reproduction_does_not_reference_genetics`'s `assert "Genetics" not in
  source` pattern.
- **`tests/unit/domains/` structural coverage backstop**: per the sibling ticket
  `TCK-20260904-REPUTATION-LOCALITY-SCOPE`'s own confirmed pattern, this ticket's changed files
  include `src/core/builder.py` (under `src/core/`), and a structural test-coverage backstop
  requires `tests/unit/domains/` to be included in the Test phase's scoped pytest command whenever
  `src/core/` is touched — flagging here so the Test phase does not have to rediscover this the
  hard way. (No specific `tests/unit/domains/` subfolder currently tests `SocialComponent`
  directly, per this investigation's search — the backstop is a coverage-breadth requirement, not
  evidence a specific domain test needs new assertions.)
- **Parentless paths must never gain the new kwargs.** `spawn_natural_creature_offspring()` and
  `spawn_magical_demonic_entity()` (`src/systems/world_systems/generator.py`) must not be touched
  to pass `parent_a_public_reputation`/`parent_b_public_reputation` — verified by the new AC3
  anti-drift test, matching the genetics-ticket precedent exactly.
- **Two-parent combine must not accidentally fire on the natural-creature/magical paths' internal
  `None, None` parent-id call** — the trigger condition must be gated on the new reputation kwargs
  being non-`None`, not on `parent_a_entity_id`/`parent_b_entity_id` being non-`None` (the latter
  would incorrectly couple reputation-seeding to id-presence rather than value-presence, same
  design as genetics' own `parent_a_genetic_profile is not None or parent_b_genetic_profile is not
  None` gate at builder.py:657).
