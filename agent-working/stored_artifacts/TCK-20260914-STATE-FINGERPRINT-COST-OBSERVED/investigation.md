---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED
date: 2026-10-18
tags: [performance, benchmarking]
---

# Investigation: TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED

- Evidence so far (`docs/performance/tick_cost_growth.md` section 4): `fingerprint` 0.0 % of py-spy samples in every non-audit profile, 3.5 % under `audit_mode` (strategic_100). All of them ran `no_replay=True`.
- Replay-only call sites: `src/engine/kernel.py:654-664` (REFINED_UPDATE carries `self._state.fingerprint()` when `policy.replay_allowed`), `kernel.py:1130-1131` (`CanonicalHashScheduler().compute_digest` when `replay_allowed` and (audit or `replay_richness == "FULL"`)), `kernel.py:1135-1143` (TICK_END emit and `on_tick_end`). `kernel.py:420` and `:1096` are audit-only and already measured.
- `no_replay` is applied twice: at construction (`kernel.py:200`) and after every governor update (`kernel.py:562`), so `flags["no_replay"]=False` alone is enough; replay is then allowed whenever the mode's policy allows it (NORMAL: allowed, richness FULL, so both (a) and (b) run). The governor can switch it off under pressure, so each tick records the policy it ran under.
- The kernel creates `data/runs/<run_id>/` (observability, manifest) with or without replay; only the replay writer's chunks follow the injected `ReplayManager` directory. Those run directories are cleaned by run id with `done_checker_static --clean-data-runs`, never `rm data/runs/*`.
- Open until measured: whether canonical-contract `strategic_100` stays in NORMAL (earlier records show CONSTRAINED for 20 ticks), which decides whether replay is allowed on most ticks.
