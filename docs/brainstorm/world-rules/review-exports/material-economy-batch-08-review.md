---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Review Export: Batch 08 (Objects / Ownership / Resources / Economy)

**This file is a generated, non-authoritative review view.** It exists so an external reviewer
can assess the batch without opening every canonical file. It is never edited directly as the
fix for a review finding — feedback goes back into the canonical files below, and this export is
regenerated from them. See `world-rules/README.md`'s review index for the current status of
every batch.

## Batch scope

The fifth domain-facing (Milestone B) batch — how material objects, property, resources,
production, scarcity, exchange, and wealth become durable causal parts of individual and world
trajectories. Four rule families: Objects/Material Culture, Ownership/Possession, Resources/
Production, Economy/Exchange. Files live under `material-economy/`, per the batch
instruction's own directory suggestion — no split or merge was found necessary. Built directly
with the strict Rule-admission discipline Batch 07's own follow-up review established (pure
target-semantic Rule statements; every repository fact in Repository evidence/Findings) —
applied from the first draft this time, not as a correction pass.

**Naming note.** This family deliberately uses a `PROP-*` prefix for Ownership/Possession
rather than reusing Batch 01's `OWN-*` — the batch instruction itself stresses "Ownership is
in-world property semantics, not Batch 01 State Ownership," and reusing the same prefix would
have invited exactly the conflation the instruction warns against.

## Canonical files included

- `material-economy/objects-material-culture.md` (OBJ-01, OBJ-02, OBJ-03)
- `material-economy/ownership-possession.md` (PROP-01, PROP-02)
- `material-economy/resources-production.md` (PROD-01, PROD-02)
- `material-economy/economy-exchange.md` (EXCH-01)
- `scenarios/material-economy-batch-08.md` (ME-S01–S16)

## Rule admission accounting

Per the standing admission discipline: a statement earns a new local Rule ID only if it adds or
refines target world semantics beyond Rules already defined elsewhere. This batch's 24 total
catalog entries break down as:

- **8 genuine Domain Rules**: OBJ-01, OBJ-02, OBJ-03; PROP-01, PROP-02; PROD-01, PROD-02;
  EXCH-01.
