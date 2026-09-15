---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260915-MECHANISM-REGISTRY-FOUNDATION
artifact_type: investigation
tags: [architecture, documentation, schema]
---

# Investigation — TCK-20260915-MECHANISM-REGISTRY-FOUNDATION

## Current Behavior

There is no mechanism registry today. Five artifacts each record a mechanism's build state
independently, confirmed directly against `origin/main` during this investigation (not just cited
from the plan doc):

- `docs/brainstorm/rpg_feature_atlas.html` — a `<script type="application/json" id="card-sections-data">`
  block at line 1127 (`rpg_feature_atlas.html:1127`) holding 14 sections, 139 cards total. Each card
  has `title`, `badges: [{cls, text}]`, `fromNote`, `desc`, `src`. `cls` is drawn cleanly from exactly
  six values across every non-`design-ideas` card checked in this pass: `done` (38), `partial` (13),
  `gap` (11), `orphan` (9), `gated` (5), `skeleton` (2) — confirming Finding 1's claim that the atlas
  already speaks the target six-class vocabulary natively, no seventh class needed.
- `docs/brainstorm/rpg_simulation_wiring_map.html` (695 lines) — three mermaid flowcharts (Layer
  Model at line 275, Entity Operating Loop at line 447, Entity Lifecycle Arc at line 606) using a
  *different*, four-value badge vocabulary (`live` / `bug` / `gated` / `proposed`, legend at line
  262) plus a 21-row lifecycle transition table (T1–T20, line 660).
- `tools/generate_brainstorm_idea_index.py` → `docs/brainstorm/idea_index.json` — the existing
  generated sibling-index precedent, keyed by **design idea** (1–68), not by mechanism (Finding 2).
- `src/engine/capability.py` + `docs/engine/capability_registry.yaml` — a working hand-authored
  YAML-registry + reader + validator-test precedent for a *different* subject (engine capabilities,
  not mechanisms), but the closest structural match in the repo: a `VALID_STATUSES` frozenset
  (`capability.py:10`), a `CapabilityRegistry` reader class loading the YAML once
  (`capability.py:14-53`), and `tests/unit/engine/test_capability_registry.py` asserting YAML
  validity, required fields, and valid statuses via `pytest.mark.parametrize`.

No `mechanisms.yaml` exists yet; no validator exists yet; no `make` target exists yet.

## Mechanics / Engine Constraints

This ticket does not implement or change any simulation mechanic — it builds a tracking artifact
about mechanics. No `docs/mechanics/` chapter or `docs/engine/` contract constrains its *shape*. The
one constraint that does apply: per CLAUDE.md's Authoritative Mechanics Rule, the registry's `state`
values must not silently contradict a Mechanics Bible chapter or parity-ledger `status` for the same
mechanism — this is a soft consistency expectation, not a hard invariant the validator can check
(the validator's four invariants are schema-internal: `depends_on` resolution, DAG acyclicity, layer
declaration, six-class `state` enum — none of them cross-reference `docs/mechanics/` or
`docs/parity_ledger/`). Cross-referencing against the Bible/ledger is not in this ticket's scope
(Out of Scope explicitly excludes the `verified` block, child 2) and is not attempted here.

## Docs Requiring Update

- `docs/brainstorm/rpg_feature_atlas.html`: two of its badge/citation texts are confirmed stale
  against the current codebase, found during this investigation, and both would be seeded into the
  new registry as *wrong* data if not corrected first. (1) The "XP, Attribute Points, Breakthrough &
  Mastery" card (`entity-profile` section, card index 10) badges Breakthrough as `gap`
  ("Breakthrough is a no-op"), citing `apply_bonuses()` as a stub — but
  `src/progression/breakthroughs.py:36-58` (`BreakthroughService.apply_bonuses`) is a real,
  non-stub implementation, called in production from `src/engine/rpg_depth.py:367`, and covered by
  both `tests/unit/progression/test_breakthroughs.py` (5 tests) and
  `tests/unit/core/test_rpg_depth.py:514` ("active_breakthroughs reaches apply_bonuses and surfaces
  in derived atk"). This mechanism is `done`, not `gap`. (2) The "Race-Keyed Evolution Chains" card
  (`entity-profile` section, card index 8) badges a second path `orphan`, citing
  `progression/evolution.py: EvolutionService (orphaned, goblin-only, redundant)` — but that file
  was deleted in full by `tickets/done/TCK-20260824-WIRE-ORPHANED-MECHANISMS.md` (Step 2, confirmed
  by `test -f src/progression/evolution.py` returning false in this session), so there is now only
  one live path (`src/engine/evolution.py: EvolutionSystem`), not two. This mechanism is cleanly
  `done`, no duplicate caveat.
- `docs/brainstorm/rpg_simulation_wiring_map.html`: the same Breakthrough staleness appears in its
  own Buildup table (line 573, "literal `pass`") and its Operating Loop flowchart (`BRK` node styled
  `:::bug` at line 491, "`apply_bonuses()` is a literal stub"). Both need the same correction as the
  atlas card above, from the same evidence (`breakthroughs.py:36-58`, `rpg_depth.py:367`).

The `docs/plans/mechanism_registry_initiative.md` design doc (path:
`docs/plans/mechanism_registry_initiative.md`) is not required to change for this ticket: it is
already the accepted design and its own "Open questions for implementation" section explicitly
anticipates this investigation resolving question 3 (file location) and question 4 (atlas mapping
cleanliness) without itself needing an edit — this investigation's findings settle those questions
in prose here, not by rewriting the plan.

No `docs/parity_ledger/*.yaml` entry needs a new or updated `status` for this ticket: the registry
adds a build/tracking artifact, not a logic or mechanics change, so there is nothing for the parity
ledger's `v2_evidence`/`status` fields to describe yet. (A future ticket cross-checking each
mechanism's `state` against its parity-ledger entry, if one is ever scoped, would be new work, not
implied by this Foundation ticket.)

