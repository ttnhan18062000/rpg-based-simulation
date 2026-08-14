---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS
artifact_type: investigation
tags: [simulation-quality, faction]
---

# Investigation — TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS

## Current Behavior

### `data/content/social/faction_relationships.yaml` — verified by direct count, not by trusting the ticket text

Counted directly (34 list entries, 20 unique unordered `(source,target)` pairs):

- **34 entries** confirmed. Every pair is authored as a directed pair, almost always in **both**
  directions (e.g. `town_to_wild_beasts` + `wild_beasts_to_town`), sometimes with asymmetric
  `axes`/`relationship_model` per direction (e.g. `town_to_bandits` uses `security_hostility`,
  the reverse via `bandits_to_town` uses `outlaw_settlement_hostility` — different flavor, same
  hostility level).
- **20 unique undirected pairs covered** out of `C(16,2) = 120` possible (16 factions in
  `data/content/social/factions.yaml`, confirmed) → **16.7%**, exactly matching the ticket's
  framing. (The task briefing was skeptical this framing might be stale — it is not; recomputed
  independently and it is exact.)
- **15 of 16 factions appear** in at least one relationship entry. The only faction with **zero**
  entries is `neutral` — also confirmed exact.
- Factions covered: `town_council, wild_beast_pack, goblin_warband, merchant_league,
  bandit_company, forest_wardens, dwarven_mine_clan, moon_cult, orc_clan, undead_remnants,
  hero_guild, dragon_cult, arcane_circle, swamp_tribe, spirit_court`.

### Populated-vs-catalog cross-reference (new finding, not in the ticket text)

