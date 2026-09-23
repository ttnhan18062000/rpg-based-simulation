---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# World Rule Family: Reach

**Purpose/scope.** Under what conditions one subject, process, or state can meaningfully affect
another — as a precondition for a valid causal claim, distinct from whether that effect would
also be *authorized* (see `authority.md`). Reach is not reducible to physical distance: it may be
established or constrained through space, time, information, relationships, institutions, or
(later) magic. Domain-specific reach rules (spatial reach, political reach, magical reach, etc.)
remain for later batches; this family states only the foundational shape.

**Status.** Foundational Batch 02, first draft. Candidates below originated as external-reviewer
hypotheses (`tmp/world-rule-batch-2-ext-ai.md`); each carries this session's disposition and
repository evidence, not the original wording uncritically kept.

---

## REACH-01 — Reach is a precondition for a valid direct causal claim

> If no reach exists between a producer and a consumer, no direct causal effect between them
> should be attributed. This is the Reach-family instance of CAUSE-01's real-causal-path
> requirement, made explicit for the specific case where the missing ingredient is reach.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED.** `LegalityServiceV2.verify_occupancy`/`is_adjacent`/
`get_manhattan_dist` and the `OUT_OF_RANGE`/`LOS_OBSTRUCTED` reason codes exist specifically to
reject an attempted direct effect between two subjects that lack the necessary spatial reach —
the rejection is structural, not merely narrative.

