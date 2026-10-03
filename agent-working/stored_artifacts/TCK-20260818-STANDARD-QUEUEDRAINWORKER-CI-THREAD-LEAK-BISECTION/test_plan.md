---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260818-STANDARD-QUEUEDRAINWORKER-CI-THREAD-LEAK-BISECTION
artifact_type: test_plan
tags: [observability, investigation, testing, root-cause]
---

# Test Plan — TCK-20260818-STANDARD-QUEUEDRAINWORKER-CI-THREAD-LEAK-BISECTION

No code was changed, so there is no regression test to add. This document records the
verification commands actually run to attempt reproduction, for anyone continuing this
investigation.

## Commands Run (all synchronous, foreground, `CI=true`, `--resource-budget large` where noted)

```
# Fast-lane scope (matches all 9 passing fast-lane CI jobs combined) — chunked across:
pytest tests/unit/observability tests/simulation_quality tests/unit/engine -m "not slow and not extra_slow" -q
pytest tests/unit/actions tests/unit/ai tests/unit/tools tests/regression \
  tests/agent_orchestration_claude_adapter tests/agent_orchestration tests/agent_codex_posttool_adapter \
  tests/agent_replay tests/agent_codex_pilot_orchestration tests/agent_replay_codex \
  tests/agent_codex_live_transport tests/agent_orchestration_codex_adapter \
  tests/agent_codex_realrepo_pilot_harness tests/agent_codex_pilot_guardrails \
  tests/agent_codex_runtime_shadow tests/agent_codex_pilot_executor -m "not slow and not extra_slow" -q
pytest tests/api tests/engine -m "not slow and not extra_slow" -q
pytest tests/integration/kernel tests/integration/observability tests/unit/kernel tests/unit/core \
  tests/observability -m "not slow and not extra_slow" -q
pytest tests/perf tests/certification tests/arena tests/replay tests/world tests/scenarios -m "not slow and not extra_slow" -q
pytest tests/integration --ignore=tests/integration/kernel --ignore=tests/integration/observability \
  -m "not slow and not extra_slow" -q
pytest tests/unit/<all remaining subdirs, 2 batches> -m "not slow and not extra_slow" -q
pytest tests/social tests/strategic tests/strategy tests/cognition tests/combat tests/systems \
  tests/tactical tests/town tests/quests tests/inventory tests/progression tests/contract \
  tests/architecture tests/integrity tests/logging tests/platform tests/verify tests/config \
  tests/cli tests/rpg tests/refactor tests/static tests/fixtures tests/helpers tests/docs \
  -m "not slow and not extra_slow" -q
```
Result: real pre-existing failures only (SimQ calibration drift, live-server-subprocess
connection-refused tests that spawn a bare `python3` missing `pydantic`, one perf-flake timing
assertion) — zero `QueueDrainWorker thread leak detected` sentinel failures.

```
# Slow-lane scope — exact CI step command from .github/workflows/test.yml:265-266, chunked:
CI=true pytest tests/perf -m "slow or extra_slow" --resource-budget large --tb=short -q
CI=true pytest tests/simulation_quality -m "slow or extra_slow" --resource-budget large --tb=short -q
CI=true pytest tests/integration/certification tests/integration/scenarios \
  tests/unit/engine/test_scenario_checkpointer.py tests/unit/social/test_multi_hero.py \
  tests/arena/test_arena_regional_control.py tests/integration/kernel/test_milestone_b_closure.py \
  tests/regression/test_behavioral_5k.py tests/unit/economy/test_economy_health_monitor.py \
  tests/unit/worldassembly/test_hero_guild_routing_population_stability.py \
  -m "slow or extra_slow" --resource-budget large --tb=short -q
CI=true pytest tests/certification/test_cert_long_run_stability.py -m "slow or extra_slow" \
  --resource-budget large --tb=short -q   # all 3 skip under CI=true, matching real CI
pytest tests/arena/test_arena_stress.py -m "slow or extra_slow" --resource-budget large --tb=short -q
```
Result: 9 pre-existing SimQ grade-anchor-drift failures (already tracked elsewhere), 0 leak
sentinel failures.

```
# Confirmed structurally irrelevant (no Kernel/EventRecorder/QueueDrainWorker usage):
grep -l "Kernel(\|EventRecorder(\|QueueDrainWorker" tests/tools/test_knowledge_search.py \
  tests/tools/test_kgmcp_phase2_baseline_recomparison.py \
  tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py \
  tests/tools/test_kgmcp_phase4_direct_tool_comparison.py
# -> no matches
```

## Not Verifiable In This Session

- A true single, unchunked `pytest tests/ -m "slow or extra_slow" --resource-budget large ...`
  run across the full ~166-test scope in one process (exceeds this sandbox's 600s per-command
  foreground ceiling; a background run was attempted and killed per explicit instruction not to
  background-and-wait). This is the one scenario (cross-test/ordering-dependent state) this
  investigation's chunked reproduction could not rule out — see `investigation.md` hypothesis 2.
- The real CI run's raw log text (network-blocked in this sandbox; see `investigation.md`).
