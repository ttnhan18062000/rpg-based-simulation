---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS
tags: [testing, ai, bug]
---

# Investigation — TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS

## Origin
User question this session: "is there any missing tests run in the workflow/action?" — distinct
from "are there failing tests." Investigation compared every job's explicit pytest path list in
`.github/workflows/test.yml` against the real `tests/` directory tree.

## Finding
16 directories with real, collectible test content were never referenced by path in any CI job:
`tests/agent_codex_live_transport` (3), `agent_codex_pilot_executor` (4),
`agent_codex_pilot_guardrails` (8), `agent_codex_pilot_orchestration` (4),
`agent_codex_posttool_adapter` (13), `agent_codex_realrepo_pilot_harness` (3),
`agent_codex_runtime_shadow` (8), `agent_orchestration` (5),
`agent_orchestration_claude_adapter` (9), `agent_orchestration_codex_adapter` (8), `agent_replay`
(5), `agent_replay_codex` (13) = 83 files across 12 dirs, plus `tests/regression` (1 file), plus 3
`tests/unit/` subdirs: `actions` (1), `ai` (4), `tools` (1) = 440 tests total.

All 16 directories trace to the same commit, `29d78798` ("Simulation quality #20", 2026-08-14),
confirmed via `git log --diff-filter=A` on 4 sampled directories, all returning the same commit —
the workflow file was simply never updated in that same PR to include the new directories.

Marker-filtered `--collect-only` confirmed only 1 of the 440 tests carries `@pytest.mark.slow`/
`@pytest.mark.extra_slow` (so would have incidentally run via the `slow` job's blanket `pytest
tests/` scan) — 439 of 440 had never executed in CI, ever, in any lane.

## Real failures found once run
A local full run of all 440 (before this session's other fixes) found 9 real failures, all root-
caused and fixed as their own separate tickets in this session's batch:
`TCK-20260817-HOTFIX-PHASE-TIER-MATRIX-WORKFLOW-VERSION-STALE`,
`TCK-20260817-HOTFIX-TERMINAL-STATUS-STALE-LINE-NUMBERS`,
`TCK-20260817-HOTFIX-SIMQ-AUDIT-GAPS-ISOLATED-ANCHOR-FALSE-POSITIVE`,
`TCK-20260817-STANDARD-CODEX-SHADOW-CONTRACT-VERSION-FIXTURE-CONFLATION` (3 of the 4
`agent_codex_runtime_shadow` failures), plus 2 more surfaced only when re-running against the real
CI "API / tools / logging" job scope: `TCK-20260817-HOTFIX-LEGACY-READER-IN-PROGRESS-MISCLASSIFICATION`
(the record flagged happened to be an `agent_codex_*`-adjacent run, but the bug was in
`tools/agent-monitoring/legacy_reader.py`, unrelated to the orphaned dirs themselves) — this is
disclosed for completeness; the point is every real failure found in these 440 tests was
independently investigated and fixed before this wiring ticket, not swept under the rug by adding
the directories to CI while still red.
