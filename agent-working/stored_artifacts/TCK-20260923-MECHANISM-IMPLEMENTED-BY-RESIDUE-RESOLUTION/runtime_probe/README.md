---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION
artifact_type: investigation
tags: [architecture]
---

# Runtime probe

Positive-controlled per-method call counters run over corpus worlds (`Kernel.tick_once()`, seed 42, the
default `PROD_SMALL` profile), used as the runtime instrument for the absence and reachability claims in
`registries/mechanisms.yaml` (`TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE`).

- `call_counter_named_methods.py <worlds,comma> <ticks> [module:Class.method ...]` wraps the named methods,
  proves each wrapper can increment (asserts before the run), then counts calls per world. Output:
  `output_named_methods_5worlds_2000ticks.jsonl` (crowded_frontier, quest_dense_frontier, hero_guild_routing,
  frontier_living_world, generated_frontier_3_42; 2000 ticks each). **An absent key means 0 calls.**
- `call_counter_whole_classes.py <world> <ticks> <out.json>` wraps every method of a fixed class list; the
  `control` object records the positive control per class. Outputs: `output_whole_classes_<world>_1000ticks.jsonl`
  for crowded_frontier, quest_dense_frontier, frontier_living_world. Here `counts` also omits zero-call methods.
- `wider_scope_candidate_rederivation.py` is the early ast re-derivation of the wider-scope sweep (the
  authoritative rule now lives in `tools/mechanism_registry/mechanism_registry_completeness_check.py`).

Reachability at runtime, not effect size, is what is measured. A short horizon can miss a rare path, which
is why zero-call registrations use verdict `inconclusive`.

## Scope limit (stated, not to be rediscovered)

These counters run a single `Kernel.tick_once()` world. They are competent to detect calls on the
engine path and blind to anything that only runs in multi-episode campaign runs
(`src/domains/campaigns/`). `registries/mechanisms.yaml` has 9 entries citing `domains/campaigns`;
for those, 0 calls is what a healthy and a dead mechanism both look like, so the right verdict is
`inconclusive`, never `orphan`. Every orphan verdict written from this probe (calamity producer,
`SocialMemoryService`, `SourceTrustUpdateService`) concerns a class outside `domains/campaigns/`, imported
and reachable from the engine path, which is why those hold (checked by rpg-feature-planning).