## Parity Ledger Overlap

None directly touched by this ticket (see above — no logic change). Loosely, several seeded
mechanism ids will eventually correspond to parity-ledger entries with real `P0` status (e.g.
`combat_resolution` ↔ `COMB-290` in `combat_movement.yaml`, cited directly in the atlas's own
Combat Resolution card and in wiring-map T6). That correspondence is not built by this ticket — no
`P0` entry's `test_path` is read, written, or required to pass here.

## Prior Work

- `tickets/done/TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX.md` +
  `stored_artifacts/TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX/plan.md` — the generated-index
  precedent this ticket's own Related Tickets section cites; confirmed its script
  (`tools/generate_brainstorm_idea_index.py`) raises `SystemExit` rather than writing a dangling
  reference (the same "build the failure loud" instinct this ticket's Implementation Notes calls
  for), and that it has **no dedicated test file** (`find tests -iname "*idea_index*"` returned
  nothing) — its correctness is enforced entirely by the generator's own internal assertions at
  generation time, not by a separate pytest suite. This is a **location and generation-pattern**
  precedent only, not a validator-shape precedent, exactly as the task briefing anticipated: the
  idea index is machine-*generated*, the mechanism registry is meant to be hand-*authored* and
  separately validated.
- `tests/unit/engine/test_capability_registry.py` + `src/engine/capability.py` — the closer
  validator-shape precedent (confirmed via `graphify query "registry()"`, 22-node BFS): a frozenset
  of valid enum values, a reader class with `__init__` loading YAML once via `yaml.safe_load`, and a
  parametrized test file covering YAML-exists, YAML-parses, required-fields-present,
  valid-statuses-only, and reader behavior (`is_supported`/`get_status`/`unknown_id` cases). This is
  the pattern to imitate for the mechanism registry's own reader/validator, adapted for the extra
  two invariants (`depends_on` resolution, DAG acyclicity) this registry needs that capability.py's
  simpler flat list did not.
- `tickets/done/TCK-20260824-WIRE-ORPHANED-MECHANISMS.md` — directly relevant prior investigation of
  several of the same mechanisms seeded below (Evolution, Emotion, elder attribute modifiers,
  consequence events). Cross-referencing it is what surfaced the Breakthrough/Evolution atlas
  staleness above. It also surfaced a live discrepancy worth flagging rather than silently resolving
  (see Risks below): that ticket wired `EmotionUpdateService.update_on_event()` into
  `NearDeathHardeningPhase.apply()` for the `"near_death"` event kind on 2026-08-24, yet both the
  atlas (`entity-cognition` card 3, badge `orphan`) and the current wiring map (`EMO` node, line
  494, "write path ORPHANED") still describe Emotion as orphaned as of this session. I did not
  re-verify which is currently true — see Risks.

## Real Mechanism Candidate List

Derived entirely from the atlas's own 14 JSON sections (`docs/brainstorm/rpg_feature_atlas.html:1127-3139`),
excluding the `design-ideas` section (68 cards) per Finding 2 — design ideas are proposals, keyed
differently from built-or-gap mechanisms, and the ticket's own Open Question #2 leans toward not
blocking seeding on reconciling that separate key space. The wiring map's own tables/flowcharts were
used only to (a) supply explicit dependency arrows where they exist, (b) resolve layer assignment
for macro-scale mechanisms, and (c) as a cross-check on state where its four-class vocabulary
disagreed with the atlas's six-class one (flagged, never silently overridden).

**Real count: 75 candidate mechanisms**, not 30–50. Reported plainly per the task briefing: 71 raw
non-design-idea atlas cards, plus 2 net splits (see Judgment Calls) where one atlas card bundles two
genuinely distinct mechanisms whose badges already disagree with each other, plus 2 further
mechanisms (`nest`, `lair`) sourced from the wiring map's own hand-authored table rather than the
atlas JSON — see the "Region layer — City / Beyond-City" table below for the full, ground-truth-
verified accounting (71 + 2 splits + 2 wiring-map-only = 75; an earlier pass in this same document
mis-cited two rows and computed 73, corrected 2026-09-16 after a direct check against the real
atlas JSON). This exceeds the ticket's own estimate by a wide margin — flagged as a real,
not-force-fit finding.

