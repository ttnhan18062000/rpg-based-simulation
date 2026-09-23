---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# World Rule Family: Survival Needs

**Purpose/scope.** Only needs with meaningful causal consequences — food, water, rest, shelter,
temperature/exposure, or other fantasy-specific requirements, where each modeled need follows
the pattern `need pressure accumulates → thresholds/conditions become relevant →
capability/body/decision consequences become possible`. This family does not create a
universal mandatory need system for its own sake.

**Status.** Batch 05 (Life/Body/Survival/Ecology), first draft. Candidates below originated as
external-reviewer hypotheses (`tmp/world-rule-batch-5-ext-ai.md`); each carries this session's
disposition and repository evidence, not the original wording uncritically kept.

**Normalized 2026-09-22** per external-reviewer instruction on Rule admission discipline
(`tmp/world-rule-batch-5-normalization-ext-ai.md`): entries separated into Domain Rules and
Repository Findings. All four original SURV-* entries pass the admission test as genuinely
new domain-refined semantic constraints — none is a bare restatement of an earlier Rule ID —
so **all four (SURV-01–04) remain Domain Rules; nothing was reclassified.** SURV-04 was
specifically flagged for review per the normalization instruction: its target semantic
principle ("unconsumed need-adjacent state is inert") is kept as the Rule; the specific
repository fact (`last_meal_tick`/`last_sleep_tick` are unread) is separated below as a
Repository Finding, not treated as the Rule's own content.

---

## Domain Rules

## SURV-01 — A need is distinct from a resource, a cost, a body condition, and a pressure

> Need, resource, cost, body condition, and pressure are not automatically the same concept. A
> need is an accumulating internal state calling for satisfaction; a resource is a held/
> accessible quantity; a cost is what an action consumes; a body condition is a persistent
> constraint on capability; a pressure is what a need (or an aggregate condition) exerts once
> accumulated.