- **8 Inherited/Applied Foundational Rules** (direct reuse/reconfirmation, no new claim): in
  `objects-material-culture.md` — creation/destruction via real causal path (CAUSE-01, ID-04),
  durability as persistent capability-relevant condition (Batch 07's PROG-01/PROG-03); in
  `ownership-possession.md` — transfer requires a real causal path and proposed≠committed
  state (CAUSE-01, OWN-04), participation ≠ ownership (OWN-02); in `resources-production.md` —
  production creates new identity without preserving input identity (ID-04, CAUSE-01),
  cost-lifecycle for interrupted processes (COST-03); in `economy-exchange.md` — exchange
  preconditions are domain-declared, never universal (CAP-01–05, AUTH-01–06, REACH-01–06,
  this batch's own PROP-01, OWN-04), power/wealth conversion edges are specific (Batch 07's
  PROG-07).
- **8 Scope/Deferred Boundaries** (no world-semantic claim, only a deferral): universal
  first-class-object requirement, `ItemInstance` promotion trigger criteria, in
  `objects-material-culture.md`; Family/Lineage succession eligibility, Law/crime/recovery
  semantics, in `ownership-possession.md`; crafting trees/content catalogs, in
  `resources-production.md`; universal transaction engine, equilibrium/stabilizing
  counterforces, later-domain wealth-conversion downstream semantics, in
  `economy-exchange.md`.

**Genuine new-Rule count for this batch: 8.** **Inherited/reused foundation count: 8 entries,
citing CAUSE-01, ID-04, COST-03, OWN-02, OWN-04, CAP-01–05, AUTH-01–06, REACH-01–06, and this
batch's own reuse of Batch 07's PROG-01, PROG-03, PROG-07** — 12 distinct foundational Rule IDs
outside the AUTH/REACH families, plus those two families' own full member sets.

## Rule Inventory

| ID | Category | Short name | One-line semantic purpose | Status |
|---|---|---|---|---|
| OBJ-01 | Domain Rule | Object Identity ≠ Owner/Holder/Value/Quantity | A sword changing owner does not change which sword it is. | Accepted |
| OBJ-02 | Domain Rule | Fungible Quantity by Default; Promotable to Individual Identity | Graduated boundary; promotion is a declared, opt-in choice. | Accepted (mechanism INERT/OFF) |
| OBJ-03 | Domain Rule | Object-Level Provenance/Significance, Distinct from Entity-Level | An object may accumulate its own historical significance. | Accepted (never realized in practice) |
| PROP-01 | Domain Rule | Ownership/Possession/Custody/Access/Control Are Distinct | A mismatch (illegitimate possession) must be representable. | Accepted (PARTIAL — mismatch confirmed unrepresented) |
| PROP-02 | Domain Rule | Transfer Producer ≠ Transfer Owner | Resolves Batch 01's OWN-05 open question for the object/property side. | Accepted (CONFLICTING implementation) |
| PROD-01 | Domain Rule | Jointly-Necessary, Non-Substitutable Production Inputs | Multiple input categories may be jointly required. | Accepted |
| PROD-02 | Domain Rule | Scarcity ≠ Price/Value/Desire | Real, world-driven; confirmed disconnected from this repo's own pricing. | Accepted (confirmed disconnected) |
| EXCH-01 | Domain Rule | Value ≠ Price ≠ Cost ≠ Wealth, No Universal Value | Price may derive from plural, non-universal influences. | Accepted |

## Inherited Foundations Summary

| Entry (as stated in its own file) | Foundational Rule(s) reused | File |
|---|---|---|
| Object creation/destruction via real causal path, new creation = new identity | CAUSE-01, ID-04 | `objects-material-culture.md` |
| Equipment durability is persistent, capability-relevant condition | PROG-01, PROG-03 (Batch 07) | `objects-material-culture.md` |
| Ownership transfer requires a real causal path and proposed≠committed state | CAUSE-01, OWN-04 | `ownership-possession.md` |
| Participation in producing a change ≠ ownership of the resulting state | OWN-02 | `ownership-possession.md` |
| Production creates new object identity without preserving input identity | ID-04, CAUSE-01 | `resources-production.md` |
| Interrupted process cost has its own declared lifecycle | COST-03 | `resources-production.md` |
| Exchange preconditions are domain-declared, never universal | CAP-01–05, AUTH-01–06, REACH-01–06, PROP-01, OWN-04 | `economy-exchange.md` |
| Power/wealth conversion edges are specific, never automatic | PROG-07 (Batch 07) | `economy-exchange.md` |

## Scenario Inventory

| Scenario ID | Short name | Trajectory | Rule families challenged | Result |
|---|---|---|---|---|
| ME-S01 | Sword Changes Hands | create → own → buy → die → heir | Objects, Ownership | Partial |
| ME-S02 | Possession Without Ownership | theft → possession ≠ ownership | Ownership | Revealed gap |
| ME-S03 | Owner Without Possession | goods owned, stored elsewhere | Ownership | Covered |
| ME-S04 | Shared Access | org controls stock → member partial use | Ownership | Revealed gap |
| ME-S05 | Resource Conversion | ore → production → sword | Resources/Production, Objects (inherited) | Covered |
| ME-S06 | Production Fails After Partial Cost | interrupted → cost incurred → no output | Resources/Production (inherited) | Covered |
| ME-S07 | Scarcity Emerges | depletion → availability falls → pressure | Resources/Production | Covered |
| ME-S08 | Scarcity Without Price Change (counter) | scarcity → no pricing mechanism → exists anyway | Resources/Production | Covered |
| ME-S09 | Price Without Objective Scarcity | belief/institution → price rises, supply unchanged | Economy, Resources/Production | Partial |
| ME-S10 | Wealth Converts to Capability | wealth → equipment → capability | Economy (inherited) | Covered |
| ME-S11 | Theft | non-consensual transfer → possession changes | Ownership | Revealed gap |
| ME-S12 | Wealth Does Not Automatically Mean Power | wealth → no valid path → capability unchanged | Economy (inherited) | Covered |
| ME-S13 | Resource Access but No Ownership | harvest access ≠ owning the source | Ownership | Covered |
| ME-S14 | Ordinary Object Becomes Relic (flagship) | object → events → provenance → recognition | Objects | Revealed missing rule enforcement |
| ME-S15 | Inheritance | death → property persists → succession → transfer | Ownership | Revealed contradiction (CONFLICTING) |
| ME-S16 | Market Feedback (schematic) | scarcity → price/behavior → production → scarcity | Resources/Production, Economy | Blocked |

## Coverage Summary

**Objects/Material Culture**
- object identity ≠ owner/holder/value/quantity — ME-S01
- fungible quantity vs. promotable individual identity, object-level provenance — ME-S05,
  ME-S14

**Ownership/Possession**
- ownership/possession/custody/access/control distinctness — ME-S02, ME-S03, ME-S11, ME-S13
- collective ownership with partial member access — ME-S04
- transfer producer ≠ transfer owner, resolving OWN-05 — ME-S15

**Resources/Production**
- jointly-necessary, non-substitutable inputs — ME-S05
- interrupted-process cost lifecycle — ME-S06
- scarcity is real and world-driven, confirmed disconnected from price — ME-S07, ME-S08, ME-S16

**Economy/Exchange**
- value/price/cost/wealth distinctness, plural price influences — ME-S09
- power/wealth conversion edges are specific — ME-S10, ME-S12

## Deferred Semantics

- No universal first-class-object requirement; `ItemStack`'s fungible default remains
  legitimate.
- `ItemInstance`'s own promotion trigger criteria (what makes an item worth tracking
  individually) are not decided here.
