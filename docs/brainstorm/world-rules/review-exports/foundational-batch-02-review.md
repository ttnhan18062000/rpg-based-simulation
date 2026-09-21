---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Review Export: Foundational Batch 02 (Time / Authority / Reach)

**This file is a generated, non-authoritative review view.** It exists so an external reviewer
can assess the batch without opening every canonical file. It is never edited directly as the fix
for a review finding — feedback goes back into the canonical files below, and this export is
regenerated from them. See `world-rules/README.md`'s review index for the current status of
every batch.

## Batch scope

Three foundational law families — Time, Authority, Reach — following directly on Batch 01
(Identity, State Ownership, Causality). Not a per-domain batch; deliberately domain-agnostic.
Drafted per `tmp/world-rule-batch-2-ext-ai.md`, using the same canonical-file + Scenario Bank +
review-export workflow established in Batch 01.

## Canonical files included

- `foundations/time.md` (TIME-01–07)
- `foundations/authority.md` (AUTH-01–06)
- `foundations/reach.md` (REACH-01–06)
- `scenarios/foundational-batch-02.md` (TAR-S01–S13)

## Rule Inventory

One row per Rule — semantic territory only. Full preconditions, ownership analysis, repository
evidence, and rationale stay in the canonical files linked above.

### Time (`foundations/time.md`)

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| TIME-01 | Temporal Ordering Is Real | The world has one stable, monotonic tick counter; before/after relationships don't change once recorded. | Accepted |
| TIME-02 | Delayed Consequence Stays Traceable | A cause's consequence may occur later, but must still trace to a real producer. | Accepted |
| TIME-03 | Expiration Must Be Declared | An effect's expiration condition must be a structural, declared boundary, not inferred. | Accepted |
| TIME-04 | Recurrence Is a Continuing Rule | A repeating process is one standing rule re-evaluated over time, not a fresh causal chain each cycle. | Accepted |
| TIME-05 | Elapsed Time Is Derived; Aging Is Forward-Only | Age is computed from tick difference, not stored; life-stage progression never runs backward for a subject. | Accepted |
| TIME-06 | Simultaneity ≠ Causal Connectivity | Two same-tick events are not automatically causally linked. | Accepted |
| TIME-07 | The Past Is Fixed | Once committed, a tick's facts do not change; later ticks build on them, never rewrite them. | Accepted |

### Authority (`foundations/authority.md`)

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| AUTH-01 | Authority ≠ Capability | Being able to act and being authorized to act are independent; neither implies the other. | Accepted |
| AUTH-02 | Authority ≠ Ownership | Governing something doesn't require owning it, and owning something doesn't authorize every action on it. | Accepted |
| AUTH-03 | Authority ≠ Knowledge | Correctly believing a transition should occur doesn't authorize causing it. | Accepted |
| AUTH-04 | Authority ≠ Opportunity/Reach | Having the chance to act doesn't authorize the act; Authority and Reach are independent checks. | Accepted |
| AUTH-05 | Unauthorized Proposal Rejected Regardless of Content | The same proposal is legitimate or not based on the actor, not the content alone. | Accepted |
| AUTH-06 | Authority Persists Through Occupant Change | Role-held authority survives succession; only its holder changes. | Accepted |

### Reach (`foundations/reach.md`)

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| REACH-01 | Reach Is a Precondition for Direct Causal Claims | No reach between producer and consumer means no direct causal attribution. | Accepted |
| REACH-02 | Reach ≠ Physical Distance | Reach may exist through space, time, information, relationships, or institutions, not distance alone. | Accepted |
| REACH-03 | Reach May Be Asymmetric | A having reach to B doesn't imply B has reach to A. | Accepted |
| REACH-04 | Historical Relevance ≠ Present Reach | A subject may remain a legitimate historical reference with zero current ability to affect the world. | Accepted |
| REACH-05 | Mediated Reach Differs in Kind, Not Just Degree | Reach through an intermediary carries different evidentiary status than direct reach. | Accepted |
| REACH-06 | Reach Must Be Declared Per Mechanism | Every reach-constrained mechanism states its own boundary; nothing is globally reachable by default. | Accepted |

## Scenario Inventory

One row per scenario, including the required counter and positive-counterpart scenarios. Full
traces stay in `scenarios/foundational-batch-02.md`.

