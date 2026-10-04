---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-04
tags: [mcp, live-map, testing]
---

# Retention, `gc` and rollback (visual assets)

Result of `TCK-20261004-VISUAL-ASSETS-RETENTION-AND-ROLLBACK`. Decisions: the owner approved the retention bound and named the rollback/recall owner on 2026-10-04 (blocking
questions); the planner fixed the `gc` scope the same day. Nothing here deploys anything or activates anything.

## Retention (`U-05`, the last unset row): approved

`config.MAX_UNADOPTED_INTAKE_AGE_DAYS = 30`, approved 2026-10-04 (rule R0: a judgment, not a measurement; `docs/assets/budgets.md`). Measured: one adopt + build + release adds about 4.4 KB of tracked
files; a local intake with its review export about 6 KB, up to about 2.3 MB at the size bounds. `gc` may list (and with `--delete` remove) a PASSED, never-adopted, unrevoked intake and its review export
once the intake's own timestamp is more than 30 days old. Exactly 30 days is kept. Dry run is the default. `gc` takes a cutoff timestamp (now minus 30 days) computed by the CLI, because library code may not import `datetime` or read the clock (a test enforces it); timestamps are fixed-width UTC, so a string comparison is a time comparison.

## What `gc` protects (`AM-C09`: judged as "`gc` removes no protected object")

Protected = all tracked state (`sources/`, `provenance/`, `generated/` records, `manifests/`) + PASSED un-adopted intakes younger than the bound + any intake an adoption record refers to + referenced review
evidence (tracked inside `provenance/`). `gc` never deletes a tracked object or record: tracked history is git's job and the audit chain is hash-anchored. Retained releases are derived (every committed
candidate under `manifests/candidates`), not declared. A dry run also prints "kept: tracked history, never deleted" for artifact records no committed candidate refers to (none in the real catalog today).
If `gc` ever gains a deletion kind for tracked objects, a typed roots record must exist first, in its own ticket. Which frontend builds may still be in use is a deployment fact the `AM-M6` charter declares
(ticket 5), not store state.

Proof: `tests/visual_assets/store/unit/test_gc.py` (17 tests). Mutants, each failing a named test: age guard dropped (young intake listed), adoption guard dropped (old adopted intake listed), age bound infinite
(old intake kept), boundary off by one (an intake exactly on the cutoff listed), unreferenced report emptied.

## Store operations (`ADR D18`, owner, 2026-10-04)

- **Single operator, no lock.** One store command at a time; the rule, not a lock, covers two commands at once. The code still defends only a single operator (all-or-nothing staged writes, exclusive-create release publishing). Reverses when a second operator or automation runs store commands.
- **`gc --delete` keeps no record.** It prints each item it removes (`deleted <kind> <name> (<reason>)`, the `gc` branch of `visual_assets/store/cli.py`) and cannot delete tracked state, so no protected record is lost. The printed line is the only trace.
- **Growth review by hand.** When the tracked catalog passes 50 MB (about 0.9 MB today, `du -sh visual_assets/catalog`) the owner reviews it. A review trigger, not an enforced limit; nothing checks it.

## Rollback drill (`AM5-W09`, `AM-C06`) under Profile A (ADR D8)

Rollback is redeploying the previous whole frontend build. In the drill, "previous release" = the previous build's runtime fixture set (the synthetic rehearsal export, catalog `rehearsal`) and "new" =
the pilot export (`pilot/rc-0003`: the rc-0002 slots under the registry that also names the other terrain keys; `rc-0001` and `rc-0002` are retained history). `frontend/src/visualAssets/__tests__/rollbackDrill.test.ts`:

| Combination | Result |
|---|---|
| new client + new release | the tile on every forest cell (baseline) |
| new client + old release | `terrain.forest` is absent, so every forest cell shows the flat fill |
| old client + new release | a mis-deploy, defence in depth only (under Profile A an old client never receives a new manifest, because the manifest is bound to its build): the old rehearsal scene knows none of the keys and shows only its typed `?` fallbacks, no image |
| recall (key removed from the release) | every forest cell shows the flat fill |
| release switched mid-load | the superseded release's late images are dropped and never drawn; only the current release's image appears |

Mutant "accept a mixed snapshot" (the loader no longer drops a superseded view's late completions) fails the mid-load test. This is a harness drill: no real deployment, no old browser build, no
real rollback authority was exercised.

## Rollback / recall owner

Named by the owner on 2026-10-04: **nhan (owner)**, recorded verbatim from the blocking question. This names a person for the drill; the `AM-M6` charter must still confirm it.