**Decision (peer review, 2026-09-16, made against the then-reported count of 73; substance
unaffected by the later 73→75 correction): seed all 75, do not curate.** The 30–50 figure was an
estimate with no method behind it; every seeded mechanism carries a real citation. Curating toward
the estimate would mean dropping real, cited mechanisms against no stated exclusion criterion —
and a mechanism missing from the registry is invisible, the precise failure this epic exists to
end. A wrong estimate loses to a real count. The two net splits (aging_death/succession,
xp_leveling/breakthrough_bonuses) are recorded above with their provenance so the number is
traceable, not asserted.

Layer key used below: **entity** (rank 1, per_tick) · **group** (rank 2, per_tick) · **faction**
(rank 3, daily) · **region** (rank 4, slow) · **world** (rank 5, rare) — matching the design doc's
own 5-layer example exactly (`mechanism_registry_initiative.md` §3). `city`, `clan`, `race`,
`worldobject`, and `beyond-city` are atlas *sections*, not registry *layers* — each is folded into
one of the 5 (reasoning under Judgment Calls).

### Entity layer — Action (9, `rpg_feature_atlas.html` section `entity-action`)

| id | depends_on | state | citation |
|---|---|---|---|
| `combat_resolution` | `tactical_decision`, `combat_engagement` | done | atlas `entity-action#0`; wiring-map T6, `COMB-290` verified |
| `tactical_decision` | `action_pacing_readiness` | done | atlas `entity-action#1`; `engine/tactical.py` |
| `combat_engagement` | `action_pacing_readiness` | done | atlas `entity-action#2` ("Live by default since 2026-09-14"); `domains/combat_engagement/engine/pipeline.py:255` |
| `movement` | `action_pacing_readiness` | done | atlas `entity-action#3`; `engine/movement.py` |
| `action_pacing_readiness` | — | partial | atlas `entity-action#4` ("Live, but uniform" — flat ATB, ignores AGI) |
| `interaction_channeling` | `action_pacing_readiness` | done | atlas `entity-action#5`; `engine/interaction.py` |
| `conversation` | `action_pacing_readiness` | gap | atlas `entity-action#6` ("Real fragments exist; the concept itself does not") |
| `entity_trade` | `action_pacing_readiness` | gap | atlas `entity-action#7`; verified absent, no schema kind |
| `team_up` | `action_pacing_readiness` | gap | atlas `entity-action#8`; verified absent, no invite/accept step |

### Entity layer — Profile (12 atlas cards → 14 mechanisms, 2 splits)

| id | depends_on | state | citation |
|---|---|---|---|
| `attributes_biology` | — | done | atlas `entity-profile#0` |
| `derived_stats` | `attributes_biology` | done | atlas `entity-profile#1` |
| `race_archetype` | — | done | atlas `entity-profile#2` (composition root) |
| `class_assignment` | `race_archetype` | partial | atlas `entity-profile#3` ("narrow and role-locked") |
| `personality` | — | done | atlas `entity-profile#4` |
| `build_diversity` | `class_assignment` | gap | atlas `entity-profile#5` ("no branching exists") |
| `aging_death` | — | done | atlas `entity-profile#6`, split half — split rationale below |
| `succession` | `aging_death` | orphan | atlas `entity-profile#6`, split half; wiring-map T15 "Live, unreachable" |
| `genetics_aptitude` | — | orphan | atlas `entity-profile#7`; wiring-map T3/T4 |
| `evolution` | `derived_stats` | done | atlas `entity-profile#8` — **corrected**, see Docs Requiring Update |
| `skill_unlocks` | — | partial | atlas `entity-profile#9` |
| `xp_leveling` | `combat_resolution` | done | atlas `entity-profile#10`, split half; wiring-map CMB -.-> XP |
| `breakthrough_bonuses` | `xp_leveling` | done | atlas `entity-profile#10`, split half — **corrected**, see Docs Requiring Update; wiring-map XP-->BRK |
| `entity_role` | — | done | atlas `entity-profile#11` |

### Entity layer — Modification (2)

| id | depends_on | state | citation |
|---|---|---|---|
| `trauma` | `combat_resolution` | done | atlas `entity-modification#0`; wiring-map CMB -.-> TRM |
| `status_effects` | — | partial | atlas `entity-modification#1` ("Multipliers real; No unified system") |

### Entity layer — Cognition (18)

