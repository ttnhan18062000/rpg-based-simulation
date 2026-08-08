---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY
artifact_type: investigation
tags: [simulation-quality, faction]
---

# investigation.md — TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY

## Current Behavior

`docs/simulation_quality/quality_scoring_contract.md` §7.6 (this ticket's own rationale source)
correctly identifies the gap: FACTION scores diplomatic/territorial events in isolation plus
threshold checks (`faction_monopoly`, `all_factions_neutral`, `tension_oscillation`), but has no
trajectory-*coherence* rule the way WORLD's `trauma_hazard_broken` is (a trend flat despite active
related events, not a single bad event or static threshold).

## What's queryable at scoring time

`FactionUpdate` (`src/core/updates.py:844-853`) is a typed per-tick delta record carrying
`territory_add`/`territory_remove` (tuples of region IDs) and `diplomatic_relations_set` (dict of
target faction → new `DiplomaticState`) — both already read by `FactionShaper`
(`event_shapers.py:300-419`), the current live-by-default path for FACTION (this domain was
migrated in Phase 1 of the push-migration epic, `ENABLE_PUSH_EVENT_SHAPERS` defaults `ON`).
`FactionState.territory: tuple[str, ...]` (`src/core/state.py`, confirmed via `FactionState.
from_dict`) is the full snapshot field these deltas mutate — available via `prior_state.factions`,
though a multi-tick trend check needs cross-tick memory regardless of snapshot access, not just a
single prior/current comparison.

Regional Sovereignty Influence (`docs/mechanics/05_world_evolution.md` §3,
`docs/world/regional_sovereignty_runtime_contract.md`: sovereignty at influence ≥ +50 (hero) or ≤
−50 (monster)) is a *region-level* field, not a per-faction aggregate readily available without a
region-by-region scan — the ticket's own re-check requirement. Using `territory_add`/
`territory_remove` (a faction-level count already directly available via `FactionUpdate`, no scan
needed) is the minimal-viable signal that satisfies "is this faction's territory/influence
actually rising or falling" without introducing a new region-scanning mechanism.

## Architecture decision: implement in `FactionShaper` (not `event_extractor.py`)

Unlike `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE` (implemented directly in
`event_extractor.py`, deliberately unconditional/not flag-gated), this ticket's new signal is
implemented in `FactionShaper` (`event_shapers.py`) instead. Reasoning:
1. FACTION's live-by-default path is already `FactionShaper` (Phase 1 of the push-migration
   epic, not Phase 2) — implementing the new rule there means it's delivered by default
   immediately, matching how this domain already works, rather than needing to reason about
   bypassing a flag the way the PROGRESSION ticket did for the (Phase-2-migrated) PROGRESSION
   domain.
2. The signal only needs `FactionUpdate.territory_add`/`territory_remove`/
   `diplomatic_relations_set` — all typed delta fields `FactionShaper` already reads directly, no
   full-snapshot reconstruction needed (unlike PROGRESSION's need for equipped-gear/gold, which
   pushed that ticket toward the extractor's full-snapshot access instead).
3. `FactionShaper` is currently fully stateless (no `reset_run_state()` of its own, confirmed by
   reading the class — every other shaper with cross-tick memory has one). This ticket adds the
   first cross-tick state to `FactionShaper` and wires its `reset_run_state()` into
   `Kernel.__init__` alongside the other shapers, mirroring the exact established pattern.

## Region/world-layer re-check (ticket's own Scope item)

Re-confirmed WORLD's existing `trauma_hazard_broken`/`world_static`/`trauma_accumulation_broken`
rules (`src/simulation_quality/scorers/world_dynamics.py`) still cover region/world-layer
trajectory coherence — no gap found at those layers, matching §7.6's own conclusion. No change to
`world_dynamics.py`.

## Rule design

**`faction_trajectory_stagnant`**: a faction's territory (`territory_add`/`territory_remove`
combined — either direction counts as "territorial activity", matching the ticket's "rising or
falling" framing) stays unchanged for `_FACTION_STAGNANT_TICKS` (300, matching
`capability_growth_stalled`'s and `all_level_1`'s own dormancy magnitude for consistency across
this session's own newly-added rules) ticks while the *same* faction continues to show diplomatic
activity (`diplomatic_relations_set` non-empty for that faction) — mirrors `trauma_hazard_broken`'s
exact pattern (a trend flat despite an active, ongoing related signal). Tracked via
`_last_territory_change_tick: dict[str, int]` (per faction_id) and `_emitted_stagnant: set[str]`,
both new class-level state on `FactionShaper`, cleared via a new `reset_run_state()` classmethod
wired into `Kernel.__init__` alongside `StrategyShaper`/`ProgressionShaper`/`SocialShaper`'s own
calls. Initializes a faction's tracked baseline to its first-observed tick (not 0), same
correctness pattern established in the PROGRESSION ticket, for the same reason (a faction first
observed mid-run should not be immediately misclassified as stagnant).

## A separate, pre-existing, unrelated finding (not fixed here)

`FactionScorer.score()`'s `territory_ownership_changed` branch (`src/simulation_quality/scorers/
faction.py:88`) reads `payload.get("faction_territory_pct", 0.0)` to gate `faction_monopoly`/
`faction_conquest_degenerate` — but **neither** `event_extractor.py`'s legacy construction nor
`FactionShaper`'s live construction of `territory_ownership_changed` ever sets a
`faction_territory_pct` key in the payload (confirmed via direct grep of both files). This means
`faction_territory_pct` always defaults to `0.0`, so `faction_monopoly`
(`territory_pct > 0.8`)/`faction_conquest_degenerate` (`territory_pct >= 1.0`) can never fire in
either the old or new path — a genuine, pre-existing, unrelated bug (present since before Phase 1's
migration, not introduced or regressed by it). Filed as a separate follow-up
(`TCK-20260807-FACTION-TERRITORY-PCT-PAYLOAD-GAP`), not fixed inline — out of this ticket's own
scope (territorial-monopoly threshold detection is a different question from trajectory
*coherence*), matching this session's established discipline for pre-existing findings surfaced
incidentally.

## Docs Requiring Update

- `docs/simulation_quality/quality_scoring_contract.md`: §5 FACTION table + event-type list.
- `docs/simulation_quality/event_type_coverage.md`: §1.1 Direct Emission table.
- `docs/parity_ledger/faction.yaml`: new entry.

## Parity Ledger Overlap

`FAC-013` (`docs/parity_ledger/faction.yaml`) covers Phase 1's own FACTION cutover — this ticket
adds a genuinely new signal, not touched by that migration; a new, separate entry is warranted.

## Prior Work

- `TCK-20260806-SIMQ-LIFECYCLE-PILLAR-BOUNDARY-DOC` (rationale source, DONE)
- `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE` (sibling, entity-layer equivalent, DONE —
  established the "first-observed-tick baseline" correctness pattern reused here)

## Risks and Open Questions

None left open.

## Anti-Drift Hazards

- `faction_trajectory_stagnant`'s "diplomatic activity without territorial consequence" framing is
  deliberately narrower than a full Sovereignty-Influence trend check (region-level scan) — if a
  future ticket needs the fuller signal, it should build on this one's `_last_territory_change_tick`
  tracking rather than duplicating it.
- The `faction_territory_pct` payload gap (see above) affects any future work touching
  `faction_monopoly`/`faction_conquest_degenerate` — flagged, not silently worked around.
