# Core RPG Review — Plan and Brainstorm Update Request

Date: 2026-08-27  
Status: proposed documentation update  
Scope: the core RPG brainstorm corpus and the M1-M9 RPG design roadmap  
Constraint: this document requests changes; it does not itself supersede or modify the source documents

## Request

Update the current RPG brainstorm and roadmap documents so that they reflect the repository state and dependency findings recorded in the [Core RPG Feature Review](2026-08-27-core-rpg-feature-review.md) and the [Brainstorm-to-Plan Crosswalk](2026-08-27-brainstorm-plan-crosswalk-review.md).

The update should preserve the existing 66-idea design corpus and M1-M9 milestone structure. It should correct stale planning status, remove contradictory sequencing, assign missing prerequisite ownership, and make feature-level observability and corpus reachability explicit without converting exploratory ideas into approved implementation scope. Supporting evidence includes the roadmap's own [`rpg_direction_alignment_audit.md`](../../plans/rpg_design_roadmap/rpg_direction_alignment_audit.md).

This is primarily a documentation-consistency request. It does not authorize implementation, ticket creation, schema migration, balance changes, or edits to the 37-phase authoritative mutation pipeline.

## Why an update is needed

The brainstorm corpus remains useful and unusually well grounded, but promotion into plans has left several layers describing different states of the same program:

1. The roadmap and M1 epic still say M1 is scope-only and not ticketed, while 21 ordered M1 child tickets now exist under `tickets/todos/m1-quick-wins/`.
2. Idea 66 is recognized as the Region/Place foundation, but its formal ownership and exact gate boundary remain inconsistent.
3. M3 lists Coming of Age before the birth record it explicitly requires.
4. M6 describes Drifting Loyalty both before/alongside and after the affiliation mutation path.
5. M7 defers SimQ work until after M1-M6, while the schema registry already specifies expected events and scenarios ahead of implementation.
6. The dormant `CultureDeriver`/`CulturalBiasApplicator` substrate blocks work in three milestones without one prerequisite owner.
7. A confirmed final-permadeath lifecycle defect is documented in the wiring map and alignment audit but is not owned in the executable roadmap.
8. The roadmap title and introductory language still describe six epics even though the program now contains M1-M9.

These are not merely editorial differences. They can cause a future ticket-scoping pass to select the wrong build order, apply an architectural gate too broadly, or omit a required acceptance surface.

## Required interpretation rules

Apply the requested updates using these rules:

- Treat factual repository state and dependency contradictions as corrections.
- Treat the revised program shape and priority ordering as recommendations requiring plan-owner acceptance.
- Keep brainstorm ideas exploratory until a plan or ticket explicitly promotes them.
- Do not renumber the existing ideas.
- Do not make Idea 66 a blanket gate for all of M2 or M4.
- Do not replace domain-specific authoritative updates with a generic social-interaction mutation.
- Preserve the Singular Bottleneck Law: every accepted behavior still produces its own typed `StateUpdate` and enters the authoritative pipeline.
- Keep M7 and M9 as completeness audits, but do not use them to defer acceptance obligations that belong to the feature creating the behavior.

For Idea 66 gate language in this request, **resolved** means all three of the following: the plan owner accepts the Region/Place architecture, assigns an implementation owner, and the prerequisite migration is complete. Dependent tickets may be drafted earlier if they are explicitly blocked, but implementation against the old flat model must not begin. If Idea 66 is rejected, the plan owner must define the replacement Place/ownership boundary before dependent work proceeds.

### Change classification

Use these classifications rather than treating every item below as an automatic correction:

- **Factual synchronization:** M1's current ticket count/status; the M1-M9 roadmap count; the existing permadeath mismatch; the absence of a shared cultural-derivation owner; and removal of statements that contradict dependencies written in the same plan.
- **Plan-owner decisions:** promotion and exact gate contract for Idea 66; the corrected M3 and M6 execution contracts; prerequisite ownership; interaction-layer ownership; and shifting event/reachability obligations into feature acceptance.
- **Priority recommendations:** the R0-R4 summary lens, M1 lane ordering, and emphasis on lifecycle closure and earned character divergence.

