---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Scenario Bank: Foundational Batch 01

**Purpose/scope.** Twelve seed scenarios used to pressure-test the Identity, State Ownership, and
Causality rule families in `foundations/identity.md`, `foundations/state-ownership.md`, and
`foundations/causality.md`. Five of the twelve are the required counter-scenarios (marked
**COUNTER** below) per the batch-01 instruction's own requirement: a transformation that *should*
create new identity, a state change that should *not* persist historically, two similar facts with
legitimately different state owners, two correlated-but-not-causal events, and an aggregate change
that should not affect every individual member.

Each scenario is scored **covered** / **partially covered** / **blocked** / **revealed missing
rule** / **revealed contradiction** against current repository behavior, not against the ideal
design — a partial or blocked result documents a real gap, it is not a failure of the scenario.

---

## FND-S01 — The dead don't fight back

A defeated entity's corpse is looted. The looting action is narratively gated on "the corpse
cannot resist" — a precondition claim.

- **Rules invoked:** ID-05 (destruction doesn't erase history), CAUSE-01 (real causal path),
  CAUSE-04 (preconditions must be real, not narrative).
- **Result: partially covered.** The corpse-as-object distinction is real and SUPPORTED
  (`CorpseState`); the "cannot resist" precondition, however, is not checked against any general
  capability gate — it works here only because no combat system currently allows corpses to act,
  not because a precondition check exists. This is the concrete instance of CAUSE-04's PARTIAL
  finding, not a separate gap.

## FND-S02 — Ingots become a sword (COUNTER: transformation that should create new identity)

Raw ore is smelted into ingots, then forged into a sword. Unlike ID-03's default (transformation
preserves identity), a crafted end product should **not** be treated as the same identity as its
consumed inputs.

- **Rules invoked:** ID-03 (transformation preserves continuity **by default** — this scenario is
  the deliberate exception case the rule itself anticipates).
- **Result: covered.** Crafting consumes input item records and creates a new output item record;
  there is no continuity claim anywhere in the crafting path, and none should exist. This confirms
  ID-03's default/exception split is the right shape: continuity is the default only where nothing
  overrides it, and crafting is a legitimate, already-correctly-behaving override.

## FND-S03 — Camp, settlement, ruin

A camp grows into a settlement, and the settlement later collapses into a ruin.

- **Rules invoked:** ID-03 (transformation preserves continuity by default).
- **Result: blocked.** No mechanism currently tracks a place through this lifecycle at all — the
  question of whether the ruin is "the same place" as the settlement can't yet be answered because
  neither transition exists in code. Recorded as deliberately deferred to the future Places domain
  in `identity.md`'s ID-03 entry, not resolved here.

## FND-S04 — The chronicle remembers what the world doesn't

A chronicle entry, written in Campaign mode, records that "the mill was built by hand." Outside
Campaign mode, the same causal detail is not retained at the same fidelity.

- **Rules invoked:** OWN-06 (historical reference doesn't imply present ownership), CAUSE-05
  (causal history traceable within declared reach).
- **Result: partially covered.** Both rules hold exactly as declared: the chronicle never becomes
  an authoritative owner of the mill's construction fact, and the reach limitation (Campaign-mode
  only) is a real, honestly-declared boundary rather than a silent gap — the chronicle system
  doesn't claim fidelity it doesn't have.

## FND-S05 — Feared and hated are not the same field (COUNTER: two similar facts, legitimately different owners)

An entity is both widely feared (`public_reputation` scalar, low) and specifically labeled
"oathbreaker" (`PublicReputationProfile.labels`). These read as "the same kind of fact" on the
surface but are two independently owned authoritative fields.

- **Rules invoked:** OWN-03 (derived views are not duplicate truth — used here as the boundary
  case, since these two fields are the counter-example: neither is derived from the other, both
  are genuinely owned).
- **Result: revealed missing rule.** This is not a bug, but it is an undocumented seam: nothing in
  the Social relations domain currently declares how these two owned fields are meant to relate to
  each other in player/AI-facing narration (they can drift apart — e.g. a well-labeled "honorable"
  entity with catastrophic `public_reputation`, or the reverse). Flagged for the Social relations
  batch to formally resolve, not resolved here — this batch's job was only to confirm the two
  fields are legitimately separate owners, which they are.

## FND-S06 — A famine doesn't rewrite every name (COUNTER: aggregate change should not affect every individual)

A regional famine shifts population-level demographic aggregates. It must not silently overwrite
every named entity's individual state in that region, and it must not be treated as equivalent to
founding or splitting a named organization.