| id | depends_on | state | citation |
|---|---|---|---|
| `self_model` | `perception`, `trauma` | gated | atlas `entity-cognition#0`; wiring-map PER-->SELF, TRM==>SELF |
| `declared_cognition_schema` | — | orphan | atlas `entity-cognition#1` |
| `perception` | `cognition_capacity_fatigue` | done | atlas `entity-cognition#2`; wiring-map CAPT==>PER (next-tick feedback) |
| `emotion` | `tactical_decision` | orphan | atlas `entity-cognition#3`; wiring-map TAC-.->EMO — **see Risks: possibly stale, TCK-20260824 wired a near_death call site** |
| `affection_relationship_bonds` | `interaction_channeling` | done | atlas `entity-cognition#4`; wiring-map ITX-.->REL |
| `motivation_doctrine` | `goal_hierarchy`, `affection_relationship_bonds` | partial | atlas `entity-cognition#5`; wiring-map GOAL-->MOT, REL==>MOT |
| `commitment_betrayal` | `combat_resolution` | done | atlas `entity-cognition#6` ("Richer & more live") — **cross-doc disagreement, see Judgment Calls: wiring-map badges this `gated`** |
| `temporal_pressure` | — | skeleton | atlas `entity-cognition#7`; "46 LoC total" |
| `goal_hierarchy` | `belief_cycle`, `reputation` | done | atlas `entity-cognition#8`; wiring-map BEL-->GOAL, REP==>GOAL |
| `belief_cycle` | `self_model` | done | atlas `entity-cognition#9`; wiring-map SELF-->BEL |
| `information_trust_deception` | — | gated | atlas `entity-cognition#10` |
| `knowledge_model` | — | gated | atlas `entity-cognition#11`, Tier-2-only slice — see Judgment Calls for why this card was not seeded whole |
| `causal_spatial_memory` | `belief_cycle` | orphan | atlas `entity-cognition#12`; wiring-map BEL-->MEM |
| `adventure_routing` | `motivation_doctrine`, `cognition_capacity_fatigue` | done | atlas `entity-cognition#13`; wiring-map MOT-->CAPT-->DEC |
| `quest_generation_sourcing` | — | gated | atlas `entity-cognition#14` (hub-based, "built correctly, OFF by default") |
| `strategic_intelligence_core` | `belief_cycle` | done | atlas `entity-cognition#15`; "Calls both Belief Cycle and Detour Suggestion directly" |
| `committed_intentions` | `goal_hierarchy` | orphan | atlas `entity-cognition#16` badges `partial` ("consume-only") — **cross-doc disagreement, see Judgment Calls: wiring-map INT node badges `bug`, "no write path exists"** |
| `cognition_capacity_fatigue` | — | done | atlas `entity-cognition#17` |

### Group layer (2)

| id | depends_on | state | citation |
|---|---|---|---|
| `party_formation` | — | done | atlas `group-layer#0` |
| `guilds` | — | partial | atlas `group-layer#1` — layer assignment note below |

### Faction layer (8)

| id | depends_on | state | citation |
|---|---|---|---|
| `diplomacy` | — | done | atlas `faction-layer#0` |
| `betrayal_siege_war` | — | done | atlas `faction-layer#1` |
| `social_contracts` | — | done | atlas `faction-layer#2` |
| `reputation` | `affection_relationship_bonds` | done | atlas `faction-layer#3`; wiring-map MOV-.->REP — **see Judgment Calls, the wiring-map's own arrow source (Movement, witnessed events) is a low-confidence single citation** |
| `social_memory` | — | skeleton | atlas `faction-layer#4` |
| `cross_episode_social_consequences` | `social_memory` | orphan | atlas `faction-layer#5` ("narrative-event conversion layer... orphaned, not the underlying memory") |
| `cross_episode_grief_nemesis` | — | done | atlas `faction-layer#6` |
| `country_lifecycle` | `betrayal_siege_war` | partial | atlas `faction-layer#7` |

### Region layer (2)

| id | depends_on | state | citation |
|---|---|---|---|
| `regional_trauma_hazards_sovereignty` | `betrayal_siege_war` | done | atlas `region-layer#0` ("Live, buggy" — two disagreeing ownership systems); wiring-map FAC==>REG |
| `demographic_cohort_cycle` | `regional_trauma_hazards_sovereignty` | orphan | atlas `region-layer#1`; wiring-map "wired... input never seeded" |

### World layer (7)

| id | depends_on | state | citation |
|---|---|---|---|
| `campaigns` | — | done | atlas `world-layer#0` |
| `chronicle` | — | done | atlas `world-layer#1` |
| `opportunity_rumor_seeds` | — | gated | atlas `world-layer#2` |
| `cultural_drift` | — | done | atlas `world-layer#3` |
| `calamities_boss_spawns` | `regional_trauma_hazards_sovereignty` | done | atlas `world-layer#4`; wiring-map REG==>WLD "trauma feeds Calamities" |
| `world_generation` | — | done | atlas `world-layer#5` |
| `gods_pantheon_blessings` | — | gap | atlas `world-layer#6` — intentionally excluded per idea 63, see Anti-Drift Hazards |

