---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION
artifact_type: investigation
tags: [world, observability, determinism, root-cause]
---

# Runtime evidence — `regional_sovereignty` ownership writers

Prepared for `world-rule-catalog-design` at its request, in the shape it asked for, to support the
`regional_sovereignty` registry entry moving from `instrument: code_trace` to a runtime instrument.
**Markdown, not `.json`** — `.gitignore` drops `.json` under artifact dirs, so cited evidence in that
format never reaches the remote.

Registry content is the catalog session's lane. **This file is evidence only; it proposes no registry
edit.**

## Engine SHA and configuration

| | |
|---|---|
| Engine SHA | `6d630250d` (`origin/main` at measurement time) |
| Profile | `PROD_SMALL`, flag `no_frame_pacing` |
| Driver | real `Kernel.tick_once()` / `AuthoritativeApplyPipeline.refine()` |
| Instrumentation | monkeypatch wrappers from outside the repo; no repo file modified |
| **`audit_mode`** | **`False` — see the caveat in §4. This is a material limitation.** |

Worlds and seeds, 2000 ticks each:

| world | regions | seed | runs |
|---|---|---|---|
| `frontier_living_world` | 8 | 42 | 3 |
| `crowded_frontier` | 4 | 42, 7 | 1 each |
| `frontier_marches` | 9 | 7 | 1 |
| `urban_political` | 3 | 7 | 1 |

≈48,000 region-ticks of distinct configuration (≈96,000 counting repeats).

## 1. Per writer

Writer 1 = `WorldDynamicsSystem.resolve_dynamics` (phase `world_dynamics`, `pipeline.py:348`),
unconditional sweep over all regions.
Writer 2 = `FactionInfluenceService.process_influence_shift` (phase `lifecycle`, call site
`lifecycle.py:298` behind `if recent_deaths:` at `294`), death-gated.

| | writer 1 | writer 2 |
|---|---|---|
| Calls | 2,000/run (every tick) | ~230 total (one per tick with a death), over ~220 deaths |
| Non-zero `influence_delta` region updates produced | — (does not produce influence) | ~80 |
| **`owner_faction_id_set` ownership writes** | **3** across all runs | **0** |
| Emits `SOVEREIGNTY_SHIFT` | yes (`world_dynamics.py:91-100`) | **no** |

## 2. Region-tick overlap count

**0.** Both writers wrote `owner_faction_id` for the same region in the same tick **zero** times:
0 of ≈48,000 region-ticks; 0 of 14,000 ticks.

## 3. Observed durable flips — and which writer produced them

This is the question the catalog session specifically asked, because it bears on whether the registry
binding is right.

| world | tick | region | transition | **writer** |
|---|---|---|---|---|
| `frontier_living_world` | 1203 | `goblin_camp` | `None → HERO_GUILD` | **writer 1** (`world_dynamics`) |
| `frontier_marches` | 1503 | `goblin_camp` | `None → HERO_GUILD` | **writer 1** (`world_dynamics`) |

**Both flips were writer-1-only**, in ticks with no writer-2 ownership write at all.

**Direct answer to the registry question: yes — in these runs `FactionInfluenceService` is not the
mechanism that moves ownership.** It executes (~230 calls) and it does move *influence* (~80 delta
updates), but it never moved ownership. If the `regional_sovereignty` note claims
`FactionInfluenceService` is "the real, live ownership-tracking mechanism", that is **not borne out in
practice** for this corpus; `WorldDynamicsSystem` is. Whether the binding should be re-pointed is the
catalog session's call, not mine — this is the measurement it asked for.

Neither flip was same-tick with its causing death. Structurally it cannot be: see §5.

## 4. Caveat that limits these numbers — read before citing any count

**The runs were made with `audit_mode=False`, and they should not have been.** A follow-up probe
confirmed engine nondeterminism on the same world and seed and traced it to
`src/engine/kernel.py:612-620`: when `not self._audit_mode and elapsed > max_tick_budget_ms`, the
mid-tick emergency throttle **drops the remaining authoritative result items**. Verified directly in
source.

This is the **known, documented, deliberately deferred** mechanism — `INFRA-273`,
`docs/audits/D06_longrun_health.md` §F6/§F7,
`TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE` — **not a new defect and deliberately
not filed as one.** `docs/engine/deterministic_execution.md` Extension Rule 5 already mandates
`audit_mode` for determinism-verifying runs.

