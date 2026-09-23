---
status: authoritative
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# Scenario Bank: Foundational Batch 01

**Purpose/scope.** Twenty-one scenarios used to pressure-test the Identity, State Ownership, and
Causality rule families in `foundations/identity.md`, `foundations/state-ownership.md`, and
`foundations/causality.md`. FND-S01–S12 are the original seed set; FND-S13–S21 are a later
adversarial expansion (`tmp/world-catalog-expand-scenario-and-review-layer-ext-ai.md`) added
before treating the batch as ready for high-level external review. Eight of the twenty-one are
counter-scenarios (marked **COUNTER** below): the five required by the original batch-01
instruction (a transformation that *should* create new identity, a state change that should *not*
persist historically, two similar facts with legitimately different state owners, two
correlated-but-not-causal events, an aggregate change that should not affect every individual
member) plus three added by the expansion (a successor that must not be treated as the
predecessor, a false belief that never produces any consequence, a dead entity's historical
relevance legitimately fading).

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

## Expansion: adversarial probes (FND-S13–S21)

Added per `tmp/world-catalog-expand-scenario-and-review-layer-ext-ai.md`, before treating Batch 01
as ready for high-level external review. These remain **foundational probe scenarios** — they ask
whether identity continuity still makes sense, who owns the durable facts involved, whether a
valid causal path exists, and which semantics must be deferred to a later domain. They
deliberately do **not** attempt to design vampire mechanics, inheritance law, organizational
politics, or belief propagation — those stay out of scope for this batch. Several of these probes
pair a headline scenario with a **counter** that tests the opposite trajectory, checking that the
accepted Rules are not simply broad enough to approve every desirable outcome.

## FND-S13 — Growing into a new form

An ordinary creature, through repeated experience and accumulated exposure, undergoes a
significant capability or form change.

- **Probe:** does the subject remain the same identity? What kinds of change clearly do *not*
  create a new identity? Does provenance/history remain attached? Which later domain actually
  owns the transformation mechanics?
- **Rules invoked:** ID-02 (identity ≠ classification), ID-03 (transformation preserves
  continuity by default).
- **Result: covered.** `EvolutionSystem.evaluate()` triggers exactly this pattern — accumulated
  level/XP crossing a threshold (`for threshold in [10, 25, 50]`) drives a kind/capability change
  on the same `entity_id`, never a new one. This is the clean confirming case for ID-03's default:
  the actual threshold values and mechanics belong to Capability/progression, not to the Identity
  family, which only needs to state (and here reconfirms) that the transformation doesn't break
  continuity by itself.

## FND-S14 — Something wears a human shape (radical transformation boundary)

A human undergoes a supernatural transformation into a vampire-like being. Intentionally left
unresolved — this scenario checks the *shape* of the boundary, not the answer.

- **Probe:** does foundational Identity establish a default continuity rule? What would let a
  later domain declare an identity-ending exception? What must remain historically traceable
  either way?
