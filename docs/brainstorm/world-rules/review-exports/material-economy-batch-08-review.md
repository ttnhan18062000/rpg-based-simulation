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
Production, Economy/Exchange. Drafted 2026-09-22, then revised the same day per a targeted
semantic cleanup (`tmp/world-rule-batch-8-followup-ext-ai.md`) — see "Follow-up revision
summary" below.

## Follow-up revision summary (2026-09-22)

A targeted semantic cleanup was applied without redesigning the batch or discarding any major
repository finding:

1. **OBJ-02 reframed.** No longer describes a specific promotion *mechanism* (`ItemStack` →
   `ItemInstance`) as the normative content; now states the underlying semantic distinction
   (fungible-quantity vs. identity-bearing representation is a legitimate world choice) and
   adds a substantive requirement the original draft only implied: meaningful provenance from
   the source material must remain traceable across individuation. Does not establish that
   material things are universally fungible by default.
2. **OBJ-03 reclassified from a Domain Rule to Inherited.** Checked directly against History/
   Provenance's own scope: HP-02 already names "artifact" (not entity) alongside "fact" and
   "record" as things whose provenance must be traceable, and HP-05's significance-fading
   claim uses fully generic language. Both already apply to any first-class simulation
   subject, not entities alone — "an object can accumulate history/significance" is HP-02/
   HP-05 applied at Objects' own point of use, not genuinely new content. The flagship
   trajectory (ordinary object → historically important events → recognized relic) remains
   fully supported by this reclassification.
