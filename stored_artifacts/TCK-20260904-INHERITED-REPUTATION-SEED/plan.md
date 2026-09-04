---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260904-INHERITED-REPUTATION-SEED
artifact_type: plan
tags: [lifecycle, social]
---

# Implementation Plan — TCK-20260904-INHERITED-REPUTATION-SEED

## Summary

Seed `SocialComponent.public_reputation` (a flat `float`, `src/core/models/social.py:52`, default
`1.0`, clamped `[0.0, 2.0]`) at birth from the simple average of both parents' current
`public_reputation` values, following the exact structural precedent of
`TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE`: a new pure combine function, optional kwargs on
`V2EntityBuilder.birth_record()`, a construction-time write via the already-existing
`.social(public_reputation=...)` kwarg, and a parentless-path anti-drift test. Two decisions are
locked in below (both required by the task, neither left open):

1. **Trigger semantics**: seeding requires **both** parent values to be supplied — AC2 (zero-or-one
   supplied falls back to the class default `1.0`) governs over the Scope text's looser "weighted
   average of whichever parent value(s) are supplied" wording. The gate is `is not None and is not
   None` (AND), not genetics' `is not None or is not None` (OR) — reputation has no
   fallback-generation function because every entity's `public_reputation` always has a real value,
   so there is no missing-value case to backfill; "less than both supplied" simply means "do not
   seed."
2. **Combine-function placement**: `src/systems/social_systems/reputation.py`, as a new
   `@staticmethod` on the **existing** `ReputationService` class (confirmed present at
   `src/systems/social_systems/reputation.py:4-19`, currently `get_impact()` and
   `calculate_caution_modifier()` — a pure-function domain module, structurally distinct from both
   `RelationshipService` in `relationships.py` (the SOC-217 authoritative live-mutation writer) and
   `ReputationUpdateService` in `src/domains/commitment/reputation.py` (AC5's excluded, unrelated
   system). This mirrors the genetics precedent's actual placement more precisely than either
   alternative floated in the investigation: `GeneticsSystem.combine_profiles()` lives in
   `src/systems/lifecycle_systems/genetics.py` — a dedicated systems module holding only pure
   functions, **not** the file that applies `LifecycleUpdate` authoritatively — and
   `social_systems/reputation.py` is that exact analog for the reputation domain, already
   pre-existing rather than needing to be created fresh. Putting the combine function in
   `relationships.py` instead was rejected per the investigation's own hazard: it would blur that
   file's "sole authoritative writer" identity (SOC-217).

Confirmed via direct read that no other writer to `SocialComponent.public_reputation` exists beyond
`RelationshipService.process_update()` (`relationships.py:98-100`, exact lines re-verified against
current source — not `93-95` as the investigation's summary loosely stated) and
`V2EntityBuilder.social()`'s construction-time write (`builder.py:545`, inside the already-existing
`.social()` kwarg method, `public_reputation` param at `builder.py:512`). This plan's new write
goes through the same already-allowlisted `builder.py` construction path — `tests/architecture/
test_social_write_paths.py`'s `ALLOWED_FILES` requires no edit (verified: the new kwargs are named
`parent_a_public_reputation`/`parent_b_public_reputation`, and the guard's regex
`\b(public_reputation|regional_reputation)\s*=` requires a word-boundary immediately before the
literal, which the `_` in `parent_a_public_reputation=`/`parent_b_public_reputation=` prevents from
matching — confirmed by inspecting the regex at `tests/architecture/test_social_write_paths.py:29`).

## Steps

### Step 1 — Add the pure combine function to `ReputationService`
**Files:** `src/systems/social_systems/reputation.py`
**Change:** Add a new `@staticmethod combine_public_reputation(parent_a: float, parent_b: float) ->
float` to the existing `ReputationService` class (class currently spans lines 4-19, holding
`IMPACTS`, `get_impact()`, `calculate_caution_modifier()` — confirmed by direct read). Body:
`return max(0.0, min(2.0, (parent_a + parent_b) / 2.0))` — simple arithmetic mean, explicitly
clamped to the field's authoritative `[0.0, 2.0]` range (matching the exact clamp literal used by
the sole authoritative writer, `RelationshipService.process_update()` at `relationships.py:99` —
`max(0.0, min(2.0, ...))`), defense-in-depth exactly as `GeneticsSystem.combine_profiles()`'s own
explicit clamp is (`genetics.py:131`), even though two in-range inputs averaged cannot leave range
by construction. Docstring notes: idea 53's "starting echo, not full inheritance" language refers
to the seed being swamped by the child's own subsequent `heroism_delta`/`notoriety_delta` play
(verified AC4/Step 6 below), not to any additional dampening inside this function — AC1 requires
the result to land strictly between the two parent values, which a blend toward the neutral
default (1.0) would violate whenever 1.0 falls outside `[min(a,b), max(a,b)]`.
**Do NOT touch:** `IMPACTS`, `get_impact()`, `calculate_caution_modifier()` — leave both existing
methods and the `IMPACTS` dict completely unchanged. Do not add this method to
`RelationshipService` (`relationships.py`) or to `ReputationUpdateService`
(`src/domains/commitment/reputation.py`).
**Verify:** No standalone unit test required for this pure function in isolation — it is exercised
end-to-end via Step 2's AC1/AC2 tests through `birth_record()`. (`tests/unit/progression/
test_genetics.py` must stay green unchanged, confirming this addition does not disturb the sibling
`GeneticsSystem` module it is structurally parallel to.)

### Step 2 — Extend `V2EntityBuilder.birth_record()` with reputation-seed kwargs
**Files:** `src/core/builder.py`
**Change:** Add `from src.systems.social_systems.reputation import ReputationService` near the
existing `from src.systems.lifecycle_systems.genetics import GeneticsSystem, GeneticProfile`
import (`builder.py:54`). Add two new `Optional[float] = None` kwargs to `birth_record()`'s
signature (currently `builder.py:624-637`): `parent_a_public_reputation`,
`parent_b_public_reputation`, placed after the existing `parent_a_role`/`parent_b_role` kwargs.
Inside the method body, after the existing genetics-combine block (`builder.py:657-663`) and
before the bonds-seeding block (`builder.py:664` onward), add:
```python
if parent_a_public_reputation is not None and parent_b_public_reputation is not None:
    combined_reputation = ReputationService.combine_public_reputation(
        parent_a_public_reputation, parent_b_public_reputation
    )
    self.social(public_reputation=combined_reputation)