**Scenarios:** [TAR-S10](../scenarios/foundational-batch-02.md#tar-s10).

---

## REACH-02 — Reach is not reducible to physical distance, and time is not itself a reach channel

> Reach may be established through space, information, relationships, institutions, or (later)
> magic. A subject with no spatial proximity to a target may still have reach through one of
> these other channels, and a spatially nearby subject may still lack reach if none of these
> channels connect them (see REACH-01's LOS-obstruction case).
>
> Temporal separation is *not* itself a reach channel. A past entity's consequences may persist
> and continue to matter (see REACH-04, History/Provenance), but that persistence is always
> carried forward through something that presently exists — persistent state, history,
> information, an institution, or a mediated causal chain — never through the entity itself
> somehow "reaching through time." Reach is always exercised in a real present, by something that
> currently exists to exercise it.

**Disposition: ACCEPT, refined 2026-09-21 — "time" removed from the channel list.** The original
list of channels included "time" alongside space/information/relationships/institutions/magic.
That was a real internal inconsistency, not just loose wording: REACH-04 (below) already
established that a historical actor does *not* retain present reach merely because its
consequences persist — treating time as a reach channel in its own right would contradict that.
The fix keeps every other channel and adds the explicit clarification that temporal persistence
works *through* a present-existing carrier (state, history, information, institution, chain),
never as reach exercised directly by something no longer present.

**Repository evidence: SUPPORTED, across the remaining channels, plus the correction itself
confirmed.** *Space:* `LegalityServiceV2`'s adjacency/occupancy checks. *Perception (a
space-plus-senses channel):* `PerceptionGate.can_perceive()`'s distance-falloff model, distinct
from the pure occupancy check. *Information (a non-spatial channel):* `BeliefCycleSystem.
process_rumor()` lets a subject who never observed an event directly acquire a belief about it,
sourced from another entity's report (`source_entity_id`) rather than proximity to the event
itself. *Institution (a further non-spatial channel):* clan-leader authority (`leader_entity_id`)
reaches every member's join-request evaluation regardless of the leader's spatial position
relative to the applicant. *The correction itself:* `_transfer_inherited_feud()` (REACH-04's own
evidence) confirms the "carried forward by a present carrier" model directly — the dead
antagonist's own reach is zero; only the living heir, a presently-existing carrier, has any.

**Scenarios:** [TAR-S11](../scenarios/foundational-batch-02.md#tar-s11).

---

## REACH-03 — Reach may be asymmetric

> Subject A having reach to affect subject B does not imply subject B has reach to affect subject
> A. Reach is a directed relationship, not automatically mutual.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED.** `PerceptionGate.can_perceive()` computes source→target
detection as a one-directional query — nothing in its signature or return value implies or
computes the reciprocal target→source detection, which is exactly what makes stealth/ambush
mechanically coherent: A perceiving B does not entail B perceiving A.

**Scenarios:** [TAR-S17](../scenarios/foundational-batch-02.md#tar-s17) (added 2026-09-21 — a
dedicated scenario trace, upgrading this rule's evidence from read-level only). Formal
domain-specific stealth/ambush content is still flagged for the future Perception/knowledge
batch.

---

## REACH-04 — Historical relevance does not imply present reach

> A subject may remain a legitimate, causally-relevant historical reference (per ID-05/OWN-06)
> without retaining any present ability to affect the world. Persisting in history and possessing
> current reach are independent facts.

**Disposition: ACCEPT.** This is the explicit cross-batch check the instruction required
("historical fact persists ≠ historical actor still has present reach"), and it is one of the
cleanest-evidenced rules in this batch.

**Repository evidence: SUPPORTED.** `LifecycleSystem._transfer_inherited_feud()` keeps the
deceased antagonist's identity present in a real, causally-active record (`inherited_nemesis_
{antagonist}`) — the historical fact of who the rival was remains fully legitimate and
consequential — while the deceased entity itself performs no action whatsoever; every actual
effect from that point forward is carried out by the living heir, who has real present reach. The
two facts (historical relevance, present reach) are tracked by entirely different mechanisms and
never conflated.

**Scenarios:** [TAR-S13](../scenarios/foundational-batch-02.md#tar-s13).

---

## REACH-05 — Mediated reach means reach through explicit intermediary links, each with its own constraints and failure modes

> Reach established through an intermediary — a messenger, a report, an institution acting on
> someone's behalf — is reach established through one or more explicit intermediary links, not a
> direct connection. Each link in that chain carries its own constraints and possible failure
> modes (a messenger may be delayed, blocked, or lie; an institution may misrepresent or fail to
> relay), and any such failure can alter the resulting causal path. This is what distinguishes
> mediated reach from direct reach as a matter of world semantics.

**Disposition: ACCEPT, refined 2026-09-21 — recentred from "evidentiary status" to "the
intermediary link itself is a real, constrainable part of the causal path."** The original
wording made how confident an observer *should be* in mediated information the core of the rule.
That is a real and correct downstream fact, but it belongs to Perception/Knowledge (how certainty
is assigned and used), not to Reach's own foundational claim. Reach's job is narrower and more
structural: mediated reach exists *through* one or more intermediary links, and those links are
themselves part of the causal path — capable of failing, being delayed, or distorting what
passes through them — which is what makes mediated reach a different *kind* of reach, not merely
a weaker one.

**Repository evidence: SUPPORTED for the reach-exists-through-a-link claim; MISSING for
intermediary-failure modeling specifically.** `process_rumor()` establishes mediated reach exists
as a real, distinct mechanism from direct observation — `certainty=LeadCertainty.VAGUE`/`0.3` vs.
`process_observation()`'s `PRECISE`/`1.0` confirms the repository already treats mediated reach
differently (now understood as a downstream *consequence* of the link existing, per this
revision, not the rule's own definition). Checked directly: no mechanism currently models a
messenger's own failure modes (a rumor being lost, distorted in transit, or deliberately falsified
by the intermediary rather than the original source) as a distinct causal event in its own right
— `process_rumor()` takes `rumor_detail` directly from `source_entity_id` with no intermediary-
link step modeled at all. This is a real, honestly-recorded gap, not a violation of the rule,
which only asserts such failure modes *would be* legitimate causal events if built.

**Scenarios:** [TAR-S11](../scenarios/foundational-batch-02.md#tar-s11) (same scenario as
REACH-02 — the rumor-to-distant-leader case establishes mediated reach exists; it does not probe
intermediary-link failure, which remains unmodeled).

---

## REACH-06 — Reach must be declared per mechanism, not assumed universal

> Every reach-constrained mechanism must state its own reach boundary explicitly; nothing should
> silently assume a subject's influence or perception is global by default.

**Disposition: ACCEPT strongly.** This generalises CAUSE-05's "declared reach" concept (stated
there for causal-history retention specifically) into the Reach family's own governing principle
— the same discipline CAUSE-05 already required for memory now applies to reach in general.

**Repository evidence: SUPPORTED, by the same pattern CAUSE-05 already found.** `PerceptionGate`'s
distance-falloff model is one concrete declared-reach boundary; CAUSE-05's Campaign-mode-only
chronicle reach is another instance of the exact same underlying discipline, restated here as a
Reach-family principle rather than only a Causality/History-Provenance one.

**Scenarios:** [TAR-S12](../scenarios/foundational-batch-02.md#tar-s12).

---

## Cross-domain links recorded here

- REACH-01, REACH-06 → Causality (CAUSE-01, CAUSE-05), History/Provenance (declared-reach
  boundaries generalised)
- REACH-02 → Perception/knowledge/information, Groups/organizations & institutions
  (information- and institution-mediated reach), History/Provenance (the "carried forward by a
  present carrier" boundary against REACH-04)
- REACH-03 → Perception/knowledge/information (asymmetric detection; future stealth/ambush
  content)
- REACH-04 → Identity (ID-05), State Ownership (OWN-06), History/Provenance
- REACH-05 → Perception/knowledge/information (this is now explicitly *where* certainty/
  evidence-tier design belongs, having been recentred out of REACH-05 itself)

## Open questions carried forward

1. **Upgraded 2026-09-21.** REACH-03's asymmetry finding now has a dedicated scenario
   (TAR-S17), no longer read-level evidence only. Formal domain-specific stealth/ambush content
   remains flagged for the Perception/knowledge batch.
2. Whether Politics/authority & war's or Magic/supernatural's own eventual reach concepts
   (diplomatic reach, spell range) inherit REACH-01–06 unchanged or need domain-specific
   refinement is explicitly not decided here, per the roadmap's guardrail against automatically
   unifying foundational and later-domain concepts that share a name.
3. **Added 2026-09-21.** REACH-05's intermediary-link-failure modeling (a messenger being
   delayed, blocked, or lying; an institution misrepresenting a relay) is a confirmed MISSING
   mechanism, not merely unexplored — flagged for whichever future batch (most plausibly
   Perception/knowledge/information) first needs to model a mediated reach failure as its own
   causal event.
