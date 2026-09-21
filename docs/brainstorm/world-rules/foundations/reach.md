---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
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

## REACH-02 — Reach is not reducible to physical distance

> Reach may be established through space, time, information, relationships, institutions, or
> (later) magic. A subject with no spatial proximity to a target may still have reach through one
> of these other channels, and a spatially nearby subject may still lack reach if none of these
> channels connect them (see REACH-01's LOS-obstruction case).

**Disposition: ACCEPT.** This is the rule the batch instruction most explicitly required
("do not reduce Reach to physical distance"), and it is directly evidenced by at least three
independent, structurally distinct repository mechanisms.

**Repository evidence: SUPPORTED, across three channels.** *Space:* `LegalityServiceV2`'s
adjacency/occupancy checks. *Perception (a space-plus-senses channel):* `PerceptionGate.
can_perceive()`'s distance-falloff model, distinct from the pure occupancy check. *Information
(a non-spatial channel):* `BeliefCycleSystem.process_rumor()` lets a subject who never
observed an event directly acquire a belief about it, sourced from another entity's report
(`source_entity_id`) rather than proximity to the event itself. *Institution (a further
non-spatial channel):* clan-leader authority (`leader_entity_id`) reaches every member's
join-request evaluation regardless of the leader's spatial position relative to the applicant.

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

**Scenarios:** none yet directly probe asymmetry as its own scenario; the perception evidence
above is read-level, not scenario-traced, this batch. Flagged for the future Perception/knowledge
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

## REACH-05 — Mediated reach differs in kind from direct reach, not just in degree

> Reach established through an intermediary (a report, a rumor, an institution acting on someone's
> behalf) is not simply a weaker version of direct reach — it carries a different evidentiary
> status, and that difference should be visible rather than collapsed.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED.** `process_observation()` (direct) produces a `LeadState` with
`certainty=LeadCertainty.PRECISE` and a `BeliefEntry` with `certainty=1.0`; `process_rumor()`
(mediated) produces the same record *types* but with `certainty=LeadCertainty.VAGUE` and
`certainty=0.3` — the repository already treats mediated reach as categorically different
evidence, not merely a discounted version of direct observation, confirming this rule rather than
requiring it to be newly designed.

**Scenarios:** [TAR-S11](../scenarios/foundational-batch-02.md#tar-s11) (same scenario as
REACH-02 — the rumor-to-distant-leader case is simultaneously the cleanest evidence for "reach
exists" and "mediated reach is evidentially distinct").

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
- REACH-02 → Perception/knowledge/information, Groups/organizations & institutions (information-
  and institution-mediated reach)
- REACH-03 → Perception/knowledge/information (asymmetric detection; future stealth/ambush
  content)
- REACH-04 → Identity (ID-05), State Ownership (OWN-06), History/Provenance
- REACH-05 → Perception/knowledge/information (certainty/evidence-tier design)

## Open questions carried forward

1. REACH-03's asymmetry finding is read-level evidence only, not yet scenario-traced; flagged for
   the Perception/knowledge batch to formally probe rather than resolved here.
2. Whether Politics/authority & war's or Magic/supernatural's own eventual reach concepts
   (diplomatic reach, spell range) inherit REACH-01–06 unchanged or need domain-specific
   refinement is explicitly not decided here, per the roadmap's guardrail against automatically
   unifying foundational and later-domain concepts that share a name.