- **Rules invoked:** ID-03, ID-05 (destruction doesn't erase history).
- **Result: covered, as a boundary check rather than a resolution.** ID-03 already states the
  default (continuity) and leaves an explicit slot for a domain-declared exception (Magic/Life, not
  yet designed) — this scenario confirms that slot is real and sufficient: nothing about how Magic
  eventually resolves the exception can retroactively erase the human-phase history, because ID-05
  guarantees historical traceability independently of which way ID-03's exception gets decided. No
  vampire mechanics were designed to reach this conclusion.

## FND-S15 — Death, then succession (cross-domain ownership chain)

A ruler dies; death becomes authoritative; succession becomes eligible; another entity acquires
role and authority. Property does not yet transfer anywhere in the chain.

- **Probe:** does any single domain accidentally own the whole chain? Is death merely a trigger
  rather than an owner of succession? Can identity/history stay distinct between predecessor and
  successor?
- **Rules invoked:** OWN-01, OWN-02, OWN-05 (cross-domain transitions preserve ownership
  boundaries).
- **Result: partially covered, per link.** `death → authoritative state`: SUPPORTED (Life/Body
  owns this). `succession eligibility → role/authority transfer`: SUPPORTED — clan leadership
  succession (`ClanLifecycleService.process_succession()`, `leader_entity_id_set`) resolves to an
  existing, independently-identified living member; Politics/Authority owns this cleanly, and
  death never becomes anything more than the trigger that makes the check run. `role/authority
  transfer → property/wealth transfer`: MISSING — checked directly, no inheritance-of-objects/
  gold mechanism exists anywhere in the repository. No domain was found accidentally owning a link
  it shouldn't; the chain simply runs out of implemented consequence at the Objects boundary,
  which is a repository gap, not an ownership violation.

## FND-S16 — The heir is not the ruler (COUNTER, paired with FND-S15)

A successor acquires the predecessor's role and authority but must never be treated as a
continuation of the predecessor's own identity.

- **Probe:** is a successor ever silently conflated with the person it succeeds?
- **Rules invoked:** ID-01, OWN-01.
- **Result: covered.** `heir_entity_id`/`leader_entity_id_set` always resolve to an already-
  existing, independently-tracked living entity's own id — there is no code path in the
  succession or clan-leadership mechanism that could assign the deceased's id to the successor even
  by accident. Confirms the counter cleanly: authority moves, identity does not.

## FND-S17 — One organization, two successors

An organization undergoes internal division and produces two successor organizations that may
share provenance but should not share identity.

- **Probe:** does the original identity survive? Do both successors inherit provenance? Can the
  foundational rule stay neutral and require Organization-domain semantics? Does ID-06 provide
  enough structure without deciding the answer prematurely?
- **Rules invoked:** ID-06 (split/merge/succession require explicit identity semantics).
- **Result: blocked/deferred — matches the existing FND-S06 finding rather than adding a new one.**
  No organization or clan split mechanism exists at all (confirmed again by direct search), so the
  scenario cannot progress past "does the original identity survive" to actually test provenance
  inheritance — there is no split operation to trace. This is the same gap-shape already recorded
  for FND-S03/FND-S06/FND-S10, and it reconfirms rather than changes ID-06's own disposition: ID-06
  already states the requirement ("must not silently assume identity behaviour") without deciding
  it, and this scenario shows that stance is still correct under adversarial pressure — nothing
  here argues ID-06 needs to be more specific yet.

## FND-S18 — A lie that moves an army

A false claim is believed by an entity, the entity acts on the belief, and the action produces a
real consequence — even though the original claim was never true.

- **Probe:** world truth ≠ belief truth ≠ causal irrelevance. Can a false proposition still be a
  real cause, through a real belief state?
- **Rules invoked:** CAUSE-01 (real causal path required), OWN-04 (proposed change ≠ committed
  state), OWN-06 (historical reference ≠ present ownership).
- **Result: partially covered.** `BeliefCycleSystem.process_rumor()` and `estimate_threat()`
  confirm belief — regardless of whether the underlying claim is true — is a real input to
  decision logic; an entity can act (e.g. engage in combat) on a belief that turns out to be false,
  and that action is a real cause per CAUSE-01, satisfying the "false belief as real cause"
  requirement without ever promoting the false claim itself to authoritative truth (OWN-04/OWN-06
  hold throughout). The belief→combat-action link is SUPPORTED; belief→economic/social/political
  consequence beyond combat is MISSING, for the same underlying reason OWN-05's own downstream
  links are MISSING — this is a repository-completeness gap, not a Causality-family gap.

## FND-S19 — A rumor that went nowhere (COUNTER, paired with FND-S18)

A belief is held, with real confidence, but never triggers any action or downstream consequence.

- **Probe:** must every belief eventually cause something, or is causal irrelevance a legitimate
  outcome for a belief?
- **Rules invoked:** CAUSE-01, CAUSE-03 (correlation is not causal connectivity).
- **Result: covered.** `decay_stale_leads()`/`resolve_lead_staleness()` confirm a belief can decay
  or go stale without ever producing an effect — nothing in the architecture forces a belief to
  eventually matter. This is the correct behavior the counter is checking for: a held belief is not
  automatically a pending cause.

## FND-S20 — The king is dead, the feud is not

An important entity dies; active participation ends; other entities still remember and react;
territory, rivalry, institutions, or story continue to change afterward.

- **Probe:** identity termination vs. historical persistence; historical reference vs. present
  authoritative state; indirect causality after an entity is no longer active.
- **Rules invoked:** ID-05, OWN-06, CAUSE-05 (causal history traceable within declared reach),
  CAUSE-06 (compression must not fabricate causal links).
- **Result: covered — reconfirms rather than newly discovers these rules.** `_transfer_inherited_
  feud()` and dying-wish seeding are exactly this pattern: real causal effects produced after the
  actor is no longer active, referencing the dead actor's stable id, without granting the dead
  actor's own historical record any present authority. No new evidence beyond what ID-05/OWN-06
  already established was needed to confirm this.

## FND-S21 — A name the world forgets (COUNTER, paired with FND-S20)

A dead entity's historical relevance should be able to legitimately fade over time, rather than
persisting at constant significance forever.

- **Probe:** is "fading relevance" distinguishable from erasure or fabrication? Does anything
  currently model it?
- **Rules invoked:** CAUSE-06.
- **Result: revealed a new, previously-unnamed gap.** Checked directly: no importance-decay
  mechanism exists anywhere in the chronicle/legend code (`src/domains/chronicle/`,
  `src/domains/fame/legend.py`) — every recorded fact stays at constant significance once created,
  within whatever reach CAUSE-05 already declares. This is a genuinely different gap from CAUSE-05's
  Campaign-mode reach boundary: reach is about retention *fidelity*, this is about a legitimately
  *fading weight* over time for facts that are still fully retained. Not previously named in this
  batch — see the CAUSE-06 refinement below.

---

## Cross-batch note

Two scenarios (FND-S03, FND-S10) surface the same underlying Places-domain gap
(no settlement-lifecycle mechanism) from two different angles — identity continuity and causal-
chain continuation, respectively. FND-S17 surfaces the same-shaped gap a third time, for
organizations rather than places (no split mechanism exists there either). This is recorded once
here rather than as three unrelated findings, since whichever future batch resolves each will need
one mechanism per domain, not a special case per scenario.

FND-S21 surfaced a gap distinct from anything found in the original twelve scenarios: no mechanism
exists to let a historical fact's significance legitimately fade over time, as opposed to being
compressed, forgotten outside a declared reach, or fabricated. This motivated a light refinement
to CAUSE-06 in `foundations/causality.md` (see that file's revision note) — the only Rule change
this expansion produced.
