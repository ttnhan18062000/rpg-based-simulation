---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC
phase: done
date: 2026-08-10
tags: [ai, agent-monitoring, process-improvement, observability]
---

# TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC

## Title
Agent tooling integrity hardening epic — context-search, parity-ledger, skill-usage, and
ticket-status checkers that exist but aren't reliably enforced

## Status
DONE

## Tier
epic

## Type
chore

## Priority
P1

## Request Summary
A 2026-08-10 deep-dive audit (real `agent-monitoring/tools.jsonl`/`events.jsonl` data, last 14
days, 258 runs) of search-before-grep compliance and parity-ledger update quality found two real,
currently-unaddressed gaps, plus a tracking gap the user asked to close:

1. **Search-before-grep still fails outside the `investigator` subagent path.**
   `TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP` fixed `.claude/agents/investigator.md`
   (commit `9d9ed87`, 2026-08-08 12:55 UTC) and it worked — zero `investigator`-agent violations
   in the 14-day window after that commit. But 3 post-fix violations remain, **all attributed to
   `agent=claude`** (hand-orchestrated/hotfix-tier Investigate work that never spawns the
   `investigator` subagent at all): `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD::2`,
   `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION::2`,
   `TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE::2`. Same root cause the epic-gap
   ticket already proved once: an instruction living only in global `CLAUDE.md` context, with no
   explicit callout at the actual entry point doing the work, gets skipped under task pressure —
   just recurring in a second, unpatched place.
2. **`docs/parity_ledger/*.yaml` has no write-time safety net.** `docs/parity_ledger/schema.json`
   exists but nothing enforces it when `parity-updater` or a hand-orchestrated session edits a
   ledger shard via raw `Read`/`Edit`. Measured: **0 of N** parity-ledger YAML writes in the last
   14 days co-occurred with a `tools/parity_index.py build` call in the same run — the derived
   SQLite index (`entry`/`impact`/`health`, reviewed and GO-verdicted in
   `docs/ai/parity_readpath_gate_a_decision.md`) goes stale on every real edit with nothing
   surfacing that staleness at write time.
3. **No recurring visibility into whether context-search tooling actually helps.**
   `TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC` already built a real, non-fabricated
   `raw_investigation_count`/`read_to_search_ratio` metric in
   `tools/agent-monitoring/retrieval_baseline_metrics.py`, but explicitly scoped out wiring it
   into the recurring weekly retro (`generate_retro.py`) — it only exists as a manual one-off run
   today, and there is no metric at all correlating search-before-grep *compliance* against actual
   raw-investigation effort, nor any tracking for `parity_index.py`'s `entry`/`impact`/`health`
   read path (which nothing calls yet).
4. **The same "real metric, no recurring cadence" gap exists for skill adoption.** A follow-up
   2026-08-10 audit of `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`'s own work found
   `tools/agent-monitoring/skill_usage_metric.py` (built DONE, tested, honest) is deliberately a
   standalone one-off script, never wired into the recurring retro. Live run found that epic's own
   6 new bespoke domain skills (`observability`, `simq-dev`, `systems-economy`, `combat-mechanics`,
   `cognition-strategy`, `progression-entities`, authored 2026-08-05) show **zero invocations** in
   the corpus so far — too early to call a failure, but nothing currently re-checks this on a
   schedule.