Where a requested change selects among valid designs, the relevant plan owner must record acceptance before the source document presents it as authoritative.

## Requested plan updates

### 1. Roadmap overview

Target: [`rpg_design_roadmap.md`](../../plans/rpg_design_roadmap/rpg_design_roadmap.md)

Requested changes, subject to the classification above:

- Rename the title and introduction so they describe the full M1-M9 roadmap rather than “Six Epics.”
- Reconcile M1's status with the committed 21-ticket sequence.
- State that 19 M1 ideas produced implementation tickets, Idea 16 was resolved by investigation without a behavior-change ticket, and Ideas 7 and 17 were split by responsibility.
- Link `tickets/todos/m1-quick-wins/SEQUENCE.md` as M1's executable ordering authority.
- Add final permadeath repair to the M1 correctness lane or give it another explicit roadmap owner.
- Replace “M2 ideas have no dependencies on each other” with the more precise branch model described below.
- Keep M3 and M4 parallel after shared M2 prerequisites, while also allowing the Place and family/social branches to advance independently once their own prerequisites clear.
- Add a single named prerequisite owner for activating or retiring `CultureDeriver`/`CulturalBiasApplicator`.
- Preserve M8/M9 oversight while stating that their reachability and test findings must be consumed during individual feature scoping.

Recommended program summary:

1. Core correctness and activation.
2. Shared entity foundations and individual divergence.
3. Place architecture and voluntary family/social life in parallel.
4. Institutions, ecology, and material ambition.
5. Legacy, memory, belief, and political identity.
6. Continuous feature acceptance followed by M7/M9 completeness audits.

This summary is a priority lens over M1-M9, not a request to renumber the milestones.

### 2. M1 — Quick Wins and Housekeeping

Target: [`rpg_m1_quick_wins_epic.md`](../../plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md)

Requested changes, subject to the classification above:

- Replace prospective/scope-only language with the actual 21-child-ticket state.
- Reconcile the outdated “19 prospective tickets” acceptance text with the committed sequence.
- Record Idea 16 as investigation-resolved rather than silently missing.
- Link each split responsibility for Ideas 7 and 17 through the sequence or crosswalk rather than implying one ticket per idea.
- Organize or annotate the sequence using four lanes:
  - correctness repairs;
  - activation and governance;
  - player-visible RPG improvements;
  - scope-only decisions.
- Add the final-permadeath defect to the correctness lane unless a separate owner is selected.

The requested permadeath scope is narrow: combat already emits `PERMADEATH`; lifecycle deactivation must recognize the terminal outcome and preserve the intended succession/death consequences. This request does not prescribe the implementation beyond use of the authoritative pipeline.

### 3. M2 — Foundational Systems

Target: [`rpg_m2_foundational_systems_epic.md`](../../plans/rpg_design_roadmap/rpg_m2_foundational_systems_epic.md)

Replace the claim that all 16 ideas are independent with this conceptual partition:

1. **Entity foundations:** Ideas 2, 4, 5, 8, 11, 14, 23, 27, 28, and 30.
2. **Independent institution/species foundations:** Ideas 36 and 37.
3. **Population foundation:** Idea 43.
4. **Place-dependent foundations:** Ideas 35 and 48.
5. **Interaction capability:** Idea 6.

Requested gate rule:

- If Idea 66 is promoted, it must be resolved before implementation of Ideas 35 and 48 begins; otherwise the accepted replacement Place/ownership boundary must be complete. Earlier ticket drafts must carry the applicable blocking dependency.
- Ideas 36, 37, and 43 must not be blocked on the Region/Place migration.
- Idea 6 may reuse the appraisal policy established by M1 Idea 13, but its teaching outcome remains a domain-specific authoritative update.

### 4. M3 — Family, Species, and Adult Life

Target: [`rpg_m3_family_species_epic.md`](../../plans/rpg_design_roadmap/rpg_m3_family_species_epic.md)

If Marriage remains a reproduction gate, replace the current internal build order with:

1. Idea 33 — Marriage and its two-party proposal/acceptance lifecycle.
2. Idea 32 — Reproduction, birth event, and persistent parentage.
3. Idea 38 — Birth-to-population-pressure feedback, immediately after or atomically with Idea 32.
4. Idea 31 — Dependents, responsibility, and succession connection.
5. Idea 34 — Coming of Age and its earned branch choice.

Retain M1 Idea 20 and M2 Ideas 14/43 as external prerequisites. Record that Reproduction may deserve its own epic or unusually guarded ticket because it has the scorecard's worst cost/risk profile.

If Marriage is not retained as a reproduction gate, record that design decision explicitly and use `32 -> 38 -> 31 -> 34`; Idea 33 may proceed independently once its own proposal prerequisites clear. The plan must not place Coming of Age before its required birth record in either design.

The acceptance text should forbid exposing repeatable births before Idea 38's safety loop can incorporate births into the aggregate pressure signal.

### 5. M4 — Beyond the City and the Layer Model

Target: [`rpg_m4_beyond_city_epic.md`](../../plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md)

Separate the milestone into explicit branches:

- **Place-shaped ecology and settlements:** Ideas 44-47 and 61. If Idea 66 is promoted, satisfy its gate first; otherwise resolve the replacement Place boundary first.
- **Material exploration and national expansion:** Ideas 49-52. At ticket scope, apply the Idea 66 gate only to outcomes that authoritatively use Place identity or containment.
- **Institutions and economic signals:** Ideas 40, 41, and 64. Retain their own Clan-lifecycle, information-activation, and vacancy-signal prerequisites; do not block them globally on Idea 66.

Give the shared cultural-derivation activation work one external prerequisite owner rather than independently wiring it inside Ideas 56, 57, 61, and 62.

### 6. M5 — Memory, Reputation, and Legacy

Target: [`rpg_m5_memory_reputation_epic.md`](../../plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md)

Make these internal dependency branches explicit:

- Reputation: Idea 60 before Ideas 53/54.
- Death and lineage: Ideas 55/58 after Reproduction, heir assignment, and correct death dispatch exist.
- History and belief: Idea 62 before Idea 57, then Idea 63.

Allow the branches to proceed independently after their own prerequisites clear. Do not describe M5 as one unnecessary linear chain.

### 7. M6 — Political Identity and Belonging

Target: [`rpg_m6_political_identity_epic.md`](../../plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md)

Resolve the current contradiction in favor of one explicit contract:

1. Idea 39 first establishes the authoritative affiliation mutation primitive.
2. Idea 56 derives gradual loyalty pressure that may request or influence that mutation.
3. Ideas 59/65 add home, exile, return, and displacement consequences.

If the intended design instead requires Drift before any affiliation change, split Idea 39 into the mutation primitive and a later voluntary-change trigger. Do not retain both sequencing interpretations.

Also replace City-specific wording where the result is intended to apply to the proposed Place model, conditional on Idea 66's acceptance.

### 8. M7 — Simulation Quality integration

Target: [`rpg_m7_simq_pillar_integration_epic.md`](../../plans/rpg_design_roadmap/rpg_m7_simq_pillar_integration_epic.md)

Retain M7 as a consolidated completeness and calibration audit. Revise the rationale that currently makes all SimQ work a post-M1-M6 concern.

Each behavior-changing feature ticket should define before completion:

- its authoritative update and observable event;
- a deterministic or corpus scenario that causes it to fire;
- a SimQ pillar/rule mapping or explicit exclusion;
- an observer-facing Chronicle, rumor, reputation, UI, or other legibility path, or an explicit reason none is required.

M7 should verify completeness and calibrate the aggregate rules after implementation. It should not be the first owner of missing event contracts.

### 9. M8 and M9 — generation and corpus readiness

Targets: [`rpg_m8_world_corpus_generation_epic.md`](../../plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md) and [`rpg_m9_corpus_test_coverage_epic.md`](../../plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md)

Requested clarification:

