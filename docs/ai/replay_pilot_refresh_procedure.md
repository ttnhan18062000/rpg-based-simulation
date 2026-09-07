---
status: active
layer: ai
authority: P2
audience: agent
date: 2026-09-07
tags: [ai, agent-monitoring, testing]
---

# Filtered Replay Eval Pilot — Refresh Procedure

Documents how to add newer closed tickets to the eligible sampling pool later. Built by
`TCK-20260907-FILTERED-REPLAY-EVAL-PILOT` (Scope item 8) — this doc describes the procedure only.
**Actually re-running a refreshed pilot is explicitly out of this ticket's own scope**; do not
run these steps as part of closing that ticket.

## When to refresh

Per `agent_evaluation_foundation_experiment.md`'s Method step 5 ("periodically refresh the
eligible pool"). No fixed cadence is mandated — refresh when a materially larger `tickets/done/`
corpus has accumulated since the last sample, or when a new recurring defect class is added to
`guardrail_enforcement_epic.md` and needs its own detector.

## Steps

1. **Re-sample.** Run `tools/agent_replay/sampler.py::build_sample_manifest()` against the
   current `tickets/done/` and `agent-monitoring/` state:

   ```python
   from pathlib import Path
   from agent_replay.sampler import build_sample_manifest, write_manifest

   manifest = build_sample_manifest(Path("tickets/done"), Path("agent-monitoring"))
   write_manifest(manifest, Path("stored_artifacts/<new-ticket-id>/sample_manifest.yaml"))
   ```

   This re-derives the corpus size, tier breakdown, and stratification live — never reuse the
   prior pilot's own manifest numbers, which will be stale (see this pilot's own results.md,
   "Freshly-Measured Baseline" section, for how quickly these figures move).

2. **Re-convert.** Run `tools/agent_replay/fixture_converter.py::convert_sample()` against the new
   manifest's ticket IDs, writing fresh fixtures and a fresh `conversion_log.yaml` under the new
   ticket's own `stored_artifacts/` directory — never overwrite this pilot's own
   `stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/` outputs or
   `tests/fixtures/agent_replay/pilot/sample/`.

3. **Re-run the detectors.** Apply `tools/agent_replay/defect_detectors.py::detect_m2_doc_update_gap`
   to every newly-converted fixture (via `tools/agent_replay/run_pilot.py`'s own
   `_build_ticket_commit_index()`/`_docs_paths_for_commit()` helpers, which resolve a ticket's real
   per-ticket closing commit — remember: a real, significant fraction of this repo's history closes
   multiple tickets inside one squashed batch/epic-merge commit with no isolable per-ticket diff;
   those tickets correctly get no M2 evidence either way, not a fabricated verdict). M3 stays
   synthetic-only (`m3_synthetic_known_positive.yaml`) — do not attempt to derive a real per-ticket
   M3 fixture unless `subagent_stop_background_guard.py`'s `background_tasks` signal ever becomes
   persisted to a stored artifact (it is not today — see investigation.md Risks #1).

4. **Re-run isolated, twice.** Call `tools/agent_replay/pilot_isolation.py::run_pilot_isolated()`
   with the new fixture set, exactly as `run_pilot.py::execute_pilot()` does.

5. **Recompute metrics and write a fresh results report.** Call
   `tools/agent_replay/metrics.py::compute_metrics()` and write a new
   `stored_artifacts/<new-ticket-id>/results.md` — never overwrite this pilot's own results.md,
   which is this ticket's permanent evidence record. A refreshed pilot's own results should be
   appended to `agent_evaluation_foundation_experiment.md` as a dated addendum under `## Results`,
   not by replacing this pilot's original entry.

6. **File a new ticket for the refresh.** Per this project's Workflow Rule, a refresh run is new
   work with its own ticket, its own `staging_artifacts/`, and its own Definition-of-Done — it is
   not a silent edit to this pilot's own closed artifacts.

## What must not change between refreshes

- The sample size bound (20-40 tickets) — a refresh is not license to widen the sample; that
  remains gated on this pilot's own Exit Criteria being met and a separate decision to grow scope
  (see `bucket_c_future_options.md` item 20).
- The M2/M3 detector logic itself (`tools/agent_replay/defect_detectors.py`) — a refresh applies
  the same detectors to a newer sample; it does not redesign them. If a third recurring defect
  class is later added to `guardrail_enforcement_epic.md`, that is new detector-build work
  (its own ticket), not part of a routine refresh.