Consequences for this evidence:

- **Every count above is order-of-magnitude, not exact.** Dropped result items make per-tick counters
  under-report.
- **The zeros rest on structure, not on the counts** (§5). A dropped-item artifact could hide an
  occurrence — which is why §2's result is stated as a true zero *for this corpus*, never as proof of
  impossibility.
- **A re-run with `audit_mode=True` and a relaxed `max_tick_budget_ms` would be needed for exact
  figures.** Sequential execution does *not* substitute: a single-threaded `LocalSequentialExecutor`
  still diverged (200 ticks, 3 runs, deaths 16/14/14, three distinct canonical hashes).

If the registry entry needs exact counts rather than magnitudes, say so and I will re-run under
`audit_mode`.

## 5. Why the zeros are structural, independent of the counts

- Writer 1 settles ownership against **last tick's** influence. `influence.py:62` is the only producer
  of `WorldUpdate.influence_delta` in `src/` (exhaustive grep) and runs 13 phases *after* its only
  consumer `world_dynamics.py:89`. Instrumented at that exact read: 24,000 executions, **0 nonzero**.
- Writer 2's conquest branch emits `MONSTER_HORDE`; so does writer 1's. Identical values cannot
  disagree.
- So the **only** expressible disagreement is writer 1 `HERO_GUILD` vs writer 2 unowned, which
  requires an invader owner **and** influence ≥ +50 **and** an in-region death in one tick — a state
  writer 1 destroys on the first tick it exists.
- Influence never reaches ±50 in most regions: most sit pinned at exactly `0.0` for the whole run,
  while the one or two town regions saturate at 100–135 and are already protector-owned, so writer 1's
  `is_protector` guard blocks. **Ownership dynamics are near-inert in corpus worlds.** Offered as the
  most consequential observation here; it is balance work, parked by `owner_decision_memo.md` row 7,
  and deliberately not filed.

## 6. Positive controls, both directions

Reported because a zero with no control is not a measurement.

- **Writer-1 hook, detection:** captured a real write
  `(tick=1203, goblin_camp, HERO_GUILD, owner_before=None, influence=50.0)`, matching the
  independently observed durable transition. Instrument and ground truth agree.
- **Writer-2 hook, liveness:** fired on every death tick (27–60 calls/run), proving the wrapper sits
  on the live call path. Its *ownership-write branch* was separately exercised by a constructed
  scenario in which the same hook code did report writes of both the unowned sentinel and
  `MONSTER_HORDE`. So "writer 2 never wrote ownership" is a true zero, not a silent hook.
- **`influence_delta` hook:** on an injected
  `StateUpdate(world_updates={"forest": WorldUpdate(influence_delta=10.0)})` the identical hook
  captured the nonzero. It detects one when present.
- **The overlap path is live, not impossible:** a constructed scenario (invader-owned region,
  influence 55.0, one in-region death) drove both writers in one tick through real `refine()` + apply,
  with writer 2 overriding writer 1 via `WorldUpdate.merge`'s other-wins rule
  (`core/updates.py:882`).

## 7. Reproduce

```
cd <worktree>            # branch sovereignty-ownership-writer
PYTHONPATH=. /home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 \
    -m pytest tests/integration/world/test_region_owner_sentinel.py -q
```

The three tests above assert the sentinel decoding and the liberation path deterministically, with no
instrumentation and no long run. For the corpus counts, the instrumented probe wrapped
`WorldDynamicsSystem.resolve_dynamics`, `FactionInfluenceService.process_influence_shift` and
`LifecycleSystem.resolve_lifecycle` from outside the repo and inspected each returned
`StateUpdate.world_updates[rid].owner_faction_id_set`, plus a per-tick snapshot of every region's
durable `owner_faction_id`. Re-running it for exact figures requires `audit_mode=True` per §4.

## 8. Separate finding the catalog session flagged, verified here

The two management views' `OBSERVED OUTCOME` axis reading
`UNKNOWN -- no runtime evidence currently exists` is a **hardcoded literal**, not a derived value:
`tools/semantic_control_plane/generate_territory_control_view.py:74` (`_OBSERVED_OUTCOME_VALUE`),
injected at `:156`. Verified directly. **No evidence can reach that axis without a tooling change**,
so this file cannot move those rows no matter what it contains. Logged as a foundation finding under
`owner_decision_memo.md` row 7 rather than fixed here; SCP tooling is not this ticket's scope.
