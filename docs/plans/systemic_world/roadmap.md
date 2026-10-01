---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
last_verified: "2026-09-27"
---

# Systemic World Roadmap — PROPOSED / FOR REVIEW

**Status: `PROPOSED / FOR REVIEW`. Not owner-approved. Does not supersede any existing canonical
roadmap.** Produced by the local repository-aware investigator per a five-stage investigation arc
(Pass 1/2, Recognition/Standing synthesis, Parts A/B/C, the foundational synthesis, this document).
This document stays high-level and cites supporting evidence by pointer, rather than repeating
code-level traces. All paths below are relative to this folder:
- **Investigation arc**: `evidence/rpg-core-investigation-*.md` (Pass 1/2, the Recognition/Standing
  synthesis, Parts A/B/C) and `evidence/rpg-core-foundational-synthesis-and-roadmap-revision.md`.
- **2026-09-27 probe reports**:
  - §3.1 audit → `evidence/2026-09-27-authority-boundary-audit-findings.md`
  - §7.1 composition probe → `evidence/2026-09-27-lineage-composition-probe-findings.md`
  - §7.2 observer encounter → `evidence/2026-09-27-inheritance-observer-encounter-findings.md`
  - §7.4 candidate search → `evidence/2026-09-27-candidate-trajectory-search-findings.md`
  - §9 tooling → `evidence/2026-09-27-registry-scp-tooling-findings.md`

  Some of these reports were written under instructions that were later superseded, and they carry
  milestone or ticket labels that no longer exist. Where they differ from this roadmap, the roadmap
  is authoritative.
- **Review instructions received**: `review_history/`.

**What this is not**: an implementation plan, a ticket list, or a claim that any part of it is
approved. Engineering decisions (record types, class reuse, symbol retirement, test design) belong to
the downstream ticket planner and implementation agents.

**Metadata note.** The frontmatter `status: active` is the repository's "live working document"
value. The frontmatter schema offers only `authoritative`, `active`, `historical` and `archive`,
with no "proposed" value. `active` does **not** record owner approval; the visible status above is
the review state of record. `authoritative` would be the approval-bearing value. Adding a `proposed`
value is a separate schema correction, not done here.

---

## 0. Relationship to existing plans

| Document | Authoritative for | Relationship to this document |
|---|---|---|
| `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` (M1-M9) | The 65-idea brainstorm-to-implementation program that already shipped | **Closed, unrelated scope.** M1-M9 are all `DONE`; M10 is a narrow 2-idea backlog. This document does not extend that numbering — a new capability program forced into a finished, dated milestone series would misrepresent both. |
| `docs/world_rules/roadmap.md` (World Rule Catalog) | Target world semantics, frozen | **Upstream authority.** Every capability area below cites which frozen Rules already define its target semantics. This document never redefines a Rule; it sequences *realizing* what the Catalog already states. |
| `docs/plans/simulation_semantic_control_plane/roadmap.md` (M0-M4) | Rule↔Mechanism *mapping*, not new capability implementation | **Independent, parallel track.** M3's ongoing triage stream stays exactly what it is — this document's findings feed it, but this document does not manage or gate on M0-M4's own sequencing. |
| `docs/plans/long_term_development_roadmap.md` | Engine-infrastructure phases (CI, determinism, corpus tooling) | **Independent axis.** A different kind of health entirely — this document assumes that infrastructure exists and builds capability on top of it, not instead of it. |
| `docs/plans/render_and_art_program_roadmap.md`, `hud_delivery_roadmap.md`, `live_map_scaling_roadmap.md` | Presentation-layer programs | **Explicitly unrelated axis**, per this investigation's own repeated instruction not to confuse the two. Section 5's "Observation and player delivery" area is deliberately about *what* a gameplay lens may expose, never *how* it renders — those documents own the how. |

**This document's own proposed home**: `docs/plans/systemic_world/roadmap.md`, a standalone
location not appended to any of the above. It is `PROPOSED / FOR REVIEW` until the owner accepts
its direction.

**Companion documents** (same folder, same review status):
- `first_wave_plan.md` — the epic-level first-wave plan: epics, boundaries, gates, and failure
  branches.
- `ticket_planner_handoff.md` — one card per first-wave epic, for the downstream ticket planner.
- `owner_decision_memo.md` — the only home for owner-level choices.

---

## 1. Product north star