### World layer — World Objects (5)

| id | depends_on | state | citation |
|---|---|---|---|
| `equipment_scoring` | — | done | atlas `worldobject-layer#0` |
| `inventory_trade_conservation` | — | done | atlas `worldobject-layer#1` |
| `crafting` | — | partial | atlas `worldobject-layer#2` ("real gate, thin content") |
| `buildings_town_services` | `city` | done | atlas `worldobject-layer#3`; wiring-map WOB==>CTY "located in" |
| `building_sabotage` | `buildings_town_services` | done | atlas `worldobject-layer#4` |

### Region layer — City / Beyond-City (5 mechanisms: 4 atlas cards + 1 wiring-map-only addition)

**CORRECTED 2026-09-16, re-verified directly against the real atlas JSON before finalizing the
YAML** (`python3 -c "...data['beyond-city']..."` — see Anti-Drift Hazards for why this check was
necessary). The original pass below had wrong card indices for this row group; the citations here
are ground-truth-checked, not re-derived from memory.

The atlas JSON's `beyond-city` section has exactly **3** cards, not citation-matched the way the
first pass assumed:
- `beyond-city#0` = "Camp: real, dormant scaffolding for a lesser settlement"
- `beyond-city#1` = "Ruins, mines & battlefields: real, but flattened into ordinary Region tags"
- `beyond-city#2` = "The content already implies a settlement-capacity axis, separate from intelligence"

`camp` and `ruins_mines_battlefields` are real atlas cards (`#0` and `#1` respectively —
**not** the same card, and **not** `#2`); `settlement_capacity_axis` is the genuine third card
(`#2`). None of the three double-cite each other. `nest` and `lair` are **not** atlas JSON cards
at all — they exist only in the wiring map's own separate, hand-authored "Beyond the City" HTML
table (`rpg_simulation_wiring_map.html` lines ~377-388), which itself has 4 rows (Camp, Nest,
Lair, Ruins/mines/battlefields) despite its own header text saying "3 cards" (that header counts
the atlas's 3 real JSON cards; Nest and Lair are additions layered on top in the wiring map's own
prose, both explicitly labelled "Proposed" / not yet built). Deriving them is legitimate per the
ticket's own instruction to use both the atlas AND the wiring map as sources — they are real,
cited, non-invented mechanisms, just sourced from a different document than the other three rows
in this group.

| id | depends_on | state | citation |
|---|---|---|---|
| `city` | `regional_trauma_hazards_sovereignty` | partial | atlas `city-layer#0`; wiring-map REG==>CTY |
| `camp` | `regional_trauma_hazards_sovereignty` | done | atlas `beyond-city#0` |
| `nest` | `camp` | skeleton | wiring-map only, no atlas JSON card ("target reuses Camp's real shape almost verbatim") |
| `lair` | — | skeleton | wiring-map only, no atlas JSON card ("real precedent is Boss's anchor pattern, not Camp's shape") |
| `ruins_mines_battlefields` | `regional_trauma_hazards_sovereignty` | partial | atlas `beyond-city#1` — real in content, flattened into Region tags |

### Faction layer — Clan / Race (2)

| id | depends_on | state | citation |
|---|---|---|---|
| `clan` | `betrayal_siege_war` | gap | atlas `clan-layer#0`; wiring-map "ordinary Factions underneath" — layer choice flagged, see Risks |
| `race_collective_force` | — | gap | atlas `race-layer#0` — **layer choice is an open question, not resolved cleanly, see Risks** |

### Entity layer — settlement-capacity axis (1, from `beyond-city`'s real 3rd card)

| id | depends_on | state | citation |
|---|---|---|---|
| `settlement_capacity_axis` | `race_archetype` | gap | atlas `beyond-city#2` ("implies a settlement-capacity axis, separate from intelligence") |

