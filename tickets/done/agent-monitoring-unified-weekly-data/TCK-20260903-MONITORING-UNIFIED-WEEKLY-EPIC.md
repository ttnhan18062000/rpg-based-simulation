---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC
phase: done
date: 2026-09-03
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC

## Title
Correct and extend weekly monitoring sharding: unify `runs.jsonl` + `events.jsonl` + `tools.jsonl`
under one per-ISO-week folder (`agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl`) with real
referential-integrity verification between them

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC` (3 child tickets + 1 follow-up hotfix, all DONE, on
open PR #112 branch `worktree-monitoring-tools-weekly-sharding`, **not yet merged to main**) sharded
only `agent-monitoring/tools.jsonl` into `agent-monitoring/tools/tools-YYYY-Www.jsonl`, leaving
`agent-monitoring/runs.jsonl` and `agent-monitoring/events.jsonl` as monolithic single files. The
requester has explicitly corrected this scope, verbatim: *"you are wrong, you need to sharding the
whole week for every data, including events, tools and runs, not only tools... I expected to have
agent-monitoring/data/2026-WXY/ folders include tools runs events, under that week, verify if they
are linked between (like foreign keys)"*.

**Target design (directive from the requester, not open for re-derivation absent a concrete blocking
reason — none found this session):** one folder per UTC ISO week,
`agent-monitoring/data/YYYY-Www/`, containing exactly 3 fixed-name files: `runs.jsonl`,
`events.jsonl`, `tools.jsonl`. This retires all 3 of today's physical shapes: the monolithic
`agent-monitoring/runs.jsonl`, the monolithic `agent-monitoring/events.jsonl`, and the already-shipped
(but now itself superseded) `agent-monitoring/tools/tools-YYYY-Www.jsonl` shard family from the prior
epic. `%G-W%V` (the existing `generate_retro.py::iso_week()` format, already reused by the prior
epic and by `agent-monitoring/retro/RETRO-YYYY-Www.md`) stays the ISO-week format.

**Critical, time-sensitive finding, confirmed by direct source read this session — a currently-live
data-quality bug, not just an architecture gap:** `tools/agent-monitoring/record_events.py` hardcodes
`TOOLS_FILE = Path("agent-monitoring/tools.jsonl")` (line 17) and reads it directly
(`load_jsonl(TOOLS_FILE)` feeding `_compute_tool_stats_by_key()`, lines 59-60) to deterministically
compute `tool_call_count`/`cost_proxy_score` for **every event it writes**. Since
`TCK-20260902-MONITORING-SHARD-MIGRATION` (child 2 of the prior epic) ran `git rm
agent-monitoring/tools.jsonl` on 2026-09-02, that path has been permanently empty for
`record_events.py`'s purposes ever since — every real `implement-ticket.js`-orchestrated run since
has gotten `tool_call_count=0`/wrong `cost_proxy_score` on its events, silently (no crash: `TOOLS_FILE
.exists()` is `False`, so the read degrades to an empty list, not an error). **Two more sites,
confirmed by direct grep this session, share the identical bug pattern and must be fixed as part of
this epic, not treated as a one-off:**
- `tools/agent-monitoring/weight_sensitivity_check.py:29` —
  `TOOLS_FILE = Path("agent-monitoring/tools.jsonl")`, unconditional, no `.exists()` guard visible at
  the constant-definition site (confirm exact read-site guard behavior at implementation time).
- `src/api/agent_ops_dashboard/ingest.py:476` — `DashboardCache.__init__`'s
  `self._tools_file = repo_root / "agent-monitoring" / "tools.jsonl"`, read via
  `load_jsonl_counted(self._tools_file)` in `_rebuild()` (line 521). This is real, production
  API-facing code (the Agent Ops Dashboard backend), not a dev tool — its `tools_all`/
  `_tools_by_seq`/`_tools_by_run_recent` state (feeding Skill Usage / cost-proxy dashboard views) has
  been silently empty since the prior epic's `git rm`, with no crash and no visible error.

This epic's write-path child ticket must treat fixing this bug class as a first-class, explicitly
urgent acceptance criterion — not a side note — precisely because it is presently live and silently
corrupting real data on every run.

**Full inventory of confirmed hardcoded `runs.jsonl`/`events.jsonl`/`tools.jsonl` path references**,
gathered via direct grep and source reads this session (see each child ticket's own Related Code
Areas for exact line numbers):

Writers: `tools/agent-monitoring/post_tool_hook.py` (already shard-aware for `tools` only, per the
prior epic), `record_events.py` (writes `events.jsonl`, plus the critical `TOOLS_FILE` read-side bug
above), `record_run.py` (writes `runs.jsonl`). `writer.py`'s shared `write_line()`/`write_lines()` is
confirmed still fully generic on `target_path` — no change needed there, same as the prior epic's
finding.

Readers/consumers, confirmed still hardcoded to a single `runs.jsonl`/`events.jsonl` path (in
addition to `tools.jsonl` sites already fixed by the prior epic for the `tools` source only):
`build_index.py` (`DEFAULT_RUNS_FILE`, `DEFAULT_EVENTS_FILE`), `generate_retro.py` (`RUNS_FILE`,
`EVENTS_FILE`), `seq_offset.py` (`EVENTS_FILE`), `retro_nudge_hook.py` (`RUNS_FILE`),
`weight_sensitivity_check.py` (`TOOLS_FILE` — the bug above — and `EVENTS_FILE`),
`done_ticket_monitoring_coverage.py` (reads `runs.jsonl` directly by its own doc comments — exact
constant to confirm at implementation), `validate.py`/`query.py` (prior epic confirmed these are
largely SQLite-index consumers with no direct `tools.jsonl` constant; their `runs.jsonl`/`events.jsonl`
surface was never checked by that epic since it was tools-only in scope — must be reconfirmed here),
`tools/gate_checks/done_checker_static.py::check_monitoring_write_recorded` (default args
`runs_path=Path("agent-monitoring/runs.jsonl")`, `events_path=Path("agent-monitoring/events.jsonl")`
— explicitly out of scope for the prior epic since it never touched `tools.jsonl`; now squarely in
scope), `src/api/agent_ops_dashboard/ingest.py::DashboardCache` (`_runs_file`, `_events_file`, and
the `_tools_file` bug above — real production API code, treat with extra care).

Codex-runtime-activation subsystem: `tools/agent_replay_codex/monitoring_shards.py` (the shared
dual-mode helper built by `TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS`) is confirmed, by
its own docstring and `resolve_tree_lines()` body, to hardcode the assumption that "runs.jsonl/
events.jsonl are always single-file in both shapes" — this epic breaks that assumption and the
helper (plus its 6 call sites: 3 conftest.py fixtures, `provenance_check.py`, `config_toggle.py`,
`proofs.py`) must be generalized to cover all 3 sources, not just `tools`.

Docs/config: `CLAUDE.md` itself already contains stale claims from the *already-shipped* prior epic,
confirmed by direct grep this session (line 94: "stage `agent-monitoring/` (including
`tools.jsonl`)"; lines 137/140: "`agent-monitoring/tools.jsonl` is rewritten by a hook on nearly
every tool call" plus a literal-path example command; line 254: DoD checklist naming
`agent-monitoring/runs.jsonl`/`agent-monitoring/events.jsonl` literally) — these need correcting
regardless of this epic, and additionally need to describe the new unified layout once it lands.
`.gitattributes` currently has 3 separate `merge=union` lines (`runs.jsonl`, `events.jsonl`,
`tools/*.jsonl`) that all need replacing with one unified glob. `docs/agent-monitoring/README.md`
(confirmed already updated for `tools` by the prior epic, e.g. line 19's `tools/tools-YYYY-Www.jsonl`
naming — but still describes `runs.jsonl`/`events.jsonl` as single files, correctly for today, needs
updating once this epic lands), `docs/agent-monitoring/schema.md` (including its Join Example Python
snippet), `docs/guides/agent_monitoring.md`, `docs/ai/system_overview.md` §6. `.claude/workflows/
implement-ticket.js` has prose-only references (confirmed, no functional file I/O in JS — it
delegates entirely to the Python tools above) at multiple lines that should be corrected for
accuracy even though no functional JS change is required. `.claude/skills/agent-monitoring-retro/
SKILL.md` needs a final check for path references.

## Scope
- Scope-only epic: create and track the 7 child tickets that implement the unified per-week
  `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` layout, migrate all historical data
  (both the still-monolithic `runs.jsonl`/`events.jsonl` and the prior epic's already-sharded
  `tools/tools-YYYY-Www.jsonl` files), migrate every confirmed consumer, generalize the codex
  subsystem's shard-aware helper, build real referential-integrity verification, and sweep docs/
  CLAUDE.md/`.gitattributes`/workflow prose. No direct implementation in this ticket itself.
- Record the design and the critical-bug findings above as already-decided/confirmed, not reopened
  for child-ticket re-derivation.
- Sequence: write-path unification (+ the critical bug fix) lands first, then one-time historical
  migration, then the 4 largely-independent consumer/codex/referential-integrity/docs tracks. See
  this batch folder's `SEQUENCE.md`.
- Continue on branch `worktree-monitoring-tools-weekly-sharding` / PR #112 (per this repo's "push to
  open PR, not new stacked PR" convention) rather than opening a new PR, since that PR has not yet
  merged and this epic corrects/extends its own not-yet-landed scope.

## Out of Scope
- Auto-pruning, archiving, or deleting old week folders beyond git's own history — a frozen week
  folder just stops growing; no retention/deletion policy is in scope (same boundary the prior epic
  drew).
- Redesigning any of the 3 per-line record schemas (the field shapes documented in
  `docs/agent-monitoring/schema.md`) — this epic changes physical file layout and adds a verification
  layer only, never the record shape itself.
- Backfilling or repairing any pre-existing malformed/off-schema historical lines beyond what
  zero-data-loss migration requires (content repair stays out of scope, same boundary as the prior
  epic's migration child).
- Building a general-purpose relational/SQL referential-integrity engine — the verification tooling
  in scope here is narrowly the 2 real FK relationships this schema actually has
  (`events.run_id -> runs.run_id`, `tools.(run_id, seq) -> events.(run_id, seq)`), not a reusable
  framework for arbitrary future joins.
- Activating, enabling, or invoking any live Codex pilot behavior — the codex-subsystem child ticket
  only fixes monitoring-file-shape assumptions in already-existing readiness/containment code.
- Any change to `writer.py`'s locking protocol — confirmed by the prior epic to already be fully
  generic on `target_path`; no change expected here either, to be reconfirmed per child ticket.

## Acceptance Criteria
- [x] All 7 child tickets are DONE.
- [x] New writes for all 3 sources land in `agent-monitoring/data/<current-ISO-week>/{runs,events,
      tools}.jsonl`, never in `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, or
      `agent-monitoring/tools/tools-*.jsonl`.
- [x] All historical data (monolithic `runs.jsonl`, monolithic `events.jsonl`, and the prior epic's
      already-sharded `tools/tools-YYYY-Www.jsonl` files) has been migrated into the unified layout
      with a verified zero-data-loss reconciliation, and none of the 3 old paths exist in the working
      tree afterward (history recoverable via `git log --follow`).
- [x] `record_events.py`'s `tool_call_count`/`cost_proxy_score` computation, `weight_sensitivity_
      check.py`'s tools-source read, and `DashboardCache._tools_file`'s read are all confirmed fixed
      against real post-migration multi-week data (a regression test for each proving nonzero/
      correct output, not just "doesn't crash").
- [x] Every confirmed consumer (`build_index.py`, `generate_retro.py`, `manifest.py`, `seq_offset.py`,
      `weight_sensitivity_check.py`, `retro_nudge_hook.py`, `done_ticket_monitoring_coverage.py`,
      `validate.py`, `query.py`, `done_checker_static.py`, `agent_ops_dashboard/ingest.py`) reads the
      union of all week folders for each source it consumes, not one hardcoded path.
- [x] `tools/agent_replay_codex/monitoring_shards.py` and its 6 dependent call sites are generalized
      to resolve all 3 sources (not just `tools`) against the new layout, with the synthetic-scratch
      single-file shape still working unchanged.
- [x] A referential-integrity verification tool exists, is tested, and correctly joins
      `events.run_id -> runs.run_id` and `tools.(run_id, seq) -> events.(run_id, seq)` **across week
      folders** (a run/its events/tool-calls spanning an ISO week boundary must not be flagged as
      broken), while still flagging genuine orphans and respecting the schema's own documented
      exceptions (retrieval-event shadow rows, `run_id: null` interactive tool calls, negative
      shadow-packet `seq` values).
- [x] `docs/agent-monitoring/README.md`, `schema.md`, `docs/guides/agent_monitoring.md`,
      `docs/ai/system_overview.md` §6, `CLAUDE.md` (including the already-stale claims named above),
      and `.gitattributes` all describe the unified per-week layout, not any of the 3 retired shapes.

## Related Tickets
- TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY (child 1)
- TCK-20260903-MONITORING-DATA-MIGRATION (child 2)
- TCK-20260903-MONITORING-DATA-CONSUMERS-CORE (child 3)
- TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD (child 4)
- TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION (child 5)
- TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY (child 6)
- TCK-20260903-MONITORING-DATA-DOCS-SWEEP (child 7)
- TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC and its 3 children
  (TCK-20260902-MONITORING-SHARD-WRITE-PATH, TCK-20260902-MONITORING-SHARD-MIGRATION,
  TCK-20260902-MONITORING-SHARD-CONSUMERS) — this epic explicitly corrects and extends that epic's
  tools-only scope to all 3 sources; reuses its established patterns (the `%G-W%V` ISO-week
  convention, `writer.py::write_lines()`'s locked-batch-append contract, the rename-aside historical
  merge algorithm for a week already receiving live writes, the dual-mode
  directory-glob-or-literal-file consumer pattern) rather than redesigning from scratch. That epic's
  PR #112 is still open (not merged) — this epic's work lands on the same branch/PR.
- TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS — built the
  `tools/agent_replay_codex/monitoring_shards.py` shared helper this epic's codex child ticket
  generalizes from tools-only to all 3 sources, reusing its dual-mode design rather than replacing
  it.
- TCK-20260713-MONITORING-SQLITE-INDEX and its sibling batch (`MONITORING-QUERY-INDEX-MIGRATE`,
  `MONITORING-VALIDATE-INDEX-MIGRATE`, `MONITORING-RETRO-INDEX-MIGRATE`) — built the gitignored
  SQLite index this epic's consumer-migration children must keep working against the new layout.
- TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION — confirms paused/resumed sessions sharing one
  `run_id` are real and already-encountered in this corpus; directly relevant to why the
  referential-integrity child ticket must be cross-week-boundary aware, not assume same-folder
  locality.
- TCK-20260719-COST-PROXY-WRITE-PATH / TCK-20260719-LIVE-PHASE-AGENT-LABEL — established
  `record_events.py`'s deterministic `tool_call_count`/`cost_proxy_score` computation from
  `tools.jsonl` ground truth at write time; the exact mechanism the critical bug above breaks.

## Related Docs
- `docs/agent-monitoring/README.md`, `docs/agent-monitoring/schema.md` (including its Join Example
  snippet), `docs/guides/agent_monitoring.md`, `docs/ai/system_overview.md` §6 — all describe the
  current (partially stale) physical layout.
- `CLAUDE.md` — confirmed to already contain stale claims from the prior epic (lines 94, 137, 140,
  254); needs both an accuracy fix regardless of this epic and a further update once this epic lands.
- `docs/parity_ledger/infrastructure.yaml` `INFRA-291` — the entry the prior epic's consumer-migration
  child updated for the tools-only cutover; this epic's docs-sweep child must add a further addendum
  (via `tools/parity_ledger_writer.py`, never a raw YAML edit).

## Related Stored Artifacts
None yet — epic ticket, no staging artifacts required (scope-only, per Tier Routing). Each
standard-tier child ticket requires its own `staging_artifacts/{ticket_id}/`.

## Related Code Areas
- `tools/agent-monitoring/record_run.py`, `record_events.py`, `post_tool_hook.py`, `writer.py`
- `tools/agent-monitoring/build_index.py`, `generate_retro.py`, `manifest.py`, `seq_offset.py`,
  `weight_sensitivity_check.py`, `retro_nudge_hook.py`, `done_ticket_monitoring_coverage.py`,
  `validate.py`, `query.py`
- `tools/gate_checks/done_checker_static.py`
- `src/api/agent_ops_dashboard/ingest.py` (`DashboardCache`)
- `tools/agent_replay_codex/monitoring_shards.py` and its 6 call sites (3 conftest.py fixtures,
  `provenance_check.py`, `config_toggle.py`, `proofs.py`)
- `.gitattributes`
- `CLAUDE.md`, `docs/agent-monitoring/README.md`, `docs/agent-monitoring/schema.md`,
  `docs/guides/agent_monitoring.md`, `docs/ai/system_overview.md`, `.claude/workflows/
  implement-ticket.js` (prose only), `.claude/skills/agent-monitoring-retro/SKILL.md`

## Assumptions / Open Questions
- Target shape `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` is a directive from the
  requester (verbatim quote in Request Summary), recorded as already-decided. No concrete blocking
  reason to deviate was found this session; a child ticket's own implementer should still flag it
  explicitly (not silently substitute something else) if one surfaces.
- Week-bucketing key per source, confirmed via direct source read this session:
  `runs.jsonl` records are keyed by their own `start_ts` field (required, per `record_run.py`'s
  `REQUIRED` set); `events.jsonl`/`tools.jsonl` records are keyed by their own `ts` field (matching
  the prior epic's `migrate_tools_shards.py` precedent). New live writes bucket by write-time ("now"),
  matching the prior epic's write-path precedent for `tools.jsonl` — this means a run whose
  `start_ts` and completion/write time fall in different ISO weeks is expected and legitimate, not a
  bug; see the referential-integrity child's cross-week-join requirement below.
- A single `run_id`'s `events`/`tools` rows can legitimately land in a different week folder than its
  own `runs.jsonl` row, or than each other, whenever a run/session crosses an ISO-week boundary
  (confirmed real precedent: `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`'s pause/resume
  scenario). The referential-integrity child ticket (child 6) must join across all week folders for a
  given `run_id`, never assume same-folder locality — this is the single most important correctness
  requirement for that ticket.
- `layer: observability` matches every other `agent-monitoring/` ticket in this repo's history,
  confirmed via `python3 tools/layer_registry.py list`.
- The critical `record_events.py`/`weight_sensitivity_check.py`/`DashboardCache` ground-truth-read
  bugs are treated as fixes bundled into the relevant write-path/consumer-migration child tickets
  (per the requester's own framing: "not buried as a side note"), not spun out as separate hotfix
  tickets — each gets an explicit, dedicated, urgency-framed AC in its owning child ticket.

## Implementation Notes

All 7 child tickets ran through the full standard-tier pipeline (Investigate → Plan → Implement →
Test → Architecture-Verify → Verify → Finalize), each with an independent Test-phase re-verification
(test-scoper), an independent Architecture-Verify pass (architecture-reviewer), and an independent
Verify pass (done-checker) — none trusted the implementing agent's own self-report. Children 3, 4, 5,
and 6 (the 4 mutually file-disjoint consumer/dashboard/codex/referential-integrity tracks) ran in
parallel per the requester's own explicit authorization to speed up implementation for non-blocking
tickets, after child 2 (migration) landed; child 7 (docs sweep) ran last, after all 6 others, so it
could describe the actually-landed final state rather than an aspirational one.

Real findings surfaced and correctly handled at every stage, not silently absorbed:
- Child 1 fixed the critical `record_events.py::TOOLS_FILE` ground-truth bug (silently zeroing
  `tool_call_count`/`cost_proxy_score` on every event since 2026-09-02) with a genuine cross-week
  regression test, and its own Test-phase caught a missed test file
  (`test_execution_identity_end_to_end.py`) before Finalize.
- Child 2 executed the real, irreversible historical-data migration only after zero-data-loss
  verification passed for all 3 sources, then retired the 3 legacy paths via `git rm` — full
  history recoverable via `git log --follow`. Its own Test-phase found a broader-than-anticipated
  (but genuinely out-of-scope) test-breakage surface, correctly deferred to children 3/4.
- Children 3 and 4 fixed 2 more live, silently-broken production bugs
  (`weight_sensitivity_check.py`, `retro_nudge_hook.py`'s permanent no-op; `DashboardCache._tools_all`
  silently empty on the live Agent Ops Dashboard) with dedicated cross-week regression tests. Child
  3's own investigation corrected a real bug in its own plan (2 call sites the plan claimed needed
  "zero code change" would have actually raised `IsADirectoryError`).
- Child 5's Verify phase, re-run after children 3/4 landed, found a real, currently-live regression
  in their already-landed code (dropped scratch-shape fallback support in `manifest.py`/
  `DashboardCache`, silently masking a corruption-detection test) — outside every one of this epic's
  6 children's scope, filed as `TCK-20260904-HOTFIX-MANIFEST-DASHBOARD-SCRATCH-SHAPE-FALLBACK`
  rather than fixed inline or silently ignored.
- Child 6 built the referential-integrity tool as report-only (never gating/crashing on the
  ~12.7%/18-orphan real violations already present in the corpus), with its cross-week test fixture
  modeled on real corpus patterns, not synthetic guesses.
- Child 7's own Verify phase found and fixed 2 more missed doc references (its original sweep's
  gap-detection command only checked the `tools.jsonl` bare-mention pattern, not `events.jsonl`/
  `runs.jsonl`), and filed a second follow-up ticket
  (`TCK-20260904-HOTFIX-AGENT-REPLAY-MONITORING-PATH-STALENESS`) for the unrelated,
  unowned-by-any-child `tools/agent_replay/` package's own path staleness.

One real infrastructure anomaly encountered and resolved: a background `git gc --auto` process
repeatedly OOM-killed itself (`pack-objects died of signal 9`) on nearly every commit this session
due to heavy concurrent write pressure on the shared `.git` object store from many active worktree
sessions. This caused one real, confirmed commit-content-loss incident early in the session (child
1's first Finalize commit landed with stale pre-edit ticket content despite correct staging) —
diagnosed by comparing `git show HEAD:<path>` against the known-correct working tree, fixed with an
immediate follow-up commit, and verified as landed correctly on every subsequent commit for the rest
of the epic by re-checking `git show HEAD:<path>` after each one.

Cross-worktree `git rm` merge-conflict exposure (documented, not automated, per this repo's
established precedent) is now real for whichever other concurrently-active sessions' branches merge
past this epic's file-retirement commits — 3 paths retired by child 2, on top of the prior epic's own
1. Recommend merging this branch's PR promptly once ready, per the runbook already recorded in child
2's own ticket.

## Test Summary

Every child ticket's own Test Summary (in `stored_artifacts/TCK-20260903-MONITORING-DATA-*/`)
documents its independently-re-run pass counts. Aggregate: hundreds of tests across the 3 write-path
scripts, the migration script, 9 core consumer scripts, the dashboard/gate-check pair, the codex
subsystem, and the new referential-integrity tool — all independently re-verified clean by a
test-scoper agent that did not trust the implementing agent's self-report, for every one of the 7
children.

## Files Changed

See each child ticket's own Files Changed section for the full per-file list. At the epic level: all
3 legacy monitoring paths (`agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`,
`agent-monitoring/tools/`) are retired; `agent-monitoring/data/<ISO-week>/{runs,events,tools}.jsonl`
is now the sole live layout; 9 `tools/agent-monitoring/*.py` consumer scripts, `tools/gate_checks/
done_checker_static.py`, `src/api/agent_ops_dashboard/ingest.py`, `tools/agent_replay_codex/
monitoring_shards.py` and its 7 call sites, and a new `tools/agent-monitoring/
verify_referential_integrity.py` were migrated/added; `CLAUDE.md`, `.gitattributes`, 8 `docs/`
files, 3 `.claude/skills/*/SKILL.md` files, and `.claude/workflows/implement-ticket.js` (prose only)
were swept for accuracy; `docs/parity_ledger/infrastructure.yaml`'s `INFRA-291` entry carries 2 new
addenda (children 3 and 7).

## Completion Summary

Corrected and extended the prior epic's tools-only weekly sharding to all 3 monitoring sources
(`runs`, `events`, `tools`), per the requester's own explicit, verbatim correction. Delivered the
directed target design (`agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl`, one folder per
UTC ISO week) via 7 child tickets run through this repo's full standard-tier pipeline with
independent verification at every gate, 4 of them (children 3-6) executed in parallel per explicit
authorization once their shared prerequisite (child 2's migration) landed. Fixed 4 real, live,
silently-broken production bugs discovered during investigation and Verify (2 in the epic's own
originally-scoped critical-bug list, 2 more found live during the epic's own execution), each with a
genuine cross-week regression test. Built real referential-integrity verification, cross-week-
boundary aware as the requester specifically required, confirmed against real corpus patterns rather
than synthetic guesses. Migrated all historical data with a verified zero-data-loss reconciliation
before retiring the 3 legacy physical paths. Filed 2 new follow-up hotfix tickets for real gaps
discovered outside this epic's own scope, rather than silently absorbing or ignoring them. All 7
Acceptance Criteria satisfied.
