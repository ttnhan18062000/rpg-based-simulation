---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260807-FACTION-TERRITORY-PCT-PAYLOAD-GAP
phase: done
date: 2026-08-07
tags: [observability, simulation-quality, faction]
---

# TCK-20260807-FACTION-TERRITORY-PCT-PAYLOAD-GAP

## Title
`faction_monopoly`/`faction_conquest_degenerate` can never fire — `territory_ownership_changed`
never carries the `faction_territory_pct` payload key both construction paths' own scorer expects

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`FactionScorer.score()`'s `territory_ownership_changed` branch (`src/simulation_quality/scorers/
faction.py:88`) reads `payload.get("faction_territory_pct", 0.0)` to decide `faction_monopoly`
(`territory_pct > 0.8` after a tick gate) and `faction_conquest_degenerate`
(`territory_pct >= 1.0`). Confirmed via direct grep: **neither** `event_extractor.py`'s legacy
construction of `territory_ownership_changed` nor `FactionShaper`'s live construction
(`event_shapers.py:374-380`) ever sets a `faction_territory_pct` key in the payload — both always
default to `0.0`, so both branches can never fire in either the old diffing path or the new
push-shaper path. A genuine, pre-existing, unrelated bug — present since before Phase 1's
push-migration cutover, not introduced or regressed by it.

Found incidentally during `TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY`'s own investigation
while tracing `territory_ownership_changed`'s construction sites.

## Scope
Compute `faction_territory_pct` (this faction's fraction of total claimed territory across all
factions, or total world regions — confirm the exact denominator this ticket's own Investigate
phase should use, matching whatever `faction_monopoly`'s original design intended) at both
construction sites (`event_extractor.py` and `FactionShaper`), and include it in the
`territory_ownership_changed` payload.

## Out of Scope
- `TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY`'s own `faction_trajectory_stagnant` rule —
  unrelated, already DONE.
- Any change to the `faction_monopoly`/`faction_conquest_degenerate` weight values themselves.

## Acceptance Criteria
- [x] `faction_territory_pct` computed and included in `territory_ownership_changed`'s payload at
      both construction sites
- [x] Unit test confirming `faction_monopoly` fires when a real payload crosses the 0.8 threshold
      — satisfied by the combination of `test_faction_scorer.py`'s pre-existing
      `test_faction_monopoly`/`test_faction_conquest_degenerate` (scorer correctly handles a
      real crossing payload) plus this ticket's own new tests confirming both construction sites
      now actually supply that payload key with the correct value (previously they never did)
- [x] Real-kernel or calibration check confirming the fix doesn't introduce a false-positive
      monopoly/conquest signal on a healthy multi-faction world — real 1500-tick `urban_political`
      and 500-tick `dungeon_crawl` runs both showed zero `territory_ownership_changed` events at
      all (territory changes are genuinely rare in these corpora within these windows) — no false
      positive observed, though also no positive-path confirmation in a real run; unit tests are
      the decisive verification here
- [x] Scoped pytest run passes

## Related Tickets
- TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY (found this incidentally, DONE)

## Related Docs
None.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY/investigation.md` (the finding)

## Related Code Areas
- `src/observability/event_extractor.py` (territory_ownership_changed construction, ~line 1227)
- `src/observability/event_shapers.py` (`FactionShaper.shape()`, ~line 374-380)
- `src/simulation_quality/scorers/faction.py` (the consuming branch, line 88)

## Assumptions / Open Questions
- The exact denominator for "percent of territory" (total world regions vs. total claimed
  territory across factions vs. something else) is not yet confirmed — this ticket's own
  Investigate phase must trace the original intent, not guess.

## Implementation Notes
Denominator chosen: total world regions (`len(state.regions)`), not "total claimed territory
across factions" — the simpler, more direct reading of "single faction controls >80%/100% of
territory" (§5 FACTION table's own wording), and the one requiring no cross-faction aggregation.

`event_extractor.py` (full `current_state` access): reads `current_state.factions[fid].territory`
directly (post-update, no reconstruction needed) over `len(current_state.regions)`.

`FactionShaper` (`prior_state` + `update` only): reconstructs current territory as
`(prior_territory - territory_remove) | territory_add`, over `len(prior_state.regions)` — region
count itself doesn't change tick-to-tick, so `prior_state`'s count is an equally valid denominator
to `current_state`'s would be, matching this file's own established reconstruction-pattern
precedent.

## Test Summary
`tests/unit/observability/test_event_shapers_economy_faction.py` (2 new tests:
`test_territory_ownership_changed_includes_faction_territory_pct`,
`test_territory_ownership_changed_pct_reflects_full_conquest`),
`tests/unit/observability/test_event_extractor_social_faction.py` (1 new test). Scoped run
(these 2 files + `test_faction_scorer.py`): 97 passed. Real-kernel checks: `dungeon_crawl` (500t)
and `urban_political` (1500t) both ran without error; zero `territory_ownership_changed` events
observed in either (territory changes are rare in these corpora at these tick depths) — no crash,
no false positive, but also no real-run positive-path confirmation; unit tests (which construct
the exact scenario directly) are the decisive verification.

## Files Changed
- `src/observability/event_extractor.py` — `faction_territory_pct` computed and added to
  `territory_ownership_changed`'s payload
- `src/observability/event_shapers.py` — same, in `FactionShaper`
- `tests/unit/observability/test_event_shapers_economy_faction.py`
- `tests/unit/observability/test_event_extractor_social_faction.py`

## Completion Summary
Fixed the `faction_territory_pct` payload gap at both `territory_ownership_changed` construction
sites (`event_extractor.py`'s legacy path, `FactionShaper`'s live path) — `faction_monopoly`/
`faction_conquest_degenerate` were dead code in both delivery paths before this fix, since the
scorer's own threshold checks always read a defaulted `0.0`. No `src/` behavior change beyond the
payload enrichment itself; no gameplay mechanic touched.
