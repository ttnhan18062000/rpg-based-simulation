---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Ownership / Possession

**Purpose/scope.** What it means for a subject to own, possess, control, store, borrow,
occupy, or merely have access to something, and what makes an ownership transfer valid.
Ownership here is in-world property semantics — distinct from Batch 01's State Ownership
(which governs how the *simulation's own authoritative durable state* is canonically owned by
one domain, a substrate-level architecture concern, not an in-world property fact). This
family therefore uses its own `PROP-*` prefix rather than reusing Batch 01's `OWN-*`, to keep
the two categorically different concepts from being read as the same family.

**Status.** Batch 08 (Objects/Ownership/Resources/Economy), first draft. Candidates below
originated as external-reviewer hypotheses (`tmp/world-rule-batch-8-ext-ai.md`); each carries
this session's disposition and repository evidence. Structured per the normalized five-category
methodology.

---

## Domain Rules

## PROP-01 — Ownership, possession, custody, access, and control are distinct, independently-trackable facts; a mismatch between them (illegitimate possession) must be representable

> Ownership, possession, custody, access, and control are separate facts about a subject's
> relationship to an object or resource — none automatically implies any other. A subject may
> possess something it does not own (a borrower, a thief); a subject may own something it does
> not possess (goods stored elsewhere); a collective (an organization, an institution) may own
> a resource that no single member personally owns in full, while individual members hold
> partial access to it. A world must be able to represent a mismatch between legitimate
> ownership and current possession, not merely infer ownership from wherever an object
> currently sits.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule states this plurality of
property-relationship concepts or requires that a legitimate-owner/current-possessor mismatch
be representable — this is genuinely new content, directly required by the batch instruction's
own §3/§13.

