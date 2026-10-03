---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS
artifact_type: investigation
tags: [combat, faction, root-cause]
---

# Investigation — TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS

## The fix, as scoped

`LegalityServiceV2.get_engaged_hostiles_at_pos()` (`src/engine/legality.py`) had three internal
implementations of the same hostility test (`entity.identity.faction != other.identity.faction`,
the raw legacy 4-value enum). Extracted a single shared helper,
`LegalityServiceV2._is_engagement_hostile(entity, other)`, that resolves real `faction_id` strings
via `EntityIdentityResolver` (falling back to `get_faction_id_str()` on resolution failure, the
same fallback pattern `tactical.py`'s own hostiles-loop already uses) and delegates to
`FactionSemanticsService.is_hostile_compat()`. All three internal implementations now call this
one helper — one definition, three call sites, per the ticket's own hard scope guard against a
partial fix.

## A fourth place with the same bug, found only by testing the positive case directly

Writing tests for each of the three internal paths — one positive case (a real, same-legacy-
bucket catalog rivalry that the old code structurally could not see: `bandit_company`/
`goblin_warband`) and one negative case (a real, different-legacy-bucket non-hostile pair the old
code wrongly flagged: `hero_guild`/`merchant_league`) — found that **2 of 6 tests failed on the
first pass**: both "catches the real rivalry" cases for the occupancy-snapshot and
`SpatialQueryService` paths. The dict-iteration fallback's own "catches" case passed immediately.

Traced directly, not assumed: `AuthoritativeState.__post_init__` (`src/core/state.py`) computes a
separate field, `_has_hostiles_or_dead_cache`, using the exact same raw legacy-enum comparison —
"does any entity's `identity.faction` differ from the first entity's, or is any entity dead" — as
a cheap early-exit gate consumed at the very top of `get_engaged_hostiles_at_pos()`:
`if getattr(state, "_has_hostiles_or_dead_cache", None) is False: return []`. Because my two test
entities share one legacy bucket (`MONSTER_HORDE`), this cache computed `False` ("no diversity,
nothing worth checking") and returned an empty list **before the newly-fixed per-pair logic ever
ran** — the exact same class of bug, one level upstream, silently defeating the fix for precisely
the flagship case (a real rivalry sharing a legacy bucket) the whole investigation was about.

This cache field has two real consumers beyond `legality.py`:
`src/systems/strategic_systems/intelligence.py` recomputes the identical logic independently
whenever the cache has been reset to `None` (done by `src/engine/pipeline_phases/actions.py` for a
"sliding" trial state used in speculative evaluation) — a second, structurally identical copy of
the same bug that would have silently reintroduced it the moment that code path fires.

**Why this was fixed in-scope rather than filed as its own follow-up**: it sits directly upstream
of the two real call sites this ticket exists to fix, and leaving it broken would make the fix
*look* complete (green tests that happen to hit the dict-iteration path, or worlds where no two
hostile factions share a legacy bucket) while being silently inert in exactly the case that
motivated the whole investigation. This is the same "a partial fix is a regression, not half a
fix" principle already governing the two-call-site scope guard, applied one layer deeper.

**Why the fix is a conservative approximation, not a full catalog check**: `src/entities/
identity_resolver.py` itself imports from `src/core/state.py`, so the full
`EntityIdentityResolver`/`is_hostile_compat()` machinery cannot be used inside `state.py`'s own
`__post_init__` without a circular import. The chosen fix compares the real
`identity.properties.get("faction_id")` first (falling back to the raw legacy enum only when
absent) instead of doing a full catalog lookup. This is intentionally asymmetric: a false
"diverse" positive here only costs a wasted downstream scan (the real per-pair check still runs
and correctly says "not hostile"); a false negative was the actual bug (skips the real check
entirely). Erring toward more scans, never toward silently skipping one, is the correct direction
for a cache whose only job is "is there possibly something here worth checking."

## Real before/after combat volume, measured (not asserted)

Predicted in advance, per peer review, before running the measurement: real combat volume should
drop substantially, since 97% of `hero_guild_routing`'s legacy-triggered engagements were
previously measured to be phantom (not real catalog hostility). Measured via a self-contained
script that authentically reconstructs the true pre-fix runtime condition — both the old
hostility test *and* the old, unfixed `_has_hostiles_or_dead_cache` value (forced via
`object.__setattr__` immediately after normal state construction, matching what the original
unmodified `__post_init__` would have computed) — rather than only reverting half of the fix:

| World | Ticks | Before (legacy enum) | After (catalog) | Change |
|---|---|---|---|---|
| `crowded_frontier` | 2000 | 874 | 133 | **-84.8%** |
| `hero_guild_routing` | 2000 | 1418 | 58 | **-95.9%** |
| `quest_dense_frontier` | 2000 | 0 | 0 | unchanged |
| `metropolis`† | 30 | 15 | 15 | 0.0% |

**The prediction survives contact**: both real corpus worlds with nonzero volume show a large,
real drop, exactly the direction and rough magnitude predicted. `hero_guild_routing`'s -95.9% is a
near-total collapse — consistent with, and slightly larger than, the 97% legacy-only-false-
-positive rate the original investigation measured for pair-level determinations (not identical,
since this counts real `resolve_multi_attack()` calls across a full 2000-tick run rather than a
single-tick pair-check snapshot, but directionally the same finding at a different unit of
measurement). This is not "essentially all combat was phantom" territory (a much stronger claim,
per peer's own flagged alternative) — `crowded_frontier` still retains real, non-phantom combat
volume (133 real calls over 2000 ticks) after correction, and `hero_guild_routing`'s residual 58
calls confirm real hostile engagement still happens there too, just far less often than the
uncorrected code implied.

`quest_dense_frontier` staying at exactly 0 both before and after is consistent with its own
earlier-established profile (population-minimal by design, likely single-faction-dominant) — not
a new finding, but confirms the fix doesn't spuriously create volume where none should exist
either.

†`metropolis` shows no change, but this is not informative given its own disclosed spawn-collision
limitation and the small 30-tick sample — not weighted in the conclusion above.

## Zero remaining divergence, verified directly

Re-ran the original investigation's own instrumented divergence probe (comparing
`get_engaged_hostiles_at_pos()`'s real classification against an independent `is_hostile_compat()`
check for the same pairs) against the fixed code:

| World | Total pair-checks | `legacy_only` (should be 0) | `catalog_only` (should be 0) |
|---|---|---|---|
| `crowded_frontier` | 24492 | **0** | **0** |
| `hero_guild_routing` | 31748 | **0** | **0** |
| `quest_dense_frontier` | 108 | **0** | **0** |

Both false-positive and false-negative counts are exactly zero across all three worlds — the
function's real classification now matches the catalog exactly, not just in the two hand-
constructed unit-test pairs.

## What was NOT changed

- `TacticalDecisionSystem`'s own decision-driven `ATTACK` path — already correct, unaffected.
- `FactionSentimentService`/`pairwise_tension` — not touched; whether it has any real effect on
  engagement remains an open question for a separate ticket, per the source investigation.
- `docs/parity_ledger/combat_movement.yaml`'s existing entries citing `get_engaged_hostiles`
  (COMB-004) or `resolve_multi_attack()`'s dominance (COMB-297) — checked both directly; neither
  entry's actual claim is factually invalidated by this fix (COMB-004 is about adjacency/
  engagement rules existing at all, not their hostility definition; COMB-297 is about
  `resolve_multi_attack()` being the dominant kill mechanism, which remains true at a lower
  absolute volume) — left as pre-existing, unrelated gaps rather than rewritten as part of this
  ticket's own scope.
