---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content]
---

# Roadmap — RPG Design Ideas: From Brainstorm to the M1-M9 Program

**Purpose**: `docs/brainstorm/rpg_feature_atlas.html` (Rev 60+) contains 65 fully-investigated RPG design
ideas, already sequenced (Suggested Build Order), grouped into the M1-M9 milestone program (Roadmap
section), classified by implementation pattern and flag-risk (Implementation Patterns), traced for
real-code blast radius (Cross-Cutting Risk), checked for consolidation opportunities (Shared Implementation
Opportunities), and mapped to real pipeline phases with proposed arena-style tests (Phase Placement &
Testing Strategy). This doc is the bridge from that brainstorm-tier investigation into this repo's real
epic-tier planning format — it does not re-derive any of that grounding, it routes to it.

**This is genuinely large enough that one epic can't hold it cleanly** — 65 ideas, 9 milestones, several
long dependency chains. Following the same pattern already used for the live-map and HUD design-system
efforts: one roadmap doc stating the sequencing/gating rule once, one milestone epic fully scoped and ready
to ticket, and the sibling epics kept scope-only (M2-M6) or oversight-only (M7-M9) until the milestones
before them actually ship.

**2026-08-29 review note**: this roadmap has been reconciled against
[`docs/brainstorm/codex/2026-08-27-core-rpg-plan-brainstorm-update-request.md`](../../brainstorm/codex/2026-08-27-core-rpg-plan-brainstorm-update-request.md)
(documentation-consistency findings) and
[`docs/brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md`](../../brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md)
(a new temporal-axis dimension, added beside the existing spatial/containment model — see "Temporal axis"
below). Plan-owner decisions made in this pass: Idea 66 promoted with a narrow gate; M3's Marriage decoupled
from Reproduction; M6's Idea 39 stays one contract; `CultureDeriver`/`CulturalBiasApplicator` activation is
owned by M4. M1's 21-ticket implementation batch (already in flight under `tickets/todos/m1-quick-wins/`)
was deliberately left untouched by this review — see M1's section below.

## Source of truth

All technical grounding — real file:line citations, blast-radius findings, reuse opportunities, phase
placement, and per-idea quality scores — lives in three published documents, not duplicated here:

- `docs/brainstorm/rpg_feature_atlas.html` — the 65 ideas themselves, Build Order, Roadmap, Implementation
  Patterns, Cross-Cutting Risk & Blast Radius, Shared Implementation Opportunities, Infrastructure Gaps,
  Phase Placement & Testing Strategy.
- `docs/brainstorm/design_merit_scorecard.html` — a 7-axis quality score for every idea (Direction Fit,
  Narrative Generativity, Groundedness, Pillar Reach, Efficiency, Risk-Adjusted Cost, Leverage).
- `docs/brainstorm/the_unwritten_world.html` — the 8 creative-direction principles every idea was checked
  against.

Each milestone epic below cites specific idea numbers; look them up in the atlas by anchor
(`rpg_feature_atlas.html#idea-N`) for full investigation detail rather than re-reading it here.

## Milestones

### M1 — Quick Wins & Housekeeping (in flight)

**Tracking**: 21 ordered child tickets already exist under `tickets/todos/m1-quick-wins/`, with
`tickets/todos/m1-quick-wins/SEQUENCE.md` as the executable ordering authority — see
`docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md` for the full breakdown. 19 of the 20 originally
scoped ideas produced tickets (idea 7 and idea 17 were each split into two tickets by responsibility); idea
16 was resolved by investigation with no behavior-change ticket needed.

