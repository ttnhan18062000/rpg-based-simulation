---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Law / Enforcement

**Purpose/scope.** What makes something a law or institutional rule rather than merely a
preference, custom, or norm; how a law's existence, a subject's knowledge of it, compliance,
detection, judgment, and sanction relate as distinct, independently-failing facts; and how an
institutional record's own correctness relates to world truth and to individual belief. Does
not design a concrete criminal-justice content catalog, nor build territorial jurisdiction
depth (deferred to Batch 11).

**Standing direction (2026-09-22, `tmp/world-rule-direction.md`).** Applied from this batch
onward: Rule statements below describe only target world semantics, independent of current
repository realization.

**Status.** Batch 10 (Organizations/Institutions/Politics/Law), first draft, per
`tmp/world-rule-batch-10-ext-ai.md`.

---

## Domain Rules

## LAW-01 — Rule existence, applicability, subject action, compliance/violation, knowledge or belief about the rule/event, detection/report, adjudication (where applicable), sanction decision (where applicable), and sanction execution are semantically distinct facts that do not automatically imply one another

> A law or institutional rule existing does not mean it applies to every subject/place/time
> (see LAW-03), that a subject acted in a way the rule addresses, that the action complied or
> violated it, that any subject knows or believes either the rule or the event occurred, that a
> violation is detected or reported, that a detected matter is adjudicated, that adjudication
> produces a sanction decision, or that a decided sanction is actually executed. These are
> semantically distinct facts, and none is required by any legal system to route through every
> other one — a domain may validly declare a violation that is simply never detected; a
> detected violation that triggers an automatic declared consequence with no separate
> adjudication step; or a full accusation → adjudication → sanction pipeline. What must always
> hold regardless of which stages a specific institution declares: a sanction being decided is
> never the same fact as that sanction being successfully executed — reach, capability, or
> authority may still prevent execution — and a law remaining formally valid despite repeated
> disobedience is a legitimate outcome, never a sign the law itself has lapsed.

**Disposition: ACCEPT — REQUIRED for the distinctness; which stages any specific legal system
actually uses is PERMITTED, domain-specific content (REVISED 2026-09-22 per external follow-up
review).** The original wording ("six distinct facts in a causal chain") risked implying one
mandatory justice pipeline every legal system must implement in full. This revision keeps the
substantive requirement (these are genuinely separate facts, not automatically implying each
other) while explicitly permitting a domain to declare a shorter chain — skipping detection
entirely, or collapsing detection straight into an automatic declared consequence with no
separate judgment stage — without weakening the one universal constraint this Rule still
requires: decision ≠ execution. Passes the admission test unchanged: no earlier Rule states
this specific multi-way distinctness for an institutional rule-enforcement context.

