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
review-export workflow established in Batch 01. Revised once, per
`tmp/world-rule-batch-2-followup-ext-ai.md`, to remove implementation-specific wording from Time,
sharpen Authority's actor-only framing, correct a real internal inconsistency in Reach, and add
four scenario probes — before being frozen as ready for high-level external review.

## Canonical files included

- `foundations/time.md` (TIME-01–07)
- `foundations/authority.md` (AUTH-01–06)
- `foundations/reach.md` (REACH-01–06)
- `scenarios/foundational-batch-02.md` (TAR-S01–S17)

## Rule Inventory

One row per Rule — semantic territory only. Full preconditions, ownership analysis, repository
evidence, and rationale stay in the canonical files linked above.

### Time (`foundations/time.md`)

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| TIME-01 | Temporal Ordering Is Real | The world has a stable temporal ordering/reference for before/after, simultaneity, and elapsed duration — implementation (e.g. a tick counter) is evidence, not the rule. | Accepted, refined |
| TIME-02 | Delayed Consequence Stays Traceable | A cause's consequence may occur later, but must still trace to a real producer. | Accepted |
| TIME-03 | Expiration Must Be Declared | An effect's expiration condition must be a structural, declared boundary, not inferred. | Accepted |
| TIME-04 | Recurrence Is a Continuing Rule, Occurrences Stay Traceable | A repeating process is one standing rule, but each occurrence remains its own distinct, traceable event when causally relevant. | Accepted, refined |
| TIME-05 | Elapsed Time Is a Real Semantic Quantity | Time since a reference point is meaningful to the world; forward-only aging is a later-domain (Life/Body) question, not asserted here. | Accepted, refined |
| TIME-06 | Simultaneity ≠ Causal Connectivity | Two same-tick events are not automatically causally linked. | Accepted |
| TIME-07 | Authoritative Past Facts Aren't Retroactively Rewritten | Scoped to the authoritative fact; belief/knowledge/interpretation/chronicle/significance may still change, and a future declared exception isn't foreclosed. | Accepted, refined |

### Authority (`foundations/authority.md`)

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| AUTH-01 | Authority ≠ Capability | Being able to act and being authorized to act are independent; neither implies the other. | Accepted |
| AUTH-02 | Authority ≠ Ownership | Governing something doesn't require owning it, and owning something doesn't authorize every action on it. | Accepted |
| AUTH-03 | Authority ≠ Knowledge | Correctly believing a transition should occur doesn't authorize causing it. | Accepted |
| AUTH-04 | Authority ≠ Opportunity/Reach | Having the chance to act doesn't authorize the act; Authority and Reach are independent checks. | Accepted |
| AUTH-05 | Content Alone Is Insufficient to Establish Authority | Legitimacy may depend on actor, role, mandate, context, target, or current state — never content alone. | Accepted, refined |
| AUTH-06 | Authority Survives Occupant Change Only While the Role/Mandate Remains Valid | Succession is one possible outcome; the role/mandate ending entirely is another — this rule doesn't assume which. | Accepted, refined |

### Reach (`foundations/reach.md`)

| ID | Short name | One-line semantic purpose | Status |
|---|---|---|---|
| REACH-01 | Reach Is a Precondition for Direct Causal Claims | No reach between producer and consumer means no direct causal attribution. | Accepted |
| REACH-02 | Reach ≠ Physical Distance; Time Is Not a Reach Channel | Reach may exist through space, information, relationships, or institutions — never through time itself; persistence works through a present-existing carrier. | Accepted, refined |
| REACH-03 | Reach May Be Asymmetric | A having reach to B doesn't imply B has reach to A. | Accepted |
| REACH-04 | Historical Relevance ≠ Present Reach | A subject may remain a legitimate historical reference with zero current ability to affect the world. | Accepted |
| REACH-05 | Mediated Reach Means Reach Through Constrainable Intermediary Links | Each link in a mediated chain carries its own constraints/failure modes that can alter the causal path — not primarily a claim about evidentiary confidence. | Accepted, refined |
| REACH-06 | Reach Must Be Declared Per Mechanism | Every reach-constrained mechanism states its own boundary; nothing is globally reachable by default. | Accepted |