- **Rules invoked:** ID-07 (aggregate membership doesn't erase individual identity), ID-04
  (creation establishes identity — checked here for organizations specifically), ID-06
  (split/merge/succession need explicit semantics — checked here for clans/factions specifically).
- **Result: mixed.** The core counter-scenario is **covered**: demographic-cohort state and named-
  entity state are architecturally separate, so an aggregate shift genuinely cannot leak into named
  entities' own records. But probing the same scenario for organization-founding and clan-splitting
  triggers by the famine surfaces two confirmed **revealed missing rule** findings already logged
  in `identity.md`: no organization/settlement creation-establishes-identity mechanism, and no
  clan/faction split mechanism, exist at all (both confirmed absent by direct grep, not inferred).

## FND-S07 — A wound becomes a debt (full cross-domain chain)

A wounded entity's reduced combat capability should eventually reduce its economic output and
change how others relate to it.

- **Rules invoked:** OWN-02 (participation ≠ ownership), OWN-05 (cross-domain transitions preserve
  ownership boundaries).
- **Result: partially covered.** `combat event → injury → impaired capability` is fully
  SUPPORTED end to end. `impaired capability → economic loss` and `economic loss → relationship
  reaction` are both MISSING. The scenario is scored as partially covered by design — it correctly
  stops exactly where OWN-05's per-link evidence review already found the chain stops.

## FND-S08 — Two systems, one field

A hypothetical check: could both the Combat domain and the Life/Body domain each believe they own
`readiness`?

- **Rules invoked:** OWN-01 (one authoritative source of durable truth), OWN-02 (participation ≠
  ownership).
- **Result: covered.** `readiness` has exactly one owning patch path; Combat-domain logic reads it
  and reacts to it but the apply-pipeline architecture makes a second, competing write path
  structurally impossible, not merely discouraged by convention.

## FND-S09 — A rumor that never became true (COUNTER: state change that should not persist historically)

A rumor claims an entity betrayed their clan. The rumor spreads as a belief but the betrayal never
actually happened — no authoritative state ever changes.

- **Rules invoked:** OWN-04 (proposed change is distinct from committed state), OWN-06 (historical
  reference doesn't imply present ownership).
- **Result: covered.** Belief/lead records are explicitly modeled as possibly-wrong and never
  write back into the authoritative fact they claim about; the rumor can spread, be believed, and
  even be chronicled as "it was said that..." without ever becoming the committed truth that the
  betrayal occurred. This is the clean confirming case for both rules.

## FND-S10 — Drought to ruin (cross-domain causal chain)

`drought → resource scarcity → migration → abandoned settlement → ecological takeover.`

- **Rules invoked:** CAUSE-02 (causal chains may cross domains without breaking).
- **Result: partially covered.** First two links SUPPORTED; last two links MISSING, matching the
  same Places-domain gap already surfaced in FND-S03. The chain doesn't break architecturally — it
  simply runs out of implemented consequence partway through, which is the correct way for a
  partially-built world to fail this scenario (a design gap, not a semantic contradiction).

## FND-S11 — Two omens, no connection (COUNTER: correlated but not causal)

A merchant's shop burns down the same week a rival opens a competing stall nearby. The two events
are temporally adjacent and narratively tempting to link, but nothing produced one from the other.

- **Rules invoked:** CAUSE-03 (correlation is not causal connectivity).
- **Result: covered.** Applying the four-part test (declared link / producer-side consequence /
  consumer-side reaction / causal-or-provenance relation) to this pair fails at the first part —
  there is no declared link between the two events anywhere in the system, so no causal claim
  should ever be generated from their mere adjacency. The scenario confirms the standard rejects
  exactly this kind of coincidence.

## FND-S12 — A kingdom falls, and that's not the point

A region's authority structure collapses entirely over a long run.

- **Rules invoked:** CAUSE-07 (world outcomes carry no inherent polarity).
- **Result: covered, by definition of the rule rather than by new evidence.** The collapse itself
  is not scored as good or bad; only whether the causal chain that produced it is traceable and
  real (per CAUSE-01/CAUSE-03) has standing to be evaluated. This scenario exists to keep the
  distinction concrete for future domain authors, not to re-derive it.

---

## Cross-batch note

Two scenarios (FND-S03, FND-S10) surface the same underlying Places-domain gap
(no settlement-lifecycle mechanism) from two different angles — identity continuity and causal-
chain continuation, respectively. This is recorded once here rather than as two unrelated
findings, since a future Places foundational batch will need to resolve both with a single
mechanism, not two.