5. **A real, tested `## Status` drift checker ships unwired, and is catching real current drift
   right now.** A 2026-08-10 audit of ticket process/frontmatter/tag health found
   `tools/gate_checks/status_drift_check.py`'s own docstring discloses it "ships unwired — no
   `Makefile` target, no `.claude/workflows/*.js` invocation... a future ticket decides
   where/whether to call it" — unlike `## Tier`/`## Priority`, which `tools/ticket_field_values.py`
   *does* hard-block on in `done_checker_static.py::run_static_precheck`. Run live: **3 real,
   current** (not legacy) drift cases — `TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER.md`,
   `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE.md`, and
   `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC.md` (closed 4 days ago) all sit in
   `tickets/done/` with `## Status` still reading `OPEN`. The checker's own docstring documents the
   real consequence: this exact drift class previously caused the dashboard's
   `GanttBar.tsx::classifyFinalStatus()` to render genuinely-successful runs in the wrong (gray,
   not green) bucket. Separately (frontmatter schema and tag vocabulary), live validation confirmed
   **no live gap**: `validate_frontmatter.py` shows zero violations on any ticket dated
   2026-07-04 or later (187 flagged violations are 100% pre-enforcement-cutoff legacy, exactly
   matching `docs/guidelines/tag_taxonomy.md`'s documented forward-only-enforcement design), and
   `tag_report.py` shows a healthy, fully-categorized 56-tag vocabulary across 372 in-scope
   tickets — those two are not in scope for this epic.

This is a **scope-only epic**: it tracks the five child tickets below and does not implement any of
them directly.

## Scope
- Track and sequence the 5 child tickets in this folder.
- Require each child to cite real `agent-monitoring/*.jsonl` (or, for child #5, real
  `tickets/done/` corpus) evidence for its fix, not assumption.
- Require the tracking children (#3, #4) to make the *effect* of children #1 and #2 measurable
  going forward — the epic is not done just because #1 and #2 land; the improvement has to be
  visible in real retro data.
- Require child #5 to both wire the checker in going forward AND resolve the 3 real current drift
  instances it already found — wiring alone without fixing the 3 known-bad records would leave the
  gate passing on a corpus that's already dirty.

## Out of Scope
- Any change to `done-checker`'s DoD conditions themselves.
- Broadly wiring `tools/parity_index.py`'s `entry`/`impact`/`health` read path into a live
  workflow gate — `docs/ai/parity_readpath_gate_a_decision.md`'s own GO verdict is explicitly
  scoped narrowly (read-path review only) and requires a **separate** Phase-3 scoping decision
  before any workflow call site is added. This epic's child #2 covers write-safety only.
- Re-litigating already-closed tickets (`TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP`,
  `TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC`, `TCK-20260731-PARITY-READPATH-GATE`) — this
  epic extends their findings, it does not redo them.

## Acceptance Criteria
- [x] All 5 child tickets are reviewed, dependency-ordered (see `SEQUENCE.md`), and linked below.
- [x] Child #1 closes the hotfix/hand-orchestrated search-before-grep gap with an explicit
      callout at the actual entry point doing that work (found via its own Investigate phase —
      confirmed the real dispatch mechanism is `.claude/skills/implement-ticket/SKILL.md`'s
      Investigate step, not hotfix-tier routing as originally hypothesized).
- [x] Child #2 adds a schema-validating write path for `docs/parity_ledger/*.yaml` and resolves or
      explicitly defers-with-rationale the index-freshness gap (in-process rebuild on every
      validated write, plus a required separate visible `parity_index.py build` call).
- [x] Child #3 makes both the read/search effectiveness ratio and (once any workflow calls it) the
      parity sqlite read-path usage visible in the recurring `generate_retro.py` report, with a
      real correlation between search-before-grep compliance and raw-investigation effort computed
      from real data.
- [x] Child #4 makes skill-usage counts visible in the recurring `generate_retro.py` report, with a
      grace-period-aware zero-invocation flag validated against a real historical case
      (`backend-testing`).
- [x] Child #5 wires `status_drift_check.py` into a real enforcement or reporting path (a report-only
      `status-drift-check` Makefile target, chosen over a blocking gate with cited evidence — a
      per-ticket gate would have caught none of the real drift found) and fixes the real current
      `## Status` drift instances found live (7 confirmed real, not the 3 originally cited — the
      corpus had moved since this epic was authored; fixing only 3 while 4 more known-real
      instances sat unfixed would have misrepresented the corpus state).
- [x] The epic is not closed merely because code exists for #1/#2/#5 — see the
      `2026-08-14 Retro Verification` note below for the real follow-up evidence checked before
      closing (3 of 4 signals confirmed with real data; the 4th — search-before-grep compliance for
      child #1's specific fix — is explicitly flagged as pending natural recurrence, not silently
      claimed as proven).

## Related Tickets
- TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP (child)
- TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL (child)
- TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING (child)
- TCK-20260810-SKILL-USAGE-RETRO-TRACKING (child)
- TCK-20260810-STATUS-DRIFT-CHECK-WIRING (child)
- TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP (DONE; predecessor, same root-cause class)
- TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP (DONE; same shape — hand-orchestration
  bypassing an agent-specific instruction)
- TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC (DONE; predecessor metric, one-off today)
- TCK-20260731-PARITY-READPATH-GATE (DONE; sqlite read-path Gate A review, GO verdict)
- TCK-20260807-DOC-UPDATER-FIRST-ATTEMPT-BLOCKED-RATE (DONE; confirms doc-updater itself is clean
  — not in scope for this epic)
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (DONE; authored the 6 domain skills child #4 will
  track adoption for)
- TCK-20260805-SKILL-USAGE-METRIC (DONE; built the metric child #4 wires into the recurring retro)
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC (backlog; broader retrieval epic this work
  supports evaluating, not a duplicate of it)
- TCK-20260718-STATUS-DRIFT-REPAIR, TCK-20260718-STATUS-MULTILINE-FIX (DONE; built
  `status_drift_check.py` and its `parse_body_section`-based extraction fix — child #5 wires it in,
  does not rebuild it)
- TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM (DONE; built `ticket_field_values.py` and the
  hard-blocking precedent for `## Tier`/`## Priority` that child #5 extends to `## Status`)

## Related Docs
- `docs/ai/parity_readpath_gate_a_decision.md`
- `docs/agent-monitoring/README.md`
- `docs/agent-monitoring/schema.md`
- `docs/architecture/doc_updater_agent.md` (comparison precedent — `doc-updater` already has a
  clean bill of health; this epic does not touch it)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP/`
- `stored_artifacts/TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL/`
- `stored_artifacts/TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING/`
- `stored_artifacts/TCK-20260810-SKILL-USAGE-RETRO-TRACKING/`
- `stored_artifacts/TCK-20260810-STATUS-DRIFT-CHECK-WIRING/`
- `agent-monitoring/retro/RETRO-LAST14D.md` (2026-08-14 closing-verification retro run — see
  `## Notes` section's "Epic verification check" for the per-signal evidence)

## Related Code Areas
- `.claude/agents/investigator.md`
- `.claude/agents/parity-updater.md`
- `tools/parity_index.py`
- `docs/parity_ledger/schema.json`
- `tools/agent-monitoring/generate_retro.py`
- `tools/agent-monitoring/retrieval_baseline_metrics.py`
- `tools/agent-monitoring/skill_usage_metric.py`
- `.claude/skills/*/SKILL.md`
- `agent-monitoring/tools.jsonl`, `agent-monitoring/events.jsonl`
- `tools/gate_checks/status_drift_check.py`
- `tools/ticket_field_values.py`
- `tools/gate_checks/done_checker_static.py`
- `dashboard-frontend/src/components/GanttBar.tsx` (reference only — the real downstream consumer
  of `## Status` drift's consequence, per `status_drift_check.py`'s own docstring)

## Assumptions / Open Questions
- Which real entry point drives hotfix/hand-orchestrated Investigate work (child #1's own
  Investigate phase must confirm this — not assumed here).
- Whether child #2's write-through tool should live in `tools/parity_index.py` itself or a
  sibling module — deferred to child #2's own Investigate/Plan.

## Implementation Notes
Scope-only epic; no direct implementation — all work happened in the 5 child tickets. This
ticket's own edits (2026-08-14) are limited to marking the tracked scope complete and recording
the closing verification evidence, per its own Acceptance Criteria requirement not to close on
code-exists alone.

## Test Summary
Not applicable directly — each child ticket ran and independently verified its own scoped test
suite (see each child's `## Test Summary`). No epic-level test suite exists; verification for
epic closure was the 2026-08-14 retro run (`agent-monitoring/retro/RETRO-LAST14D.md`) plus a
live `status_drift_check.py` re-run, both described in `## Notes`.

## Files Changed
None directly by this epic ticket besides its own body/frontmatter. All 5 child tickets'
`## Files Changed` sections list the real implementation diffs.

## Completion Summary
All 5 child tickets closed 2026-08-14. Per this epic's own Acceptance Criteria — "not closed
merely because code exists" — a follow-up `agent-monitoring-retro --days 14` run was generated
the same day specifically to check real post-close evidence (see `## Notes`'s "Epic verification
check" for full detail). Result: 3 of 4 verification signals confirmed with real, non-fabricated
data —

- Parity ledger write-safety co-occurrence moved from the epic's original 0/N baseline to 15
  real co-occurrences this window (child #2's schema-validating writer).
- Skill-adoption visibility mechanism is live and correctly excludes all 6 domain skills (still
  in grace period); `cognition-strategy` already shows real movement (0 -> 1 invocation) (child #4).
- `status_drift_check.py` re-run live shows exactly 2 FAIL, both the documented known false
  positives — zero real drift remains (child #5).

The 4th signal — search-before-grep compliance for child #1's specific fix (hand-orchestrated
`agent=claude` Investigate-phase work) — could not yet be confirmed or denied: no hand-orchestrated
Investigate-phase run has occurred anywhere in the corpus since the fix shipped
(2026-08-14T18:47Z), so its target failure mode has not recurred to test against. The fix itself
is verified real and reachable (confirmed structurally during child #1's own Architecture-Verify
pass), but actual compliance evidence requires a future retro once such a run occurs naturally.
This is recorded honestly as pending, not silently claimed as proven — closing the epic now
reflects that 3 of 4 signals are positively confirmed and the 4th is a structural
can't-measure-yet gap, not a failure.