- M8/M9 remain oversight and completeness plans.
- Any schema/compiler change, reachable world content, scenario trigger, determinism impact, or grade-anchor recalibration discovered there must enter the affected feature ticket's Definition of Done.
- If Idea 66 is promoted, its implementation ticket must own the world-schema migration and corpus-wide anchor impact rather than deferring those costs to a later audit.
- If promoted, Campaign-only ideas must own the evaluator fields required to detect their success or failure.

For future tickets, these findings belong in the initial Definition of Done. If an M8/M9 finding concerns an already-completed ticket, preserve the closed ticket record and route the gap through the project's normal follow-up/remediation process; this request does not itself create or reopen that work.

## Requested brainstorm updates

### 1. RPG Feature Atlas

Target: [`rpg_feature_atlas.html`](../rpg_feature_atlas.html)

Requested changes:

- Add a dated review note linking this request and the focused review.
- Preserve all existing idea numbers and investigation history.
- If Marriage remains a reproduction gate, correct the M3 suggested build order to `33 -> 32 -> 38 -> 31 -> 34`; otherwise use `32 -> 38 -> 31 -> 34` and mark Idea 33 independent.
- Clarify M6 as `39 mutation primitive -> 56 drift consumer/trigger -> 59/65`, unless Idea 39 is explicitly split.
- Update Idea 66's dependency note so it gates place-shaped work only.
- Distinguish three reusable interaction layers:
  1. appraisal policy;
  2. proposal lifecycle;
  3. domain-specific authoritative outcome.
- Add the confirmed final-permadeath defect to the atlas's repair/backlog view without renumbering it as a new design idea unless the maintainers intentionally choose to do so.
- Mark `CultureDeriver`/`CulturalBiasApplicator` activation as one shared prerequisite requiring an owner.
- Add a core-RPG priority lens: completed lifecycle loops and earned character divergence outrank additional combat breadth.

Do not erase correction history or replace the atlas with the shorter prioritization from this request.

### 2. RPG Schema Registry

Target: [`rpg_expected_schemas.html`](../rpg_expected_schemas.html)

Requested changes:

- Keep the existing expected-event registry.
- Replace language implying event design belongs only to M7 with the split responsibility: feature tickets own event contracts; M7 owns completeness and calibration.
- Add or clarify the durable-state boundary between an interaction proposal and its accepted domain outcome.
- Ensure Marriage, affiliation, Clan entry, trade, and teaching do not imply one generic mutation schema merely because they can share appraisal or handshake patterns.
- Cross-link the final-permadeath outcome mismatch and its eventual ticket owner.
- Record Idea 66's gate boundary as Place-state consumers, not an entire milestone.

### 3. RPG Simulation Wiring Map

Target: [`rpg_simulation_wiring_map.html`](../rpg_simulation_wiring_map.html)

Requested changes:

- Preserve the existing permadeath evidence.
- Once plan ownership is chosen, replace “Unscoped” with the selected roadmap/ticket reference.
- Add the M3 birth-feedback adjacency requirement where lifecycle transitions are summarized.
- Cross-link the shared cultural-derivation prerequisite owner.
- Keep population seeding separate from the Place migration.

### 4. Design Merit Scorecard

Target: [`design_merit_scorecard.html`](../design_merit_scorecard.html)

Requested changes:

- Score Idea 66 using the same seven-axis rubric, or explicitly document why architectural foundation ideas are excluded.
- Do not silently change existing scores to match this review's priorities.
- Add a note that priority also depends on prerequisite leverage, lifecycle closure, and whether a feature creates earned character divergence; the seven visible axes remain the evidence, not a single composite score.
- Preserve Reproduction's high-value but very low efficiency/risk-adjusted-cost result as an implementation warning.

### 5. Creative direction and supporting brainstorms

Targets: [`the_unwritten_world.html`](../the_unwritten_world.html), [`entity_capabilities.html`](../entity_capabilities.html), [`simulation_capabilities.html`](../simulation_capabilities.html), and [`simulation_design_taxonomy.html`](../simulation_design_taxonomy.html)

No broad rewrite is requested. Add cross-links only where these documents currently claim roadmap completeness or a canonical status that would otherwise hide the updated dependency findings.