- Family/Lineage succession eligibility (*who* is a valid heir) stays with a future domain;
  this batch owns only the resulting property relation.
- Law/crime/recovery semantics for illegitimate possession stay deferred.
- Crafting trees/content catalogs are not designed here.
- No universal transaction engine, no required equilibrium for economic feedback loops, and
  later-domain wealth-conversion downstream semantics (Social/Politics) all stay deferred.

## Cross-domain findings

- Objects/Ownership ↔ History/Provenance: OBJ-03's object-level provenance/significance claim
  is a genuinely new category alongside HP-01/HP-04/HP-05's subject-level claims, not a
  restatement of them — the first time this Rule Catalog has addressed provenance for a
  non-entity subject.
- Ownership ↔ State Ownership (Batch 01): PROP-02 is this batch's own resolution of OWN-05's
  own carried-forward open question ("succession's property/wealth transfer... deferred
  jointly")  — and the resolution immediately surfaced a real implementation defect
  (the `"CHEST"` resolver gap), making this one of the highest-value cross-domain resolutions
  this Catalog has produced, because verifying the resolution's own repository evidence is what
  found the bug.
- Resources/Production ↔ Perception/Knowledge (Batch 06) ↔ Economy: PROD-02's confirmed
  scarcity/price disconnection and `ServiceOpportunityProvider`'s confirmed perception-bypass
  (Repository Finding, `ownership-possession.md`) are two independent but related findings
  about this repository's economic decision-making surface reading raw world/registry state
  rather than any subject-local, causally-connected representation.
- Economy/Exchange ↔ Capability/Progression (Batch 07): the inherited power/wealth-conversion
  entry directly parallels PROG-07's own combat/fame-side finding — of the two conversion
  chains this Rule Catalog has now checked (combat→fame→influence, wealth→protection→
  influence), both break at the same downstream point (political/social influence), a real,
  recurring pattern worth a future owner's attention.

**Explicit call-out — genuine Domain Rule count:** **8.**

**Explicit call-out — object identity vs. resource representation:** Object identity
(`ItemInstance`, opt-in) and resource-quantity representation (`ItemStack`, default) coexist
without collapsing — OBJ-01/OBJ-02. The promotion boundary between them is real and
well-designed but never exercised in production (confirmed INERT/OFF).

**Explicit call-out — ownership vs. possession/access/control:** Distinct in principle
(PROP-01); collapsed to inventory-location in practice for the general (non-`ItemInstance`)
case; a legitimate-owner/current-possessor mismatch (theft) is confirmed unrepresentable
anywhere in this repository.

**Explicit call-out — whether inheritance transfers real property:** **No — confirmed
CONFLICTING, the single most significant finding in this batch.** The heirloom-transfer intent
is constructed with `source_kind="CHEST"`, which `src/core/conservation.py`'s resolver does
not handle, rejecting every such transfer with `UNKNOWN_SOURCE_KIND`. Property persists as a
generically-lootable corpse; it never actually reaches the resolved heir.

**Explicit call-out — whether scarcity derives from real world state:** **Yes, confirmed.**
`ResourceNodeState.remaining_charges` depletes from real harvest events and feeds real
downstream route-scoring consequences.

**Explicit call-out — whether prices have causal inputs:** **Yes, but not from scarcity.**
`calculate_price()`'s multiplier chain (`region_mod`/`building_mod`/`type_bias`) is real and
causal, but every write site for those modifiers is static/authored content — never computed
from actual resource depletion. Scarcity and price are confirmed disconnected.

**Explicit call-out — whether wealth has meaningful conversion edges:** **One real edge
(wealth → equipment → capability); three confirmed MISSING (protection, political influence,
supply-chain control).** Of every lived-history conversion chain this Rule Catalog has traced
so far, wealth's own breaks earliest.

**Explicit call-out — whether economic agents use omniscient information:** **Yes, confirmed
CONFLICTING, reconfirming Batch 06's own pattern from the market/service side.**
`ServiceOpportunityProvider.get_opportunities()` reads `ServiceRegistry.all()` filtered only by
region, with no `PerceptionGate` check — the same active-violation shape as Batch 06's
`ResourceOpportunityProvider`/`HarvestScorer`.

**Explicit call-out — whether objects can acquire provenance/significance:** **Permitted by a
real, fully-wired mechanism (`ItemInstance`); never realized in practice** — gated
`ENABLE_ITEM_INSTANCE_HISTORY` OFF, and zero production call sites ever set
`significant=True`.

**Explicit call-out — which economic/material state is causally inert:** `ItemInstance`'s own
provenance-tracking mechanism (INERT/OFF, both flag-gated and never-triggered);
`faction_{id}_gold` vaults (accumulate, never spent by members); `ContractKind.PROTECTION`
(DORMANT, certification-only).

**Explicit call-out — whether an ordinary object can causally become a relic:** **Permitted by
the target Rules; never realized by the current repository** — see ME-S14 and OBJ-03's own
evidence. The mirror image of Batch 07's own non-HERO-significance finding, on the object side
rather than the individual-entity side.

## Repository Findings

Classified per the CONFLICTING/INERT-OFF/MISSING distinction Batch 06/07 established.

**CONFLICTING (2 findings):**
1. **The single most significant finding in this whole batch.** The heirloom-transfer
   mechanism constructs a real `ResourceTransferIntent(source_kind="CHEST")` that
   `src/core/conservation.py`'s resolver has no handler for, rejecting it with
   `UNKNOWN_SOURCE_KIND` every time. See PROP-02.
2. `ServiceOpportunityProvider.get_opportunities()` reads raw `ServiceRegistry` state with no
   perception gate — an active violation of Batch 06's own PERC-01 default, reconfirming the
   same pattern found for resource opportunities.

**INERT/OFF (2 findings):**
3. `ItemInstance`'s provenance/significance mechanism is fully wired but gated
   `ENABLE_ITEM_INSTANCE_HISTORY` (default OFF) and never triggered (`significant=True` set
   nowhere in production).
4. `ContractKind.PROTECTION` exists and is appraised but constructed only in
   `src/certification/scenarios.py`, never real production gameplay code.

**MISSING (4 findings):**
5. No theft/illegitimate-possession representation exists anywhere.
6. No individual member access to collective/organizational wealth exists — faction vaults
   accumulate, never spent.
7. No wealth → political-influence or wealth → supply-chain-control conversion edge exists.
8. No mechanism computes `price_modifiers` from real scarcity/depletion data — price and
   scarcity are confirmed disconnected mechanisms.

**Not classified under the three-way distinction (an architecture/documentation observation):**
9. "Value" to a specific subject (as opposed to market price) has no dedicated mechanism —
   architecturally permitted to diverge from price, but this repository does not yet implement
   a separate computation that could.

Key evidence, all confirmed by direct code/doc inspection: `docs/mechanics/
03_economic_laws.md`, `src/core/state.py` (`ItemStack`, `ItemInstance`, home storage),
`src/engine/apply_plan.py` (corpse creation), `src/systems/lifecycle_systems/lifecycle.py`
(heirloom transfer), `src/core/conservation.py` (the `source_kind` resolver dispatch),
`src/systems/economy_systems/market.py` (`calculate_price`), `src/world/
regional_sovereignty.py` (`faction_{id}_gold`), `src/world/providers/services.py`
(`ServiceOpportunityProvider`), `docs/brainstorm/
2026-09-19-core-rpg-lived-history-growth-brainstorm.md` (Scenario B, cross-checked against
source for `ContractKind.PROTECTION`).

## Owner-attention decisions

- **Highest priority.** Whether to fix the heirloom-transfer resolver gap (add a `"CHEST"`
  handler, or route the transfer through an already-handled `source_kind` such as `CORPSE`) —
  a confirmed, real defect in a mechanism that otherwise looks complete.
- Whether `ENABLE_ITEM_INSTANCE_HISTORY` should be turned on, and what should trigger
  `significant=True` in production.
- Whether theft/illegitimate-possession should gain its own representable state.
- Whether individual members should gain real access to collective/organizational wealth.
- Whether `price_modifiers` should ever be computed from real scarcity/depletion data.
- Whether wealth should gain a real protection/political-influence/supply-chain conversion
  edge, and whether `ServiceOpportunityProvider` should be re-scoped through perception.

## Candidate disposition

Eight Domain Rules were drafted across four families (3 Objects/Material Culture, 2
Ownership/Possession, 2 Resources/Production, 1 Economy/Exchange) — **all 8 accepted, 0
rejected, 0 split, 0 merged.** No target rule count was set in advance. Eight further entries
were identified as Inherited/Applied Foundational Rules and eight as Scope/Deferred
Boundaries — none required a new Rule ID, and none represents lost work.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/material-economy-batch-08-report.md` (local review report, not part of this catalog).

---

> **BATCH 08 (OBJECTS / OWNERSHIP / RESOURCES / ECONOMY) READY FOR HIGH-LEVEL EXTERNAL
> REVIEW.**

All required artifacts exist: four rule-family files (8 genuine Domain Rules; 24 total
catalog entries), one scenario file (16 scenarios covering all sixteen required seed probes),
this review export with all required sections plus every explicitly-required call-out, and a
local disposition report. No contradiction was found against any prior batch — this batch's
own genuinely new material is concentrated in one confirmed CONFLICTING implementation defect
(the heirloom-transfer resolver gap, PROP-02) and one confirmed INERT/OFF mechanism
(`ItemInstance` provenance tracking, OBJ-02/03), both structurally identical in shape to
findings prior batches already established elsewhere, plus a reconfirmation of Batch 06's own
omniscient-economic-decision pattern. All thirteen of the batch instruction's own
stop-condition checklist items are satisfied: object identity and resource quantity are
clearly distinguished; ownership/possession/access/control are not collapsed (though the
general case's own collapse-in-practice is honestly recorded); transfer semantics have valid
causal ownership updates in principle, with a confirmed real defect named rather than
smoothed over; production/conversion semantics preserve appropriate provenance; scarcity is
distinct from price/value (and confirmed disconnected in practice); wealth matters only
through real conversion paths, most of which are confirmed missing; inheritance's property
side is semantically clear even though the implementation is broken; theft/non-owner
possession is representable *in principle* by this Rule Catalog's own semantics, even though
this repository does not yet implement it; economic decisions were checked against Knowledge/
Agency boundaries and a real violation was found and classified correctly; material/economic
state with no consumer is identified; object lived-history/significance has been probed;
aggregate economic behavior's entity-facing consequences were traced; genuine Rules remain
separated from repository findings.

Do not begin Batch 09 (Social Relations / Family / Lineage) until this batch receives
high-level review.
