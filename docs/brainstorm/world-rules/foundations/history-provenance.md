---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: History / Provenance

**Purpose/scope.** What may legitimately persist about the past, who is allowed to attest to it,
how it may be compressed without becoming fabrication, and how its prominence may change over
time without that being erasure. Named at scope level in Batch 01 (2026-09-21); drafted here as
the Milestone A completion pass `roadmap.md` planned, after Batch 03, before any per-domain
Milestone B batch begins.

**Status.** Milestone A completion pass, first draft. This is the fourth foundational family,
following Identity/State Ownership/Causality (Batch 01) and Time/Authority/Reach (Batch 02) —
not itself numbered as a "Batch," per the roadmap's own framing of this as a completion pass
inside Milestone A rather than an ordinary batch.

**Explicit non-goals, carried forward from the scope-only draft.** Chronicle/legend content
design, notability, naming, myth/legend distortion, rumour propagation — these stay with
Perception/knowledge/information, Social relations, and later domain batches; this family states
only the constraints those domains must obey, never their content. "Systemic pressure &
propagation" is a separate cross-cutting layer, not covered here. No specific compression-tier
mechanism, decay-rate formula, or fidelity schedule is designed here — this family states what
such a mechanism must respect if and when a future batch builds one, not the mechanism itself.

---

## HP-01 — Historical continuity survives ordinary change

> A subject's causal history remains attached to it (or, where ID-03/ID-06 declare a genuine
> successor, to that successor with provenance intact) as it changes form, state, or occupant
> over time. Changing what a subject is does not sever what happened to it.

