# Brainstorm-to-Plan Crosswalk Review

Date: 2026-08-27  
Scope: read-only review of `docs/brainstorm/` and its downstream `docs/plans/` and ticket artifacts  
Constraint: this review does not modify or supersede any existing brainstorm, plan, or ticket document

Evidence baseline: repository `HEAD` `2af384ff` (2026-08-26T01:02:33+07:00), inspected on 2026-08-27. Git tracking statements and source-code claims in this review describe that baseline plus the then-current working tree.

Status terms used here:

- **Promoted** — a brainstorm finding is named and scoped in a plan or ticket. Promotion does not by itself mean the artifact is tracked, approved, or durable.
- **Scope-only** — a plan exists, but no tracking/child tickets for its implementation were found.
- **Ticketed** — concrete files exist under `tickets/`; this does not mean implementation has started.
- **Tracked/committed** — Git knows the file at the evidence baseline.
- **Untracked** — the file exists in the working tree but is not in Git.
- **Executable ordering authority** — a committed ticket sequence consumed by the implementation workflow; it does not imply that every ticket is dependency-ready at the same time.

## Executive conclusion

The brainstorm collection has already produced two substantial planning programs:

1. The RPG design branch is durable and mostly promoted. All original 65 numbered ideas have a milestone home in M1-M6, idea 66 is provisionally referenced through M8/M9 but has unresolved formal ownership, and M1 has already been decomposed into 21 ordered child tickets.
2. The simulation-architecture branch has been promoted into a design-enhancement roadmap and three scoped epic plans, but the two source brainstorm files and the entire downstream plan directory are currently untracked.

The existing brainstorm documents should remain unchanged for now. Their historical correction notes and revision trail are useful evidence. Where they are stale, this document should act as the crosswalk rather than silently rewriting the investigation record.

Updates are nevertheless advisable in the downstream planning layer before implementation continues. The highest-priority corrections are the stale M1 “not yet ticketed” language, idea 66's ambiguous milestone ownership, and the lack of a ticket/plan for the verified permadeath lifecycle defect.

## Canonical reading order

### RPG design branch

1. [`the_unwritten_world.html`](../the_unwritten_world.html) — creative direction and eight governing principles.
2. [`rpg_feature_atlas.html`](../rpg_feature_atlas.html) — implementation-grounded capability audit and ideas 1-66.
3. [`design_merit_scorecard.html`](../design_merit_scorecard.html) — seven-axis evaluation for ideas 1-65.
4. [`rpg_expected_schemas.html`](../rpg_expected_schemas.html) — existing and proposed durable-state shapes, configuration choices, and expected events.
5. [`rpg_simulation_wiring_map.html`](../rpg_simulation_wiring_map.html) — system topology and lifecycle transitions.
6. [`rpg_design_roadmap.md`](../../plans/rpg_design_roadmap/rpg_design_roadmap.md) — milestone sequencing and promotion boundary.
7. [`rpg_direction_alignment_audit.md`](../../plans/rpg_design_roadmap/rpg_direction_alignment_audit.md) — independent direction/omission review.
8. The milestone plans: [M1](../../plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md), [M2](../../plans/rpg_design_roadmap/rpg_m2_foundational_systems_epic.md), [M3](../../plans/rpg_design_roadmap/rpg_m3_family_species_epic.md), [M4](../../plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md), [M5](../../plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md), [M6](../../plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md), [M7](../../plans/rpg_design_roadmap/rpg_m7_simq_pillar_integration_epic.md), [M8](../../plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md), and [M9](../../plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md).

`entity_capabilities.html` and `simulation_capabilities.html` are presentation companions. They should not be used as planning authorities where they differ from the atlas or schema registry.

### Architecture/performance branch

1. [`simulation_design_taxonomy.html`](../simulation_design_taxonomy.html) — architecture classification and genuine gaps.
2. [`performance_evolution_roadmap.html`](../performance_evolution_roadmap.html) — optimization ideas checked against current implementation.
3. [`design_enhancement_roadmap.md`](../../plans/design_enhancement/design_enhancement_roadmap.md) — consolidated program and priority order.
4. [`determinism_envelope_epic.md`](../../plans/design_enhancement/determinism_envelope_epic.md).
5. [`subphase_domain_contracts_epic.md`](../../plans/design_enhancement/subphase_domain_contracts_epic.md).
6. [`performance_milestones_epic.md`](../../plans/design_enhancement/performance_milestones_epic.md).

