---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Resources / Production

**Purpose/scope.** How inputs become outputs through a declared production process, and what
makes something scarce in the simulated world. Does not design crafting trees/content
catalogs. Distinguishes resource scarcity from price, value, and desire.

**Status.** Batch 08 (Objects/Ownership/Resources/Economy), drafted 2026-09-22, revised the
same day per follow-up review (`tmp/world-rule-batch-8-followup-ext-ai.md`): PROD-01
generalized from a strict "jointly-necessary, no-substitution" requirement to a broader
permission — a production process declares whatever inputs/conditions and substitution
semantics it needs, required inputs simply cannot be silently skipped. Candidates below
originated as external-reviewer hypotheses (`tmp/world-rule-batch-8-ext-ai.md`); each carries
this session's disposition and repository evidence. Structured per the normalized five-category
methodology.

---

## Domain Rules

## PROD-01 — A production process declares whichever inputs/conditions it requires, including any allowed substitution semantics; a required input cannot be silently omitted

> A production process declares the inputs/conditions required for that process (raw
> materials, capability, tools/equipment, time, currency cost, environmental conditions),
> including any allowed substitution semantics — one required category may permit alternative,
> substitutable materials to satisfy it, or may not, entirely as the process's own declaration
> states. What a process may never do is silently omit a declared-required input: satisfying it
> through an undeclared substitute, or skipping it entirely, is not permitted merely because
> some other input was abundant.

**Disposition: ACCEPT, revised 2026-09-22 per follow-up review — generalized from a strict
"jointly-necessary, no-substitution" requirement (which would have wrongly forbidden a world
from ever declaring substitutable materials) to a broader permission: substitution semantics
are themselves something a process may declare, not something this Rule forbids.** Passes the
admission test: no earlier Rule states that production inputs are declared per-process,
including their own substitution rules, with only the "cannot silently omit a required input"
half held constant — COST-01 (Batch 03) establishes that cost has many dimensions, not that a
process may declare its own substitution semantics across them.

**Repository evidence: SUPPORTED for the current, unconditional-requirement shape this
repository actually implements; this repository's own current recipes happen to declare no
substitution semantics at all, which this Rule now explicitly permits as one legitimate
choice among several, not the only one.** `docs/mechanics/03_economic_laws.md` §5's Crafting
law requires exact recipe material item counts, a gold cost, and (for some recipes) a specific
station/building type — none of these are ever satisfied by a substitute in this repository's
own current content, and none is ever silently skipped. This is one legitimate instance of
this Rule's own permission (a process declaring strict, non-substitutable requirements), not
evidence that non-substitutable is the only shape a process may take.

**Scenarios:** [ME-S05](../scenarios/material-economy-batch-08.md#me-s05) (resource
conversion), [ME-S06](../scenarios/material-economy-batch-08.md#me-s06) (production fails
after partial cost), [ME-S18](../scenarios/material-economy-batch-08.md#me-s18) (production
with substitutable inputs, added per 2026-09-22 follow-up).

---

## PROD-02 — Scarcity is a fact about real availability in world state or process, distinct from price, value, and desire

> Scarcity is a fact about how little of something is actually available, accessible, or
> producible in the world — not a narrative label, and not the same fact as price, value, or
> how much a subject wants it. A world's pricing or valuation mechanisms may or may not read
> real scarcity; scarcity is real and may matter to a subject's own prospects whether or not
> any pricing mechanism connects to it.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule distinguishes scarcity
from price/value/desire as four separable facts, or permits scarcity to exist and matter
independent of whether any pricing mechanism reads it — this is genuinely new content directly
required by the batch instruction's own §6.

**Repository evidence: SUPPORTED for real, world-state-driven scarcity; CONFIRMED
DISCONNECTED from this repository's own pricing mechanism — a significant, honestly-recorded
finding, not assumed connected.** `ResourceNodeState.remaining_charges`/`max_charges`
(Batch 06 evidence) is real, causally-produced scarcity — nodes deplete from actual harvest
events and regenerate on a real cadence (`ResourceEcologyService`, `ECOLOGY_INTERVAL=200`
ticks) — never a narrative label. This real scarcity already matters to a subject's own
prospects independent of price: `GATHER_RESOURCE` route benefit scales by
`remaining_charges/max_charges` directly (Batch 06 evidence). **Checked directly: no producer
anywhere computes `region.price_modifiers`/`building.price_modifiers` from real depletion,
supply, or scarcity data** — every write site for `price_modifiers_set` is pure merge/
propagation logic (`other.price_modifiers_set if not None else self.price_modifiers_set`);
none assigns a computed value derived from scarcity. `calculate_price()`
(`src/systems/economy_systems/market.py`) multiplies `base_val * region_mod * building_mod *
type_bias` — a real causal input mechanism (the multiplier chain is genuine, not decorative),
but the specific multiplier values it reads are static, author-set content, never updated from
actual resource depletion. Scarcity and price are not merely conceptually distinct in this
repository — they are actually, confirmedly disconnected.