**Disposition: ACCEPT.** This is the History/Provenance-family restatement of ID-05
(destruction doesn't erase history) and TIME-07 (the past is fixed), stated once more at the
point where a future domain author designing chronicle/biography content would actually look for
it — not a new claim.

**Repository evidence: SUPPORTED**, reusing evidence already established twice:
`LifecycleSystem._transfer_inherited_feud()`/`_seed_dying_wish()` (ID-05, REACH-04) keep a
deceased subject's history causally live; `EvolutionSystem.evaluate()` (ID-02, TIME-01) never
severs an entity's history when its `kind` changes. No new evidence gathered — reuse, not
re-verification.

**Scenarios:** [HP-S01](../scenarios/history-provenance-completion.md#hp-s01).

---

## HP-02 — Provenance requires a real causal ancestor, distinct from truth

> A historically significant fact, record, or artifact should be traceable to what actually
> produced it — a real event, decision, or prior state (CAUSE-01) — and this causal traceability
> is a separate question from whether the fact's *content* is true. A belief, rumour, or
> chronicle entry can have real provenance as an event (something genuinely produced it) while
> the claim it carries is false; provenance tracks the causal ancestor of the record, not the
> correctness of what the record asserts.

**Disposition: ACCEPT.** This sharpens OWN-06 (historical reference ≠ present ownership) and
CAUSE-01 for the specific case of provenance-tracking, and it resolves this family's own
scope-only open question #2: "provenance" here (a record's causal ancestor) and ID-04's
"provenance" (what a newly-created subject carries from its predecessors) are related uses of
the same word at different scales — ID-04's is about a *subject's* lineage; HP-02's is about a
*record's* causal origin — but both share the same underlying shape (a real producer, tracked
without becoming identity or truth).

**Repository evidence: SUPPORTED.** `BeliefEntry`/`LeadState` (reused from Batch 02's REACH-05,
AUTH-03) already carry `source_entity_id`/`source` fields — the record of *who reported this* is
tracked distinctly from `certainty`, the record of *how much to trust it*. A false rumour
(`process_rumor()`) has entirely real provenance (a real source entity, a real tick) while
carrying a false claim — exactly the distinction this rule states.

**Scenarios:** [HP-S02](../scenarios/history-provenance-completion.md#hp-s02).

---

## HP-03 — Persistence is bounded by an honestly declared reach

> A system is not required to remember everything forever, but what it claims to remember must
> be real, and the boundary of what it remembers — by tick range, by mode, by distance, by
> subject — must be stated rather than silently assumed to be universal. This is CAUSE-05's own
> substance, migrated here per that rule's forward-reference note, and REACH-06's generalization
> of the same discipline to reach in general, restated as this family's own governing constraint
> for historical retention specifically.

**Disposition: ACCEPT.** Direct migration of CAUSE-05's persistence-specific content, per the
migration this family's own introduction anticipated. `causality.md`'s CAUSE-05 keeps its
causal-validity core (a causal chain should be reconstructable within its declared reach); this
rule is the History/Provenance-family home for what that declared reach actually looks like as a
retention boundary.

**Repository evidence: SUPPORTED, and this is the clearest instance of a "declared reach" this
whole Catalog has found.** Chronicle/causal-memory retention is Campaign-mode-only — outside
Campaign mode, the same causal chains occur but are not retained at the same fidelity. This
boundary is stated by the mode itself (a real, inspectable configuration), not silently assumed;
CAUSE-05's own scenario (FND-S04) already confirmed this.

**Scenarios:** reuses [FND-S04](../scenarios/foundational-batch-01.md#fnd-s04) directly — no new
trace needed, since the underlying evidence and finding are unchanged by migrating the rule's
canonical home.

---

## HP-04 — Compression may drop detail but must never fabricate a causal link

> When history, memory, or chronicles compress detail over time or distance from origin, the
> compression may drop detail but must not invent a causal relation that wasn't there, and must
> not silently upgrade a correlation into a stated cause. This is CAUSE-06's no-fabrication
> substance, migrated here as this family's own governing constraint on compression specifically.

**Disposition: ACCEPT.** Direct migration of CAUSE-06's no-fabrication clause. `causality.md`'s
CAUSE-06 keeps only a forward-reference to this family now that the migration is complete; the
actual constraint on compression lives here.

**Repository evidence: MISSING, honestly — no compression-tier mechanism exists anywhere in this
repository.** This was true when CAUSE-06 first stated the constraint, and remains true now that
the constraint has migrated to its proper family: there is nothing to check compression *against*
yet. The constraint itself is nonetheless stated now, ready for whichever future mechanism is
built to be checked against it, rather than being retrofitted after the fact.

**Scenarios:** none newly traced; reuses [FND-S20](../scenarios/foundational-batch-01.md#fnd-s20)
as evidence of the underlying real-causal-chain-after-death pattern compression would eventually
need to preserve, not as evidence of compression itself.

---

## HP-05 — Significance may legitimately fade, distinct from erasure or fabrication

> A fact's *prominence* in the world's living memory may legitimately diminish over time even
> while the fact itself remains fully retained and unfabricated. Fading significance is not
> erasure (which would violate HP-01/ID-05), not fabrication (which would violate HP-04/CAUSE-06),
> and not a claim about the value of an outcome (CAUSE-07's outcome-neutrality, a different axis
> entirely) — it is a distinct, legitimate kind of change: the same underlying fact, weighted
> less prominently in what the world's own inhabitants and institutions currently treat as
> significant.

**Disposition: ACCEPT.** Direct migration of CAUSE-06's fading-significance clause (added
2026-09-21 during Batch 01's adversarial expansion, per FND-S21). This is the rule whose absence
of a mechanism motivated this whole family's introduction in the first place.

**Repository evidence: MISSING, confirmed directly and unchanged since FND-S21 first found it.**
No importance-decay mechanism exists anywhere in `src/domains/chronicle/` or
`src/domains/fame/legend.py` — every recorded fact stays at constant significance once created,
within whatever reach HP-03 already declares. Stating the rule now, ahead of the mechanism,
follows the same discipline HP-04 does: the constraint exists so the eventual mechanism has
something real to be checked against.

**Scenarios:** reuses [FND-S21](../scenarios/foundational-batch-01.md#fnd-s21) directly — the
scenario that originally surfaced this gap remains the evidence base; migrating the rule's
canonical home does not require re-tracing it.

---

## HP-06 — A historical record's existence never grants present authority, reach, or truth

> Referencing, chronicling, or remembering a past fact does not make the record's source
> authoritative over present state (OWN-06), does not grant the referenced subject present reach
> (REACH-04), and does not make the record's content true merely because it persists (OWN-04).
> This rule adds nothing new to any of the three — it exists so a future History/Provenance
> content author (chronicles, legends, biographies) encounters the combined constraint once, in
> the family whose content they are actually building, rather than having to separately
> remember three other families' rules.

**Disposition: ACCEPT, by explicit consolidation rather than new claim.** Deliberately
structured like TRANS-03's deference to ID-03 — this rule's entire content is "these three
constraints apply together, here," not an independent finding.

**Repository evidence:** none newly gathered — reuses OWN-06, REACH-04, and OWN-04's own
evidence directly.

**Scenarios:** reuses [FND-S04](../scenarios/foundational-batch-01.md#fnd-s04),
[FND-S13](../scenarios/foundational-batch-02.md#tar-s13) (historical actor without present
reach), and [FND-S09](../scenarios/foundational-batch-01.md#fnd-s09) (belief never becomes
committed truth) — no new trace needed.

---

## Cross-domain links recorded here

- HP-01 → Identity (ID-05, ID-03/ID-06 succession cases), Time (TIME-07)
- HP-02 → Causality (CAUSE-01), Identity (ID-04's own use of "provenance," now explicitly
  distinguished at a different scale), Perception/knowledge/information (belief/lead provenance
  content)
- HP-03 → Causality (CAUSE-05, migrated from), Reach (REACH-06, the generalized discipline this
  rule instantiates for retention specifically)
- HP-04, HP-05 → Causality (CAUSE-06, migrated from), Perception/knowledge/information, Social
  relations & identity (future chronicle/legend/reputation content built on top of these
  constraints)
- HP-06 → State Ownership (OWN-04, OWN-06), Reach (REACH-04) — consolidation, not a new link

## Open questions carried forward

1. **Resolved.** The scope-only draft's open question #2 (is HP-02's "provenance" the same
   concept as ID-04's?) is answered above: related uses of the same word at different scales
   (record-causal-ancestor vs. subject-lineage), not the same Rule reused twice.
2. This family's own scenario bank file (`scenarios/history-provenance-completion.md`) is new
   and small (HP-S01/HP-S02 only) — HP-01, HP-03–06 all reuse existing Batch 01/02 scenarios
   directly rather than requiring fresh traces, since migrating a rule's canonical home does not
   invalidate the evidence already gathered for it.
3. HP-04/HP-05's compression-tier mechanism and significance-fading mechanism remain undesigned
   — this completion pass drafts the constraints they must obey, not the mechanisms themselves,
   per this family's own stated non-goal. Deferred to whichever future need (most plausibly
   Perception/knowledge/information or a later dedicated pass) first requires building one.
4. Whether Batch 04 (Space/Environment/Movement, next) will need its own History/Provenance
   touchpoint (e.g., "historical location significance" per that batch's own framing) is not
   pre-decided here — that batch's own investigation should cite this family rather than assume
   a link exists in advance.
