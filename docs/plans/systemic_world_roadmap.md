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
| `INTEGRATED` | **Confirmed fragile even where individually verified** — the regional-sovereignty dual-authority bug (two systems independently writing the same field, at different thresholds) was found in an already-shipped, already-tested domain, during unrelated work this same investigation arc. This is the concrete cautionary example for this whole capability area: verification of one domain in isolation does not prove integration across domains. |
| `PLAYER-EXPERIENCED` | Not directly surfaced as its own player-visible layer — but experienced indirectly, whenever a player encounters a coherent consequence that depends on this substrate holding (e.g. a region's ownership actually changing consistently). Not yet evaluated for that indirect effect specifically. |

**Cross-domain proof, revised to a bounded target (external review correction, 2026-09-26)**: an
open-ended "does this pattern recur anywhere" pass cannot be proven complete by a finite audit.
Bounded instead: identify the most consequential cross-domain mutation paths (durable ownership/
control fields written from more than one system, the shape the regional-sovereignty bug actually
had), review ownership/authority at those specific boundaries, and exercise representative
integration scenarios for each. Report the scope actually covered and name what remains `UNKNOWN`
outside that scope — never claim the absence of a defect outside the boundary actually checked.

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
| Life/Body/Ecology (Batch 05) | Full, for cases the batch investigated | Uneven — no HP recovery mechanism at all; aggregate population disconnected from individual births/deaths (Batch 05's own finding, not re-verified this arc) |
| Space/Environment (Batch 04) | Full, for cases the batch investigated | Two confirmed repository gaps (no route/portal mechanism; no non-physical movement) at Catalog-freeze time, not re-checked this arc |
| Material/Economy (Batch 08) | Full, for cases the batch investigated | **Confirmed gaps this arc**: wealth→leverage conversion `MISSING` on three independent paths (`ME-S12`); the heirloom/`"CHEST"` resolver bug, plus a sibling risk in the harvest `"NODE"` resolver path (Part A) |
| Social/Lineage (Batch 09) | Full, for cases the batch investigated | **Real, evidenced proof of the general shape working** (not a full cross-domain generalization by itself) — feud inheritance, dying wishes, displacement, heirloom transfer, and leadership succession are all `PROVEN CURRENT` at the mechanism level and compose into a real history-to-behavior loop; whether this *scales* to a presentable, temporally-continuous player-facing sequence is a separate, unchecked question (§5) |
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
| Lineage (leading candidate, gate partially run — §7) | Mechanism: yes, for the single death-to-heir transition (`PROVEN CURRENT`, re-confirmed 2026-09-27); composition into a longer sequence and product/player feasibility: `UNKNOWN` (gate Q1 partial, Q2/Q3 unknown, Q4 partial) | Resolve gate Q2/Q3 (feasibility exercise, §8) first; then projection work, scope depending on findings | Gate questions 1 (full composition) and 3 answered from a real seeded run at the longer timescale, *then* player-observation evidence per the calibrated criterion below |
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
| 3.2 Autonomous world dynamics (lineage slice) | `SOC-01` (Batch 09) — **not SCP-mapped** | `succession`/`aging_death` mechanisms, `registries/mechanisms.yaml`, `state: done`, `verified: {instrument: scenario, verdict: observed}` — the strongest evidence tier this repo uses. Two individual death-to-heir transitions re-run and confirmed passing 2026-09-27 (`tests/simulation_quality/test_heir_inventory_transfer_corpus.py`, `tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py`) — **evidence for those specific transitions, not a composed longer sequence** (external review correction, third round). | Whether individual, proven transitions compose into a *longer*, multi-generation observable sequence — no test found running this at that timescale. | Chronology-over-a-real-period, identity continuity across many ticks — `UNKNOWN`, not fabricated (§7). | High on single-transition mechanism evidence; composed-sequence and player-facing feasibility still `UNKNOWN`, gated by §7's feasibility exercise (§8). |
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

## 7. Feasibility gate results — lineage vs. economy/wealth (run 2026-09-27, reclassified per third external review round, 2026-09-27)

**Comparison candidate chosen**: economy/wealth (a genuinely different domain and causal path from
lineage, per the instruction's own requirement) — not treated as ready; its own conversion edges
are independently confirmed `MISSING` (`ME-S12`, Part B), which is itself informative for question 5.

**What the two re-run tests actually establish, precisely (external review correction, third
round)**: `test_heir_inventory_transfer_corpus.py` and
`test_lineage_dispatch_deterministic_kernel_tick.py` (re-run and passing, 2026-09-27) are real,
`verified: observed`-tier evidence for **two specific death-to-heir transitions** — nothing more.
They are **not** a completed five-question feasibility gate and **not** a player-facing proof. Every
claim below is scoped to that.

| Gate question | Lineage | Economy/wealth (comparison) |
|---|---|---|
| **1. Consequential sequence from real state/history, no invented events?** | **Partial.** The two single-tick transitions themselves are real, not fabricated: death→heir-inventory-transfer (`test_heir_inventory_transfer_corpus.py`) and death→feud-blocker-transfer+dying-wish together (`test_lineage_dispatch_deterministic_kernel_tick.py`), both through one real `Kernel.tick_once()`. **Not answered**: whether they *compose* into a longer sequence (the heir themselves later aging, dying, and transferring again) — no such run exists. Stays `partial`, not `passed`. | `BLOCKED` — no mechanism entry for `protection`/`patronage`/wealth-conversion exists in `registries/mechanisms.yaml` at all (checked directly, 2026-09-27); `PROTECTION` contracts are confirmed constructed only in `src/certification/scenarios.py`, zero production call sites (Part B). No sequence exists to seed a run against without inventing the mechanism first. |
| **2. Player-plausible traces / legitimate unknowns?** | `UNKNOWN` — not investigated; a product-projection question, not a code-running one. | `UNKNOWN`, moot until question 1's blocker clears. |
| **3. Identity/chronology/causal continuity over the relevant period?** | `UNKNOWN` — the two tests proven this round are single-tick proofs of a transition firing correctly, not a multi-tick chronology check. Foundational Rule content (identity-continuity-as-default, Batch 01) is suggestive, not a direct empirical check of this case at scale. | `UNKNOWN`, moot for the same reason as Q2. |
| **4. Projection/integration alone, or a missing simulation edge?** | **Partial, precisely scoped**: no missing simulation edge was identified **for the two tested transitions specifically** — both are real, `verified: observed`-tier mechanisms today. This does **not** establish that evidence-production and projection (surfacing the transition to an observer as a legible trace) are themselves feasible — that stays a separate, unchecked question from "does the mechanism exist." | **A missing simulation edge, confirmed** — no registered mechanism exists to project from at all. |
| **5. Comparison** | Limited, not conclusive. Economy's `BLOCKED` status is evidence *economy* has a gap, not evidence that *lineage* has the clearest player experience. No second comparison candidate with equivalent registered-mechanism, history-composing evidence was found this round — checked directly against `registries/mechanisms.yaml`'s other `state: done`/`verified: observed` entries (combat resolution, movement legality, interaction, entity-apply, skill-scaling, species/personality traits, entity-level XP/evolution) and all are single-tick or non-historical, not comparable trajectory candidates. Stated as a limitation, not resolved by asserting lineage wins. | Same limitation from the other side — its only inspected comparison is lineage. |

**Short status summary** (passed / partial / unknown / blocked, per question):

| Question | Lineage | Economy/wealth |
|---|---|---|
| 1 — real sequence, no invented events | partial | blocked |
| 2 — player-plausible traces | unknown | unknown |
| 3 — identity/chronology/continuity | unknown | unknown |
| 4 — projection-only vs. missing edge | partial | blocked |
| 5 — comparison | limited | limited |

**Gate verdict, stated precisely**: no question above is `passed`, for either candidate. Lineage
sits at `partial` on questions 1 and 4 (real evidence for the tested transition, not the composed
sequence and not the projection question), `unknown` on 2 and 3, `limited` on 5. Economy/wealth is
`blocked` on 1 and 4, `unknown` on 2 and 3 (moot), `limited` on 5. **This is a feasibility exercise
in progress, not a completed gate and not a player-facing proof** (adopted directly from the third
external review round; §8 renames its lineage half accordingly).

**This does not promote lineage to a proven product proof** — the two individually-verified
transitions are real evidence for exactly what they test, and no more. The specific remaining
unknowns (Q2, Q3, the longer-sequence half of Q1, and the projection-feasibility half of Q4) are
named rather than assumed away.

## 8. Recommended first wave — a recommendation pending §7's outstanding checks, not a selected delivery wave (revised 2026-09-27, third external review round)

**This is a recommendation for where to look next, not a committed delivery wave.** §7 leaves
questions 2 and 3, and part of 1 and 4, open for lineage; economy/wealth is `BLOCKED`. Both halves
below exist to make progress on those specific unknowns, not to declare either one delivered.

**Option A — recommended: pair one bounded causal/authority check with the lineage feasibility
exercise, in parallel.**

- **Causal/authority strengthening**: run §3.1's own bounded audit (not a full sweep) against the
  most consequential cross-domain mutation paths analogous to the regional-sovereignty case —
  durable ownership/control fields writable from more than one system. **Trajectory proof**: none
  needed for this half; it's foundation hardening. **Rule/registry evidence**: the regional-
  sovereignty pattern itself, already fully diagnosed. **Prerequisites**: none. **Parallel work**:
  fully independent of the lineage half. **Finite exit evidence**: the named boundaries reviewed,
  each with an explicit state (fixed, confirmed-fine, or a new `UNKNOWN` with a named reason) —
  never "swept the whole engine." **Costs/risks `UNKNOWN`**: how many such boundaries actually exist
  to check — not yet scoped.
- **Feasibility exercise (lineage), not yet a proof**: attempt to resolve gate questions 2 and 3
  specifically — a small, scoped design exercise (not full UI/renderer work) checking whether a
  single death→heir transition can be presented with identity and immediate causal continuity
  intact, using the already-`verified: observed` mechanisms as substrate. **This stays a
  feasibility exercise, not a player-facing proof, until a situated observer — given only the
  legitimate traces the exercise produces — can actually form a reasonable hypothesis** (§5's
  player-side inference check); the exercise existing as a design sketch is not itself that
  evidence. **Trajectory scope**: the single death→heir transition vignette only, explicitly not
  the longer multi-generation arc and explicitly not yet a durable changed-life-trajectory proof
  (§5's closed-loop distinction) — composing multiple transitions is a separate, larger question
  this exercise does not attempt to answer. **Rule/registry evidence**: `succession`/`aging_death`
  mechanism entries, both `verified: observed`, re-confirmed this round — evidence the underlying
  transition is real, not evidence the projection is legible. **Prerequisites**: none new.
  **Parallel work**: independent of the causal-authority half above. **Finite exit evidence**: gate
  questions 2 and 3 each answered from a real design check with an actual observer test (not just
  narrated), or reclassified `BLOCKED` with a named reason. **Costs/risks `UNKNOWN`**: whether the
  longer-arc question (does this compose across generations) turns out to need real new simulation
  work once the single-transition exercise is actually attempted; whether the observer test itself
  surfaces a legibility problem no one has looked for yet.

**Option B — an alternative, not recommended over A but evidence-consistent**: defer the feasibility
exercise entirely and run only the causal/authority audit first, on the reasoning that a foundation
defect (if one exists elsewhere) would undercut confidence in *any* later player-facing proof,
lineage included. **Tradeoff against A**: slower to any player-visible result, but avoids building
toward a proof on ground not yet checked for the regional-sovereignty class of defect. Not
recommended, because that defect class was found via one specific incident, not a systemic pattern
with evidence of recurrence — deferring all player-visible work on a single incident would overcorrect.

**Neither option is forced into one module or a fixed sequence** — both halves of Option A are
explicitly parallel-safe, and Option B differs from A only in sequencing, not in scope.

## 9. Response to the second external review round (2026-09-27)

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
4. **First wave recommended** (§8) — one primary option pairing bounded foundation-hardening with
   the lineage single-transition proof in parallel, plus a non-recommended alternative, each with
   finite exit evidence and named `UNKNOWN` costs.
5. **The Semantic Control Plane roadmap's own opening status was stale** (claimed "no milestone has
   started" while M0-M4 were all already complete per its own later sections) — corrected directly,
   since this round's work required citing its current state precisely.

**External-review concerns rejected on repository evidence: none.** Every requested action was
directly actionable and evidence-supported; the stale-status discrepancy the review flagged was
confirmed real, not a misreading on the reviewer's part.

## 10. Response to the third external review round (2026-09-27)

1. **Reclassified the two passing tests** — they are evidence for two specific death-to-heir
   transitions (§7), never a completed five-question gate and never a player-facing proof. Q1 stays
   `partial` (single-tick transitions real; longer-sequence composition unchecked); Q4 restated to
   say only that no missing simulation edge was found *for the tested transition* — evidence
   production and projection feasibility remain unchecked, not resolved by the mechanism existing.
2. **§8's lineage half renamed** from "player-facing proof" to a **feasibility exercise**, explicitly
   not a proof until a situated observer, given only the exercise's legitimate traces, can form a
   reasonable hypothesis (§5's player-side inference check) — and explicitly distinguished from the
   longer, durable changed-life-trajectory proof (§5's closed-loop distinction), which this exercise
   does not attempt.
3. **§3.5 reconciled with §4's path split** — the recognition candidate (Path 1) genuinely needs
   §3.4's propagation gap closed; the lineage candidate (Path 2) does not, so §3.5's own nearest
   tractable job is projecting from lineage's already-proven mechanisms, not waiting on recognition
   work. Stated directly rather than left implicit.
4. **Economy comparison reframed** (§7, Q5) — treated as evidence of economy's own missing
   conversion edge, not as evidence lineage has the clearest player experience. Checked directly
   against `registries/mechanisms.yaml`'s other `state: done`/`verified: observed` entries for a
   second viable comparison candidate; found none with equivalent registered, history-composing
   evidence this round (combat resolution, movement legality, interaction, entity-apply,
   skill-scaling, species/personality traits, and entity-level XP/evolution entries are all
   single-tick or non-historical) — comparison stated as limited, not resolved by assertion.
5. **§3.6 corrected** — existing SimQ/corpus-tier/M3 infrastructure does not establish §5's
   player-side inference check; that evaluation is unbuilt, not merely unrun.
6. **§5, §7, §8, and the Owner Decision List synchronized** — §5's pre-run narration now points to
   §7 as authoritative instead of restating superseded claims; §6's lineage row's stray extra cell
   removed and its claims softened to match; the Owner Decision List's stale "§6 below" reference to
   the gate corrected to "§7".
7. **A short passed/partial/unknown/blocked evidence table added** (§7) covering both candidates
   across all five gate questions.
8. **§8 reframed as a recommendation pending §7's outstanding checks**, not a selected delivery wave.

**External-review concerns rejected on repository evidence: none.** Every requested correction was
directly actionable; the extra table cell and the stale section reference the review implicitly
flagged were both confirmed real slips in this document, not disagreements with the review's own
reading.

---

## Change summary — what changed from the prior five-phase draft, and why

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
6. **States an initial product proof that requires zero new capability-area work** (lineage,
   §5) — the prior draft's only proposed proof (the hunter/shopkeeper scenario) required the least-
   evidenced capability area (§3.4's propagation gap) to land first; this document front-loads the
   cheapest real proof instead.

---

## External review response, 2026-09-26

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

**External-review concerns rejected on repository evidence: none.** Every requested correction is
directly supported by evidence already gathered this arc (Part A/B's own citations, the frozen
Catalog's own Rule text) — no counter-evidence was found against any of the five points.

---

## Owner Decision List (refined per external review, 2026-09-26)

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
