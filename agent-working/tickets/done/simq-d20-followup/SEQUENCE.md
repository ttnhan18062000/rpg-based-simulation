# Implementation Sequence — D20 SimQ Integration Follow-Up

Source: `docs/audits/D20_simq_integration.md` — Actionable Next Steps (2026-07-01 re-run)
No parent epic ticket — these are independent follow-ups to the closed
`TCK-20260628-SIMQ-EPIC`.

---

## Stage 1 — No blockers (run in any order / parallel)

```
TCK-20260701-SIMQ-AGENCY-ROUTING-DOC
TCK-20260701-SIMQ-CAMP-PARITY-CLEANUP
TCK-20260701-SANDBOX-MONSTER-BALANCE
TCK-20260701-SIMQ-LOOP-WINDOW-TUNE
```

- `SIMQ-AGENCY-ROUTING-DOC` and `SIMQ-CAMP-PARITY-CLEANUP` are pure documentation fixes
  with no code dependency on anything else in this batch.
- `SANDBOX-MONSTER-BALANCE` touches `data/worlds/sandbox_world/` only. It does not
  intersect `CALIBRATE-REFRESH`'s scope (dungeon_crawl/urban_political), so no gate needed.
- `SIMQ-LOOP-WINDOW-TUNE` has no prerequisite, but see the Stage 2 gate below —
  **finish this one before starting Stage 2**, even though nothing blocks it from starting.

## Stage 2 — Requires SIMQ-LOOP-WINDOW-TUNE to be resolved first

```
TCK-20260701-SIMQ-CALIBRATE-REFRESH
```

**Why the gate:** `SIMQ-CALIBRATE-REFRESH` re-runs `tools/calibrate_simq.py` against
dungeon_crawl/urban_political and commits the resulting event counts/grades into
`docs/plans/audit_fix_plan.md` and `docs/simulation_quality/event_type_coverage.md` as the
new baseline. `SIMQ-LOOP-WINDOW-TUNE` may change `config/simulation_quality/
detection_params.yaml` (window size / loop threshold), which directly changes how many
`hazard_active`/`quest_active`-tagged events get suppressed per run — i.e. it changes the
numbers `CALIBRATE-REFRESH` would produce.

Running refresh first means: if the window-tune ticket later changes the threshold, the
just-committed calibration numbers go stale immediately and the refresh has to be redone.
Running window-tune first (even if it concludes "no change needed") means the refresh only
happens once against final settings.

If `SIMQ-LOOP-WINDOW-TUNE`'s sweep concludes "200/0.70 confirmed correct, no change" —
the gate still stands procedurally (confirms settings are final before baselining) but
costs nothing extra, since no YAML changes result.

---

## Status at creation

| Ticket | Status | Gate |
|---|---|---|
| TCK-20260701-SIMQ-AGENCY-ROUTING-DOC | OPEN | None |
| TCK-20260701-SIMQ-CAMP-PARITY-CLEANUP | OPEN | None |
| TCK-20260701-SANDBOX-MONSTER-BALANCE | OPEN | None |
| TCK-20260701-SIMQ-LOOP-WINDOW-TUNE | OPEN | None |
| TCK-20260701-SIMQ-CALIBRATE-REFRESH | OPEN | SIMQ-LOOP-WINDOW-TUNE |
