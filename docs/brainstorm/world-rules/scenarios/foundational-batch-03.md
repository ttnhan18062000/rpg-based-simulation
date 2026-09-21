---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Scenario Bank: Foundational Batch 03

**Purpose/scope.** Sixteen scenarios used to pressure-test the Capability, Cost, Capacity,
Resource, and Transformation rule families in `foundations/capability.md`,
`foundations/cost.md`, `foundations/capacity.md`, `foundations/resource.md`, and
`foundations/transformation.md`, per `tmp/world-rule-batch-3-ext-ai.md`. Covers all twelve
required probes (capability without authority, authority without capability, capability without
resources, resource without capability, cost vs. consequence, capacity exceeded, renewable
resource, resource conversion, qualitative transformation, threshold without automatic
transformation, unlimited-growth counter, random outcome) plus the explicit cross-batch checks
the instruction required (`capable ≠ authorized`, `capable ≠ reachable`, `resource exists ≠
actor can use it`, `cost paid ≠ outcome guaranteed`, `threshold crossed ≠ transformation
automatically valid`, `transformation ≠ new identity by default`, `delayed regeneration still
requires causal provenance`).

Scoring uses the same vocabulary as Batches 01/02: **covered** / **partially covered** /
**blocked** / **revealed missing rule** / **revealed contradiction**, against current repository
behavior, not the ideal design.

---

## CTR-S01 — Friendly fire, capable but unauthorized

A fully capable, in-range entity attempts to attack an ally. The action is refused.

- **Rules invoked:** CAP-01 (capability ≠ authority). Re-checks the Batch 02 boundary
  (AUTH-01/AUTH-05).
- **Result: covered.** `LegalityServiceV2` returns `FRIENDLY_FIRE_ILLEGAL` — capability is fully
  satisfied; only authority fails. Same evidence as AUTH-01, reconfirmed from the Capability
  side rather than newly discovered.

## CTR-S02 — A leader authorized, but not personally able, to act

A clan leader holds full authority over a join-request decision while wounded and on cooldown —
their combat capability is reduced, but their authority is untouched.

- **Rules invoked:** CAP-01 (the other direction: authority ≠ capability).
- **Result: partially covered.** Reuses Batch 02's TAR-S07 finding directly: `core_actions.py`'s
  join-handling reads `clan.leader_entity_id` regardless of the leader's own capability state.
  Whether this is intentional or an unexamined gap remains the same open judgment call TAR-S07
  already recorded — not re-resolved here.

## CTR-S03 — Knows the recipe, lacks the materials

An entity knows a crafting recipe (capability) but does not own the required materials
(resource). The craft cannot proceed.

- **Rules invoked:** CAP-03 (capability ≠ resource availability).
- **Result: covered.** `resource_conservation_contract.md`'s Gate 3 (`CRAFTING` source-kind
  check: "entity must own all materials; gold >= gold_cost") rejects the transaction on resource
  grounds alone — the recipe/capability question never even needs to be re-litigated at this
  gate.

## CTR-S04 — Has the gold and materials, lacks the skill

An entity owns every material a recipe requires and has enough gold, but has never learned the
recipe. The craft cannot proceed.

- **Rules invoked:** CAP-03 (the other direction), RES-01 (resource ≠ capability).
- **Result: partially covered.** The resource-sufficiency side is SUPPORTED (the same Gate 3
  check would pass on materials/gold alone). Whether the crafting system additionally gates on a
  learned-recipe capability check, separate from Gate 3's resource check, was not independently
  re-verified this batch — recorded as PARTIAL rather than assumed, since Gate 3's own text
  describes only the resource-ownership condition.

## CTR-S05 — Stamina spent, wound dealt, outcome not guaranteed

An attacker pays a stamina cost to attempt an attack. The attack may miss or be resisted (cost
paid, no guaranteed consequence); when it lands, the wound consequence falls on the defender, a
separate subject from the one who paid the cost.

- **Rules invoked:** COST-01, COST-02, COST-03, COST-05, CAP-04 (cost paid ≠ outcome
  guaranteed).
- **Result: covered.** `skill_actions.py`'s attack handler shows all of this in one mechanism:
  `can_use_skill()` is the precondition, `StaminaUpdate(current_delta=-stamina_cost)` is the
  attacker's cost (paid once the action commits, per COST-03's atomicity), and the wound/combat
  outcome on `defender_up` is the consequence — a separate `EntityUpdate`, a separate subject,
  and (per ordinary combat resolution) not a certainty even once the cost is paid.

