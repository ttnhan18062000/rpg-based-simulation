---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Catalog — Roadmap

**Purpose.** A lightweight, high-level roadmap for completing the World Rule Catalog. This
roadmap is for **sequencing and review only** — batch boundaries are not semantic architecture,
and batches may split or merge when scenario evidence shows another grouping is better. Roughly
10–12 domain-facing batches, grouped into four milestones, plus one final integration pass that
sits outside that count by design (see "Batch count" below) — this is a **current forecast**,
not a target this roadmap should resist justified splits to preserve.

**Status (2026-09-21).** Drafted from an external-reviewer proposal, cross-checked against
`core_rpg_design_direction.md`'s target domain map and cross-cutting-layer table and
`simulation-rule-world-law-design-preparation.md`'s world-rule design order and foundational-law
list. Three gaps found in the original draft are resolved explicitly below (see "Cross-cutting
layer disposition") rather than left as silent omissions. Batch 01 is complete; Batch 02 (Time /
Authority / Reach) and Batch 03 (Capability / Cost / Capacity / Resource / Transformation) are
both drafted, each revised once per its own follow-up review, and both **PASS — frozen**; the
Milestone A History/Provenance completion pass is drafted and ready for high-level external
review. **Milestone A is fully drafted.** Batch 04 (Space/Environment/Movement) — the first
domain-facing Milestone B batch — is also drafted and ready for high-level external review,
begun immediately after Milestone A per that batch's own instruction. Batch 05 (Life/Body/
Survival/Ecology) is the next planned step once Batch 04 receives review.

---

## Milestone A — Foundational World Semantics

**Goal:** establish the semantic laws every later domain depends on.

### Batch 01 — Identity / State Ownership / Causality

**Status: complete.** Drafted, adversarially scenario-expanded (FND-S01–S21, 8 counters), all
open semantic questions and owner-attention decisions dispositioned, and — as a direct product of
that work — a fourth foundational family was added at scope level only:

**Includes the History / Provenance dependency, discovered through scenarios, not planned in
advance.** `foundations/history-provenance.md` names (but does not yet draft) the family that
will eventually own CAUSE-05/CAUSE-06's persistence, provenance, compression, and
significance-fading substance. See that file and `causality.md`'s forward-reference notes for the
exact boundary between what stays in Causality and what migrates once it's drafted.

### Batch 02 — Time / Authority / Reach

**Status: PASS — frozen.** Drafted, then revised once per follow-up review (implementation
detail removed from Time, Authority's legitimacy framing broadened beyond actor identity, a real
internal inconsistency in Reach corrected, 4 scenario probes added). See
`review-exports/foundational-batch-02-review.md`.

Focus on:

```text
time and ordering
temporal persistence
authority to cause/change state
reach / locality / interaction possibility
```

These should answer: **when can something affect something else, and who is semantically
allowed to do so?**

**Clarified 2026-09-21 — world-semantic time is in scope; execution-mechanical time is not:**

```text
execution scheduling / same-tick domain ordering / engine cadence
→ out of scope

world-semantic time
→ in scope
```

*World-semantic time* — squarely this batch's job — may include ordering, duration, delay,
recurrence, expiration, aging, simultaneity, and temporal persistence where relevant: whether one
event happened before another in the world's own causal sense, how long an effect lasts, whether
something recurs or expires, whether two things can be simultaneous, and how age/duration accrue.
None of that is the same question as *which system's code runs first within a tick* —
`core_rpg_design_direction.md`'s Substrate domain scope includes "state transition, scheduling and
cadence, event flow" alongside identity/time/persistence, and that execution-mechanical side stays
out of this batch. This is an implementation/execution-order concern, not a world-semantic law —
already decided once, not merely assumed: Batch 01 drafted and deliberately rejected a same-tick
read/write-ordering candidate rule on exactly this basis (see `foundations/state-ownership.md`'s
"Candidates considered and not added"). Batch 02 should carry that same disposition forward
rather than re-deciding it, and should not attempt to write a semantic rule for
scheduling/cadence/event-flow.

