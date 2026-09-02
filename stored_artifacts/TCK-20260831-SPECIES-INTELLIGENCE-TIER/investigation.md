---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260831-SPECIES-INTELLIGENCE-TIER
artifact_type: investigation
tags: [content]
---

# Investigation — TCK-20260831-SPECIES-INTELLIGENCE-TIER

## Current Behavior

### `RaceDefinition` (`src/content/schema.py:134-143`)

```python
class RaceDefinition(CatalogBaseDefinition):
    """Schema for dynamic race/species definition."""
    body_model: str = Field(..., description="Referenced BodyModelDefinition ID")
    need_profile: str = Field(..., description="Referenced NeedProfileDefinition ID")
    sense_profile: str = Field(..., description="Referenced SenseProfileDefinition ID")
    cognition_profile: str = Field(..., description="Referenced CognitionProfileDefinition ID")
    drive_profile: str = Field(..., description="Referenced DriveProfileDefinition ID")
    natural_traits: List[str] = Field(default_factory=list)
    attribute_tendencies: Dict[str, str] = Field(default_factory=dict)
    compatible_roles: List[str] = Field(default_factory=list)
```

All three fields the ticket assumes exist are confirmed exactly as claimed: `natural_traits:
List[str]`, `attribute_tendencies: Dict[str, str]`, `cognition_profile: str`. There is no
`intelligence_tier` field today and no true Python `Enum`/`Literal[...]` type anywhere in
`schema.py` — the closest existing "enum" convention in this module is a plain `str` field
validated by a `@field_validator` against a hardcoded set, e.g. `FactionDefinition.legacy_engine_bucket`
(schema.py:160-166) and `RoleDefinition.legacy_engine_role` (schema.py:178-184). If Plan specifies
`intelligence_tier: enum(high|low)`, the established in-repo pattern is a `str` field + validator
against `{"high", "low"}`, not `Literal["high","low"]` — worth flagging so Plan/Implement don't
introduce a new, inconsistent typing convention.

`RaceDefinition` inherits `CatalogBaseDefinition` (schema.py:8-20), which sets
`model_config = ConfigDict(frozen=True, extra="forbid")`. This confirms the ticket's assumed
`extra="forbid"` convention, and additionally confirms instances are **frozen** (immutable after
construction) — consistent with the Durable State / immutability posture elsewhere in the project.
This matches the precedent set by `TCK-20260831-RACE-RELATIONS-MATRIX` (confirmed via the parent
agent's own pre-pass: that ticket authored a new content family, `race_relations`, and did not
touch `RaceDefinition` itself).

### `CatalogRepository` (`src/content/repository.py`)

`repo.races: Dict[str, RaceDefinition]` (repository.py:185) is populated by `load_all()`.
`get_race(def_id) -> Optional[RaceDefinition]` (repository.py:435-436) is the public accessor. No
resolver or compile-time consumer reads `natural_traits`/`attribute_tendencies`/`cognition_profile`
to derive anything named `intelligence_tier` or an equivalent concept today — `LivingDefaultsResolver`
only propagates `need_profile`/`sense_profile`/`body_model`/etc. as defaults onto entity archetypes
(`tests/unit/content/test_resolvers.py::TestLivingDefaultsResolver`), it does not synthesize new
race-level fields.

### The 13-race roster (`data/content/living/races.yaml`) — full table

| Race | `tool_user` in `natural_traits`? | `attribute_tendencies.intelligence` | `cognition_profile` | Anchor-rule tier |
|---|---|---|---|---|
| human | YES | medium_high | practical_humanoid | high (clean) |
| goblin | YES | medium_low | opportunistic_humanoid | high (clean) |
| orc | YES | medium_low | opportunistic_humanoid | high (clean) |
| elf | YES | high | arcane_scholar | high (clean) |
| dwarf | YES | medium | practical_humanoid | high (clean) |
| lizardfolk | YES | medium | practical_humanoid | high (clean) |
| wolf | NO | low | instinctive_animal | low (clean) |
| spider | NO | very_low | instinctive_animal | low (clean) |
| undead | NO | low_medium | undead_fixated | low (clean) |
| troll | NO | low | instinctive_animal | low (clean) |
| slime | NO | very_low | instinctive_animal | low (clean) |
| dragonkin | NO | high | arcane_scholar | **AMBIGUOUS** |
| spirit | NO | medium_high | arcane_scholar | **AMBIGUOUS** |