## Scenario Inventory

One row per scenario, including the required counter, positive-counterpart, and follow-up
probe scenarios. Full traces stay in `scenarios/foundational-batch-02.md`.

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
| TAR-S14 | Role Ends With Its Holder | leader dies, no eligible successor → clan dissolves rather than role persisting | Authority | Organizations & institutions | Covered |
| TAR-S15 | Same Recurrence, Different Occurrences | node regenerates repeatedly → one specific cycle is the identifiable cause of a threshold being crossed | Time | Economy/resources | Partial |
| TAR-S16 | Past Fact, New Understanding | event occurs → later evidence contradicts a belief about it → belief changes, fact doesn't | Time, Causality | Perception/knowledge/information | Covered |
| TAR-S17 | One-Way Reach | observer perceives target → target has no reciprocal awareness of observer | Reach | Perception/knowledge/information | Covered |

## Coverage Summary

What this batch actually stress-tests — coverage shape, not scenario count.

**Time**
- temporal ordering — TAR-S04
- delayed consequence — TAR-S01
- expiration — TAR-S02
- recurrence, plus individually traceable occurrences — TAR-S03, TAR-S15
- simultaneity without causation — TAR-S05
- fixed authoritative past vs. changeable belief/interpretation — TAR-S13, TAR-S16

**Authority**
- capability vs. authority (both directions) — TAR-S06, TAR-S07
- knowledge vs. authority — TAR-S08
- actor/role/target/state-relative rejection of an otherwise-valid proposal — TAR-S06, TAR-S08
- authorized proposal → committed state — TAR-S09
- role/mandate persists through succession, or ends with no successor — reuses Batch 01's
  FND-S15/S16 for the survives-case; TAR-S14 (new) covers the ends-case

**Reach**
- direct spatial reach and its absence — TAR-S10
- non-spatial (informational, institutional) reach, explicitly not a temporal one — TAR-S11
- declared-reach boundaries generalized beyond Causality — TAR-S12
- historical relevance vs. present reach — TAR-S13
- asymmetry — TAR-S17 (upgraded from read-level evidence to a dedicated scenario)

## Deferred Semantics

An unresolved later-domain question is not the same thing as an incomplete foundational rule —
consistent with Batch 01's own framing:

- Whether *political* authority (Politics/authority & war) inherits AUTH-01–06 unchanged or earns
  its own refinement is explicitly not decided (AUTH-06's own open question, and the roadmap's
  guardrail against automatic unification) — sharpened further by AUTH-06's revision: what makes
  a *political* role/mandate "remain valid" is now an explicit part of that future investigation.
- Whether *spatial* reach or *magical* reach (Space/environment; Magic/supernatural) inherit
  REACH-01–06 unchanged is likewise not decided, per the same guardrail.