### Batch 03 — Capability / Cost / Capacity / Resource / Transformation

**Status: PASS — frozen.** Drafted, then revised once per follow-up review (repository-status
language removed from CAP-05, cost-lifecycle distinction sharpened in COST-03, RES-01 broadened
beyond personally-held resources, universal atomicity removed from RES-04, LIMIT-03 generalized
beyond one assumed response). All five families kept separate (no merge found necessary);
threshold semantics folded into Capacity rather than given their own family; deterministic
randomness investigated and moved out of the Catalog entirely, on a rationale sharpened by the
follow-up. See `review-exports/foundational-batch-03-review.md`.

Focus on foundational constraints such as:

```text
capability requirements
cost
capacity / limits
resource / conservation semantics
thresholds
transformation permission
deterministic randomness / reproducibility where semantically relevant
```

Do not build generic implementation frameworks.

### Foundational completion pass — History / Provenance

**Status: drafted 2026-09-21, ready for high-level external review.** See
`review-exports/history-provenance-completion-review.md`. Six rules (HP-01–06): two restate/
newly-claim within this family's own home (HP-01, HP-02), three are direct migrations of
CAUSE-05/CAUSE-06's persistence-specific substance (HP-03/HP-04/HP-05), one consolidates three
already-accepted rules for future chronicle-content authors (HP-06). Establishes semantics for:

```text
historical continuity
provenance
persistence
causal-history retention
compression boundaries
legitimate fading
```