**Total: 9 + 14 + 2 + 18 + 2 + 8 + 2 + 7 + 5 + 5 + 2 + 1 = 75.** No double-counting exists — the
first pass's "collapse to 73" note was itself a citation error (it believed
`ruins_mines_battlefields` and `settlement_capacity_axis` cited the same `beyond-city#2` card; the
direct JSON check above shows they are `#1` and `#2`, two genuinely distinct real cards). **The real,
ground-truth-verified count is 75 mechanisms, not 73.** Reported to peer as a correction to the
earlier 73 figure — the substance of the "seed all, don't curate" decision is unaffected (75 is
still well under the "near 100" threshold that would have changed T3's planning), but the exact
number has provenance and should be recorded accurately, not left at a number one more direct check
disproved.

## Judgment Calls (atlas badge → six-class mapping ambiguities)

Per Assumption/Open Question #4 in the ticket — every one below is a real judgment call made and
recorded here, not silently resolved:

1. **`aging_death` / `succession` split** — atlas card `entity-profile#6` carries two badges (`done`
   "Aging/death live" + `partial` "Succession never triggers"). A single `partial` state would hide
   that aging/death is fully solid while succession is a structurally different problem (a written
   field, `heir_entity_id`, that is simply never populated — matching the atlas's own `orphan`
   semantics, "built but never fires," better than `partial`). Split into two mechanisms.
2. **`xp_leveling` / `breakthrough_bonuses` split** — same reasoning, atlas card
   `entity-profile#10` bundles `done` (XP/Classes) + `gap` (Breakthrough). Also independently
   confirmed as two genuinely separate wiring-map Buildup-table rows already (`XP → Level` and
   `Breakthrough Bonuses`), so the split has a second source's precedent, not just this
   investigation's own preference.
3. **`race_evolution_chains` merge, not split** — atlas card `entity-profile#8` (`done` + `orphan`)
   was *not* split, because the `orphan` half (the duplicate `progression/evolution.py` path) no
   longer exists (deleted, see Docs Requiring Update) — after that correction there is genuinely one
   mechanism, not two, so it collapses to a single `evolution` id at `done`.
4. **`status_effects` and `crafting` kept whole** — their second badges (`gap`/`partial`) describe
   *content thinness* ("no unified system", "recipes thin"), not a structurally distinct
   sub-mechanism the way succession or breakthroughs are. Kept as one mechanism each at their
   dominant (`partial`) state.
5. **`memory_capacity_trustfulness` card excluded as a standalone mechanism id** — atlas card
   `entity-cognition#11` describes fragmentation across three tiers that (once you check) are
   *mostly already separately carded*: Tier 1 ("Leads") is the same mechanism as `goal_hierarchy`
   (Leads/Blockers), Tier 3 ("Deep tier: orphaned") is the same code as `causal_spatial_memory`
   (both cite `domains/memory/{attribution,spatial_update}.py`). Only Tier 2
   (`cognition/knowledge_model.py: effective_certainty`) has no other card naming it, so it alone
   was seeded as a new `knowledge_model` mechanism (`gated`). Registering the whole card as its own
   4th mechanism would have double-counted two mechanisms already in the list under different ids.
6. **`commitment_betrayal` state — atlas says `done`, wiring-map says `gated`, kept the atlas value.**
   The atlas card (`entity-cognition#6`) reads "Richer & more live than earlier revisions found" and
   badges `done`; the wiring map's own per-mechanism table (line 542) badges the *same* code `gated`
   ("Live via unflagged route-scoring, but the documented gating call site is inactive"). Per the
   ticket's explicit instruction to derive from the atlas, kept `done`, but this is a real,
   unresolved disagreement between the two named source documents — flagged, not silently favored.
7. **`committed_intentions` state — atlas says `partial`, wiring-map says orphaned/broken, chose
   `orphan`.** The atlas card (`entity-cognition#16`) badges `partial` ("consume-only"); the wiring
   map's `INT` node (line 459) is styled `:::bug` with the caption "read-side plan queue — no write
   path exists," and its own per-mechanism table (line 536) says "read side only... no production
   code path writes one yet." "No write path exists at all" reads as closer to the atlas's own
   `orphan` definition (built-but-never-fully-functions) than `partial`. Chose `orphan`, flagged as
   a deviation from the atlas's literal badge for the record.
8. **`race_collective_force` and `settlement_capacity_axis` layer assignment — no clean home in the
   5-layer scheme.** Both describe collective/aggregate state that, per the wiring map's own Layer
   Model diagram (`RACE` node, line 301, styled `:::bug`, drawn *outside* all four L1–L4 subgraphs),
   structurally does not belong to any existing layer — "zero collective state anywhere above the
   entity." I assigned both `faction` as the nearest organizational tier a real implementation would
   likely live in if built, but this is a guess, not a citation-backed placement, and is flagged as
   an open question in Risks below rather than presented as settled.
9. **`guilds` → `group` layer, `clan` → `faction` layer** — the wiring map's own Layer Model draws
   both inside the same `L2 ORGANIZATION` subgraph alongside Group and Faction (line 283), but the
   design doc's 5-layer scheme only has one slot at that containment tier split two ways (`group`
   rank 2 vs `faction` rank 3). Assigned by cadence-fit: Guild visits happen per-tick like Group
   composition scoring; Clan is explicitly "ordinary Factions underneath" per the wiring map's own
   text (line 309), so it follows Faction's cadence.

## Risks and Open Questions

1. **Real count (75) far exceeds the 30–50 estimate.** Reported plainly, not force-fit. Every id has
   a real citation (atlas or wiring map) — none invented — so the excess is a genuine finding about
   corpus size, not investigation scope creep. **Resolved (peer decision, 2026-09-16): seed all 75,
   do not curate.**
2. **`race_collective_force` / `settlement_capacity_axis` have no clean layer.** Blocks a fully
   confident seed for exactly 2 of 75 rows (see Judgment Call 8). Does not block the rest of the
   registry; flagged for the implementer to make a final call on (assign to `faction` as I did, add
   a 6th layer, or leave unseeded pending a design decision) rather than assumed answered here.
