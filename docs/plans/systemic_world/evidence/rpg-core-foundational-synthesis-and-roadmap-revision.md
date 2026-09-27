---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated evidence snapshot supporting `docs/plans/systemic_world/roadmap.md`, copied from the local working file `rpg-core-foundational-synthesis-and-roadmap-revision.md` on 2026-09-27. Where the roadmap has since corrected a claim, the roadmap is authoritative.

# Foundational Entity–World Architecture: Synthesis and Roadmap Revision

**Role note:** produced by the local repository-aware investigator, per the external reviewer's
own instruction. Detailed code traces live in Parts A/B (`tmp/rpg-core-investigation-part-a-
action-affordance.md`, `tmp/rpg-core-investigation-part-b-recognition-standing-test.md`) — this
document reasons at the semantic/architectural level and cites them by pointer, per the
instruction's own "do not spend the main report on line-by-line code paths" constraint.
**Status of everything below:** `PROPOSED` unless marked otherwise. Part C is treated as a
draft, not an approved roadmap, per the instruction's own framing. Nothing in this pass edits the
frozen Catalog, existing canonical roadmaps, registries, or production code.

---

## Deliverable 4 first — the calibration, since it governs everything else

Working through the instruction's own eight candidate overreach claims before rebuilding the
roadmap on top of them — building the revision on uncorrected premises would just repeat the
mistake at a higher level.

