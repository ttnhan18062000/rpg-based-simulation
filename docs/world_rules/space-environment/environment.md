---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# World Rule Family: Environment

**Purpose/scope.** How a location or environment can create conditions that affect subjects and
processes within its declared reach — terrain, hazard, climate/weather, shelter, visibility,
environmental exposure, local resource conditions, environmental modifiers/constraints.
Environment should create **causal conditions**, not passive descriptive metadata — this
family's own investigation explicitly challenged whether environmental state currently has
actual consumers, per the batch instruction's own requirement.

**Status.** Batch 04 (Space/Environment/Movement), first draft. Candidates below originated as
external-reviewer hypotheses (`tmp/world-rule-batch-4-ext-ai.md`); each carries this session's
disposition and repository evidence, not the original wording uncritically kept.

**Explicit non-goal, per the batch instruction.** Do not build detailed weather/ecology
mechanics here, and do not design the Life/Magic consequences of exposure — this family
establishes that exposure is real and causal; downstream domains own the resulting body/
capability state where appropriate.

---

## ENV-01 — Environmental state has causal significance only where a declared world rule/process can consume or react to it

> A region or location's environmental state (hazard, weather, terrain) has causal significance
> only where a declared world rule or process can consume or react to it. Environmental state
> existing as a field is not, by itself, proof that it is causally significant — this rule
> states what environment *should* be (a source of real conditions with a declared consumer),
> and this family's own evidence review found that claim is not automatically true of every
> environmental field in this repository.

**Disposition: ACCEPT, refined 2026-09-21 — "a mechanism reads it" replaced with world-semantic
language.** The original wording described the requirement in terms of a mechanism reading a
field — an implementation-level description of what causal significance looks like in code,
not a statement of the semantic requirement itself. The rule now states the semantic
requirement directly: causal significance requires a *declared world rule/process* able to
consume or react to the state, of which "a mechanism reads it" is simply this repository's own
way of realizing that requirement. The batch instruction explicitly asked this family to
challenge whether environmental state has actual consumers — the honest answer is: most of it
does, one clear field doesn't.

**Repository evidence: SUPPORTED for most environmental state; MISSING (inert) for at least one
field, confirmed directly.** *Causally live:* `EnvironmentService.calculate_hazard_drain()`
reads `region.hazard_level`, `region.calamity_intensity`, and `"MIASMA" in region.
active_modifiers` to compute a real HP-drain amount; `EnvironmentService.get_weather_
multipliers()` feeds directly into `MovementSystem.resolve_move()`'s own speed calculation.
*Causally inert, confirmed by absence of any read site:* `RegionState.service_availability` is
written (degraded by siege, recovered by successful defense — `military_conflict.py`) but
checked directly: nothing anywhere reads it back to gate or modify any behavior. It exists only
as bookkeeping today.

**Scenarios:** [SPC-S10](../scenarios/space-environment-batch-04.md#spc-s10) (the required
counter: environment is descriptive but causally inert).

---

## ENV-02 — Presence or traversal creates an exposure opportunity; actual exposure depends on whether declared conditions are satisfied

> The causal pattern is: presence/traversal → exposure opportunity/context → declared exposure
> conditions checked → exposure occurs only if those conditions are satisfied → downstream
> consequence becomes possible. Occupying or traversing a hazardous location does not, by
> itself, guarantee actual exposure — shelter, immunity, equipment, or form may prevent it.
> Environment establishes the relevant *condition*; later rules (potentially including
> Environment's own mechanism, or another domain's) determine whether that condition actually
> affects the subject.

**Disposition: ACCEPT, refined 2026-09-21 — removed the implication that occupying/traversing
automatically produces exposure.** The original wording collapsed "the environment has a
relevant condition" and "the subject is exposed" into one automatic step. That was too strong,
and this repository's own evidence already contradicted it before this refinement made the rule
match: a subject with a declared immunity to a region's hazard kind experiences the condition
(the hazard is real) without experiencing actual exposure (zero drain). The revised rule states
the full chain explicitly, with the immunity/shelter/equipment/form check as a legitimate,
expected step between condition and exposure, not an exception the original wording had no room
for.

**Repository evidence: SUPPORTED, and this refinement is confirmed by evidence already
gathered, not new evidence.** `EnvironmentService.calculate_hazard_drain()` checks
`get_faction_semantics_service().get_hazard_immunities(faction_id)` *before* computing any
drain — a faction with a declared immunity to the region's `hazard_kind` returns `0` regardless
of `hazard_level`. `WorldDynamicsSystem.resolve_dynamics()` still checks, for every active/alive
entity, which region contains its position and calls this function — presence/traversal
reliably creates the *opportunity* for exposure; whether exposure actually results is a further,
already-real conditional step this repository already implements correctly.

**Scenarios:** [SPC-S04](../scenarios/space-environment-batch-04.md#spc-s04) (enter hazardous
environment), [SPC-S05](../scenarios/space-environment-batch-04.md#spc-s05) (leave hazardous
environment), [SPC-S13](../scenarios/space-environment-batch-04.md#spc-s13) (added 2026-09-21 —
hazardous region entered, but immunity prevents actual exposure).

---

## ENV-03 — Environment establishes exposure; it does not own the downstream consequence