No dependencies on anything else in this roadmap, and nothing in M1 blocks on anything else. **This batch is
actively being implemented; this review pass deliberately made no changes to its scope, tickets, or
sequence** — the temporal-axis proposal's own integration plan (§13) assigns temporal-contract
responsibility starting at M2, never at M1, and the update-request's plan-owner review found M1's ticket
content sound as-is (only the surrounding documentation was stale). The confirmed final-permadeath lifecycle
defect (`PERMADEATH` bypasses `LifecycleSystem.resolve_lifecycle()`'s deactivation check) is a related
correctness bug but is **not** part of this 21-ticket batch — see M5 below for its owner.

### M2 — Foundational Systems (gated on M1's flag-governance decision, idea 9)

**Tracking epic**: `TCK-20260823-EPIC-RPG-M2-FOUNDATIONAL-SYSTEMS` (not yet created, scope-only — new
sibling epic).

16 ideas, the highest-leverage tier in the whole set — Species Classification (14), City ownership (35),
Clan's shape (36), population seeding (43), and place-type transitions (48) are each cited as prerequisites
by multiple downstream ideas. **Not mutually independent** — the ideas split into five branches: entity
foundations (2, 4, 5, 8, 11, 14, 23, 27, 28, 30), independent institution/species foundations (36, 37),
population foundation (43), place-dependent foundations (35, 48 — gated on Idea 66, see below), and
interaction capability (6, which may reuse M1 idea 13's appraisal-policy helper but keeps its own
domain-specific authoritative outcome). **Gate**: idea 9 (deciding the fate of 8 already-built rollout
flags) should land first — several M2 ideas are exactly the kind of new-flagged-mechanism idea 9's own
governance decision is meant to set precedent for.

**Idea 66 (Region/Place architecture) — promoted, narrow gate.** Idea 66 blocks only work whose
authoritative state depends on Place identity or containment: ideas 35 and 48 here, and the place-shaped
half of M4 (see M4 below). Ideas 36, 37, and 43 are explicitly *not* blocked by it — population seeding in
particular is a shared foundation independent of the Place migration.

### M3 — Family, Species & the Adult Life (gated on M2)

**Tracking epic**: `TCK-20260823-EPIC-RPG-M3-FAMILY-SPECIES` (not yet created, scope-only).

5 ideas — reproduction, marriage, coming of age, dependents, closing the population-pressure loop. Hard
dependency on M2's Species Classification (14) and population seeding (43) landing first, confirmed
directly in the atlas's Cross-Cutting Risk section. **Marriage is decoupled from Reproduction** (plan-owner
decision, 2026-08-29): build order is Idea 32 (Reproduction) → Idea 38 (population-pressure feedback,
immediately after or atomic with 32) → Idea 31 (Dependents) → Idea 34 (Coming of Age); Idea 33 (Marriage)
proceeds independently once its own proposal-lifecycle prerequisites clear, rather than gating Reproduction.
Also owns concrete human/species lifecycle durations and fantasy-year aging once the temporal axis's
calendar authority is settled (see "Temporal axis" below) — no numeric thresholds are changed by this
review pass.

### M4 — Beyond the City & the Layer Model (gated on M2)

**Tracking epic**: `TCK-20260823-EPIC-RPG-M4-BEYOND-CITY` (not yet created, scope-only).

12 ideas — Camp/Nest/Lair, settlement-capacity, Country's EXPAND directive, population pressure as an
expansion engine. Gated on M2's City ownership (35), Clan shape (36), and place-type transitions (48).
Splits into three branches with different gating: **place-shaped ecology/settlements** (44-47, 61) satisfy
Idea 66's gate first; **material exploration/national expansion** (49-52) apply the Idea 66 gate only to
outcomes that authoritatively use Place identity/containment; **institutions/economic signals** (40, 41, 64)
are not globally blocked on Idea 66 at all. **M4 owns the `CultureDeriver`/`CulturalBiasApplicator`
activation** (plan-owner decision, 2026-08-29) as the single prerequisite shared with M5 (ideas 57, 62) and
M6 (idea 56), rather than each milestone wiring it independently.

### M5 — Memory, Reputation & Legacy (gated on M2 + M3)

**Tracking epic**: `TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION` (not yet created, scope-only).