*(Full statement in `evidence/rpg-core-foundational-synthesis-and-roadmap-revision.md`'s own "Product
north star" section — summarized here.)*

The engine simulates a persistent world; a gameplay lens defines a player's relationship to it, and
that choice is deliberately **not** frozen into engine semantics yet. Ordinary first-class subjects
can become significant through circumstance — significance is an outcome, never a privileged
starting class. World processes, including magic, stay causally coherent across domains; growth,
decline, conflict, and instability are valid outcomes, not failure states. Advantages (capability,
wealth, status, relationships, knowledge, territory, authority) stay distinct, converting only
through specific declared paths. Simulation value is delivered the moment a player can *encounter* a
consequential difference and form their own hypothesis about it — not when every mechanic has been
explained or every cause made visible.

## 2. Epistemic and experiential delivery principle

*(Full statement, with two worked cross-domain examples, in the foundational synthesis document —
summarized here.)*

```text
world truth and causal history → potential evidence in the world
  → what particular characters/institutions can perceive or learn
  → their possibly mistaken beliefs and reactions
  → what the player can actually encounter through a gameplay lens
  → the player's own interpretation
```

The player is not automatically the world's omniscient debugger. Every player-facing surface
(biography, log, HUD, dialogue, rumor) is a projection with a viewpoint and scope — the same
discipline `KnowledgeModelService`'s own "hidden world truth is never injected" invariant already
enforces for NPCs should not be silently violated for the player through a convenient UI shortcut.
Deliberate ambiguity (a genuinely incomplete or conflicting account, the kind any in-world observer
would also face) is intended texture; opacity (no discoverable trace exists at all, or the world
behaves inconsistently with itself) is a defect regardless of how interesting it looks.

---

## 3. Capability map (a coverage checklist, not a mandated six-module architecture)

Six perspectives, each showing: the outcome it enables, its semantic foundation, current evidence
(`DESIGNED` / `REALIZED` / `VERIFIED` / `INTEGRATED` / `PLAYER-EXPERIENCED`, kept separate rather than
collapsed to one percentage), a meaningful cross-domain proof, and what stays open.

**Name clash, recorded rather than resolved.** This roadmap's `DESIGNED` is an evidence-maturity
axis: are the target semantics specified? It shares its name, but not its meaning, with the
reserved mechanism-status vocabulary term `DESIGNED` in `docs/brainstorm/core_rpg_design_direction.md`
(status note at line 480). Read the two independently. Renaming either one is deferred and is not a
mid-review change.

### 3.1 World substrate and causal governance

**Outcome**: persistent identity, time, space, authoritative state, provenance, cost/resource
conservation, transformation, reach, and cross-domain consequence all hold coherently, for every
domain, not just the ones under active development.

**Semantic foundation**: Milestone A of the frozen Catalog in full (`ID-*`, `TIME-*`, `AUTH-*`,
`REACH-*`, `CAP-*`, `COST-*`, `LIMIT-*`, `RES-*`, `TRANS-*`, `HP-*`).

| Status | Finding |
|---|---|
| `DESIGNED` | Fully, within the frozen Catalog's current scope — Milestone A is complete for the cases it addresses; this is not a claim that every future world case is designed. |
| `REALIZED` | Strong for the domains this investigation traced (Combat, Harvest, Quest reward — Part A). |
| `VERIFIED` | Partial — `TCK-20260401-ACTION-CONVERGENCE`'s bit-identical-replay acceptance criterion is real, checked evidence for the authoritative-apply/replay-determinism law specifically; not every domain's own state-authority pattern has been individually checked. |
| `INTEGRATED` | **Confirmed fragile even where individually verified.** The regional-sovereignty bug (two systems writing two *different* representations of region ownership — `owner_faction_id` vs. `FactionState.territory` — with no reconciliation between them) was found in an already-shipped, already-tested domain during unrelated work this arc. This round's audit (below) found a **second confirmed violation of the same underlying invariant** — canonical authority + a declared resolution rule (§3.1's own semantic obligation) — but **the concrete mechanism is different, not identical, and should not be assumed the same without further evidence**: the lifecycle-active case (§7) is a same-tick evaluation-*order* race between one branch that reads a stale, prior-tick-persisted value and another that computes one tick ahead, not two systems disagreeing about which field represents the truth. Two confirmed violations of the same invariant, via two distinct mechanisms, is evidence the invariant needs a real enforcement discipline (§3.1's own audit exists for exactly this) — it is not yet evidence of one recurring bug pattern. |
| `PLAYER-EXPERIENCED` | Not directly surfaced as its own player-visible layer — but experienced indirectly, whenever a player encounters a coherent consequence that depends on this substrate holding (e.g. a region's ownership actually changing consistently). Not yet evaluated for that indirect effect specifically. |

**Cross-domain proof, revised to a bounded target (external review correction, 2026-09-26)**: an
open-ended "does this pattern recur anywhere" pass cannot be proven complete by a finite audit.
Bounded instead: identify the most consequential cross-domain mutation paths (durable ownership/
control fields written from more than one system, the shape the regional-sovereignty bug actually
had), review ownership/authority at those specific boundaries, and exercise representative
integration scenarios for each. Report the scope actually covered and name what remains `UNKNOWN`
outside that scope — never claim the absence of a defect outside the boundary actually checked.

**Audit actually run, 2026-09-27 (fourth round, per the finalize instruction's §4)** — a named,
finite set of 5 boundaries, each with an explicit outcome, not "swept the whole engine":

| # | Boundary | Classification |
|---|---|---|
| 1 | Region ownership: `RegionState.owner_faction_id` vs. `FactionState.territory` (siege transfer) | `DEFECT_CONFIRMED` — but already known/tracked (`FAC-010`, `docs/parity_ledger/faction.yaml:227-237`, `status: verified`, intentional divergence, not hidden). Downstream consequence (does taxation fire against a stale post-siege owner?) is `UNKNOWN_WITH_REASON` — no test combines siege transfer with a subsequent taxation tick. |
| 2 | Entity death: `alive_set` written from `combat.py` (5 sites) and `world_dynamics.py` (hazard damage) | `UNKNOWN_WITH_REASON` — explicit cross-system precedence comments exist (`groups.py:99`, `clan_lifecycle.py:19`), suggesting deliberate ordering, but no scenario test exercises a same-tick hazard-kill + combat-kill collision to verify it. |
| 3 | Faction diplomacy: `diplomatic_relations_set` from the autonomous state machine and the auto-alliance handler, same tick, same pipeline phase | `UNKNOWN_WITH_REASON` — ordering is fixed and looks intentional (transitions computed, then alliance layered after, `pipeline.py:255-283`), but no test asserts the same-pair-same-tick collision case. |
| 4 | Quest status: `QuestUpdate.status_set` from 4 files across distinct pipeline phases | `CONFIRMED_FINE_WITHIN_SCOPE` — a strict forward state machine; matches Part A's own prior finding that quest reward is the cleanest single-writer-per-stage pattern found anywhere. |
| 5 | Public reputation: `SocialComponent.reputation` (`reputation_set`) from `social_memory.py` and `orchestrator.py` | `UNKNOWN_WITH_REASON` — two real writer call sites for the same durable field; phase ordering and same-tick-same-entity collision not checked this round. Separate from the roadmap's already-flagged *semantic* question of what `public_reputation` means (owner memo decision 4). This is a mechanical dual-writer check only. |

**A sixth, unplanned finding surfaced independently** (not part of this 5-boundary set, found instead
while investigating the lineage feasibility gate, §7): `entity.lifecycle.active` is raced between
`ApplyPath`'s passive-decay branch and `LifecycleSystem.resolve_lifecycle`'s own OLD_AGE dispatch —
a confirmed, reproducible `DEFECT_CONFIRMED`, found by running code rather than reading it. **This
violates the same authority invariant as boundary 1 (region ownership) — a persistent fact must not
be committed from a stale assumption without a declared resolution rule — but the concrete mechanism
differs**: boundary 1 is two systems writing two different *representations* of ownership with no
reconciliation; this one is a same-tick *evaluation-order* race (a stale prior-tick read racing a
one-tick-ahead write), not a representation mismatch. Treat them as two separate confirmed defects
under one shared invariant, not as the same bug recurring. See §7 for the full account; it directly
blocks natural-aging succession, not a hypothetical case.

**Exit condition, stated exactly.** The named set of 5 planned boundaries resolved as:
- 1 `DEFECT_CONFIRMED` (region ownership, already tracked);
- 3 `UNKNOWN_WITH_REASON`;
- 1 `CONFIRMED_FINE_WITHIN_SCOPE`.

The 1 unplanned finding (the lifecycle-active race) is also `DEFECT_CONFIRMED`. That makes 6
results, 2 of them confirmed defects. The audit does
**not** claim the regional-sovereignty defect class is absent elsewhere in the engine. **Deliberately
not checked this round** (named, not silently skipped): market/economy authoritative price or
inventory fields; combat durability/HP fields across the three known dispatch paths (Part A already
flagged dispatch plurality from a different angle); `cooldown_set`, `group_id_set`/`GroupRecord`,
and strategic-cognition bundle fields; `src/economy/vacancy.py`'s vacancy/settlement fields;
institutional standing (does not yet exist as a mechanism, so moot). No production code was changed
by this audit — boundary 1's downstream-consequence gap and the new lifecycle-active race are
flagged for escalation, not fixed here.

**Addendum, 2026-10-01 — boundary 2 resolved by first-wave Epic C1 (`TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK`, observed at engine commit `e9db40f0a`).** Boundary 2 moves from `UNKNOWN_WITH_REASON` to **`DEFECT_CONFIRMED`**. The 2026-09-27 reading of `groups.py:99` and `clan_lifecycle.py:19` as a "deliberate precedence" signal was wrong: both comments state a same-tick *read-freshness* rule for downstream consumers, not a combat-vs-hazard precedence rule. No declared resolution rule exists for this boundary.
- **Mechanism:** `world_dynamics.py:39` unconditionally overwrites the victim's accumulating `CombatUpdate` with `outcome_kind="HAZARD"`, between the phase that writes `KILL` and the phase that reads it (`pipeline.py:348`, between `:297`/`:320` and `:414`). Its eligibility guard (`:31`) reads committed state, so a victim killed earlier in the same tick is always eligible. `resolve_lifecycle` has only two death branches (`OLD_AGE`, `KILL`/`PERMADEATH` → `COMBAT`) and no HP/alive branch, so the collision does not resolve wrongly: it erases the combat death record.
- **Consequence:** no `death_reason`, `death_tick` or `is_permadeath`, so succession, heirloom and lineage dispatch never runs. Deactivation lands one tick late via `apply.py:109`. Groups and clan succession (`is_alive()`/`is_active()`) treat the entity as dead while lifecycle does not.
- **Reachability, two answers kept separate:** the same-tick combat-kill + hazard-kill conjunction was not observed (0 `KILL`/`PERMADEATH` in 120 unscripted ticks of `frontier_marches`; hazard drain on 0.3% of entity-ticks). This is not read as unreachable, and nothing in the code prevents it. The committed signature (`combat.alive=False`, `lifecycle.active=True`, `death_reason=None`) is nonetheless routine in the same run (9 rows on 8 distinct ticks), but it is reached by **two opposite defects that must not be conflated**. 4 rows are hazard-only drain deaths that *go unrecorded*; this is the boundary's own defect. 4 `DEFEAT` rows and 1 `REBIRTH` row are the reverse: outcomes that `LIFE-02` treats as non-lethal (each `DEFEAT` here is a non-`HERO` defender hit by an opportunity attack, `is_lethal=False` at `movement.py:241`/`combat.py:251-252`; a `HERO` is always rebirth-eligible and resolves to `REBIRTH`, which sets `generation_delta=1` and leaves `perma_set` False), which nothing ever restores (`alive` is never set back to `True` at runtime) and which `apply.py`'s passive HP gate then deactivates permanently. For those rows the absent death record is correct, and the deactivation is the bug, routed separately. C1's `DEFECT_CONFIRMED` rests only on the hazard route and the `world_dynamics.py:39` overwrite. *(Corrected 2026-10-01: the first version listed the three routes as one defect, and attributed `DEFEAT` to `HERO` defenders.)*
- **Invariant tally:** this is a third confirmed violation of the same authority invariant, by a third distinct mechanism: a missing classification branch plus an unconditional overwrite inside one accumulating update. It is neither boundary 1's representation mismatch nor the lifecycle-active evaluation-order race. Updated totals: 5 planned boundaries = 2 `DEFECT_CONFIRMED`, 2 `UNKNOWN_WITH_REASON`, 1 `CONFIRMED_FINE_WITHIN_SCOPE`; with the unplanned finding, 3 of 6 confirmed defects. Still not evidence of one recurring bug pattern.
- **Routing (not fixed by C1):** the missing HP/alive death branch goes to `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`. The `world_dynamics.py:39` overwrite needs a new ticket, sequenced against `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`, and inheriting C1's escalation and SCP drift-check requirement. Filing is the owner's decision.

**The semantic obligation itself is already supported, within investigated scope — corrected per
external review, 2026-09-27**: every persistent fact has a canonical authority, and a world effect
must not commit from stale assumptions without a declared resolution rule. This is not itself an
open question. **What remains open is how to verify and enforce that obligation across
consequential cross-domain boundaries** — the regional-sovereignty case shows a real violation can
exist even where the obligation is accepted in principle, so open means "what checking discipline
catches this class of defect," not "does the obligation hold." This does **not** imply one physical
code writer per fact, or one universal `revalidate()` API for every domain action and world process
— reservations, multistage actions, ongoing processes, and environmental effects may each have a
different, equally legitimate way of honoring the same obligation.

### 3.2 Autonomous world dynamics

**Outcome**: life/body/ecology, environment, economy, social/lineage, institutions/politics/law,
culture/belief, and magic all behave as coherent, interacting domains — **without equal
implementation depth being required or assumed**.

**Semantic foundation**: Batches 04, 05, 08, 09, 10, 11B, 12 — the entire frozen Catalog outside
Milestone A and the Agency/Recognition thread.

| Domain | `DESIGNED` (within current Catalog scope) | `REALIZED` (high-level) |
|---|---|---|
| Life/Body/Ecology (Batch 05) | Full, for cases the batch investigated | Uneven — no HP recovery mechanism at all; aggregate population disconnected from individual births/deaths (Batch 05's own finding, not re-verified this arc). **Confirmed 2026-09-27 (checked as a candidate trajectory, §7.4)**: `regional_trauma`/`calamity_intensity` (environmental-threat/calamity mechanisms) are `state: done` but real corpus runs `contradicted` them outright — built and wired, but the `trauma_score`/`calamity_intensity` values never actually move in real play (already-open tickets `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`, `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`). This is a stronger finding than "uneven" — a mechanism that was tested and found not to fire, not merely untested. |
| Space/Environment (Batch 04) | Full, for cases the batch investigated | Two confirmed repository gaps (no route/portal mechanism; no non-physical movement) at Catalog-freeze time, not re-checked this arc |
| Material/Economy (Batch 08) | Full, for cases the batch investigated | **Confirmed gaps this arc**: wealth→leverage conversion `MISSING` on three independent paths (`ME-S12`); the heirloom/`"CHEST"` resolver bug, plus a sibling risk in the harvest `"NODE"` resolver path (Part A) |
| Social/Lineage (Batch 09) | Full, for cases the batch investigated | **Real, evidenced proof of the general shape working, with a confirmed reachability caveat (fourth round, 2026-09-27)** — feud inheritance, dying wishes, displacement, heirloom transfer, and leadership succession are all `PROVEN CURRENT` at the mechanism level *for the artificially-staged already-past-max-age case both repo tests use*. Attempting to compose a second hop through **ordinary, gradual per-tick aging** (no manual staging) surfaced a real, reproducible defect: `ApplyPath`'s passive-decay branch deactivates the entity one tick before `LifecycleSystem.resolve_lifecycle`'s own OLD_AGE check ever runs, so succession/heirloom/dying-wish dispatch **never fires** for a death that arrives gradually rather than pre-staged (§7). Whether this *scales* to a presentable, temporally-continuous player-facing sequence is now blocked on fixing this specific defect, not merely an unchecked design question (§5, §7). |
| Institutions/Politics/Law (Batch 10) | Full, for cases the batch investigated | **Confirmed gap**: no per-(institution, individual) standing of any kind (`IP-S17`); no in-world law/enforcement subsystem at all (Batch 10's own freeze-time finding) |
| Culture/Belief (Batch 11B) | Full, for cases the batch investigated | `CultureState` real but correctly `PARTIAL` (not the complete definition of culture); belief-institution role narrowly scoped |
| Magic/Supernatural (Batch 12) | Full, for cases the batch investigated | **Weakest realization of any domain** — no dedicated magic mechanism of any kind exists, with one real, live, structurally-ready exception (`PerceptionGate`'s own `magic_sense`/`magic_signal` channel, currently `INERT-OFF`) |

**Cross-domain proof**: the lineage domain already provides real, mechanism-level evidence that the
general shape (history → durable consequence → later behavior) can work — worth treating as a
working reference example while other domains catch up. This is evidence the *pattern* is
achievable, not a claim that lineage itself is a fully verified, player-facing cross-domain proof
(see §5's feasibility gate for that separate, unchecked question).

**Open**: the investigated cases in every domain above found no new Rule required — this is a claim
about the cases actually traced, not that no semantic gap can exist anywhere in these domains'
fuller scope. Sequencing across domains is explicitly **not** required to be uniform; lineage needs
no further foundational work at the mechanism level, economy/institutions need targeted realization
work, magic needs the most (though still zero new Rules found necessary, per Batch 12's own already-
frozen scope).

### 3.3 Situated agency and action

**Outcome**: subjects perceive, know, want, choose, attempt, and experience consequences —
consistently across contrasting domains, and **without every world process being forced to
masquerade as an agent action**.

**Semantic foundation**: `AGENCY-01/02/03/04`, `KNOW-01/02`, `PERC-01`.

| Status | Finding |
|---|---|
| `DESIGNED` | Fully, within the frozen Catalog's current scope. |
| `REALIZED` | Strong for Combat (most rigorously evidenced of any traced family — a documented fix raised real coverage 6.3%→93.7%) and Harvest (live via generic `INTERACT`, contra two dead named-harvest files); cleanest state-authority pattern found anywhere is Quest reward's single-writer stage. |
| `VERIFIED` | Partial — the upstream edge (how a selected `ActionIntent` becomes an `ActionRouter` payload) is `UNKNOWN` across all three traced families, not confirmed broken, simply untraced. |
| `INTEGRATED` | Confirmed genuinely plural, not unified — three independent action-dispatch paths exist (bounded-worker `ActionRouter`, direct pipeline-phase calls for Guild-visit/Objective-Reward, and a dead, never-adopted typed model). **A world process and an agent action needing different execution paths is a valid architectural boundary in the two specific cases checked** (Guild-visit, Objective-Reward — each carries its own stated architectural reason). This does not establish that every current bypass path in the codebase is semantically correct by the same standard — only these two were individually checked. This plurality is a finding to design around, not a defect to fix by forcing one shape. |
| `PLAYER-EXPERIENCED` | Not directly surfaced — this is decision/execution substrate beneath whatever a gameplay lens eventually exposes. Experienced indirectly whenever a player encounters a consequence that depended on a correct attempt/resolution (e.g. an attack that fired against current, not stale, state). Not yet evaluated for that indirect effect. |

**Cross-domain proof**: the three already-traced families (Combat/Harvest/Quest-reward)
individually sound, *and* their one shared unproven edge confirmed either way — not three separate
proofs, one shared one.

**Open**: whether deliberate entity actions should ever generalize to reflexes/coercion/
organizational decisions/environmental processes — `AGENCY-02`'s own Scope Boundary already defers
this; this document leaves it exactly as deferred, not resolved by omission.

### 3.4 History and feedback

**Outcome**: accumulated personal and collective history measurably alters access, risk, resources,
relationships, and future trajectory.

**Semantic foundation**: `HP-*` (History/Provenance), `SOC-01`, the Final Integration Batch's own
lived-history→recognition→reaction finding, `politics-authority.md`'s power-conversion Rule.

| Status | Finding |
|---|---|
| `DESIGNED` | Fully, within the frozen Catalog's current scope. |
| `REALIZED` | Strong for individual-participant history (`TurningPointState`, `SocialComponent`'s direct-interaction `bonds`/`trust_history`) and lineage specifically (§3.2). **Confirmed `MISSING`**: a producer for witnessed/secondhand evidence at all (the single narrowest confirmed bottleneck in the whole investigation); institutional standing at any level; opportunity-generation reading standing/reputation as an input at all. **Correction, external review, 2026-09-26**: this does not mean `bonds`/`trust_history` is the decided destination for witnessed or hearsay evidence once a producer exists — the foundational synthesis leaves that representation choice open on purpose (direct participation, direct witnessing, and secondhand report are kept as three distinguishable primitives, not assumed to share one shape). |
| `VERIFIED` | The individual-participant case only — `appraisal.py`'s real, checked bond→trust_history→global-fallback priority order. |
| `INTEGRATED` | Not yet — this is precisely the gap the whole investigation exists to close. |
| `PLAYER-EXPERIENCED` | Not yet — no player-visible proof exists today that traces cleanly to real propagated evidence rather than an omniscient global read. |

**Cross-domain proof**: the corrected two-shopkeeper scenario (direct interaction vs. genuine
witnessing, kept distinct per the foundational synthesis's own correction), *plus* the
craftsperson/wealth trajectory (proceeds independently of any of the above, per Part B's own
`INDEPENDENT CAUSAL EDGE` finding).

**Open**: the three-way split between direct-participation, direct-witnessing, and secondhand-
hearsay primitives (not assumed to share one shape); whether individual and institutional standing
share a record shape; whether reputation-sensitive opportunity belongs at generation-time or
filter-time. Owner-level parts are in `owner_decision_memo.md`; the rest belongs to the epic that
takes this work on (portfolio epics D and E, §8).

### 3.5 Observation and player delivery

**Outcome**: a future gameplay lens can expose coherent world consequences and genuinely imperfect
information, so a player can infer rather than be instructed — the epistemic principle (§2) realized
as an actual product surface.

**Semantic foundation**: **explicitly none from the Catalog** — the Catalog's own governance
(`docs/world_rules/roadmap.md`'s "Cross-cutting layer disposition") already states "Observation &
legibility... is out of scope for this Catalog," governed instead by this repo's own Architecture
Rule and `/api-design-principles`. This capability area is real, but its semantics live outside the
frozen Catalog by design, not by oversight.

| Status | Finding |
|---|---|
| `DESIGNED` | **Not yet, at the product level** — the epistemic principle (§2) is this investigation's own first pass at this; no gameplay lens has been chosen. |
| `REALIZED` | N/A |
| `VERIFIED` | N/A |
| `INTEGRATED` | N/A |
| `PLAYER-EXPERIENCED` | N/A — this is the area with the least existing evidence of any of the six, entirely appropriately, since the product direction was only just clarified. |

**Cross-domain proof**: not yet definable in general, but not uniformly blocked either (§4's
paths).
- The recognition-dependent path needs §3.4's propagation gap closed before any projection is
  possible.
- The lineage probe does not. However, no in-world carrier or provenance signal exists for it today
  (§7.2). So this area's nearest tractable job is the evidence-path and observer-contract design in
  portfolio Epic B (§8), preceded by the first wave's feasibility check B0. It is not a projection
  of an already-encounterable clue.

This says only that lineage does not share recognition's dependency. It does not claim the projection question itself
is answered; see §7 for exactly what remains open there.

**Open**: essentially everything — this is a genuinely new capability area, not a realization gap
under existing content. No Rule needs to be written for it (per the Catalog's own explicit
exclusion); its own design work is architecture-and-product work, distinct from Rule-drafting.

### 3.6 Evaluation and expansion

**Outcome**: hard correctness, causal correctness, observed reach, persistent consequence, emergent
capacity, performance/scale, and distributional behavior are all measurable — across varied domain
trajectories, not one benchmark scenario.

**Semantic foundation**: none new — this reuses existing, real infrastructure: SimQ's pillar scoring,
the corpus-tier taxonomy (Unit/End-to-end/Stress/Regression), and the Semantic Control Plane's own
M3 ongoing ingestion stream.

| Status | Finding |
|---|---|
| `DESIGNED` | Fully — this infrastructure already exists and is not part of what this roadmap proposes building. |
| `REALIZED` | Real, live, already in use for unrelated tracks. |
| `VERIFIED` | Ongoing, by design (M3's own "permanent, ongoing stream" framing). |
| `INTEGRATED` | This roadmap's own job is ensuring the capability areas above *feed* this machinery once they produce real findings — not building new evaluation infrastructure. |
| `PLAYER-EXPERIENCED` | Not directly surfaced — evaluation infrastructure isn't itself player-facing, but a player experiences its effect indirectly whenever it catches a regression before it reaches them. Not evaluated for that indirect effect. |

**M3 stays exactly what it already is**: an ongoing, non-blocking ingestion stream. Nothing in this
roadmap gates on M3, and this roadmap does not propose changing M3's own scope or cadence.

**Gap acknowledged — external review correction, third round, 2026-09-27**: none of the
infrastructure above (SimQ pillar scoring, the corpus-tier taxonomy, M3's ingestion stream)
evaluates §5's *player-side inference check* — whether a real observer, given only legitimate
in-world clues, can form an intelligible hypothesis and revise it on new evidence. That is a
human/usability evaluation this roadmap has not built and has no existing infrastructure for; §5's
player-observation requirement stays unmet by existing tooling alone, not merely unrun.

---

## 4. Dependency paths through the epic portfolio (a sample, not an exhaustive graph)

Epic letters refer to the portfolio in §8. Each dependency below is a semantic or evidentiary
necessity, not a universal phase order.

```text
Proposed first wave (§8): J reachability · B0 observation feasibility · C1 death boundary
  B0 finds perception inactive ──> proposal: a perception-foundation epic (precedes B and D)

Path 1 — no recognition propagation (lineage probe):
  C authority boundaries (parallel, reusable)
  A life/death continuity  ──>  [world-side proof complete on its own]
  B0 feasibility ──> B observer contract (design) ──> B route built ──> player inference on the probe
                                                          ──> closed-loop trajectory (future)

Path 2 — recognition-dependent (individual history):
  A/C foundations ──> D witness/hearsay propagation (world side)
                  ──> B's observer contract applied to D ──> recognition inference proof (future)

Path 3 — no recognition, different owner (wealth/office):
  F declared conversion edges (independent of D) ──> B's contract where observer value is intended
```

**Reusable foundations**:
- C: the authority-boundary discipline.
- B: the observer contract.

Both serve every path.

**Independent domain work**: E (institutions), F (wealth/office) and G (ecology/settlement) can
proceed without D's recognition work.

**No world-side epic waits on an observer or inference outcome.** Nothing gates future development
on completing every Rule mapping or every domain.

---

## 5. Delivery path

**Working default trajectory: lineage.** It is the only candidate with a real mechanism-level proof
(§7.4); this is a local delivery default, not an owner-level question. **Whether it becomes a
player-facing proof is not established**: its composition is `BLOCKED` on a confirmed defect (§7.1),
and today no in-world carrier exists through which an observer could encounter the inheritance at
all (§7.2). A mechanism being `PROVEN CURRENT` does not make its player-facing projection feasible,
and "few new simulation mechanisms needed" is not the same claim as "cheap to deliver."

**Feasibility gate to run before committing to any candidate** (five questions, per external
review):
1. Can a real seeded run produce a consequential sequence from existing authoritative state/
   history, without inventing events or causes?
2. What traces could a player plausibly encounter through a proposed gameplay lens, and what might
   legitimately remain unknown?
3. Can an initial presentation preserve identity, chronology, and causal continuity across the
   relevant period?
4. Is the player-facing proof feasible with projection/integration work alone, or does the run
   reveal a missing simulation or evidence-production edge?
5. How does it compare in feasibility and experiential clarity to at least one other candidate
   trajectory?

**Current state of this gate for lineage: see §7.3/§7.5, which is authoritative.** In short: the
single death→heir hop is real; composing a second hop is `BLOCKED` on the natural-aging defect; the
observer questions are `BLOCKED` on a missing in-world carrier; the comparison is limited because no
second candidate qualified. None of the five questions is `passed`, so lineage is not a delivered or
committed product proof.

**The recognition-domain proof** (once §3.4's propagation gap closes): a player notices two
merchants treat the same character differently, and can reconstruct why from situated context (who
was where, when) — the scenario the whole investigation traced in code terms, now stated in player
terms. This proof requires its own capability-area work (§3.4) to exist at all, unlike lineage.

**Later closed-loop proof**, distinguished explicitly from reaction-only: changed opportunity must
feed a **later decision** producing a **durable, player-observable outcome** — not merely a merchant
reacting differently once. E.g., the hunter (from the recognition proof) is offered a materially
different contract as a result of standing, *accepts it*, and the acceptance produces a lasting
change (new location, new relationship, new resource) a player can later observe as a consequence of
the earlier recognition — chaining §3.3→3.4→3.4-opportunity→3.3 again, not one isolated reaction.

**Contrasting-domain proofs.** Lineage is a non-recognition, non-combat trajectory. It has
mechanism-level evidence for a single hop only; its world-side composition and its player-side proof
are both still open (§7). A second contrasting trajectory is available once §3.2's economy gaps
close: a craftsperson's wealth converting into a concrete leverage outcome (protection, patronage),
independent of any recognition work. That is portfolio Epic F.

**Evidence table**:

| Proof | Currently evidenced | Requires engineering | Evidence needed to claim delivery |
|---|---|---|---|
| Lineage (working default, gate partially run — §7) | Mechanism: yes, for the single death→heir hop (`PROVEN CURRENT`, re-confirmed 2026-09-27). Composition: `BLOCKED` on a confirmed defect (§7.1). Observer encounter: `BLOCKED` — no in-world carrier exists today (§7.2) | World side: Epic A, which resolves the defect and then runs a composed sequence. Player side: Epic B, which designs a minimal evidence-production and carrier path; the current observer sketch cannot be tested yet | World side: a real two-hop run through ordinary aging. Player side: an encounterable clue, *then* a blinded-human inference exercise per the calibrated criterion below |
| Recognition (later) | Partial — direct-interaction case only | §3.4's propagation gap, §3.5's projection | Scenario-runtime evidence: a seeded scenario where two observers diverge, sourced from real propagation, not a global-scalar read |
| Closed-loop (later still) | No | §3.4 opportunity-feedback + a later-decision trace | Scenario-runtime evidence spanning two decision points, not one |
| Economy (contrasting) | No | §3.2's wealth-conversion edge | Scenario-runtime evidence for one concrete declared edge |

**Evaluation criterion, calibrated per external review, 2026-09-26 — two separate checks, not one:**

1. **World-side truth check**: the underlying outcome has a coherent, Rule-conforming causal
   trace, and every player-facing clue originates from legitimate world evidence or an explicitly
   scoped projection of it — never fabricated for the demo.
2. **Player-side inference check**: given only the available clues, a player can form one or more
   *intelligible* hypotheses, distinguish observation from their own speculation, and revise an
   earlier interpretation when later evidence arrives. **The hypothesis does not need to be true** —
   only reasonably supported by the clues actually given. (The earlier draft's "a player can state a
   plausible causal account matching the real underlying state" wrongly turned this into "guess the
   correct hidden answer" — corrected here.)

**Explicit failure cases to test against, not just success cases**: an outcome the product expects
a player to understand but that has no meaningful clue leading to it at all; a nominally in-world
surface (biography, HUD, dialogue) that silently leaks hidden world truth; and behavior that changes
with no coherent world cause behind it. **Not every private event needs a publicly discoverable
trace** — salience and the product's own promised level of comprehension matter, and a genuinely
private event staying private is not automatically a failure.

An event being unknown to the player is not itself a defect. The defect is an outcome the product
presents as learnable or important with no fair, situated way to reason about it, or behavior that
violates the world's own causal rules — not mystery itself.

**`PLAYER-EXPERIENCED` is an evidence level, not a property automatically produced by a projection
existing in code** — a small player-observation exercise, or equivalent usability evidence, is
required before any proof in the table above can claim it, no matter how complete the underlying
mechanism or projection looks from source alone. **No existing infrastructure runs this exercise
today** (§3.6, external review correction, third round) — it would need to be a new, explicit
usability check, not an automatic SimQ/M3 side effect.

---

## 6. Decision bridge — Catalog × Semantic Control Plane × Systemic Roadmap (added 2026-09-27)

**Keeping the three authorities distinct, per external review**: the World Rule Catalog specifies
target semantics. The Semantic Control Plane (SCP) records Rule↔Mechanism relationships,
classifications, and evidence — **currently, only for Territory/Control (`TERR-*`) and Combat/
Conflict's 10 inherited-from IDs** (`registries/rule_classifications.yaml`, 14 rows total,
re-verified 2026-09-27; every other family is `UNKNOWN` from the SCP's own formal-mapping
perspective, per its own corrected status above — not because those Rules are unmapped-and-
therefore-broken, but because M0-M4 never touched them by design). The systemic roadmap (this
document) identifies capabilities the *engine* still needs. **Mapping coverage does not dictate
product priority, and full-Catalog mapping is not a gate on anything below.**

Three levels kept separate per capability area: **semantic target** (what the Rules specify),
**realization/integration** (what the engine does, per Parts A/B and this round's own direct
registry/test checks), **player observation** (which legitimate traces a player could encounter).

| Area | Related Rules (SCP-mapped only where noted) | Realization/integration evidence | Consequential gaps | Missing evidence | Player-facing-proof potential |
|---|---|---|---|---|---|
| 3.1 World substrate | Milestone A (`ID-*`/`TIME-*`/`AUTH-*`/etc.) — **not SCP-mapped**, Catalog-level only | `TCK-20260401-ACTION-CONVERGENCE`'s replay-determinism law, verified. Regional-sovereignty dual-writer bug confirmed live (verified current, this session, 2026-09-23/24). | Two confirmed authority-invariant violations with distinct mechanisms (region ownership; lifecycle-active race). | Bounded audit run (§3.1): 5 planned boundaries (1 defect, 3 `UNKNOWN_WITH_REASON`, 1 fine), plus 1 unplanned defect. Everything outside the named set stays `UNKNOWN`. | Indirect only — a player never sees this layer directly. |
| 3.2 Autonomous world dynamics (lineage slice) | `SOC-01` (Batch 09) — **not SCP-mapped** | `succession`/`aging_death` mechanisms, `registries/mechanisms.yaml`, `state: done`, `verified: {instrument: scenario, verdict: observed}` — the strongest evidence tier this repo uses. Two individual death-to-heir transitions re-run and confirmed passing 2026-09-27 (`tests/simulation_quality/test_heir_inventory_transfer_corpus.py`, `tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py`) — **evidence for those specific (artificially-staged) transitions, not a composed longer sequence**. | Whether individual, proven transitions compose into a *longer*, multi-generation observable sequence — **now `BLOCKED`, not merely untested (fourth round, §7.1)**: a real, reproducible dual-writer race on `entity.lifecycle.active` (`ApplyPath` vs. `LifecycleSystem.resolve_lifecycle`) prevents succession from firing at all for a death that arrives through ordinary per-tick aging rather than pre-staging. | Chronology-over-a-real-period, identity continuity across many ticks — `BLOCKED`, not fabricated, moot until §7.1's defect clears. | High on single-transition mechanism evidence. Single-hop player-facing feasibility is `BLOCKED` until an evidence producer and an in-world carrier exist (§7.2). Composed-sequence feasibility is gated on a confirmed defect fix (§7.1, §8). |
| 3.3 Situated agency | `AGENCY-*`/`PERC-01`/`KNOW-01` — **SCP-mapped, all `PARTIAL`** (`registries/rule_classifications.yaml`, re-verified 2026-09-27) | Part A's own direct trace: Combat/Harvest/Quest-reward dispatch real; intent→payload edge `UNKNOWN`. | Shared upstream edge untraced across all three families. | Same. | Indirect — substrate beneath any future lens. |
| 3.4 History and feedback (recognition) | `SOC-01`/`HP-*` — **not SCP-mapped** for the recognition-specific finding (the mapped `AGENCY`/`PERC`/`KNOW` rows above are Combat's own citations, not this area's) | Part B's own direct trace: `bonds`/`trust_history` real for direct participation; no producer for witnessed/hearsay. | The confirmed narrowest bottleneck in the whole arc. | Three-way primitive split still `OPEN` (§3.4). | Requires §3.4's own work to exist at all first. |
| 3.5 Observation/player delivery | None — explicitly outside Catalog scope | Epistemic principle (§2) only; no gameplay lens chosen. | Everything — genuinely new area. | Everything not yet designed. | This *is* the delivery layer once built. |
| 3.6 Evaluation | None — infrastructure, not a Rule area | SimQ/corpus-tier/M3 all real, live, unrelated to this roadmap's own scope. | None new; this roadmap's job is feeding it findings. | N/A | Indirect (regression-catching). |

**Discipline honored**: `UNKNOWN` is reported as `UNKNOWN`, not inferred as `MISSING`, for every
family the SCP hasn't formally mapped — the Catalog's own prose Repository Findings (e.g. `ME-S12`,
`IP-S17`, cited earlier this arc) remain valid Catalog-level evidence in their own right; they are
simply a different evidentiary tier than an SCP-registered classification, and this table doesn't
conflate the two. No full-Catalog sweep was run to produce this table — only the Rules and
mechanisms needed for the candidates actually under consideration in §7 were inspected.

## 7. Feasibility gate results — lineage vs. economy/wealth and other candidates (2026-09-27)

**Comparison candidates chosen**: economy/wealth (confirmed `BLOCKED` — no conversion mechanism
registered anywhere), plus a bounded search this round for a second, genuinely-different-shape
candidate (below). Every claim in this section is scoped to what was actually run or read, not
narrated.

### 7.1 Composition probe — actually executed, not merely reasoned about

A throwaway investigation script (not committed, not under `tests/`) built a 3-entity scenario
(grandparent → parent → grandchild) reusing the exact `V2EntityBuilder`/`Kernel` technique the two
repo tests use.

**Tick 0 — real, composed inheritance, succeeded**: one real `kernel.tick_once()` produced, read
directly from `kernel.state` afterward: the grandparent inactive with `death_reason="OLD_AGE"`; the
parent's inventory gaining the grandparent's item alongside its own; the parent acquiring an
`inherited_nemesis_99` blocker (severity halved per `LifecycleSystem`'s own multiplier); and a real
dying-wish `NamedIntention` seeded with `source_entity_id=1`. This confirms the single hop is real
and reproducible, exactly as the two repo tests already established — nothing new here.

**Extending to a second, later-tick hop — a confirmed defect, not an unknown**: composing a *second*
hop (the parent later dying through **ordinary, ungimmicked per-tick aging** rather than the
"already past max_age" staging trick both repo tests use) surfaced a real, reproducible defect,
verified empirically by running 5 real ticks and reading `kernel.state` after each one:

```
tick= 1 subject.age_ticks=1 active=True  death_reason=None  heir.inventory=[]
tick= 2 subject.age_ticks=2 active=True  death_reason=None  heir.inventory=[]
tick= 3 subject.age_ticks=3 active=False death_reason=None  heir.inventory=[]
tick= 4 subject.age_ticks=4 active=False death_reason=None  heir.inventory=[]
tick= 5 subject.age_ticks=5 active=False death_reason=None  heir.inventory=[]
```

The subject goes inactive at tick 3 and **stays that way forever with `death_reason=None`** —
`LifecycleSystem.resolve_lifecycle`'s own OLD_AGE branch never fires, and no succession/heirloom/
feud/dying-wish dispatch happens at all. **Root cause**: `resolve_lifecycle`'s own OLD_AGE check
(`src/systems/lifecycle_systems/lifecycle.py:193-194`) reads `age_ticks` as persisted at the *end of
the prior tick*; `ApplyPath._compute_entity_changes` (`src/engine/apply.py:94-99`) independently
computes `new_age = age_ticks + 1` and commits `active=False` **one tick ahead**, with no
`death_reason` and no heir dispatch, in the *same* tick's commit. Next tick, `resolve_lifecycle`'s
own `if not entity.lifecycle.active: continue` guard finds the entity already inactive and skips it
— succession never runs. **Why the two existing repo tests never hit this**: both stage `age_ticks`
already massively past `max_age_ticks` from the tick-0 starting snapshot, so `resolve_lifecycle`'s
check fires immediately in the very first tick, before the passive branch ever gets a chance to race
ahead on some later tick. The race only exists for a death arriving gradually, in the ordinary run
of the simulation — exactly the case a longer, composed lineage sequence would need.

**This violates the same authority invariant §3.1's bounded audit exists to check** — a durable
field (`entity.lifecycle.active`) committed without a declared precedence rule between its two
writers — found here independently, by running code rather than reading it. **Its concrete mechanism
is a same-tick evaluation-order race (a stale prior-tick read vs. a one-tick-ahead write), distinct
from boundary 1's dual-representation mismatch (§3.1)** — the same invariant, a different bug, not
assumed identical. **Narrowest confirmed blocker, stated exactly**: this is not
a scenario-setup problem, not a missing runtime integration, and not a missing evidence-production
gap — it is a real, reproducible simulation defect. (A combat-triggered second death was not tried as
an alternative path this round; a static read suggests it does not share this specific age-based
race, but that is untried, out of this probe's bound.)

### 7.2 Minimal provisional observer position + evidence packet (design check only)

**Not** a real player-observation exercise — `PLAYER-EXPERIENCED` is not claimed for anything below.

**Position**: a townsperson NPC with an existing `SocialComponent.bonds` entry to the deceased or
heir, co-located at the death site. **Candidate early clue**: the heir now carries an item they
did not carry before, shortly after a nearby death. **This is a potential trace in world state,
not a clue the observer can currently encounter — corrected 2026-09-27 by a read-only code
inspection**:
- No in-world carrier delivers another entity's inventory or equipment to an observer.
  `PerceivedEntity` (`src/core/cognition.py:28-33`) holds only id, kind, position, salience and
  confidence.
- `PerceptionUpdatePhase` (`src/domains/perception/phase.py`) has no production caller outside its
  own module (verified by grep).
- `KnowledgeModelService` assimilates only paid information facts (resources, recipes, danger,
  leads).
- The one real in-world effect of the death is the grief trigger for trusted allies
  (`src/observability/event_extractor.py:1722-1762`). It carries the death, not the inheritance.
  It is trust-scoped and location-independent, which itself deserves a look under the epistemic
  principle (§2, §3.4).

**No inheritance-origin signal exists either** (`ResourceTransferIntent(source_kind="CHEST")` at
`lifecycle.py:252-257` carries no provenance). So even with a carrier, the clue would be only
"this person now carries an item."

**If a carrier existed**, the reasonable hypothesis "this person is the deceased's heir" would be
plausible but unprovable. The fallback heir selector picks the highest-bond candidate, not a socially
designated heir, and item possession cannot distinguish an heir from a looter. The confirming later
clue (the heir acting on the inherited grudge or dying wish) also cannot occur today (negative
check 1).

**Negative check 1 (no discoverable trace)**: the inherited nemesis blocker and dying wish are pure
cognition/strategic internal state — `LifecycleSystem._seed_dying_wish`'s own docstring states
plainly that nothing in this codebase reads `NamedIntentionBundle.status` to force an action. No
system converts either into any player-observable signal today. If the product ever expects a player
to notice "this NPC now secretly resents someone," there is currently **zero** discoverable trace —
exactly the failure case §5's evaluation criterion warns against (this may be a fine, intentional
private-hook state for now — just not yet exposed, not evidence against the mechanism itself).

**Negative check 2 (a named leak-risk)**: any future biography/HUD projection rendering
`EntityState.cognition.motivation.named_intention` or `EntityState.strategic.blockers` verbatim to
the player would leak literal internal world-truth as if it were ordinary public knowledge — the
same discipline `KnowledgeModelService`'s "hidden world truth is never injected" invariant already
enforces for NPCs. These two fields are named precisely as the leak surface for future projection
work to guard against.

### 7.2.1 Combat-death trace findings (Epic B0, TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY)

A sibling check to §7.2's aging-death case, run against a combat death instead: an entity killed
in combat and recorded with `death_reason == "COMBAT"`, rather than natural aging.

**Q1, empirically confirmed, not `BLOCKED_WITH_REASON`**: a real, deterministic
`Kernel.tick_once()` forced-attack scenario (goblin vs orc,
`mechanic_scenario_combat_judgement_withdrawal`) produced `lifecycle.active == False` and
`lifecycle.death_reason == "COMBAT"` in the same tick, through the real
`CombatResolutionSystem.resolve_attack()` -> `LifecycleSystem.resolve_lifecycle()` path. Combat
deaths are real and structurally correct when they occur. Caveat carried from `registries/
mechanisms.yaml`'s `tactical_decision` entry (`verified: corpus_run, verdict: contradicted`): real
unscripted `ATTACK` dispatch is rare in ordinary corpus play (0-2 per 1000-2000 ticks) -- both
facts recorded, not merged.

**Answer 2 (trace existence, kept separate from Answer 3)**: the same tick a combat death
resolves also produces lifecycle deactivation/classification, heir dying-wish/inherited-feud
writes, heirloom/inventory transfer with no provenance marker (the identical finding §7.2 already
records for the aging-death lineage case -- this is the same transfer mechanism regardless of
`death_reason`), faction influence shift, conquest/stronghold lifecycle, an economic vacancy
signal, the grief trigger for trusted allies, and a set of developer-only observability surfaces
(`CombatDamageEvent`/`CombatKillEvent`/`hero_death_unrecorded`, `event_shapers.py::CombatShaper`,
`GriefUrgencyTriggeredEvent`/`NemesisRelationFormedEvent`, `src/observability/live/*`,
`src/api/presenters/*`, the `REFINED_UPDATE` replay stream). `docs/mechanics/
04_strategic_cognition.md` §13's "witnessing combat" third tier (§13.7) does not exist as a
runtime mechanism -- the whole section is headed "Status: declared, not yet implemented," and
parity ledger `STRAT-273` (`status: missing`) independently confirms it.

**Answer 3 (situated encounterability, kept strictly separate from Answer 2)**: the grief trigger
(`src/observability/event_extractor.py:1722-1762`) is the ONLY real trace any runtime consumer
legitimately receives from a combat death, and only for a bonded observer
(`trust_history >= ALLY_TRUST_THRESHOLD`, 0.30) -- never for a co-located-but-unbonded observer,
since the path carries zero proximity/perception check anywhere. This is a legitimate encounter
for the bonded category specifically (a real authoritative `StrategicUpdate`, not a
developer-only surface); it is location-independent, which is a named tension with the epistemic
principle (§2, §3.4), not resolved here. All other traces (inheritance, faction, conquest,
economy) exist but are not encounterable by any observer today, for the same reasons already
established in §7.2: `PerceivedEntity` (`src/core/cognition.py:28-33`) has no item/event field,
and `PerceptionUpdatePhase` has zero production call sites.

This closes the combat-specific half of §11 item 3's Epic B0 owner note -- the aging-death
lineage case (§7.2) and this combat-death case are sibling findings, reaching the same
"perception inactive, one location-independent trust-keyed exception" conclusion from two
independent runtime checks.

### 7.3 Gate question table

| Gate question | Lineage | Economy/wealth (comparison) |
|---|---|---|
| **1. Consequential sequence from real state/history, no invented events?** | **Partial, with a confirmed blocker on composition.** The single hop is real, not fabricated (§7.1). Composing a *second*, ordinary-aging hop is not merely unchecked — it is **`BLOCKED` by a confirmed defect** (§7.1's dual-writer race). This is stronger information than "unknown": the blocker is named and reproducible, not just untried. | `BLOCKED` — no mechanism entry for `protection`/`patronage`/wealth-conversion exists in `registries/mechanisms.yaml` at all; `PROTECTION` contracts are confirmed constructed only in `src/certification/scenarios.py`, zero production call sites (Part B). |
| **2. Player-plausible traces / legitimate unknowns?** | **`BLOCKED`** — the candidate clue exists in world state, but no in-world carrier delivers it to a situated observer, and no inheritance-origin signal exists (§7.2; verified by read-only code inspection 2026-09-27). The design sketch names what a legitimate trace would need; it cannot be tested yet. | `UNKNOWN`, moot until question 1's blocker clears. |
| **3. Identity/chronology/causal continuity over the relevant period?** | **`BLOCKED`, not merely unknown** — the same composition defect that blocks Q1's second hop blocks any multi-tick chronology check by construction; there is no longer sequence to check continuity over until §7.1's defect is addressed. | `UNKNOWN`, moot for the same reason as Q2. |
| **4. Projection/integration alone, or a missing simulation edge? (three separate sub-answers, per the finalize instruction)** | **(a) Does the tested transition need another simulation edge?** No — the single hop is real and correct as tested. **(b) Does its evidence production exist?** No — confirmed absent by direct inspection (§7.2); no provenance/evidence producer exists for an inheritance event. **(c) Could a situated projection be built from it?** Not today — it needs both an evidence producer and an in-world carrier (§7.2), and a projection across a *second* hop is additionally blocked by §7.1's defect. | **A missing simulation edge, confirmed** — no registered mechanism exists to project from at all. |
| **5. Comparison** | See §7.4 — no second candidate qualified at lineage's evidence tier; comparison stays limited, not conclusive in lineage's favor. | Same limitation from the other side. |

### 7.4 Candidate comparison — bounded search, no artificial winner

Beyond economy/wealth, this round searched (bounded keyword sweep of `registries/mechanisms.yaml`,
not a full repo sweep) for a second, genuinely-independent candidate:

- **Environmental threat/calamity** (`regional_trauma`, `calamity_intensity`) — **disqualified,
  and in worse shape than economy**: both are `state: done`, but both carry
  `verified: {instrument: corpus_run, verdict: contradicted}` — a real run was executed and it
  disproved the mechanism firing (`TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`,
  `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`, both already-open). Economy simply has no
  mechanism registered; this domain has one that was built, wired, and then directly falsified.
- **Displaced family/feud** — **not independent**: no `displacement`/`feud` mechanism id exists
  separately; the roadmap already treats these as part of the *same* `succession`/`aging_death`
  family as lineage. Choosing it as a "second candidate" would be a lineage variant, not a
  contrasting causal shape.
- **Institutional/office consequences** (`IP-S17`) — **disqualified, reconfirmed**: no
  `institutional_standing`/`office` mechanism id exists; the one institution-adjacent entry
  (`belief_institution`) is `state: partial` with a confirmed dead half (no general assimilation
  writer). `IP-S17`'s prior `MISSING` finding stands.

**Result, stated honestly**: no second candidate qualifies at lineage's evidence tier (`state: done`,
`verified: observed`, a real passing test through a real game tick, a genuinely different causal
domain) after this bounded search. **Comparative experiential clarity: `UNKNOWN`, bounded search
exhausted** — scope was the three candidate families above, checked in one registry file, not a
full sweep. Lineage remains the only candidate with a real single-hop mechanism proof; economy is
`BLOCKED` on a missing mechanism, and environmental/calamity is *worse* — `contradicted` by a real
run, not merely missing.

### 7.5 Gate verdict, stated precisely

No question is `passed`, for any candidate. Lineage is `partial` on Q1 (real single hop;
composition `BLOCKED`), `BLOCKED` on Q2 (no in-world carrier, no provenance signal), `BLOCKED` on
Q3 (moot until Q1's defect clears), and split three ways on Q4 (mechanism: yes; evidence production:
no; projection: not buildable today). Economy/wealth is `BLOCKED` on Q1/Q4, `UNKNOWN`/moot on Q2/Q3.
Q5 is limited for both. **This is a feasibility result with two load-bearing blockers — one
world-side (§7.1's defect) and one player-side (no encounter path, §7.2) — not a completed gate and
not a player-facing proof.** It does not disqualify lineage: the single hop is still the strongest
mechanism evidence of any candidate checked.

## 8. Epic portfolio and first-wave selection

The portfolio is outcome-based. It is not one epic per capability area: an epic may cross areas,
and an area may need several epics. Lineage is one probe, not the organizing axis.

**How to read the evidence column.** "Inherited" means cited from earlier investigation (Parts A/B,
Catalog batch findings) and not rechecked in this pass. "Verified 09-27" means checked in the
current repository this week.

| Epic | Capability area(s) | Domain owner(s) | Rule support | Current evidence maturity | World outcome | Observer value | Independent prerequisites | Wave |
|---|---|---|---|---|---|---|---|---|
| **A** Life/death and cross-tick continuity | 3.1, 3.2, 3.4 | engine apply; lifecycle/lineage | `SOC-01`, `HP-*` (Catalog; not SCP-mapped; inherited) | Single hop verified (staged); natural-aging defect reproduced (verified 09-27) | Deaths recorded with cause; lineage persists over ticks | Indirect, via B | Its natural-aging defect is ready for planning, scheduled by a trigger (plan §3) | Later |
| **B** Situated evidence and observer contract | 3.5, 3.4 | perception/observation plus the probe event's domain | None (observation is outside Catalog scope by design) | Encounter `BLOCKED`, provenance `ABSENT` (verified 09-27) | — (design) | Enables every later player-inference proof | B0 result; owner memo decision 2 (probe event) | Later — its bounded precursor B0 is first wave |
| **C** Authority-boundary verification program | 3.1 | one per boundary | `AUTH-*` (Catalog; not SCP-mapped) | Audit of 5 planned boundaries run: 1 defect, 3 `UNKNOWN_WITH_REASON`, 1 fine; plus 1 unplanned defect (verified 09-27) — boundary 2 → `DEFECT_CONFIRMED` by C1, 2026-10-01 (§3.1 addendum) | Declared resolution at named boundaries | None directly | None | **First wave: C1 (entity death) only.** Diplomacy and reputation are tracked outside the wave, with revisit triggers (plan §3) |
| **D** Individual history propagation (witness/hearsay) | 3.4 | social memory / cognition | `SOC-01`, `HP-*` (inherited) | Direct-participation history real; witness/hearsay producer `MISSING` (inherited, Part B) | Uninvolved witnesses and hearsay recipients form subject-specific beliefs | High (the recognition proof) | For a player proof: B's contract. World side: none | Later |
| **E** Institutional judgment and authority | 3.2, 3.4 | institutions | `IP-S17`, `INST-03` (inherited) | No per-(institution, individual) standing mechanism (registry checked 09-27) | Institutions hold judgments distinct from personal ones | Medium | Owner memo decision 3 | Later |
| **F** Wealth/office conversion through declared edges | 3.2, 3.4 | economy; institutions | `ME-S12` (inherited) | No conversion mechanism registered (verified 09-27) | Wealth converts to leverage only through declared paths | Medium | None (independent of D) | Later |
| **G** Ecology/settlement dynamics | 3.2 | world dynamics / ecology | Batch 05 (inherited) | `regional_trauma`, `calamity_intensity` contradicted by corpus runs; open tickets exist (verified 09-27) | Environmental pressure actually changes the world | Medium | Existing open repair tickets first | Later |
| **H** Agency across action and non-action processes | 3.3 | action dispatch / agency | `AGENCY-*` (SCP-mapped, `PARTIAL`) | 3 dispatch paths; intent→payload edge `UNKNOWN` (inherited, Part A) | Coherent attempt semantics, including world processes | Indirect | None | Parked (`UNKNOWN`) |
| **I** Magic and culture breadth | 3.2 | magic; culture | Batches 11B/12 (inherited) | Weakest realization; the magic perception channel is inert (inherited) | — | Later | — | Parked |
| **J** Bounded mechanism reachability | 3.1, 3.2 | the domain that owns each selected mechanism | per mechanism | A bounded initial set with existing evidence of not acting: `calamity_intensity` and `regional_trauma` (contradicted by corpus runs; open tickets exist) and `aging_death`/`succession` (act only when ages are staged). This is **not** an engine-wide audit (§11 item 5) | Each of three named mechanisms (J1 `calamity_intensity`, J2 `regional_trauma`, J3 `aging_death`/`succession`) gets an explicit outcome on four levels; J1/J2 link their existing open tickets | Indirect | None | **First wave** |
| **B0** Situated-observation feasibility check | 3.5 | perception/observation plus the selected event's domain | None (outside Catalog scope) | Perception has no production caller per a grep: `UNKNOWN` at runtime (§11 item 3) | — (feasibility) | Reports separately whether a combat death in an ordinary run leaves a trace, and whether a situated observer can legitimately encounter it. Not a player-experience proof | None | **First wave** |

**Proposed first wave: bounded reachability-first — J + B0 + C1** (owner memo decision 1). The
detail is in `first_wave_plan.md`. External review supports this direction in principle.
- **J** answers, for three named mechanisms, whether and how each acts in ordinary runs.
- **B0** checks at runtime whether perception is live. For one combat death in an ordinary run, it
  reports separately whether a trace exists and whether a situated observer can legitimately
  encounter it.
- **C1** resolves the entity-death authority boundary.

Better behaviour in ordinary runs is a hypothesis this wave tests, not a promised result. The wave
also does not:
- claim player inference or a changed life trajectory;
- schedule the natural-aging fix, which waits for a trigger (plan §3);
- run the diplomacy and reputation checks, which stay outside the wave with owners and revisit
  triggers.

Region ownership (FAC-010) stays on its own track.

## 9. Evidence workflow — existing registry/Semantic Control Plane tooling

Per the finalize instruction's §1: real commands run against the current repo, not invented ones.
Smallest incremental improvement only — explicitly not a second registry, a universal ontology, or
an early Stage-F Context Compiler.

**Q1 — given a Rule/domain capability, which formal mapping/mechanism/classification/evidence
exist?** No general-purpose query tool exists.
`tools/semantic_control_plane/generate_territory_control_view.py` is hardcoded to exactly two
domains (Territory, Combat) — no `--rule` argument for an arbitrary Rule ID. The real recipe today:

```python
import yaml
edges = yaml.safe_load(open('registries/rule_mechanism_edges.yaml'))['edges']
len(edges)                                      # -> 18
sorted(set(e['rule_id'] for e in edges))         # -> 14 distinct Rule IDs, everything else UNKNOWN
```

**Named gap**: no CLI/function does this lookup — a hand-rolled YAML filter every time.

**Q2 — given a mechanism/changed path, which mapped Rules/downstream relationships/scenario checks
need revalidation?** `tools/semantic_control_plane/registry.py` has real, working `consumers_of()`/
`producers_for()` — but only over `mechanism_causal_edges.yaml` (mechanism→mechanism chains). **No
equivalent reverse lookup exists from `mechanism_id` → citing `rule_id`** in
`rule_mechanism_edges.yaml`. Verified directly: `succession`/`aging_death` both return zero SCP
edges — consistent with "not SCP-mapped," but confirming it took a manual scan, not a query.

**Q3 — what's formally mapped vs. Catalog-prose-only vs. no evidence yet?** Already answered
structurally by Q1's 18-edge/14-Rule-ID count. `registries/rule_classifications.yaml`'s own header
is explicit that `UNKNOWN` must never be conflated with `MISSING` — real, working, already-documented
discipline, not a gap.

**Q4 — which paths/evidence have drifted since last verification?** Real, working tool, actually run
against current HEAD:

```
$ python3 tools/semantic_control_plane/mapping_drift_check.py
Mapping drift check (report-only, never fails): 0 cited-code drift finding(s), 0 verdict drift finding(s)
$ python3 tools/semantic_control_plane/registry.py
OK: rule_mechanism_edges.yaml, mechanism_causal_edges.yaml, rule_classifications.yaml valid
```

No gap here.

**Tooling follow-up (not scheduled; implementation belongs to whoever owns SCP tooling).** The one
concrete query gap is a reverse lookup: from a mechanism, find the Rules that cite it. It
belongs in the existing SCP registry API, next to its existing mechanism-edge queries. A second
registry or a general query CLI is not needed for this gap, and neither is proposed. Every other
question above already has a working answer today.

## 10. Owner decisions

Owner-level choices live in one place only: `owner_decision_memo.md` in this folder. It has six
entries:
1. the first-wave epic set;
2. whether inheritance is meant to be player-understandable;
3. whether individual and institutional standing are distinct concepts;
4. what `public_reputation` means;
5. how world time scale relates to feasible run length;
6. where player-inference evidence will come from.

Engineering choices (record types, class reuse, the fate of the unused `ActionProposal` model,
field layouts, the technical fix for §7.1) belong to the ticket planner and implementation agents,
not to the owner or to this roadmap.

## 11. Open strategic questions and risks (raised 2026-09-28)

These are points the roadmap has not settled. Each names its owner or decision point.
Implementation detail is deliberately left out.

1. **The first wave has no visible payoff.**
   - Epic A's defect only fires at the default lifespan, about 20M ticks; corpus runs are 1k–5k
     ticks. Epic C only verifies. Epic B only designs.
   - As planned, typical runs would behave the same after the wave, and no player-side claim would
     move.
   - Several review rounds have produced documents, while the one real defect found so far came
     from running code.

   *Decision point*: owner memo decision 1. The proposed reachability-first wave (§8) tests
   ordinary-run behaviour directly, as a hypothesis rather than a promised visible change.

2. **Time scale versus run length is unaddressed.**
   - Lineage is the roadmap's main probe for persistent history.
   - The current corpus runs do not naturally reach generational succession, so today it can be
     shown only through chosen initial conditions (staged ages).
   - Whether other long-horizon domains, such as institutions or ecology, have the same problem is
     `UNKNOWN`; each needs its own evidence.

   *Decision point*: owner memo decision 5. It does not block the bounded reachability work.

3. **Situated perception may be an engine gap, not a presentation gap. `UNKNOWN`, needs
   verification.**
   - A grep-level check found no production caller for the perception update phase (§7.2).
   - Other knowledge flows found so far are paid information facts or location-independent reads:
     the grief trigger, and `public_reputation` used as a global fallback.
   - If this is confirmed at runtime, NPCs are also not situated observers. That would make situated
     perception a core foundation affecting every domain, and it would re-rank Epic B above lineage
     work.
   - Perception could run through another path that a grep does not reveal, so this is not yet a
     finding.

   *Owner*: first-wave Epic B0, the situated-observation feasibility check. If perception is
   confirmed inactive at runtime, record that as an engine foundation finding, and propose a separate
   perception-foundation epic with its dependency implications. The wave is not expanded. Grep alone
   never establishes this finding.

   - **Resolved for the combat-death path (TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-
     ENCOUNTERABILITY, 2026-09-29)**: the perception update phase is confirmed still inactive at
     runtime -- consistent with, not new evidence beyond,
     `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`'s own finding. The one new finding
     this ticket adds beyond that ticket is the grief trigger's location-independence as a live,
     real (non-perception) trace path with no distance or channel constraint -- named as worth a
     future look under the epistemic principle, not remediated here. This does NOT re-rank Epic B
     above lineage work per this item's own decision criterion: the grief trigger is a real,
     working, bonded-only trace path, not evidence that NPCs are non-situated observers across the
     board. The broader perception-is-an-engine-gap question remains owned by
     `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`, unchanged.

4. **There is no route to player-inference evidence yet.**
   - A blinded proxy reviewer can give *formative* evidence, which is useful for design and labelled
     as a proxy.
   - A `PLAYER-EXPERIENCED` claim requires an appropriately blinded player-observation exercise.
   - The only human currently involved knows the answers, so neither tier has a source yet.

   *Decision point*: owner memo decision 6. It does not block the bounded reachability work.

5. **Registry maturity may be overstated across the engine. Extent `UNKNOWN`.**
   - Three independent cases this arc: two mechanisms contradicted by corpus runs, and succession
     that fires only when ages are staged.
   - All are `state: done` mechanisms that don't act in ordinary runs, and the observer clue this
     roadmap first planned around turned out not to be encounterable.
   - A bounded reachability epic (portfolio J) may deliver more world liveliness per unit of work
     than new capability.
   - Three cases do not measure the scale, and "does not fire in an ordinary run" is not the same as
     "defective". A rare or conditional mechanism can be correct.
   - So J is bounded to an initial set of consequential mechanisms with existing evidence (§8). Each
     selected mechanism gets an outcome on four separate levels:
     - **trigger reachability**: can its precondition arise in ordinary play?
     - **feasible run horizon**: does it arise within a run we can afford?
     - **actual state effects**: when triggered, does it change authoritative state as declared?
     - **observer evidence**: does any legitimate trace exist? This level is recorded, not required.
   - Each mechanism's exit claim is one of:
     - *acts in ordinary runs*;
     - *legitimately rare or conditional*, with the condition stated;
     - *defect*, routed to separate work;
     - *registry label corrected*;
     - `BLOCKED_WITH_REASON`.
   - Expanding the set is a separate, later decision; J does not become an engine-wide audit.
   - J's set is exactly J1 `calamity_intensity`, J2 `regional_trauma` and J3 `aging_death`/
     `succession`. J1 and J2 link their existing open tickets, which are not duplicated.

   *Decision point*: owner memo decision 1.

   - **Resolved for Card J (TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING,
     2026-09-29)**: all three of J's mechanisms received a four-level assessment, re-verified
     against current worktree HEAD (`702c3af83`), not merely cited from the adopted tickets.
     - **J1 `calamity_intensity`** maps to *defect, routed to separate work* — a grep-level
       confirmation found `CalamityService.apply_calamity_consequences()` has zero real callers
       anywhere under `src/`, a deeper finding than the adopted ticket's original composition-gap
       framing (Level 1 fails structurally, before the trigger condition is even reachable). The
       registry write for this label is a **recommendation only**, routed to
       `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION`, which already owns
       `calamity_intensity`'s registry `state` reconciliation — two tickets must not write the same
       entry.
     - **J2 `regional_trauma`** and **J3 `aging_death`/`succession`** both map to *legitimately
       rare or conditional, with the condition stated* — neither needs a registry write, since
       each mechanism's current registry label already states its condition accurately. J2:
       `generated_frontier_3_42`'s `moon_cave` region is spatially isolated from every hostile
       faction (confirmed by a real 5000-tick `Kernel.tick_once()` run recording
       `trauma_score == 0.0` throughout), a fixed geometric fact of the world's composition, not a
       wrong threshold or broken accrual code. J3: the default lifespan (20,160,000 ticks) is
       ~4,032x–20,160x longer than any real corpus run this repo's evidence cites — the mechanism
       is proven correct via staged-scenario technique (the already-merged
       `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE` fix, `5d4e4a237`), but natural aging
       death by ordinary accumulation remains unobserved in any real corpus run.
     - **Shared-root-cause hypothesis, checked, not confirmed.** J2's spatial-isolation cause and
       the out-of-scope `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`'s zero-effect symptom
       are, on inspection, opposite causes: J2 has no entities co-located to fight; the other
       ticket's sampled region has entities correctly co-located and genuinely dying, but
       `resolve_lifecycle()`'s own death-outcome-kind filter is missing `"DEFEAT"` (only checks
       `"KILL"`/`"PERMADEATH"`) — a code-level filter gap, not a composition condition. Stated
       here, per this ticket's own instruction; not absorbed into this ticket's scope.

6. **Governance overhead.** This track spans several authorities: the Catalog, the SCP, the mechanism
   registry, the parity ledger, this roadmap and its companions, and multiple planning sessions.
   - Each keeps its own status vocabulary, and some state is summarized in more than one of them.
     For example, gate results appear in §7 here and in the plan.
   - Risk: drift between documents, and review cycles consuming effort better spent on runs.
   - Proposal: once the direction is accepted, stop revising these documents except to record
     verified results.

   *Owner*: this planning session, subject to the owner's acceptance of the direction.

---

## Appendix: External review response log (historical)

Moved out of the decision-bearing body per the fifth external review round's own request, so the
capability map (§0-§7) and current decision evidence (§8-§10) stay easy to read. These are **dated
records of what changed and why at the time**, not current status — current status always lives in
the numbered sections above; where a historical entry below has been superseded, it is marked so
inline rather than silently left to look current.

### Round 1 response, 2026-09-26

Responding to `review_history/external-ai-review-systemic-world-roadmap-instruction.md`, mapped to its five
required-change areas:

1. **Lineage reclassified** from committed first proof to leading candidate, gated by a five-
   question feasibility check (§5) — the check has not been run; selection is `OPEN`.
2. **Player-understanding criterion split** into a world-side truth check and a player-side
   inference check (§5), with explicit failure cases and an "unknown ≠ defect" clarification added.
3. **Broad status claims narrowed** throughout §3 — `DESIGNED`/"no Rule needed" now scoped to "within
   the frozen Catalog's current scope"/"the cases investigated," never an implied claim about the
   whole future engine; `PLAYER-EXPERIENCED: N/A` replaced with "not directly surfaced"/"experienced
   indirectly, not yet evaluated" for world substrate, agency, and evaluation; §3.4's wording no
   longer implies `bonds`/`trust_history` is the decided destination for witnessed/hearsay evidence.
4. **§3.1's foundation verification bounded** — replaced the unfalsifiable "absence of recurrence"
   framing with a stated, finite scope (most consequential cross-domain mutation paths, reviewed at
   their boundaries, with named remaining `UNKNOWN`s), and restated the semantic obligation precisely
   (canonical authority + a declared resolution rule, not one writer or one universal `revalidate()`).
5. **Owner Decision List reframed** — item 1 restated as the real semantic question (are individual
   and institutional standing distinct concepts, not just different record shapes) with a Rule-
   sourced default; item 2 downgraded from open decision to a proposed default, escalated only on a
   real conflict; item 3 reframed as "define the meaning first," not a retain/retire choice; item 4
   (promotion path) removed as a numbered item and replaced with the real near-term choice — which
   candidate the feasibility gate runs against first.

**External-review concerns rejected on repository evidence: none.**

### Change summary — five-phase draft to capability map, 2026-09-26

The prior document (`evidence/rpg-core-foundational-synthesis-and-roadmap-revision.md`'s original
"Revised capability areas") organized around a five-*phase* sequence, scoped only to the Action-
Recognition-Opportunity loop this investigation traced most deeply. This document:

1. **Widens scope to the whole engine** — the recognition loop is now one thread (Path 1) among
   several, not the organizing principle.
2. **Replaces phase-sequence framing with a capability-map framing** — dependency is stated per-path
   (§4), not assumed universal; Paths 2 and 3 need none of Path 1's recognition work.
3. **Adds the product north star and epistemic-delivery principle** (§1-2) — new content reflecting
   the owner's newly clarified product direction, not present in any prior document this arc.
4. **Applies the four corrections** the instruction identified in the foundational synthesis
   directly (state-authority vs. attempt-correctness separated; individual standing claim narrowed
   to a three-way split; the World Rule conclusion explicitly bounded to investigated cases; the
   capability areas restated as a map, not a pipeline) — detailed in the foundational synthesis
   document itself, referenced here rather than repeated.
5. **Adds a genuinely new capability area** (§3.5, Observation and player delivery) that the prior
   five-phase draft didn't separate out as its own area at all — the epistemic principle now has an
   explicit home in the capability map, not folded into "recognition."
6. **States an initial product proof that requires no *new capability area*** (lineage, §5) — the
   prior draft's only proposed proof (the hunter/shopkeeper scenario) required the least-evidenced
   capability area (§3.4's propagation gap) to land first; this document front-loads lineage instead,
   since its capability area (§3.2) needs no new area of work to exist. **Superseded, 2026-09-27**:
   this was never a claim that lineage needs *no engineering work at all* — §7.1's confirmed
   dual-writer defect shows real engineering work is still required within that existing capability
   area. "No new capability area" and "cheap to deliver" are not the same claim; current status is
   in §7/§8, not here.

### Round 2 response, 2026-09-27

1. **Two small roadmap corrections applied**: §3.1's semantic obligation restated as already-
   supported (not open), with what's open narrowed to cross-domain verification/enforcement
   discipline; the Owner Decision List's feasibility-gate item downgraded from an owner decision to
   a recommended default for local investigation.
2. **Decision bridge added** (§6) — a compact, three-level table per capability area, citing SCP
   mapping status precisely (`UNKNOWN` where the SCP hasn't touched a family, never inferred as
   `MISSING`), with no full-Catalog sweep run.
3. **Feasibility gate actually run** (§7) — real tests re-executed 2026-09-27, not cited
   secondhand; economy/wealth checked as the comparison candidate and found genuinely `BLOCKED` on
   its own missing mechanism, not assumed weaker without evidence.
4. **First wave recommended** (§8, since revised further — see Round 4/5) — one primary option
   pairing bounded foundation-hardening with the lineage single-transition proof in parallel, plus a
   non-recommended alternative, each with finite exit evidence and named `UNKNOWN` costs.
5. **The Semantic Control Plane roadmap's own opening status was stale** (claimed "no milestone has
   started" while M0-M4 were all already complete per its own later sections) — corrected directly,
   since this round's work required citing its current state precisely.

**External-review concerns rejected on repository evidence: none.**

### Round 3 response, 2026-09-27

1. **Reclassified the two passing tests** — they are evidence for two specific death-to-heir
   transitions (§7), never a completed five-question gate and never a player-facing proof.
2. **§8's lineage half renamed** from "player-facing proof" to a **feasibility exercise** (since
   further refined in Round 4/5 — see §8), explicitly not a proof until a situated observer, given
   only the exercise's legitimate traces, can form a reasonable hypothesis (§5's player-side
   inference check) — and explicitly distinguished from the longer, durable changed-life-trajectory
   proof (§5's closed-loop distinction), which this exercise does not attempt.
3. **§3.5 reconciled with §4's path split** — the recognition candidate (Path 1) genuinely needs
   §3.4's propagation gap closed; the lineage candidate (Path 2) does not.
4. **Economy comparison reframed** (§7, Q5) — treated as evidence of economy's own missing
   conversion edge, not as evidence lineage has the clearest player experience.
5. **§3.6 corrected** — existing SimQ/corpus-tier/M3 infrastructure does not establish §5's
   player-side inference check; that evaluation is unbuilt, not merely unrun.
6. **§5, §7, §8, and the Owner Decision List synchronized**; a stray extra table cell and a stale
   section reference were fixed.
7. **A short passed/partial/unknown/blocked evidence table added** (§7).
8. **§8 reframed as a recommendation pending §7's outstanding checks**, not a selected delivery wave.

**External-review concerns rejected on repository evidence: none.**

### Round 4 (finalize instruction) response, 2026-09-27

1. **Bounded cross-domain authority audit actually run** (§3.1) — 5 named boundaries, classified
   (2 `DEFECT_CONFIRMED`, 3 `UNKNOWN_WITH_REASON`, 1 `CONFIRMED_FINE_WITHIN_SCOPE`), with a named
   deliberately-not-checked list.
2. **Lineage composition probe actually executed, not just reasoned about** (§7.1) — surfaced a
   genuinely new, load-bearing finding: composing a second lineage hop through ordinary per-tick
   aging is `BLOCKED` by a real, reproducible dual-writer race on `entity.lifecycle.active`. This is
   documented and escalated per the instruction's own boundary — **no production code was changed**
   to fix it; it is flagged for a future ticket, not fixed under this planning-only pass. **Note,
   Round 5**: this entry originally described the region-ownership and lifecycle-active defects as
   "the same defect class" — corrected in §3.1/§7.1 to state the shared invariant precisely while
   naming the two distinct mechanisms; see those sections, not this historical entry, for the
   accurate framing.
3. **Observer/evidence-packet design check actually built** (§7.2) — a minimal provisional observer
   position, one early clue, one reasonable-but-unprovable hypothesis, and two named negative checks.
4. **Gate question 4 split into three separate sub-answers** — mechanism exists / evidence-
   production exists / projection-is-buildable are no longer conflated into one "partial" (§7.3).
5. **Bounded second-candidate search completed** (§7.4) — environmental/calamity checked and
   disqualified (`contradicted` by real corpus runs, worse than economy's `BLOCKED`); displaced-
   family/feud found not independent of lineage; institutional/office reconfirmed `MISSING`.
6. **Registry/SCP tooling query recipes documented with real command output** (§9), plus one
   concrete, minimal incremental-improvement recommendation.
7. **§8's recommended first wave re-scoped to the single hop** (since further split in Round 5 —
   see §8's current world-side/player-side separation).
8. **A separate `PROPOSED / FOR REVIEW` first-wave milestone plan drafted** at
   `docs/plans/systemic_world/first_wave_plan.md`.

**External-review concerns rejected on repository evidence: none.**

### Round 5 response, 2026-09-27

Responding to the fifth external review round's architectural-consistency pass:

1. **World correctness separated from product legibility** — §8 and the first-wave plan's M4 no
   longer pause the lineage defect fix or composed-sequence verification on M2's player-side
   outcome; world-side and player-side tracks now have separate gates and separate exit claims
   throughout (§8, first-wave plan §3/§4).
2. **State/evidence/encounter/inference separated in M2** (first-wave plan) — the real inventory-
   transfer state change, whether the specified observer can *encounter* it (scriptable: viewpoint
   access, timing, non-leakage), the separately-confirmed-missing provenance signal, and the human-
   only inference step are now four distinct sub-checks, not one. A scripted test cannot substitute
   for a blinded human observer on the inference step; `PLAYER-EXPERIENCED` stays `pending` if that
   step is not run.
3. **§8 synchronized with the audit and defect already found** — no longer phrased as "run the
   audit"; reflects the 5 real boundary results and the confirmed defect directly.
4. **"One incident," "zero new capability-area work," and "cheapest real proof" claims corrected or
   removed from current recommendations** — §8's alternative-option reasoning no longer says "one
   specific incident" (two confirmed invariant violations now exist, via distinct mechanisms, per
   §3.1/§7.1's corrected framing); the Change summary's item 6 above is marked superseded rather than
   left to read as current.
5. **Region-ownership and lifecycle-active defects clarified as distinct mechanisms under one shared
   invariant**, not assumed identical (§3.1, §7.1).
6. **Historical review-response logs moved to this appendix**, keeping §0-§10 as the current
   capability map and decision evidence.
7. **First-wave plan's M3 made explicitly separately-schedulable per boundary, with
   `BLOCKED_WITH_REASON`** added as a legitimate third outcome alongside `CONFIRMED_FINE_WITHIN_SCOPE`
   and `DEFECT_CONFIRMED`, so a boundary that genuinely cannot be scenario-tested is never forced
   into a false fine/defect verdict.

**External-review concerns rejected on repository evidence: none.** Every requested correction was
directly actionable; no counter-evidence was found against any of the five architectural points.