Exact source lines: human (races.yaml:2-19), wolf (22-39), goblin (42-59), spider (62-79), orc
(82-99), elf (102-120), dwarf (123-139), undead (142-157), troll (160-175), lizardfolk (178-193),
dragonkin (196-212), slime (215-230), spirit (233-246).

### Verification of the ticket's 6/13 clean-anchor claim

Confirmed exactly: **human, goblin, orc, elf, dwarf, lizardfolk** are the 6 races carrying
`tool_user` in `natural_traits`. All 6 have distinct, non-overlapping `attribute_tendencies.intelligence`
values ranging from `medium_low` (goblin, orc) to `high` (elf) — proving the ticket's framing that
`attribute_tendencies.intelligence` is a "false friend": goblin and orc are both `tool_user`-anchored
"high" tier but read `medium_low` qualitatively, which would produce the wrong classification if
that field were used as the anchor instead of `natural_traits`.

The 5 non-ambiguous "low" races — **wolf, spider, undead, troll, slime** — all genuinely lack
`tool_user`, all have `intelligence` in the `very_low`..`low_medium` band (never above), and 4 of 5
share `cognition_profile: instinctive_animal` (the exception, undead, has its own unique
`undead_fixated` profile, not shared with any `tool_user` race). None of these 5 shares
`cognition_profile` with any of the 6 clean-high races. This confirms the ticket's claim: the
binary is genuinely clean for 11/13 races, leaving **dragonkin and spirit** as the only two races
where the anchor rule and other signals disagree.

### The dragonkin/spirit edge case — full evidence for Plan's review

Both dragonkin and spirit:
- Lack `tool_user` in `natural_traits`.
- Have `attribute_tendencies.intelligence` in the high band (dragonkin: `high`; spirit: `medium_high`
  — the ticket's characterization of "both have high/medium_high" is confirmed exactly, one per
  race).
- Share `cognition_profile: arcane_scholar` with elf (the highest-tier clean `tool_user` race).

Additional evidence found during this investigation, not stated in the ticket, that bears directly
on Plan's decision:

- **`arcane_scholar` (`data/content/living/cognition_profiles.yaml:63-72`) is the single most
  cognitively capable profile in the entire catalog**: `planning_depth: high`, `abstraction:
  very_high`, `tool_reasoning: high` — the only profile in the file with `tool_reasoning: high`
  (every other profile that isn't `none`/`low` tops out at `medium`, e.g. `practical_humanoid`,
  `opportunistic_humanoid`, `trade_pragmatist`, `disciplined_guard` all have `tool_reasoning:
  medium`). This is a real mechanical tension against the `natural_traits` anchor: dragonkin and
  spirit are authored with the *highest* `tool_reasoning` value of any race in the roster, despite
  not carrying the `tool_user` trait literally.
- **Physical embodiment evidence points the other way.** `data/content/living/body_models.yaml`:
  dragonkin's body model (`winged_reptilian`, lines 51-55) and spirit's (`spirit_body`, lines
  37-41) both have `equipment_slots: ["trinket"]` only — no `weapon`/`armor`/`tool` slot. Every
  `tool_user`-anchored race's body model (`standard_humanoid`, `small_humanoid`, `large_humanoid`)
  has `equipment_slots` including `"tool"` (and the body model's own independent `traits` list also
  separately carries `tool_user` for those three humanoid body models, never for
  `winged_reptilian`/`spirit_body`). So at the body-model layer, dragonkin and spirit are
  structurally non-tool-using (no hands/tool slot) even though their cognition and attribute
  values read as highly intelligent — a real anatomy-vs-cognition split, not just an authoring
  inconsistency.
