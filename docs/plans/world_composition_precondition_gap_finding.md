---
status: historical
layer: world
authority: P1
audience: agent
tags: [world, architecture]
---

# Finding — Mechanics Whose Preconditions Depend on Unvalidated World Composition

> **SUPERSEDED 2026-09-30. Do not cite this document as evidence for anything.**
>
> Filed 2026-09-15. It claimed a general pattern resting on "five confirmed instances" — its own
> body only ever marked four, and `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION`
> (PR #260) subsequently found that **none of the four survives as an instance of this pattern.**
> Its thesis is not supported. It is retained for the method lesson below, not for its findings.
>
> The text that follows the status block is the original 2026-09-15 document, unedited. **Every
> claim in it must be read through the status block first.**

## Status of each section, as of 2026-09-30

| § | Mechanic | Claimed | Actual — see the cited owner, not this document |
|---|---|---|---|
| 1 | Lair-occupant spawning | confirmed instance | **Open, per J2.** Owned by `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` = workstream J2 of `docs/plans/systemic_world/first_wave_plan.md`. Whether it is a content condition or a routing/pathing defect is **J2's own open question** — this document's guess must not pre-empt it. |
| 2 | Calamity-intensity production | confirmed instance, "doubly so" | **`DEFECT` — not a composition gap.** `CalamityService.apply_calamity_consequences` (`src/world/calamity.py:80`) has zero production callers; the only other `src/` hit is a comment at `displacement.py:27`. The mechanic is never entered, so composition was never what stopped it. |
| 3 | Cross-faction combat volume | explicitly *not* confirmed | **Unchanged** — still a sibling lead, still never verified by a live run. Correctly not counted when filed. |
| 4 | Regional influence shift | the checked exception | **Confirmed `DEFECT`, unchanged.** `lifecycle.py:202` accepts `("KILL","PERMADEATH")`; combat (`src/engine/combat.py:172,273,383`) emits `"DEFEAT"`. 59 deaths, 0 influence-shift calls in 1,500 ticks. |
| 5 | Camp-object placement | confirmed instance | **Premise false.** A real compile of `frontier_living_world` yields 2 `CampState`. Content shipped `cb0b23b07` (**2026-09-08**), twelve days before the ticket was filed. |
| 6 | Demographic cohort cycling | confirmed instance | **Premise false.** Same compile: 6 of 7 regions seed non-empty cohorts. Seeding shipped **2026-08-31**, three weeks before the ticket was filed. |

Verdicts, evidence and evidence-strength caveats for all 14 corpus tickets live in
`docs/plans/unreachable_mechanism_classification.md`. They are not restated here.

**Two figures in the original §1 are also wrong.** It cites the lair spawn gate as
`state.maturity >= 50.0` and `trauma_score >= 20.0` (repeated from a stale comment in
`moon_cult_ruins.yaml`). The live values are `BOSS_SPAWN_THRESHOLD = 2.0` and
`BOSS_SPAWN_TRAUMA_THRESHOLD = 8.0` (`src/world/boss.py:26-27`), lowered from 50.0/20.0 as a
reachability fix in `b1ab4cc92` (**2026-09-15**, PR #198) and recorded as provisional in
`docs/plans/deferred_tuning_decisions_register.md` D-05. That change landed *after* §1's
5,000-tick measurement was taken, which is a further reason §1 is unsettled rather than confirmed.

## Why it was wrong — the only part worth carrying forward

**Premises were taken from reading content and registry verdicts, not from compiling the world and
looking.** §5 and §6 both quoted `registries/mechanisms.yaml` verdicts dated 2026-09-16 that were
already contradicted by code and content shipped on 2026-08-31 and 2026-09-08. Those verdicts were
`instrument: code_trace` — reading code — while the claim they made was about the *absence* of
runtime world data, which reading code cannot establish. Neither ticket named the instrument, so
nothing downstream could weigh the claim. A single real compile falsified both, and one grep for
production callers falsified §2. None of the three needed a long run or new instrumentation.

**Grouping by symptom shape produced the candidates and then had to be corrected by the
classification.** Every entry was collected because it presented as "a mechanic that is silent" —
a symptom common to dead code, unreached guards, unmet runtime conditions and genuine composition
gaps alike. Once a composition-shaped hypothesis is in hand, composition-shaped evidence is
available for *every* silent mechanic, because a silent mechanic always has some unmet
precondition somewhere. §2 is the clean demonstration: the composition facts cited were true and
none of them mattered. The classification epic reached the same conclusion independently — only
two of its fourteen tickets matched the shape the grouping assumed, and both of those were false.

Establishing that a mechanic is actually *reached* — its producer has a production caller, its
guard is actually evaluated at runtime — has to come before attributing its silence to anything.

**Runtime reachability evidence, not a compile-time checker, is the right instrument.** The
original document implied a composition-validation layer in the world-compile path. That case is
not supported: three of four instances were not composition gaps, and the fourth would not be
caught by such a layer — spatial isolation is legal, internally consistent content, and whether
participants meet depends on runtime routing and gates. The one compile-time check with real value
is reference existence (§3's `trade_road` dangling reference), which belongs to the existing
resolve/integrity validation of Mechanics ch.06, not to a new layer.

## Open items this document leaves behind

- `TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION` and
  `TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED` are still `OPEN` on false
  premises. Re-scoping or closing them belongs to the RPG side.
- `registries/mechanisms.yaml`'s `camp` and `demographic_cohort_cycle` entries still carry the
  2026-09-16 verdicts shown false above. Both the process fix and these two data corrections are
  owned by `TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE` — **written but not yet
  committed** as of 2026-09-30, so treat it as forthcoming rather than filed.
  `docs/brainstorm/mechanism_verification_view.md` mirrors both entries but is generated
  (`make mechanism-verification-view`) and must not be hand-edited; it corrects itself when the
  registry does.
- `registries/mechanisms.yaml`'s `calamity_intensity` entry (`done` + `contradicted`) carries a
  2026-09-20 note that it is zero-caller and "closer to `orphan`", matching §2's `DEFECT` finding.
  It is **outside** the above ticket's instrument filter (it is a `corpus_run` verdict, not
  `code_trace`) and so is unowned — it belongs with the roadmap side.
- `moon_cult_ruins.yaml`'s comment still cites the pre-2026-09-15 50.0/20.0 thresholds.

## Related

- `docs/plans/unreachable_mechanism_classification.md` — the classification that superseded this
- `docs/plans/systemic_world/first_wave_plan.md` — J2 owns §1's open question
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` (§1, = J2)
- `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` (§2 — `DEFECT`)
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (§3 — unverified lead)
- `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` (§4 — confirmed `DEFECT`)
- `TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION` (§5 — `STALE-PREMISE`)
- `TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED` (§6 — `STALE-PREMISE`)
- `TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE`
- `TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH` (surfaced by §3)
- `TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES` (surfaced by §3)

---

<!-- ORIGINAL DOCUMENT, 2026-09-15, UNEDITED BELOW THIS LINE. Read the status block above first. -->

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

## Six mechanics checked, five confirmed instances, one clean exception

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

### 5. Camp-object placement — confirmed, added 2026-09-20

`TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION`. `CampState` (`src/core/state.py`) is
real and complete — spawns monsters, triggers raids, a real clearing-reward loop — and is correctly
wired into the apply path. But no compiled or procedurally-generated corpus world today ever
populates `state.camps` with a single real camp instance, so the mechanic is a structural no-op in
every real run. Found while resolving the `camp` mechanism registry entry
(`registries/mechanisms.yaml`'s own `verified` block, dated 2026-09-16) but never given a dedicated
ticket until this document's own update — same shape as instances 1 and 2 above, a mechanic whose
precondition (a world actually composing the participant it needs) is never satisfied.

### 6. Demographic cohort cycling — confirmed, added 2026-09-20

`TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED`.
`DemographicCycleService.process_demographics` has a real, confirmed caller
(`engine/world_dynamics.py:178-179`) — the mechanism was previously mis-registered `orphan` and
already corrected. But the caller is guarded by `if not region.population_cohorts`
(`worldbuilding/compiler.py:203`), and no compiled or procedurally-generated world today seeds any
region's `population_cohorts`, so the guard never opens. Found by
`TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION`'s own first real run (2026-09-16) but,
like instance 5, never given a dedicated ticket until this document's own update.

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
