---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# World Rule Family: Resource / Conservation Semantics

**Purpose/scope.** The foundational distinction between a *resource* and neighboring concepts
(state, capability, capacity, a derived abstraction), what it means for a resource to be
consumable, renewable, transferable, transformable, generated, or depleted, and when resource
creation/destruction requires a declared semantic cause. The foundational requirement is **causal
legitimacy**, not real-world physics — this family explicitly does not impose strict physical
conservation universally; fantasy-world creation, conversion, regeneration, decay, and loss are
all legitimate when a declared world rule permits them.

**Status.** Foundational Batch 03, first draft. Candidates below originated as external-reviewer
hypotheses (`tmp/world-rule-batch-3-ext-ai.md`); each carries this session's disposition and
repository evidence, not the original wording uncritically kept.

---

## RES-01 — A resource is distinct from state, capability, capacity, and derived abstraction

> Not every world concept is a resource. A resource is a quantity that participates in the
> world's causal fabric as something that can be **held, stored, available, accessible,
> allocated, consumed, transferred, transformed, or regenerated**, depending on domain
> semantics — a resource does not have to be literally held by a single subject to qualify. What
> makes it a resource is that quantity, not the specific relationship (personal possession vs.
> shared/environmental access) a subject has to it. A resource remains distinct from a
> directly-owned state field that isn't consumable (combat readiness), a capability (a skill), a
> capacity bound (`max_leads`), or a derived abstraction computed at read time (a scarcity
> ratio).