8 ideas — inherited reputation, guilt by association, inherited feuds, drifting loyalty, the Living Legend
feedback loop, a dying wish, generational misremembering, emergent belief. Needs M2's Clan (36) and M3's
Reproduction (32) as real state to attach to. Three independent branches once their own prerequisites clear:
reputation (idea 60 before ideas 53/54), death and lineage (ideas 55/58, after Reproduction, heir
assignment, and correct death dispatch exist), and history/belief (idea 62 before idea 57, then idea 63).

**M5 owns the final-permadeath repair** (plan-owner decision, 2026-08-29 — a confirmed lifecycle
correctness defect, not part of M1's in-flight batch): combat already emits `PERMADEATH`, but
`LifecycleSystem.resolve_lifecycle()` only deactivates on `outcome_kind=="KILL"`, so a permadead entity
stays `active=True`. M5's death-and-lineage branch (55/58) already depends on "correct death dispatch"
existing — this repair is the prerequisite that makes that true, and belongs alongside it rather than in M1
or as an unowned bug.

### M6 — Political Identity & Belonging (gated on everything above)

**Tracking epic**: `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY` (not yet created, scope-only).

4 ideas, the deepest single dependency chain in the whole roadmap (39 &rarr; 56 &rarr; 59 &rarr; 65) —
affiliation's real change path, drifting loyalty, personal place attachment, refugee threads. Explicitly the
least-validated milestone: its Direction/Narrative scores are strong in the Merit Scorecard, but its Phase
Placement entry names a real, currently-unbuilt substrate (the history/culture-drift engine) as a shared
blocker with parts of M4 and M5. **Confirmed single contract** (plan-owner decision, 2026-08-29): idea 39
first establishes the affiliation mutation primitive; idea 56 derives gradual loyalty pressure that may
request/influence that mutation; ideas 59/65 add consequences after — idea 39 is not split into a separate
primitive/trigger pair. **M6 consumes M4's `CultureDeriver`/`CulturalBiasApplicator` activation** (idea 56's
blocker) rather than wiring it itself. City-specific wording in this milestone's scope should be read as the
Place model going forward, now that Idea 66 is promoted.

### M7 — Simulation Quality Pillar Integration (follow-up, gated on M1-M6)

**Tracking epic**: `TCK-20260823-EPIC-RPG-M7-SIMQ-INTEGRATION` (not yet created, scope-only — see
`docs/plans/rpg_design_roadmap/rpg_m7_simq_pillar_integration_epic.md`).

Not a new RPG feature — a consolidated audit-and-registration pass ensuring every real event type the other
milestones introduce actually gets registered into SimQ's per-pillar scoring rules, using the Merit
Scorecard's Pillar Reach axis (expanded from a count into named pillars first) as the checklist that nothing
gets missed. Deliberately sequenced as one follow-up epic after the rest of the roadmap ships, not
distributed as per-milestone acceptance criteria — see that epic's own Problem statement for why. **M7 is
not the first owner of missing event contracts** (plan-owner decision, 2026-08-29): each behavior-changing
feature ticket in M2-M6 should define its own authoritative update/observable event, a scenario that causes
it to fire, a SimQ pillar mapping (or explicit exclusion), and an observer-facing legibility path before that
ticket is considered done — M7 verifies completeness and calibrates the aggregate rules afterward, it
doesn't backfill missing contracts feature-ticket by feature-ticket.

### M8 — World Corpus, Generation & Modules (informs M1-M6, doesn't block them)

**Tracking epic**: `TCK-20260823-EPIC-RPG-M8-WORLD-CORPUS` (not yet created, scope-only — see
`docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md`).