> Environment produces the *fact and magnitude* of exposure. It does not commit the resulting
> body/capability/resource state change itself — that commitment happens through whichever
> domain's own authoritative update path owns the affected state (Life/Body, or another
> appropriate later domain, depending on what the exposure affects). This is OWN-02
> (participation ≠ ownership) restated for Environment specifically. **This rule does not
> decide which domain that is** — only that Environment itself is never that domain.

**Disposition: ACCEPT strongly, refined 2026-09-21 — the specific target-owner claim
loosened.** The original wording named Life/Body (via the repository's own `CombatUpdate` path)
as though that settled which domain *should* own environmental bodily harm going forward. It
doesn't: this repository's current implementation happens to route hazard damage through Combat/
Life's own update path, but that is repository evidence about *today's* wiring, not a target-
architecture claim that Combat specifically must always own this consequence. A later domain
(Life/Body more generally, a distinct Survival domain, or something else this Catalog hasn't
named yet) may end up being the more precise owner once that domain is actually designed — this
rule's own job is only to keep Environment itself out of that role, not to decide who fills it.

**Repository evidence: SUPPORTED for "Environment never owns it"; read as today's wiring, not
target ownership, for "who does."** `EnvironmentService.calculate_hazard_drain()` returns a
plain `int` — it does not construct, touch, or return any `EntityUpdate`/`CombatUpdate` object,
which is the part of this rule that is genuinely settled. The actual commitment happens two
call-frames away, in `WorldDynamicsSystem.resolve_dynamics()`, which builds a
`CombatUpdate(hp_delta=..., alive_set=...)` — real evidence of *a* domain other than Environment
owning the result, cited here as evidence of the boundary holding, not as a claim that Combat is
where this consequence should live once Life/Body/Survival is actually designed.

**Scenarios:** [SPC-S04](../scenarios/space-environment-batch-04.md#spc-s04),
[SPC-S05](../scenarios/space-environment-batch-04.md#spc-s05) (same scenarios as ENV-02 — one
mechanism answering both "does exposure happen" and "who owns the result").

---

## ENV-04 — Environmental modifiers may affect other domains' calculations without owning their commit path

> A weather or terrain modifier may change how another mechanism's own calculation resolves
> (movement speed, combat modifiers) without Environment itself owning or committing that
> mechanism's result. This is ENV-03's same ownership discipline, restated for the
> modifier-rather-than-exposure case.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED.** `EnvironmentService.get_weather_multipliers(region)` returns
a plain multiplier dict, consumed inside `MovementSystem.resolve_move()`'s own speed
calculation — Movement's own mechanism reads and applies the multiplier; Environment never
touches Movement's `EntityUpdate` directly.

**Scenarios:** none newly traced; reuses the same evidence as ENV-03, read for a second,
adjacent purpose (a modifier feeding a calculation, rather than exposure feeding a consequence).

---

## ENV-05 — Inert environmental state should be recognized as such, not assumed causal by its mere existence

> If an environmental field exists but no declared world rule/process currently consumes or
> reacts to it, that is a real, nameable fact about the repository's current state — not a
> violation of ENV-01, and not something to silently assume is "probably used somewhere."
> Recognizing inert state explicitly is what keeps ENV-01's "causal significance requires a
> declared consumer" standard honest rather than aspirational.

**Disposition: ACCEPT.** This is the rule ENV-01's own counter-finding motivated — stated
separately so a future domain author has an explicit standard to check newly-added
environmental fields against, rather than relying on this batch's one-time investigation
remaining accurate forever.

**Repository evidence:** same as ENV-01 — `service_availability` is the confirmed instance;
recorded once, not duplicated.

**Scenarios:** [SPC-S10](../scenarios/space-environment-batch-04.md#spc-s10) (same scenario as
ENV-01).

---

## Cross-domain links recorded here

- ENV-01, ENV-05 → all future domains that add environmental state (a standing standard to check
  new fields against)
- ENV-02, ENV-03 → Life/body/survival, Capability & progression (plausible future owners of
  exposure's downstream consequences — **not settled here**; ENV-03 keeps Environment itself out
  of that role without deciding which of these, or another domain not yet named, fills it)
- ENV-04 → Movement/Navigation (`movement-navigation.md`), Conflict & combat (future terrain-
  affects-combat content)
- ENV-03 → State Ownership (OWN-02, directly reused)

## Open questions carried forward

1. Should `service_availability` (confirmed inert) be wired to an actual consumer (e.g., shop
   pricing, trade availability) in a future Economy/resources or Places batch, or was it added
   ahead of its own consumer intentionally (a forward-declared field awaiting siege-mechanics
   content not yet built)? Not decided here — this batch only confirms the fact, not the
   remedy.
2. **Checked directly:** `price_modifiers` is causally live, not inert — `src/systems/
   economy_systems/market.py` reads it directly into buy/sell price calculation. `weather` and
   `active_modifiers` beyond `"MIASMA"` were not exhaustively re-verified for every possible
   modifier string this batch; flagged for whichever future Economy/resources or Ecology/
   population batch next touches regional modifiers, rather than assumed either way.
3. **Added 2026-09-21.** ENV-03 deliberately leaves open which domain owns exposure's downstream
   consequences (Life/Body, a future Survival domain, or another not yet named) — not decided
   here, and not to be read as already-settled by the `CombatUpdate` path this repository
   currently happens to use.
