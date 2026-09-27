---
status: proposed
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
Supporting evidence lives in `tmp/rpg-core-investigation-*.md` and
`tmp/rpg-core-foundational-synthesis-and-roadmap-revision.md` — this document stays high-level and
cites them by pointer rather than repeating code-level traces.

**What this is not**: an implementation plan, a ticket list, or a claim that any part of it is
approved. Engineering decisions (record types, class reuse, symbol retirement) are explicitly left
to local engineering investigation once a semantic boundary is set — see the Owner Decision List at
the end for the short list of things this document cannot decide for itself.

---

## 0. Relationship to existing plans

| Document | Authoritative for | Relationship to this document |
|---|---|---|
| `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` (M1-M9) | The 65-idea brainstorm-to-implementation program that already shipped | **Closed, unrelated scope.** M1-M9 are all `DONE`; M10 is a narrow 2-idea backlog. This document does not extend that numbering — a new capability program forced into a finished, dated milestone series would misrepresent both. |
| `docs/world_rules/roadmap.md` (World Rule Catalog) | Target world semantics, frozen | **Upstream authority.** Every capability area below cites which frozen Rules already define its target semantics. This document never redefines a Rule; it sequences *realizing* what the Catalog already states. |
| `docs/plans/simulation_semantic_control_plane/roadmap.md` (M0-M4) | Rule↔Mechanism *mapping*, not new capability implementation | **Independent, parallel track.** M3's ongoing triage stream stays exactly what it is — this document's findings feed it, but this document does not manage or gate on M0-M4's own sequencing. |
| `docs/plans/long_term_development_roadmap.md` | Engine-infrastructure phases (CI, determinism, corpus tooling) | **Independent axis.** A different kind of health entirely — this document assumes that infrastructure exists and builds capability on top of it, not instead of it. |
| `docs/plans/render_and_art_program_roadmap.md`, `hud_delivery_roadmap.md`, `live_map_scaling_roadmap.md` | Presentation-layer programs | **Explicitly unrelated axis**, per this investigation's own repeated instruction not to confuse the two. Section 5's "Observation and player delivery" area is deliberately about *what* a gameplay lens may expose, never *how* it renders — those documents own the how. |

**This document's own proposed home**: itself, at `docs/plans/systemic_world_roadmap.md` — a new,
standalone location, not appended to any of the above. Marked `PROPOSED / FOR REVIEW` throughout;
promotion to `active` status is the owner's call, not decided here.

**Companion document, added 2026-09-27 (fourth review round)**:
`docs/plans/systemic_world_first_wave_plan.md` holds the concrete milestone plan (entry/exit
evidence, domain ownership, a decision gate) for the first wave this roadmap's §7/§8 recommend —
kept separate so this document stays a capability/dependency map rather than a milestone transcript,
per the finalize instruction's own request.

---

## 1. Product north star