| # | Candidate claim | Corrected status | Why |
|---|---|---|---|
| 1 | The first general break is always a standing record | **SUPERSEDED (as a single verdict), split into two true statements** | For **individuals**: `PROVEN CURRENT` that a directed standing record already exists (`SocialComponent`'s `bonds`/`trust_history`) — the real first break is **propagation** (edge 3, Part B), not standing. For **institutions**: standing itself remains the confirmed first break — no primitive exists there at any level (`IP-S17`). One verdict was wrong; two narrower ones hold. |
| 2 | The existing generic rumor function is sufficient for direct witnessing *and* secondhand information | **OPEN/UNKNOWN — and Part C already conflated the two cases it shouldn't have.** `process_rumor()`'s generic shape only helps the **secondhand/non-participant** case. **Direct witnessing while physically present but not personally transacting** is a third case neither Part B nor Part C's Slice 1 actually separated from "direct interaction" (already solved by `bonds`/`trust_history`) or "secondhand hearsay" (the rumor path). Whether a directly-witnessed-but-not-participated event should carry the same confidence/decay semantics as a rumor, or needs its own tier, is unresolved. Part C's Slice 1 scenario description blurred exactly this line. |
| 3 | Individual relationship history and institution-specific standing should share one record shape | **OPEN/UNKNOWN, real owner-level choice, not an implementation detail.** Part B raised this and left it open; Part C's Slice 2 implicitly assumed reuse ("reusing whatever shape Slice 1 establishes") without justifying it. `SocialComponent` (per-entity-pair) and `FactionSentiment` (per-faction-pair) are not the same shape today. See Owner Decision Memo #1. |
| 4 | A fifth `RequirementsFilter` category is the correct place for reputation-sensitive opportunity | **OPEN/UNKNOWN — likely wrong architectural level, not just an unverified detail.** `RequirementsFilter`'s own documented job is gating *already-generated* opportunities (binary prerequisite checks). A trusted merchant offering a genuinely *different* contract — not just passing/failing a trust threshold on the same one — is a **generation-time** decision (`ResourceOpportunityProvider`/`ServiceOpportunityProvider`), not a filter-time one. Pass 2 and Part C inherited this placement uncritically from "there are already 4 categories, add a 5th." Corrected: this needs its own design pass, not an assumed slot. |
| 5 | A global reputation view can safely be derived by aggregating private observer attitudes | **OPEN/UNKNOWN — my own synthesis's framing was too casual.** Computing an aggregate is safe; treating it as automatically, universally *knowable* recreates the exact omniscience defect this whole investigation exists to fix, one level up. An aggregate notability projection needs its own information-boundary treatment (who can see it, how widely, how current) — not a free pass because it's "derived." |
| 6 | Wealth, office, and reputation conversion share one prerequisite | **SUPERSEDED, already corrected by Part B, carried forward unchanged.** Wealth→coercive-capacity and office→resource-access are `INDEPENDENT CAUSAL EDGE`s; only reputation→leverage is standing-adjacent. |
| 7 | A source/unit-level check proves a world-level causal behavior | **Reaffirmed as a standing methodological principle, not a specific correction to one claim.** Matches this repository's own existing SimQ/corpus-tier distinction (unit vs. scenario-runtime vs. distribution/corpus evidence). Applied throughout this document's own verification-level columns below — a passing unit test proves reachability, never real-world frequency or distributional behavior. |
| 8 | The first recognition slice alone proves a changed life trajectory | **SUPERSEDED.** Part C's own Slice 1 was labeled "the thin end-to-end proof of changed life trajectory" — overreach. Slice 1 alone proves **differentiated treatment/reaction**, not a changed *opportunity* or a *later decision* consuming it. A genuine end-to-end trajectory proof needs treatment → opportunity → decision chained, not treatment alone. Corrected in the revised roadmap below. |

---

## Product north star (added 2026-09-26, owner-clarified direction)

**The engine simulates a world; a gameplay lens defines a player's relationship to it. These are not
the same thing, and the second must not be frozen into the first.**

- The world exists and changes through agents *and* non-agent processes (weather, ecology, market
  pressure, institutional drift, calamity) whether or not a player is watching any particular
  subject at a given moment.
- Ordinary first-class subjects can accumulate consequential history and, through circumstance,
  become significant. Significance is an outcome, not a privileged starting class — matching the
  Final Integration Batch's own already-established finding that ordinary-person-to-historically-
  significant trajectories require no `HERO` role.
- World processes stay causally coherent across domains. Magic participates in that coherence
  (Batch 12's own already-frozen framing: magic is connected outward into body, capability,
  environment, objects, knowledge, belief, places, institutions, conflict — never an isolated spell
  subsystem). Growth, decline, conflict, positive feedback, and instability are all valid, expected
  outcomes, not failure states to be engineered away.
- Capability, wealth, status, relationships, knowledge, territory, and authority remain distinct
  advantages. Conversion between them happens only through specific, declared causal paths
  (`politics-authority.md`'s own already-frozen Rule) — never a universal power score.
- A gameplay lens (observer, indirect-influence, direct-action, or something not yet chosen) may
  permit different relationships to this same world later. **That choice is explicitly deferred and
  must not be designed into engine semantics now.**
- Simulation value is delivered the moment a player can *encounter* a consequential difference,
  recognize a pattern across situations, and form their own hypothesis about why it happened —
  not when every mechanic has been explained, every event has been logged, or every cause has been
  made visible. Depth means meaningful causal connectivity between the things that do exist, not
  maximum variable count.

**Explicitly not promised**: exhaustive historical detail, complete event logging, universal player
access to ground truth, or a guarantee that every event is interesting. None of these are the bar.

## Epistemic and experiential delivery principle (added 2026-09-26)

Six distinct layers, never collapsed into each other:

```text
world truth and causal history
  → potential evidence in the world
  → what particular characters/institutions can perceive or learn
  → their possibly mistaken beliefs and reactions
  → what the player can actually encounter through a gameplay lens
  → the player's own interpretation
```

**The player is not automatically the world's omniscient debugger.** A biography, event log, map,
HUD, dialogue line, rumor, behavior change, or institutional record is a *projection or source of
evidence* — it has a viewpoint and a scope, exactly like a character's own belief does. Some
projections may be explicitly analytical/debug surfaces (and should be labeled as such); ordinary
player-facing surfaces should never silently leak hidden world truth through the back door of a
convenient UI. This is the same discipline `KnowledgeModelService`'s own stated invariant already
enforces for characters ("hidden world truth is never injected") — the product experience should not
quietly violate for the player what the engine already refuses to violate for an NPC.

**Experiential quality bar**, stated in outcomes, not UI:
- Similar causes tend to have intelligible relationships to similar effects, subject to context,
  chance, and incomplete information — not identical effects every time, and not arbitrary ones.
- Important consequences may leave discoverable traces — through behavior, material changes,
  witnesses, records, offers, and relationships — wherever the world's own rules actually support
  that trace existing. Not every consequence needs a trace; not every trace needs to be found.
- Different observers can hold different accounts. A player can reasonably form a false
  explanation from a partial or unreliable account, exactly as an NPC can.
- New evidence can revise an earlier interpretation. **The engine does not retroactively change
  causal truth to match a plot twist** — revision happens in belief, never in history.
- A player can learn recurring world logic by observing multiple situations, without a mandatory
  tutorial for every mechanic.
- Enough temporal/contextual continuity exists to relate an outcome to an earlier event, without
  printing an internal score or narrating every causal edge.

**Two cross-domain examples, illustrative only, not a UI spec:**
- *Lineage domain.* A player notices a family's holdings shrank generation over generation and
  independently theorizes a feud is draining them — without ever being shown a "feud meter." If the
  world's own displacement/inheritance mechanisms (already `PROVEN CURRENT`, Pass 2) are what
  actually caused it, the player's inference is *correct and earned*, not spoon-fed. If the real
  cause was unrelated (a market collapse, say), the player's plausible-but-wrong theory is not a bug
  — it's the intended texture, provided the world itself stayed coherent underneath.
- *Recognition domain.* A player notices one merchant is unusually warm toward their character and
  a nearby merchant is coldly neutral, despite the character behaving identically in view of both.
  If the difference genuinely traces to one merchant having witnessed something the other didn't
  (once Phase 3 work exists), the player can reconstruct *why* from context — who was where, when —
  without a tooltip explaining "reputation +1." A player who instead assumes both merchants know
  everything about them (today's actual `public_reputation` behavior) would currently be *wrong in a
  way the world's own architecture doesn't yet support being right about* — exactly the gap this
  investigation traced, now framed in product terms instead of code terms.

**Deliberate ambiguity vs. opacity, distinguished explicitly**: ambiguity is a player facing genuinely
incomplete or conflicting evidence that the world itself would also leave incomplete to any in-world
observer — earned, intended texture. Opacity is the player being unable to form *any* reasonable
account because the causal chain producing an outcome has no discoverable trace at all, or behaves
inconsistently with itself — a defect, not texture, regardless of how mysterious it looks from
outside. Distinguishing the two case by case is exactly what "does a discoverable trace exist,
consistent with the world's own rules" resolves — not a judgment call about how interesting the
mystery feels.

---

## A. The causal loop, reassessed as a foundation (not a mandatory pipeline)

Testing the instruction's own loop question against everything Pass 1/2, the synthesis, and
Parts A/B found: **the loop holds as a description of what a coherent world needs, but the repo's
own real architecture already refuses to implement it as one pipeline** — Part A confirmed at
least three independent action-dispatch paths and multiple direct-pipeline-phase bypasses, each
with a stated architectural reason. The loop is the right *test*, not a *target shape to build*.

### Minimal semantic distinctions

For each, semantic home / authoritative owner (only where already established) / participating
domains / causal vs. derived vs. narrative:

**1. World truth vs. observation vs. information vs. belief vs. memory vs. socially-recognized
interpretation.** Already six genuinely distinct, already-separated concepts in this repo, not
collapsed: `AuthoritativeState` (world truth, engine-owned) → `PerceptionGate` (observation,
cognition domain, `PERC-01`) → `InformationProvider`/`InformationResponse` (information,
world/cognition boundary) → `KnowledgeModelComponent` (belief, cognition domain, `KNOW-01/02`) →
the Memory domain (`MEM-02`, currently `INERT-OFF` for causal memory specifically, Pass 1) →
socially-recognized interpretation (partially real for individuals via `SocialComponent`, confirmed
`MISSING` for institutions). All causal state except the last, which should stay a derived/narrative
projection once built for aggregate notability specifically (per calibration #5). **Already covered
by existing Rules** (`KNOW-01/02`, `PERC-01`, `MEM-02`, `SOC-01`) — the gap is realization
(propagation wiring), not a missing distinction or a missing Rule.

**2. Affordance/opportunity vs. desire/goal vs. selected intent vs. valid attempt vs. resolution vs.
consequence.** `AGENCY-03` already states Opportunity/Actionable-Affordance as two required,
distinct tiers. Goal (`ScoreModifierSystem`, Pass 1) → selected intent (`ObjectiveIntentResolver` →
`ActionIntent`, `AGENCY-01`) → valid attempt (domain-specific: Combat's posture recheck, Harvest's
`InteractionSystem.enforce()`) → resolution (domain-specific outcome vocabulary) → consequence
(`TurningPointState`, inventory grants). All six stages are already distinct in Rule text *and*
realized distinctly in code. **The one confirmed unproven edge**: how a selected `ActionIntent`
becomes an `ActionRouter` payload — shared across all three families Part A traced, `UNKNOWN`, not a
missing distinction, a missing trace.

**3. Action by an agent vs. world process vs. involuntary effect vs. institutional decision vs.
environmental event.** Already genuinely separate causal paths, confirmed by Part A: agent action
(`ActionRouter` dispatch), world process (`WorldDynamicsSystem`'s hazard/calamity/sovereignty
phase — a direct pipeline-phase call, no agent decision involved), institutional decision
(`GuildAction.visit()`, also a direct pipeline-phase call, for a stated architectural reason —
`WorkerPacket`'s bounded-context law), environmental event (`EnvironmentService`'s hazard drain).
**Involuntary effect (reflex/compulsion/mind-control) is the one genuinely undesigned case** —
`AGENCY-02`'s own Scope Boundary already defers it explicitly. Carried forward as `OPEN`, matching
the Catalog's own existing stance — not resolved here, and not blocking anything else, since no
found mechanism currently depends on this boundary being settled.

**4. Objective capability/access vs. an actor's belief that an action is possible.** Already a tested
Catalog distinction (`KA-S12`/`KA-S15`, Batch 06) — an entity can be capable but unaware, or aware
but incapable, and both are representable. **The one confirmed realization gap is the same one named
under distinction #1 and by `AGENCY-03`'s own Repository Finding**: opportunity generation reads raw/
omniscient world state rather than perception-gating it, meaning today's actual opportunity pool
collapses "objective capability" and "actor's belief" closer together than the Rule requires. One
underlying defect, visible under two different names — worth stating explicitly so a future fix
isn't attempted twice under different framings.

**5. Physical possession vs. legitimate ownership vs. legal/social interpretation.** Already
well-covered across three batches (`OWN-01/02` Batch 01, `PROP-01/02` Batch 08, `LAW-01/03` Batch
10), including `PROP-02`'s own already-stated finding that the producer of an ownership-changing
event is not automatically the owner of the resulting relation. **Already-confirmed realization
defect**: the heirloom-transfer/`"CHEST"` `ResourceTransferIntent` resolver bug (Batch 08's own
finding) — and Part A's Harvest trace found a **sibling risk**, not independently confirmed either
way: whether `"NODE"`'s own resolver path (the live harvest completion path) resolves cleanly, given
the same resolver is confirmed broken for at least one other `source_kind`. Worth checking together,
not as two separate tickets.

**6. Private attitude vs. durable relationship vs. institutional standing vs. public claim vs.
aggregate narrative notability.** The single most load-bearing distinction in the whole
investigation. Private attitude/durable relationship: `PROVEN CURRENT`, real, owned by
`social_systems` (`SocialComponent`'s per-pair dicts). Institutional standing: `MISSING` entirely,
**no owner established** — a genuinely open design question (Owner Decision Memo #2). Public claim
(`public_reputation`): real, but **wrongly scoped as global/authoritative** rather than
per-observer — its correct long-term role (demoted to a narrow fallback signal? retired in favor of
per-observer views entirely? kept as a genuinely public, declared-scope fact for some specific
cases?) is not decided here. Aggregate narrative notability: `MISSING`, and per calibration #5,
should be a narrative/analytical projection with its own information-boundary treatment, never
free-standing authoritative state.

**7. Actual causal power/resources vs. concrete conversion paths.** Already covered precisely by
`politics-authority.md`'s own Rule (specific, declared edges, never a universal score) — Part B's
own correction (calibration #6) already confirms wealth/office/reputation are not one prerequisite.
No new Rule needed; this is a realization question under already-correct Rule content.

**Cross-cutting conclusion for Section A — bounded explicitly, 2026-09-26.** In every one of these
seven distinctions, **the cases this investigation actually traced** found the World Rule Catalog
already composing to supply the needed semantics — this is a claim about the investigated cases, not
a claim that no semantic gap can exist anywhere in the final engine. Every real gap found in *these
cases* is one of: an implementation-contract gap (the intent→payload edge), a missing mechanism
(institutional standing), absent wiring (rumor's entity-subject producer), weak/unproven evidence
(the `"NODE"` resolver), or a genuinely open architecture question this document itself raises for
the first time (distinctions #6's ownership question, and calibration #3/#4/#5). This matches Pass 1
and Pass 2's own conclusion, reaffirmed a third time for the cases examined — **it does not extend by
assumption to domains or subjects this investigation never traced** (magic, culture, most of
economy/institutions beyond the specific edges Part B checked). **Deferred subjects stay explicitly
open, not silently covered**: coercion, involuntary action, and reflex/compulsion override remain
exactly where `AGENCY-02`'s own Scope Boundary already left them — undesigned, not resolved by
omission. The Catalog remains frozen; any future substantial counterexample uses the same
evidence-first reopening process this investigation itself followed (the TERR-04 and
`combat_engagement`-staleness corrections earlier this week), never a silent edit.

---

## B. Architecture boundaries

**1. Agency and opportunity.** `AGENCY-03`'s two-tier distinction stands; the confirmed gap is the
perception-bypass in opportunity generation (distinction #1/#4 above) — a wiring defect against an
already-correct Rule, not a missing boundary.

**2. Attempt and resolution — corrected, 2026-09-26.** The earlier framing here ("every action
attempt is revalidated at execution, not only at decision time," stated as if it were one shared
mechanical step) overreached. **State authority and attempt correctness are separate concerns.** A
world fact having exactly one canonical authoritative owner does not mean only one code site may
ever write it under that owner's control, and it does not imply every domain must run an identical
`revalidate()` step. Combat's posture-recheck-at-execution fix (6.3%→93.7% coverage, Part A) is real
evidence for *a* declared resolution rule mattering, in that one domain — not evidence that the
*same* mechanical shape belongs everywhere. Reservations, multistage actions, ongoing processes,
conflict resolution, and environmental effects may each have a different, equally legitimate
contract for the same underlying obligation. **The shared semantic obligation, correctly scoped**:
state changes must never be committed using stale assumptions without a declared, domain-owned
resolution rule for what happens when the world moved between decision and commit. **Left explicitly
open, domain-shaped**: what that resolution rule looks like per domain — Harvest's depletion-and-
capacity gate, Quest's per-kind completion evaluators, and Combat's own readiness/posture gate are
three already-different, already-correct answers to the same obligation, not a pattern to unify.
**Caution, unchanged**: `ActionProposal`/`ActionType` (`TCK-20260422`) is standing evidence that a
*broader*, more mechanically-uniform unification was already attempted and not adopted (confirmed
dead, zero consumers, Part A) — a reason for caution against re-attempting that shape, not for
building a new uniform `revalidate()` requirement instead.

**3. State authority and causal history.** Already governed by a real, working law (`TCK-20260401`'s
own bit-identical-replay acceptance criterion). Quest reward's single-writer pattern
(`PROG-084`) is the cleanest live example. **The clearest currently-live violation of this exact
boundary**, found by this session's own separate work two days before this investigation began: the
regional-sovereignty dual-authority bug (`FactionInfluenceService` at ±50 and `WorldDynamicsSystem`
at ±100, both independently able to write `owner_faction_id`) — already scoped as a quick fix,
cited here only as the concrete cautionary example of what this boundary being violated actually
looks like in practice. Durable provenance (`TurningPointState`) exists at individual scale; nothing
comparable exists at institutional/aggregate scale.

**4. Observation and interpretation — corrected, 2026-09-26, claim narrowed.** The heart of this
whole investigation's real finding, but stated too broadly before. What is actually `PROVEN CURRENT`
is narrower than "individual standing exists": `SocialComponent.bonds`/`trust_history` proves a
directed, causally-used history **of direct interpersonal interaction between the two specific
parties**, already correctly consumed by `appraisal.py`'s bond→trust_history→global-fallback
priority order. **This does not prove that an uninvolved witness, or a recipient of secondhand
hearsay, can form the right kind of subject-specific belief, evaluation, and later reaction** — no
evidence was found either way for those two cases, because no producer feeds either path today.
Three cases, not one, and not assumed to share one storage primitive: **direct participation**
(`PROVEN CURRENT`, real, consumed), **direct witnessing without participating** (no producer found;
whether it should reuse `SocialComponent`'s own shape, `process_rumor()`'s shape, or a third shape
of its own is `OPEN`), and **secondhand/hearsay report** (same `OPEN` status, plausibly a different
confidence/decay tier than direct witnessing, not assumed identical to it). Institutions have no
equivalent mechanism at any confidence level, for any of the three cases.

**5. Feedback into future opportunity.** Confirmed `MISSING` as an input category — but per
calibration #4, likely at the **wrong layer** if simply bolted onto `RequirementsFilter`. The
correct layer (generation-time vs. filter-time) is itself an open design question, not a settled
implementation detail.

### Design-test trajectories (stress-testing the model, not scoping new features)

Five deliberately varied trajectories, each surfacing a **different causal owner** — confirming the
model doesn't collapse to one mechanism:

- **Craftsperson → economically influential.** Owner: economy domain (`OWN-*`/`PROP-*`/`RES-*`,
  `politics-authority.md`'s wealth→coercive-capacity edge). Per calibration #6, this trajectory's
  first blocking edge is **independent of standing entirely** — it can be built without waiting on
  recognition work at all.
- **Displaced family → feud.** Owner: lineage domain (`LIN-*`, Batch 09). Already `PROVEN CURRENT`
  and working today (Pass 2's own finding: death→feud inheritance, dying wishes, displacement
  markers). A positive existing example, not a gap — worth citing in the roadmap as proof the
  general *shape* (history → durable consequence → later behavior) already works somewhere real.
- **Guild changing treatment of a member.** Owner: institutions domain (`IP-S17`, Batch 10). The
  confirmed `MISSING` piece, unowned pending Owner Decision Memo #2.
- **Settlement reacting to danger.** Owner: world-evolution/environment domain
  (`RegionThreatClassifier`, hazard/calamity systems) — a genuinely different *shape* of reaction:
  triggered by an aggregate/environmental condition, not an individual-standing record at all. Tests
  that the model doesn't over-fit to "one entity recognized by one observer."
- **Political office exercising authority.** Owner: institutions/politics domain (`INST-03`,
  `AUTH-*`). Confirms office→resource-access is a genuinely separate edge from personal reputation,
  matching Part B's own split (calibration #6).

No single universal ontology is implied or needed by these five — each keeps its own domain's
already-established ownership, exactly as the Catalog's own admission discipline requires.

---

## C. Delta from Part C, and the revised roadmap

### What Part C got right (retained)
- The six-capability framing of the loop itself.
- Slice 0's groundwork repairs (the `"NODE"` resolver check, the `AGENCY-03` perception-bypass fix,
  the `ActionProposal` retire/adopt question) — still valid, independent, low-risk.
- The roadmap-authority ambiguity finding (§0 of Part C) — unchanged, still correct.
- Part B's own corrections (calibration #6) — carried through unchanged.

### What Part C got wrong or overreached on (corrected here)
- **Slice 1 was labeled a full changed-life-trajectory proof; it isn't** (calibration #8) — it's one
  necessary piece of a larger chain.
- **Slice 1's own scenario conflated direct witnessing with secondhand hearsay** (calibration #2) —
  these need to be told apart before either is wired.
- **Slice 2 assumed shape-reuse between individual and institutional standing without justifying
  it** (calibration #3) — now correctly left open.
- **Slice 3 assumed `RequirementsFilter` was the right architectural home without questioning it**
  (calibration #4) — now correctly flagged as a real open design question, likely wrong as stated.
- **The synthesis's "notability is just a safe derived view" framing was too casual** (calibration
  #5) — now correctly flagged as needing its own information-boundary design.
- Part C organized the whole roadmap around *recognition* first. This document reorganizes around
  the *foundation* first (state authority, attempt/resolution), matching this instruction's own
  critique — recognition is capability area 3, not capability area 1.

### Revised capability areas — a map, not a compulsory pipeline (corrected, 2026-09-26)

The five areas below are numbered for reference, not because every world trajectory must pass
through all five in that order. **Real causal dependency is per-trajectory, not universal**: the
lineage trajectory (Section B) already has a working history-to-behavior loop today with none of
Phase 3's recognition machinery involved at all; the craftsperson/wealth trajectory's first edges
(wealth→coercive-capacity, office→resource-access) are `INDEPENDENT CAUSAL EDGE`s (Part B) that need
none of Phase 3 either. Phases 1 and 2 can develop concurrently with parts of Phase 5 (breadth work
in already-strong domains like lineage doesn't wait on the recognition work at all). The numbering
below states *a* coherent build order for the specific loop this investigation traced most deeply
(the hunter/shopkeeper/guild case) — not *the* order for the whole engine. The whole-engine roadmap
(a separate document, see below) reorganizes this as an explicit capability map with per-trajectory
dependency paths, including at least one path that never touches recognition at all.

**Phase 1 — Foundational causal/authority contract.**
- World-level outcome: every durable world fact has exactly one authoritative writer; every action
  attempt is revalidated at execution, not just decision time.
- Invariant: Boundary #2/#3 above, combined.
- Already designed: `TCK-20260401`'s own unification; the Combat posture-recheck precedent.
  Realized: strongly, for Combat and Quest reward specifically. Unknown: the intent→payload edge
  (all 3 families); the `"NODE"` resolver; whether the regional-sovereignty pattern recurs
  elsewhere unnoticed.
- Minimum cross-domain demonstration: the same "revalidate at execution" invariant checked (not
  necessarily rebuilt) against at least one domain outside Combat.
- True dependency: none upstream — this is the floor everything else stands on.
- Explorable independently: yes, entirely — can start immediately.
- Enters Semantic Control Plane: any confirmed dual-authority pattern found feeds M3 as an ordinary
  triage finding, same as the regional-sovereignty case already did.

**Phase 2 — Situated agency and action.**
- World-level outcome: subjects encounter genuinely partial opportunities and experience real
  success/failure/cost/persistence differently across contrasting domains (not just Combat).
- Invariant: Boundary #1/#2 — opportunity/affordance distinctness, revalidation at execution.
- Already designed: `AGENCY-01/02/03/04` fully. Realized: Combat strongly; Harvest via generic
  `INTERACT` (confirmed live, contra two dead named-harvest files); Quest reward's single-writer
  pattern. Unknown: whether Trade is equally clean (not traced to the same depth by Part A).
- Minimum demonstration: the three already-traced families (Combat/Harvest/Quest) both individually
  sound *and* their shared upstream edge (intent→payload) confirmed, not just individually plausible.
- True dependency: Phase 1's revalidation invariant, if adopted, should land here at the same time,
  not as a retrofit.
- Enters M3: the perception-bypass in opportunity generation is an ordinary triage-worthy finding
  today, independent of everything else in this document.

**Phase 3 — Information and world reaction.**
- World-level outcome: specific observers/institutions can learn, mislearn, remember, interpret, and
  respond, without omniscient injection — the individual case working *and* correctly bounded (not
  leaking into automatic global knowledge), the institutional case built for the first time.
- Invariant: Boundary #4 — direct-participation, witnessed, and hearsay knowledge stay distinguished,
  never collapsed into one confidence tier without a stated reason.
- Already designed: `SOC-01`, `KNOW-01/02`, `AGENCY-02`'s influence-not-determination framing.
  Realized: direct-interaction case fully (`bonds`/`trust_history` + `appraisal.py`). Unknown:
  whether direct-witnessed-without-participation should use the same tier as hearsay (calibration
  #2); institutional standing's own shape (Owner Decision Memo #1/#2).
- Minimum demonstration: the two-shopkeeper scenario, corrected to genuinely separate "A directly
  transacted" (already works) from "A merely witnessed, uninvolved" (the real gap) — not the
  conflated version Part C proposed.
- True dependency: Phase 2's opportunity/decision machinery must exist for there to be an event
  worth propagating in the first place — otherwise causal, not merely convenient, ordering.
- Enters M3: this phase's own findings (once real) become the Catalog's first real test of whether
  `SOC-01`/`KNOW-01/02` compose correctly across a live propagation case — genuinely new evidence
  for the Catalog, not just a repeat of existing findings.

**Phase 4 — Development and opportunity feedback.**
- World-level outcome: accumulated history measurably alters access, risk, resources, relationships,
  and future trajectory — closing the loop Phase 3 opens.
- Invariant: Boundary #5 — feedback into opportunity exists as a real causal edge, at whichever layer
  (generation vs. filter) proves correct.
- Already designed: `politics-authority.md`'s declared-edge Rule. Realized: nothing yet at this
  layer — confirmed `MISSING` as an input category, current architectural placement unresolved
  (calibration #4).
- Minimum demonstration: an opportunity *set*, not just a price or dialogue line, differing between
  two entities with different standing — and the wealth/office-independent edges (craftsperson
  trajectory) proven separately, since they don't depend on Phase 3 at all.
- True dependency: Phase 3 for the reputation-adjacent edge specifically; **wealth/office edges are
  independent and can proceed in parallel starting now** (calibration #6).
- Enters M3: ongoing, non-blocking, unchanged.

**Phase 5 — Systemic breadth and validation.**
- World-level outcome: the same foundation (Phases 1-4) composes across non-combat professions,
  institutions, places, politics, economy, lineage, and other domains — proven by the five design-
  test trajectories in Section B, not assumed.
- Already designed: lineage's feud/inheritance chain is already a **positive existing proof** this
  composes somewhere real. Realized: unevenly — strong for lineage, absent for institutions,
  independent-and-untested for economy/politics.
- Minimum demonstration: at least one trajectory outside the hunter/shopkeeper/guild set (the
  settlement-reacting-to-danger case is the best test of genuine breadth, since it's
  aggregate-triggered, not individual-standing-triggered).
- True dependency: Phases 1-4 for the trajectories that need recognition/opportunity-feedback;
  none for the ones that don't (lineage already proves itself; craftsperson/wealth can run parallel).
- This phase is explicitly open-ended — not a fixed exit condition, an ongoing validation posture.

### One eventual end-to-end validation trajectory

**An ordinary hunter's witnessed (not merely self-reported) deed changes one specific merchant's
later contract offer to them, which the hunter then accepts, producing a materially different
outcome than an otherwise-identical stranger would have received in the same circumstance.** This
requires Phases 2 (real action + consequence), 3 (witnessed propagation, correctly distinguished
from direct interaction), and 4 (the changed opportunity itself, plus a later decision that actually
consumes it) chained — not any one phase alone, correcting calibration #8 directly.

**Smaller proofs that can and should precede it, independently:**
- Phase 1's revalidation invariant, checked against one non-Combat domain (no dependency on
  anything else).
- The craftsperson/wealth trajectory (Phase 4's independent edges) — provable without any
  recognition work at all.
- The lineage trajectory — its underlying *mechanisms* are already provable today, zero new
  simulation work needed. **Correction, external review, 2026-09-26**: this is evidence the
  mechanism-level pattern works, not a claim that a player-facing *projection* of it is cheap or
  ready — event selection, temporal continuity, and pacing for an actual product surface remain
  unchecked. Leading candidate for the systemic-world roadmap's own feasibility gate, not a
  committed proof in itself. Still a useful working reference example of the pattern while
  everything else is built.

**This one scenario validates a causal chain. It does not define final ontology, and it does not
imply universal completion across professions, institutions, magic, or any domain not named here** —
stated explicitly per the instruction's own closing caution.

### Where this lives

Confirms Part C's §0 finding, now reasoned through more carefully: `rpg_design_roadmap.md` (M1-M9)
is closed and the wrong shape (a finished, numbered feature list) for an open-ended, phase-based
foundational program; `simulation_semantic_control_plane/roadmap.md` is deliberately scoped to
mapping, not new capability design, and mixing the two would blur a boundary that roadmap itself
took care to draw; `long_term_development_roadmap.md` is a different, engine-infrastructure axis
entirely. **Recommendation, `PROPOSED`**: a new standalone document, not a forced fit into any
existing numbering — see Owner Decision Memo #3 for the permanent-home choice itself.

---

## Owner Decision Memo

Only the choices this evidence cannot settle — target semantics, architectural commitment, or
program scope. Not implementation details (per the instruction's own explicit boundary).

**1. Should individual-scale and institution-scale standing share one record shape, or be built as
two distinct types?**
Recommended default: **build them as two distinct types initially** (specialize downward from
`FactionSentiment`'s own existing directed shape for institutions, keep `SocialComponent` as-is for
individuals), and revisit unification only if a real consumer needs to query both uniformly.
Consequence of the default: cheaper, lower-risk near-term; possible future refactor if a genuine
shared-query need emerges later. Consequence of choosing unification now: one design pass instead of
two, but real risk of forcing institution-shaped and individual-shaped semantics into an
ill-fitting common mold before either is proven. `OPEN` either way — this is a real call, not
resolved by evidence.

**2. Who owns institutional standing as a concept — is it a new responsibility for the institutions
domain (Batch 10), the social/relationship domain, or a genuinely new shared boundary?**
Recommended default: **institutions domain**, since `IP-S17` is already that domain's own scenario
and its own Rule content (`ORG-*`/`INST-*`) already anticipates organizations tracking history about
members. Consequence: keeps ownership aligned with where the Rule already lives; risk is thin
practical precedent for how that domain's existing state model would carry a per-individual field.
`OPEN` — flagged, not resolved.

**3. What is this document's permanent home?**
Recommended default: **a new standalone file** (e.g. `docs/plans/entity_world_recognition_roadmap.
md`), not a revival of `rpg_design_roadmap.md`'s numbering — that roadmap's own M1-M9 shape is a
closed, dated feature list; forcing a new, open-ended, phase-based program into it "to reuse the
numbering" would misrepresent both. Consequence of the alternative (an M11): easier discoverability
for anyone who already knows the old roadmap, but implies false continuity with a finished program.
`OPEN` — genuinely the owner's call, not evidence-resolvable.

**4. Should `public_reputation` be retired, narrowed to a specific declared use, or kept as-is once
per-observer standing exists?**
No recommended default — genuinely `UNKNOWN` until Phase 3 work reveals what, if anything, still
needs a cheap global fallback (Part B found `appraisal.py` already uses it only as a last resort for
total strangers — that specific role might be worth *keeping*, deliberately, rather than eliminating
outright). Flagged for revisit once Phase 3 is scoped, not decided now.

**Confirmed not owner-level, left to local implementation investigation once boundaries are
set:** which existing class to extend, whether to retire `ActionProposal` immediately or reuse it,
exact field layouts for any new record — per the instruction's own explicit boundary, these belong
to whoever scopes the first real ticket under each phase.
