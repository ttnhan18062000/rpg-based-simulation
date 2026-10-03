---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION
artifact_type: plan
tags: [combat, faction, root-cause]
---

# Plan — TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION

Investigation only, per this ticket's own explicit scope. No `src/` change beyond
`registries/mechanisms.yaml`'s own `implemented_by` bindings (a side effect of reading this
code closely, per explicit instruction, not new scope).

## Steps

1. Find every real caller of `LegalityServiceV2.get_engaged_hostiles`/`get_engaged_hostiles_at_pos`
   repo-wide (`grep -rn` across `src/`), rather than trusting the ticket's own "3 call sites"
   framing at face value.
2. Read each call site's own surrounding code in full to determine what it actually does with the
   result — not just that it calls the function.
3. Determine whether `get_engaged_hostiles` and `get_engaged_hostiles_at_pos` are structurally
   independent or one wraps the other, since that changes how many independent semantic decisions
   are actually in play.
4. For each real, independent call site: what does "hostile" need to mean for that specific
   consumer, and would `is_hostile_compat()` semantics change its real behavior in an undesired
   way? Check code comments stating intent, not just code structure.
5. Check for existing tests covering each call site's real behavior, and whether their fixtures
   would still pass under catalog-aware semantics (a real check, not assumed).
6. Measure real call volume per independent call site over real `Kernel.tick_once()` runs across
   multiple worlds (not just the one already-measured attack/escape path) — the ticket's own
   scope named the pathing check as possibly needing different semantics, so its real volume and
   behavior needed independent measurement, not inference from the attack-path numbers alone.
7. Check `RelationContext`'s field requirements and `EntityIdentityResolver.resolve()`'s cost/
   reliability profile, since a proposed fix that swaps to `is_hostile_compat()` needs both to be
   cheap and safe to call at the measured volume.
8. State the fix shape as a recommendation, not implement it.
9. Bind `implemented_by` for every mechanism whose implementing code was read with real,
   citable confidence during this investigation (`combat_resolution`, `tactical_decision`,
   `movement`) — per explicit instruction, a side effect of the reading already done, not a
   separate pass over the other 4 combat mechanisms not directly read here.
