---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Economy / Exchange

**Purpose/scope.** What economic value represents, under what conditions a price becomes
meaningful, what makes an exchange legitimate and causally complete, and what wealth actually
means in world terms. Does not require one universal objective value, does not build a
universal transaction engine, and avoids one universal `Power`/`Wealth` interpretation.
Entity-centred: economic systems matter through their effect on what a specific entity can
afford, acquire, reach, and become.

**Status.** Batch 08 (Objects/Ownership/Resources/Economy), first draft. Candidates below
originated as external-reviewer hypotheses (`tmp/world-rule-batch-8-ext-ai.md`); each carries
this session's disposition and repository evidence. Structured per the normalized five-category
methodology.

---

## Domain Rules

## EXCH-01 — Value, price, cost, and wealth are four distinct facts; price may be influenced by several factors without any single universal objective value

> Value, price, cost, and wealth are four separable facts, never automatically identical: an
> object's value to a specific subject need not equal its market price; a price need not equal
> the cost of producing it; wealth is an aggregate holding, not a price or a value. A world may
> let price be influenced by any combination of scarcity, local demand, utility, risk,
> transport/access, information, relationships, or institutions — no single universal,
> objective value is required to underlie all of them.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule distinguishes value/
price/cost/wealth as four separate facts, or states that price may legitimately derive from a
plural, non-universal set of influences — Batch 03's COST-01 addresses cost specifically
("broader than currency"), not this broader plurality including value/price/wealth.

**Repository evidence: SUPPORTED for cost/price as separate, real mechanisms; PARTIAL for
value; SUPPORTED for wealth as a distinct aggregate.** `calculate_price()`
(`src/systems/economy_systems/market.py`) computes a real buy price from `base_val *
region_mod * building_mod * type_bias` — several real, independent multiplicative influences,
not one universal value. Sell price is a separately-computed, largely static `50%` of base
value plus a regional-trauma surcharge (`docs/mechanics/03_economic_laws.md` §4) — confirming
buy and sell price are not simply inverses of one shared "value," a real asymmetry consistent
with this Rule's own plurality claim. `entity.inventory.gold` (wealth, an aggregate holding) is
tracked entirely separately from any specific item's own price or value. **"Value" to a
specific subject** (as opposed to market price) was not found to have its own dedicated
mechanism distinct from price — recorded as PARTIAL: the Rule's own distinction between price
and subjective value is architecturally available (nothing forces them to be equal), but this
repository does not yet implement a separate subject-relative value computation that could
diverge from price in practice.

**Scenarios:** [ME-S09](../scenarios/material-economy-batch-08.md#me-s09) (price without
objective scarcity), [ME-S10](../scenarios/material-economy-batch-08.md#me-s10) (wealth
converts to capability), [ME-S12](../scenarios/material-economy-batch-08.md#me-s12) (wealth
does not automatically mean power).

---

## Inherited / Applied Foundational Rules

### An exchange's legitimacy and completeness depend on whichever preconditions a domain's own rules declare, never a universal transaction requirement

> What makes a specific exchange legitimate and causally complete (authority, knowledge,
> consent, ownership, reach, resources) is declared per exchange type by the domains that
> govern those preconditions — not one universal set every exchange must satisfy identically.

**Disposition: INHERITED — direct reuse of Capability (CAP-01–05), Authority (AUTH-01–06),
Reach (REACH-01–06), and this batch's own PROP-01 (ownership/possession/access distinctness)
and OWN-04 (proposed ≠ committed state, Batch 01). No new claim: an exchange is simply an
ownership transfer with each side's own preconditions checked, and those preconditions'
plurality is already established by the foundational families named above — stating that
again for "exchange" specifically would restate, not refine.**

**Repository evidence: SUPPORTED.** `docs/mechanics/03_economic_laws.md`'s Market Law
requires, for buying, that the building actually hold the item in stock and the entity have
sufficient gold (a resource/capability precondition); for selling, that the building hold
sufficient liquidity (gold) to pay. Both are real, checked preconditions that gate whether the
`ResourceTransferIntent` the exchange constructs is ever accepted by `src/core/
conservation.py`'s resolver — the same commit-only-if-preconditions-hold pattern OWN-04
already requires, and the same resolver whose `source_kind` dispatch PROP-02 (in
`ownership-possession.md`) already found to reject an unhandled case.

**Scenarios:** none newly traced; reuses the Market Law evidence directly.

### Power/wealth conversion edges are specific, never automatic; the existence of one edge does not imply any other

> Wealth converting into any other form of effective power (capability, protection, influence,
> production) requires its own real, declared conversion mechanism — the existence of one such
> edge never implies any other exists.