## Brainstorm-to-plan crosswalk

| Brainstorm artifact | Material promoted into plans | Current downstream state | Review disposition |
|---|---|---|---|
| `the_unwritten_world.html` | Direction constraints for the full RPG roadmap | Explicitly audited in [`rpg_direction_alignment_audit.md`](../../plans/rpg_design_roadmap/rpg_direction_alignment_audit.md) | No source update needed. Use the direction audit for omissions and proposed extensions. |
| `rpg_feature_atlas.html` | Ideas 1-65 into M1-M6; idea 66 into M8/M9 | M1 has 21 child tickets; M2-M9 remain scope-only | No source rewrite. Planning metadata needs reconciliation, especially M1 state and idea 66 ownership. |
| `design_merit_scorecard.html` | Priority and risk inputs for M1-M7 and the direction audit | Ideas 1-65 scored; idea 66 explicitly unscored | Update only if the scorecard is still used for prioritization. Add idea 66 and preserve the existing no-composite-score rule. |
| `rpg_expected_schemas.html` | Schema/event expectations referenced by the roadmap and M9 | Used as planning input for stateful ideas and corpus tests | No immediate source update. Clarify its “30 ideas introducing durable state” versus M9's broader “32 stateful/behavioral ideas” terminology during ticket scoping; these are different sets, not proven counts of the same unit. |
| `rpg_simulation_wiring_map.html` | Lifecycle and system-boundary evidence used by the direction audit | Mostly advisory; one verified lifecycle defect remains unplanned | Preserve as evidence. Promote the permadeath defect into a ticket rather than editing the map first. |
| `simulation_capabilities.html` | Plain-language context cited by the RPG roadmap | Not an implementation authority | No update required unless it remains a public-facing/current-state page. If maintained, regenerate it from the atlas rather than editing manually. |
| `entity_capabilities.html` | Earlier entity-only subset | Superseded in scope by `simulation_capabilities.html`; five card descriptions differ | Marking it superseded would help, but no change is required if it is intentionally a historical snapshot. Do not plan from it. |
| `simulation_design_taxonomy.html` | Design-enhancement roadmap, determinism-envelope work, subphase contracts | Promoted, but source and plans are untracked | Content is usable. Durability/source-control status must be resolved before treating it as an active program. |
| `performance_evolution_roadmap.html` | Performance epic M1-M4 and revised priority order | Promoted, but source and plans are untracked | Content is usable. Track the source and plan set together or explicitly keep the whole branch experimental. |

## RPG idea promotion map

The original 65 ideas are completely assigned across the first six milestones:

| Milestone | Ideas | Count | Promotion state |
|---|---|---:|---|
| M1 — Quick Wins & Housekeeping | 1, 3, 7, 9, 10, 12, 13, 15-22, 24-26, 29, 42 | 20 | The scope produced 21 child tickets for 19 ideas; idea 16 was resolved by investigation without a behavior-change ticket. |
| M2 — Foundational Systems | 2, 4, 5, 6, 8, 11, 14, 23, 27, 28, 30, 35, 36, 37, 43, 48 | 16 | Scope-only epic plan. Gated on M1's rollout-flag decision. |
| M3 — Family, Species & Adult Life | 31, 32, 33, 34, 38 | 5 | Scope-only epic plan. Hard-gated on ideas 14 and 43. |
| M4 — Beyond the City & Layer Model | 40, 41, 44-47, 49-52, 61, 64 | 12 | Scope-only epic plan. Its place work is now affected by idea 66. |
| M5 — Memory, Reputation & Legacy | 53, 54, 55, 57, 58, 60, 62, 63 | 8 | Scope-only epic plan. Depends on Clan and Reproduction state. |
| M6 — Political Identity & Belonging | 39, 56, 59, 65 | 4 | Scope-only epic plan. Deepest chain: 39 -> 56 -> 59 -> 65. |

Supporting milestones:

- M7 is the SimQ integration/audit pass for events introduced by M1-M6.
- M8 covers world corpus/generation and now also carries idea 66.
- M9 covers corpus test reachability and explicitly accounts for idea 66's migration blast radius.

