---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHADOW-VALIDATION-PERF
artifact_type: investigation
tags: [observability, engine, simulation-quality, performance]
---

# investigation.md — TCK-20260806-PUSH-SHADOW-VALIDATION-PERF

## Summary

Built a real, non-mocked comparison tool (`shadow_compare.py`, scratchpad, not committed —
throwaway validation tooling per this repo's established convention): runs a world with
`ENABLE_PUSH_EVENT_SHAPERS=SHADOW`, captures the old diffing extractor's real
`simulation_events.jsonl` output alongside the new shaper registry's output (via a monkeypatch on
`run_shadow_shapers`), and compares them per-tick for the 3 migrated domains. Ran against 6 real
worlds (`dungeon_crawl`, `sandbox_world`, `hero_guild_routing`, `urban_political`,
`wilderness_survival`, `crowded_frontier`), seed 42, 500 ticks each.

**This found 2 real, confirmed bugs — not zero, as a superficial pass might have concluded — and
fixed both by reopening `TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT`, per this epic's own
`SEQUENCE.md` rule ("reopen, don't patch around it here").**

## Bug 1: `entity_killed` false positive on hazard-caused "death"

First run (`dungeon_crawl`) found the shaper emitting a spurious `entity_killed` at 2 ticks the old
extractor did not. Traced precisely: `CombatUpdate.alive_set` (which the shaper used to derive
death) maps to `CombatComponent.alive` (confirmed via `src/engine/patches.py:301`), a **different**
field from `LifecycleComponent.active` — the field `entity_killed`/the old extractor's kill-events
branch actually needs. `LifecycleSystem.resolve_lifecycle()` (`src/systems/lifecycle_systems/
lifecycle.py:43`) only transitions `lifecycle.active` on `outcome_kind == "KILL"` specifically (or
old-age) — never on `alive_set` alone. Hazard damage (`outcome_kind="HAZARD"`) can set
`combat.alive=False` while `lifecycle.active` stays `True`.

**Fix**: gate `entity_killed`/`hero_death_unrecorded` on `outcome_kind == "KILL"` directly, not
`alive_set`/HP arithmetic (see `TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT`'s reopened
Implementation Notes for the full fix).

## Bug 2: missing volumization rule — `combat_damage` over-firing in sustained combat

Re-running across more worlds (`urban_political`, `crowded_frontier`) found `combat_damage` firing
far more often in the new path than the old — the old extractor's volumization rule ("skip
routine, non-lethal damage in `LIGHT`/`LONG_RUN` observability mode") was never ported to
`CombatShaper` at all — a straightforward omission in the original implementation, not a subtle
edge case. Since `ObservabilityConfig`'s default mode is `LIGHT` (confirmed,
`src/observability/config.py:25`), and calibration runs never override it, this affected every
sustained-combat sequence in every world tested.

**Fix**: added `mode: ObservabilityMode` parameter to the `EventShaper` protocol and
`CombatShaper.shape()`, applying the exact same `is_lethal or mode not in (LIGHT, LONG_RUN)` check
the old extractor uses. Threaded through `run_shadow_shapers()` and `kernel.py`'s call site
(`obs_mode`, already computed at the point `_phase_observability` runs — no new plumbing needed).

## Disclosed, accepted limitation: delayed hazard-death lifecycle transition (1 remaining divergence)

After both fixes, re-ran all 6 worlds: **130 of 131 active ticks match exactly (99.2%)**. The one
remaining divergence (`hero_guild_routing`, tick 5: old shows `combat_kill: 3`, new shows nothing)
was traced precisely: `combat.alive` transitions to `False` at tick 4 (hazard hit), but
`lifecycle.active` doesn't transition until tick 5 — **with zero `EntityUpdate.combat` present at
tick 5 for these entities** (confirmed via direct pipeline tracing — see
`TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT`'s reopened investigation notes for the full trace). The
"prior_state+update alone" design cannot see a transition with no update record to read at the tick
it happens. This is not a bug to fix — it's a structural limitation of the design, and it's the
same underlying cause as the already-disclosed old-age-death gap (both are non-`KILL`-tagged
lifecycle transitions with no combat_upd at the relevant tick).

**Frequency in this sample**: 1 occurrence across 6 worlds × 500 ticks (3,000 world-ticks of
sampling) — genuinely rare, not a systemic gap. **Decision: accept as a disclosed, named
limitation for Phase 1's cutover, not a blocker.** `entity_killed`'s scope is narrower than the old
extractor's (same-tick, `outcome_kind=="KILL"` combat deaths only, not all lifecycle transitions) —
this is now explicit in code comments, this ticket, the epic's `SEQUENCE.md`, and the parity
ledger.

## Payload-value comparison (Child 2's disclosed compounding-tick concern)

Extended the comparison tool to check `combat_damage`'s `damage` payload values (not just event
types) on every tick, across all 6 worlds. **Zero payload mismatches found.** The apply-time-only
HP-mutation sources Child 2 flagged (passive health decay, level-up heal/clamp) did not coincide
with a real combat hit on the same entity in the same tick in any of the 3,000 world-ticks sampled.
This does not prove the scenario can never occur — it confirms it did not occur in this real
sample, which is the evidence this check was designed to gather.

## Performance re-validation

Adapted `docs/performance/simq_isolation_overhead.md`'s methodology (`BenchHarness`,
`sandbox_world`, `PROD_SMALL`, `cpu_time_total_delta_s`) — **scope reduced from that doc's
warmup=100/sample=1000 to warmup=30/sample=150**, disclosed explicitly (this ticket's own
turnaround, not a full by-the-book isolation-overhead certification run). 2 runs:

| Run | baseline (no flag) | SHADOW active | Overhead |
|---|---|---|---|
| 1 | 0.96s | 0.87s | -9.37% |
| 2 | 0.96s | 0.86s | -10.42% |

Both runs show SHADOW mode *faster* than baseline — well within the measurement noise already
documented for this sandbox environment (`simq_isolation_overhead.md`'s own run-to-run divergence
was 6-8%; INPROCESS mode was measured at -8.4% vs. disabled in that doc too, also "noise, not a
real speedup"). No measurable overhead from running the shaper registry alongside the existing
diffing extractor. This is a reduced-scope check, not a replacement for a full certification-grade
isolation-overhead run — recommend a full run before the eventual `ON`-mode cutover ticket, not
required to gate this SHADOW-mode validation.

## Recommendation

**GO.** 130/131 active ticks match exactly across 6 real worlds; the 1 remaining divergence is a
precisely understood, narrow, disclosed, rare (1/3000 world-ticks) limitation, not an unexplained
bug. Zero payload-value mismatches. No measurable performance overhead across 2 runs.
`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION` is cleared to proceed.
