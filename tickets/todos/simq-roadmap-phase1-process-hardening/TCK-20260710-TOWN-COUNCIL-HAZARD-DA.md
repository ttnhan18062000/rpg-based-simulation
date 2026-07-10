---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260710-TOWN-COUNCIL-HAZARD-DA
phase: open
date: 2026-07-10
tags: [world, faction, simulation-quality]
---

# TCK-20260710-TOWN-COUNCIL-HAZARD-DA

## Title
DA ruling: `town_council` hazard exposure at `bandit_road` (P2-Q, Phase 1.2)

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`town_council`'s `merchant_caravan_frontier_guard` entities are stationed at `bandit_road`
(present in both `urban_political` and `generated_frontier_3_42`) — a region with
`hazard_kind: "NATURAL_TERRAIN"` that correctly exempts its native `bandit_company` occupants
via their declared `hazard_immunities`. `town_council` itself declares no `hazard_immunities`,
so its 2 guards there take slow, continuous, unmitigated hazard drain over a long run. Two
independent investigations (`TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`,
`TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`) found this exact question,
each correctly declined to fix it unilaterally per the standing guidance against blanket/wildcard
immunities, and each silently re-deferred it as "may be intentional conflict-pressure flavor"
without ever recording an actual decision. This ticket makes that ruling once, resolves
P2-Q in `docs/plans/audit_fix_plan.md`, and closes Phase 1.2 of
`docs/plans/simq_development_roadmap.md`. Either outcome is acceptable: (a) rule it intentional
and record the decision in `docs/guidelines/intentional_divergences.md`, or (b) rule it a genuine
gap and add a `NATURAL_TERRAIN` (or narrower) `hazard_immunities` entry for `town_council` in
`data/content/social/factions.yaml`, recompile the two affected worlds, and re-verify.

## Scope
- Make exactly one explicit, recorded DA ruling on whether `town_council` should endure
  `NATURAL_TERRAIN` hazard exposure at `bandit_road`, applicable to both `urban_political` and
  `generated_frontier_3_42` (and any future world reusing this pattern).
- Before ruling, check blast radius: confirm whether `town_council` is populated (not merely
  listed as a module `factions:` entry) in any other hazardous (`hazard_level > 0`) region
  corpus-wide. Confirmed-so-far candidate: `data/content/world_modules/trading_company_hub.yaml`'s
  `hometown` region (`hazard_level: 0.5`, `hazard_kind: "NATURAL_TERRAIN"`) — that module's own
  `population_recipes` only spawns `merchant_league` there, but a composed world may add a
  separate `town_council` population recipe against the same `hometown` region id; verify against
  actual composed-world specs, not just this one module in isolation.
- If ruled (a) intentional: add a new row to the Divergence Summary Table and a Detailed Record
  entry in `docs/guidelines/intentional_divergences.md`, classified with the appropriate
  rationale class (likely **Intentional Gameplay Change** — "conflict-pressure" exposure is a
  deliberate design choice, not a bug being tolerated) and a verification path (cite the existing
  `test_population_stability`-style tests for both worlds as evidence the exposure does not break
  the 60%-alive floor).
- If ruled (b) genuine gap: add `hazard_immunities` to `town_council` in
  `data/content/social/factions.yaml` (scope the value to what the blast-radius check in the
  point above supports — `["NATURAL_TERRAIN"]` if safe corpus-wide, a narrower/no-op scoping if
  not), recompile `urban_political` and `generated_frontier_3_42`, and update
  `docs/parity_ledger/world_dynamics.yaml` WORLD-029/WORLD-060 evidence.
- Coordinate with `TCK-20260710-HAZARD-KIND-CORPUS-WIDE` (Phase 1.1, currently in progress in
  `tickets/inprogress/`): that ticket added (or will add) a temporary, narrowly-scoped test-level
  exception for the `town_council`/`bandit_road` case in
  `tests/unit/worldassembly/test_corpus_diversity.py`, explicitly citing this ticket as the
  pending formal ruling. Once this ticket lands, either remove that temporary exception (if the
  mechanism now naturally passes under ruling (b)) or update its comment to cite this ticket's
  landed ruling instead of "not yet its own ticket" (if ruling (a) keeps the carve-out permanent).
  Check that ticket's current state at implementation time — do not assume which state it is in.