| Scenario ID | Short name | Trajectory (initial → consequence) | Rule families challenged | Deferred domain dependencies | Result |
|---|---|---|---|---|---|
| TAR-S01 | The Dying Wish, Resolved Much Later | death → inherited hostility seeded → heir encounters antagonist much later | Time, Causality | Family/lineage, Politics | Covered |
| TAR-S02 | A Cooldown Quietly Ends | skill used → cooldown set → cooldown expires → skill usable again | Time | Capability/progression | Covered |
| TAR-S03 | The Node Regrows | node harvested → charges depleted → charges regenerate on a recurring rule | Time | Economy/resources | Covered |
| TAR-S04 | Founded Before, Dissolved After | clan founded → (time passes) → clan dissolved | Time | Organizations & institutions | Covered |
| TAR-S05 | Two Unrelated Things, Same Tick (counter) | entity ages into adulthood ↔ unrelated distant calamity, same tick | Time, Causality | none | Covered |
| TAR-S06 | Friendly Fire, Refused | capable + in-range attack proposed against an ally → refused | Authority | Conflict & combat | Covered |
| TAR-S07 | A Leader Who Cannot Currently Act | wounded/cooling-down clan leader retains full join-request authority | Authority | Organizations & institutions | Partial |
| TAR-S08 | Wrong Actor, Same Proposal, Rejected | identical attack proposal → accepted vs. hostile target, rejected vs. ally | Authority | Conflict & combat | Covered |
| TAR-S09 | Authorized Proposal Becomes Real | leader accepts join → contract accepted → membership committed via apply pipeline | Authority, State Ownership | Organizations & institutions | Covered |
| TAR-S10 | Adjacent, but Blocked | two entities adjacent → line-of-sight obstructed → no direct effect | Reach | Space & environment | Covered |
| TAR-S11 | A Rumor Reaches a Distant Leader | distant witness observes → rumor → leader informed, never spatially close | Reach | Perception/knowledge, Organizations | Covered |
| TAR-S12 | An Event Outside the Declared Reach | causal chain occurs outside Campaign mode → later query cannot treat it as recorded | Reach, Causality | History/Provenance | Covered |
| TAR-S13 | A Dead Rival, Still Explaining Present Hostility | antagonist dies → feud inherited → deceased never acts again, heir does | Reach, Identity, State Ownership, Time | Family/lineage, History/Provenance | Covered |

## Coverage Summary

What this batch actually stress-tests — coverage shape, not scenario count.

**Time**
- temporal ordering — TAR-S04
- delayed consequence — TAR-S01
- expiration — TAR-S02
- recurrence — TAR-S03
- simultaneity without causation — TAR-S05
- fixed past / historical actor without present reach — TAR-S13

**Authority**
- capability vs. authority (both directions) — TAR-S06, TAR-S07
- knowledge vs. authority — TAR-S08
- actor-relative rejection of an otherwise-valid proposal — TAR-S06, TAR-S08
- authorized proposal → committed state — TAR-S09
- role-persistence through succession — reuses Batch 01's FND-S15/S16 evidence, not newly traced

**Reach**
- direct spatial reach and its absence — TAR-S10
- non-spatial (informational, institutional) reach — TAR-S11
- declared-reach boundaries generalized beyond Causality — TAR-S12
- historical relevance vs. present reach — TAR-S13
- asymmetry — evidenced at the read level (`reach.md`), not yet scenario-traced this batch

## Deferred Semantics

An unresolved later-domain question is not the same thing as an incomplete foundational rule —
consistent with Batch 01's own framing:

- Whether *political* authority (Politics/authority & war) inherits AUTH-01–06 unchanged or earns
  its own refinement is explicitly not decided (AUTH-06's own open question, and the roadmap's
  guardrail against automatic unification).
- Whether *spatial* reach or *magical* reach (Space/environment; Magic/supernatural) inherit
  REACH-01–06 unchanged is likewise not decided, per the same guardrail.
- REACH-03's asymmetry finding is deferred to the Perception/knowledge batch for a formal
  scenario probe — this batch only found it at the read/evidence level.
- TIME-05's forward-only aging constraint may need an explicit exception mechanism for Magic/
  supernatural (age reversal); not decided here.
- AUTH-02's governance-vs-ownership distinction is deferred to Economy/resources for dense,
  concrete content.
- AUTH-06's role-persistence-through-succession finding reuses Batch 01 evidence rather than
  requiring new Family/lineage or Politics content; those domains still own the actual succession
  law.

## Cross-domain findings

- Time ↔ Causality: TIME-02 and TIME-06 are direct restatements of CAUSE-01 and CAUSE-03 at the
  temporal layer specifically — not new ideas, but necessary so a Time-focused author doesn't
  have to re-derive them from Causality.
- Time ↔ History/Provenance: TIME-07 ("the past is fixed") is the same immutability law
  History/Provenance's eventual compression/fading design must respect — noted here, not
  designed here.
- Authority ↔ Reach: AUTH-04 is the explicit boundary statement between the two families — Reach
  asks *can this possibly affect that*, Authority asks *is this specific transition legitimate*.
  TAR-S06 is deliberately the single scenario answering both families' probes at once.
