---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260929-UNREACHABLE-CLASSIFY-DEAD-GUARD
artifact_type: investigation
tags: [investigation, root-cause, corpus, world]
---

# Investigation — TCK-20260929-UNREACHABLE-CLASSIFY-DEAD-GUARD

Three classification checks; no `src/` change. All three covered tickets are self-derived (none cites a
`registries/mechanisms.yaml` verdict), so claims were re-run and cited code was dated against filing rather than
registry-dated. Branch tip `3dbdff48a`.

## 1. `REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` — `DEFECT`
Cause already established (death-outcome-kind filter: `lifecycle.py:202` accepts `("KILL","PERMADEATH")`, combat resolves
non-lethal kills as `"DEFEAT"`, `world_dynamics.py:47` uses `alive_set is False`) — recorded, not re-investigated, re-confirmed
in the code at HEAD. Extra runtime check: 1,500 real ticks of `frontier_living_world` seed 42 with `process_influence_shift`
wrapped -> 59 alive->dead transitions, 0 calls, influence never off `0.0`/`100.0`. `RegionState.influence` has never moved,
so the sovereignty-threshold unification tuned a path this defect keeps from firing.

## 2. `REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS` — `DEFECT`
Defect 1 re-verified: `create_battlefield_scar` / `create_raid_scar` have no reference anywhere beyond their definitions;
`LocalScarState(` constructed only there; `local_scars` otherwise only read, serialized, or decayed. Defect 2 is stale as
written: `generate_crafting_blockers` emits `material` blockers with real recipe material ids and has production callers
(`blacksmith.py:190,207`); reachability of that path and of a matching location lead was not measured. Verdict rests on Defect 1
alone, which the ticket itself says is sufficient.

## 3. `COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES` — `UNDECLARED`
Not a never-fires mechanism: the 3 existing scenario tests pass, and the opportunistic behaviour is declared in code as
PERF-007 ("O(Dirty) enforcement", 2026-05-18) — so the ticket's "undocumented" is partly wrong; the consequence is what is
unadjudicated. Measured: 1,500-tick `V2EngineManager` run, 10,916 entity-checks, 0 over-cap observations. One world, one seed.

## Not done
Shared classification document (-> `T06`); fixes; adjudicating the capacity ticket's priority; measuring the blacksmith path.