The eight creative principles should remain the design authority. The review's “life-path layer” diagnosis is an application of those principles, not a ninth principle.

## Canonical statements to align across documents

The following statements should have the same meaning everywhere, even if wording differs:

1. M1 has 21 ordered child tickets covering 19 ideas; Idea 16 required no behavior-change ticket.
2. Final permadeath is a confirmed lifecycle correctness defect with an explicit owner.
3. Population seeding is a shared foundation and is not gated by Idea 66.
4. If Idea 66 is promoted, it gates work whose authoritative state depends on Place identity or containment, including M2 Ideas 35/48 and the Place-shaped parts of M4; if rejected, the accepted replacement Place boundary supplies that gate.
5. If Marriage remains a reproduction gate, M3 order is Marriage, Reproduction, immediate population feedback, Dependents, then Coming of Age; otherwise the order is Reproduction, immediate population feedback, Dependents, then Coming of Age, with Marriage independent.
6. Affiliation mutation exists before Drifting Loyalty requests or influences it, unless the plan explicitly splits the primitive from the trigger.
7. Appraisal and proposal mechanics may be reused; accepted outcomes remain domain-specific `StateUpdate`s.
8. Feature tickets own events, reachability, and observer legibility; M7/M9 audit completeness and calibration.
9. `CultureDeriver`/`CulturalBiasApplicator` activation has one prerequisite owner shared across M4-M6.
10. Place architecture and voluntary social/family development may proceed in parallel after their shared foundations are ready.

## Proposed update order

Apply documentation changes in this order to avoid reintroducing contradictions:

1. Accept, revise, or reject the ten canonical statements above. Reconcile every rejected statement with replacement wording before applying any dependent edit.
2. Update the roadmap overview and assign the two missing owners: permadeath and cultural derivation.
3. Correct M1, M2, M3, M4, M6, and M7 epic documents.
4. Clarify M5, M8, and M9 acceptance/dependency language.
5. Update the Atlas's sequencing and shared-mechanism summaries.
6. Synchronize the Schema Registry and Wiring Map.
7. Address Idea 66 in the Merit Scorecard.
8. Run a final cross-document link, idea-count, ticket-count, and dependency consistency check.

## Acceptance checklist for the documentation update

- [ ] Existing idea numbers and historical correction notes are preserved.
- [ ] No brainstorm idea is presented as approved implementation merely because it has a proposed schema.
- [ ] Roadmap title and status accurately describe M1-M9.
- [ ] M1 ticket count and sequence match the filesystem.
- [ ] Permadeath and cultural-derivation prerequisites have explicit owners.
- [ ] M2 does not claim all ideas are mutually independent.
- [ ] Idea 66 has a narrow, consistent gate boundary.
- [ ] M3 and M6 contain no contradictory order statements.
- [ ] Population feedback is adjacent to or atomic with Reproduction.
- [ ] Interaction reuse does not bypass domain-specific authoritative updates.
- [ ] Feature-level event, corpus, SimQ, determinism, and observer-legibility obligations are explicit.
- [ ] M7 and M9 remain final completeness/calibration audits.
- [ ] All new local links resolve.
- [ ] HTML navigation/anchors remain valid after brainstorm edits.
- [ ] Documentation validation and `git diff --check` pass.

## Explicitly not requested

- No source-code implementation.
- No ticket creation or ticket status transition.
- No direct edit to authoritative pipeline phases.
- No automatic activation of feature flags.
- No balance-value invention.
- No deletion or renumbering of brainstorm ideas.
- No replacement of the M1-M9 roadmap with the R0-R4 review shorthand.
- No modification of existing brainstorm or plan documents as part of this request document itself.

## Requested decision

Plan owners should review the canonical statements first, then either:

1. approve the documentation synchronization and assign owners for the permadeath and cultural-derivation prerequisites; or
2. record explicit disagreements and replacement contracts in the roadmap before further M2-M6 ticketing.

Until that decision is made, the current plans remain authoritative, and this document remains a review-derived update request only.