## CTR-S06 — Several domain-specific limits, degraded by strain

A fatigued entity's concurrent-commitment bounds (`max_leads`, `max_concerns`,
`max_active_projects`) are each independently reduced by the same fatigue multiplier — no single
"Capacity" number degrades; several do, together.

- **Rules invoked:** LIMIT-01 (capacity is domain-specific), LIMIT-02 (capacity may degrade
  under strain).
- **Result: covered.** `CapacityService.derive_profile()`'s `fatigue_multiplier` (0.5×/0.8×
  depending on sleep debt/hunger thresholds) applies uniformly across five independently-derived
  bounds — confirms both the plurality of bounds and their shared responsiveness to strain.

## CTR-S07 — Capacity exceeded

An entity's active leads would exceed `max_leads` if a new one were added. The system must do
something explicit rather than silently accept or silently drop the addition.

- **Rules invoked:** LIMIT-03 (exceeding capacity produces explicit, declared handling).
- **Result: covered.** `CapacityEnforcementPhase` explicitly checks the would-be count against
  `profile.max_leads` before allowing the addition; `DetourService` computes and handles
  `excess = active_leads[profile.max_leads:]` explicitly. Neither silent acceptance nor silent
  loss occurs.

## CTR-S08 — Resource, or something else entirely?

Four superficially similar quantities are compared: gold (a resource), combat readiness (owned
state, not a resource), a learned skill (a capability, not a resource), and a scarcity ratio (a
derived abstraction, not a resource).

- **Rules invoked:** RES-01 (resource is distinct from state, capability, capacity, derived
  abstraction).