**Disposition: ACCEPT, broadened 2026-09-21 — removed the implicit requirement that a resource
be personally "held" by a subject.** The original wording ("a quantity that can be held,
consumed, transferred, or transformed") read as though every resource must be something one
subject possesses. That's too narrow: a shared water source, a region's ambient mana, or a
commons grazing field are all legitimate resources — accessible and consumable, but not held by
any one subject — and excluding them from the definition would have been a real gap, not a
simplification. The distinguishing boundary this rule actually needs (resource ≠ state ≠
capability ≠ capacity ≠ derived abstraction) is unaffected by this broadening; only the
"personally held" assumption is removed. This is deliberately not turned into a catch-all: the
four-way exclusion list is exactly as strict as before.

**Repository evidence: SUPPORTED, by contrast across four categories, plus one further
distinction confirmed this pass.** *Resource:* gold, item stacks, resource-node charges — all
held quantities that are consumed/transferred/transformed. *State, not a resource:*
`entity.combat.readiness` (OWN-03's own corrected finding — directly owned, not consumable in
the resource sense). *Capability, not a resource:* a learned skill (`SKILL_NOT_LEARNED`) — a
subject either has it or doesn't; it isn't spent. *Capacity, not a resource:* `max_leads` — a
bound on concurrent commitments, not a quantity that is itself consumed. *Derived abstraction,
not a resource:* a scarcity ratio (`remaining_charges / max_charges`) — computed at read time
from a real resource, never itself held or transferred. *Accessible-but-not-personally-held, a
resource nonetheless:* a resource node's remaining charges are accessible to any entity that
reaches them, and no single entity "holds" the node's charge pool the way it holds its own
inventory gold — confirmed by inspection that `ResourceNodeState`'s charges are keyed to the
node, not to a claimant.

**Scenarios:** [CTR-S08](../scenarios/foundational-batch-03.md#ctr-s08),
[CTR-S18](../scenarios/foundational-batch-03.md#ctr-s18) (added 2026-09-21 — an accessible,
shared resource not personally held by the subject drawing from it).

---

## RES-02 — Resource creation or destruction requires a declared semantic cause

> A resource may not appear or vanish without a rule that says why. "Declared" does not mean
> "strictly conserved" — it means the creation or destruction traces to a real, named mechanism,
> per CAUSE-01's real-causal-path requirement applied to resources specifically.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED, for both a strict-conservation case and a declared-creation
case.** *Strict:* `docs/engine/governance_logic.md`'s Conservation Law (RPG-AUTH-003) — "Total
Gold in World = Sum(Entity Gold) + Sum(Building Gold) + Sum(Faction Vaults)"; gold is never
created or destroyed, only moved. *Declared creation, not strict conservation:* a creature
definition's `loot_table: Dict[ItemDefinition ID, chance]` (`src/content/schema.py`) generates
items on death with no corresponding removal anywhere — a real, declared creation mechanism,
authored as content, not an unexplained appearance.

**Scenarios:** [CTR-S09](../scenarios/foundational-batch-03.md#ctr-s09).

---

## RES-03 — Strict conservation is a domain-specific choice, not a universal law

> Some resources (gold) obey strict conservation; others (loot) are legitimately generated by a
> declared rule. The world does not impose real-world physical conservation everywhere — each
> resource kind's own conservation strictness is a domain decision, stated explicitly per
> resource, not inherited from a universal physical law.

**Disposition: ACCEPT strongly.** This is the rule the batch instruction most explicitly
required ("do not impose strict physical conservation universally"), and RES-02's own two
pieces of evidence (gold vs. loot) are simultaneously the proof that the repository already
makes this choice correctly, case by case, rather than uniformly.

**Repository evidence: SUPPORTED**, same evidence as RES-02, read for the contrast rather than
the individual facts: gold's strictness and loot's generativity coexist in the same repository
without contradiction, because each is its own domain's declared choice.

**Scenarios:** [CTR-S09](../scenarios/foundational-batch-03.md#ctr-s09).

---

## RES-04 — Resource transfer semantics must be explicitly declared, and authoritative state must never depend on an accidental partial application

> Resource transfer semantics must explicitly define whether a transfer is atomic, divisible,
> partial, interruptible, or otherwise constrained — universal atomicity is not itself a world
> law. What the world does require is that the authoritative resulting state never depend on an
> *accidental* partial application: whatever the declared transfer semantics are (fully atomic,
> or explicitly divisible), the resulting state must be exactly what those declared semantics
> say it should be, never an undefined in-between state nobody decided to allow.

**Disposition: ACCEPT, refined 2026-09-21 — universal atomicity removed as a world law.** The
original wording ("a resource transaction either completes entirely or leaves the world state
completely unchanged... no partial resource transaction is legitimate") over-generalized this
repository's own implementation choice into a universal semantic requirement. Partial, divisible,
or interruptible transfers are legitimate world behavior in principle (a partially-successful
trade, a rationed withdrawal from a scarce shared resource, an interrupted long-running
extraction) — the world rule doesn't get to forbid them. What actually matters, and is genuinely
universal, is that whatever a specific transfer mechanism declares about its own divisibility
must be honored exactly, so that no resource ever ends up in an authoritative state nobody
designed for.

**Repository evidence: SUPPORTED for the declared-semantics-honored-exactly requirement; this
repository's own current choice (full atomicity) is evidence of *one* legitimate declared
semantics, not proof that atomicity is the only one.** `resource_conservation_contract.md`'s
four-gate sequence (idempotency → destination capacity → source existence/stock → atomic commit)
is this repository's own declared transfer semantics — fully atomic, by explicit design choice —
and it is honored exactly: "If any check fails, the world state is unchanged." That remains
excellent evidence that *this* repository's declared semantics are followed correctly; it is no
longer read as evidence that every resource transfer, anywhere, must be atomic.

**Scenarios:** [CTR-S09](../scenarios/foundational-batch-03.md#ctr-s09) (this repository's own
declared-atomic semantics, honored exactly),
[CTR-S19](../scenarios/foundational-batch-03.md#ctr-s19) (added 2026-09-21 — a partial transfer,
legitimate under a different, hypothetically-declared transfer semantics).

---

## RES-05 — Renewable resources regenerate through a real, declared process

> A depleted resource returning later must do so through a real recurring mechanism (TIME-04),
> not unexplained reappearance. Regeneration is a continuing rule, and — per TIME-04's own
> refinement — each regeneration occurrence remains its own traceable event where relevant.

**Disposition: ACCEPT.** Directly reuses TIME-04's own finding, applied to Resource specifically
— deliberately not re-derived from scratch, since Time already established the general shape.

**Repository evidence: SUPPORTED**, reusing Batch 02's own evidence: `regen_rate_per_tick` on
resource nodes, and `DENSITY_FLOOR`'s saturation-bounded regeneration multiplier (`src/world/
ecology.py`) — regeneration is always a real, running rule, never a silent reset.

**Scenarios:** [CTR-S11](../scenarios/foundational-batch-03.md#ctr-s11) (renewable resource:
depleted → valid regeneration process → resource returns later, without being treated as
unexplained creation).

---

## RES-06 — Resource conversion must preserve a real provenance link, not treat the output as spontaneously new

> Raw material converted through a process into a new material, object, or resource must carry a
> traceable link to its inputs. This does not require the output's *identity* to be the same as
> the input's (ID-03's crafting exception already settled that a forged sword is a new identity,
> not a continuation of the ore) — it requires the *causal* link (what was consumed to produce
> this) to be real and inspectable.

**Disposition: ACCEPT.** Deliberately framed to avoid re-opening ID-03's already-settled
identity question — this rule is about causal provenance, a distinct concern from identity
continuity, even though both apply to the same crafting scenario.

**Repository evidence: SUPPORTED.** Crafting's `CRAFTING` source-kind check
(`resource_conservation_contract.md`'s Gate 3) requires "entity must own all materials; gold >=
`gold_cost`" before the new item is produced — the output is never generated without its inputs
being consumed in the same atomic transaction.

**Scenarios:** [CTR-S12](../scenarios/foundational-batch-03.md#ctr-s12).

---

## Cross-domain links recorded here

- RES-01 → State Ownership (OWN-03, the derived-view/state-vs-resource contrast reused directly)
- RES-02, RES-03, RES-04 → Economy/resources, Objects & material culture (the future domains
  that design the actual resource catalog on top of this boundary)
- RES-05 → Time (TIME-04, reused directly), Ecology/population (`DENSITY_FLOOR`'s own content)
- RES-06 → Identity (ID-03's crafting exception — explicitly not reopened), Objects & material
  culture

## Open questions carried forward

1. **Deterministic randomness, investigated per the batch instruction's §7, is explicitly NOT
   given a Rule family here or anywhere in this batch — reaffirmed 2026-09-21 on a sharpened
   rationale, per direct follow-up review.** Traced via
   [CTR-S16](../scenarios/foundational-batch-03.md#ctr-s16) and re-checked against the
   adversarial probes added this pass (none exposed a contradiction). **The disposition's real
   justification is not the deterministic seed** — that would make the case sound like an
   implementation accident rather than a semantic conclusion. The real reason is that a
   dedicated Randomness family would have nothing new to govern: the valid outcome space for any
   stochastic-flavored decision, and the causal legitimacy of whichever outcome actually occurs,
   are already fully governed by the accepted world Rules and by Causality (CAUSE-01's real-
   causal-path requirement; CAUSE-03's anti-fabrication standard). A Randomness family would
   either restate those constraints under a new name or invent new ones a fantasy world doesn't
   need. Loot generation (`loot_table`'s `chance` field) is the closest touchpoint to "chance" in
   this family, and it needs no rule beyond RES-02's own declared-cause requirement. Replay/RNG
   *implementation* — how outcomes are actually generated, and whether a run can be reproduced —
   belongs outside the Rule Catalog entirely, per the established Rule/Law-vs-Evaluation boundary
   (`simulation-rule-world-law-design-preparation.md` §3.8). This repository's `state.seed`
   (`src/engine/kernel.py`) remains cited below only as supporting implementation evidence that
   this repository's own RNG happens to be reproducible — not as the reason randomness is out of
   scope; a world whose implementation used genuinely non-reproducible randomness would reach
   the identical disposition, because the semantic argument above doesn't depend on
   reproducibility either way. **Disposition: moved out entirely, not forced into a Rule
   family — unchanged, on firmer footing.**