**Repository evidence: PARTIAL — the plurality is representable in principle and realized for
one real case; collapsed to inventory-location for the general case; theft/mismatch is
confirmed unrepresented.** `HomeStorageService`'s private, access-controlled storage
(`docs/mechanics/03_economic_laws.md` §6 — "only the owning entity can deposit or withdraw... only
accessible when physically present at home coordinates") is a real, clean instance of
ownership and possession/location being separate facts about the same goods. `ItemInstance.
owner_history` (OBJ-01/02) is a second, real (if never-triggered) instance. **For the general
case, checked directly: an ordinary `ItemStack` entry carries no ownership metadata of its own
at all** — for any item without a promoted `ItemInstance`, "who owns it" is not a tracked fact
separate from "whose inventory list currently contains it." **Confirmed MISSING: no theft/
illegitimate-possession representation exists anywhere** — no code path flags a transferred
item as taken without the legitimate owner's consent, and no mechanism records that a current
possessor is not the legitimate owner. A stolen item is, today, indistinguishable in this
repository's own state from a legitimately-traded one. **Confirmed MISSING: no organizational/
collective ownership with partial member access exists** — `faction_{id}_gold`
(`src/world/regional_sovereignty.py`) is a real, accumulating per-faction vault (filled by
taxation), but checked directly: no individual member ever withdraws from or spends it — the
"member may use some portion, does not own the entire stock" half of collective ownership is
confirmed absent.

**Scenarios:** [ME-S02](../scenarios/material-economy-batch-08.md#me-s02) (possession without
ownership), [ME-S03](../scenarios/material-economy-batch-08.md#me-s03) (owner without
possession), [ME-S04](../scenarios/material-economy-batch-08.md#me-s04) (shared access),
[ME-S11](../scenarios/material-economy-batch-08.md#me-s11) (theft), [ME-S13](../scenarios/material-economy-batch-08.md#me-s13)
(resource access but no ownership).

---

## PROP-02 — The producer of an ownership-changing event is not automatically the owner of the resulting ownership relation

> Whatever event triggers an ownership change (a death, a trade, a gift, a confiscation) is
> the *producer* of that change, not automatically its *owner* — the resulting property
> relation is owned by whichever domain's own rules govern property relations, regardless of
> which domain's own event triggered the change.

**Disposition: ACCEPT.** Passes the admission test: this resolves Batch 01's own OWN-05 open
question ("succession's property/wealth transfer... deferred across Family/Lineage, Politics,
and Objects/Economy jointly... whichever of those three domain batches is reached first should
cite this rather than deciding it alone") specifically for the object/property side, which the
batch instruction's own §12 explicitly assigns to this batch. Resolving a previously-deferred
open question with a real, citable answer is new content, per the same precedent Batch 05's
BODY-07 and Batch 06's several resolutions already established — not a bare restatement of
OWN-02 (Batch 01's general "participation ≠ ownership" claim), which does not by itself say
*which* domain owns the resulting state when death is the trigger.

**Repository evidence: CONFLICTING — a real, load-bearing finding: this repository's own
implementation actively constructs an ownership-transfer intent that its own resolver
rejects, meaning the resulting property relation is never actually committed by anyone.** The
single most significant finding in this whole batch. `LifecycleSystem`'s "Transactional
Heirloom Transfer" (`src/systems/lifecycle_systems/lifecycle.py`) resolves a real heir
(`entity.lifecycle.heir_entity_id`, or a computed default heir), combines the deceased entity's
own inventory with any declared `heirlooms`, and constructs a real
`ResourceTransferIntent(source_id=entity.id, source_kind="CHEST", transfer_kind="AUTO",
items_add=all_transfer_items)` attached to the heir's own `EntityUpdate.resource_transfers`.
This looks, from the producer side, like a complete inheritance mechanism. **Checked directly
against the actual resolver, `src/core/conservation.py`: its `source_kind` dispatch handles
`NODE`, `GROUND_ITEM`, `CORPSE`, `CRAFTING`, `SHOP_BUY`, `SHOP_SELL`, `COMBAT`, `QUEST`, and
`HOME_STORAGE` — there is no `"CHEST"` branch. Every heirloom-transfer intent falls through to
the resolver's own final `return TransactionResult(accepted=False, reason=ReasonCode.
UNKNOWN_SOURCE_KIND)`.** The heir never actually receives the inventory or heirlooms — the
transaction is rejected and, per the Atomic Conservation Law's own rollback guarantee, produces
no state change at all. Meanwhile, `CorpseState.items` (`src/engine/apply_plan.py`) is
independently snapshotted from the *same* (unmodified) `entity.inventory.items` at the moment
of death and becomes generically lootable by any entity that interacts with the corpse — so
this repository's own actual behavior on death is exactly the generic-loot path Family/
Lineage's own succession-eligibility determination has no bearing on, not the heir-specific
transfer the code's own construction implies. This is classified CONFLICTING rather than
MISSING: the code actively attempts a specific transaction that its own conservation-path
resolver actively rejects — a real, live mismatch between two parts of this repository's own
implementation, not an absent feature.

**Scenarios:** [ME-S15](../scenarios/material-economy-batch-08.md#me-s15) (inheritance).

---

## Inherited / Applied Foundational Rules

### An ownership transfer requires a real causal path and a distinct proposed-vs-committed state

> A transfer of ownership must trace to a real cause, and the transfer's own intended change is
> not itself the committed authoritative state until it actually applies through the
> authoritative path.

**Disposition: INHERITED — direct reuse of CAUSE-01 (a consequence requires a real causal
path) and Batch 01's OWN-04 (proposed change is distinct from committed state). PROP-02's own
CONFLICTING finding is exactly an instance of a proposed change (the constructed
`ResourceTransferIntent`) failing to become committed state — confirming this inherited
boundary rather than adding a new claim about it.**

**Repository evidence: SUPPORTED**, reused directly — see PROP-02's own evidence above, which
is this inherited entry's own clearest illustration: a proposal that never becomes committed
state, exactly as OWN-04 predicts is possible.

**Scenarios:** [ME-S15](../scenarios/material-economy-batch-08.md#me-s15).

### Participation in producing a change does not imply ownership of the resulting state

> A domain that triggers or causes a change is not automatically the owner of whatever
> resulting state that change produces.

**Disposition: INHERITED — direct reuse of Batch 01's OWN-02. PROP-02's own new content is the
specific *resolution* (which domain owns property-relation state after a death-triggered
transfer) — the general participation-≠-ownership principle itself is not restated as new.**

**Repository evidence: SUPPORTED**, reused directly from OWN-02's own evidence.

**Scenarios:** none newly traced; folded into PROP-02's own evidence.

---

## Scope / Deferred Boundaries

### Family/Lineage succession eligibility

> This family owns the resulting property relation once a transfer occurs (PROP-02); it does
> not design *who* is eligible to be a successor, or under what family/lineage rules that
> eligibility is determined — that remains Family/Lineage's own future domain, per the batch
> instruction's own explicit "Family/Lineage → determines eligible successor under its rules;
> Objects/Ownership → owns resulting property relation" boundary.

**Disposition: SCOPE BOUNDARY.**

### Law/crime/recovery semantics for illegitimate possession

> This family only ensures that a possessor-≠-owner mismatch (theft, unauthorized use) can be
> represented — it does not design what happens next (criminal consequence, social reaction,
> recovery mechanisms). Those remain deferred to future Law/Crime and Social relations
> domains, per the batch instruction's own explicit deferral.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

- **CONFLICTING — the single most significant finding in this whole batch.** The heirloom/
  inheritance transfer mechanism is fully constructed on the producer side but rejected by its
  own resolver (`UNKNOWN_SOURCE_KIND` for `source_kind="CHEST"`) — see PROP-02 above. This is a
  more dangerous kind of gap than a simple absence: the code's own appearance of completeness
  (a named "Transactional Heirloom Transfer" step, a resolved heir, a combined item list) could
  easily mislead a future reader into believing inheritance already works.
- **MISSING — no theft/illegitimate-possession representation exists anywhere.** See PROP-01
  above.
- **MISSING — no individual member access to collective/organizational wealth exists.**
  `faction_{id}_gold` accumulates via taxation; nothing withdraws from it. See PROP-01 above.
- **CONFLICTING — economic opportunity generation reads raw registry/world state without any
  perception gate**, the same pattern Batch 06 already confirmed for
  `ResourceOpportunityProvider`. `ServiceOpportunityProvider.get_opportunities()`
  (`src/world/providers/services.py`) iterates `ServiceRegistry.all()` filtered only by the
  entity's current *region*, with no `PerceptionGate` check at all — an entity is offered every
  registered service in its region regardless of whether it has ever perceived or learned of
  it. Classified CONFLICTING, per the batch instruction's own §17 requirement, not MISSING: this
  is active behavior contradicting Batch 06's own PERC-01 default, not an absent feature.

## Cross-domain links recorded here

- PROP-01 → Perception/Knowledge (Batch 06's PERC-01/KNOW-02, what a subject may legitimately
  be said to "know" it owns/possesses is a related but distinct question this family does not
  design)
- PROP-02 → State Ownership (OWN-02, OWN-04, OWN-05, all Batch 01 — this Rule is this batch's
  own resolution of OWN-05's own carried-forward open question), Life/Body/Progression (the
  death event itself, Batch 05/07's own domain)

## Open questions carried forward

1. Whether the heirloom-transfer resolver gap (`source_kind="CHEST"` unhandled) should be
   fixed by adding a real handler, or by routing the transfer through an already-handled
   `source_kind` (e.g. `CORPSE`, which the resolver does handle) is a real implementation
   question — flagged as the highest-priority fix this batch surfaces, not decided here.
2. Whether theft/illegitimate-possession should gain its own representable state is flagged
   for whichever future batch (most plausibly this one's own later revision, or Law/Crime) 
   first needs it — not decided here.
3. Whether individual members should gain real access to collective/organizational wealth is
   flagged for Social relations/Politics, not decided here.