3. **`emotion`'s state may itself be stale.** `tickets/done/TCK-20260824-WIRE-ORPHANED-MECHANISMS.md`
   claims `EmotionUpdateService.update_on_event()` was wired into
   `NearDeathHardeningPhase.apply()` for the `"near_death"` event kind on 2026-08-24, yet both
   current source documents (atlas card 3, wiring-map `EMO` node) still describe it as orphaned. I
   did not independently re-verify `src/engine/pipeline_phases/hardening.py`'s current state to
   resolve this — it is out of this investigation's scope to re-audit every mechanism beyond the two
   staleness findings already confirmed and flagged in Docs Requiring Update. Left as `orphan` per
   the atlas (the ticket's primary source), flagged as possibly wrong.
4. **`depends_on` edges are deliberately sparse (~25 of 75 rows have a non-empty value).** The wiring
   map's mermaid arrows mostly encode **tick execution order** ("Perceive happens before Self-Model
   this tick"), not necessarily a hard functional "requires this to exist" dependency. Converting
   every sequence arrow into `depends_on` would produce a technically-populated but semantically
   misleading DAG. I included only edges with a defensible "consumes this mechanism's output/state"
   reading (readiness gating the whole Act phase; combat feeding trauma/XP/commitment; feedback
   loops named explicitly as "next tick"). The remaining ~49 rows are left with `depends_on: []` per
   the design doc's own rule ("hand-author only real edges... do not guess") rather than populated
   speculatively. This is not a defect to fix before seeding — it is the expected state for a
   from-scratch hand-authored file — but whoever authors the YAML should not read the sparse count as
   "incomplete," only as "conservatively sourced."

   **This is a third axis, distinct from the two the wiring map already keeps apart.** The Layer
   Model diagram's own containment lanes (Individual/Organization/Geography/World, `ENT ==> GRP`
   etc.) are **containment** — a Faction *contains* Entities. The mermaid sequence arrows inside the
   Entity Operating Loop (`PER --> SELF --> BEL`) are **execution order** — what happens before what,
   within one tick. `depends_on` in the registry is neither: it is **functional dependency** — "this
   mechanism cannot produce a meaningful result without that one already existing/having run,"
   independent of both containment and tick sequencing. The design doc's own Finding 3 already
   distinguishes containment from dependency ("Containment is not dependency: a Faction *contains*
   Entities, whereas war *depends on* combat"); this investigation adds the third term explicitly
   because the wiring map's own arrows are the most natural, and wrong, source to reach for when
   populating `depends_on` — most of them encode the second axis (execution order), not the third
   (functional dependency), and conflating the two is exactly how the sparse count above could get
   "fixed" incorrectly by a future editor under time pressure.

   **Known consequence for T3 (priority derivation), recorded now rather than discovered late:**
   with only ~25 of 75 mechanisms carrying a non-empty `depends_on`, roughly 50 mechanisms have zero
   dependents. If T3's priority rule is `rank × dependents` (or similar), the dependents term
   collapses to zero for most rows, and **layer `rank` alone will do nearly all of the ordering work
   in this first cut** — not because rank is the intended dominant signal, but because the dependency
   graph is still thin. This is not a defect in this ticket's seed data (inventing edges to make the
   graph denser would be worse, per the reasoning above) — it is a known, load-bearing property of a
   from-scratch hand-authored graph that T3 should plan around (e.g. treating near-zero-dependent
   rows as expected rather than a sign something is missing), not rediscover under pressure once
   chart generation is underway.
5. **File location.** `docs/brainstorm/mechanisms.yaml` is the right location, confirmed by
   contrasting the two existing conventions directly rather than assuming the ticket's own leaning:
   `registries/*.jsonl` (`tag_registry.jsonl`, `layer_registry.jsonl`) is documented in
   `docs/guidelines/tag_taxonomy.md` (lines 20, 146, 187-188) as strictly **append-only**, managed
   exclusively through a `tools/*_registry.py add` CLI, never hand-edited — the opposite of what a
   mechanism registry needs (mechanisms get renamed, reparented, restated as their real code state
   changes). `docs/brainstorm/idea_index.json` is git-tracked, lives beside the brainstorm corpus it
   indexes, and is edited by **regeneration** (`make brainstorm-idea-index` overwrites it). The
   mechanism registry is neither pattern cleanly: it is hand-edited *and* validated (unlike the
   append-only registries, and unlike the fully-generated idea index). `docs/brainstorm/` is still
   the closer fit of the two, because it is editable-and-git-tracked (the load-bearing property the
   registry needs) even though the *mechanism* of editing differs (hand-edit + validate, vs.
   regenerate). `registries/` is disqualified outright by its append-only contract, which is
   structurally incompatible with a file whose rows need real edits over time.