**Scenarios:** [ME-S07](../scenarios/material-economy-batch-08.md#me-s07) (scarcity emerges),
[ME-S08](../scenarios/material-economy-batch-08.md#me-s08) (scarcity without price change,
counter), [ME-S09](../scenarios/material-economy-batch-08.md#me-s09) (price without objective
scarcity).

---

## Inherited / Applied Foundational Rules

### A production process creates a new object identity without preserving input identity, unless a domain declares otherwise

> Production consumes its declared inputs and creates a new output with its own identity —
> the output is never a continuation of any single input's own prior identity, and preserving
> provenance across that transformation is a domain choice, not automatic.

**Disposition: INHERITED — direct reuse of ID-04 (creation establishes identity) and CAUSE-01
(real causal path), and cross-referenced from `objects-material-culture.md`'s own identical
entry. No new claim added here: this family's own investigation of "production" (§5) confirms
the same boundary that family already established from the object side.**

**Repository evidence: SUPPORTED**, reused directly — see `objects-material-culture.md`'s own
fuller evidence.

**Scenarios:** [ME-S05](../scenarios/material-economy-batch-08.md#me-s05).

### An interrupted process that has already incurred cost does not refund that cost merely because the output never materialized

> A cost already expended toward an incomplete process is a real, already-committed fact —
> its own lifecycle (committed vs. refundable vs. sunk) is a declared property of the cost
> itself, not automatically reversed by the process failing to complete.

**Disposition: INHERITED — direct reuse of Batch 03's COST-03 (cost-lifecycle distinction),
per the batch instruction's own explicit "reuse Batch 03 lifecycle-of-cost semantics"
instruction. No new claim.**

**Repository evidence: SUPPORTED**, reused directly from COST-03's own evidence.

**Scenarios:** [ME-S06](../scenarios/material-economy-batch-08.md#me-s06).

---

## Scope / Deferred Boundaries

### Crafting trees / content catalogs

> This family does not design concrete crafting trees, recipe catalogs, or specific production
> chains — only the semantic boundary a production process must respect, per the batch
> instruction's own explicit "do not design crafting trees/content catalogs yet" instruction.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions.** PROD-02 states that
scarcity and price *may* be disconnected; the finding below reports that in this repository
they *are*. Whether to connect them is an implementation-planning decision this Rule Catalog
identifies but does not make.

- **CONFIRMED — scarcity and price are actually disconnected in this repository, not merely
  conceptually separable.** See PROD-02 above — no producer computes price modifiers from real
  resource depletion.
- **Cross-referenced from `economy-exchange.md`**: whether price has *any* real causal input at
  all (as opposed to none) is that file's own question; this file's own finding is narrower and
  more specific — price's real causal inputs (`region_mod`/`building_mod`/`type_bias`) exist,
  but none of them is scarcity.

## Cross-domain links recorded here

- PROD-01 → Cost (COST-01, Batch 03), Capability (CAP-01–05, Batch 03)
- PROD-02 → Perception/Knowledge (Batch 06, information about scarcity is a distinct question
  from scarcity itself — not designed here), Economy/Exchange (`economy-exchange.md`'s own
  EXCH-01, value/price distinctness)
- Inherited creation/destruction entry → Identity (ID-04), Causality (CAUSE-01),
  `objects-material-culture.md` (the same entry, cross-referenced not duplicated in spirit)
- Inherited cost-lifecycle entry → Cost (COST-03, Batch 03)

## Open questions carried forward

1. Whether `price_modifiers` should ever be computed dynamically from real scarcity/depletion
   is a real design/implementation question this batch flags but does not decide.
2. Whether this repository should build a real opportunity-seeking mechanism (an entity
   noticing and acting on a scarcity/price differential) is flagged for a future batch or
   ticket — not decided here.
