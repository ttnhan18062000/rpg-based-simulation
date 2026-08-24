---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content]
---

# Roadmap — RPG Design Ideas: From Brainstorm to Six Epics

**Purpose**: `docs/brainstorm/rpg_feature_atlas.html` (Rev 60+) contains 65 fully-investigated RPG design
ideas, already sequenced (Suggested Build Order), grouped into 6 milestones (Roadmap section), classified
by implementation pattern and flag-risk (Implementation Patterns), traced for real-code blast radius
(Cross-Cutting Risk), checked for consolidation opportunities (Shared Implementation Opportunities), and
mapped to real pipeline phases with proposed arena-style tests (Phase Placement & Testing Strategy). This
doc is the bridge from that brainstorm-tier investigation into this repo's real epic-tier planning format —
it does not re-derive any of that grounding, it routes to it.

**This is genuinely large enough that one epic can't hold it cleanly** — 65 ideas, 6 milestones, several
long dependency chains. Following the same pattern already used for the live-map and HUD design-system
efforts: one roadmap doc stating the sequencing/gating rule once, one milestone epic fully scoped and ready
to ticket, and five sibling epics kept scope-only until the milestones before them actually ship.

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

### M1 — Quick Wins & Housekeeping (ready to ticket now)

**Tracking epic**: `TCK-20260823-EPIC-RPG-M1-QUICK-WINS` (not yet created — see
`docs/plans/rpg_m1_quick_wins_epic.md`, fully scoped, 20 ideas).

No dependencies on anything else in this roadmap. Finishes half-built mechanisms, resolves 5 formerly-open
technical questions (now answered), and fixes 2 confirmed real bugs. The atlas's own Roadmap section
estimates this lands as roughly 18 tickets once idea 1's own checklist folds 2 items into ideas 26/32.

### M2 — Foundational Systems (gated on M1's flag-governance decision, idea 9)

**Tracking epic**: `TCK-20260823-EPIC-RPG-M2-FOUNDATIONAL-SYSTEMS` (not yet created, scope-only — new
sibling epic).

16 ideas, no dependencies on each other but the highest-leverage tier in the whole set — Species
Classification (14), City ownership (35), Clan's shape (36), population seeding (43), and place-type
transitions (48) are each cited as prerequisites by multiple downstream ideas. **Gate**: idea 9 (deciding
the fate of 8 already-built rollout flags) should land first — several M2 ideas are exactly the kind of
new-flagged-mechanism idea 9's own governance decision is meant to set precedent for.

### M3 — Family, Species & the Adult Life (gated on M2)

**Tracking epic**: `TCK-20260823-EPIC-RPG-M3-FAMILY-SPECIES` (not yet created, scope-only).

5 ideas — reproduction, marriage, coming of age, dependents, closing the population-pressure loop. Hard
dependency on M2's Species Classification (14) and population seeding (43) landing first, confirmed
directly in the atlas's Cross-Cutting Risk section.

### M4 — Beyond the City & the Layer Model (gated on M2)

**Tracking epic**: `TCK-20260823-EPIC-RPG-M4-BEYOND-CITY` (not yet created, scope-only).

12 ideas — Camp/Nest/Lair, settlement-capacity, Country's EXPAND directive, population pressure as an
expansion engine. Gated on M2's City ownership (35), Clan shape (36), and place-type transitions (48).

### M5 — Memory, Reputation & Legacy (gated on M2 + M3)

**Tracking epic**: `TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION` (not yet created, scope-only).

8 ideas — inherited reputation, guilt by association, inherited feuds, drifting loyalty, the Living Legend
feedback loop, a dying wish, generational misremembering, emergent belief. Needs M2's Clan (36) and M3's
Reproduction (32) as real state to attach to.

### M6 — Political Identity & Belonging (gated on everything above)

**Tracking epic**: `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY` (not yet created, scope-only).

4 ideas, the deepest single dependency chain in the whole roadmap (39 &rarr; 56 &rarr; 59 &rarr; 65) —
affiliation's real change path, drifting loyalty, personal place attachment, refugee threads. Explicitly the
least-validated milestone: its Direction/Narrative scores are strong in the Merit Scorecard, but its Phase
Placement entry names a real, currently-unbuilt substrate (the history/culture-drift engine) as a shared
blocker with parts of M4 and M5.

### M7 — Simulation Quality Pillar Integration (follow-up, gated on M1-M6)

**Tracking epic**: `TCK-20260823-EPIC-RPG-M7-SIMQ-INTEGRATION` (not yet created, scope-only — see
`docs/plans/rpg_m7_simq_pillar_integration_epic.md`).

Not a new RPG feature — a consolidated audit-and-registration pass ensuring every real event type the other
six milestones introduce actually gets registered into SimQ's per-pillar scoring rules, using the Merit
Scorecard's Pillar Reach axis (expanded from a count into named pillars first) as the checklist that nothing
gets missed. Deliberately sequenced as one follow-up epic after the rest of the roadmap ships, not
distributed as per-milestone acceptance criteria — see that epic's own Problem statement for why.

### M8 — World Corpus, Generation & Modules (informs M1-M6, doesn't block them)

**Tracking epic**: `TCK-20260823-EPIC-RPG-M8-WORLD-CORPUS` (not yet created, scope-only — see
`docs/plans/rpg_m8_world_corpus_generation_epic.md`).

Also not a new RPG feature — checks whether the real world-generation/compilation pipeline and the 6 named
test-corpus profiles actually have a place for each idea's content to enter a running world. Found two real
scope corrections (ideas 45 and 14 both need new schema/compiler work, deeper than originally scoped),
confirmed three corpus profiles already have what idea 44 needs with zero new authoring, and confirmed
ideas 39/51 and 32 can't be corpus-tested at all until their own upstream mechanisms exist. Unlike M7, this
one's findings feed directly back into M2/M3/M4's own scope — read it before, not after, those epics start
their affected tickets.

## Sequencing rules

- **M1 has no gate — it's ready today.** Nothing else in this roadmap blocks it, and nothing in M1 blocks on
  anything else.
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
- **Idea 66 (Region Contains Multiple Places, scoped under M8) is a real sequencing gate, not just a read.**
  Unlike the rest of M8, this is a foundational rebuild of the Region/City data model itself — City isn't a
  place inside a Region today, it IS a Region (`RegionSpec.bounds` is a single box; real world-modules
  contribute flat sibling regions with no containment). Idea 66 replaces that with a real `Place` hierarchy
  and directly subsumes ideas 45 (Camp) and 46 (Nest), reshapes idea 47 (Lair), and gives the previously-
  unscoped Ruins/Mines gap a home. **Recommendation: land idea 66 before ticketing M2's idea 35
  (sovereignty) or M4's ideas 45/46/47** — each of those would otherwise be built against the flat model and
  need reworking once (or if) idea 66 lands, the same rework M8's own idea-45 finding already flagged as a
  real cost once.
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

## References

- `docs/brainstorm/rpg_feature_atlas.html` (all sections cited above)
- `docs/brainstorm/rpg_expected_schemas.html` ("RPG Schema Registry" — existing + proposed schemas for every layer)
- `docs/brainstorm/design_merit_scorecard.html`
- `docs/brainstorm/the_unwritten_world.html`
- `docs/brainstorm/simulation_capabilities.html` (plain-language companion, for non-technical review)
- `docs/plans/live_map_scaling_roadmap.md`, `docs/plans/hud_design_system_foundation_epic.md`'s sibling-epic
  roadmap (the two structural precedents this doc follows)
