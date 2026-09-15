---
status: active
layer: world
authority: P1
audience: agent
tags: [world, architecture]
---

# Finding — Mechanics Whose Preconditions Depend on Unvalidated World Composition

**Filed 2026-09-15.** This is a finding, not a plan — it states what was found and checked, not
what to do about it. No fix is proposed here; that is a real design decision for the user, put to
them separately once this document existed.

## The pattern, stated once

**A mechanic can be live, its content references can resolve, its entities can spawn correctly —
and its precondition can still never be met, because world composition placed the participants
where they will never meet, or never composed one of the participants at all.** Nothing in the
world-compile path checks that a specific world's actual composition satisfies what its own
mechanics structurally require. Only that content references resolve syntactically — and, per one
of the four instances below, not even always that.

This is distinct from two other silence-as-failure shapes already catalogued this arc:
- **Dead code**: a mechanism nothing calls.
- **Systems fed by nothing**: a mechanism that runs and receives no input, full stop.
- **This pattern**: the mechanism runs, is fed real input in principle, and the specific inputs it
  needs exist somewhere in the game — just never in the same place, or never in this world's own
  composition, so the precondition is structurally unreachable for reasons invisible to a static
  read of the mechanic's own code.

## Four mechanics checked, three confirmed instances, one clean exception

### 1. Lair-occupant spawning — confirmed

`TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`. `moon_cave` (the corpus's one real LAIR-kind
Place) sits at `grid_bounds: [100, 70, 130, 110]`, spatially isolated from every other populated
region in `generated_frontier_3_42`'s composition — the nearest, `orc_clan_territory`
(`[160, 60, 200, 100]`), has a ~30-unit gap. `moon_cave`'s sole population
(`moon_cult_apprentice_circle`) is correctly spawned there — no dangling reference — but no
hostile faction is ever composed within combat range. The Lair's own occupant-spawn gate
(`trauma_score` accrual from combat deaths) can never open because no combat ever happens there.

### 2. Calamity-intensity production — confirmed, doubly so

`TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`. The producer requires a `hero`-kind
entity to die in a `hazard_level > 0.5` region. `hazard_level` itself is confirmed live and
populated (several corpus regions exceed 0.5). But `frontier_living_world` — the exact world the
original 5000-tick probe used — has **zero `hero`-kind entities composed into it at all**; its
module list omits `hero_adventurers`, the corpus's only source of that entity kind. In a world
that does include it (`crowded_frontier`), `hero_adventurers.yaml`'s own population recipes
hardcode `spawn_region: "hometown"` (`hazard_level: 0.0`) for all three heroes, unconditionally.
Two independent, compounding reasons the precondition can never be met, in two different worlds.

### 3. Cross-faction combat volume — a strong sibling, not a confirmed instance of this exact
pattern (keep the confidence level distinct)

`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`. Six candidate root causes were checked
and falsified for why most corpus worlds show near-zero cross-faction combat. A static comparison
of `merchant_league`'s own composition found a real, evidence-backed but **unverified** lead:
`crowded_frontier`'s only source of `merchant_league`, the `merchant_caravan` population, declares
`preferred_regions: ["trade_road", "hometown"]` — but no module in that world's composition
defines a region actually named `"trade_road"`, so the reference silently falls through to
`"hometown"`, the map's far corner, away from the hostile factions that do exist.
`frontier_living_world` (which shows real cross-faction combat) instead composes a second source
of `merchant_league` via `trading_company_hub`, whose own `"hometown"` region has different,
much-closer-to-hostile-territory bounds. This is a real, static, well-evidenced lead — and it was
never verified with a live run, per an explicit scope cap on this investigation. It belongs in
this document as the strongest sibling case, not folded in as a fourth confirmed instance: the
investigation's own six falsified candidates mean the actual cause of the broader rarity question
is still open, even though this specific geometry finding is real.

### 4. Regional influence shift — checked, does NOT share this pattern (the exception)

`TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`. This looked like a strong fourth-instance
candidate on its own title (`region.influence` never moves despite real deaths in the same
regions), but direct instrumentation found a different, real, single-cause defect: entities are
correctly co-located and deaths genuinely occur where the mechanic needs them to.
`world_dynamics.py`'s own trauma block detects every real death (`alive_set is False`), but
`resolve_lifecycle()`'s own separate death filter checks `outcome_kind in ("KILL", "PERMADEATH")`
— missing `"DEFEAT"`, which real combat resolution also sets `alive_set=False` for. Confirmed
empirically: 20 of 20 real deaths in the sampled run were `"DEFEAT"`, zero were `"KILL"`. This is
a classification divergence between two independent readers of the same event, not a geometry or
composition gap.

**This exception matters as much as the three confirmed instances.** A pattern checked against a
real candidate and found not to apply is what makes the other three credible — without it, this
document would be at risk of becoming a lens that explains every starved mechanic in the corpus,
whether or not composition is actually the cause.

**This finding is not merely a foil for the pattern above — it is a real, complete, standalone
defect in its own right**, and belongs to a different, separately-named shape:
`TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS` found two independent
`ItemRegistry` classes disagreeing about what counts as a valid item id (one raises `KeyError`,
the other silently returns `None`). This ticket's own root cause — two independent readers of the
same combat-outcome event disagreeing about what counts as a death — is the same shape: **two
readers of one thing, disagreeing about what counts, with no error surfaced either time.** Both
are filed and tracked as complete, actionable, standalone bugs, parked by the same investment-cap
decision as the three composition instances above, not folded into or subordinated by this
document's own pattern.

## The implication

Nothing in the world-compile path (`WorldCompiler`, `WorldRepository`) currently validates that a
specific world's composition satisfies what its own mechanics structurally require to function —
only that content references resolve syntactically, and (per
`TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH`) not even reliably that.
Any mechanic requiring two things to be spatially co-located, or requiring a specific entity kind
to exist in a world's roster at all, is exposed to this class of gap — and it will look, from a
static read of the mechanic's own code, exactly like healthy, correctly-wired content.

## What this document does not do

- It does not propose a fix. The candidate directions named in the individual tickets (content-
  authoring composition changes; mechanic-design changes to what a trigger condition requires; a
  compile-time validation layer) are real options, but choosing among them, or deciding whether
  to build a general-purpose composition-validation mechanism at all, is the user's call.
- It does not claim the cross-faction rarity investigation's broader question is answered by this
  pattern — see instance 3's own framing above.
- It does not audit the rest of the corpus for further instances. The four mechanics checked here
  were checked because each had its own already-open ticket; this pattern likely generalizes
  further, but that is future work, not part of this finding.

## Related

- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` (instance 1; named the pattern first)
- `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` (instance 2)
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (sibling — unverified lead, not a
  confirmed instance)
- `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` (the checked exception, with its own
  distinct, confirmed root cause)
- `TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH` (a specific content-
  reference defect surfaced by instance 3)
- `TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES` (a specific region-composition
  ambiguity, also surfaced by instance 3)
- `docs/plans/simulation_execution_census_initiative.md` — a related but distinct measurement
  effort: the census finds branches that never execute; this pattern is about branches that
  execute rarely, for a structural reason the census's own design (stated explicitly in that
  document) does not detect.