**Disposition: ACCEPT.** This is the core distinguishing rule the batch instruction asked this
family to establish. Passes the admission test: a genuine taxonomy claim specific to this
family, not a restatement of RES-01/COST-01/BODY-04 (those are cited only as contrast
categories, not as the source of this rule's own claim).

**Repository evidence: SUPPORTED, by contrast.** `BiologicalComponent.hunger`/`sleep_debt`/
`rest_pressure` are needs (accumulating internal state) — distinct from a resource (gold, item
stacks — RES-01's own category), a cost (`StaminaService`'s drain functions — COST-01's own
category), and a body condition (`WoundState`/`ScarState` — BODY-04/06's own category). The
*pressure* a need exerts once thresholds are crossed (SURV-02) is itself a further, derived
fact distinct from the need's own raw accumulated value.

**Scenarios:** none newly traced; confirmed by direct contrast across already-established
categories rather than requiring a fresh scenario.

---

## SURV-02 — Need pressure accumulates, and crossing a threshold produces real consequences

> A modeled need's pressure accumulates over time; crossing a declared threshold produces a
> real capability, body, or decision consequence — never an assumed or silent effect.

**Disposition: ACCEPT.** Passes the admission test: instantiates the general threshold
discipline (LIMIT-04) specifically for needs, with its own richly-confirmed consequence set —
domain-refined, not a bare restatement.

**Repository evidence: SUPPORTED, richly.** `hunger`/`sleep_debt` accumulate passively each
biological tick (`bio.hunger + 0.1 * cadence.biological`). Crossing declared thresholds
produces real, varied consequences: `hunger >= 95.0` → direct HP damage
(`total_passive_dmg += 2`, `src/engine/apply.py`); `sleep_debt > 70` or `hunger > 70` →
capacity degradation (`CapacityService.derive_profile()`'s `fatigue_multiplier`, reused from
Batch 03's LIMIT-02); `hunger > 50/60/80` → real goal-urgency and decision-priority changes
(`src/systems/world_systems/routine.py`, `src/systems/strategic_systems/intelligence.py`,
`work_queue.py`). Need pressure is one of the most thoroughly-consumed state categories this
Catalog has found.

**Scenarios:** [LB-S08](../scenarios/life-body-batch-05.md#lb-s08) (survival pressure).

---

## SURV-03 — Only needs with real causal consequences are modeled

> A need is not modeled merely because it would be realistic — every modeled need must have a
> real, traceable downstream consequence. This is a scope-discipline rule specific to this
> family's own need catalog, patterned after (but not a restatement of) COST-04's "not every
> action requires a cost."

**Disposition: ACCEPT.** Passes the admission test: COST-04 governs actions/costs; this rule
governs a different category (needs) and states its own standard for this family's own
catalog — a domain-refined instantiation, not a reconfirmation of COST-04 itself.

**Repository evidence: SUPPORTED, by the absence of a wider need catalog than this repository
actually consumes.** Only `hunger`, `sleep_debt`, and `rest_pressure` are modeled as
biological pressures, and (per SURV-02) all three have real, confirmed consequences — the
repository has not added a need field it doesn't also consume, which is exactly this rule's
own standard held up correctly.

**Scenarios:** none newly traced; a negative claim confirmed by the absence of an
over-broad need catalog, not something a scenario trace would add evidence to.

---

## SURV-04 — Tracked need-adjacent state with no consumer is inert bookkeeping

> If a field exists alongside a need but no declared world rule/process consumes or reacts to
> it, that is a real, nameable fact — not a violation of SURV-02/SURV-03, and not something to
> assume is "probably used somewhere." This is the same discipline ENV-05 applies to
> Environment, restated as its own standing standard for Survival Needs specifically (not a
> bare reuse of ENV-05, since it names a distinct set of fields in a distinct family).

**Disposition: ACCEPT — the target semantic principle stands as a Rule; the specific
repository fact confirming it is separated below as a Repository Finding, not folded into the
Rule's own text.** The batch instruction explicitly required identifying causally inert
bookkeeping — the honest answer is that the needs *themselves* are all live (SURV-02/SURV-03),
but two closely-adjacent timestamp fields are not. Passes the admission test as a standing
constraint (a general standard future need-adjacent fields must be checked against); the
"last_meal_tick/last_sleep_tick are unread" fact is repository-specific and does not belong in
the Rule statement itself.

**Repository Finding: MISSING (inert), confirmed directly.** `BiologicalComponent.
last_meal_tick`/`last_sleep_tick` are written whenever an entity eats or sleeps
(`core_actions.py`, `town_service.py`) but checked directly: nothing anywhere reads either
field back to gate or modify any behavior. They exist only as timestamps today, unlike
`well_rested_until` (a similarly-shaped field that *is* read, by `EvolutionSystem`, confirming
the contrast is real and not an artifact of how timestamps are generally treated).

**Scenarios:** [LB-S09](../scenarios/life-body-batch-05.md#lb-s09) (need exists but no
consequence, counter).

---

## Repository Findings (significant, cross-referenced)

- **SURV-04's confirmed inert pair** — `last_meal_tick`/`last_sleep_tick` are written on every
  meal/sleep action and read nowhere, contrasted against the live `well_rested_until`. See
  SURV-04 above for full evidence. This fact is what the Rule's own general standard (inert
  need-adjacent state is a nameable gap, not assumed-used) is checked against here; it is not
  itself the Rule.

## Cross-domain links recorded here

- SURV-01 → Resource (RES-01), Cost (COST-01), Body/Condition (BODY-04/06) — the category
  contrast this rule reuses directly
- SURV-02 → Capacity (LIMIT-02, directly reused), Agency/motivation/decision (the goal-urgency
  content this rule's evidence already touches, owned by that future domain's own content)
- SURV-04 → all future domains that add need-adjacent tracked fields (a standing standard to
  check new fields against, matching ENV-05's own role for Environment)

## Open questions carried forward

1. Should `last_meal_tick`/`last_sleep_tick` (confirmed inert) be wired to a real consumer
   (e.g., a "time since last meal" decision input distinct from the raw `hunger` value) in a
   future Agency/decision batch, or left as forward-declared bookkeeping? Not decided here.
2. Whether temperature/exposure or shelter should become modeled needs in their own right, or
   remain fully owned by Space/Environment/Movement's own exposure mechanism (ENV-02, BODY-07)
   without a separate Survival-Needs-side pressure, is not decided here — this batch found no
   evidence of a modeled temperature/shelter *need* (as distinct from environmental exposure
   itself), and did not invent one to fill the gap.
