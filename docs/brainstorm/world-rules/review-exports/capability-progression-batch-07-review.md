---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Review Export: Batch 07 (Capability / Progression / Conflict)

**This file is a generated, non-authoritative review view.** It exists so an external reviewer
can assess the batch without opening every canonical file. It is never edited directly as the
fix for a review finding — feedback goes back into the canonical files below, and this export is
regenerated from them. See `world-rules/README.md`'s review index for the current status of
every batch.

## Batch scope

The fourth domain-facing (Milestone B) batch — how lived experience becomes durable capability
change, how power is plural rather than one stat, and how conflict creates consequences
without reducing progression to bigger numbers. Three rule families: Capability/Progression,
Learning/Adaptation, Conflict/Combat. Drafted 2026-09-22, then revised the same day per a
targeted Rule-admission and semantic cleanup (`tmp/world-rule-batch-7-followup-ext-ai.md`) —
see "Follow-up revision summary" below.

## Follow-up revision summary (2026-09-22)

A targeted Rule-admission and semantic cleanup was applied without redesigning the batch or
discarding any repository finding:

1. **Repository/evaluation language removed from Domain Rule statements.** PROG-01, PROG-02,
   PROG-05, PROG-06 all originally stated repository facts ("this repository has N mechanisms,"
   "must be checked/verified against the repository's own implementation," "a documentation
   claim... does not match") inside their own quoted Rule text. Each was rewritten to state only
   the target semantic core; every repository fact moved to that Rule's own Repository
   evidence/Findings, where it belongs.
2. **PROG-04 reclassified from a Domain Rule to Inherited.** "Capability loss ≠ identity loss ≠
   history erasure" is fully covered by combining Batch 01/05's LIFE-03/HP-01 (death/identity
   persistence) with Batch 01/05's BODY-04/06 (injury durably reduces capability) — no
   genuinely new progression-specific semantic content survives the combination. Importance of
   a distinction is not, by itself, grounds for a local Rule ID.
3. **Learning/Adaptation's two original Rules reassessed.** The original LEARN-01 ("this
   repository's learning is epistemic, not capability") and LEARN-02 ("only success grants XP
   here") were primarily repository findings, not target world laws. LEARN-02 retired entirely
   to Repository Findings — the follow-up review explicitly required not establishing
   "success-only progression" as a law merely because current code behaves that way. LEARN-01
   was rewritten into a genuinely normative statement (an experience's epistemic and capability
   effects are distinct, independently-declared outputs) that keeps the target design open to
   practice → capability, failure → learning, exposure → adaptation, or success → progression,
   whichever a world declares. This family now has exactly one genuine Domain Rule.
4. **CONFLICT-02 reclassified from a Domain Rule to Inherited.** The semantic requirement that
   decisions must respect subject-local perception/knowledge is already fully established by
   Batch 06 (PERC-01, KNOW-01, AGENCY-01, AGENCY-02). That live combat targeting correctly uses
   `PerceptionGate` is real, valuable Repository evidence supporting that already-established
   boundary, not a new Conflict-specific semantic claim. CONFLICT-01 survived unchanged.
5. **Two progression probes added.** CP-S17 (Non-Combat Lived Experience — the repository may
   legitimately return MISSING; the purpose is confirming the target Rule Catalog does not
   accidentally define progression as combat/quest XP only). CP-S15 (Ordinary Creature →
   Regional Threat) was deepened in place, rather than duplicated, to explicitly distinguish
   generic reaction to a creature's kind/threat from reaction to this specific historied
   individual — central to the project's own vision.
6. **All major findings preserved prominently, not weakened**: combat XP farming without a
   real counterforce; lived-history → capability progression is narrow; `TRAIN_SKILL` has no
   producer; ordinary non-HERO significance tracking is missing; fame → followers conversion is
   missing; capability changes that do exist have strong downstream consumers; Evolution kind
   changes are causally live.

## Canonical files included

- `capability-progression/capability-progression.md` (PROG-01, PROG-02, PROG-03, PROG-05,
  PROG-06, PROG-07 — Domain Rules; PROG-04 — Inherited)