Also not a new RPG feature — checks whether the real world-generation/compilation pipeline and the 6 named
test-corpus profiles actually have a place for each idea's content to enter a running world. Found two real
scope corrections (ideas 45 and 14 both need new schema/compiler work, deeper than originally scoped),
confirmed three corpus profiles already have what idea 44 needs with zero new authoring, and confirmed
ideas 39/51 and 32 can't be corpus-tested at all until their own upstream mechanisms exist. Unlike M7, this
one's findings feed directly back into M2/M3/M4's own scope — read it before, not after, those epics start
their affected tickets.

### M9 — World Corpus Test Coverage for New Features (follow-up, informs M1-M8, doesn't block them)

**Tracking epic**: `TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE` (not yet created, scope-only — see
`docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md`).

Also not a new RPG feature, and distinct from both M7 and M8: M7 asks whether SimQ knows how to *grade* an
event once it fires; M8 asks whether the compiler can *seed* an idea's content into a world at all. M9 asks
the question in between — once an idea ships, does a real SimQ corpus world (Unit/End-to-end/Stress/
Regression, per `docs/simulation_quality/corpus_tier_taxonomy.md`) actually exist to *exercise* it, or does
one need authoring. Classified all 32 stateful/behavioral ideas against the real corpus tier taxonomy, then
specified each one concretely on direct follow-up request — real world names, module compositions,
entity/region counts, trigger sequences, and assertable checks, not tier labels alone. Headline findings:
4 ideas (53, 55, 58, 62) can only be tested by a real multi-episode Campaign run, and
`CampaignScorecardEvaluator` itself has zero fields today that would even catch a failure in any of them —
a distinct test-infrastructure gap, not just a missing world; idea 66's Region/Place rebuild has
corpus-wide blast radius across all 21 worlds and 84 committed grade anchors, with a concrete 2-stage pilot
plan and a `state_hash`-based recalibration procedure now specified; the long-run observation tool's
default 5000-tick run would never even reach the real 7000-tick elder-attribute threshold idea 20 needs,
a timing bug that would have silently produced a false-negative test; and several ideas (32, 43, 48)
already have live SimQ scoring rules sitting idle, waiting only for the event to fire.



## Temporal axis (added dimension, 2026-08-28 brainstorm)

The existing model above describes the simulation across space and social containment
(`entity -> relationship/party -> Household/Clan -> Place -> faction -> world/campaign`). A brainstorm
proposal, [`docs/brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md`](../../brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md),
argues this is necessary but incomplete without a temporal direction, since an entity's lifecycle overlaps
immediate action, daily routine, seasonal development, annual path review, and generational succession all
at once. **This document does not itself approve implementation, change ticket scope, or edit any numeric
threshold** — it is a review-only brainstorm (explicit in its own scope constraint), reconciled here only to
the extent of recording which of its decisions are accepted-in-brainstorm versus still open.

**Accepted in this brainstorm pass** (directional, not yet implementation-authorized):
- Time is an overlapping axis, not another containment layer; entities, relationships, Households, Places,
  and institutions each have independent lifecycles crossing the same clock.
- Ordinary human days use recognizable real-world 24-hour behavior; one fantasy year is four 30-day seasons
  (120 days); a human ages one year per personal 120-day interval from birth (not the shared New Year).
- A tick is an advancement opportunity, not a synonym for "one action" — activity duration comes from a
  universal formula plus explicit, activity-scoped modifiers, not broad attribute-based time scaling.
- Entity life paths stay autonomous and deterministic-emergent (minor RPG cognition + major bounded rules);
  direct player control and time-control interfaces are explicitly deferred, not designed against here.
- Shared calendar/duration calculation should be reused across features; authoritative state and transition
  logic stay owned by their existing domains (M2-M6), not a new monolithic time engine.

**Still open, per the proposal's own §17** — not resolved by this review pass: exact human life-stage
boundaries and lifespan distribution; fantasy-calendar duration of pregnancy/recovery/education/
apprenticeship; whether the current tick length remains the final minor time quantum; modifier-stacking
rules; which processes first qualify for safe interval advancement. These require their own dedicated
balance/design-authority review before any M3+ ticket bakes in a specific number.