**Disposition: INHERITED — direct reuse of Batch 07's PROG-07 (power conversion edges are
specific, never automatic), applied here to wealth specifically. No new claim: PROG-07 already
states the general principle this family's own §9 investigation instantiates for wealth.**

**Repository evidence: SUPPORTED for wealth → capability; MISSING for wealth → protection,
wealth → political influence, and wealth → supply-chain control — checked directly against
each named example, not assumed uniform.** Wealth → capability is real: gold buys equipment
(`BUY_UPGRADE` route family, Batch 06 evidence) and equipment is a real, confirmed capability
channel (Batch 07's PROG-01). **Checked directly, per `docs/brainstorm/
2026-09-19-core-rpg-lived-history-growth-brainstorm.md`'s own verified investigation ("Scenario
B: a poor merchant becomes a power"), cross-checked against source**: `ContractKind.
PROTECTION` exists and is appraised, but is constructed only in `src/certification/
scenarios.py` — confirmed never created by real production gameplay code, DORMANT rather than
live (contrasted with `RECRUITMENT`, which has a real employment cost and is live).
Faction gold vaults (`faction_{id}_gold`) accumulate via taxation but individual wealth never
reaches faction-level decisions — wealth → political influence is confirmed MISSING. No
mechanism translates accumulated wealth into control over a supply chain or resource monopoly
beyond a SimQ-only scoring flag (`faction_monopoly`, not a real mechanism) — confirmed MISSING.

**Scenarios:** [ME-S10](../scenarios/material-economy-batch-08.md#me-s10),
[ME-S12](../scenarios/material-economy-batch-08.md#me-s12).

---

## Scope / Deferred Boundaries

### Universal transaction engine

> This family does not build a universal transaction engine at the semantic level — each
> exchange type's own preconditions remain declared per-domain, per the batch instruction's
> own explicit "do not build a universal transaction engine at the semantic level" instruction.

**Disposition: SCOPE BOUNDARY.**

### Equilibrium / stabilizing counterforces for economic feedback loops

> This family does not require economic feedback loops (scarcity ↔ price ↔ behavior,
> wealth ↔ opportunity) to reach equilibrium or to be stabilized by a declared counterforce —
> open instability is an explicitly legitimate outcome, per the batch instruction's own
> explicit "do not require equilibrium. Open instability remains valid" instruction. This is a
> scope statement about what this family does not require designed, not a world-semantic claim
> in its own right — PROG-05's own "must declare a scaling/limiting stance" requirement
> (Batch 07) still applies to any specific repeatable economic source that exists; this
> boundary only says a *stabilizing* answer is never mandatory.

**Disposition: SCOPE BOUNDARY.**

### Later-domain wealth-conversion downstream semantics

> This family confirms which wealth-conversion edges are real and which are missing, but does
> not design the downstream Social/Politics content those edges would feed (how protection
> translates into safety, how political influence is spent) — those remain future domains.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

- **CONFLICTING — economic decisions read raw registry/world state without a perception gate,
  reconfirming Batch 06's own finding from the market/service side.** See
  `ownership-possession.md`'s own Repository Findings for `ServiceOpportunityProvider`'s own
  evidence — cross-referenced here since it is this family's own decision-making surface
  (shop/service opportunities), not duplicated in full.
- **MISSING — wealth → protection, wealth → political influence, wealth → supply-chain
  control.** See the inherited power-conversion entry above. Of the batch instruction's own six
  named merchant-to-power steps (per the design brainstorm's own verified table), this chain
  breaks earliest of any lived-history trajectory checked across this whole Rule Catalog so
  far — wealth accumulates but has almost nothing real to convert into beyond goods and
  equipment.
- **PARTIAL — "value" to a specific subject has no dedicated mechanism distinct from market
  price.** See EXCH-01 above.

## Cross-domain links recorded here

- EXCH-01 → Resources/Production (`resources-production.md`'s PROD-02, scarcity ≠ price),
  Cost (COST-01, Batch 03)
- Inherited exchange-preconditions entry → Capability, Authority, Reach (Batch 02/03),
  Ownership/Possession (`ownership-possession.md`'s PROP-01)
- Inherited power-conversion entry → Capability/Progression (`capability-progression.md`'s
  PROG-07, Batch 07), History/Provenance (fame/legend tracking, the parallel combat-side
  finding)

## Open questions carried forward

1. Whether this repository should build a real opportunity-seeking mechanism, a real
   protection-market, a real wealth-to-political-influence channel, or a real supply-chain-
   control mechanism is flagged for future batches/tickets (most plausibly Social relations,
   Politics) — not decided here, consistent with this batch's own explicit non-goal against
   designing those downstream semantics.
2. Whether "value" (subject-relative) should gain its own mechanism distinct from market price
   is flagged, not decided here.