- Run the relevant regression checks for both affected worlds (`test_population_stability`-style
  tests, `test_hazard_kind_matches_populating_faction_immunity` /
  `test_hazard_kind_completeness`) to confirm 0 regressions from whichever path is taken.

## Out of Scope
- Re-deciding or touching `bandit_company`'s existing `NATURAL_TERRAIN` immunity at `bandit_road`
  — already correct, not in question.
- `merchant_league`'s own hazard exposure at `bandit_road` (also flagged, unresolved, in both
  prior investigations) — a related but textually distinct question the request did not scope in.
  If the ruling's rationale mechanically also applies to `merchant_league`, note that explicitly
  in Implementation Notes as a candidate follow-up; do not implement a `merchant_league` change
  under this ticket without a separate scoping pass.
- Race-level `hazard_immunities` (the `RaceDefinition` extension point documented as deliberately
  out of scope by `TCK-20260701-HAZARD-NATIVE-IMMUNITY`) — not needed here.
- Any change to `src/world/environment.py::calculate_hazard_drain` or
  `src/worldassembly/resolver.py`'s `"PHYSICAL"` hazard_kind default — both are working as
  documented and unrelated to this decision.
- P2-O / Phase 1.1 (`TCK-20260710-HAZARD-KIND-CORPUS-WIDE`'s corpus-wide completeness test
  extension) — separate ticket; this ticket only coordinates with it, does not implement its scope.
- Phase 0.1 (tick-budget-throttle long-run calibration reliability, F6/P2-P) — unrelated engine
  determinism question; do not conflate with this content/design decision.
- Any world beyond `urban_political` and `generated_frontier_3_42` unless the blast-radius check
  above finds `town_council` genuinely populated in another hazardous region — if so, that is a
  new finding to flag for a follow-up ticket, not to silently fix here.

## Acceptance Criteria
- [ ] Exactly one DA ruling is made and recorded (not merely investigated) on whether
      `town_council` should be exempt from `bandit_road`'s `NATURAL_TERRAIN` hazard drain,
      explicitly applicable to both `urban_political` and `generated_frontier_3_42`.
- [ ] If ruled intentional: `docs/guidelines/intentional_divergences.md` gains a new
      Divergence Summary Table row plus a Detailed Record section with rationale class and a
      verification/test-path citation; `data/content/social/factions.yaml` and
      `docs/parity_ledger/world_dynamics.yaml` are unchanged by this ticket.
- [ ] If ruled a genuine gap: `town_council` in `data/content/social/factions.yaml` gains a
      `hazard_immunities` entry; `urban_political` and `generated_frontier_3_42` are recompiled;
      `docs/parity_ledger/world_dynamics.yaml` WORLD-029/WORLD-060 `v2_evidence` is updated to
      reflect the new content; a regression run shows 0 new failures on the existing
      `test_hazard_kind_matches_populating_faction_immunity` / `test_hazard_kind_completeness` /
      population-stability tests for both worlds.
- [ ] The blast-radius check against `trading_company_hub.yaml`'s `hometown` region (and any
      other corpus module pairing `town_council` with `hazard_level > 0`) is performed and its
      result recorded in Implementation Notes, regardless of which ruling is made.
- [ ] `TCK-20260710-HAZARD-KIND-CORPUS-WIDE`'s temporary `town_council`/`bandit_road` test-level
      exception (if present at implementation time) is reconciled with this ticket's ruling —
      either removed (ruling (b), mechanism now passes unaided) or its comment updated to cite
      this ticket instead of "not yet its own ticket" (ruling (a)).
- [ ] `docs/plans/audit_fix_plan.md` P2-Q and `docs/plans/simq_development_roadmap.md` Phase 1.2
      are updated to reflect closure, citing this ticket.