- Authority ↔ State Ownership: TAR-S09 shows the same evidence (clan join-acceptance) answering
  both AUTH-05 (actor-relative legitimacy) and OWN-04 (proposal ≠ committed state) — one
  repository mechanism, two independently necessary foundational rules.
- Reach ↔ Identity/State Ownership/History-Provenance: REACH-04/TAR-S13 is the explicit
  cross-batch check the instruction required — historical fact persistence (ID-05, OWN-06) and
  present reach are confirmed as fully independent facts.
- Reach ↔ Causality: REACH-06/TAR-S12 generalizes CAUSE-05's declared-reach discipline from
  causal-history retention specifically to reach-constrained mechanisms in general.

## Open questions

1. Is a currently-incapacitated role-holder's unaffected authority (TAR-S07) intentional design
   or an unexamined repository gap? Not conclusively verified this batch.
2. Does political authority inherit AUTH-01–06 unchanged, or refine them? Deferred to Politics/
   authority & war, per the roadmap's guardrail.
3. Does spatial or magical reach inherit REACH-01–06 unchanged, or refine them? Deferred to
   Space/environment and Magic/supernatural respectively, per the same guardrail.
4. Does aging need an explicit reversal-exception mechanism (TIME-05)? Deferred to Magic/
   supernatural.
5. Is REACH-03's asymmetry finding sufficient at read-level evidence, or does it need its own
   scenario trace before Perception/knowledge can build on it? Flagged, not resolved.

## Repository evidence

No CONFLICTING or UNKNOWN findings this batch. All MISSING-adjacent findings are actually PARTIAL
(TAR-S07) or explicit open questions rather than confirmed gaps — this batch's evidence base
turned out unusually clean relative to Batch 01, likely because Time/Authority/Reach map onto
already-mature, heavily-tested repository subsystems (combat legality, lifecycle, belief) rather
than the largely-unbuilt domains (Organizations, Places) Batch 01's gaps concentrated in. Key
evidence, all confirmed by direct code inspection: `src/engine/legality.py` (`LegalityServiceV2`,
`SELF_ATTACK_ILLEGAL`, `FRIENDLY_FIRE_ILLEGAL`, `LOS_OBSTRUCTED`, `OUT_OF_RANGE`), `src/core/
state.py` (`expires_tick`, `cooldown_remaining`, `reproduction_cooldowns`, `birth_tick`/
`founded_tick`/`dissolved_tick`), `src/ai/life_stage.py` (`get_stage_for_age`,
`is_forward_transition`), `src/systems/social_systems/clan_lifecycle.py`
(`process_succession`, `leader_entity_id_set`), `src/engine/domain/core_actions.py` (join-request
handling), `src/world/perception/gate.py` (`can_perceive`, distance falloff), `src/systems/
strategic_systems/belief.py` (`process_observation` vs. `process_rumor` certainty contrast).

## Owner-attention decisions

- Whether TAR-S07's incapacitated-leader-authority behavior should be confirmed as intentional
  (and documented as such) or treated as a real gap to fix in a future hotfix ticket — this is a
  judgment call about existing repository behavior, not a new design decision, and sits outside
  this design-only session's remit to resolve.
- Whether to pre-register Politics/authority & war's and Space/environment's/Magic/supernatural's
  "inherits vs. refines" questions as standing open items in `roadmap.md` now, or leave them
  implicit until those batches start (current disposition: implicit, per each family's own open
  questions section).

## Starter-candidate disposition summary

19 of 19 external candidate concepts (7 Time, 6 Authority, 6 Reach) accepted as drafted Rules — 0
rejected, 0 split, 0 merged. No rule was added locally beyond the external candidate set this
batch (unlike Batch 01's ID-08/ID-09) — the starter hypotheses, once traced against repository
evidence, were judged complete for a first foundational draft. No rule was rejected as an
implementation concern this batch either, though the batch instruction's own exclusion (engine
tick ordering/scheduler execution order) was carried forward unchanged from Batch 01's precedent
rather than re-litigated.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/world-rule-foundational-batch-02-report.md` (local review report, not part of this catalog).

---

> **FOUNDATIONAL BATCH 02 READY FOR HIGH-LEVEL EXTERNAL REVIEW.**

All required artifacts exist: three rule-family files (19 rules total), one scenario file (13
scenarios covering all 11 required probes plus 1 required counter and 1 required positive
counterpart), this review export with Rule Inventory, Scenario Inventory, Coverage Summary,
Deferred Semantics, Cross-domain findings, Open questions, Repository evidence, and Owner-
attention decisions, and a local disposition report. No contradiction was found against Batch 01
or within this batch. Per the batch instruction: do not begin Batch 03 until this batch is
reviewed.