```
This is the AND-gated trigger from the Summary's Decision 1 — deliberately the opposite of the
genetics block's OR-gate (`builder.py:657`, `is not None or is not None`) because genetics has a
`generate_profile_from_seed()` fallback for a missing single parent profile and reputation has no
equivalent fallback (confirmed by investigation: every entity's `public_reputation` always has a
real value, so "one supplied" is never a "need to backfill the other" case — it is simply "not
enough to seed," per AC2). Writes via the pre-existing `.social(public_reputation=...)` kwarg
(`builder.py:512`, `builder.py:545`'s `_component(SocialComponent, **current)` construction) — the
same direct-construction pattern the genetics block uses via `.lifecycle(genetic_profile=combined)`
(`builder.py:663`), and already inside `test_social_write_paths.py`'s allowlisted `builder.py`
exception.
**Do NOT touch:** The existing genetics-combine block's logic or gate condition
(`builder.py:657-663`), the bonds-seeding block (`builder.py:664-674`), or any other
`birth_record()` kwarg. Do not add a `parent_a_public_reputation`/`parent_b_public_reputation`
fallback-generation function — none is needed (see Decision 1).
**Verify:** New tests in `tests/unit/progression/test_lifecycle.py` —
`test_birth_record_seeds_public_reputation_from_both_parents_average` (AC1) and
`test_birth_record_public_reputation_falls_back_to_default_with_partial_parent_data` (AC2, three
sub-cases: neither/only-a/only-b). Existing `test_builder_birth_record_path_two_parent_case`,
`test_builder_birth_record_path_parentless_case`,
`test_builder_birth_record_seeds_child_social_bonds_toward_parents` must stay green unchanged
(new kwargs are additive/optional, default `None`, so omitting them must not alter any existing
call's output).

### Step 3 — Thread the new kwargs through `EntityGenerator.spawn_humanoid_offspring()`
**Files:** `src/systems/world_systems/generator.py`
**Change:** Add two new `Optional[float] = None` parameters to `spawn_humanoid_offspring()`'s
signature (currently `generator.py:155-160`): `parent_a_public_reputation`,
`parent_b_public_reputation`, placed after the existing `parent_a_role`/`parent_b_role`
parameters. Pass them through into the `.birth_record(...)` call inside the method body
(currently `generator.py:178-186`, the block with `parent_a_genetic_profile=parent_a_genetic_profile,
...`) as `parent_a_public_reputation=parent_a_public_reputation,
parent_b_public_reputation=parent_b_public_reputation,`.
**Do NOT touch:** `spawn_natural_creature_offspring()` (`generator.py:86-118`) or
`spawn_magical_demonic_entity()` (`generator.py:123-152`) — neither method gains the new
parameters or passes them to its own `.birth_record()` call (both currently call
`.birth_record(parent_a_entity_id=None, parent_b_entity_id=None, birth_tick=birth_tick,
birth_city_id=None)` with no genetics/role kwargs either — this must stay exactly as-is). Do not
touch `spawn_goblin()` or `spawn_calamity()`, which do not call `birth_record()` at all.
**Verify:** Covered together with Step 4 by the new integration test
`test_humanoid_reproduction_seeds_child_public_reputation_from_parents` (below) — no standalone
test for this step alone, since `spawn_humanoid_offspring()` has no other live caller besides
`HumanoidReproductionService.process_reproduction()` (confirmed the only real two-parent call
chain per investigation).

### Step 4 — Wire real parent reputation values at the `HumanoidReproductionService` call site
**Files:** `src/world/reproduction_humanoid.py`
**Change:** At the existing `generator.spawn_humanoid_offspring(...)` call
(`reproduction_humanoid.py:87-91`), add two new keyword arguments:
`parent_a_public_reputation=a.social.public_reputation,
parent_b_public_reputation=b.social.public_reputation,`. This mirrors the existing pattern one
block above it that resolves `a_profile`/`b_profile` at the call site
(`reproduction_humanoid.py:79-85`) — except reputation needs no
`GeneticsSystem.generate_profile_from_seed()`-style fallback resolution first, since
`a.social.public_reputation` / `b.social.public_reputation` are plain `SocialComponent` fields
that always hold a real value (never `None`) for any already-constructed entity — read directly at
the call site with no intermediate resolution step.
**Do NOT touch:** Any other part of `process_reproduction()` — the region/scarcity gating logic
(lines ~67-71), the cooldown/pair-update construction (lines ~92-107), or
`build_parent_bond_updates_for_birth()` (a separate helper this ticket does not touch).
**Verify:** New test `test_humanoid_reproduction_seeds_child_public_reputation_from_parents` in
`tests/unit/world/test_reproduction_humanoid_cadence.py`, alongside existing
`test_social_bond_seeded_between_each_parent_and_child_at_high_familiarity_sentiment`,
`test_genetics_uses_real_parent_role_data_for_combat_lean`,
`test_humanoid_reproduction_commits_through_authoritative_apply_path` (all three must stay green
unchanged). New test constructs two parent entities with differing `social.public_reputation`
values, runs `HumanoidReproductionService.process_reproduction()`, and asserts the produced child's
`public_reputation` lies strictly between the two parents' values.

### Step 5 — Anti-drift test: parentless paths never seed `public_reputation`
**Files:** `tests/unit/world/test_natural_creature_reproduction.py`
**Change:** Add `test_natural_creature_and_magical_demonic_paths_never_seed_public_reputation`,
directly mirroring the existing
`test_natural_creature_and_magical_demonic_paths_never_attach_genetic_profile`
(`test_natural_creature_reproduction.py:262-280`) in shape: call
`generator.spawn_natural_creature_offspring(...)` and `generator.spawn_magical_demonic_entity(...)`
and assert both produced entities have `social.public_reputation == 1.0` (the `SocialComponent`
class default, per `social.py:52`). No production code change in this step — Step 3 already
confirmed neither parentless spawn method gains the new kwargs, so this step is purely the AC3
proof.
**Do NOT touch:** `spawn_natural_creature_offspring()` / `spawn_magical_demonic_entity()`
themselves (see Step 3's guard) — this step only adds a test.
**Verify:** The new test itself, plus continued green status of the existing
`test_natural_creature_and_magical_demonic_paths_never_attach_genetic_profile` and
`test_natural_creature_reproduction_does_not_reference_genetics` in the same file.

### Step 6 — Test: post-birth deltas move a birth-seeded value identically to the class default
**Files:** `tests/unit/social/test_relationships.py`
**Change:** Add
`test_heroism_and_notoriety_deltas_apply_identically_to_birth_seeded_reputation`, co-located with
existing `process_update()` reputation tests. Construct one `SocialComponent` with
`public_reputation=0.6` (simulating a birth-seeded value) and one with the class default `1.0`;
apply the same `SocialUpdate(heroism_delta=0.2)` to each via
`RelationshipService.process_update()`; assert both moved by exactly `+0.2` (`0.6 -> 0.8` and
`1.0 -> 1.2`), proving no floor/ceiling/persistence is special-cased to birth-seed origin. No
production code change — `RelationshipService.process_update()` (`relationships.py:16-100`,
specifically the `public_reputation=` write at lines 98-100) is confirmed unchanged by this
ticket; this step is a proof-only addition confirming that fact.
**Do NOT touch:** `RelationshipService.process_update()` itself — zero new fields on `SocialUpdate`,
zero new decay/periodic call sites, per the ticket's explicit Scope guard. Do not add any
birth-seed-origin tracking field anywhere.
**Verify:** The new test itself, plus continued green status of the full
`tests/unit/social/test_relationships.py` file (especially
`test_public_reputation_locality_differs_by_region_after_region_scoped_event`,
`test_regional_reputation_delta_clamped_to_public_reputation_range`,
`test_public_reputation_impact`), confirming `process_update()`'s existing clamp/delta semantics
are byte-for-byte unchanged.

### Step 7 — Source-text guard: new write path never references the excluded reputation system
**Files:** `tests/architecture/test_social_write_paths.py`
**Change:** Add
`test_reputation_seed_write_path_does_not_reference_reputation_update_service`, mirroring
`test_natural_creature_reproduction_does_not_reference_genetics`'s
`assert "Genetics" not in source` pattern. Use `inspect.getsource()` on
`V2EntityBuilder.birth_record()` and on `ReputationService.combine_public_reputation()` (the new
Step 1 function); assert neither source string contains `"ReputationUpdateService"` nor
`"PublicReputationProfile"`. (Confirmed safe: `"ReputationService"`, the class this ticket's new
method lives on, is a distinct string from `"ReputationUpdateService"` — the latter is never a
substring match of source containing only the former, since `"Update"` is inserted mid-string, not
appended.)
**Do NOT touch:** The existing `ALLOWED_FILES` set or `_WRITE_PATTERN` regex in this file — no edit
is required or expected (see Summary's placement-decision note on why `builder.py`'s existing
allowlist entry already covers the new write, and why the `parent_a_/parent_b_` kwarg naming
avoids tripping the regex in `generator.py`/`reproduction_humanoid.py`). If implementing this step
reveals `ALLOWED_FILES` does need an edit, stop and treat that as a signal the write landed
somewhere unexpected — do not silently allowlist it.
**Verify:** The new test itself, plus continued green status of both existing tests in this file
(`test_public_reputation_and_regional_reputation_write_paths_are_allowlisted`,
`test_relationships_py_is_the_authoritative_writer`).

### Step 8 — Docs: Mechanics Bible subsection + parity ledger entry
**Files:** `docs/mechanics/01_entity_anatomy.md`, `docs/parity_ledger/social_narrative.yaml` (via
`tools/parity_ledger_writer.py` only — never hand-edited)
**Change:** In `01_entity_anatomy.md` §5, add a new "Reputation Seed" subsection immediately after
the existing "Genetic Inheritance (Combination)" subsection (currently ending around line 199),
following that subsection's exact shape: field type/location
(`SocialComponent.public_reputation`, `[0.0, 2.0]`), the new
`ReputationService.combine_public_reputation()` pure function and its simple-average formula, the
both-parents-required AND-gate trigger condition (Decision 1, contrasted explicitly with genetics'
OR-gate and its reason), the `builder.py:512`/`545` construction-time write, and the
parentless-path exclusion (natural-creature/magical-demonic paths never pass the new kwargs, keep
`public_reputation` at class-default `1.0`). Then run `tools/parity_ledger_writer.py` to add a new
`SOC-267` entry to `docs/parity_ledger/social_narrative.yaml` (confirmed next available id — last
existing entry is `SOC-266` at line 4015), modeled on `SOC-260`'s (genetics-inheritance, line 3821)
shape, cross-referencing `SOC-217` (authoritative-writer law) and `SOC-193` (public-vs-private
reputation separation), `status: verified`, `v2_evidence` citing `builder.py`'s `birth_record()`
and `reputation.py`'s `combine_public_reputation()`, `test_path` citing the Step 2 AC1 test.
**Do NOT touch:** `docs/simulation/lifecycle_systems_contract.md` (out of scope per investigation —
no equivalent social-systems-contract doc section exists at this granularity) or
`docs/brainstorm/rpg_expected_schemas.html` (its `BirthEvent`/`reputation_decay_rate` proposal is
explicitly rejected, not adopted). Do not hand-edit the parity ledger YAML directly.
**Verify:** `python3 tools/parity_ledger_writer.py`'s own schema validation (run with `--help`
first to confirm current CLI invocation shape, since this session's own `--help` probe returned no
usage text and needs re-checking before use), plus a visual diff confirming only one new `SOC-267`
block was added and no existing entries were altered.

## Scope Guards

- **Do not touch `regional_reputation`** (`social.py:48`) or `SocialUpdate.regional_reputation_delta`
  (`updates.py:310`) anywhere in this ticket — confirmed by investigation as always-empty at
  construction for a newborn, with no design-doc precedent for a region-selection rule. Any
  `regional_reputation`-touching test in `tests/unit/social/test_relationships.py`
  (`test_public_reputation_locality_differs_by_region_after_region_scoped_event`,
  `test_regional_reputation_delta_clamped_to_public_reputation_range`) must pass unchanged as a
  regression guard that this ticket did not silently expand into that field.
- **Do not build a `BirthEvent` class or a `reputation_decay_rate` field** — explicitly Out of
  Scope; contradicts the epic's own verified "no decay logic needed" finding
  (`docs/brainstorm/rpg_expected_schemas.html`'s schema-53 proposal is rejected).
- **Do not touch `ReputationUpdateService`** (`src/domains/commitment/reputation.py:11`) or
  `PublicReputationProfile` (`src/core/cognition.py:516`) — structurally separate systems that only
  share a name with `SocialComponent.public_reputation`; AC5's source-text guard (Step 7) enforces
  this.
- **Do not add any new field to `SocialUpdate`** (`updates.py:287-370`) — the birth-seed write goes
  through the pre-existing `.social(public_reputation=...)` construction-time kwarg, not through
  `SocialUpdate`/`process_update()` at all.
- **Do not add any decay logic, periodic call site, or new field to
  `RelationshipService.process_update()`** (`relationships.py:16-100`) — confirmed by investigation
  to already have zero passive decay on `public_reputation`; Step 6 proves this stays true, it does
  not change it.
- **Do not touch `spawn_natural_creature_offspring()` or `spawn_magical_demonic_entity()`**
  (`generator.py:86-152`) — no new kwargs, no `.birth_record()` call changes on either path.
- **Do not touch idea 60's landed field shape or idea 54's `ClanState.clan_reputation`** — sibling
  epic tickets, out of scope here.
- **Do not edit `tests/architecture/test_social_write_paths.py`'s `ALLOWED_FILES` or
  `_WRITE_PATTERN`** unless Step 7's implementation genuinely reveals a need — treat any such need
  as a stop-and-investigate signal, not a routine edit.
- **Do not hand-edit `docs/parity_ledger/social_narrative.yaml`** — `tools/parity_ledger_writer.py`
  only.

## Dependency Map

- Step 1 (pure combine function) has no dependencies — can be implemented and reviewed first.
- Step 2 depends on Step 1 (imports `ReputationService.combine_public_reputation()`).
- Step 3 depends on Step 2 (`spawn_humanoid_offspring()` calls the extended `birth_record()`).
- Step 4 depends on Step 3 (the call site needs the new parameters to exist on
  `spawn_humanoid_offspring()`).
- Step 5 is independent of Steps 1-4 in terms of code touched (parentless paths are untouched) but
  is most naturally verified after Step 2 lands, to confirm the new kwargs' default (`None`)
  behavior by contrast.
- Step 6 is independent of Steps 1-5 (tests existing, unchanged `process_update()` behavior) — can
  run any time, but is most meaningful once Step 2 exists to produce a birth-seeded value to test
  against.
- Step 7 depends on Steps 1 and 2 (needs both new functions' source to exist to inspect).
- Step 8 depends on Steps 1-7 being functionally complete and their tests green (docs describe
  landed behavior, not planned behavior).

Recommended implementation order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 (matches step numbering).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — both parents supplied yields a value strictly between them | Steps 1, 2 | `test_birth_record_seeds_public_reputation_from_both_parents_average` (`tests/unit/progression/test_lifecycle.py`) |
| AC2 — zero or exactly one parent value supplied falls back to class default | Step 2 | `test_birth_record_public_reputation_falls_back_to_default_with_partial_parent_data` (`tests/unit/progression/test_lifecycle.py`) |
| AC3 — natural-creature/magical-demonic parentless paths keep class-default reputation | Steps 3, 5 | `test_natural_creature_and_magical_demonic_paths_never_seed_public_reputation` (`tests/unit/world/test_natural_creature_reproduction.py`) |
| AC4 — heroism/notoriety deltas move a birth-seeded value identically to the class default | Step 6 | `test_heroism_and_notoriety_deltas_apply_identically_to_birth_seeded_reputation` (`tests/unit/social/test_relationships.py`) |
| AC5 — new write path never imports/calls `ReputationUpdateService`/`PublicReputationProfile` | Steps 1, 2, 7 | `test_reputation_seed_write_path_does_not_reference_reputation_update_service` (`tests/architecture/test_social_write_paths.py`) |

Additional (not a literal AC, closes the real-call-chain gap): Steps 3, 4 →
`test_humanoid_reproduction_seeds_child_public_reputation_from_parents`
(`tests/unit/world/test_reproduction_humanoid_cadence.py`).

## Anti-Drift Notes

- **AC2 governs over Scope's looser wording (Decision 1, locked in above).** The implementer must
  write the AND-gate (`is not None and is not None`), not an OR-gate or a "seed from whichever is
  supplied, default-filling the other" reading — that would pass a naive reading of the Scope
  section but fail AC2's own test. This is the single highest-risk spec-ambiguity in this ticket
  per the investigation.
- **Combine function lives in `src/systems/social_systems/reputation.py` on the existing
  `ReputationService` class (Decision 2, locked in above)** — not in `relationships.py` (would blur
  the SOC-217 sole-authoritative-writer file's identity) and not as a new standalone module (a
  fitting pure-function home already exists).
- **`regional_reputation` is the single most likely scope-creep vector** given its newness and
  topical adjacency (landed same day by the prerequisite ticket) — this ticket seeds only
  `public_reputation`, per the investigation's recommendation and idea 53's own card text.
- **Two-parent combine must trigger on the new reputation kwargs' own presence, not on
  `parent_a_entity_id`/`parent_b_entity_id` presence** — the parentless paths pass explicit
  `parent_a_entity_id=None, parent_b_entity_id=None` but never the new reputation kwargs at all;
  the gate in Step 2 checks the reputation kwargs directly, matching the genetics precedent's own
  design (gated on `parent_a_genetic_profile`/`parent_b_genetic_profile` presence, not id
  presence).
- **No fallback-generation function is needed or should be added** for reputation, unlike genetics'
  `generate_profile_from_seed()` — every entity's `public_reputation` always holds a real value.
  Adding such a function would be unnecessary and contradict AC2's "fall back to class default when
  incomplete" contract.
- **`tests/unit/domains/` must be included in the Test phase's scoped pytest command** whenever
  `src/core/` is touched (this ticket touches `src/core/builder.py`) — a confirmed structural
  coverage backstop from the sibling `TCK-20260904-REPUTATION-LOCALITY-SCOPE` ticket, even though no
  specific `tests/unit/domains/` subtest currently asserts on `SocialComponent` directly.
- **Determinism/canonical-hash coverage needs no new code** — `StateFingerprinter.get_fingerprint()`
  (`src/replay/fingerprint.py:69`) already covers `public_reputation` unconditionally; run
  `tests/unit/core/test_entity_integrity.py` as a verification pass only, not an implementation
  step.