**Suggested integration, by milestone** (per the proposal's §13 — read as a lens on M2-M9, not a new
milestone or a mandate to start now):
- M2 features should declare their timing/spatial-reach assumptions (population, Place transitions,
  cognition, property, relationships) once ticketed.
- M3 owns concrete human/species lifecycle durations, fantasy-year aging, childhood, and the reproduction/
  coming-of-age arc's actual numbers (see M3 above).
- M4 owns seasonal settlement, economy, vacancy, apprenticeship, and travel cadence.
- M5 owns persistence, decay, testimony, generational transfer, and historical-memory horizons.
- M6 owns the time needed for affiliation, loyalty, attachment, and refugee identity to change.
- M7 should require temporal/observer legibility alongside machine (SimQ) visibility.
- M8 ensures calendar/lifecycle/routine/seasonal configuration can actually enter compiled worlds.
- M9 should add daily/seasonal/annual/lifespan/multi-generation scenario horizons, not rely on one fixed
  tick count (this roadmap's existing 5000-tick-run-can't-reach-elder-threshold finding, under "Known open
  items" below, is the same class of gap the proposal names in its own §9.7).

No ticket, epic acceptance criterion, or numeric threshold in this roadmap or its sibling epics is changed
by this section — it is a pointer for whoever next scopes M2-M9 ticket-level work, per the proposal's own
"maintainers should later review — not automatically edit" framing.

## Sequencing rules

- **M1 has no gate — it's ready today.** Nothing else in this roadmap blocks it, and nothing in M1 blocks on
  anything else. Its 21-ticket batch is already in flight and this roadmap's 2026-08-29 review deliberately
  left it unchanged (see M1 above) — the final-permadeath defect that surfaced alongside it is sequenced
  under M5, not folded into M1's batch.
- **M2 is the load-bearing milestone.** M3, M4, M5, and M6 all depend on at least one M2 idea landing first
  (see each milestone's own gate above) — this mirrors the atlas's own finding that M2's ideas are "cited
  by more downstream ideas than anything else."
- **M3 and M4 are independent of each other** once M2 clears — either can proceed first, or both in
  parallel.
- **M5 needs both M2 and M3.** **M6 needs effectively everything before it** — it's the one milestone this
  roadmap explicitly does not recommend starting early, even speculatively.
- **M7 gates on M1 through M6 as a whole, not on any single one of them.** It's a consolidated audit, not a
  feature — starting it early against a partial roadmap would mean re-running the same audit later against
  the rest, defeating the point of doing it once.
- **M8 is different from M7: read it early, not late.** It has no hard gate of its own, but its findings
  change M2's idea 14 ticket and M4's idea 45 ticket before they start, not after — treat M8 as a
  prerequisite read for whoever scopes those two specific tickets, even though the epic itself can run in
  parallel with anything.
- **Idea 66 (Region Contains Multiple Places, scoped under M8) is promoted (plan-owner decision, 2026-08-29)
  and is a real sequencing gate, not just a read.**
  Unlike the rest of M8, this is a foundational rebuild of the Region/City data model itself — City isn't a
  place inside a Region today, it IS a Region (`RegionSpec.bounds` is a single box; real world-modules
  contribute flat sibling regions with no containment). Idea 66 replaces that with a real `Place` hierarchy
  and directly subsumes ideas 45 (Camp) and 46 (Nest), reshapes idea 47 (Lair), and gives the previously-
  unscoped Ruins/Mines gap a home. **Recommendation: land idea 66 before ticketing M2's idea 35
  (sovereignty) or M4's ideas 45/46/47** — each of those would otherwise be built against the flat model and
  need reworking once (or if) idea 66 lands, the same rework M8's own idea-45 finding already flagged as a
  real cost once.
- **M9, like M8, should be read early rather than treated as a strict post-ship follow-up — but it's lighter
  than M7.** Most of its findings are cheap reuse ("idea 22 needs no new world, extend `highland_traverse`'s
  existing SOCIAL calibration"), not blocking scope corrections. Two exceptions are real gates: idea 66's
  ticket must budget a full `grade_anchors.json` recalibration pass across all 21 worlds as part of its own
  deliverable, not discover it mid-implementation when regression tests start failing corpus-wide; and ideas
  53/55/58/62 need a real multi-episode Campaign test plan decided before their tickets are scoped, since no
  static corpus world can exercise them at all.
- **Detailed child-ticket breakdown beyond M1 is deliberately not done yet.** M2 through M6 are scope-only
  epics for now — this roadmap and the sibling epic tickets exist to capture milestone structure and
  sequencing intent, not to fully plan implementation ahead of M1 shipping and M2's flag-governance
  precedent being set.
- **Content/balance validation is a real gate, not an afterthought, wherever Content & Balance Requirements
  flags an unanchored numeric decision.** The atlas's own content-risk table names idea 37 (M2, race-relations
  hostility matrix) as the single highest-risk unanchored number in the entire roadmap. Before idea 37's
  ticket is considered done, it must be run through `src/lab/metamorphic.py`'s real metamorphic-rule engine,
  not just pass a correctness test. **That tool has never been run against real content — zero recorded
  sessions in `data/lab_sessions/`.** Do not let idea 37 be the first real-world exercise of an unproven
  tool: M2's scope should include a small, low-stakes metamorphic-lab pilot (e.g. against an already-live,
  already-tuned numeric surface like `CampService`'s maturity constants) *before* idea 37's matrix is
  validated through it, so a tooling failure and a bad balance decision aren't discovered at the same time,
  on the highest-risk idea in the set.

## Known open items, inherited from the atlas (not re-litigated here)

- **Direction alignment (2026-08-24):** a full re-read of `the_unwritten_world.html`'s 8 principles against
  the Design Merit Scorecard's Direction Fit axis and this list itself, in
  `docs/plans/rpg_design_roadmap/rpg_direction_alignment_audit.md`. Headline: no idea contradicts a
  principle — drift found is by omission, not commission. Surfaced three more "idea 1"-shaped undersold
  fixes (ideas 3, 42, 17), tied five items already in this list to specific principles they weren't credited
  for, and found that idea 8 ("Prune or finish the dead cognition schema") already covers `core/cognition.py`
  — the source document's own named worked example of the Principle-7 failure mode — but its DF=0 score
  doesn't distinguish idea 8's principle-serving "finish" branch from its inert "prune" one. Named one
  candidate new idea (Living Relationship Decay) plus two scope extensions (idea 14's per-species logic, idea
  59/66's place-history tracking) — all drafted, none yet added to the atlas. Extended coverage to the
  Sequencing rules section, all 9 epic docs, the Simulation Wiring Map, and the Milestone Map found a real
  naming collision (idea 8's orphaned `core/cognition.py::SelfModel` vs. idea 9's live
  `core/self_model.py::SelfModelBundle`) and a gap in M7's own Acceptance Signal (SimQ-visibility isn't the
  same as in-world observer legibility) — both actionable, neither blocking.
- Idea 30 (Possessions With Personal History, part of no milestone above's critical path but flagged in
  Infrastructure Gaps) needs genuinely new per-instance-identity infrastructure this codebase doesn't have
  anywhere today — the one idea of 65 with no real precedent to build on.
- Three separate clusters (M4's settlement-personality idea, M5's history/belief cluster, M6's drifting-
  loyalty signal) all block on the identical dormant substrate (`CultureDeriver`/`CulturalBiasApplicator`),
  per Phase Placement & Testing Strategy — worth a single wiring ticket early rather than three separate
  discoveries later.
- The Design Merit Scorecard's own single-pass calibration (all 65 ideas scored in one batch) is unverified
  without an independent second read of a sample — noted, not blocking any milestone above.
- The real race roster is 13 entries (`data/content/living/races.yaml`), and `RaceDefinition` has no numeric
  field anywhere — only qualitative strings. Any idea introducing a new per-race numeric constant (idea 32's
  cooldowns, idea 37's matrix) is extending a schema that has never carried a number before, not following
  an established numeric-content pattern.
- **The 6 Mechanics Bible chapters have no social/relationship/reputation/political chapter.** Mapping all
  65 ideas against the Bible and the 8 parity ledger files (see the atlas's new Mechanics Bible & Parity
  Ledger Mapping section) found that `social_narrative.yaml` — the second-largest ledger, 265 entries — has
  no chapter home at all, affecting roughly a third of the roadmap's ideas. Whoever scopes a ticket touching
  Clan, faction diplomacy, Chronicle, grief/nemesis, or reputation should expect to update the ledger entry
  with no corresponding Bible chapter section to point it at — that gap is not a defect in any single idea's
  ticket, it's a standing hole in the Bible's own structure worth its own follow-up ticket eventually. Idea
  39 (M6, affiliation change) is the single widest cross-ledger idea in the whole set (5 of 8 ledger files);
  ideas 53/54/60 all touch `entity.social.public_reputation`, which is included in the deterministic replay
  hash (`replay/fingerprint.py`) — a determinism concern layered on top of the ordinary parity-ledger one.
- **Cross-epic file-conflict check (2026-08-17): no near-term risk.** This roadmap's only PR so far changes
  zero `src/`/`tests/` files and nothing is ticketed yet, so there is nothing to conflict with today. The one
  real historical near-hit — a merged `worldgen-organic-terrain` epic that touched `src/worldbuilding/compiler.py`,
  the exact file M8 (World Corpus/Generation) centers on — already landed and settled before M8's own
  investigation was written, so M8's picture of that file is accurate, not stale. Re-run this check
  specifically against `src/worldbuilding/compiler.py` when M8 actually gets ticketed — it's a contended,
  high-blast-radius file for world-gen work generally, not just for this roadmap.
- **"Done" isn't the same as tested, content-reachable, balance-checked, or SimQ-visible.** Four parallel
  audits of the 37 `done`-badged existing mechanics (new Depth Beneath "Done" atlas section) found real gaps
  on three of four axes not owned by any of the 65 ideas: the `CHURCH` building's Blessing/Resurrection
  services are fully coded and placed in zero worlds; `ReputationService` has zero tests despite a done
  badge that conflates it with a different, tested class; and four content categories (Sense/Drive/Need/
  Cognition profiles, 6-7 entries each) cap the real behavioral range of three done, live mechanics. None of
  these block any milestone above, but whoever picks up a ticket touching Reputation, Perception, Goal
  Hierarchy, or town Buildings should read that section first — the badge alone will overstate confidence.
- **Idea 66 surfaced a real process gap: prose descriptions of proposed state let ambiguity slip through
  that a schema would have caught.** `docs/brainstorm/rpg_expected_schemas.html` (page titled "RPG Schema
  Registry" — the tracking page for every RPG feature's schema, current and planned) gives field-level
  schemas — not prose — for all 30 proposed ideas that introduce new durable state, the *existing* live
  schemas for every layer (Entity, Group/Guild, Faction, Region, Camp, World, World Objects, Clan/Race —
  even fields with no proposed change), and a third dimension: ~13 hardcoded/flat values already in the live
  codebase (`readiness_speed=10.0`, `max_perceived=10`, the sovereignty ownership-flip constants,
  `RecipeRegistry`'s 3-recipe dict) that behave like schema-driven state but are Python literals today, most
  with no idea currently targeting them. Three proposed schemas (ideas 30, 60, 63) are marked explicitly as
  genuinely underspecified rather than presenting invented fields as settled. Whoever scopes a ticket for
  any idea — new state or a change to existing state — should start from that document, not re-derive field
  shapes from the atlas's prose.
- **Two real bugs found this session, neither of the 66 design ideas.** (1) Generation-4+ Hero "permadeath"
  doesn't actually work: `combat.py` sets `outcome_kind="PERMADEATH"`, but
  `LifecycleSystem.resolve_lifecycle()` only deactivates an entity on `outcome_kind=="KILL"` — a "permadead"
  Hero stays `active=True` and keeps acting in the simulation (see the Simulation Wiring Map's T14). Expected
  fix: route `"PERMADEATH"` through the same deactivation check as `"KILL"`. **Now has an explicit home: M5
  (2026-08-29 review), alongside its death-and-lineage branch** — see M5 above. Not part of M1's in-flight
  batch. (2) `docs/mechanics/README.md` line 77 is stale — it still describes idea 15's wound-threshold
  question as an open divergence ("Chapter 02 requires correction") after the real parity ledger entry
  (`COMB-290`) was already fixed to `status: verified` and ch02 already corrected; a small doc-only hotfix,
  independent of this roadmap's own milestones — file as its own bug when picked up.
- **Two design gaps flagged repeatedly across multiple passes, not yet resolved by any of them.** Idea 63
  (Belief/Religion) has come back "too underspecified to be concrete" in the schema, event, and
  data-configuration passes alike — worth its own dedicated ideation/grounding session before it's touched
  again as a side note. Idea 37's race-diversity corpus gap (no registry dimension tracks race composition
  per world, M9's own finding) still has no owner. Neither blocks anything shipping today; both will keep
  resurfacing as a caveat on someone else's finding until addressed directly.
- **One possible duplicate system, not yet reconciled.** `get_age_bracket()`'s string-based age tiers
  (young/adult/elder, `cohort.py`) and `LifeStage`'s enum (CHILD/ADULT/ELDER, `IdentityComponent`) may be two
  overlapping representations of the same concept — flagged in M9, not resolved there or here. Whoever scopes
  idea 20 should settle this first, not discover it mid-ticket.

## References

- `docs/brainstorm/rpg_feature_atlas.html` (all sections cited above)
- `docs/brainstorm/rpg_expected_schemas.html` ("RPG Schema Registry" — existing + proposed schemas for every layer)
- `docs/brainstorm/rpg_simulation_wiring_map.html` ("Simulation Wiring Map" — high-level layer model and
  wiring diagram: Entity/Group/Faction/Region/World/World Objects, expected/current/proposed status per
  connection, plus an Entity-level operating-loop and lifecycle-arc drill-down)
- `docs/brainstorm/design_merit_scorecard.html`
- `docs/brainstorm/the_unwritten_world.html`
- `docs/brainstorm/simulation_capabilities.html` (plain-language companion, for non-technical review)
- `docs/plans/live_map_scaling_roadmap.md`, `docs/plans/hud_design_system_foundation_epic.md`'s sibling-epic
  roadmap (the two structural precedents this doc follows)
- `docs/plans/rpg_design_roadmap/rpg_direction_alignment_audit.md` (direction-level cross-check of this
  roadmap against the 8 principles, 2026-08-24)
- `docs/brainstorm/codex/2026-08-27-core-rpg-plan-brainstorm-update-request.md` (documentation-consistency
  review this roadmap reconciled against, 2026-08-29 — also see its sibling
  `2026-08-27-brainstorm-plan-crosswalk-review.md`, `2026-08-27-core-rpg-feature-review.md`, and
  `2026-08-27-core-rpg-new-idea-portfolio.md`)
- `docs/brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md` (the temporal-axis dimension added
  above, review-only — see "Temporal axis")
- `docs/simulation_quality/corpus_tier_taxonomy.md` — the real Unit/End-to-end/Stress/Regression corpus
  framework M9 classifies all 32 stateful ideas against, rather than reinventing