This is where the persistence-specific substance already flagged for migration out of CAUSE-05
and CAUSE-06 (declared-reach mechanism, compression-tier design, significance-fading mechanism)
actually gets drafted as History/Provenance's own rules, per those rules' own forward-reference
notes and `history-provenance.md`'s "Relationship to Causality" section. **The Final Integration
Batch later deepens and integrates these already-drafted semantics with significance, world
reaction, propagation, and long causal chains — it does not define History/Provenance for the
first time.** (See that batch's own updated wording below.)

**Milestone A exit:** later domains can define their own rules without redefining basic
identity, causality, authority, reach, time, capability, persistence, and now
historical-continuity/provenance semantics.

> **Guardrail, added 2026-09-21.** Foundational concepts such as Authority, Reach, Resource,
> Capacity, and State Ownership must not be automatically unified with similarly named
> later-domain concepts such as political authority, spatial reach, economic resources, or
> property ownership. A shared word is not a shared Rule — each later domain earns its own
> semantics through its own investigation (per `simulation-rule-world-law-design-preparation.md`
> §3.3's A–L order), even where a foundational family already used the same word at a more
> abstract level.

---

## Milestone B — Individual Entity World Model

This milestone should receive especially strong depth because the primary narrative subject is
the trajectory of individual entities.

### Batch 04 — Space / Environment / Movement

**Status: drafted 2026-09-21, ready for high-level external review.** 17 rules across
`space-environment/location-topology.md`, `environment.md`, `movement-navigation.md`. Two
confirmed repository gaps (no route/portal/directional-connection mechanism; no non-physical
movement mechanism) and one confirmed causally-inert environmental field
(`service_availability`). See `review-exports/space-environment-batch-04-review.md`.

```text
location
topology
movement
accessibility
environmental exposure
spatial reach
```

### Batch 05 — Life / Body / Survival / Ecology

```text
life and death
body state
injury
needs
survival
creatures
population / ecological pressures
```

Keep individual entity semantics distinct from aggregate ecology.

### Batch 06 — Perception / Knowledge / Information / Agency

```text
observation
belief
truth vs knowledge
memory
information propagation
decision
motivation
opportunity / affordance
```

This batch should strongly revisit scenarios such as:

```text
false belief → real action → real consequence
```

(Batch 01's FND-S18/S19 already probed this at the foundational level via Causality/State
Ownership; this batch is where the actual Perception/Agency domain semantics get written.)

### Batch 07 — Capability / Progression / Conflict

```text
learning
adaptation
XP / level where applicable
qualitative transformation
power development
combat / conflict
injury → capability consequences
```

This is where lived-history progression should begin becoming concrete.

**Milestone B exit:** an individual can meaningfully live, perceive, decide, act, change, fight,
learn, survive, die, and accumulate history.

---

## Milestone C — Material and Social World

### Batch 08 — Objects / Ownership / Resources / Economy

```text
objects
material transformation
possession / ownership
production
scarcity
wealth
trade
economic consequences
```

Revisit inheritance/property-transfer scenarios here — Batch 01's FND-S15 already found that
role/authority succession is real but object/wealth transfer to an heir has no mechanism at all
(deferred jointly across this batch, Family/Lineage, and Politics; see
`foundations/state-ownership.md`'s OWN-05 open questions).

### Batch 09 — Social Relations / Family / Lineage

```text
relationships
reputation
identity in society
family
inheritance
succession
feuds
obligations
```

Also formally document the reputation-scalar-vs-reputation-labels naming collision Batch 01's
OWN-03/FND-S05 surfaced (two legitimately separate owned fields with an undocumented narrative
relationship) — flagged there, not resolved there.

### Batch 10 — Organizations / Institutions / Politics / Law

```text
groups
organizations
institutional roles
authority
political power
law
crime / enforcement where applicable
war
split / merge / succession of organizations
```

Batch 01's ID-06 found no organization/clan split, merge, or founding mechanism exists at all
(confirmed twice, independently, by FND-S06 and FND-S17) — resolve here, not before.

### Batch 11 — Places / Settlements / Territory / Culture / Belief

```text
persistent places
settlement lifecycle
territory
place ownership / occupation
culture
religion
belief institutions
```

If this becomes too large, split it into two batches. Settlement lifecycle (camp → settlement →
ruin) is a gap Batch 01 found independently from two angles (ID-03, CAUSE-02) — resolve here.

**Milestone C exit:** individuals can participate in durable material, economic, social,
institutional, territorial, and cultural structures that themselves evolve historically.

---

## Milestone D — Fantasy Integration and Whole-World Validation

### Batch 12 — Magic / Supernatural

Do not make magic an isolated spell subsystem. Define its world rules and connect it outward
into:

```text
body
capability
environment
objects
knowledge
belief
places
institutions
conflict
```

Use previously deferred cases such as `human → vampire-like transformation` as real scenario
probes — Batch 01's ID-03/FND-S14 already confirmed the default+exception slot is sufficient
without inventing a universal identity-ending test; this batch writes the actual exception.

### Final Integration Batch — Cross-Domain History / Significance / Propagation

This is not another ordinary domain. Use it to examine the World Rule Catalog as one causal
system:

```text
history
significance
world reaction
power conversion
cross-domain propagation
counterforces
long causal chains
```

**Updated 2026-09-21.** History / Provenance is no longer first-defined here — it is drafted in
Milestone A's foundational completion pass (see above). This batch's job for History /
Provenance is to **deepen and integrate** those already-drafted semantics (historical
continuity, provenance, persistence, causal-history retention, compression boundaries,
legitimate fading) with significance, world reaction, propagation, and long causal chains — not
to define the family for the first time.

Run a small set of end-to-end canonical trajectories, for example:

```text
ordinary creature
→ survival
→ adaptation
→ growing capability
→ territory
→ conflict
→ reputation
→ organized response
→ death / persistence of legacy
```

and:

```text
poor individual
→ knowledge / opportunity
→ wealth
→ relationships
→ organization
→ political influence
→ institutional consequence
```

Do not script these outcomes. Use them to test whether the Rule Catalog makes such trajectories
possible through valid causal chains.

---

## Cross-cutting layer disposition

**Added 2026-09-21.** `core_rpg_design_direction.md` §7 names five cross-cutting layers, not
domains. This roadmap's batches account for three of them; the other two need an explicit call
rather than silent omission:

- **History, significance & world reaction** — covered by Batch 01's History/Provenance naming,
  Milestone A's foundational completion pass (actual drafting), and the Final Integration
  Batch's later deepening/integration with significance and world reaction specifically.
- **Systemic pressure & propagation** — covered by the Final Integration Batch ("power
  conversion, cross-domain propagation, counterforces").
- **Evaluation** — **correctly out of scope for this Catalog**, not a gap. Rule/Law design
  defines world semantics; evaluation semantics (what must hold, what constitutes violation, what
  should be observable) is `simulation-rule-taxonomy-evaluation-direction.md`'s own document, per
  the evaluation/governance boundary already established in
  `simulation-rule-world-law-design-preparation.md` §3.8. No batch should attempt to redefine or
  absorb it.
- **Observation & legibility** (read models, presenters, chronicles, telemetry, inspection
  surfaces) — **out of scope for this Catalog.** This is how the world's state is *presented*,
  not a rule about what is *true* of the world — the same distinction the project's Architecture
  Rule already draws ("API/routes present shaped read models through presenters/schemas, not raw
  domain objects"). No batch should write a semantic Rule family for it; it stays governed by the
  existing Architecture Rule and `/api-design-principles`, outside this Catalog's remit.
- **Content authoring & world assembly** (catalogs, world modules, compilation, content
  resolution, registries) — **mostly out of scope, with one real semantic sub-question flagged,
  not resolved, for whichever batch first needs it.** The compilation/tooling mechanics
  themselves are implementation, not world semantics. But "where authored identity enters the
  world" touches a genuine open question already latent under Batch 01's ID-04 (creation
  establishes identity explicitly): does an authored catalog template carry its own identity
  distinct from the instances it produces, or is it purely a stamp with no identity of its own?
  Not decided here — flagged so whichever future batch first needs the answer (most likely
  Objects/Batch 08 or Organizations/Batch 10, wherever templated instantiation first becomes
  concrete) cites this rather than silently deciding it.

## Batch count

The 12 numbered batches above, plus the unnumbered Milestone A History/Provenance completion
pass, plus the Final Integration Batch, total 14 labeled units. **This entire section is a
current forecast, not a target** — "10–12" was never meant to resist a justified split (or, as
happened here, a justified insertion); the count is expected to keep moving as scenario evidence
warrants, per "Roadmap governance" below. The Final Integration Batch specifically is not an
ordinary domain batch (see its own heading above) and was never counted toward the forecast range
either way.

---

## Expected Depth Reassessment

After Milestones B and C, and again after final integration, reassess the existing Expected
Depth Priority Map (`simulation-rule-world-law-design-preparation.md` §4). Compare expected depth
against the actual causal load revealed by Rules and Scenarios so far. Revise ratings only when
evidence warrants it.

---

## Batch workflow

Every batch should follow approximately:

```text
seed scenarios
        ↕
draft / refine rules
        ↕
counter-scenarios
        ↓
cross-domain dependency findings
        ↓
canonical files updated
        ↓
review export generated
```

Do not require external high-level review for every trivial internal edit. Generate an external
review packet at: major batch completion, milestone completion, major semantic contradiction, or
unexpected architectural discovery.

---

## Roadmap governance

Keep this roadmap high-level. Do not create implementation milestones yet. Do not estimate code
effort. Do not freeze the exact number of batches — the "10–12" figure anywhere in this document
is a current forecast, never a target to protect by declining a justified split or insertion.

- If a batch becomes too broad: split it.
- If two adjacent batches are inseparable after investigation: merge them.
- If scenario evidence reveals a missing foundational family: add it explicitly, but require a
  semantic reason rather than taxonomy completeness (this is exactly how History/Provenance was
  added in Batch 01, and how its own completion pass was then moved into Milestone A — scenario
  evidence and semantic dependency, not a desire for a complete-looking list or a fixed count).

The governing principle remains: **Scenario Bank and World Rule Catalog co-evolve; the roadmap
organizes the investigation rather than predetermining its conclusions.**