- `capability-progression/learning-adaptation.md` (LEARN-01 — Domain Rule)
- `capability-progression/conflict-combat.md` (CONFLICT-01 — Domain Rule)
- `scenarios/capability-progression-batch-07.md` (CP-S01–S17)

## Rule admission accounting

Per the standing admission discipline: a statement earns a new local Rule ID only if it adds or
refines target world semantics beyond Rules already defined elsewhere. Post-follow-up, this
batch's 26 total catalog entries break down as:

- **8 genuine Domain Rules**: PROG-01, PROG-02, PROG-03, PROG-05, PROG-06, PROG-07; LEARN-01;
  CONFLICT-01.
- **13 Inherited/Applied Foundational Rules** (6 original + 1 reclassified in
  `capability-progression.md`; 1 original + 2 added in `learning-adaptation.md`; 3 original + 1
  reclassified in `conflict-combat.md`): in `capability-progression.md` — capability loss ≠
  identity/history loss (PROG-04, reclassified — LIFE-03, HP-01, BODY-04, BODY-06),
  foundational Capability (CAP-01–05), a real causal path requirement (CAUSE-01), capability ≠
  guaranteed success (CAP-01, AGENCY-04), injury/scars reduce capability (BODY-04, BODY-06),
  ordinary transformation via valid trigger (TRANS-01, ID-03); in `learning-adaptation.md` — a
  durable-change causal-bridge requirement (CAUSE-01), capability changes only through a
  declared mechanism (this batch's own PROG-01), belief/knowledge changes only through a
  declared path (KNOW-02); in `conflict-combat.md` — combat outcomes are a real, differentiated
  vocabulary (LIFE-01, LIFE-02), Combat produces events while Life/Body owns bodily consequence
  (BODY-07, OWN-02), capability ≠ guaranteed conflict outcome (CAP-01, AGENCY-04),
  conflict/combat decisions must respect perception/knowledge (CONFLICT-02, reclassified —
  PERC-01, KNOW-01, AGENCY-01, AGENCY-02).
- **5 Scope/Deferred Boundaries** (unchanged by the follow-up): major supernatural
  transformation stays with Magic, later-domain power-conversion chains, no universal
  progression architecture, in `capability-progression.md`; detailed conditioning/habit/
  psychological modeling, in `learning-adaptation.md`; no universal conflict-resolution
  framework, in `conflict-combat.md`.

**Genuine new-Rule count for this batch: 8** (was 11 before the follow-up reclassified PROG-04
and CONFLICT-02 to Inherited and retired LEARN-02 to Repository Findings while rewriting
LEARN-01 into normative form). **Inherited/reused foundation count: 13 entries, citing 17
distinct foundational Rule IDs** (CAP-01, CAP-02, CAP-03, CAP-04, CAP-05, CAUSE-01, BODY-04,
BODY-06, BODY-07, OWN-02, TRANS-01, ID-03, LIFE-01, LIFE-02, LIFE-03, HP-01, AGENCY-04, PERC-01,
KNOW-01, AGENCY-01, AGENCY-02 — 21 IDs, several cited more than once across entries).

## Rule Inventory

| ID | Category | Short name | One-line semantic purpose | Status |
|---|---|---|---|---|
| PROG-01 | Domain Rule | Capability Change Traces to a Declared Mechanism, Plural | Different mechanisms may coexist without unification. | Accepted, revised |
| PROG-02 | Domain Rule | XP/Level's Meaning Comes From Declared Consequences | Materialized abstractions; neither substitutes for what it represents. | Accepted, revised |
| PROG-03 | Domain Rule | Capability ≠ Level, Bidirectionally Independent | Neither implies the other; confirmed both directions. | Accepted |
| PROG-05 | Domain Rule | Repeatable Sources Must Declare Scaling/Limiting Semantics | Unlimited repeatability must not arise accidentally. | Accepted, revised |
| PROG-06 | Domain Rule | Progression May Change World Reaction Through Declared Channels | Real but narrow channel confirmed as evidence. | Accepted, revised |
| PROG-07 | Domain Rule | Power Conversion Edges Are Specific, Never Automatic | Combat→fame real; fame→followers confirmed MISSING. | Accepted |
| LEARN-01 | Domain Rule | Epistemic and Capability Effects Are Distinct, Declared Outputs | Rewritten from a repository description into genuinely open target semantics. | Accepted, revised |
| CONFLICT-01 | Domain Rule | Conflict Is Broader Than Combat | Resource contention resolves incompatible outcomes without a fight. | Accepted |

## Inherited Foundations Summary

| Entry (as stated in its own file) | Foundational Rule(s) reused | File |
|---|---|---|
| Capability loss ≠ identity loss ≠ history erasure (formerly PROG-04) | LIFE-03, HP-01, BODY-04, BODY-06 | `capability-progression.md` |
| Foundational Capability ≠ acquisition/loss mechanics | CAP-01–05 | `capability-progression.md` |
| A durable consequence requires a real causal path | CAUSE-01 | `capability-progression.md` |
| Capability does not guarantee success | CAP-01, AGENCY-04 | `capability-progression.md` |
| Injury/scars are a real capability-reducing mechanism | BODY-04, BODY-06 | `capability-progression.md` |
| Ordinary transformation is a valid Transformation instance | TRANS-01, ID-03 | `capability-progression.md` |
| A durable change requires a real causal bridge | CAUSE-01 | `learning-adaptation.md` |
| Capability changes only through a declared mechanism | PROG-01 (this batch) | `learning-adaptation.md` |
| Belief/knowledge changes only through a declared path | KNOW-02 (Batch 06) | `learning-adaptation.md` |
| Combat outcomes are a real, differentiated vocabulary | LIFE-01, LIFE-02 | `conflict-combat.md` |
| Combat produces events; Life/Body owns bodily consequence | BODY-07, OWN-02 | `conflict-combat.md` |
| Capability does not guarantee a favorable conflict outcome | CAP-01, AGENCY-04 | `conflict-combat.md` |
| Conflict/combat decisions must respect perception/knowledge (formerly CONFLICT-02) | PERC-01, KNOW-01, AGENCY-01, AGENCY-02 | `conflict-combat.md` |

## Scenario Inventory

| Scenario ID | Short name | Trajectory | Rule families challenged | Result |
|---|---|---|---|---|
| CP-S01 | Practice Creates Capability | practice → learning → capability | Progression, Learning | Partial (substituted mechanism) |
| CP-S02 | Repetition Without Learning | trivial repeat → no diminishment | Progression | Revealed gap |
| CP-S03 | Failure Teaches | fail → information → later change | Learning | Partial (epistemic only) |
| CP-S04 | Experience With No Durable Change | no mechanism → unchanged | Learning, Causality (inherited) | Covered |
| CP-S05 | Level Up With Real Consequence | threshold → level → real change | Progression | Covered |
| CP-S06 | Level With No Consumer (counter) | level increases → no consumer | Progression | Blocked (premise false here) |
| CP-S07 | Capability Without Level | injury/equipment → capability, Level unchanged | Progression | Covered |
| CP-S08 | Injury Causes Regression | injury → persistent impairment → decrease | Progression (inherited), Life/Body (inherited) | Covered |
| CP-S09 | Conflict Without Combat | contention → yield/loss → no fight | Conflict | Covered |
| CP-S10 | Combat Does Not Guarantee Progression | combat occurs → no qualifying cause → unchanged | Progression | Covered |
| CP-S11 | Combat, Defeat, Survival | fight → defeat → survives → later effect | Conflict/Combat (inherited) | Covered |
| CP-S12 | Stronger Entity Still Loses | higher capability → context differs → loses | Conflict/Combat (inherited) | Covered |
| CP-S13 | Power Conversion | wins → reputation → opportunity/follower | Progression | Partial |
| CP-S14 | Progression Changes World Reaction | capable entity → others respond differently | Progression | Partial |
| CP-S15 | Ordinary Creature → Regional Threat + Significance Without HERO Role (deepened) | survive → adapt → capable → generic vs. individual reaction | Progression | Partial, sharpened |
| CP-S16 | Loss of Capability Without Loss of History | age/injury → decline → significance persists | Progression (inherited), Life/Body & History (inherited) | Partial (injury yes, aging MISSING) |
| CP-S17 | Non-Combat Lived Experience (added) | environmental/social/practical experience → declared mechanism → capability change | Learning, Progression | Revealed gap (legitimate MISSING) |

## Coverage Summary

**Capability/Progression**
- plural, non-unified acquisition/loss mechanisms — CP-S01, CP-S07
- XP/Level materialized-abstraction, meaning from declared consequences — CP-S05, CP-S06
- capability ≠ Level, both directions — CP-S07
- capability loss ≠ identity/history loss (inherited) — CP-S08, CP-S16
- repeatable sources must declare scaling/limiting semantics (confirmed undeclared here) —
  CP-S02, CP-S10
- progression → world reaction through declared channels (real but narrow) — CP-S14, CP-S15
- power conversion edges are specific — CP-S13

**Learning/Adaptation**
- epistemic and capability effects are distinct, declared outputs — CP-S01, CP-S02, CP-S03,
  CP-S04, CP-S17

**Conflict/Combat**
- Conflict broader than Combat — CP-S09
- perception/knowledge-respecting decisions (inherited), capability ≠ guaranteed outcome
  (inherited) — CP-S10, CP-S11, CP-S12

## Deferred Semantics

- Major supernatural transformation (human → vampire) stays with Magic.
- Later-domain power-conversion chains (economic, social, political, institutional,
  territorial, magical) stay deferred to their own future domain batches.
- No universal progression architecture is introduced.
- Detailed conditioning/habit/psychological modeling beyond what this repository already
  evidences is not introduced.
- No universal Conflict-resolution framework covering every imaginable contest type is built.

## Cross-domain findings

- Capability/Progression ↔ Identity/History-Provenance/Body-Condition: the reclassified
  PROG-04 entry is the cleanest example this batch produced of the admission discipline
  working correctly on a second pass — a claim that felt locally important on first draft, but
  that a stricter reading showed was fully covered by combining two already-established
  boundaries.
- Learning/Adaptation ↔ Perception/Knowledge (Batch 06) ↔ Capability/Progression: LEARN-01's
  revised form sits exactly at the seam between KNOW-02 (belief changes only via declared path)
  and PROG-01 (capability changes only via declared mechanism) — its own genuine contribution is
  stating that these are two distinct possible *outputs* of one experience, not a third
  independent claim about either side.
- Conflict/Combat ↔ Perception/Agency (Batch 06): the reclassified CONFLICT-02 entry preserves
  this batch's own most significant cross-cutting finding (live combat targeting is already
  perception-gated, a positive counter-example to Batch 06's two CONFLICTING findings) as
  Repository evidence supporting an already-established Rule, exactly where that evidence
  belongs once the underlying semantic claim is recognized as Batch 06's own.
- Capability/Progression ↔ Ecology/Population (Batch 05) ↔ History/Provenance: CP-S15's own
  deepened finding (generic kind/threat reaction vs. reaction to a specific historied
  individual) is this batch's own sharpened version of the "individual↔aggregate causal loop"
  pattern ECOL-03 first surfaced — here specialized to the question of *named* recognition
  rather than aggregate population counts.

**Explicit call-out — genuine new Domain Rule count:** **8** (was 11 before the follow-up).

**Explicit call-out — semantic meaning of XP and Level:** XP and Level are materialized
abstractions whose meaning comes from their declared world consequences; neither substitutes
for the underlying capability or history it represents (PROG-02, revised). This repository's
own XP is granted only via the conservation path from combat/quest success; Level's crossing
triggers real, verified downstream consequences (AP grant, skill unlocks, a flat HP bump, stat
recalculation) — confirmed as Repository evidence, not asserted by the Rule itself.

**Explicit call-out — whether progression currently derives from lived history:** **Only
narrowly.** Combat/quest success drives XP directly. Most other named lived-history categories
produce no capability change at all — confirmed MISSING (see Repository Findings), and CP-S17
confirms this narrowness is a fact about this repository, not a limitation of the target
Rules, which remain open to a wider set of experience-types (LEARN-01).

**Explicit call-out — whether capability changes have real downstream consumers:** **Yes,
richly, for the capability changes that do occur.** `recalculate_combat_stats()` is triggered
by every relevant `IdentityUpdate`/`AttributeUpdate`/`EquipmentUpdate`, feeding directly into
combat resolution, tactical targeting, and adventure-route scoring.

**Explicit call-out — whether Evolution/kind changes are causally live or inert:** **Live,
richly so.** `entity.kind` is read across at least eight distinct modules — confirmed, not
inert, though most of those reads are hardcoded kind-string branches rather than a general
capability-scaled function.

**Explicit call-out — whether conflict consequences propagate beyond combat:** **Yes, for one
real, narrow, generic channel** (`ThreatService.record_kill()`'s retaliation pressure) —
**but not for named-individual recognition**, per CP-S15's own deepened finding.

**Explicit call-out — whether repeated trivial activity can create unbounded progression:**
**Yes, confirmed, for combat XP specifically — the single most load-bearing finding in this
batch, unchanged by the follow-up.** No diminishing-returns, repeat-count, or difficulty-
mismatch adjustment exists on the XP-reward formula; PROG-05's own revised Rule requires a
*declared* stance, and this repository's combat-XP source declares none — an accidental
default, not a stated design choice.

**Explicit call-out — whether capability loss/regression exists:** **Yes, for injury and
equipment specifically (now an Inherited entry, PROG-04); MISSING for skill decay, aging, and
most other named loss categories.** See CP-S16.

**Explicit call-out — whether ordinary entities can causally become historically
significant:** **Sharpened by the follow-up review into two distinct halves.** A *generic*
reaction to a creature's kind or the raw fact of a threat is real and confirmed
(`record_kill()`'s retaliation pressure, `entity.kind`-keyed branches). A reaction to *this
specific historied individual* — the world or another entity recognizing that this particular
creature, by its own lived history, is the source of the danger — is confirmed **MISSING** for
any non-HERO entity; only `LegendFact`/`FameState` provides this for HERO-role entities. The
current Rules permit the full trajectory, including individual recognition; the current
repository realizes only the generic half for ordinary creatures (CP-S15).

## Repository Findings

No fully CONFLICTING finding (an active violation of a target Rule) was identified in this
batch's own new territory — the one CONFLICTING-adjacent question this batch was specifically
asked to check (§15's Agency-integration requirement) resolved to a **positive, SUPPORTED**
counter-example instead (live combat targeting is perception-gated), preserved as Repository
evidence under the reclassified Inherited entry in `conflict-combat.md`.

**SUPPORTED (1 finding, notably positive):**
1. `TacticalDecisionSystem`'s live hostile-candidate gathering routes through
   `PerceptionGate.can_perceive()` before any neighbor becomes target-eligible.

**INERT/OFF (2 findings):**
2. The declared `combat_engagement` domain never runs in production
   (`ENABLE_COMBAT_ENGAGEMENT` default OFF).
3. `BreakthroughService`'s granting path is never invoked in production outside tests.

**MISSING (7 findings, all preserved prominently per the follow-up's own explicit
instruction):**
4. No counterforce (diminishing returns, difficulty-mismatch scaling, or a real per-tick cap)
   exists against repeated-trivial-kill farming for combat XP — the most load-bearing finding
   in this batch.
5. `TRAIN_SKILL` (practice) is an unreachable route family.
6. No capability-improving mechanism exists for most named lived-experience categories
   (environmental exposure, social experience, leadership, long-term practice, near-death
   survival beyond `REBIRTH`'s own lifecycle fact) — lived-history → capability progression is
   narrow.
7. No surrender, capture, or forced-displacement-as-a-combat-outcome exists.
8. No fame-to-followers (or any concrete recruitment) conversion edge exists.
9. **No mechanism recognizes a specific non-HERO individual's own growing significance** —
   only generic kind/threat-level reaction exists for ordinary creatures; `LegendFact`/
   `FameState`'s individual-tracking channel is role-gated to HERO entities only. Sharpened by
   the 2026-09-22 follow-up's own deepened CP-S15.
10. Success-only progression (only combat/quest success grants capability-relevant XP in this
    repository) is a repository fact, not a target-semantic requirement — LEARN-01's own
    revised Rule keeps the target design open to other experience-types.

**Documentation/implementation mismatch (not itself a Rule-conformance finding):**
11. `docs/engine/supported_progression_surface_phase5.md` claims progression is bounded by
    `max_xp_per_tick` — no such symbol, constant, or check exists anywhere in `src/`.

**Naming near-collision (not a semantic overlap):**
12. `src/world/displacement.py` is a calamity-driven, World-Evolution-domain population-
    relocation mechanism, unrelated to any combat-defeat outcome.

Key evidence, all confirmed by direct code/doc inspection: `docs/mechanics/
attribute_progression_contract.md`, `docs/engine/supported_progression_surface_phase5.md`,
`src/progression/{leveling,skills,breakthroughs,class_tiers}.py`, `src/engine/evolution.py`,
`src/engine/combat.py`, `src/engine/combat_rewards.py`, `src/world/threat.py`,
`src/world/creature_territory.py`, `src/world/displacement.py`,
`docs/mechanics/04_strategic_cognition.md` §13, `src/engine/tactical.py`,
`src/domains/adventure/{scoring,generator,mapper,schema}.py`,
`docs/mechanics/adventure_routing_contract.md`.

## Owner-attention decisions

- **Highest priority.** Whether a counterforce should be added to combat XP rewards — a
  confirmed, real gap, and a documentation claim that does not match current behavior.
- Whether an ordinary (non-HERO) entity's individually-growing significance should gain its own
  tracking mechanism, closing the sharpened CP-S15 gap.
- Whether `TRAIN_SKILL` should gain a real opportunity producer and a real capability grant.
- Whether fame/reputation should gain a real follower/recruitment conversion edge.
- Whether the declared `combat_engagement` domain should be turned on, and whether its
  permissive perception-gate fallback should instead fail closed.
- Whether this repository should ever declare a non-success experience-type (failure,
  repetition, exposure) as capability-affecting — LEARN-01's own Rule leaves this fully open.

## Candidate disposition

Eight Domain Rules survive the follow-up's stricter re-examination across three families (6
Capability/Progression, 1 Learning/Adaptation, 1 Conflict/Combat) — **all 8 accepted, 0
rejected.** Two Domain Rules from the original draft (PROG-04, CONFLICT-02) were reclassified
to Inherited; one (LEARN-02) was retired to Repository Findings; one (LEARN-01) was rewritten
into normative form rather than merged or dropped. No target-semantic contradiction was
introduced by any of these changes — every reclassification narrowed the Domain Rule count
without discarding a single piece of evidence, a single scenario result, or a single cross-
domain link; everything moved to a more accurate category rather than being lost. Thirteen
Inherited/Applied Foundational Rules and five Scope/Deferred Boundaries round out the 26 total
catalog entries.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/capability-progression-batch-07-report.md` (local review report, not part of this
catalog).

---

> **BATCH 07 PASS — READY TO FREEZE.**
>
> The target Rule Catalog supports an ordinary individual's causal path toward exceptional
> capability and historical significance, but the current repository only partially realizes
> that path, especially for non-HERO named individuals.

All required artifacts exist: three rule-family files (8 genuine Domain Rules; 26 total
catalog entries), one scenario file (17 scenarios covering all sixteen required seed probes
plus one follow-up-required addition, with one probe deepened rather than duplicated), this
review export with all required sections plus every explicitly-required call-out, and a local
disposition report. No target-semantic contradiction was introduced by the follow-up's own
reclassifications — each one narrowed which statements carry a local Rule ID without changing
what any Rule requires of the world, and without discarding any repository finding. All twelve
of the batch instruction's own original stop-condition checklist items remain satisfied,
sharpened rather than weakened: foundational Capability is not duplicated; XP/Level semantics
are explicit where they exist; lived experience can produce durable change through declared
paths, and the target design remains genuinely open to which experience-types qualify
(LEARN-01); progression is not assumed monotonic; capability change has meaningful downstream
consequences; Conflict is broader than Combat; defeat/death remain distinct; capability does
not guarantee success; progression can alter world reaction in principle, now with the
generic-vs-individual distinction made explicit; trivial-repeat/unbounded-growth pressure has
been challenged and found genuinely, accidentally unbounded; repository inert/disconnected
progression state is identified; individual trajectory scenarios have been traced, including
two new adversarial probes; genuine Rules remain separated from inherited rules/findings, now
under a stricter reading than the first draft applied.

Do not begin Batch 08 (Objects / Ownership / Resources / Economy) until this batch receives
high-level review.
