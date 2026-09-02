---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260831-SPECIES-INTELLIGENCE-TIER
artifact_type: plan
tags: [content]
---

# Implementation Plan — TCK-20260831-SPECIES-INTELLIGENCE-TIER

## Summary

Add a required, `str`-typed, `@field_validator`-enforced `intelligence_tier` field (`"high"` /
`"low"`) to `RaceDefinition` (`src/content/schema.py:134-143`), author it explicitly for all 13
races in `data/content/living/races.yaml` per the `tool_user`-in-`natural_traits` anchor rule
(confirmed clean for 11/13 races), and resolve dragonkin/spirit — the two races where the anchor
disagrees with their cognition/attribute signals — as **`"high"`** for both, with the reasoning
below. Add three regression tests to `tests/unit/content/test_catalog.py` following the
`FactionDefinition.hazard_immunities` precedent (`TCK-20260701-HAZARD-NATIVE-IMMUNITY`). Also patch
two pre-existing synthetic `RaceDefinition`-shaped fixtures in
`tests/unit/content/test_layered_catalog.py` (the `"broken_race"` fixture and the `"human"`
fixture) to carry an authored `intelligence_tier`, since Step 1's required-no-default field
otherwise causes both records to be silently dropped from `repo.races`
(`CatalogRepository.load_all()` swallows the resulting pydantic `ValidationError` via
`try/except Exception: continue`, `src/content/repository.py:318-327`) — this is a real finding
from architecture review, not a hypothetical: the reviewer applied Step 1's exact diff to a clean
tree and confirmed `tests/unit/content/test_layered_catalog.py` regresses from `3 passed`
(baseline) to `2 failed, 1 passed`. No resolver, consumer, doc, or parity-ledger changes —
this ticket ships an unconsumed, fully-typed field only (mirrors the `TCK-20260831-CLAN-STATE-SCHEMA`
precedent, `tickets/done/TCK-20260831-CLAN-STATE-SCHEMA.md`
/ `stored_artifacts/TCK-20260831-CLAN-STATE-SCHEMA/`, of shipping inert-but-typed scaffolding with
zero consumers).

## The Dragonkin/Spirit Decision (AC #2 — explicit review, not silent mechanization)

**Decision: both `dragonkin` and `spirit` are classified `"high"`.**

### Evidence reviewed

- **Primary signal — `cognition_profile` (schema.py:91-101, data authored in
  `data/content/living/cognition_profiles.yaml:63-72`):** both races use `arcane_scholar`, which is
  the single most cognitively capable profile in the entire catalog — `tool_reasoning: "high"` is
  unique to this profile (every other non-`instinctive_animal`/`undead_fixated` profile —
  `practical_humanoid`, `opportunistic_humanoid`, `disciplined_guard`, `trade_pragmatist` — tops out
  at `tool_reasoning: "medium"`; verified by reading the full file). `arcane_scholar` is otherwise
  used only by `elf` (`data/content/living/races.yaml:102-120`), one of the 6 confirmed-clean
  `tool_user` "high" races.
- **Counter-signal — `natural_traits` (the ticket's stated primary anchor) and body-model
  `equipment_slots`:** neither race has `tool_user` in `natural_traits`
  (dragonkin: `races.yaml:203`, spirit: `races.yaml:238`), and their body models —
  `winged_reptilian` (`data/content/living/body_models.yaml:51-55`) and `spirit_body`
  (`body_models.yaml:37-41`) — both carry `equipment_slots: ["trinket"]` only, with no `"tool"`
  slot, unlike every real `tool_user` race's body model (`standard_humanoid`/`small_humanoid`/
  `large_humanoid`, all of which list `"tool"` and also separately carry `tool_user` in their own
  `traits` list — read in full, `body_models.yaml:2-59`).
- **Secondary signal checked and downweighted — `compatible_roles`.** Read the full
  `compatible_roles` list for all 13 races (`races.yaml`, all `compatible_roles:` lines). Dragonkin
  (`["dragon_champion", "mage", "leader"]`) and spirit (`["guardian", "healer", "leader"]`) both
  carry agency/leadership roles rather than pure-beast roles (contrast `wolf`: `["predator_hunter",
  "alpha"]`, `spider`/`slime`: `["predator_hunter"]`). This initially reads as corroborating
  "high" — but `troll` (`["brute", "leader"]`, clean-low, `cognition_profile: instinctive_animal`)
  and `undead` (`["sentinel", "raider", "leader"]`, clean-low, `cognition_profile: undead_fixated`)
  both also carry `"leader"` despite being unambiguous clean-low races. This proves
  `compatible_roles` alone is **not** a reliable tier discriminator in this dataset (a `"leader"`
  role does not imply high cognitive tier) — it is used here only as weak, non-decisive
  corroboration, not as independent evidence for the decision.