*(Full statement in `tmp/rpg-core-foundational-synthesis-and-roadmap-revision.md`'s own "Product
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
| 5 | Public reputation: `SocialComponent.reputation` (`reputation_set`) from `social_memory.py` and `orchestrator.py` | `UNKNOWN_WITH_REASON` — two real writer call sites for the same durable field; phase ordering and same-tick-same-entity collision not checked this round. Separate from the roadmap's already-flagged *semantic* question of what `public_reputation` means (Owner Decision List item 3) — this is a mechanical dual-writer check only. |

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

**Exit condition, stated exactly**: this is a named set of 5 (+1 unplanned) boundaries with explicit
outcomes — 2 `DEFECT_CONFIRMED`, 3 `UNKNOWN_WITH_REASON`, 1 `CONFIRMED_FINE_WITHIN_SCOPE`. It does
**not** claim the regional-sovereignty defect class is absent elsewhere in the engine. **Deliberately
not checked this round** (named, not silently skipped): market/economy authoritative price or
inventory fields; combat durability/HP fields across the three known dispatch paths (Part A already
flagged dispatch plurality from a different angle); `cooldown_set`, `group_id_set`/`GroupRecord`,
and strategic-cognition bundle fields; `src/economy/vacancy.py`'s vacancy/settlement fields;
institutional standing (does not yet exist as a mechanism, so moot). No production code was changed
by this audit — boundary 1's downstream-consequence gap and the new lifecycle-active race are
flagged for escalation, not fixed here.

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
| Life/Body/Ecology (Batch 05) | Full, for cases the batch investigated | Uneven — no HP recovery mechanism at all; aggregate population disconnected from individual births/deaths (Batch 05's own finding, not re-verified this arc). **Confirmed this round (fourth review round, checked as a candidate trajectory, §7)**: `regional_trauma`/`calamity_intensity` (environmental-threat/calamity mechanisms) are `state: done` but real corpus runs `contradicted` them outright — built and wired, but the `trauma_score`/`calamity_intensity` values never actually move in real play (already-open tickets `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`, `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`). This is a stronger finding than "uneven" — a mechanism that was tested and found not to fire, not merely untested. |
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
filter-time. See Owner Decision List.

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

**Cross-domain proof**: not yet definable in general, but not uniformly blocked either — reconciled
with §4's own path split (external review correction, third round, 2026-09-27): the
*recognition-specific* candidate (Path 1) genuinely needs §3.4's propagation gap closed before any
projection is possible. The *lineage* candidate (Path 2) does **not** — its underlying mechanisms
(`aging_death`, `succession`) are already `verified: observed` today, so this area's nearest
tractable first job is attempting a projection of the already-proven lineage transition (§7's
feasibility exercise, §8), not waiting on §3.4's recognition work. This line states only that
lineage does not share recognition's dependency — it does not claim the projection question itself
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

## 4. Dependency paths (a sample, not an exhaustive graph)

At least one path deliberately requires no social recognition at all, per the instruction's own
explicit requirement:

```text
Path 1 (recognition-dependent — the hunter/shopkeeper thread this investigation traced deepest):
  World substrate (3.1) → Situated agency (3.3) → History/feedback, recognition half (3.4)
  → Observation/delivery (3.5)

Path 2 (NOT recognition-dependent — already working today, zero new capability work):
  World substrate (3.1) → Autonomous world dynamics, lineage (3.2) → History/feedback,
  already-proven loop (3.4) → Observation/delivery (3.5)

Path 3 (NOT recognition-dependent — a second, different domain owner):
  World substrate (3.1) → Autonomous world dynamics, economy (3.2) → History/feedback,
  independent wealth/office edges (3.4) → Observation/delivery (3.5)
```

**Reusable foundation work** (§3.1's own recurrence check) benefits all three paths equally.
**Independent domain work** (§3.2's economy/institutions realization gaps) can proceed in parallel,
owned by their own domains, without waiting on §3.4's recognition-specific work. **Integration
proofs** are §3.4's own cross-domain scenarios, once built. **Later breadth work** is §3.6's ongoing
job across whichever domains next prove worth deepening — not scheduled here.

**Nothing in this roadmap gates all future development on completing every Rule mapping or every
domain** — Path 2 and Path 3 are proof that meaningful product value doesn't require §3.4's
recognition work to land first.

---

## 5. Delivery path

**First-proof selection: `OPEN`, with lineage the leading candidate — corrected per external
review, 2026-09-26.** The earlier draft called lineage the committed first proof because its
underlying *mechanisms* are `PROVEN CURRENT`. That's true, but it doesn't prove a player-facing
*projection* of them is feasible — event selection, temporal continuity, viewpoint/scope,
provenance, and pacing are product-design and integration questions this investigation never
checked, even though no new simulation mechanism looks necessary. "Few new simulation mechanisms
needed" is not the same claim as "cheap to deliver."

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

**Current state of this gate for lineage — superseded by the real run in §7 (2026-09-27); read that
section for the authoritative per-question result.** Kept here only as a pointer so this section
doesn't drift out of sync with §7 again (external review correction, third round): two individual
death-to-heir transitions were re-run and confirmed passing, which is evidence for those specific
transitions, **not** a completed five-question gate and **not** a player-facing proof. Composition
into a longer, multi-generation sequence (the fuller form of question 1, and question 3) remains
`UNKNOWN`. Question 5's comparison (economy/wealth) came back `BLOCKED` on its own missing
conversion mechanism — evidence that economy has a gap, not evidence that lineage is the clearest
player experience; no second comparison candidate with equivalent registered-mechanism evidence was
found this round (§7), so the comparison stays limited rather than conclusive.

**Recommendation**: lineage remains the leading candidate to run this gate against, but **selection
stays `OPEN`** — §7's real run answered two of five questions partially, not all five, so this is
still not a committed first-shipped proof.

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

**Contrasting-domain proof, required per the instruction**: the lineage proof above already *is*
one — a non-recognition, non-combat domain, evidenced today. A second contrasting proof, once
§3.2's economy gaps close: a craftsperson's wealth converting into a concrete leverage outcome
(protection, patronage), independent of any recognition work.

**Evidence table**:

| Proof | Currently evidenced | Requires engineering | Evidence needed to claim delivery |
|---|---|---|---|
| Lineage (leading candidate, gate partially run — §7) | Mechanism: yes, for the single death-to-heir transition (`PROVEN CURRENT`, re-confirmed 2026-09-27); composition into a longer sequence: `BLOCKED` on a confirmed dual-writer race, not `UNKNOWN` (§7.1); product/player feasibility for the single hop: `partial`, design-check evidence exists (§7.2) | Turn the §7.2 design sketch into a real observer test (feasibility exercise, §8) for the single hop now; the multi-hop half needs §7.1's defect fixed first — a separate, tracked prerequisite, not open-ended projection work | The §7.1 defect fixed, *then* gate questions 1 (full composition) and 3 answered from a real seeded run at the longer timescale, *then* player-observation evidence per the calibrated criterion below |
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
| 3.1 World substrate | Milestone A (`ID-*`/`TIME-*`/`AUTH-*`/etc.) — **not SCP-mapped**, Catalog-level only | `TCK-20260401-ACTION-CONVERGENCE`'s replay-determinism law, verified. Regional-sovereignty dual-writer bug confirmed live (verified current, this session, 2026-09-23/24). | Cross-domain integration unverified outside the one checked case. | Whether the dual-writer pattern recurs elsewhere — `UNKNOWN`, bounded audit not yet run (§3.1). | Indirect only — a player never sees this layer directly. |
| 3.2 Autonomous world dynamics (lineage slice) | `SOC-01` (Batch 09) — **not SCP-mapped** | `succession`/`aging_death` mechanisms, `registries/mechanisms.yaml`, `state: done`, `verified: {instrument: scenario, verdict: observed}` — the strongest evidence tier this repo uses. Two individual death-to-heir transitions re-run and confirmed passing 2026-09-27 (`tests/simulation_quality/test_heir_inventory_transfer_corpus.py`, `tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py`) — **evidence for those specific (artificially-staged) transitions, not a composed longer sequence**. | Whether individual, proven transitions compose into a *longer*, multi-generation observable sequence — **now `BLOCKED`, not merely untested (fourth round, §7.1)**: a real, reproducible dual-writer race on `entity.lifecycle.active` (`ApplyPath` vs. `LifecycleSystem.resolve_lifecycle`) prevents succession from firing at all for a death that arrives through ordinary per-tick aging rather than pre-staging. | Chronology-over-a-real-period, identity continuity across many ticks — `BLOCKED`, not fabricated, moot until §7.1's defect clears. | High on single-transition mechanism evidence; single-hop player-facing feasibility `partial` (a design-check observer sketch exists, §7.2); composed-sequence feasibility gated on a confirmed defect fix, not open design work (§7.1, §8). |
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

## 7. Feasibility gate results — lineage vs. economy/wealth and other candidates (run 2026-09-27; composition probe and observer sketch actually executed, fourth review round, 2026-09-27)

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
heir, co-located at the death site. **Early clue**: the heir is visibly carrying an item never seen
on them before, shortly after a nearby death — a legitimate in-world trace (inventory/equipment
state), not a developer log. **Reasonable hypothesis available from that clue alone**: "this person
is the deceased's heir" — true in this run, but the clue alone can't prove it (the fallback heir
selector picks the highest-bond candidate, not necessarily a *socially designated* heir; mere item
possession can't distinguish heir from opportunistic looter). **Later clue that could revise the
hypothesis**: the heir observed acting on the inherited grudge or dying wish would strengthen the
hypothesis toward confirmed — but **nothing in the current code path produces that observable
action** (see negative check below), so this confirming clue cannot occur today without further work.

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

### 7.3 Gate question table

| Gate question | Lineage | Economy/wealth (comparison) |
|---|---|---|
| **1. Consequential sequence from real state/history, no invented events?** | **Partial, with a confirmed blocker on composition.** The single hop is real, not fabricated (§7.1). Composing a *second*, ordinary-aging hop is not merely unchecked — it is **`BLOCKED` by a confirmed defect** (§7.1's dual-writer race). This is stronger information than "unknown": the blocker is named and reproducible, not just untried. | `BLOCKED` — no mechanism entry for `protection`/`patronage`/wealth-conversion exists in `registries/mechanisms.yaml` at all; `PROTECTION` contracts are confirmed constructed only in `src/certification/scenarios.py`, zero production call sites (Part B). |
| **2. Player-plausible traces / legitimate unknowns?** | **Partial** — a concrete observer position and evidence packet were sketched and checked this round (§7.2): one legitimate early clue exists, one reasonable-but-unprovable hypothesis, and two named negative-check failures (no trace for the inherited grudge/dying wish; two named leak-risk fields). This is real design-check evidence, not a code run, and not yet a real player-observation exercise. | `UNKNOWN`, moot until question 1's blocker clears. |
| **3. Identity/chronology/causal continuity over the relevant period?** | **`BLOCKED`, not merely unknown** — the same composition defect that blocks Q1's second hop blocks any multi-tick chronology check by construction; there is no longer sequence to check continuity over until §7.1's defect is addressed. | `UNKNOWN`, moot for the same reason as Q2. |
| **4. Projection/integration alone, or a missing simulation edge? (three separate sub-answers, per the finalize instruction)** | **(a) Does the tested transition need another simulation edge?** No — the single hop is real and correct as tested. **(b) Does its evidence production exist?** No — confirmed absent by direct inspection (§7.2's negative check 1); no provenance/evidence producer exists for an inheritance event at all. **(c) Could a situated projection be built from it?** Only for the single, already-proven hop, and only once an evidence producer exists — a projection across a *second* hop is blocked by §7.1's confirmed defect, not by unstarted projection-design work. This three-way split is itself new information the probe surfaced; the roadmap's prior single "partial" answer conflated these. | **A missing simulation edge, confirmed** — no registered mechanism exists to project from at all. |
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

No question is fully `passed`, for any candidate. Lineage is `partial` on Q1 (real single hop;
composition `BLOCKED`), `partial` on Q2 (a real design-check sketch exists, not yet a player test),
`BLOCKED` on Q3 (moot until Q1's defect clears), and split three ways on Q4 (mechanism: yes;
evidence-production: no; projection: blocked-by-Q1, not by unstarted design work). Economy/wealth is
`BLOCKED` on Q1/Q4, `UNKNOWN`/moot on Q2/Q3. Q5 stays limited for both — no qualifying second
candidate was found. **This is a feasibility exercise with one genuinely new, load-bearing finding
this round (§7.1's confirmed composition defect), not a completed gate and not a player-facing
proof.**

**This does not promote lineage to a proven product proof, and it does not disqualify lineage
either** — the single hop remains the strongest mechanism-level evidence of any candidate checked
across two rounds now. What changed this round is that "whether composition needs more simulation
work" moved from `UNKNOWN` to **confirmed yes, with a named root cause** — genuinely new information,
not an assumption resolved either optimistically or pessimistically.

## 8. Recommended first wave — synchronized with the audit already run and the confirmed lifecycle-active defect (revised 2026-09-27, fifth review round)

**This is a recommendation, not a committed delivery wave.** The bounded causal/authority audit
(§3.1) and the lineage composition probe (§7.1/§7.2) have both **already been run this arc** — this
section reflects their actual results, not a plan to go run them. Full milestone detail (entry/exit
evidence, owners, a decision gate) lives in the separate first-wave plan
(`docs/plans/systemic_world_first_wave_plan.md`); this section stays a short recommendation.

**Recommended: three independently-schedulable tracks, not one sequenced pair.**

- **World-side correctness (M1 in the first-wave plan)**: fix, or explicitly re-scope, the
  confirmed `entity.lifecycle.active` dual-writer race (§7.1) so natural-aging succession fires
  correctly, then verify a real composed two-hop sequence. **This track does not depend on, and is
  not paused by, any player-side/observer finding** — world correctness and product legibility are
  separate concerns with separate exit evidence (external review correction, fifth round): even if
  the observer exercise below finds the available clue too weak, fixing the defect and verifying
  composition remains worthwhile world-side work in its own right. **Rule/registry evidence**:
  `succession`/`aging_death`, both `verified: observed` for the single hop; the defect itself,
  already fully diagnosed with a root cause (§7.1). **Finite exit evidence**: a real two-hop run
  through ordinary per-tick aging, identity/chronology preserved across both hops.
- **Single-hop observer/evidence check (M2 in the first-wave plan)**: turn §7.2's design sketch into
  a real check of state → evidence → encounter → inference, in that explicit order — the inventory
  transfer is already a real state change; what's unverified is whether the specified observer can
  *encounter* it (viewpoint access, timing, non-leakage — scriptable), separately from whether an
  inheritance-*provenance* signal exists (confirmed absent, §7.2), separately again from whether a
  human observer can draw a reasonable *inference* from it (requires a real blinded-human exercise —
  a scripted test validates provenance/timing/access/non-leakage but cannot substitute for this last
  step). **If no human exercise is run, `PLAYER-EXPERIENCED` stays `pending`**, not resolved either
  way. **Finite exit evidence**: each of the four sub-checks answered from a real check, with
  inference specifically left `pending` if unrun.
- **Remaining causal/authority boundaries (M3 in the first-wave plan)**: the audit already produced
  3 `UNKNOWN_WITH_REASON` boundaries (entity-death `alive_set`, faction-diplomacy
  `diplomatic_relations_set`, public reputation) — each is **separately schedulable**, not one
  atomic milestone, and each may resolve to `CONFIRMED_FINE_WITHIN_SCOPE`, `DEFECT_CONFIRMED`, *or*
  `BLOCKED_WITH_REASON` if a representative scenario genuinely cannot be executed — never a forced
  fine/defect verdict where the real answer is "couldn't test it."

**All three tracks are parallel-safe** — none blocks another. The world-side composition check does
not wait on the observer check; the remaining boundary audits do not wait on either.

**Not recommended, evidence-consistent alternative**: defer the observer check and the remaining
boundary audits entirely, fixing only the lifecycle-active defect first. Not recommended because
nothing here actually requires that sequencing — all three tracks are independent, so deferring two
of them would only slow total progress without reducing any real risk. (Two confirmed violations of
the authority invariant now exist in this investigation arc — §3.1's INTEGRATED row — which is
evidence the invariant needs a real enforcement discipline, not yet evidence of one recurring bug
pattern; either way, nothing about that count changes whether these three tracks can run in
parallel.)

## 9. Evidence workflow — existing registry/Semantic Control Plane tooling (added 2026-09-27, fourth round)

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

**Recommended smallest incremental improvement**: one pure function in
`tools/semantic_control_plane/registry.py`, mirroring the existing `consumers_of`/`producers_for`
shape exactly —

```python
def rules_for(mechanism_id: str, edges: list[dict]) -> list[str]:
    """Every rule_id that cites this mechanism_id -- reverse of the forward Rule->edges lookup."""
    return [e["rule_id"] for e in edges if e.get("mechanism_id") == mechanism_id]
```

A ~10-line reverse-index reusing an already-proven pattern, closing Q2's one concrete gap without
touching schema, validation, or the two-domain view generator. Everything else asked in §1 already
has a real, working answer today. A broader general-purpose multi-Rule query CLI is a larger design
decision than "smallest increment" and is left out of scope here, for whoever next scopes that work.

## 10. Owner Decision List (refined per external review, 2026-09-26)

Only genuinely unresolved world-semantic or product-scope questions. Two items from the prior
version were downgraded here on external review: item 1 was mostly an implementation/modeling
question restated as if it were semantic; item 4 (roadmap promotion) is a governance step after
review, not a fourth conceptual decision competing with the real ones.

1. **Are individual subjective relations and institutional judgments distinct world concepts, with
   different authority, evidence, and update rules — or one concept at two scales?** This is the
   real semantic question underneath the prior "one record shape or two" framing, which wrongly
   pitched it as an implementation choice. **Recommended semantic default, from the frozen Rules
   themselves**: yes, distinct — `SOC-01` already separates structural relation from subjective
   attitude at individual scale, and `INST-03` already treats institutional authority/capability/
   power/legitimacy as its own, correlated-but-not-substitutable cluster; nothing in either Rule
   suggests collapsing the two scales into one concept. The exact record types implementing that
   semantic default stay with local engineering investigation.
2. **Institutional standing's domain ownership — not an owner-level decision unless a real conflict
   surfaces.** `IP-S17` and Batch 10's own Rule content already support the institutions domain as
   the semantic home; propose that as the default directly rather than presenting it as open. Escalate
   to the owner only if a genuine, unresolved cross-domain authority conflict with the social/
   relationship domain is found — none has been, this arc.
3. **`public_reputation`'s intended world meaning — state this as the open semantic question itself,
   not a retain-or-retire choice.** Is it meant to be a genuinely publicly-knowable fact, a narrow
   declared-scope claim, a derived projection, or a technical fallback? A global scalar that
   `appraisal.py` currently uses only as a last resort for total strangers is not automatically
   evidence that it's *meant* to be public knowledge — that's exactly the kind of silent-leak risk
   §2's epistemic principle warns about. Do not decide retain-vs-retire until this meaning, and its
   information provenance/scope, is established.
4. **Which candidate trajectory the feasibility gate runs against first is a recommended default for
   local investigation, not an owner decision — corrected per external review, 2026-09-27.** Lineage
   leads on mechanism-level evidence (§7 runs the gate directly); proceeding with it is a default,
   escalated to the owner only if the gate itself surfaces a genuine tradeoff evidence can't settle.
   Final proof selection stays `OPEN` until the gate produces real evidence, which §7 now provides
   in part — two of five questions, not all five (third external review round correction).

**Confirmed explicitly not owner-level, per the instruction's own boundary**: which existing class
to extend for any new record type, whether to retire or adopt the dead `ActionProposal` model,
exact field layouts. These belong to whoever scopes the first real ticket under an accepted
capability area.

---

## Appendix: External review response log (historical)

Moved out of the decision-bearing body per the fifth external review round's own request, so the
capability map (§0-§7) and current decision evidence (§8-§10) stay easy to read. These are **dated
records of what changed and why at the time**, not current status — current status always lives in
the numbered sections above; where a historical entry below has been superseded, it is marked so
inline rather than silently left to look current.

### Round 1 response, 2026-09-26

Responding to `tmp/external-ai-review-systemic-world-roadmap-instruction.md`, mapped to its five
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

The prior document (`tmp/rpg-core-foundational-synthesis-and-roadmap-revision.md`'s original
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
   `docs/plans/systemic_world_first_wave_plan.md`.

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