- **`spirit`'s `attribute_tendencies` dict is incomplete relative to every other race** — it only
  authors `intelligence`, `perception`, `willpower`, `magic_affinity` (races.yaml:241-245),
  omitting `strength`/`agility`/`endurance`/`instinct`/`charisma` entirely (consistent with having
  no physical body — `spirit_body`, shared with `undead`, whose need_profile is `spirit_anchor`
  vs. undead's `undead_purpose`).

This investigation does not decide the dragonkin/spirit classification — that is explicitly Plan's
call per the ticket's own framing — but the evidence above shows the tension is genuine and cuts
both ways (cognition/attributes argue "high", body-model equipment capacity argues "low"), so
Plan should treat it as a real design decision with a documented rationale, not a mechanical
tie-break.

### `supports_adventure_routing` cross-check (`CognitionProfileDefinition`, schema.py:91-101)

Already a real field (landed by `TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY`,
schema.py:101). Per `data/content/living/cognition_profiles.yaml`: `practical_humanoid`,
`opportunistic_humanoid`, `disciplined_guard`, `trade_pragmatist`, and `arcane_scholar` all have
`supports_adventure_routing: true`; `instinctive_animal` and `undead_fixated` have it `false`. This
means `intelligence_tier` (once added) would happen to correlate 1:1 with
`supports_adventure_routing` for all 13 races under either dragonkin/spirit resolution (since both
races already use `arcane_scholar`, which is `true`) — i.e. no race would end up "high tier,
adventure-ineligible" or vice versa given the current data. This is incidental, not a mechanical
coupling — `AdventureGoalScorer` (per `docs/simulation/domains/adventure_contract.md`) reads
`supports_adventure_routing` directly off the resolved `CognitionProfileDefinition`, never off
`RaceDefinition`, and this ticket does not change that. Worth Plan noting only so a future ticket
doesn't assume the two fields are the same axis.

## Mechanics / Engine Constraints

No chapter of the Mechanics Bible (`docs/mechanics/01_entity_anatomy.md` through
`06_worldbuilding_foundation.md`) mentions `RaceDefinition`, `natural_traits`, or any species/race
classification concept — grepped all six chapters, zero hits. Species/race content is documented
only in `docs/mechanics/content_usage_matrix.md` (family-level entry, not field-level) and the
non-authoritative brainstorm atlas `docs/brainstorm/rpg_expected_schemas.html`. There is no
existing mechanics law this ticket must reconcile with — `intelligence_tier` is a genuinely new
axis, not a reinterpretation of a documented one. The `extra="forbid"` / `frozen=True` posture on
`CatalogBaseDefinition` is the only real engine-contract-adjacent constraint: the new field must be
declared on the model (not smuggled through `metadata`/`extension`) or catalog loading will
fail-closed on unrecognized keys once authored in YAML — this is by design (see
`test_schema_fail_closed_unknown_field`, `tests/unit/content/test_catalog.py:219-231`) and is the
correct behavior to preserve, not a gap.

## Docs Requiring Update

None.

The ticket's own "Related Docs" list names two paths. Both were checked and neither requires a
change:

The `docs/mechanics/content_usage_matrix.md` (path: `docs/mechanics/content_usage_matrix.md`,
under `docs/`) row for `living/races` (`content_usage_matrix.md:38`) is not required to change for
this ticket. This file states in its own header that it "is generated dynamically" from
`CONTENT_USAGE_MATRIX` (a Python dict in `src/content/matrix.py`, per
`tests/unit/content/test_content_usage_matrix.py`'s imports) via `generate_matrix_report`. The row
is family-level, not field-level (columns: file path, schema class, repo index, validator
coverage, resolver, compile/runtime consumer, test coverage, evidence tests, resolver evidence,
runtime consumer evidence, implementation state, content maturity) — it does not enumerate
`RaceDefinition`'s individual fields. This ticket adds a field with zero new resolver/consumer
wiring (see "Prior Work" below — confirmed zero production consumers) and the regression test this
ticket adds belongs in `tests/unit/content/test_catalog.py`, a file already listed in the row's
"Test Coverage" column. Nothing in the row's actual content changes as a result of this ticket, so
neither the source dict nor the generated report needs editing.

The `docs/brainstorm/rpg_expected_schemas.html` (path: `docs/brainstorm/rpg_expected_schemas.html`,
under `docs/`) is a forward-looking proposal/atlas doc (schema-14 section, lines 676-680, already
describes `RaceDefinition.intelligence_tier: enum: high | low` with a `"badge gated" / "New field"`
marker, and correctly names the `natural_traits` containing `tool_user` anchor and the
`attribute_tendencies.intelligence` false-friend). It is not required to change for this ticket:
checked whether this doc family is retroactively updated when a proposed field actually ships, by
searching for two other fields that shipped after being proposed in this same file family —
`supports_adventure_routing` (shipped by `TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY`)
and `hazard_immunities` (shipped by `TCK-20260701-HAZARD-NATIVE-IMMUNITY`) — and found **zero**
mentions of either field anywhere in `rpg_expected_schemas.html`. That confirms this file is not
maintained as a ship-status tracker by the tickets that implement its proposals; it stays as
authored at proposal time. (Separately: per project convention, `docs/brainstorm/rpg_feature_atlas.html`
and `docs/brainstorm/simulation_capabilities.html` are the pages that get synced on
gameplay-visible changes — `rpg_expected_schemas.html` is a different, schema-only atlas page not
covered by that convention, and this ticket's own Related Docs list does not name either of those
two pages.)

No Mechanics Bible chapter, engine contract, or parity ledger entry references race/species
intelligence classification (see "Parity Ledger Overlap" below), so there is nothing else to
update there either.

## Parity Ledger Overlap

Searched all 8 parity ledger files for `race`/`RaceDefinition`/`intelligence_tier`. All hits found
are unrelated to species-intelligence classification: race-relations hostility escalation
(`combat_movement.yaml:4116-4119`, `social_narrative.yaml:3725-3729`, `strategic_cognition.yaml:3869`
— all from the just-landed `TCK-20260831-RACE-RELATIONS-MATRIX`), terrain race-label coverage
(`world_dynamics.yaml:186,544`, `substrate.yaml:1709`), spawn-tier defaults
(`social_narrative.yaml:452,716`), bravery/race correlation (`strategic_cognition.yaml:3291`,
`substrate.yaml:4486-4490`), and a progression entry noting no "slime" race/archetype exists for a
specific quest target (`progression.yaml:1417-1427` — unrelated; that's about quest target
resolution, not species classification). **No P0 entries are touched.** No new parity ledger entry
is needed: this ticket adds an unconsumed schema/data field, not a behavior change to any
already-tracked mechanic.

## Prior Work

- `stored_artifacts/TCK-20260831-RACE-RELATIONS-MATRIX/` — most recent, directly adjacent work on
  `RaceDefinition`-family content (added a new `race_relations` content family + wired hostility
  escalation). Confirmed by the parent agent's pre-pass and independently re-confirmed here:
  `RaceDefinition` itself (schema.py:134-143) was not touched by that ticket — it added a sibling
  schema class, `RaceRelationRecord` (schema.py:202-207), not a field on `RaceDefinition`.
- `stored_artifacts/TCK-20260701-HAZARD-NATIVE-IMMUNITY/` — closest real precedent for "add one new
  field to an existing `CatalogBaseDefinition` subclass, author it across the real data, and test
  it." That ticket added `FactionDefinition.hazard_immunities: List[str]` (schema.py:158) and the
  test pattern it established (`test_faction_definition_hazard_immunities_field` +
  `test_faction_catalog_loads_with_hazard_immunities_authored`, both in
  `tests/unit/content/test_catalog.py:251-289`) is a directly reusable shape for this ticket's new
  test, adjusted for the fact that `intelligence_tier` has no safe default (every race must
  explicitly author it) whereas `hazard_immunities` defaults to `[]`.
- `stored_artifacts/TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY/` and
  `docs/architecture/2026-08-10-cognition-driven-adventure-eligibility-design.md` — precedent for
  adding a field to a sibling `CatalogBaseDefinition` subclass (`CognitionProfileDefinition`) that
  gates real runtime behavior; contrast case showing what a "field with a real consumer" looks like,
  versus this ticket's zero-consumer field.
- `docs/plans/rpg_design_roadmap/rpg_m2_foundational_systems_epic.md` (lines 74, 126, 676-680,
  702-709, 924) — the epic source; already carries the anchor-rule rationale and confirms this
  ticket's scope is a faithful narrowing of the epic's idea 14.
- `tickets/todos/m2-foundational-systems/SEQUENCE.md` — records the real cross-ticket dependency:
  `TCK-20260831-ROLE-MODEL-IMITATION` (idea 27) has a hard dependency on this ticket's
  `intelligence_tier` field and must not start until this ticket lands.

## Risks and Open Questions

- **Dragonkin/spirit classification is a genuine open design call, not resolvable from data
  alone.** See the "current behavior" section above for the full evidence split (cognition/attribute
  signals vs. body-model/equipment signals disagree). Plan must make and justify this call; this
  investigation deliberately does not.
- **Should `intelligence_tier` be required (no default) or optional with a default?** Given the
  ticket's AC requires *every* one of the 13 races to carry an explicit authored value, and the
  established pattern for a truly universal field on `RaceDefinition` is a required `Field(...)`
  (e.g. `body_model`, `cognition_profile` are both required), a defaulted/optional field risks
  silently passing validation for a future 14th race that forgets to author it — which would
  undercut the ticket's own "explicit, not silently mechanized" intent. Recommend Plan specify
  `Field(...)` (required), not `Field("low")` or similar.
- **Zero real production consumers today — confirmed.** Grepped the full repo for
  `intelligence_tier` outside this ticket's own files and the epic docs: the only hits are this
  ticket, its `tickets/todos/m2-foundational-systems/` duplicate copy (pre-`implement-epic`
  materialization — normal, not a gap), `TCK-20260831-ROLE-MODEL-IMITATION.md` (the future
  consumer, still in `tickets/todos/`, correctly gated on this ticket per SEQUENCE.md), and
  `docs/plans/rpg_design_roadmap/rpg_m2_foundational_systems_epic.md`/`docs/brainstorm/rpg_expected_schemas.html`
  (planning docs). `src/strategy/cognition_capacity.py` (the module `TCK-20260831-ROLE-MODEL-IMITATION`'s
  own investigation cites as having zero existing species-classification concept) was read in full
  — confirmed: it derives `CognitionProfile` limits purely from `intelligence`/`wisdom`/`perception`
  attributes and biological pressure, with no race or species-tier concept anywhere. The ticket's
  own AC #5-equivalent (Assumptions) — "decide whether a stub consumer/predicate is required" — is
  a real open decision for Plan; this investigation surfaces the fact pattern (truly zero consumers,
  one concretely-planned future consumer already gated correctly in SEQUENCE.md) without
  prescribing the answer.
- **`tickets/todos/m2-foundational-systems/TCK-20260831-SPECIES-INTELLIGENCE-TIER.md` still exists**
  as a duplicate of the now-`tickets/inprogress/` file (normal `implement-epic` materialization
  artifact, not unique to this ticket) — standard "After Work" cleanup (delete the `tickets/todos/`
  source file) applies at Finalize, not a new finding.

## Anti-Drift Hazards

- **Do not let the dragonkin/spirit review expand into re-tiering any of the other 11 races.** The
  6/13 clean `tool_user` anchor and the 5 clean non-`tool_user` races are independently confirmed
  correct against real data in this investigation — there is no ambiguity there to "fix."
- **Do not pull `settlement_capacity` (idea 44) into this ticket.** It shares the same epic
  paragraph and the same `RaceDefinition` target class as `intelligence_tier`, and the epic doc
  itself (line 924) lists both fields side by side as siblings — easy to accidentally scope-creep
  into authoring both at once. The ticket's own Out of Scope section already excludes it explicitly;
  this investigation found no code or data reason to revisit that exclusion.
- **Do not wire `intelligence_tier` into `AdventureGoalScorer`/`supports_adventure_routing`.** They
  are separate axes on separate schema classes (`RaceDefinition` vs. `CognitionProfileDefinition`)
  that happen to correlate for all 13 races today only because both ambiguous races (dragonkin,
  spirit) already use `arcane_scholar`. Coupling them would be a real architectural conflation the
  ticket does not ask for.
- **Do not introduce a `Literal[...]`/Python `Enum` type for `intelligence_tier`** unless Plan
  explicitly decides to break from the existing `str` + `@field_validator` convention used for
  every other enum-like field in `schema.py` — doing so silently would be an inconsistent-pattern
  regression, not a neutral implementation choice.
- **Do not touch `docs/mechanics/content_usage_matrix.md` directly** — it is a generated report
  (see "Docs Requiring Update"); a manual hand-edit would drift from `src/content/matrix.py` the
  next time the generator runs.