## Related Tickets
- TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE (done — first independent discovery, Risk #2)
- TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE (done — second independent
  discovery, Root cause 2)
- TCK-20260701-HAZARD-NATIVE-IMMUNITY (done — origin of the `hazard_kind`/`hazard_immunities`
  mechanism this ruling operates within; corrected faction-declared-endurance design)
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS (done — established the `hazard_kind` +
  `hazard_immunities` corpus-authoring pattern this ticket would reuse under ruling (b))
- TCK-20260710-HAZARD-KIND-CORPUS-WIDE (in progress — Phase 1.1/P2-O sibling; holds a temporary
  stand-in test exception for this exact case pending this ticket's ruling; coordinate, do not
  duplicate its test-file scope)

## Related Docs
- `docs/mechanics/05_world_evolution.md` §3 "Regional Sovereignty" → "Hazard Impacts" / "Native
  Endurance to a Region's Hazard Kind" — authoritative mechanism this ruling must stay consistent
  with; explicitly states endurance is faction-declared, never inferred from hostility, and warns
  against "blanket/wildcard" style reasoning.
- `docs/plans/audit_fix_plan.md` P2-Q — this ticket's direct source entry.
- `docs/plans/simq_development_roadmap.md` Phase 1.2 — sequencing context.
- `docs/plans/idea_simq_near_perfect_roadmap.md` Thread 5 — evidence synthesis / ranking rationale.
- `docs/guidelines/intentional_divergences.md` — target doc if ruling (a).
- `docs/parity_ledger/world_dynamics.yaml` WORLD-029, WORLD-060 — hazard-drain/native-endurance
  parity entries; update only if ruling (b).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE/investigation.md` Risk/Open
  Question #2 (`town_council`/`merchant_league` at `bandit_road`, first discovery)
- `stored_artifacts/TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE/investigation.md`
  Root cause 2 (identical case re-surfaced, second discovery)
- `stored_artifacts/TCK-20260701-HAZARD-NATIVE-IMMUNITY/investigation.md` (mechanism design;
  rejected-design section directly informs why a blanket/inferred immunity must not be used here)

## Related Code Areas
- `data/content/social/factions.yaml` (`town_council` entry, lines 12-19 — edit target if
  ruling (b))
- `data/content/world_modules/bandit_road_trade_pressure.yaml` (`bandit_road` region — read-only
  reference; already correctly declares `hazard_kind: "NATURAL_TERRAIN"`)
- `data/content/world_modules/trading_company_hub.yaml` (`hometown` region — blast-radius check
  target)
- `docs/guidelines/intentional_divergences.md` (edit target if ruling (a))
- `src/world/environment.py::EnvironmentService.calculate_hazard_drain` (read-only reference —
  mechanism consumer, not to be modified)
- `tests/unit/worldassembly/test_corpus_diversity.py` (read-only reference / coordination point
  with `TCK-20260710-HAZARD-KIND-CORPUS-WIDE`'s temporary exception, not this ticket's own edit
  target unless reconciling that ticket's carve-out)
- `data/worlds/urban_political/`, `data/worlds/generated_frontier_3_42/` (recompile targets if
  ruling (b))

## Assumptions / Open Questions
- Assumes the request's scope (`town_council` only, not `merchant_league`) is deliberate, since
  P2-Q's own text names only `town_council`. If the implementer's blast-radius/rationale work
  finds the two cases are inseparable in practice, that should be flagged, not silently expanded
  into a `merchant_league` fix under this ticket (see Out of Scope).
- Assumes `TCK-20260710-HAZARD-KIND-CORPUS-WIDE` (Phase 1.1) may complete before, during, or
  after this ticket — its own ticket text explicitly designs for either ordering ("if P2-Q lands
  first, prefer letting the test pass unaided"). This ticket must check that sibling ticket's live
  state at implementation time rather than assume it is still pending.
- Assumes the blast-radius check on `trading_company_hub.yaml` is answerable by reading composed
  world specs (`data/worlds/*/resolved/world.resolved.yaml` or equivalent) rather than requiring
  new investigation infrastructure — if `town_council` turns out to be populated there in some
  composed world, that is new information that should inform (not be assumed away from) the
  ruling's scope (e.g. a narrower per-region mechanism might be preferred over a blanket faction
  field if the two regions warrant different outcomes).
- If ruling (b) is chosen and blast radius is NOT clean (i.e., an unwanted exemption would appear
  elsewhere), the fallback per the Mechanics Bible's `hazard_kind` taxonomy is to introduce a new,
  narrower `hazard_kind` value (e.g. distinguishing "settled trade-hub ambient risk" from
  "wilderness road hazard") rather than force a blanket `NATURAL_TERRAIN` grant — this narrower
  path was not fully explored during scoping and is left to the ticket's own investigation phase.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
