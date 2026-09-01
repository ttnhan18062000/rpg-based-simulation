---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260902-ENTITIES-DOC-REWRITE
artifact_type: plan
tags: [documentation]
---

# Implementation Plan — TCK-20260902-ENTITIES-DOC-REWRITE

## Summary
Rewrite `docs/core/entities.md` end to end, replacing the fictional "Aspect-Oriented Model"
(`Entity` shell class, 5 `Aspect` classes) with an accurate description of the real
`EntityState` composition (`src/core/state.py:723-961`) — its `id`/`kind` atom, its 16 real
components including the two currently undocumented in any sibling doc (`self_model`,
`cognition`), and real construction via `EntityGenerator`/`V2EntityBuilder`. The rewrite keeps
entities.md distinct from `docs/core/state.md` rather than duplicating it: entities.md becomes
the entity-identity/lifecycle/composition-roster doc (what an entity is, how it's created, what
components it's made of, factions, and how aptitudes really affect growth), while cross-linking
to `state.md` for the Frozen Lifecycle Law / apply-path mutation-timing mechanics and canonical
serialization details it already documents accurately — avoiding re-describing (and risking
re-diverging from) content that already has a correct, authoritative home. Every component name,
field, and enum value in the rewrite is grounded in a specific `file:line` citation gathered
during planning (verified directly against `src/core/state.py`, `src/core/enums.py`,
`src/core/self_model.py`, `src/core/cognition.py`, `src/core/strategic.py`,
`src/systems/world_systems/generator.py`, `src/core/builder.py`, and
`docs/core/attributes_and_classes.md`), not inferred from the old doc's plausible-sounding prose.

## Decisions (resolving the 4 required items)

**1. Include `self_model` and `cognition` — yes.**
Both are real, composed `EntityState` fields (`src/core/state.py:747-748`:
`self_model: SelfModelBundle = field(default_factory=SelfModelBundle)`,
`cognition: CognitionModel = field(default_factory=CognitionModel)`; imports at
`state.py:19-20` from `src/core/self_model.py` and `src/core/cognition.py`). Excluding them would
repeat the exact failure class this ticket exists to fix — a doc that omits real composed state.
`SelfModelBundle` (`src/core/self_model.py:212-244`) bundles `self_awareness`, `needs`,
`capabilities`, `knowledge` (4 sub-components, each `@dataclass(frozen=True, slots=True)`, e.g.
`SelfAwarenessComponent` at `self_model.py:79`). `CognitionModel`
(`src/core/cognition.py:549-570`) bundles `subjective`, `memory`, `motivation`, `commitment`,
`relationships`, `role_model`. Both participate in `EntityState.to_canonical_dict()`
(`state.py:807-808`: `"self_model": self.self_model.to_canonical_dict()`, `"cognition":
self.cognition.to_canonical_dict()`), so they are canonically hashed, not debug-only —
confirming they are durable entity state, not scratch data.

**2. entities.md shape — (b), narrowed but not maximal: full component roster stays, mutation-timing mechanics gets cross-linked, not re-described.**
The repo's established convention for two docs covering adjacent ground is a short "See
`docs/X.md` §N for..." cross-link rather than duplicating detailed mechanics prose in both places
(examples confirmed by grep: `docs/engine/kernel.md:150-151` → `known_limitations.md` /
`deterministic_execution.md`; `docs/simulation/domains/campaigns_contract.md:110` →
`campaign_orchestrator_contract.md`; `docs/testing/how_to_add_requirement_tests.md:33` →
`regression_policy.md`). Applying that convention here: `docs/core/state.md` already accurately
owns the "Frozen Lifecycle" Law (snapshot → deliberation → refinement → transition via
`AuthoritativeState.apply()`), the Component Composition Pattern's dependency map, the
`to_canonical_dict()` serialization protocol, and Regional State — none of that should be
re-described in entities.md (the investigation independently flagged this: no `next_act_at`
field, `WorkerPacket` class, or "Generation-Based Apply"/"Phase-Locked Mutation"/"Shallow
Packetization" terminology was found anywhere in source; these were fictional embellishments on
top of the real, already-documented apply-path). However, the ticket's own Acceptance Criteria
require every claimed component name/field to be verifiable **in `entities.md`'s own text**
("Every component name and field the rewritten doc claims exists is verifiable by name in
`src/core/state.py`..."), so entities.md cannot be reduced to a stub that just links to
`state.md` — it must still carry its own complete component roster. Final shape: entities.md
keeps a full 16-row component table (one row per real component, responsibility + key fields,
matching `state.md`'s existing 8-row table's density but complete rather than abbreviated), plus
entity-identity content unique to this doc (what `EntityState` is, `id`/`kind`, real construction
path, Faction/EntityRole enums, real aptitude-growth mechanism) — and a single cross-link sentence
pointing to `state.md`'s "Frozen Lifecycle" Law section instead of re-explaining mutation timing.

**3. Genetic Seeds section — delete the `deterministic_seed`/0.8x-1.2x claim, replace with the
real mechanism.**
No `deterministic_seed` field exists anywhere (`grep -rn "deterministic_seed" src/` → zero
matches, independently re-confirmed). No randomization/seed-assignment logic exists in
`EntityGenerator` (`src/systems/world_systems/generator.py` — independently re-confirmed via
`grep -n "apt" src/systems/world_systems/generator.py` → zero matches) or `V2EntityBuilder`
(`src/core/builder.py`). `AptitudeComponent` (`src/core/state.py:529-561`) is real — its own
docstring says "Genetic multipliers for stat growth (Pillar 2)" (`state.py:530`) — and holds 9
per-stat float multipliers (`str_apt`, `agi_apt`, `vit_apt`, `end_apt`, `int_apt`, `spi_apt`,
`wis_apt`, `per_apt`, `cha_apt`) plus `learning_rate`/`stamina_efficiency`, **all defaulting to
`1.0`** — i.e. "genetic" is real vocabulary in the source, but the specific seed-driven
0.8x-1.2x-at-creation mechanism is not. The rewrite must replace it with the real mechanism per
`docs/core/attributes_and_classes.md` §3.5 "Attribute Decay & Aptitudes" (line 115-123): an
Aptitude gives `2.0x` training rate and `+2` level-up gain for a favored attribute, and per §3
"Level-Up Attribute Gains" (line 109-113): `level_up_attributes()` applies +2 per attribute,
modified by Aptitudes, capped. Per `docs/parity_ledger/progression.yaml::PROG-069` (P0,
divergent), the rewrite must NOT claim aptitudes affect attribute-point (AP) allocation gains —
that path (`execute_allocate_ap`, `src/engine/domain/core_actions.py`) applies a flat delta with
no aptitude lookup (dead code that once did this was deleted per `DEV-004`). Cite
`level_up_attributes()` / `docs/core/attributes_and_classes.md` §3 and §3.5 exclusively.

**4. Factions & Relations table — confirmed inaccurate; replace with the real 4-value enum.**
Read directly: `src/core/enums.py:24-28` — `class Faction(IntEnum): HERO_GUILD = 0,
MONSTER_HORDE = 1, TOWN_COUNCIL = 2, NEUTRAL = 3`. Only `HERO_GUILD` overlaps with the old doc's
table; `GOBLIN_HORDE`, `WOLF_PACK`, `UNDEAD`, `ORC_TRIBE` do not exist. The rewrite must replace
the table with these 4 real values. Bonus finding while verifying this (same file, adjacent):
`entities.md`'s `IdentityAspect.role` claim ("`HERO`, `MOB`, `BOSS`, or `NPC`") is also wrong —
the real `EntityRole` enum (`src/core/enums.py:6-12`) is `HERO = 0, SHOPKEEPER = 1, MONSTER = 2,
CITIZEN = 3, WORKER = 4, GUARD = 5`. Per the ticket's own Scope language ("if investigation finds
these sections are also inaccurate, that inaccuracy should still be fixed under this ticket's
scope... same file, same root cause"), this is in-scope and folded into Step 3 (Identity
component row) below rather than deferred.

## Steps

### Step 1 — Replace the title, intro, and "Entity Shell" section with the real EntityState atom
**Files:** `docs/core/entities.md`
**Change:** Replace the `# Entities & Factions: The Aspect-Oriented Model` title (line 9) with
`# Entities & Factions: The Component-Based Model` (matching `state.md`'s real terminology, not
inventing a new architecture name — Anti-Drift Hazard from investigation.md). Replace the intro
paragraph (line 11, which claims "Resource-Safe Engine" / discrete "Aspects") and the entire
"1. The Entity Shell" section (lines 15-27, the fictional `Entity` class at
`src/core/entities/entity.py` and its "Authoritative Execution Laws") with: a short paragraph
stating `EntityState` (`src/core/state.py:723-961`, `@dataclass(frozen=True, slots=True)`) is the
real authoritative entity atom — no `Entity` shell class exists, confirmed via `src/core/`
directory listing (no `src/core/entities/` path). Keep a "Core Properties" subsection for `id:
int` and `kind: str` (both real top-level `EntityState` fields, `state.py:725-726`) — drop the
fictional `next_act_at` field entirely (investigation confirms: not found anywhere in
`EntityState` or `AuthoritativeState`; the real analogs are `TaskComponent.work_kind`/`payload`
and kernel-level scheduling state, not an entity-level field — do not invent a replacement field
name for it, just omit it). Replace the 3 fictional "Authoritative Execution Laws" (Generation-
Based Apply / Phase-Locked Mutation / Shallow Packetization — none independently verified to
exist under those names) with one short paragraph plus a cross-link: "All `EntityState` mutation
flows through the same frozen-state apply path described in `docs/core/state.md`'s 'Frozen
Lifecycle' Law — see that doc for the snapshot → deliberation → refinement → transition
sequence." Do not re-describe the sequence itself here.
**Do NOT touch:** `docs/core/state.md`'s own "Frozen Lifecycle" Law section — link to it, don't
copy it.
**Verify:** `grep -c 'src/core/entities/entity\.py\|next_act_at\|Generation-Based Apply\|Phase-Locked Mutation\|Shallow Packetization\|WorkerPacket' docs/core/entities.md` returns `0`.

### Step 2 — Replace "2. Aspect Decomposition" with a full 16-row Component roster table
**Files:** `docs/core/entities.md`
**Change:** Delete the entire "2. Aspect Decomposition" section (lines 31-60: `IdentityAspect`,
`SpatialAspect`, `CombatAspect`, `ProgressionAspect`, `MindAspect`). Replace with a "2. Component
Composition" section containing one table, one row per real `EntityState` component field, in the
same declaration order as `state.py:731-748` (interaction, identity, attributes, inventory,
strategic, social, biological, lifecycle, aptitude, combat, equipment, navigation, task, stamina,
self_model, cognition — 16 rows, independently confirmed by reading the `EntityState` dataclass
field list directly). Columns: Component | Defined In | Key Fields (short, non-exhaustive —
follow `state.md`'s existing table density, not a full field dump):
- `interaction: InteractionComponent` — `state.py:402` — `target_node_id`, `progress`,
  `start_tick`, `kind` (harvest/ground_item/corpse/chest/guild/inn/tavern)
- `identity: IdentityComponent` — `state.py:484` — see Step 3 (own sub-section, corrects the
  `role`/`faction` enum claims)
- `attributes: AttributeComponent` — `state.py:452` — 9 primary stat ints; cross-link to
  `docs/core/attributes_and_classes.md`'s attribute table rather than repeating it
- `inventory: InventoryComponent` — `src/core/models/inventory.py` (imported `state.py:16`, not
  defined inline — call this out explicitly, per investigation's flagged risk)
- `strategic: StrategicComponent` — `src/core/strategic.py:383` — `home_region_id`, `blockers`,
  `leads`, `directives`, `projects`, `concerns`, `beliefs`, `profile` (`CognitionProfile`)
- `social: SocialComponent` — `src/core/models/social.py` (imported `state.py:17`, not defined
  inline)
- `biological: BiologicalComponent` — `state.py:125` — `sleep_debt`, `hunger`, `rest_pressure`
- `lifecycle: LifecycleComponent` — `state.py:152` — `age_ticks`, `max_age_ticks`,
  `is_permadeath`, `generation`, `heirlooms`
- `aptitude: AptitudeComponent` — `state.py:529` — see Step 4 (own sub-section, corrects the
  Genetic Seeds claim)
- `combat: CombatComponent` — `state.py:306` — `hp`, `max_hp`, `atk`, `def_stat`, `speed`,
  `wounds`, `scars`, `status_effects` (the one field the old doc got right by coincidence)
- `equipment: EquipmentComponent` — `state.py:707` — `slots`, `durability`
- `navigation: NavigationComponent` — `state.py:369` — `position`, `target`, `path`,
  `movement_mode`, leash/congestion-recovery fields
- `task: TaskComponent` — `state.py:395` — `work_kind`, `payload`
- `stamina: StaminaComponent` — `state.py:57` — `current`, `max_stamina`, `regen_rate`
- `self_model: SelfModelBundle` — `src/core/self_model.py:212` (imported `state.py:19`) —
  `self_awareness`, `needs`, `capabilities`, `knowledge`
- `cognition: CognitionModel` — `src/core/cognition.py:549` (imported `state.py:20`) —
  `subjective`, `memory`, `motivation`, `commitment`, `relationships`, `role_model`
**Do NOT touch:** `docs/core/state.md`'s own 8-row summary table — entities.md's table is a
distinct, complete 16-row version; do not edit the abbreviated one in state.md to match.
**Verify:** `grep -c 'IdentityAspect\|SpatialAspect\|CombatAspect\|ProgressionAspect\|MindAspect' docs/core/entities.md` returns `0`; manually cross-check all 16 component names + cited fields
against the `file:line` citations above (this is the AC's "spot-checked" requirement).

### Step 3 — Correct the Identity component's role/faction enum claims within the new roster
**Files:** `docs/core/entities.md`
**Change:** Within the `identity: IdentityComponent` row/sub-section added in Step 2, describe
`role` and `faction` using the real enum values, not the old doc's fictional ones. Real
`EntityRole` (`src/core/enums.py:6-12`): `HERO`, `SHOPKEEPER`, `MONSTER`, `CITIZEN`, `WORKER`,
`GUARD` — replaces the old doc's wrong "`HERO`, `MOB`, `BOSS`, or `NPC`" (entities.md line 36).
Real `Faction` (`src/core/enums.py:24-28`): `HERO_GUILD`, `MONSTER_HORDE`, `TOWN_COUNCIL`,
`NEUTRAL` — this also supersedes the old "3. Factions & Relations" section (see Step 5). Also
list `IdentityComponent`'s other real fields not previously documented anywhere in either sibling
doc: `known_recipes`, `craft_target`, `evolution_level`/`evolution_points`,
`veterancy_points`/`veterancy_rank`, `unspent_ap`, `class_id`, `learned_skills`, `traits`,
`active_breakthroughs`, `cooldowns`, `personality` (nested `PersonalityComponent`, `state.py:430`
— `greed`, `bravery`, `sociability`, `industry`), `life_stage`, `group_id` (all confirmed by
direct read of `IdentityComponent`, `state.py:484-509`).
**Do NOT touch:** `docs/core/attributes_and_classes.md` — do not duplicate its class/attribute
tables; cross-link for `class_id`/attribute detail instead.
**Verify:** `grep -n 'MOB\|BOSS\|"HERO", "MOB"' docs/core/entities.md` returns no matches in the
role-description context; the doc's `EntityRole` list reads `HERO, SHOPKEEPER, MONSTER, CITIZEN,
WORKER, GUARD`.

### Step 4 — Rewrite "4. Genetic Seeds" as an accurate Aptitude section
**Files:** `docs/core/entities.md`
**Change:** Delete the entire "4. Genetic Seeds" section (lines 75-77: `deterministic_seed`
field, "generates the unique Aptitude pool"). Also delete the ProgressionAspect's inline claim at
old line 53 ("Genetic multipliers (0.8x - 1.2x)... radically different builds") — both already
removed as part of Step 2's section replacement, but explicitly re-check here since this is the
section the ticket's Assumptions flagged as needing resolution. Replace with a short "Aptitudes"
sub-section under the `aptitude: AptitudeComponent` roster row: `AptitudeComponent`
(`state.py:529-561`) holds 9 per-stat multipliers (`str_apt`...`cha_apt`) plus
`learning_rate`/`stamina_efficiency`, **all defaulting to `1.0`** — there is no seed-driven
randomization at entity creation (`grep -rn "deterministic_seed" src/` → zero matches;
`EntityGenerator`/`V2EntityBuilder` assign no aptitude randomization). State the real mechanism
instead, citing `docs/core/attributes_and_classes.md` §3 "Level-Up Attribute Gains" (line
109-113: `level_up_attributes()` grants +2 per attribute, modified by Aptitudes, capped) and §3.5
"Attribute Decay & Aptitudes" (line 115-123: a favored Aptitude gives `2.0x` training rate and
`+2` level-up gain). Explicitly state aptitudes do **not** affect attribute-point (AP) allocation
— cite `docs/parity_ledger/progression.yaml::PROG-069` (P0, divergent: `execute_allocate_ap`
applies a flat delta, no aptitude lookup; the code that once did this was dead code deleted per
`DEV-004`) as the reason not to claim otherwise.
**Do NOT touch:** `docs/parity_ledger/progression.yaml` itself (Out of Scope per ticket) — cite
`PROG-069`, do not edit it. Do NOT touch `docs/core/attributes_and_classes.md` — cross-link to
its §3/§3.5, do not copy its tables in.
**Verify:** `grep -c 'deterministic_seed\|0.8x\|0.8 - 1.2\|radically different builds' docs/core/entities.md` returns `0`; the doc states aptitude defaults are `1.0` and cites
`level_up_attributes()`/§3.5, not AP allocation.

### Step 5 — Replace "3. Factions & Relations" with the real 4-value Faction table
**Files:** `docs/core/entities.md`
**Change:** Replace the "3. Factions & Relations" table (lines 64-71: `HERO_GUILD`,
`GOBLIN_HORDE`, `WOLF_PACK`, `UNDEAD`, `ORC_TRIBE`) with the real `Faction` enum
(`src/core/enums.py:24-28`): `HERO_GUILD = 0`, `MONSTER_HORDE = 1`, `TOWN_COUNCIL = 2`,
`NEUTRAL = 3`. Drop the per-faction behavioral prose from the old table (e.g. "Hostile to all
life") since no corresponding behavioral-rule source was verified in this investigation or
planning pass for the 3 non-`HERO_GUILD` factions — state only the enum values as confirmed fact,
and note (one sentence, not a new claim) that `DiplomaticState`
(`src/core/enums.py:14-21`: `NEUTRAL`, `TENSE`, `HOSTILE`, `WAR`, `ALLIED`, `VASSAL`) is the real
typed relationship state between factions, imported alongside `Faction` at `state.py:12`, if a
one-line mention is useful for context — do not invent behavioral rules for it beyond naming its
existence, since sourcing per-value diplomatic behavior is out of this step's verified scope.
**Do NOT touch:** anything about `IdentityComponent.faction`'s field type/location — already
covered in Step 3; this step only fixes the enum's *value list*.
**Verify:** `grep -c 'GOBLIN_HORDE\|WOLF_PACK\|UNDEAD\|ORC_TRIBE' docs/core/entities.md` returns
`0`; the doc's Faction list reads `HERO_GUILD, MONSTER_HORDE, TOWN_COUNCIL, NEUTRAL`.

### Step 6 — Add real entity construction (EntityGenerator / V2EntityBuilder), preserving the accurate "monotonic id" substance
**Files:** `docs/core/entities.md`
**Change:** Add a new short section (e.g. "5. Entity Construction," after the roster/factions
content) describing the real spawn path, since this content did not exist at all in the old doc
under an accurate name and is a natural fit for an entity-identity-focused doc per Decision 2
above: `EntityGenerator.get_next_id()` (`src/systems/world_systems/generator.py:30-32`) is a
simple monotonic counter (`self._last_id += 1`) — this is the real source of the "unique,
monotonic integer id" substance the old doc's Core Properties claimed under the fictional `Entity`
shell; reattribute it here instead of dropping it, since the substance is accurate. Entities are
built via `V2EntityBuilder` (`src/core/builder.py:88-107`), which instantiates all 16 components
listed in Step 2's roster. `AuthoritativeState.__post_init__` (`state.py:1218-1263`) additionally
guards `next_entity_id` against collisions with pre-existing integer entity keys. Keep this
section short — it is not a full builder-API reference, just enough to state where ids and
components come from.
**Do NOT touch:** `src/core/builder.py`, `src/systems/world_systems/generator.py`, or any other
`src/` file — read-only references.
**Verify:** the doc names `EntityGenerator.get_next_id()` and `V2EntityBuilder` with correct file
paths; no fictional construction path (`Entity` shell) remains anywhere in the file.

### Step 7 — Update frontmatter and do a final whole-file sweep for the AC's forbidden strings
**Files:** `docs/core/entities.md`
**Change:** Keep the existing frontmatter shape exactly (`status: authoritative`, `layer: core`,
`authority: P0`, `audience: developer`) — only update `last_verified` (currently `2026-06-06`) to
this ticket's close date. Do not add a `content_type` field (none present today;
`tools/validate_frontmatter.py`'s `detect_content_type()` infers `doc` from the `docs/` path
correctly without one — do not override it). After Steps 1-6 are complete, run one final
whole-file check for every forbidden string from AC #1 in a single pass, since earlier steps
checked their own sections individually but a final sweep catches any stray reference missed
across section boundaries (e.g. in a cross-reference sentence written during a later step that
mentions an earlier, now-deleted term).
**Do NOT touch:** `status`, `layer`, `authority`, or `audience` frontmatter fields — only
`last_verified` changes.
**Verify:** `grep -c 'Aspect\|src/core/entities/entity\.py\|IdentityAspect\|SpatialAspect\|CombatAspect\|ProgressionAspect\|MindAspect' docs/core/entities.md` returns `0` (AC #1, exact);
`python3 tools/validate_frontmatter.py docs/core/entities.md` passes (AC #4); `git diff --stat`
shows only `docs/core/entities.md` changed at this point (AC #6, pre-Finalize).

### Step 8 — Run the docs test suite and knowledge-index update
**Files:** none (verification/tooling step, no further file edits expected)
**Change:** Run `pytest tests/docs/ -m "not slow"` per test_plan.md's Scoped Pytest Commands (the
two specifically-checked tests, `test_doc_integrity.py` and `test_doc_path_existence.py`, are
confirmed not to touch `docs/core/entities.md`, but the full `tests/docs/` suite is run anyway per
test_plan.md's own reasoning: a docs-content change is exactly the class of edit that suite
exists to guard, even for files outside its two named tests' direct scope). Then run
`make knowledge-index-update` per project CLAUDE.md's "docs/ modified" rule (AC #5) and confirm it
completes without error.
**Do NOT touch:** do not run `pytest tests/` (whole suite) — out of scope per test_plan.md's
explicit narrowing.
**Verify:** `pytest tests/docs/ -m "not slow"` exits 0; `make knowledge-index-update` exits 0.

## Scope Guards
- Do not modify `docs/core/state.md` under any circumstance, including "improving" it while
  cross-referencing — it is explicitly Out of Scope and already accurate.
- Do not modify `docs/core/attributes_and_classes.md` — cross-link to it (§3, §3.5), never edit
  or duplicate its tables inline.
- Do not modify any file under `src/` — this is documentation-only; every `src/` file referenced
  above (`state.py`, `enums.py`, `self_model.py`, `cognition.py`, `strategic.py`, `builder.py`,
  `generator.py`) is read-only ground truth.
- Do not modify `docs/parity_ledger/progression.yaml` (or any other parity ledger file) — cite
  `PROG-069`, do not edit its status/evidence.
- Do not re-litigate or restore the historical Aspect-Oriented Architecture (AOA) — document
  current reality only, not architecture history (that history is already captured in the
  ticket's Related Tickets section, not in the doc itself).
- Do not invent a new plausible-sounding but unverified architecture name or mechanism (the exact
  failure mode that created this ticket) — every claim in the rewrite must trace to a `file:line`
  citation gathered in this plan or independently re-verified during implementation.
- Do not change `status`, `layer`, `authority`, or `audience` in entities.md's frontmatter — only
  `last_verified`.
- Do not add automated pytest coverage for the string-absence checks — test_plan.md explicitly
  rules this out as low-value scaffolding; use the manual `grep -c` verifications specified per
  step instead.

## Dependency Map
Steps 1-6 each touch a distinct, non-overlapping section of `docs/core/entities.md` and can be
done in any relative order, but are listed in the doc's natural top-to-bottom reading order for
implementer convenience (Step 3 and Step 4 are sub-steps that land inside the roster table Step 2
creates, so Step 2 must land first; Step 5 is independent of 1-4 but conventionally follows the
roster). Step 7 (frontmatter + final sweep) depends on Steps 1-6 all being complete, since its
whole-file grep check is only meaningful once every section has been rewritten. Step 8
(tests + knowledge-index) depends on Step 7's frontmatter fix being in place (frontmatter
validity is part of what `tests/docs/` may indirectly exercise, and `last_verified` must already
be current before treating the doc as finished).

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Zero occurrences of `Aspect`/`src/core/entities/entity.py`/`IdentityAspect`/`SpatialAspect`/`CombatAspect`/`ProgressionAspect`/`MindAspect` | Steps 1, 2, 7 | `grep -c` sweep in Step 7 |
| Every claimed component name/field verifiable in `src/core/state.py` or `src/core/strategic.py` (spot-check list: Identity, Combat, Navigation, Interaction, Biological, Attribute, Personality, Aptitude, Equipment, Lifecycle, Strategic) | Step 2 (roster table), Step 3 (Identity detail), Step 4 (Aptitude detail) | Manual cross-check against `file:line` citations in Steps 2-4; `pytest tests/docs/` in Step 8 |
| Framing matches `docs/core/state.md`'s Component Composition Pattern / Frozen Lifecycle Law (no contradiction between sibling docs) | Step 1 (cross-link, no re-description), Step 2 (component terminology aligned) | Manual read-through; no independent test exists for this (test_plan.md confirms no content-level test covers this doc) |
| `python3 tools/validate_frontmatter.py` passes | Step 7 | Direct invocation in Step 7 and Step 8 |
| `make knowledge-index-update` runs without error | Step 8 | Direct invocation in Step 8 |
| No `src/` files modified | All steps (scope guard) | `git diff --stat` check in Step 7; final `git status` before Finalize |

## Anti-Drift Notes
- The Genetic Seeds correction (Step 4) is the highest-risk step for reintroducing a
  plausible-but-unverified claim, since "genetic" language is partially real
  (`AptitudeComponent`'s own docstring says "Genetic multipliers") — do not let that partial
  truth justify restoring the seed/randomization-range specifics, which are independently
  confirmed absent from source.
- Do not describe `AptitudeComponent` as affecting attribute-point (AP) allocation gains
  anywhere in the rewrite (Step 4) — `PROG-069` (P0) is explicit that this path is flat/unmodified
  on the live code path; only `level_up_attributes()` is the verified aptitude-affected mechanism.
- The Faction/EntityRole corrections (Steps 3, 5) replace enum value lists wholesale — do not
  merge old fictional values with new real ones (e.g. do not keep `GOBLIN_HORDE` "for
  flavor" alongside the real 4 values); the old values do not exist in `src/core/enums.py` at all.
- Step 1's cross-link to `state.md`'s Frozen Lifecycle Law must not re-describe that sequence in
  entities.md's own words — even an accurate paraphrase risks drifting from `state.md` over time
  if only one of the two docs gets updated on a future change. One sentence + a link, per the
  repo's established cross-doc convention (see Decision 2's citations).
- If, during implementation, any additional field/enum claim carried forward from the old doc
  (beyond the 4 items this plan already resolved) turns out to be unverifiable against source,
  treat it the same way Genetic Seeds and Factions were treated here: do not preserve it on the
  assumption it's "probably fine" — verify with a `file:line` citation or drop it, per the
  ticket's own Scope language that in-file inaccuracies found anywhere are in-scope to fix.

## Unresolved Questions
None. All four items flagged by the ticket and investigation.md (self_model/cognition inclusion,
entities.md-vs-state.md shape, Genetic Seeds correction, Factions & Relations accuracy) are
resolved above with source citations independently verified during planning.

## Deviations

Two minor, non-substantive departures from this plan occurred during implementation, both
recorded here per the project's "never silently deviate" rule. Neither changes any of this plan's
Decisions, Steps, or Scope Guards.

1. **Step 3's Identity field list was extended by 3 real fields.** The plan's Step 3 names a
   specific field list to document (`known_recipes`, `craft_target`, `evolution_level/points`,
   `veterancy_points/rank`, `unspent_ap`, `class_id`, `learned_skills`, `traits`,
   `active_breakthroughs`, `cooldowns`, `personality`, `life_stage`, `group_id`). While
   independently re-reading `IdentityComponent` (`src/core/state.py:483-527`) during
   implementation, three more real fields were confirmed present but not named in that list:
   `territory_maturity`, `properties` (free-form dict), and `latest_intent_results`. The
   implementer added a one-line mention of these three at the end of the Identity sub-section
   rather than omitting them, since silently dropping real, verified fields would reproduce the
   same "coincidentally incomplete doc" failure mode this ticket exists to fix. This is additive
   only — it does not contradict or remove anything the plan specified.

2. **Step 7's self-correction: one literal "Aspect" occurrence in the implementer's own drafted
   prose.** The plan's Step 1 change text used the word "Aspects" once in its own description
   ("its 'Aspects'") when explaining what to delete, but did not flag that the *rewritten doc's
   own new prose* could accidentally reintroduce the literal string "Aspect" in a negating
   sentence (e.g., explaining that `EntityState` is "not a shell class wrapping separate 'Aspect'
   objects"). The implementer's first draft did exactly this in the Section 1 intro paragraph.
   The Step 7 whole-file grep sweep caught it (count was `1`, not `0`), and the sentence was
   rewritten to avoid the word "Aspect" entirely ("not a shell class wrapping separate
   sub-objects") before the sweep was re-run and confirmed clean. This is exactly the sweep
   behaving as designed — flagged here only because the plan's Anti-Drift Notes are specifically
   about not reintroducing fictional claims, and a near-miss on the AC's own forbidden-string
   check is worth a one-line record for future implementers of similar doc-rewrite tickets: even
   a negating or explanatory use of a forbidden term will fail a literal `grep -c` gate.
