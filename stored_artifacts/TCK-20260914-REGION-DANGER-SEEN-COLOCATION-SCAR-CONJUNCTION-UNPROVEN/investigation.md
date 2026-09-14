# Investigation — TCK-20260914-REGION-DANGER-SEEN-COLOCATION-SCAR-CONJUNCTION-UNPROVEN

## Answer: Explanation 3 — effectively unreachable, for two independent, fully structural reasons

Not "rare" (explanation 1) and not "the prior measurement's budget was too short" (explanation 2).
Both ruled out by code-level evidence stronger than any simulation run could produce: the
conjunction cannot happen today, regardless of tick count, world, or seed, because two of its own
required preconditions have **zero real callers anywhere in the live pipeline**.

## Finding 1 — `state.local_scars` is permanently empty in every real run

`LocalScarState` (the type `has_active_scar`'s own bounds-check iterates over) is constructed in
exactly 2 places in the entire codebase: `RegionalConsequenceService.create_battlefield_scar()` and
`.create_raid_scar()` (`src/world/consequences.py`). Grepped every call site of both methods, and
of `RegionalConsequenceService` itself: the **only** real usage anywhere is
`RegionalConsequenceService.process_recovery()` (`src/engine/apply_plan.py:101`) — which only
*decays* already-existing scars toward zero severity, never creates one. Neither
`create_battlefield_scar()` nor `create_raid_scar()` has a single caller. `state.local_scars` can
never contain anything in a real run today; it is a fully dead write path, not merely one that
fires infrequently.

## Finding 2 — no real production blocker ever carries a material-name subject a location lead could match

`region_danger_seen` is only reachable for an entity that is actually navigating toward its own
untested location lead's coordinate (`resolve_location_lead_region_id(lead, state) ==
actor.navigation.region_id` requires the actor to already be standing in that region). The **only**
real consumer that drives navigation toward a location lead's own coordinate is
`ResolveBlockerScorer` (`src/ai/goals/scorers.py`), and only for `blocker.kind == "material"` where
`blocker.subject` matches `lead.subject` (e.g. both `"iron_ore"`).

Grepped every real `BlockerState(...)` construction site in the codebase. The real, live blocker
producer (`src/systems/strategic_systems/intelligence.py`'s own inference logic) does create
`kind="material"` blockers, but never with a material-name subject — only generic ones:
`"resource"`, `"out_of_stock"`, `"liquidity"`, `"capacity"`. **The only place in the entire
codebase that ever constructs a `material`-kind blocker with `subject="iron_ore"` is
`src/perf/scenarios.py:248` — a synthetic performance-benchmark fixture, not a real production call
site.** No real entity in a real run can ever have a blocker whose subject matches a real
`"iron_ore"` location lead's own subject, so `ResolveBlockerScorer`'s own travel-toward-lead branch
for this material never fires in practice — an entity holding an untested iron_ore location lead
has no real, live mechanism driving it toward that lead's coordinate at all.

## Empirical confirmation (consistent with, and reinforced by, the code-level findings above)

Ran a real 2000-tick `Kernel.tick_once()` loop against `frontier_living_world` (seed=42) — 4x the
prior ticket's own 500-tick measurement — instrumented with the exact counters the prior ticket
used plus two new ones (region-match, material-blocker-for-iron-ore), sampled every tick:

| Counter (ticks where true for ≥1 entity) | Count / 2000 |
|---|---|
| Candidate untested VAGUE/APPROXIMATE location leads present | 100 |
| Lead `detail` resolved to a real region | 100 (100%, matches the prior ticket's own 300/300) |
| Actor co-located with its own lead's resolved region | **0** |
| Full conjunction (region-match + active scar) | **0** |
| Any entity holding an active material blocker for `iron_ore` | **0** |
| Distinct scar ids ever seen in the entire run | **0** (none — matches Finding 1 exactly) |

Zero scars were created across all 2000 ticks — directly confirming Finding 1 empirically, not just
by grep. Zero material blockers for `iron_ore` ever appeared — directly confirming Finding 2
empirically. The two independent structural gaps found by code analysis are exactly what produced
the prior ticket's own zero-occurrence result, and this longer run's own zero-occurrence result —
not coincidence, not an unlucky seed, not an under-budgeted run. A longer run or a different world
would not change this outcome, because neither required precondition has a real producer to fire in
the first place, in any world, at any seed.

## Why this differs from the prior ticket's own 3-explanation framing

The prior ticket correctly identified the *symptom* (conjunction never observed) but could only see
the two dependencies mediating it — region-matching and scar-presence — as black boxes, since its
own scope was `resolve_location_lead_region_id()`'s correctness, not the conjunction's other two
halves. This investigation traced both of those halves down to their real producers and found
neither exists in the live pipeline. This is a stronger, more precise answer than "rare" or
"budget too short" — it names the exact two dead code paths responsible, each independently
sufficient to make the conjunction permanently unreachable on its own.