**Repository evidence: MISSING, for the entire set of facts — this repository has no in-world
law, crime, violation, or sanction subsystem at all.** Confirmed via direct, broad search:
every "law"/"crime"/"violation"/"sanction" hit in this repository belongs to observability/
anomaly-detection tooling (`src/observability/hard_law_monitor.py`, `src/observability/
anomaly/*`) or meta-level engine invariants (`src/core/concurrency_law.py`) — a
development/monitoring concern about the simulation's own code correctness, entirely unrelated
to an in-world subject violating an in-world rule. `LegalityServiceV2`'s own
`ReasonCode.ILLEGAL_ACTION`/`SELF_ATTACK_ILLEGAL` (Batch 02's AUTH family) is the closest
adjacent concept, but it rejects an *attempted* action before it ever becomes a committed world
event — it is not a violation-detection-and-sanction chain over an action that already
occurred, which is what this Rule's own facts require.

**Scenarios:** [IP-S11](../scenarios/institutions-politics-batch-10.md#ip-s11),
[IP-S12](../scenarios/institutions-politics-batch-10.md#ip-s12) (violation goes undetected),
[IP-S15](../scenarios/institutions-politics-batch-10.md#ip-s15) (enforcement fails, extended —
enforcement without a separate judgment stage), [IP-S16](../scenarios/institutions-politics-batch-10.md#ip-s16)
(law is ignored).

---

## LAW-02 — An institutional record's own correctness is independent of world truth and of any individual's own belief; a false or outdated institutional record may still cause real institutional consequences exactly as a true one would

> An institution's own record of a fact — that a violation occurred, that a debt is owed, that
> a claim is valid — may be correct, incorrect, outdated, forged, or missing. An institutional
> record is never automatically equated with objective world truth, nor with any specific
> individual's own belief about the same fact — these are three separate facts that may
> disagree. A false institutional record can still cause a real institutional consequence
> (an accusation acted upon, a sanction applied) exactly as a true record would; correcting the
> record afterward does not automatically undo the consequence already caused.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: this establishes an
*institution* as its own kind of record-holding subject, distinct from both world truth
(already established generally by Batch 01's causality/state-ownership content) and individual
belief (Batch 06's KNOW-01/KNOW-02) — a genuinely new three-way distinction, in the same family
of content as Batch 09's SOC-01/FAM-01 (which likewise required a new multi-way split rather
than a restatement of an existing one), now applied to a collective/institutional subject
rather than an individual or a relationship.

**Repository evidence: MISSING, for any in-world institutional record mechanism of this kind
— there is no institutional "record" for this Rule to check against.** This is the same
underlying gap LAW-01 reports (no in-world law/crime subsystem exists), viewed from the
record-keeping angle rather than the enforcement-chain angle. The closest structurally-related,
already-confirmed pattern is Batch 09's own reputation-reach finding
(`social-lineage/social-relations.md`) — every reputation consumer reads `public_reputation`
directly as global truth, which is the *opposite* failure mode this Rule is stated to permit
(a false record diverging from truth) rather than an instance of it, since `public_reputation`
is not itself modeled as a fallible institutional record with its own provenance.

**Scenarios:** [IP-S13](../scenarios/institutions-politics-batch-10.md#ip-s13) (false
accusation).

---

## LAW-03 — Law or authority applicability is determined by a declared scope, which may itself be territorial, membership-based, role-based, contractual, event-specific, temporal, or explicitly global — but is never universal merely by accident of a rule existing

> Whether a law or an authority relationship applies to a given subject, place, or moment is
> determined by a declared scope specific to that law or authority. That declared scope may
> take many legitimate forms — territorial (a specific region), membership-based (a governed
> group), role-based (an occupied position), contractual, event-specific, temporal (a time
> period), or explicitly global (declared to apply everywhere, to everyone, at all times). What
> this Rule forbids is not global applicability itself — a domain may validly declare a
> universal law — but *accidental* universality: a law or authority applying everywhere merely
> because no scope was ever declared, rather than because global scope was itself the declared
> choice. Full territorial sovereignty is not designed here.

**Disposition: ACCEPT — REQUIRED for the declared-scope requirement (explicitly permitting a
declared-global scope); REVISED 2026-09-22 per external follow-up review to remove an
overstated anti-universality framing.** The original wording ("rather than being globally
universal by default") risked reading as though global applicability itself were prohibited.
This revision keeps the substantive requirement (scope must be *declared*, never an accident of
a rule simply existing) while explicitly listing "explicitly global" as one legitimate declared
scope among several, matching this Rule's own real target: prohibiting accidental universality,
not universality itself. Passes the admission test unchanged: this is related to but distinct
from Batch 02's AUTH-05 (transition legitimacy depends on actor/target/context, never content
alone) — AUTH-05 is about what factors determine whether *a specific proposed transition* is
legitimate; this Rule is about whether a *rule itself* applies to a given subject/place/time at
all, a prior, more basic question AUTH-05 does not address.

**Repository evidence: PARTIAL — no law-specific scoping mechanism exists, but the general
pattern (location + affiliation determining an applied effect) is already real elsewhere in
this engine.** `region.suppression_active` combined with `entity.identity.faction !=
region.owner_faction_id` (`src/engine/town_resolution.py`) applies a real, scoped combat
penalty only to entities of a non-controlling faction physically located in a suppressed
region — a live instance of exactly the location-plus-affiliation scoping shape this Rule
requires, though built for a military-suppression mechanic, not a law/rule mechanic. No
mechanism scopes a *law* or *institutional rule*'s own applicability this way, since no
in-world law concept exists at all (LAW-01's own finding).

**Scenarios:** [IP-S11](../scenarios/institutions-politics-batch-10.md#ip-s11).

---

## Inherited / Applied Foundational Rules

### An institutional sanction or consequence requires a real, declared causal mechanism connecting a judgment to its execution, exactly as any other durable-state change does

> A sanction being validly ordered does not itself execute it — a real, declared causal
> mechanism must carry out the sanction, and that mechanism may fail (the enforcing agent may
> lack capability, reach, resources, or authority to actually execute it).

**Disposition: INHERITED — direct reuse of the foundational Causality family's CAUSE-01 (any
change requires a real, declared causal event) and Batch 02's AUTH-01 (authority ≠ capability).
No new claim beyond LAW-01's own chain, restated at the specific "judgment → execution" link.**

**Repository evidence: MISSING, for the same reason as LAW-01 — no sanction-execution
mechanism exists to check this against.**

**Scenarios:** [IP-S15](../scenarios/institutions-politics-batch-10.md#ip-s15).

---

## Scope / Deferred Boundaries

### Concrete criminal-justice content catalog

> This family states the distinct law/knowledge/compliance/detection/adjudication/sanction
> facts (LAW-01) and the record-vs-truth distinction (LAW-02) but does not design a concrete
> catalog of specific crimes, laws, sanctions, or legal procedures — deferred, per this
> family's own scope, and per the batch instruction's own explicit "do not design criminal
> justice content deeply."

**Disposition: SCOPE BOUNDARY.**

### Territorial jurisdiction depth

> LAW-03 states that applicability must be scoped, and that location is one legitimate scoping
> factor, but full territorial-jurisdiction design (borders, overlapping claims, contested
> zones) is deferred to Batch 11 (Places/Settlements/Territory/Culture/Belief), per the batch
> instruction's own explicit deferral.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority — this entire family's own repository realization is uniformly MISSING, which is a
statement about current implementation scope, not about whether the target semantics above are
valid or important.**

- **Confirmed MISSING — no in-world law, crime, violation, detection, judgment, or sanction
  subsystem exists anywhere in this repository.** Every "law"/"crime" hit found belongs to
  development-time observability/anomaly-detection tooling, a meta-level concern unrelated to
  in-world subjects. See LAW-01 above.
- **Confirmed MISSING — no institutional-record concept (as distinct from world truth and
  individual belief) exists.** See LAW-02 above.
- **PARTIAL — the general location-plus-affiliation scoping pattern LAW-03 requires already
  exists elsewhere in the engine** (`region.suppression_active`), **but is not applied to any
  law/rule concept**, since none exists. See LAW-03 above; cross-referenced in
  `politics-authority.md`'s own Repository Findings.

## Implementation Candidates — Non-Binding

**This section preserves implementation-relevant discoveries only. Nothing here is approved,
prioritized, or required for implementation during the World Rule Catalog phase.**

- **Target semantic:** rule existence, applicability, subject action, compliance/violation,
  knowledge/belief, detection, adjudication, sanction decision, and sanction execution are
  semantically distinct facts that do not automatically imply one another (LAW-01).
  **Current realization:** none of these exist as in-world concepts.
  **Gap/mismatch:** the entire set of facts is unrealized, not merely one of them.
  **Possible implementation direction:** a minimal declared-rule/violation-record mechanism,
  potentially reusing the existing `ReasonCode`/legality-check machinery's own shape (Batch
  02's AUTH family) as a structural starting point for the "detection/judgment" half, combined
  with a typed record analogous to `BetrayalRecord` (Batch 09) for the "violation occurred"
  half.
  **Implementation decision:** DEFERRED — no commitment in Rule Catalog phase.

## Cross-domain links recorded here

- LAW-01 → Agency/Decision (AGENCY-01, Batch 06 — the individual-scale causal-stages analogue),
  Authority (AUTH family, Batch 02 — the closest adjacent, but distinct, concept)
- LAW-02 → Perception/Knowledge (KNOW-01/KNOW-02, Batch 06), Social Relations
  (`social-lineage/social-relations.md`'s reputation-reach finding, Batch 09 — a related but
  distinct failure mode)
- LAW-03 → Authority (AUTH-05, Batch 02 — the related-but-distinct legitimacy-factors claim),
  Places/Settlements/Territory (Batch 11, deferred)
- Inherited sanction-execution entry → Causality (CAUSE-01, Foundational), Authority (AUTH-01,
  Batch 02)

## Open questions carried forward

1. **Can one record simultaneously serve institutional and individual epistemic roles without
   violating ownership?** (Revised 2026-09-22 per external follow-up review, away from the
   storage-shaped framing "should institutional record reuse `BeliefEntry`'s data shape.")
   LAW-02 requires institutional record, world truth, and individual belief to remain three
   distinct *facts*; whether one durable object could ever validly represent more than one of
   these roles at once without collapsing the distinction this Rule requires is not decided
   here.
2. Whether this family's own near-total MISSING realization reflects a genuine, currently
   deprioritized simulation area, or whether Batch 11's own territorial/settlement work will
   supply prerequisites (e.g., real jurisdiction boundaries) that make this family's own
   content easier to realize later, is not decided here — a future mapping concern, not a
   Rule Catalog decision.