- Whether forward-only aging is a Life/Body/Survival law at all, for which subjects, is that
  future batch's own question — no longer treated as an already-settled Time constraint with
  only an open exception question (TIME-05's revision).
- AUTH-02's governance-vs-ownership distinction is deferred to Economy/resources for dense,
  concrete content.
- AUTH-06's role-persistence-through-succession finding (survives-case) reuses Batch 01 evidence
  rather than requiring new Family/lineage or Politics content; those domains still own the
  actual succession law.
- REACH-05's intermediary-link-failure modeling (a messenger delayed, blocked, or lying) is
  confirmed MISSING, not merely unexplored — deferred to whichever future batch (most plausibly
  Perception/knowledge/information) first needs it.
- Whether a future domain will ever define a declared, non-ordinary temporal-alteration
  mechanism (TIME-07's explicitly-left-open possibility) is not decided — flagged for
  Magic/supernatural if that domain's own investigation raises it, not assumed either way.

## Cross-domain findings

- Time ↔ Causality: TIME-02 and TIME-06 are direct restatements of CAUSE-01 and CAUSE-03 at the
  temporal layer specifically — not new ideas, but necessary so a Time-focused author doesn't
  have to re-derive them from Causality.
- Time ↔ History/Provenance: TIME-07's revision explicitly names the same distinction
  History/Provenance's eventual design must respect (fixed authoritative fact vs. legitimately
  changeable belief/interpretation/chronicle/significance) — noted here, not designed here.
- Time ↔ Perception/knowledge/information: TAR-S16 is the first scenario evidence that belief
  contradiction (`apply_contradiction()`) and TIME-07's "fact doesn't change" claim coexist
  correctly — a finding this batch made, that Perception/knowledge will build on.
- Authority ↔ Reach: AUTH-04 is the explicit boundary statement between the two families — Reach
  asks *can this possibly affect that*, Authority asks *is this specific transition legitimate*.
  TAR-S06 is deliberately the single scenario answering both families' probes at once.
- Authority ↔ State Ownership: TAR-S09 shows the same evidence (clan join-acceptance) answering
  both AUTH-05 (multi-factor legitimacy) and OWN-04 (proposal ≠ committed state) — one
  repository mechanism, two independently necessary foundational rules.
- Authority ↔ Identity: AUTH-06's revision and TAR-S14 are the direct counterpart to ID-06
  (split/merge/succession need explicit semantics) from the authority side — both the
  survives-succession and ends-with-no-successor outcomes are now evidenced.
- Reach ↔ Identity/State Ownership/History-Provenance: REACH-04/TAR-S13 is the explicit
  cross-batch check the instruction required — historical fact persistence (ID-05, OWN-06) and
  present reach are confirmed as fully independent facts. REACH-02's revision made this
  consistent with itself, not only with Identity/State Ownership (see "internal consistency
  fix" below).
- Reach ↔ Causality: REACH-06/TAR-S12 generalizes CAUSE-05's declared-reach discipline from
  causal-history retention specifically to reach-constrained mechanisms in general.

**Internal consistency fix (2026-09-21, follow-up pass):** REACH-02's original wording listed
"time" as a reach channel, which was in direct tension with REACH-04's own claim that historical
persistence does not grant present reach. This was caught and corrected — not a new scenario
finding, but a genuine self-consistency repair within the batch, prompted by the follow-up
instruction's request to stop treating time as a generic reach channel.

## Open questions

1. Is a currently-incapacitated role-holder's unaffected authority (TAR-S07) intentional design
   or an unexamined repository gap? Not conclusively verified this batch.
2. Does political authority inherit AUTH-01–06 unchanged, or refine them — and specifically,
   what makes a political role/mandate "remain valid" for AUTH-06's purposes? Deferred to
   Politics/authority & war, per the roadmap's guardrail.
3. Does spatial or magical reach inherit REACH-01–06 unchanged, or refine them? Deferred to
   Space/environment and Magic/supernatural respectively, per the same guardrail.
4. Is forward-only aging a Life/Body/Survival law, and for which subjects? No longer a Time-family
   question with an open exception — it's that future batch's own question from scratch.
5. Does REACH-05 need an actual intermediary-link-failure mechanism designed, and if so, in which
   domain? Confirmed MISSING, not decided where it belongs yet.
6. Will any future domain define a declared, non-ordinary temporal-alteration mechanism
   (TIME-07)? Not decided; not assumed either way.

## Repository evidence

No CONFLICTING or UNKNOWN findings this batch. MISSING-adjacent findings are PARTIAL (TAR-S07,
TAR-S15) or a confirmed-absent mechanism recorded honestly as MISSING (REACH-05's intermediary-
link-failure modeling) rather than left ambiguous. This batch's evidence base remains unusually
clean relative to Batch 01, and the follow-up pass added further precision rather than new gaps:
one internal-consistency issue (REACH-02 vs. REACH-04) was found and fixed, and every revision
either narrowed an over-broad claim to what the repository actually supports (TIME-01, TIME-05,
AUTH-05, AUTH-06, REACH-05) or corrected a real tension (REACH-02) — none required walking back
an already-accepted rule's core claim.

Key evidence, all confirmed by direct code inspection: `src/engine/legality.py`
(`LegalityServiceV2`, `SELF_ATTACK_ILLEGAL`, `FRIENDLY_FIRE_ILLEGAL`, `TARGET_INCAPACITATED`,
`LOS_OBSTRUCTED`, `OUT_OF_RANGE`), `src/core/state.py` (`expires_tick`, `cooldown_remaining`,
`reproduction_cooldowns`, `birth_tick`/`founded_tick`/`dissolved_tick`), `src/ai/life_stage.py`
(`get_stage_for_age`, `is_forward_transition` — now cited as Life/Body-domain evidence, not a
Time-family claim), `src/systems/social_systems/clan_lifecycle.py` (`process_succession`
returning `(None, None)` with no eligible successor, deferring to `process_dissolution`'s
`dissolved_tick`), `src/engine/domain/core_actions.py` (join-request handling), `src/world/
perception/gate.py` (`can_perceive`, one-directional signature, distance falloff), `src/systems/
strategic_systems/belief.py` (`process_observation` vs. `process_rumor` certainty contrast;
`apply_contradiction`'s confidence reduction).

## Owner-attention decisions

- Whether TAR-S07's incapacitated-leader-authority behavior should be confirmed as intentional
  (and documented as such) or treated as a real gap to fix in a future hotfix ticket — this is a
  judgment call about existing repository behavior, not a new design decision, and sits outside
  this design-only session's remit to resolve.
- Whether to pre-register Politics/authority & war's and Space/environment's/Magic/supernatural's
  "inherits vs. refines" questions as standing open items in `roadmap.md` now, or leave them
  implicit until those batches start (current disposition: implicit, per each family's own open
  questions section).
- Whether REACH-05's intermediary-link-failure mechanism is worth prioritizing ahead of its
  "natural" place in the design order, given how many future information-mediated interactions
  (rumor, diplomacy, trade) would benefit from it once built.

## Starter-candidate disposition summary

19 of 19 external candidate concepts (7 Time, 6 Authority, 6 Reach) accepted as drafted Rules — 0
rejected, 0 split, 0 merged, in both the original pass and the follow-up revision pass. No rule
was added locally beyond the external candidate set (unlike Batch 01's ID-08/ID-09). The
follow-up pass refined 8 of the 19 rules (TIME-01, TIME-04, TIME-05, TIME-07, AUTH-05, AUTH-06,
REACH-02, REACH-05 — see Rule Inventory's "Accepted, refined" rows) without rejecting,
splitting, or merging any of them, and added 4 further scenarios (TAR-S14–S17) without
producing any new rejection either. The batch instruction's engine-tick-ordering/
scheduler-execution-order exclusion was carried forward unchanged from Batch 01's precedent
throughout both passes, never re-litigated.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/world-rule-foundational-batch-02-report.md` (local review report, not part of this catalog).

---

> **FOUNDATIONAL BATCH 02 PASS — READY TO FREEZE**

All required artifacts reflect the follow-up revision: three rule-family files (19 rules, 8
refined this pass), one scenario file (17 scenarios: the original 13 plus 4 follow-up probes),
this review export with Rule Inventory, Scenario Inventory, Coverage Summary, Deferred Semantics,
Cross-domain findings, Open questions, Repository evidence, Owner-attention decisions, and the
Starter-candidate disposition, and a local disposition report. No new contradiction appeared —
the one internal-consistency issue found (REACH-02 vs. REACH-04) was a self-correction the
follow-up instruction prompted, not an external contradiction discovered afterward, and it has
been resolved. Per the follow-up instruction: stop before Batch 03.