3. **PROP-02 reclassified from a Domain Rule to Inherited.** Its claim ("the durable property
   relation has an authoritative owner independent of whichever process caused the transfer")
   is Batch 01's OWN-01/OWN-02 applied at Ownership's own point of use. The broken
   heirloom-transfer implementation is kept entirely as a CONFLICTING Repository Finding
   attached to that Inherited entry, per the follow-up's own explicit instruction, not folded
   into any Rule's own wording.
4. **PROD-01 generalized.** No longer requires production inputs to be jointly-necessary and
   non-substitutable; now permits a process to declare whichever inputs/conditions it needs,
   including any allowed substitution semantics — the only fixed requirement is that a
   declared-required input may never be silently omitted.
5. **PROD-02 confirmed already clean** — its own quoted Rule statement did not contain
   repository-evaluation language; the "confirmed disconnected" finding was already correctly
   isolated to Repository evidence.
6. **Two adversarial probes added:** ME-S17 (Individuation From Fungible Material) and ME-S18
   (Production With Substitutable Inputs) — confirming the revised OBJ-02/PROD-01 are
   correctly permissive rather than over-restrictive.
7. **World Rule decisions kept explicitly separate from implementation findings**: each rule
   family's Repository Findings section now opens with a one-line statement that findings
   report repository/implementation facts, not World Rule decisions, and that acting on them is
   implementation planning's own call.
8. **Both project-level conclusions preserved, not weakened**: "can an ordinary object become
   historically significant?" — YES in World Rule semantics, PARTIAL/unrealized in the current
   repository; "wealth only becomes power through concrete causal conversion edges" — one real
   edge confirmed, three confirmed absent.

## Canonical files included

- `material-economy/objects-material-culture.md` (OBJ-01, OBJ-02 — Domain Rules)
- `material-economy/ownership-possession.md` (PROP-01 — Domain Rule)
- `material-economy/resources-production.md` (PROD-01, PROD-02 — Domain Rules)
- `material-economy/economy-exchange.md` (EXCH-01 — Domain Rule)
- `scenarios/material-economy-batch-08.md` (ME-S01–S18)

## Rule admission accounting

Per the standing admission discipline: a statement earns a new local Rule ID only if it adds or
refines target world semantics beyond Rules already defined elsewhere. Post-follow-up, this
batch's 23 total catalog entries break down as:

- **6 genuine Domain Rules**: OBJ-01, OBJ-02; PROP-01; PROD-01, PROD-02; EXCH-01.
- **9 Inherited/Applied Foundational Rules** (3 in `objects-material-culture.md`, up from 2 —
  the reclassified HP-02/HP-05 entry, formerly OBJ-03; 2 in `ownership-possession.md`,
  unchanged in count — the reclassified OWN-01/OWN-02 entry, formerly PROP-02, replacing the
  prior generic participation-≠-ownership bullet; 2 in `resources-production.md`, unchanged; 2
  in `economy-exchange.md`, unchanged): object-level provenance/significance is HP-02/HP-05
  applied here, object creation/destruction via a real causal path (CAUSE-01, ID-04), and
  equipment durability as a persistent capability-relevant condition (Batch 07's PROG-01/
  PROG-03), in `objects-material-culture.md`; the durable property relation has an
  authoritative owner independent of the transfer's producer (OWN-01, OWN-02), a transfer
  requires a real causal path (CAUSE-01), in `ownership-possession.md`; production creates new
  identity without preserving input identity (ID-04, CAUSE-01), interrupted-process
  cost-lifecycle (COST-03), in `resources-production.md`; exchange preconditions are
  domain-declared (CAP-01–05, AUTH-01–06, REACH-01–06, PROP-01, OWN-04), power/wealth
  conversion edges are specific (Batch 07's PROG-07), in `economy-exchange.md`.
- **8 Scope/Deferred Boundaries** (unchanged by the follow-up): universal first-class-object
  requirement, `ItemInstance` promotion trigger criteria, in `objects-material-culture.md`;
  Family/Lineage succession eligibility, Law/crime/recovery semantics, in
  `ownership-possession.md`; crafting trees/content catalogs, in `resources-production.md`;
  universal transaction engine, equilibrium/stabilizing counterforces, later-domain
  wealth-conversion downstream semantics, in `economy-exchange.md`.

**Genuine new-Rule count for this batch: 6** (was 8 before the follow-up reclassified OBJ-03
and PROP-02 to Inherited). **Inherited/reused foundation count: 9 entries, citing CAUSE-01,
ID-04, COST-03, OWN-01, OWN-02, OWN-04, HP-02, HP-05, CAP-01–05, AUTH-01–06, REACH-01–06, and
this batch's own reuse of Batch 07's PROG-01, PROG-03, PROG-07.**

## Rule Inventory

| ID | Category | Short name | One-line semantic purpose | Status |
|---|---|---|---|---|
| OBJ-01 | Domain Rule | Object Identity ≠ Owner/Holder/Value/Quantity | A sword changing owner does not change which sword it is. | Accepted |
| OBJ-02 | Domain Rule | Fungible-or-Individuated Representation; Provenance Must Survive Individuation | A world choice, not a universal-fungible default; provenance requirement added. | Accepted, revised |
| PROP-01 | Domain Rule | Ownership/Possession/Custody/Access/Control Are Distinct | A mismatch (illegitimate possession) must be representable. | Accepted (PARTIAL — mismatch confirmed unrepresented) |
| PROD-01 | Domain Rule | Production Declares Its Own Inputs/Conditions, Including Substitution Semantics | Generalized; required inputs cannot be silently omitted. | Accepted, revised |
| PROD-02 | Domain Rule | Scarcity ≠ Price/Value/Desire | Real, world-driven; confirmed disconnected from this repo's own pricing. | Accepted (confirmed disconnected) |
| EXCH-01 | Domain Rule | Value ≠ Price ≠ Cost ≠ Wealth, No Universal Value | Price may derive from plural, non-universal influences. | Accepted |

## Inherited Foundations Summary

| Entry (as stated in its own file) | Foundational Rule(s) reused | File |
|---|---|---|
| Object-level provenance/significance (formerly OBJ-03) | HP-02, HP-05 | `objects-material-culture.md` |
| Object creation/destruction via real causal path, new creation = new identity | CAUSE-01, ID-04 | `objects-material-culture.md` |
| Equipment durability is persistent, capability-relevant condition | PROG-01, PROG-03 (Batch 07) | `objects-material-culture.md` |
| Durable property relation has an authoritative owner independent of the transfer producer (formerly PROP-02) | OWN-01, OWN-02 | `ownership-possession.md` |
| An ownership transfer requires a real causal path | CAUSE-01 | `ownership-possession.md` |
| Production creates new object identity without preserving input identity | ID-04, CAUSE-01 | `resources-production.md` |
| Interrupted process cost has its own declared lifecycle | COST-03 | `resources-production.md` |
| Exchange preconditions are domain-declared, never universal | CAP-01–05, AUTH-01–06, REACH-01–06, PROP-01, OWN-04 | `economy-exchange.md` |
| Power/wealth conversion edges are specific, never automatic | PROG-07 (Batch 07) | `economy-exchange.md` |

## Scenario Inventory

| Scenario ID | Short name | Trajectory | Rule families challenged | Result |
|---|---|---|---|---|
| ME-S01 | Sword Changes Hands | create → own → buy → die → heir | Objects, Ownership (inherited) | Partial |
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
| ME-S14 | Ordinary Object Becomes Relic (flagship) | object → events → provenance → recognition | Objects (inherited HP-02/HP-05) | Revealed missing rule enforcement |
| ME-S15 | Inheritance | death → property persists → succession → transfer | Ownership (inherited) | Revealed contradiction (CONFLICTING) |
| ME-S16 | Market Feedback (schematic) | scarcity → price/behavior → production → scarcity | Resources/Production, Economy | Blocked |
| ME-S17 | Individuation From Fungible Material (added) | stack → one portion individuated → own history | Objects | Covered by permission; MISSING by exercise |
| ME-S18 | Production With Substitutable Inputs (added) | material A unavailable → declared substitute B → valid | Resources/Production | Covered by permission; not exercised |

## Coverage Summary

**Objects/Material Culture**
- object identity ≠ owner/holder/value/quantity — ME-S01
- fungible-or-individuated representation, provenance-through-individuation — ME-S05, ME-S17
- object-level provenance/significance (inherited HP-02/HP-05) — ME-S14

**Ownership/Possession**
- ownership/possession/custody/access/control distinctness — ME-S02, ME-S03, ME-S11, ME-S13
- collective ownership with partial member access — ME-S04
- authoritative owner independent of transfer producer (inherited) — ME-S15

**Resources/Production**
- production declares its own inputs/conditions, including substitution — ME-S05, ME-S18
- interrupted-process cost lifecycle — ME-S06
- scarcity is real and world-driven, confirmed disconnected from price — ME-S07, ME-S08, ME-S16

**Economy/Exchange**
- value/price/cost/wealth distinctness, plural price influences — ME-S09
- power/wealth conversion edges are specific (inherited) — ME-S10, ME-S12

## Deferred Semantics

- No universal first-class-object requirement; `ItemStack`'s fungible default remains
  legitimate — and, per the follow-up, this is now explicitly not framed as a universal-
  fungible-by-default claim either.
- `ItemInstance`'s own promotion trigger criteria are not decided here.
- Family/Lineage succession eligibility, Law/crime/recovery semantics for illegitimate
  possession, crafting trees/content catalogs, universal transaction engine, required
  equilibrium for economic feedback loops, and later-domain wealth-conversion downstream
  semantics all stay deferred, unchanged by the follow-up.

## Cross-domain findings

- Objects/Ownership ↔ History/Provenance: the reclassification of OBJ-03 is the cleanest
  example in this batch of the admission discipline working correctly on a second pass — a
  claim that felt locally important on first draft, but that checking History/Provenance's own
  actual scope (HP-02 explicitly names "artifact") showed was already covered.
- Ownership ↔ State Ownership (Batch 01): the reclassified PROP-02 entry preserves this
  batch's own resolution of OWN-05's carried-forward open question (which domain owns the
  property relation after a death-triggered transfer) as Repository-evidence-bearing
  Inherited content — the resolution's own value (finding the `"CHEST"` resolver gap) survives
  the reclassification untouched.
- Resources/Production: PROD-01's generalization directly parallels Batch 07's PROG-05
  ("repeatable sources must declare their scaling/limiting semantics, unlimited must not arise
  accidentally") — both moved from a specific restrictive shape to a declared-choice
  permission during their own follow-up review, the same corrective pattern applied twice now.
- Economy/Exchange ↔ Capability/Progression (Batch 07): the inherited power/wealth-conversion
  entry directly parallels PROG-07's own combat/fame-side finding — unchanged by this
  follow-up.

**Explicit call-out — genuine Domain Rule count:** **6** (was 8 before the follow-up).

**Explicit call-out — object identity vs. resource representation:** Object identity
(individuated, `ItemInstance`) and resource-quantity representation (`ItemStack`, default)
coexist without collapsing — OBJ-01/OBJ-02. OBJ-02 no longer claims fungibility is universal
by default; it states the choice is a world's own to make, with provenance required to survive
individuation when it occurs.

**Explicit call-out — ownership vs. possession/access/control:** Distinct in principle
(PROP-01); collapsed to inventory-location in practice for the general case; a legitimate-
owner/current-possessor mismatch (theft) is confirmed unrepresentable anywhere in this
repository.

**Explicit call-out — whether inheritance transfers real property:** **No — confirmed
CONFLICTING, the single most significant finding in this batch, unchanged by the follow-up.**
The heirloom-transfer intent is constructed with `source_kind="CHEST"`, which `src/core/
conservation.py`'s resolver does not handle, rejecting every such transfer with
`UNKNOWN_SOURCE_KIND`. This is a repository/implementation finding, not a World Rule
decision — the target semantics (a durable property relation has an authoritative owner
independent of the transfer's producer) remain coherent and are now correctly filed as
Inherited rather than a new Rule.

**Explicit call-out — whether scarcity derives from real world state:** **Yes, confirmed.**

**Explicit call-out — whether prices have causal inputs:** **Yes, but not from scarcity** —
confirmed disconnected, unchanged by the follow-up.

**Explicit call-out — whether wealth has meaningful conversion edges:** **One real edge
(wealth → equipment → capability); three confirmed MISSING (protection, political influence,
supply-chain control).** Preserved project-level conclusion: wealth only becomes power through
concrete causal conversion edges.

**Explicit call-out — whether economic agents use omniscient information:** **Yes, confirmed
CONFLICTING**, unchanged by the follow-up.

**Explicit call-out — whether objects can acquire provenance/significance:** **Preserved
project-level conclusion: YES in World Rule semantics (now via History/Provenance's own
HP-02/HP-05, correctly filed as Inherited rather than a new Objects-specific Rule) — PARTIAL/
unrealized in the current repository.**

**Explicit call-out — which economic/material state is causally inert:** unchanged by the
follow-up — `ItemInstance`'s provenance-tracking mechanism, `faction_{id}_gold` vaults,
`ContractKind.PROTECTION`.

**Explicit call-out — whether an ordinary object can causally become a relic:** see the
preserved project-level conclusion above.

## Repository Findings

Classified per the CONFLICTING/INERT-OFF/MISSING distinction Batch 06/07 established. **These
are repository/implementation facts, not World Rule decisions** — the Rules and Inherited
entries above state what this batch's own target semantics require and permit; the findings
below report where this repository's own current implementation does or does not realize them.
Whether and how to act on any of them is implementation planning's own call, not this Rule
Catalog's.

**CONFLICTING (2 findings, unchanged by the follow-up):**
1. **The single most significant finding in this whole batch.** The heirloom-transfer
   mechanism constructs a real `ResourceTransferIntent(source_kind="CHEST")` that `src/core/
   conservation.py`'s resolver has no handler for, rejecting it with `UNKNOWN_SOURCE_KIND`
   every time.
2. `ServiceOpportunityProvider.get_opportunities()` reads raw `ServiceRegistry` state with no
   perception gate.

**INERT/OFF (2 findings, unchanged):**
3. `ItemInstance`'s provenance/significance mechanism is fully wired but gated
   `ENABLE_ITEM_INSTANCE_HISTORY` (default OFF) and never triggered.
4. `ContractKind.PROTECTION` exists and is appraised but constructed only in certification
   fixtures.

**MISSING (4 findings, unchanged):**
5. No theft/illegitimate-possession representation exists anywhere.
6. No individual member access to collective/organizational wealth exists.
7. No wealth → political-influence or wealth → supply-chain-control conversion edge exists.
8. No mechanism computes `price_modifiers` from real scarcity/depletion data.

**Not classified under the three-way distinction:**
9. "Value" to a specific subject has no dedicated mechanism distinct from market price.

Key evidence, all confirmed by direct code/doc inspection: `docs/mechanics/
03_economic_laws.md`, `src/core/state.py`, `src/engine/apply_plan.py`,
`src/systems/lifecycle_systems/lifecycle.py`, `src/core/conservation.py`,
`src/systems/economy_systems/market.py`, `src/world/regional_sovereignty.py`,
`src/world/providers/services.py`, `docs/brainstorm/
2026-09-19-core-rpg-lived-history-growth-brainstorm.md`.

## Owner-attention decisions

Unchanged by the follow-up — see the batch's own original list: fixing the heirloom-transfer
resolver gap (highest priority); `ENABLE_ITEM_INSTANCE_HISTORY` and its trigger criteria;
theft/illegitimate-possession representation; collective-wealth member access;
scarcity-driven `price_modifiers`; wealth → protection/political-influence/supply-chain
conversion edges; re-scoping `ServiceOpportunityProvider` through perception.

## Candidate disposition

Six Domain Rules survive the follow-up's stricter re-examination across four families (2
Objects/Material Culture, 1 Ownership/Possession, 2 Resources/Production, 1 Economy/
Exchange) — **all 6 accepted, 0 rejected.** Two Domain Rules from the original draft (OBJ-03,
PROP-02) were reclassified to Inherited; two others (OBJ-02, PROD-01) were generalized rather
than reclassified or dropped. No target-semantic contradiction was introduced by any of these
changes — every reclassification narrowed the Domain Rule count without discarding a single
piece of evidence, scenario result, or cross-domain link; every generalization widened a
Rule's own permission without removing any repository finding attached to it. Nine
Inherited/Applied Foundational Rules and eight Scope/Deferred Boundaries round out the 23
total catalog entries.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/material-economy-batch-08-report.md` (local review report, not part of this catalog).

---

> **BATCH 08 PASS — READY TO FREEZE.**

All required artifacts exist: four rule-family files (6 genuine Domain Rules; 23 total
catalog entries), one scenario file (18 scenarios covering all sixteen required seed probes
plus two follow-up-required additions), this review export with all required sections plus
every explicitly-required call-out, and a local disposition report. No target-semantic
contradiction was introduced by the follow-up's own reclassifications or generalizations — each
one either narrowed which statements carry a local Rule ID (OBJ-03, PROP-02 → Inherited) or
widened a Rule's own permission (OBJ-02, PROD-01), without changing what any Rule requires of
the world and without discarding any repository finding. All thirteen of the batch
instruction's own original stop-condition checklist items remain satisfied, several sharpened
rather than weakened: object identity and resource quantity are clearly distinguished, with
the fungible/individuated boundary now stated as a world choice rather than a default;
ownership/possession/access/control are not collapsed, with the general case's own
collapse-in-practice honestly recorded; transfer semantics have a clear authoritative-owner
requirement, with a confirmed real defect named rather than smoothed over; production/
conversion semantics preserve appropriate provenance, now explicitly required across
individuation too; scarcity is distinct from price/value and confirmed disconnected in
practice; wealth matters only through real conversion paths, most confirmed missing;
inheritance's property side is semantically clear even though the implementation is broken;
theft/non-owner possession is representable in principle, even though unimplemented; economic
decisions were checked against Knowledge/Agency boundaries and a real violation was found;
material/economic state with no consumer is identified; object lived-history/significance has
been probed and both preserved project-level conclusions remain intact; aggregate economic
behavior's entity-facing consequences were traced; genuine Rules remain separated from
repository findings, now under a stricter reading than the first draft applied.

Proceed to Batch 09 (Social Relations / Family / Lineage).