Per `stored_artifacts/TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS/investigation.md` (lines 77-82,
today's sibling ticket), only **12 of 16** catalog factions are ever populated by any current
world-module combination: `town_council, merchant_league, wild_beast_pack, goblin_warband,
bandit_company, forest_wardens, spirit_court, orc_clan, undead_remnants, arcane_circle,
swamp_tribe, hero_guild`. `moon_cult`, `dwarven_mine_clan`, `dragon_cult`, and `neutral` have
**zero** module path to population today.

Filtering the current 20 covered pairs down to "both factions populated" gives **14 of the
`C(12,2) = 66`** populated-only pairs → **21.2%**. The other 6 covered pairs (10 of the 34 raw
entries: `dwarves_to_goblins`, `moon_cult_to_town`, `dwarves_to_orc`/`orc_to_dwarves`,
`dragon_cult_to_town`/`town_to_dragon_cult`, `moon_cult_to_arcane`/`arcane_to_moon_cult`,
`arcane_to_dwarves`/`dwarves_to_arcane`) involve a faction with **no live gameplay presence** in
any current world — content that inflates the raw-120 percentage without improving any world's
actual encounter variety.

This gives the planner concrete numbers for the ticket's own UQ-1:
- Raw 120-pair basis: currently 20/120 (16.7%); 50%+ target = 60+ pairs (40 more needed).
- Populated-only 66-pair basis: currently 14/66 (21.2%); 50%+ target = 33+ pairs (19 more needed).

### The catalog file is NOT the runtime diplomacy state — two separate mechanisms exist

`docs/systems/faction_contract.md` describes `FactionState.diplomatic_relations: Dict[str,
DiplomaticState]` — the **per-world runtime** diplomacy state that `DiplomaticStateMachine`
(`src/domains/faction/diplomatic_state_machine.py`) mutates tick-by-tick (NEUTRAL→TENSE→
HOSTILE→WAR/ALLIED). "Absence = NEUTRAL — do not populate all pairs at construction" (contract,
line 66) refers to **this** structure, not to `faction_relationships.yaml`.

`src/engine/faction_decision.py` (`FactionDecisionPhase`, `FactionAwarenessService`, the
diplomatic-action dataclasses `TreatyOffer`/`TradeAgreement`/`AllianceProposal`/`Betrayal`) reads
only `state.factions[*].tension_level/territory/military_strength/diplomatic_relations` — it
**never touches `faction_relationships.yaml`**. The ticket's own "Related Code Areas" line
("`src/engine/faction_decision.py` — `DiplomaticStateMachine` (consumer of this catalog, not
modified by this ticket)") is factually incorrect: `faction_decision.py` is not a consumer of this
catalog at all. See below for the actual consumers.

### Actual runtime consumers of `faction_relationships.yaml` — this is the critical finding

`grep -rn "faction_relationships" src/` surfaces the real call graph:

- `src/content/repository.py:112,198` — `CatalogRepository.faction_relationships: Dict[str,
  FactionRelationshipDefinition]`, loaded from `social/faction_relationships.yaml`.
- `src/content/validator.py:343-370` — `_validate_relationship_relations()`: every entry's
  `source_faction`/`target_faction` must resolve in `factions.yaml` (rule `CAT-REL-012`), and
  every `axes` key must resolve in `data/content/foundation/relationship_axes.yaml` (11 valid
  axis IDs today: `hostility, trust, fear, respect, territorial_conflict, trade_affinity,
  resource_competition, religious_conflict, ancient_grudge, kinship, debt`).
- `src/content_semantics/relation.py` (`RelationProjectionService.project_relation()`, lines
  72-144) — looks up a matching `(source_faction, target_faction)` relationship record and maps
  its `axes["hostility"]` value to a `label`:
  - `"high"` or `"medium"` → **`"enemy"`, unconditionally** (no context needed).
  - `"medium_contextual"|"high_contextual"|"low_base_contextual"` → context-dependent
    (`"enemy"` if combat_engaged, else `"threat"` if intruding/close, else `"threat"`).
  - `axes["territorial_conflict"] == "high_if_intruding"` → `"intruder"` if intruding else
    `"neutral"`.
  - Otherwise → `"neutral"`.
  - Perspective-projected labels (from `perspectives.yaml`, checked first) win over relationship
    axes when a perspective exists for the source faction and covers the target in one of its
    label groups.
- `src/content_semantics/faction.py` (`FactionSemanticsService.is_hostile_compat()`, lines
  160-213) — the actual hostility predicate used at combat time. It checks whether a
  perspective **or** a relationship record exists for `(source, target)`; if neither exists it
  falls straight to the coarse legacy `is_hostile()` (alignment-bucket: `invader` vs
  non-`invader`). If either exists, it calls `RelationProjectionService.project_relation()` and
  maps the resulting `label` to a bool (`"enemy"` → True; `"threat"` → context-dependent;
  `"intruder"` → context-dependent; else False).
- `src/engine/legality.py:221-261` (`LegalityServiceV2.verify_attack_legality()`, "Faction
  Validity (Friendly Fire Law)" step) — calls `is_hostile_compat()` to decide whether an attack
  between two entities is `ReasonCode.FRIENDLY_FIRE_ILLEGAL`. **This is a live combat-legality
  gate evaluated every attack, every tick.**
- `src/engine/combat_rewards.py` (`CombatRewardClassificationService.classify_defeated_target()`)
  — also calls `is_hostile_compat()` (relation projection first, legacy `EntityRole` fallback
  second) to classify kill rewards. Documented in parity ledger `COMB-280` (**P0**, see below),
  which already records an explicit behavior-change divergence for this exact mechanism.
- `src/content/resolver.py:319` — also iterates `faction_relationships` (world-assembly-time
  resolution; not fully traced in this pass, flagged for the implementer to check before
  assuming compile-time-only usage).

**Only 6 of 16 factions have a `perspectives.yaml` entry as `chosen_faction`**: `hero_guild,
wild_beast_pack, goblin_warband, merchant_league, undead_remnants, swamp_tribe` (confirmed by
reading `data/content/social/perspectives.yaml`). For the other **10** factions as *source*
(`town_council, neutral, bandit_company, forest_wardens, orc_clan, dwarven_mine_clan, moon_cult,
arcane_circle, dragon_cult, spirit_court`), `project_relation()` has no perspective to consult, so
a **new relationship entry with `hostility: "high"` or `"medium"` deterministically flips
`is_hostile_compat()` to `True`** for that directed pair — a real, unconditional change from
today's coarser legacy alignment-bucket fallback (`invader` vs non-`invader` only).

**This directly contradicts the ticket's inherited premise** ("pure content, additive, no code
risk... same risk class as FACTION tension seeding"). That analogy traces to
`stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-FACTION/plan.md:147`, which describes seeding
*numeric* `initial_tension_level` fields — genuinely inert until a separate threshold check
consumes them. `faction_relationships.yaml` is categorically different: its `hostility` axis
value is read directly by two engine-tier consumers (combat legality, combat reward
classification) with **no separate gating threshold** — for factions without a perspective, the
axis value alone determines the hostility verdict.

## Mechanics / Engine Constraints

- `docs/mechanics/02_combat_laws.md` line 87: "**Friendly Fire**: Faction allies do not take
  splash damage from their teammates." This is the mechanic whose enforcement path
  (`LegalityServiceV2.verify_attack_legality`, Faction Validity step) is affected by this ticket.
- `docs/systems/faction_contract.md` — authoritative for `FactionState`/`DiplomaticState`
  runtime diplomacy, **not** for `faction_relationships.yaml`. Do not conflate the two when
  scoping or reviewing this ticket.
- `docs/content/content_semantics_contract.md` states `src/content_semantics/` is "**NOT
  authoritative simulation state**... consumed at world-building/compilation time, not during
  simulation ticks" (lines 12, 20). This is **stale relative to actual code**:
  `FactionSemanticsService`/`RelationProjectionService` are invoked live, per-attack, from
  `src/engine/legality.py` and `src/engine/combat_rewards.py` — both engine-tier, tick-path
  modules. This is a pre-existing doc/code divergence, out of this ticket's explicit scope to
  fix, but the implementer and reviewer should not rely on the doc's "compile-time only" claim
  when reasoning about blast radius. Recommend a follow-up doc-fix ticket.

## Parity Ledger Overlap

- **`COMB-280`** (`docs/parity_ledger/combat_movement.yaml:2885-2901`), **priority P0**, status
  `verified`. Text: "Combat result emits reward/progression consequence when applicable."
  `v2_evidence` names `CombatRewardClassificationService.classify_defeated_target()` — step 1 is
  `FactionSemanticsService.is_hostile_compat()` via relation projection. Its own
  `divergence_note` already documents "MONSTER_HORDE attacker defeating HERO_GUILD defender now
  gives HOSTILE_CREATURE (source=relation_projection) instead of HERO_KILL" — i.e. this exact
  mechanism is known to be behavior-sensitive to relation-projection inputs.
  **`test_path: tests/unit/combat/test_combat_rewards.py` — this P0 entry requires this test to
  keep passing after the catalog change** (per CLAUDE.md's "P0 entries require a passing
  test_path" rule). Read: that test file uses legacy `Faction` enum literals
  (`HERO_GUILD`/`MONSTER_HORDE`/`NEUTRAL`), which do not match any real catalog faction ID
  (`get_faction_id_str()` falls back to the lowercased enum name, e.g. `"monster_horde"`, which
  is not a key in `factions.yaml` — no catalog faction has that literal ID), so `repo.get_faction()`
  returns `None` and the test stays on the legacy fallback path regardless of new catalog
  entries. **Low risk to this specific test**, but confirm this reasoning holds after authoring —
  do not assume it silently.
- No parity ledger entry exists yet for `faction_relationships.yaml` coverage percentage, nor
  specifically for the `LegalityServiceV2` friendly-fire gate's dependency on
  `is_hostile_compat()`. Per CLAUDE.md's Authoritative Mechanics Rule ("If no entry exists, add
  one"), this ticket's implementation likely needs to **add** a parity entry (candidate location:
  `docs/parity_ledger/combat_movement.yaml`, near `COMB-280`, or a new `FAC-0xx` in
  `docs/parity_ledger/faction.yaml`) documenting that catalog coverage of `faction_relationships`
  now determines legality/reward outcomes for previously-legacy-fallback faction pairs. This is
  not currently in the ticket's Acceptance Criteria — flagging as a likely gap for the planner.
- `docs/parity_ledger/faction.yaml` — FAC-001 through FAC-012 all cover the **runtime**
  `FactionState`/`DiplomaticStateMachine` mechanism, not the catalog file. None require changes
  from this ticket; listed here to confirm none silently regress (they don't touch
  `faction_relationships.yaml`).

## Prior Work

- **`tickets/done/TCK-20260627-P2D-FACTION-RELS.md`** (done 2026-06-27) is the ticket that
  originally took the file from 14→34 entries (20/120 pairs) — i.e. **this is the second pass at
  the same P2-D backlog item**, not new ground. Its Implementation Notes establish the working
  conventions this ticket should continue: `FactionRelationshipDefinition` schema
  (`extra="forbid"`): `id, source_faction, target_faction, relationship_model, axes: Dict[str,
  str]`; snake_case `relationship_model`/axis-value vocabulary; prioritize
  conflict/economy-module factions; author in both directions with asymmetric flavor per
  direction; `# STATE: ADDITIONAL` comment convention for new entries (existing entries also use
  `# STATE: REDESIGNED-CORE`/`# STATE: LEGACY-EXPORT` — new entries should use `ADDITIONAL`).
- `docs/plans/audit_fix_plan.md` P2-D section's `Files:` field still says
  `data/content/faction_relationships/` (a directory) — stale/wrong; the real path
  (`data/content/social/faction_relationships.yaml`, single file) is correctly identified
  elsewhere in the same document's Summary Table row and in this ticket. When this ticket updates
  the P2-D section (Scope items 6-7), fix this stale `Files:` field too.
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS/investigation.md` — source of the
  12/16-populated-factions finding used above; also documents that `moon_cult` and
  `dwarven_mine_clan` have **zero module path to population today** even though
  `dragon_cult_elite_cell` exists in `populations.yaml` unreferenced by any module.
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO/` — sibling ticket done
  today; its new FACTION-isolation world is a downstream beneficiary of this ticket per the
  Related Tickets list, but made no changes to `faction_relationships.yaml` itself.
  `TCK-20260702-SIMQ-UPLIFT2-FACTION` — source of the (mis-applied) "same risk class" analogy;
  its actual change was seeding numeric `initial_tension_level`, not qualitative relationship
  content — see Current Behavior section above for why the analogy does not hold.

## Risks and Open Questions

1. **(Blocking) UQ-1 needs a decision before authoring, not just a note.** The ticket says
   "interpret 'active' as populated-somewhere-in-corpus pairs first... but also report the raw
   120-pair percentage." Concrete numbers now available: raw 20/120 (16.7%) vs. populated-only
   14/66 (21.2%). The planner must pick which denominator the "50%+" AC is graded against
   (60+ raw pairs vs. 33+ populated-only pairs) — these require materially different amounts of
   new content. Do not assume; this changes the size of the ticket.
2. **This is not risk-free content.** New relationship entries for any of the 10 factions
   lacking a `perspectives.yaml` entry (see Current Behavior) will deterministically change
   `is_hostile_compat()` outcomes for that directed pair versus today's legacy alignment-bucket
   fallback — affecting both combat legality (`FRIENDLY_FIRE_ILLEGAL`) and reward classification
   (`COMB-280`, P0) for any world where those faction pairs actually meet in combat. This must be
   treated as a behavior change requiring the regression tests below, not "pure content."
3. **`neutral` faction is the universal fallback ID** (`get_faction_id_str()` returns `"neutral"`
   for any entity that fails to resolve a real faction identity). AC#3 requires at least one
   explicit `neutral` relationship entry but does not specify a stance. An aggressive
   `hostility: "high"` entry with `neutral` as source has unusually wide blast radius — it would
   affect every entity that falls back to the neutral ID, not just a specific two-faction
   interaction. Recommend the planner require a low/neutral-flavored `hostility` value (e.g.
   `"none"` or a `_contextual` variant) for `neutral`'s first entries unless a specific target
   faction and gameplay reason is identified.
4. **AC#4's stated verification method is insufficient for this risk.** `make evaluate --dry-run`
   runs `tools/evaluate_simq.py --dry-run`, documented in the Makefile as "Diff current
   calibration data against grade anchors (**no engine re-run**)." Since this ticket's change is
   pure catalog data (no calibration JSON is touched by editing a YAML content file), `--dry-run`
   will trivially report 0 regressions regardless of whether the new entries actually change
   combat legality/reward outcomes in any world. To genuinely test this ticket's real risk,
   `make evaluate-full` (re-runs the engine) and/or the specific unit/integration suites listed
   in the Test Plan must also run. Flag this to the planner as a correction to the ticket's own
   AC, not just an addition.
5. 10 of the current 34 entries (5 of the 20 pairs) involve `moon_cult`, `dwarven_mine_clan`, or
   `dragon_cult` — factions with zero populated presence in any current world. The ticket's
   Scope items 2-3 already say to prioritize populated/conflict/economy factions; the planner
   should not let new authoring pad the raw-120 percentage with more theoretical pairs among
   these three, since that would satisfy AC#1 (raw-120 framing) without improving any world's
   actual encounter variety — the stated goal.
6. No parity ledger entry currently documents the catalog-coverage-affects-legality relationship
   established above. This ticket likely needs to add one (see Parity Ledger Overlap) — not
   currently in the AC list. Flag to planner; do not silently skip.
7. The ticket's "Related Code Areas" listing of `src/engine/faction_decision.py` as "the
   consumer" is factually wrong (see Current Behavior) — implementer should be redirected to the
   real consumers (`src/content_semantics/faction.py`, `src/content_semantics/relation.py`,
   invoked from `src/engine/legality.py` and `src/engine/combat_rewards.py`) so no time is spent
   looking for catalog usage in the wrong file.

## Anti-Drift Hazards

- **Do not touch `src/engine/faction_decision.py`, `src/domains/faction/diplomatic_state_machine.py`,
  or `MilitaryConflictPhase`** — correctly out of scope per the ticket, and doubly so since (per
  this investigation) none of them even read `faction_relationships.yaml`.
- **Do not "fix" the content_semantics_contract.md doc's stale compile-time-only claim as part of
  this ticket** — real, but explicitly out of scope; file a follow-up ticket instead if desired.
- **Do not add relationship entries with `hostility: "high"`/`"medium"` casually for
  non-perspective factions** without checking whether that pair is ever actually co-present in a
  world — the effect is unconditional and immediate on `is_hostile_compat()`, not a soft/tunable
  signal.
- **Do not violate `CAT-REL-012` validation**: every new entry's `source_faction`/`target_faction`
  must exist in `factions.yaml`, and every `axes` key must exist in
  `data/content/foundation/relationship_axes.yaml` (11 valid IDs — do not invent new axis names
  without registering them there first, mirroring the same append-only pattern as the tag
  registry).
- **Do not create duplicate `(source_faction, target_faction)` entries** — check the existing 34
  before authoring; the schema does not appear to enforce pair-uniqueness at the validator level
  (only per-field referential integrity), so a duplicate would silently coexist and the
  first-match-wins iteration order in `RelationProjectionService`/`is_hostile_compat` would decide
  which one "wins," which is a subtle latent bug class to avoid introducing.
- **Do not let the `neutral` AC (item 4) become a wide-blast-radius change** — see Risk #3 above.
- **Do not treat `make evaluate --dry-run` passing as proof of "0 regressions"** for this
  specific ticket — see Risk #4. The dedicated legality/reward test suites are the real signal.
