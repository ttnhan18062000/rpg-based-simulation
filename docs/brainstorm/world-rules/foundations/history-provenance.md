---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: History / Provenance (scope only — not yet drafted)

**Status.** Introduced 2026-09-21, during Foundational Batch 01's open-question resolution pass
(direct owner instruction, not a `tmp/*-ext-ai.md` file this round). This file **defines scope
only**. It does
not contain numbered rules yet, and drafting them is explicitly out of scope for this task — that
work belongs to a future batch. This file exists so the family has an explicit, citable home
*now*, rather than leaving its load-bearing semantics implicit inside Causality or unnamed
entirely.

**Why now, and why not fully designed now.** `foundations/causality.md`'s CAUSE-05 (causal
history traceable within a declared reach) and CAUSE-06 (compression must not fabricate causal
links; significance may legitimately fade) already carry real semantic weight, confirmed twice —
once by the original batch, once by the adversarial scenario expansion
(`scenarios/foundational-batch-01.md`'s [FND-S20](../scenarios/foundational-batch-01.md#fnd-s20)
and [FND-S21](../scenarios/foundational-batch-01.md#fnd-s21)). That weight is real enough to
warrant a named family rather than staying an unnamed placeholder — but `world-rules/README.md`'s
own stop condition ("do not begin the next foundational batch") still applies to actually
*drafting* this family's rules. Introducing the name and scope is not the same act as drafting
the family, and this task does only the former.

## Scope, at a high level

This family governs: **what may legitimately persist about the past, who is allowed to attest to
it, how it may be compressed without becoming fabrication, and how its prominence may change over
time without that being erasure.** Concretely, in scope:

- **Persistence within a declared reach.** A system is not required to remember everything
  forever, but what it claims to remember must be real, and the boundary of what it remembers
  must be stated rather than silently assumed (CAUSE-05's substance).
- **Provenance.** What it means for a fact, record, or artifact to carry a traceable origin —
  who/what produced it, and through what causal or productive path — distinct from whether that
  origin is currently believed, disputed, or forgotten.
- **Compression semantics.** How detail may be legitimately dropped over time without inventing a
  causal relation that wasn't there or upgrading a correlation into a stated cause (CAUSE-06's
  no-fabrication substance).
- **Significance fading.** How a fact's *prominence* in the world's living memory may legitimately
  diminish over time even while the fact itself remains fully retained and unfabricated — a
  distinct axis from compression (compression reduces stored detail; fading reduces narrative/
  causal weight) and from CAUSE-07's outcome-neutrality (fading is about *record weight* over
  time, not about the *value* of an outcome). This is the piece FND-S21 showed had no mechanism or
  named rule anywhere yet.

**Explicitly out of scope for this family** (stays with later per-domain work, not moved here):

- Chronicle/legend content design, notability, naming, myth/legend distortion, rumour propagation
  — these stay with Perception/knowledge/information, Social relations, and later domain batches;
  this family only states the persistence/provenance/compression/fading constraints those domains
  must obey, never their content or mechanics.
- "Systemic pressure & propagation" (the other half of the design-preparation document's item 19)
  — a separate cross-cutting layer, not covered by this family at all.
- Any specific compression-tier mechanism, decay-rate formula, or fidelity schedule — those are
  implementation decisions for whichever future batch actually drafts this family's rules.

## Relationship to Causality — what stays where

**Do not read this file as moving CAUSE-05 or CAUSE-06 out of `causality.md`.** Nothing in
`causality.md` changed as part of introducing this family; that would reopen an accepted family
without a direct contradiction forcing it, which this task does not have. The distinction, stated
explicitly so a future author doesn't have to re-derive it:

- **Stays in Causality:** the causal-*validity* constraints — that a consequence must trace to a
  real producer (CAUSE-01), that correlation is never sufficient for a causal claim (CAUSE-03),
  that a claimed precondition must be checked against real state (CAUSE-04), and the general
  no-fabrication principle itself (CAUSE-03's four-part test, which CAUSE-06 already restates for
  the compression case).
- **Anticipated to migrate here, once this family is actually drafted:** the *persistence-specific*
  substance currently living inside CAUSE-05 (the declared-reach mechanism itself) and CAUSE-06
  (the compression-tier design and the significance-fading mechanism) — because those are about
  how facts are stored and weighted over time, which is this family's subject, not a causal-
  validity question per se. Until that future drafting happens, CAUSE-05/CAUSE-06 remain the
  authoritative statement of both the causal-validity constraint and its persistence-specific
  instance, and `causality.md` carries a forward-reference note to this file rather than being
  edited to remove that content prematurely.

## Cross-domain links recorded here

- CAUSE-05, CAUSE-06 (`foundations/causality.md`) — the causal-validity constraints this family's
  eventual rules must continue to satisfy once drafted.
- [FND-S04](../scenarios/foundational-batch-01.md#fnd-s04) — Campaign-mode-only reach as an
  honest declared boundary (CAUSE-05's worked case).
- [FND-S20](../scenarios/foundational-batch-01.md#fnd-s20) — real causal effects produced after
  an actor is no longer active, referencing a stable id without granting it present authority.
- [FND-S21](../scenarios/foundational-batch-01.md#fnd-s21) — the counter that motivated this
  family's introduction: no mechanism exists anywhere (`src/domains/chronicle/`,
  `src/domains/fame/legend.py`) to let historical significance legitimately fade.
- Perception/knowledge/information, Social relations & identity — future consumers of this
  family's persistence/provenance constraints for belief, rumour, and reputation content.

## Open questions carried forward

1. When this family is actually drafted (a future batch, not this one), does it get its own
   scenario bank file, or extend `scenarios/foundational-batch-01.md`'s existing FND-S20/S21
   coverage? Not decided here.
2. Whether "Provenance" as used here (fact/record origin-tracing) and "provenance" as already used
   in `identity.md` (a newly-created subject may carry provenance from its causes/predecessors
   without becoming identical to them, ID-04) are the same concept applied at different scales, or
   two related-but-distinct uses of the same word. Flagged for whoever drafts this family, not
   resolved here — reusing a word is not the same as reusing a Rule.