Idea 66 is not part of the original 65-idea partition. It is more than an M8 corpus concern: it changes the Region/City/Place state model and gates M2 idea 35 and M4 ideas 45-47. Before those tickets are created, planning should decide whether idea 66 becomes a prerequisite architecture epic of its own or remains formally owned by M8 with explicit cross-milestone blocking edges.

## Items that already became actionable tickets

M1's 20-idea scope produced 21 tickets: 19 ideas were ticketed, idea 16 was closed by investigation without an implementation ticket, and ideas 7 and 17 were split by responsibility. The committed `tickets/todos/m1-quick-wins/SEQUENCE.md` is now the executable ordering authority for this batch.

The relationship is not one idea to one ticket:

| Atlas idea | Child ticket(s) or disposition |
|---|---|
| 1 — Wire orphaned mechanisms | [`TCK-20260824-WIRE-ORPHANED-MECHANISMS`](../../../tickets/todos/m1-quick-wins/TCK-20260824-WIRE-ORPHANED-MECHANISMS.md) |
| 3 — Breakthrough bonuses | [`TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION`](../../../tickets/todos/m1-quick-wins/TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION.md) |
| 7 — Grief/Nemesis reachability and protection | [`TCK-20260824-GRIEF-NEMESIS-REACHABILITY`](../../../tickets/todos/m1-quick-wins/TCK-20260824-GRIEF-NEMESIS-REACHABILITY.md), [`TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS`](../../../tickets/todos/m1-quick-wins/TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS.md) |
| 9 — Rollout flags | [`TCK-20260824-ROLLOUT-FLAG-DECISIONS`](../../../tickets/todos/m1-quick-wins/TCK-20260824-ROLLOUT-FLAG-DECISIONS.md) |
| 10 — Assign heirs | [`TCK-20260824-DEFAULT-HEIR-ASSIGNMENT`](../../../tickets/todos/m1-quick-wins/TCK-20260824-DEFAULT-HEIR-ASSIGNMENT.md) |
| 12 — Lead contradiction wiring | [`TCK-20260824-LEAD-CONTRADICTION-WIRING`](../../../tickets/todos/m1-quick-wins/TCK-20260824-LEAD-CONTRADICTION-WIRING.md) |
| 13 — Affection/contract gate | [`TCK-20260824-AFFECTION-CONTRACT-GATE`](../../../tickets/todos/m1-quick-wins/TCK-20260824-AFFECTION-CONTRACT-GATE.md) |
| 15 — Wound-threshold question | [`TCK-20260824-WOUND-THRESHOLD-DECISION`](../../../tickets/todos/m1-quick-wins/TCK-20260824-WOUND-THRESHOLD-DECISION.md) |
| 16 — Ranger-doctrine question | No implementation ticket; the investigation resolved the question without requiring a behavior change. |
| 17 — Wound/scar mechanics | [`TCK-20260824-WOUND-PENALTY-FORMULA-WIRING`](../../../tickets/todos/m1-quick-wins/TCK-20260824-WOUND-PENALTY-FORMULA-WIRING.md), [`TCK-20260824-WOUND-HEALING-DECISION`](../../../tickets/todos/m1-quick-wins/TCK-20260824-WOUND-HEALING-DECISION.md) |
| 18 — Route-kind count | [`TCK-20260824-ROUTE-KIND-COUNT-FIX`](../../../tickets/todos/m1-quick-wins/TCK-20260824-ROUTE-KIND-COUNT-FIX.md) |
| 19 — `ALLOCATE_AP` reachability | [`TCK-20260824-ALLOCATE-AP-BRANCH-DECISION`](../../../tickets/todos/m1-quick-wins/TCK-20260824-ALLOCATE-AP-BRANCH-DECISION.md) |
| 20 — Life-stage transitions | [`TCK-20260824-LIFE-STAGE-TRANSITIONS`](../../../tickets/todos/m1-quick-wins/TCK-20260824-LIFE-STAGE-TRANSITIONS.md) |
| 21 — Careers/occupation changes | [`TCK-20260824-OCCUPATION-CHANGE-TRIGGER`](../../../tickets/todos/m1-quick-wins/TCK-20260824-OCCUPATION-CHANGE-TRIGGER.md) |
| 22 — Relationship roles | [`TCK-20260824-RELATIONSHIP-ROLE-FIELD`](../../../tickets/todos/m1-quick-wins/TCK-20260824-RELATIONSHIP-ROLE-FIELD.md) |
| 24 — Personal economy | [`TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK`](../../../tickets/todos/m1-quick-wins/TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK.md) |
| 25 — Secrets/disclosure | [`TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ`](../../../tickets/todos/m1-quick-wins/TCK-20260824-SECRETS-DISCLOSURE-SCOPE-SEQ.md) |
| 26 — Causal memory consumer | [`TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING`](../../../tickets/todos/m1-quick-wins/TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING.md) |
| 29 — Wound-aware tactics | [`TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`](../../../tickets/todos/m1-quick-wins/TCK-20260824-TACTICAL-WOUND-SCAR-WIRING.md) |
| 42 — Town-center bug | [`TCK-20260824-TOWN-CENTER-POINTER-FIX`](../../../tickets/todos/m1-quick-wins/TCK-20260824-TOWN-CENTER-POINTER-FIX.md) |