- **Spirit's incomplete `attribute_tendencies`** (`races.yaml:241-245`: only `intelligence`,
  `perception`, `willpower`, `magic_affinity` — no `strength`/`agility`/`endurance`/`instinct`/
  `charisma`) confirms spirit has no physical body at all (consistent with `spirit_body`'s
  `movement_modes: ["float"]`). This is additional evidence *for* treating spirit's "no tool slot"
  as a fact about embodiment, not about cognitive capacity — it never had hands to lack a tool in.

### Why cognition wins over the anchor for these two races specifically

The ticket's own stated downstream purpose (idea 27 / `TCK-20260831-ROLE-MODEL-IMITATION`, read in
full at `tickets/todos/m2-foundational-systems/TCK-20260831-ROLE-MODEL-IMITATION.md`) is to "wire
imitation-sophistication **scaling** to read `intelligence_tier` ... **to modulate behavior**."
This is a cognitive-capacity gate on how sophisticated an entity's learned/imitated behavior can
be, not a physical-dexterity gate on whether an entity can wield a specific item. The `tool_user`
anchor was chosen by the ticket as an *observable proxy* for cognitive/civilizational sophistication
— and it is a very good proxy for 11/13 races, where `tool_user` presence and `arcane_scholar`/
`practical_humanoid`/etc. cognitive sophistication co-occur perfectly. For dragonkin and spirit,
the proxy and the underlying signal it stands in for diverge: both lack the literal trait, but both
are authored with the *single most cognitively sophisticated profile in the catalog* — a stronger
and more direct signal of the actual thing `intelligence_tier` is meant to capture (per its own
name and idea 27's stated use) than the absence of a body-model equipment slot, which governs
combat/inventory item-equip compatibility (a separate, already-serving axis of the schema — see
Anti-Drift Notes) rather than cognitive capacity. `equipment_slots` answers "can this body wear a
`tool`-tagged item," not "can this species reason, plan, and imitate sophisticated behavior."
Given the two signals conflict specifically for these two races, and the field's stated purpose
maps onto the cognition axis, both dragonkin and spirit resolve to **`"high"`**.

They resolve identically here, but for asymmetric reasons worth recording: dragonkin has a
physical body that structurally lacks tool-manipulation (a taloned/winged form with no `tool`
equipment slot); spirit has no physical body at all (attribute_tendencies omits every physical
attribute). Neither asymmetry changes the cognition-axis conclusion.

## Field Type and Required/Optional Decision

- **Type: `str` field + `@field_validator`, not `Enum`/`Literal`.** Confirmed by reading
  `src/content/schema.py:1-210` in full: there is no true `Enum`/`Literal[...]` type anywhere in
  the module. The established convention for every enum-like field is a plain `str` validated
  against a hardcoded set — `FactionDefinition.legacy_engine_bucket` (schema.py:150-166) and
  `RoleDefinition.legacy_engine_role` (schema.py:169-184) both follow this exact shape (a `str`
  field plus a `@field_validator` classmethod raising `ValueError` on an out-of-set value). Step 1
  below follows this precedent exactly for `intelligence_tier`, validated against
  `{"high", "low"}`. No strong reason to deviate — deviating would introduce a second,
  inconsistent enum-typing convention into the same file for no schema-expressiveness gain (both
  approaches equally reject invalid values at construction time).
- **Required, no default** (`Field(...)`, mirroring `body_model`/`cognition_profile`/etc., all
  required on `RaceDefinition`, schema.py:136-140) — not `Field("low")` or similar. AC #2 requires
  every one of the 13 races to carry an explicit authored value; a defaulted/optional field would
  let a future 14th race pass catalog validation without ever authoring `intelligence_tier`,
  silently defeating the ticket's own "explicit, not silently mechanized" intent. This differs
  deliberately from the `hazard_immunities` precedent (`List[str] = Field(default_factory=list)`,
  schema.py:158), which is intentionally optional because "no factions have this hazard" is a valid
  state — there is no equivalent valid "no tier" state for `intelligence_tier`.

## Stub Consumer Decision

**No stub consumer/predicate is added.** Confirmed zero real production consumers exist today
(investigation.md "Prior Work" / "Risks and Open Questions" — grepped the full repo for
`intelligence_tier` outside this ticket's own files; only hits are this ticket, its
`tickets/todos/` pre-materialization duplicate, `TCK-20260831-ROLE-MODEL-IMITATION.md` (the future
consumer, correctly gated on this ticket per `tickets/todos/m2-foundational-systems/SEQUENCE.md`),
and planning docs). This mirrors the `TCK-20260831-CLAN-STATE-SCHEMA` precedent
(`tickets/done/TCK-20260831-CLAN-STATE-SCHEMA.md`) of shipping typed, catalog-validated,
zero-consumer scaffolding and deferring all wiring to the ticket that actually needs it
(`TCK-20260831-ROLE-MODEL-IMITATION`, already sequenced after this one and explicitly scoped to
consume `intelligence_tier` read-only). Adding a stub predicate now would be speculative code with
no caller and no test that exercises real behavior — against the "do not plan more work than the
ticket scope" rule, and against the ticket's own Scope item 5 framing this as an explicit
either/or decision rather than a default-yes.

## Steps

### Step 1 — Add `intelligence_tier` field to `RaceDefinition`

**Files:** `src/content/schema.py`

**Change:** In `RaceDefinition` (schema.py:134-143), add:

```python
intelligence_tier: str = Field(..., description="Species cognitive-sophistication classification: 'high' or 'low', anchored via tool_user presence in natural_traits (see docs/mechanics species-tier note if authored) with explicitly justified exceptions.")
natural_traits: List[str] = Field(default_factory=list)
attribute_tendencies: Dict[str, str] = Field(default_factory=dict)
compatible_roles: List[str] = Field(default_factory=list)

@field_validator("intelligence_tier")
@classmethod
def validate_intelligence_tier(cls, v: str) -> str:
    valid_tiers = {"high", "low"}
    if v not in valid_tiers:
        raise ValueError(f"intelligence_tier must be one of {valid_tiers}")
    return v
```

Field ordering within the class is not load-bearing (pydantic keyword-based construction), but
place `intelligence_tier` near the top of the field list (after the profile-reference fields,
before `natural_traits`) for readability alongside the other classification-shaped fields.
Validator pattern copied exactly from `FactionDefinition.validate_legacy_bucket`
(schema.py:160-166), adjusted to two lowercase values with no `.upper()` normalization (the
ticket's AC states `enum(high|low)` lowercase, matching how `legacy_engine_bucket`'s own valid set
is uppercase by its own convention — `intelligence_tier` has no legacy-engine-name precedent
forcing case, so lowercase matches the ticket's literal AC text and the `hazard_immunities`-style
tag conventions elsewhere in the file, e.g. `"NATURAL_TERRAIN"` is the exception, not the rule, for
free-form tag lists — `intelligence_tier` is a closed enum-like field, not a tag list, so it
follows `legacy_engine_bucket`'s validator shape but not its case-folding).

**Other writers to `RaceDefinition`:** In production, `RaceDefinition` instances are only ever
constructed by `CatalogRepository.load_all()` deserializing `data/content/living/races.yaml`
(`src/content/repository.py`); no runtime code path mutates a `RaceDefinition` (instances are
`frozen=True` via `CatalogBaseDefinition.model_config`, schema.py:10). **Correction (architecture
review, blocking finding — the plan's earlier claim that no other code path constructs a
`RaceDefinition` was false and is retracted):** two test fixtures also construct
`RaceDefinition`-shaped YAML directly, independent of `races.yaml` —
`test_layered_catalog_validation_errors`'s `"broken_race"` fixture and
`test_phase23_reference_graph_and_dead_active_data`'s `"human"` fixture, both in
`tests/unit/content/test_layered_catalog.py` (see Step 2, added below, which patches both). Making
`intelligence_tier` required-no-default means every one of these construction sites — production
YAML and both test fixtures alike — must supply it, or `CatalogRepository.load_all()`'s
`try/except Exception: continue` (`src/content/repository.py:318-327`) silently drops that record.
Adding the field itself is still a pure schema addition with no concurrent-*mutation* risk (the
model stays frozen); the risk this correction addresses is at construction time across all
call sites, not runtime mutation.

**Do NOT touch:** `body_model`, `need_profile`, `sense_profile`, `cognition_profile`,
`drive_profile` field declarations (unchanged, required); `CatalogBaseDefinition` base class
(schema.py:8-20); any other `CatalogBaseDefinition` subclass in the file (`FactionDefinition`,
`RoleDefinition`, `RaceRelationRecord`, etc.).

**Verify:** `test_race_definition_intelligence_tier_field_round_trips` (new, Step 4).

### Step 2 — Patch two pre-existing `RaceDefinition` test fixtures for the new required field

**Files:** `tests/unit/content/test_layered_catalog.py`

**Background (architecture-review finding, empirically verified, not hypothetical):** Step 1 makes
`intelligence_tier` required with no default. `CatalogRepository.load_all()`
(`src/content/repository.py:318-327`) wraps each item's pydantic construction in
`try/except Exception: continue`, so a validation failure on one record silently drops just that
record rather than raising. Two fixtures in this file construct `RaceDefinition`-shaped YAML
without `intelligence_tier` and are silently dropped from `repo.races` once Step 1 lands, breaking
their tests' downstream assertions:
- `test_layered_catalog_validation_errors`'s `"broken_race"` fixture
  (`tests/unit/content/test_layered_catalog.py:104-115`) — the test expects `"broken_race"`'s
  intentionally-broken references (`missing_body`, `missing_need`, etc.) to be flagged by
  `CatalogValidator` as `CAT-REL-017`, not silently excluded from validation entirely.
- `test_phase23_reference_graph_and_dead_active_data`'s `"human"` fixture
  (`tests/unit/content/test_layered_catalog.py:182-187`) — the test expects
  `graph.has_node("race:human")` to be `True`.

The reviewer confirmed this empirically: applying Step 1's exact schema.py diff to a clean tree and
running `tests/unit/content/test_layered_catalog.py` regresses the file from `3 passed` (baseline)
to `2 failed, 1 passed`; reverting Step 1's diff restores `3 passed`.

**Change:** Add an `intelligence_tier` key to both fixture dicts, exactly as they are currently
authored (do not otherwise restructure either fixture):

1. In `test_layered_catalog_validation_errors` (`test_layered_catalog.py:104-115`), the
   `"broken_race"` dict currently reads:

   ```python
   races_data = [
       {
           "id": "broken_race",
           "body_model": "missing_body",
           "need_profile": "missing_need",
           "sense_profile": "missing_sense",
           "cognition_profile": "missing_cognition",
           "drive_profile": "missing_drive",
           "natural_traits": ["missing_trait"],
           "compatible_roles": ["missing_role"]
       }
   ]
   ```

   Add `"intelligence_tier": "low"` immediately after `"cognition_profile": "missing_cognition",`
   and before `"drive_profile": "missing_drive",` (mirrors the key placement convention used for
   the real `races.yaml` records in Step 3 below). The value `"low"` is arbitrary — this is
   synthetic test data standing in for an intentionally-broken record, not real content, so it
   needs no dragonkin/spirit-style justification; any value from `{"high", "low"}` satisfies the
   new `@field_validator` and restores construction. Resulting dict:

   ```python
   races_data = [
       {
           "id": "broken_race",
           "body_model": "missing_body",
           "need_profile": "missing_need",
           "sense_profile": "missing_sense",
           "cognition_profile": "missing_cognition",
           "intelligence_tier": "low",
           "drive_profile": "missing_drive",
           "natural_traits": ["missing_trait"],
           "compatible_roles": ["missing_role"]
       }
   ]
   ```

2. In `test_phase23_reference_graph_and_dead_active_data` (`test_layered_catalog.py:182-187`), the
   `"human"` dict currently reads:

   ```python
   races_data = [{
       "id": "human", "display_name": "Human",
       "body_model": "humanoid", "need_profile": "human_needs",
       "sense_profile": "human_senses", "cognition_profile": "practical_human",
       "drive_profile": "human_drives", "natural_traits": [], "compatible_roles": []
   }]
   ```

   Add `"intelligence_tier": "high"` after `"cognition_profile": "practical_human",` and before
   `"drive_profile": "human_drives",`, keeping the same single-line dict style. `"high"` is chosen
   for readability/consistency with the real `races.yaml` `human` record's own value (Step 3 below
   authors `human` as `"high"`) — not load-bearing for this test, which does not assert on
   `intelligence_tier`. Resulting dict:

   ```python
   races_data = [{
       "id": "human", "display_name": "Human",
       "body_model": "humanoid", "need_profile": "human_needs",
       "sense_profile": "human_senses", "cognition_profile": "practical_human",
       "intelligence_tier": "high",
       "drive_profile": "human_drives", "natural_traits": [], "compatible_roles": []
   }]
   ```

**Other writers to these two fixtures / this file:** None — confirmed via
`grep -n "id.*race\|races.yaml\|RaceDefinition\|races_data" tests/unit/content/test_layered_catalog.py`
that only these two call sites in the file construct `races.yaml`-shaped data; no other in-flight
ticket touches `test_layered_catalog.py` (same Prior Work scan as `test_catalog.py` in Step 4).

**Do NOT touch:** Any other fixture in this file (factions, roles, recipes, regions, biomes,
ecologies, body/need/sense/cognition/drive profile fixtures, etc.); the assertions in either test
(`rule_ids`/`errors` checks in `test_layered_catalog_validation_errors`,
`graph.has_node(...)` checks in `test_phase23_reference_graph_and_dead_active_data`); any other
test in this file.

**Verify:** `pytest tests/unit/content/test_layered_catalog.py -v` — all tests in this file pass
(specifically `test_layered_catalog_validation_errors` and
`test_phase23_reference_graph_and_dead_active_data`, the two the reviewer found regressed).

### Step 3 — Author `intelligence_tier` for all 13 races in `races.yaml`

**Files:** `data/content/living/races.yaml`

**Change:** Add one `intelligence_tier` YAML key to each of the 13 race records, per this table
(anchor rule for 11/13, dragonkin/spirit per the Decision section above):

| Race | `intelligence_tier` | Basis |
|---|---|---|
| human (races.yaml:2-19) | `high` | `tool_user` in `natural_traits` |
| goblin (42-59) | `high` | `tool_user` in `natural_traits` |
| orc (82-99) | `high` | `tool_user` in `natural_traits` |
| elf (102-120) | `high` | `tool_user` in `natural_traits` |
| dwarf (123-139) | `high` | `tool_user` in `natural_traits` |
| lizardfolk (178-193) | `high` | `tool_user` in `natural_traits` |
| wolf (22-39) | `low` | no `tool_user`; `instinctive_animal` |
| spider (62-79) | `low` | no `tool_user`; `instinctive_animal` |
| undead (142-157) | `low` | no `tool_user`; `undead_fixated` |
| troll (160-175) | `low` | no `tool_user`; `instinctive_animal` |
| slime (215-230) | `low` | no `tool_user`; `instinctive_animal` |
| dragonkin (196-212) | `high` | exception — `arcane_scholar` cognition overrides missing `tool_user` (see Decision) |
| spirit (233-246) | `high` | exception — `arcane_scholar` cognition overrides missing `tool_user` (see Decision) |

Add `intelligence_tier: "high"` or `intelligence_tier: "low"` as a new key on each record, placed
immediately after `cognition_profile` (mirrors the field's placement in Step 1) and before
`drive_profile`, to keep every record's key ordering identical across the file for readability.
Do not reorder or otherwise touch any existing key on any record — in particular, do not touch
`natural_traits` or `compatible_roles` list ordering/contents on any race (this is the exact
anti-drift hazard `tests/unit/content/test_resolvers.py`'s ordering tests, listed in Regression
Surface below, exist to catch).

**Other writers to `races.yaml`:** None — this is a static content file, hand-authored, loaded
read-only at catalog-load time by `CatalogRepository.load_all()`. No other in-flight ticket in
`tickets/inprogress/` touches this file (only `TCK-20260831-RACE-RELATIONS-MATRIX`, already `DONE`
per investigation.md "Prior Work," touched a sibling file for a new `race_relations` family, not
`races.yaml` itself).

**Do NOT touch:** `settlement_capacity` (out of scope per ticket, idea 44 — do not add this field
to any race even though the epic doc lists it alongside `intelligence_tier`); any existing field
value on any of the 13 records; the `# STATE: ...` comment markers preceding each record.

**Verify:** `test_all_13_races_have_documented_intelligence_tier` and
`test_race_catalog_loads_with_intelligence_tier_authored` (new, Step 4).

### Step 4 — Add regression tests

**Files:** `tests/unit/content/test_catalog.py`

**Change:** Add three tests, co-located with the `hazard_immunities` precedent tests
(`test_faction_definition_hazard_immunities_field` /
`test_faction_catalog_loads_with_hazard_immunities_authored`, read in full at
`tests/unit/content/test_catalog.py:251-289`), adjusted for `intelligence_tier` being required
(no safe default) rather than optional:

1. **`test_race_definition_intelligence_tier_field_round_trips`** — construct two `RaceDefinition`
   instances directly (supplying all required sibling fields: `id`, `body_model`, `need_profile`,
   `sense_profile`, `cognition_profile`, `drive_profile`, `intelligence_tier`), one `"high"` one
   `"low"`; assert `.intelligence_tier` reads back correctly on each. Also assert that omitting
   `intelligence_tier` entirely raises `pydantic.ValidationError` (the primary guard against a
   future race silently passing validation without an authored value — this is the load-bearing
   assertion given the Required/no-default decision above). Also assert that an invalid value
   (e.g. `"medium"`) raises `ValidationError` via the new `@field_validator`.

2. **`test_all_13_races_have_documented_intelligence_tier`** — load the real catalog via
   `CatalogRepository("data/content").load_all()`, iterate `repo.races`, and assert
   `race.intelligence_tier` for every one of the 13 races matches the exact table in Step 3 above
   (hardcode `EXPECTED_INTELLIGENCE_TIER = {"human": "high", "goblin": "high", "orc": "high",
   "elf": "high", "dwarf": "high", "lizardfolk": "high", "wolf": "low", "spider": "low",
   "undead": "low", "troll": "low", "slime": "low", "dragonkin": "high", "spirit": "high"}`).
   Assert `set(EXPECTED_INTELLIGENCE_TIER) == set(repo.races.keys())` so the test fails loudly if a
   14th race is ever added without an entry here. Additionally, assert the *rule* itself for the
   11 unambiguous races: for each race in `repo.races` whose `race.id` is not `"dragonkin"` or
   `"spirit"`, `("tool_user" in race.natural_traits) == (race.intelligence_tier == "high")` — this
   encodes the anchor rule as an executable invariant, not just a flat lookup, and will catch a
   future race's authored value silently drifting from its own `tool_user` status without an
   equally explicit documented exception added to this test.

3. **`test_race_catalog_loads_with_intelligence_tier_authored`** — assert
   `CatalogRepository("data/content").load_all()` succeeds without raising (catches a YAML
   authoring typo, e.g. a value outside `{"high","low"}` or a missing field on one race, that a
   narrower per-record test might not directly surface as a load failure). This may be folded into
   test 2 above as a single function (both load the real catalog) rather than kept fully separate
   — implementer's call; the AC requires "a regression test," not necessarily a single function.

**Other writers to `test_catalog.py`:** None — this ticket is the only in-flight work touching this
file (confirmed via `tickets/inprogress/` scan in investigation.md's Prior Work section; the
adjacent `hazard_immunities` tests this step sits beside were landed by the already-`DONE`
`TCK-20260701-HAZARD-NATIVE-IMMUNITY`).

**Do NOT touch:** `test_schema_fail_closed_unknown_field`, `test_schema_metadata_nested_field_allowed`,
`test_faction_definition_hazard_immunities_field`,
`test_faction_catalog_loads_with_hazard_immunities_authored`,
`test_schema_compatibility_model_fail_closed`, or any other existing test in this file — all must
pass unmodified (see Regression Surface below).

**Verify:** `pytest tests/unit/content/test_catalog.py -v` — all three new tests pass; all listed
existing tests in this file still pass.

## Scope Guards

- Do not add `settlement_capacity` to `RaceDefinition` or `races.yaml` (idea 44, explicitly out of
  scope per the ticket).
- Do not re-tier any of the 11 unambiguous races (human, goblin, orc, elf, dwarf, lizardfolk, wolf,
  spider, undead, troll, slime) — their anchor-rule classification is independently confirmed
  correct against real data (investigation.md) and is not open for reinterpretation.
- Do not wire `intelligence_tier` into `AdventureGoalScorer`, `supports_adventure_routing`, or any
  other `CognitionProfileDefinition`-based mechanism — separate axis on a separate schema class;
  any incidental 1:1 correlation across the 13 races today (both dragonkin and spirit already use
  `arcane_scholar`, which happens to have `supports_adventure_routing: true`) is coincidental, not
  a coupling this ticket introduces or should encode.
- Do not add a stub consumer/predicate for `intelligence_tier` anywhere in `src/` (see Stub
  Consumer Decision above) — defer entirely to `TCK-20260831-ROLE-MODEL-IMITATION`.
- Do not introduce a Python `Enum`/`Literal` type — follow the `str` + `@field_validator`
  convention (see Field Type Decision above).
- Do not edit `docs/mechanics/content_usage_matrix.md` (generated report, not hand-edited — see
  Docs section below) or `docs/brainstorm/rpg_expected_schemas.html` (proposal atlas, not
  retroactively synced — see Docs section below).
- Do not touch `src/content/repository.py` — `RaceDefinition` is loaded generically via existing
  pydantic deserialization; no repository-level code change is needed for a new field on an
  existing model.
- Do not touch any parity ledger file (see Parity Ledger section below).
- In `tests/unit/content/test_layered_catalog.py` (Step 2), touch only the two named fixture
  dicts' key sets (add `intelligence_tier`) — do not change either test's assertions, do not touch
  any other fixture in the file, and do not add new tests to this file (new tests belong in
  `test_catalog.py`, Step 4, per the existing precedent).

## Docs

**No documentation updates are required for this ticket.** Verified directly:

- `docs/mechanics/content_usage_matrix.md` — confirmed (investigation.md "Docs Requiring Update")
  this file is machine-generated from `CONTENT_USAGE_MATRIX` in `src/content/matrix.py` via
  `generate_matrix_report`, and its `living/races` row is family-level (columns: file path, schema
  class, repo index, validator coverage, resolver, compile/runtime consumer, test coverage,
  evidence tests, resolver evidence, runtime consumer evidence, implementation state, content
  maturity) — it does not enumerate individual `RaceDefinition` fields, and this ticket adds no new
  resolver/consumer wiring, so no row content changes. Do not hand-edit this generated file.
- `docs/brainstorm/rpg_expected_schemas.html` — confirmed (investigation.md) this is a
  forward-looking proposal atlas (schema-14 section, lines 676-680, already describes
  `RaceDefinition.intelligence_tier: enum: high | low`) that is never retroactively synced when a
  proposed field ships — verified by checking two other fields that shipped after being proposed in
  this same file family (`supports_adventure_routing`, `hazard_immunities`) and finding zero
  post-ship mentions of either in this file. No edit needed.
- No Mechanics Bible chapter (`docs/mechanics/01_entity_anatomy.md` through
  `06_worldbuilding_foundation.md`) references `RaceDefinition`, `natural_traits`, or species
  classification (investigation.md, grepped all six chapters, zero hits) — nothing to reconcile.

## Parity Ledger

**No parity ledger entry is needed.** Confirmed (investigation.md "Parity Ledger Overlap") — all 8
parity ledger files were searched for `race`/`RaceDefinition`/`intelligence_tier`; every hit found
is unrelated to species-intelligence classification (race-relations hostility escalation, terrain
race-label coverage, spawn-tier defaults, bravery/race correlation, a progression quest-target
note). No P0 entries are touched. This ticket adds an unconsumed schema/data field, not a behavior
change to any already-tracked mechanic, so there is nothing to update.

## Dependency Map

Step 1 gates everything else — no other step is meaningful until `intelligence_tier` exists on the
schema. Step 2 (fixture fix) depends only on Step 1 and is otherwise independent of Steps 3/4 — it
can and should land immediately after Step 1, before Step 3, since Step 1 alone (without Step 2)
leaves `tests/unit/content/test_layered_catalog.py` red, and that regression is real and
independently confirmed (see Step 2's Background). Steps 3 → 4 are sequential in practice (Step 3's
`races.yaml` authoring depends on Step 1's field existing for the catalog to accept the new key
without `extra="forbid"` rejecting it; Step 4's tests depend on Step 1 and Step 3). Each step is
independently verifiable once its predecessor lands — Step 1 alone can be verified by constructing
`RaceDefinition` instances directly in a scratch test before touching YAML or the fixtures; Step 2
alone can be verified by re-running `tests/unit/content/test_layered_catalog.py`; Step 3 alone can
be verified by re-running `test_base_catalog_loading` once the field exists. Full green state
requires all four steps landed: Step 1 alone (without Step 2) leaves the codebase in a regressed,
not-done state — Step 2 is not optional cleanup, it is required for the plan's own Step 1 change to
be safe to land.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `RaceDefinition` gains `intelligence_tier: enum(high|low)`, pydantic-validated | Step 1 | `test_race_definition_intelligence_tier_field_round_trips` |
| All 13 races get an explicit authored `intelligence_tier` derived from the `tool_user`-anchor, with dragonkin/spirit exceptions explicitly reviewed and justified | Step 3 (authoring) + this plan's "Dragonkin/Spirit Decision" section (justification, in-plan and to be copied into ticket's Implementation Notes at Finalize) | `test_all_13_races_have_documented_intelligence_tier` |
| A regression test asserts each of the 13 races' `intelligence_tier` matches the documented anchor rule with justified exceptions | Step 4 | `test_all_13_races_have_documented_intelligence_tier` |
| `settlement_capacity` (idea 44) is explicitly OUT of scope | N/A — Scope Guards + Out of Scope section (no step implements it) | Procedural (see test_plan.md Anti-Drift Test Guards — no automated test possible for a field that doesn't exist) |

Step 2 (fixture fix) has no dedicated AC of its own — it is not new functionality, it is the
correction required to keep Step 1's own AC-mapped change from regressing pre-existing, unrelated
tests. It is required for the plan to be landable, not for any AC's content.

## Anti-Drift Notes

- **Do not let the dragonkin/spirit review expand into re-tiering any of the other 11 races** — the
  6/13 clean `tool_user` races and the 5 clean non-`tool_user` races are independently confirmed
  correct against real data; there is no ambiguity there to "fix."
- **`natural_traits`/`compatible_roles` list ordering is a real regression surface** —
  `tests/unit/content/test_resolvers.py`'s ordering-sensitive tests (see Regression Surface in
  test_plan.md) will fail if Step 3's YAML edit accidentally reorders either list on any race while
  inserting the new `intelligence_tier` key. Insert the new key as a new line; do not
  reformat/reflow existing keys.
- **Step 1's required-no-default field has a real, empirically-confirmed blast radius beyond
  `races.yaml`** — any code path that constructs a `RaceDefinition` without going through the real
  `races.yaml` file must also supply `intelligence_tier`, or `CatalogRepository.load_all()`'s
  `try/except Exception: continue` (`src/content/repository.py:318-327`) silently drops that
  record rather than raising. Step 2 fixes the two known instances of this
  (`tests/unit/content/test_layered_catalog.py`'s `"broken_race"` and `"human"` fixtures) — if a
  future step or later ticket adds another synthetic `RaceDefinition`-shaped fixture anywhere in
  the test suite, it must also carry `intelligence_tier`, or it will silently vanish from
  `repo.races` rather than fail loudly.
- **`equipment_slots` and `intelligence_tier` are deliberately different axes** — do not conflate
  "lacks a tool equipment slot" with "low intelligence_tier" as a general rule going forward; for
  dragonkin/spirit specifically the cognition signal was judged to dominate (see Decision section),
  but this is a one-time judgment call for these two races' authored data, not a new general
  schema rule linking the two fields.
- **Zero consumers today is expected, not a gap** — do not add wiring, a stub predicate, or a
  helper function "in case idea 27 needs it." `TCK-20260831-ROLE-MODEL-IMITATION` is already
  correctly sequenced after this ticket and owns that work.
- **`extra="forbid"` fail-closed behavior on `CatalogBaseDefinition` (schema.py:10) must remain
  intact** — the new field must be declared on the model itself (Step 1), never smuggled through
  `metadata`/`extension`, or the real catalog load will fail closed once `intelligence_tier` is
  authored in YAML (Step 3) without the schema knowing about it. This is the correct design
  (`test_schema_fail_closed_unknown_field`) — preserve it, do not work around it.

## Open Questions

None remaining that block implementation. Both items flagged as open in investigation.md are
resolved by this plan:

1. **Dragonkin/spirit classification** — RESOLVED: both `"high"`, per the "Dragonkin/Spirit
   Decision" section above (cognition_profile=arcane_scholar as primary signal, weighed against
   equipment_slots/natural_traits counter-evidence and the field's stated downstream purpose in
   idea 27).
2. **Stub consumer/predicate** — RESOLVED: none added, per the "Stub Consumer Decision" section
   above (mirrors the `TCK-20260831-CLAN-STATE-SCHEMA` precedent).

Architecture-review does not need to wait on either of these; both are settled with cited evidence
above and ready for implementer to proceed.