- **Result: covered.** Each of the four is architecturally distinct: gold is held/transferred
  through the resource-conservation contract; `entity.combat.readiness` is directly owned state
  (OWN-03's own corrected finding); a skill is a boolean-ish capability flag, never consumed; a
  scarcity ratio is computed at read time and never stored. No category collapses into another.

## CTR-S09 — Strict gold, generous loot

Gold obeys strict conservation (moved, never created or destroyed); a monster's loot table
generates items on death with no corresponding removal anywhere in the system.

- **Rules invoked:** RES-02 (creation/destruction requires a declared cause), RES-03 (strict
  conservation is domain-specific, not universal), RES-04 (atomicity).
- **Result: covered.** `governance_logic.md`'s Conservation Law (RPG-AUTH-003) enforces strict
  gold conservation; `src/content/schema.py`'s `loot_table` generates items by declared design.
  Both are legitimate, declared choices coexisting in the same repository — confirming RES-03's
  core claim directly rather than requiring it to be argued for.

## CTR-S10 — Threshold crossed, transformation withheld (counter)

An accumulated value crosses a numeric threshold, but a required trigger or context is absent.
The transformation does not occur merely because the number crossed a line.

- **Rules invoked:** LIMIT-04 (threshold-crossing is not automatically a cause), TRANS-04 (the
  accumulated condition, not the check, is the cause).
- **Result: covered.** `EvolutionSystem.evaluate()`'s threshold check (`for threshold in [10,
  25, 50]`) is gated on more than the raw number — the surrounding condition (`evolved` flag,
  species-specific evolution availability) must also hold; crossing 10 XP alone, without the
  rest of the trigger condition, does not produce a transformation.

## CTR-S11 — The node regrows, and the regrowth itself is traceable

A harvested resource node's charges regenerate through a real, running rule. The specific
regeneration that returns the node to harvestable status is not treated as unexplained creation.

- **Rules invoked:** RES-05 (renewable resources regenerate through a declared process), TIME-04
  (reused directly).
- **Result: covered — reuses Batch 02's own TIME-04/TAR-S03/TAR-S15 evidence, applied to
  Resource specifically.** `regen_rate_per_tick` and `DENSITY_FLOOR`'s saturation-bounded
  regeneration multiplier are both real, running mechanisms; no reappearance is silent.

## CTR-S12 — Ore becomes a sword, traceably

Raw ore and gold are consumed; a sword is produced. The sword's *identity* is new (per ID-03's
already-settled crafting exception), but the *causal* link between what was consumed and what
was produced is real and inspectable.

- **Rules invoked:** RES-06 (resource conversion preserves a provenance link, distinct from
  ID-03's identity question).
- **Result: covered.** `resource_conservation_contract.md`'s `CRAFTING` source-kind check
  requires material and gold ownership before the output is produced, within the same atomic
  transaction — the provenance link is structurally guaranteed, independent of whatever ID-03
  decides about the sword's identity relative to the ore's.

## CTR-S13 — An ordinary creature, sufficiently changed

A creature accumulates enough experience to cross an evolution threshold. Its kind,
attributes, and equipment/reward change together; its relationships and resource behavior do
not. Its identity does not change.

- **Rules invoked:** TRANS-01 (valid trigger required), TRANS-02 (scope is whatever the domain
  rule declares), TRANS-03 (identity preserved by default, per ID-03 — not re-decided here),
  CAP-01/COST/RES (the integration probe the instruction requested: "Capability + Resource/Cost
  + Transformation + Identity").
- **Result: covered.** `EvolutionSystem.evaluate()` is the same evidence TRANS-01/02 already
  cite; this scenario confirms it holds when read as one integrated trajectory rather than four
  separate rule checks — the transformation is triggered validly, touches only the fields it
  declares, and never constructs a new entity id (ID-03 undisturbed).

## CTR-S14 — Capable, but out of reach (cross-batch check)

An entity is fully capable of an action but the target is line-of-sight obstructed.

- **Rules invoked:** CAP-02 (capability ≠ opportunity/reach), REACH-01 (reused directly).
- **Result: covered — the explicit `capable ≠ reachable` cross-batch check the instruction
  required.** `LOS_OBSTRUCTED` rejects the attempt on reach grounds alone; the same evidence
  Batch 02 already established, now explicitly re-confirmed from the Capability side.

## CTR-S15 — Growth meets its ceiling (unlimited-growth counter)

A population or accumulation continues to grow. Left unconstrained, it would scale without
bound; a declared counterforce prevents that.

- **Rules invoked:** LIMIT-05 (diminishing returns/saturation must be explicit).
- **Result: covered.** `DENSITY_FLOOR` caps a resource node's regeneration multiplier at a
  declared floor as density increases — growth does not silently continue unconstrained, and the
  constraint itself is an explicit, named value, not an emergent accident. Domain-specific
  counterforce content (per the instruction's own note) is not designed here.

## CTR-S16 — Same situation, different outcome? (random outcome)

The same broad situation is proposed to potentially produce several semantically valid outcomes.
Does randomness belong in the World Rule Catalog at all?

- **Rules invoked:** none accepted — this scenario's purpose is to test the *disposition*
  itself, not to probe an accepted rule.
- **Result: moved out, not a Rule Catalog concern.** `state.seed` (`src/engine/kernel.py`)
  confirms every "random" outcome in this repository is a deterministic function of a stored
  seed — there is no genuine world-level stochasticity to give semantics to. The one real
  question a "random" outcome raises at the world-semantic level (is a dice-roll-flavored
  decision a legitimate cause?) is already fully answered by CAUSE-01 (yes, provided it's a real
  producer) and CAUSE-03 (no upgrading correlation into fabricated causation). Reproducibility/
  replay is squarely Evaluation/implementation's concern, per the established boundary. This
  scenario's conclusion is the disposition itself, not a new Rule.

---

## Cross-batch note

CTR-S01/S02 and Batch 02's TAR-S06/S07 are the same underlying evidence read from two directions
across two batches — Capability's own "authority ≠ capability" boundary and Authority's "authority
≠ capability" boundary are the same fact, stated from each family's own vantage point. This is
recorded once here rather than as a new finding, since re-deriving it a third time would add
nothing.

CTR-S10 and CTR-S13 both rely on the exact same repository mechanism (`EvolutionSystem.
evaluate()`'s threshold check) to answer two different families' questions (Capacity's
threshold-causality principle; Transformation's valid-trigger requirement) — a small piece of
evidence that Capacity and Transformation are correctly kept as separate families rather than
merged, since one mechanism answering two questions is not the same as one question needing two
answers.

CTR-S16 is deliberately the only scenario in this batch whose "result" is a disposition rather
than a rule confirmation — recorded this way, rather than omitted, because the batch instruction
explicitly required tracing whether randomness belongs in the Catalog at all, and a scenario that
concludes "no" is still a completed probe, not a skipped one.