6. **Graphify's report-only cross-check needs to be more careful than "does a path exist."** See
   below.

## Graphify Cross-Check Feasibility

`graphify path "<A>" "<B>"` works and is scriptable: it returns a labeled hop chain
(`A --relation [confidence]--> B`) when a path exists, and a clean `"No node matching '<X>' found."`
message when a named symbol doesn't exist in the graph at all — both are parseable.

**But a bare "does *any* path exist" check is not a reliable suspicious-edge detector at this
codebase's scale**, confirmed by direct testing in this session:

- `graphify path "CombatResolutionSystem" "MovementSystem"` → 1 hop, direct `uses` edge — this is
  exactly the kind of real, close relationship the check should confirm.
- `graphify path "CampService" "EquipmentService"` → 3 hops, routed through `StateUpdate` (a
  near-universal shared type) and a test file's imports.
- `graphify path "TemporalPressureService" "ChronicleCompiler"` → 4 hops, routed through
  `EntityState` and `GriefUrgencyModifier`, two more near-universal hub nodes.

`CampService`/`EquipmentService` and `TemporalPressureService`/`ChronicleCompiler` are not
meaningfully related mechanisms — nothing in the atlas or wiring map suggests a real dependency
between them — yet both pairs return a "path found" result within a handful of hops, purely because
`EntityState`/`StateUpdate`/`AuthoritativeState` are used pervasively across nearly the entire
codebase (36,087 nodes total per `graphify-out/GRAPH_REPORT.md`). A checker that treats "path exists
within N hops" as "supported" would essentially never flag anything as suspicious, defeating the
purpose of the check (Scope item 5: "flag any declared `depends_on` edge with no supporting
call/import path as suspicious").

**What's feasible, for whoever implements the actual checker (this ticket does not build it, per Out
of Scope item 4's spirit — Scope item 5 asks only that this investigation assess feasibility):**
`graphify-out/graph.json` is a plain JSON dict (`directed`, `multigraph`, `graph`, `nodes`, `links`,
`hyperedges`, `built_at_commit`) with 105,139 `links`, each carrying `relation` (e.g. `"contains"`,
presumably also `"uses"`/`"calls"`/`"imports"`), `confidence` (`EXTRACTED` vs `INFERRED`), `source`,
`target`, and `confidence_score`. A real checker should load this file directly in Python (not shell
out to `graphify path` per edge — 105k edges is far too many for repeated subprocess calls) and do a
bounded-hop BFS that (a) only counts `relation` values that mean a real call/import/use, not
`"contains"` (a file containing a symbol is not evidence of a cross-mechanism dependency), and (b)
either excludes a small set of known high-fan-in hub nodes from counting as a supporting hop, or
treats any path that must route through one as `weak`/`unverified` rather than `supported`. Building
that exclusion list is itself feasible — `graphify-out/GRAPH_REPORT.md`'s own community-detection
output (1,368 communities) or a simple degree-count over `links` would surface the hub nodes
directly. This is real, non-trivial script design work, appropriately left to whichever ticket
actually builds the checker, not fully specified here.

## Anti-Drift Hazards

- **Do not let seeding turn into fixing.** Several atlas cards describe genuine, well-scoped future
  work (e.g. `gods_pantheon_blessings` is *intentionally* excluded per design idea 63, not a gap to
  close — the atlas's own text says so directly). The registry's job is to record `state: gap`
  accurately, not to imply every `gap`/`orphan` row is a to-do list for this or the next child
  ticket.
- **Do not silently curate the 75 down to "a rounder-looking 30–50."** If the eventual seed count
  differs from what's listed above, the reason must be recorded (e.g., in the ticket's Assumptions
  section or a follow-up investigation note) — not quietly dropped rows.
- **Do not let the `depends_on` sparsity get "fixed" by mechanically converting every wiring-map
  sequence arrow into a dependency edge.** That would produce a DAG that looks complete but encodes
  tick-order, not real "requires to function" dependency — see Risk 4. Filling in more edges
  correctly requires either source-level verification per mechanism or waiting on the graphify
  cross-checker (a later, out-of-scope tool) to surface real candidates for human confirmation.
- **`reputation`'s single depends_on citation (`affection_relationship_bonds`) is thin** — the
  wiring map's own arrow for it (`MOV -.-> REP`, "witnessed events") actually names Movement, not
  Affection, as the trigger. I substituted `affection_relationship_bonds` because both mechanisms
  ultimately write through the same `RelationshipService`, but this is my own inference, not a
  direct citation — do not treat it as more certain than it is when the YAML is actually authored.
- **Two atlas cards (`race_collective_force`, `settlement_capacity_axis`) genuinely do not fit the
  5-layer scheme.** Resist the urge to quietly force them into `faction` without recording that it's
  a placeholder guess (Judgment Call 8) — a future ticket revisiting layer design should be able to
  find this flagged, not discover it was silently decided.