See the committed [`SEQUENCE.md`](../../../tickets/todos/m1-quick-wins/SEQUENCE.md) for the actual dependency ordering. The table above explains traceability, not scheduling.

This means the following language is stale in both `rpg_design_roadmap.md` and `rpg_m1_quick_wins_epic.md`:

- “ready to ticket”
- “tracking epic not yet created”
- “scope for the eventual create-tickets pass”
- “not created yet — this epic is scope-only”

The absence of a tracking-epic ticket may still be intentional, but the child-ticket creation has definitely happened. Future plan maintenance should distinguish “tracking epic absent” from “child tickets absent”; they are no longer the same state.

## Brainstorm findings not yet represented cleanly in plans

### Verified permadeath defect

The Wiring Map reports that a generation-4+ hero receives `outcome_kind="PERMADEATH"`, while `LifecycleSystem.resolve_lifecycle()` deactivates only `outcome_kind=="KILL"`. Current source still has this mismatch. The entity remains lifecycle-active, succession does not run, and the permadeath flag has no downstream consumer.

Evidence at the review baseline: `src/engine/combat.py:188` and `:413` emit `PERMADEATH`; `src/systems/lifecycle_systems/lifecycle.py:43` recognizes only `KILL` for combat deactivation. Succession begins inside that same `if is_dead` block at `lifecycle.py:58`, so the unmatched outcome bypasses it. A repository search for `is_permadeath` found state/schema, propagation, apply, serialization, and test references, but no production conditional consumer after the flag is stored.

Disposition: create a focused lifecycle/combat repair ticket. Do not bury this inside a speculative RPG milestone.

### Living relationship decay

The direction audit identifies passive trust/grudge evolution between two living characters as a genuine unnumbered gap. Ideas 55 and 56 cover inherited feud and political drift, not this behavior.

Disposition: keep as a candidate idea until its owning relationship schema is settled; then either add it to the atlas or scope it directly from the direction audit through the normal ticket workflow.

### Historical place memory

Ideas 48, 59, and 66 model current place type, home pointer, and Region/Place structure. They do not yet provide a transformation or prior-owner history sufficient to express repeatedly moved borders, a city that changed hands several times, or an entity grieving a home whose identity later changed.

Disposition: resolve as acceptance-criteria extensions during idea 66/59 design, rather than creating another parallel place-state system.

### Observer legibility

M7 can register events with SimQ without making those events understandable to an in-world character or external observer. The direction audit already distinguishes telemetry visibility from narrative legibility.

Disposition: when M7 is refreshed, require each new feature to name either a Chronicle, rumor, reputation, UI, or other observer-facing surfacing path, or explicitly justify why none is needed.

### Cognition-model collision

The direction audit found two differently implemented “self-model” concepts: the gated live `SelfModelBundle` path and the orphaned `core/cognition.py::SelfModel` family. Ideas 8 and 9 refer to different systems but M1/M2 planning can easily conflate them.

Disposition: add a disambiguation note during the next plan or ticket-scoping pass; do not merge their decisions by name alone.

## Architecture/performance promotion map

The architecture brainstorm branch has already been decomposed appropriately:

| Promoted concern | Plan home | Gate/status |
|---|---|---|
| Wall-clock/load-driven `RuntimeMode` changes the reproducibility envelope | `determinism_envelope_epic.md` | Should precede performance work that assumes a determinism guarantee. Scope-only. |
| The 37 Resolution subphases lack machine-checkable read/write/emit contracts | `subphase_domain_contracts_epic.md` | Hard prerequisite for the proposed Resolution job graph. Scope-only. |
| Measurement, spatial decomposition, narrow DOD projections, memoization, hashing, job graph, aggregate simulation | `performance_milestones_epic.md` | Four ordered milestones; measurement first, fidelity-changing aggregation last. Scope-only. |
| Checkpoint experimentation, resilience audit, interest-management cross-reference, API/security boundaries | `design_enhancement_roadmap.md` | Consolidated roadmap; not yet ticketed. |

The content decomposition is healthy. The current issue is durability: `git status --short` at the review baseline reported both source HTML files and the entire `docs/plans/design_enhancement/` directory as untracked. They should be committed as one coherent program or kept explicitly experimental; mixing untracked sources with `status: active` plan frontmatter is ambiguous.

## Recommended update queue

This queue describes future maintenance; this review does not apply any of it.

### Priority 0 — planning correctness

1. Reconcile M1's roadmap/epic status with the 21 committed child tickets.
2. Decide formal ownership for idea 66 before creating M2 idea 35 or M4 idea 45-47 tickets.
3. Create a focused ticket for the verified permadeath lifecycle defect.
4. Decide whether the untracked architecture/performance program is durable or experimental.

### Priority 1 — cross-document consistency

1. Score idea 66 if the Merit Scorecard remains a prioritization input.
2. Distinguish the two self-model systems in downstream plans.
3. Add observer-legibility acceptance to M7 when it is next revised.
4. Clarify that “30 ideas introducing durable state” and M9's broader “32 stateful/behavioral ideas” count different sets; reconcile the wording only if readers are expected to compare the figures.

### Priority 2 — hygiene

1. Treat `simulation_capabilities.html` as the current plain-language view and `entity_capabilities.html` as a subset/snapshot.
2. Correct stale `CLAUDE.md` terminology, the old race-catalog path, and unavailable scratch-source references when those documents are next regenerated.
3. If the HTML collection remains authoritative, move its structured data into reviewable source files and generate the rendered HTML to avoid giant one-line JavaScript payloads.

## Update decision by document

| Document or plan | Timing | Reason |
|---|---|---|
| Existing source files in `docs/brainstorm/` | Preserve now | Preserve the investigation/revision record; use this crosswalk to document promotion and drift. Conditional future regeneration is hygiene, not a current request. |
| `rpg_design_roadmap.md` | Update before further milestone execution | M1 ticket state is stale and idea 66's ownership remains structurally ambiguous. |
| `rpg_m1_quick_wins_epic.md` | Update before running the epic | Its create-tickets state no longer matches the committed child-ticket folder. |
| M2/M4 epic plans | Update when creating affected tickets | They must consume the idea 66 decision before affected tickets are scoped. |
| M7 epic plan | Update during implementation planning | Add observer-legibility alongside SimQ registration. |
| M8/M9 epic plans | Update after the idea 66 ownership decision | Keep corpus responsibilities, but avoid making M8 appear to be the sole owner of a cross-cutting state-model migration unless that is deliberate. |
| `docs/plans/design_enhancement/` | Resolve Git tracking before content edits | The program is coherent but entirely untracked. |

## Evidence notes for lower-priority hygiene findings

- The five differing card descriptions between `entity_capabilities.html` and the corresponding prefix of `simulation_capabilities.html` are Genetic Variation, Growing Into a Stronger Form, Occupation & Social Role, A Second/Larger Mental Model, and Asking Specific People for Information.
- `simulation_design_taxonomy.html:1041` and `rpg_expected_schemas.html:598,729` still refer to project rules through `CLAUDE.md`; the repository's current generated instruction entry point is `AGENTS.md`.
- The Race-layer card embedded in `rpg_feature_atlas.html:1109` cites `data/content/entities/race_definitions.yaml`; the live catalog is `data/content/living/races.yaml`.
- `rpg_feature_atlas.html:744` cites absent `docs/brainstorm/settlement_tiers_genre_brief.txt`. The taxonomy and performance pages also disclose unavailable session-local `tmp/` source/review notes.

## Boundary for future work

This review is a navigation and freshness layer, not a replacement source of mechanics or architecture truth. Implementation work should continue to use the authoritative engine pipeline, Mechanics Bible, parity ledger, live source, and scoped ticket investigation. When this review disagrees with a live code read, the live code plus authoritative documentation wins and the discrepancy should be recorded during ticket investigation.
