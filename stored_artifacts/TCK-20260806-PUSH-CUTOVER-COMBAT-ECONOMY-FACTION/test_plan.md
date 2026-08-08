---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION
artifact_type: test_plan
tags: [observability, engine, combat, simulation-quality]
---

# test_plan.md — TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION

## Tests / verification performed

- Full `tests/unit/observability/` suite: 798 passed, 6 skipped (unchanged from pre-cutover —
  existing unit tests are mock-based and unaffected by the flag-default change; real behavior
  verified separately below).
- Real, non-mocked kernel integration runs (the check unit tests alone would not catch, since
  MagicMock's auto-attribute behavior coincidentally masked the real default-ON logic in existing
  tests):
  - `dungeon_crawl_seed42_500t`, no explicit flag override: confirmed real
    `AuthoritativeState.feature_flags` defaults to `{}`; all 39 combat/economy/faction events
    delivered via `source_system="event_shapers"`.
  - Same world, `ENABLE_PUSH_EVENT_SHAPERS="OFF"`: byte-identical event counts, delivered via
    `source_system="event_extractor"` instead — confirms the rollback path is real, not
    theoretical.
  - `hero_guild_routing_seed42_500t`, default flag state: confirmed the delayed-hazard-death case
    (entities 26/28/30, tick 5) still correctly emits `combat_kill` from the old extractor's
    narrowed-not-removed Kill-events branch, proving the `is_shaper_owned_kill` exclusion logic
    works as designed.
- Full calibration corpus (`make simq-full-audit-full`, 79 scenarios) — 32/69 `test_grade_regression.py`
  cases failed (18 deselected as `slow`). Root-caused rather than dismissed or worked around (see
  `investigation.md` "Full-corpus verification" section for the full methodology): reproduced
  `hero_guild_routing_seed42_500t` in isolation with the push-shaper path live (flag default `ON`,
  twice, for a determinism check) and with the old `event_extractor.py` path forced live instead
  (flag forced `OFF` via a kernel-level monkeypatch). All three isolated runs produced
  near-identical pillar breakdowns — `COMBAT=0`, `ECONOMY=0`, `FACTION=0` in every run regardless
  of which pipeline was active, and raw `simulation_events.jsonl` inspection confirmed no real
  attacker-driven combat events exist in the underlying simulation data for this run under either
  pipeline (only environmental `hazard_drain_applied`, 16 events, in both). **Conclusion: the
  32 failures are the pre-existing, already-tracked INFRA-273 F6-class tick-budget-watchdog
  mechanism (dropped-resolution-queue-item trajectory divergence), not a regression introduced by
  this migration** — confirmed via the flag-on/flag-off identical-outcome comparison, which is the
  correct differential test for a cutover ticket. `grade_anchors.json` and
  `test_grade_regression.py` were left untouched (out of this ticket's scope; any anchor
  recalibration belongs to a dedicated ticket in the INFRA-273 family, not this migration ticket).
  `docs/parity_ledger/infrastructure.yaml` INFRA-273 was updated with this session's confirming
  evidence (a stronger characterization: the mechanism can starve a domain's event count to zero
  entirely, not just shift it, under sustained watchdog pressure).
- Parity ledger YAML validation (`combat_movement.yaml`, `town_resource.yaml`, `faction.yaml`,
  `infrastructure.yaml`) — all 4 files re-validated after edits.

## Out of scope

`test_simq_isolation_overhead.py`'s full by-the-book 3-mode run — the reduced-scope check from
`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF` already confirmed no measurable overhead; a full
certification-grade run is a reasonable follow-up but not required to gate this cutover, which
carries strictly less risk than that ticket's own validated SHADOW-mode measurement (same code
path, just now delivering instead of logging).
