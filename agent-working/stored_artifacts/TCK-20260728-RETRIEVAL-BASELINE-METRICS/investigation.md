---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260728-RETRIEVAL-BASELINE-METRICS
artifact_type: investigation
tags: [agent-monitoring, observability]
---

# Investigation — TCK-20260728-RETRIEVAL-BASELINE-METRICS

## Current Behavior

### No existing tool computes any of the 5 metrics this ticket needs

None of `tools/agent-monitoring/generate_retro.py`, `validate.py`, `query.py`, `manifest.py`,
`cost_proxy.py` compute or report: context-token counts, a "follow-up search count," a
gap-aware/active-duration view, or a "review rework" signal. This is genuinely new reporting
logic, built on top of existing read-only precedent — not a modification of any of those files'
existing behavior.

### `generate_retro.py` — the closest existing precedent (`tools/agent-monitoring/generate_retro.py`)

- `_load_runs_and_events()` (lines 53-88): sources `runs`/`events` from the derived SQLite index
  (`agent-monitoring-index/monitoring.db`), building it on demand if missing, falling back to
  direct `load_jsonl(RUNS_FILE)/load_jsonl(EVENTS_FILE)` scan on any failure — "never a hard gating
  dependency," per its own docstring. Any new baseline-report tool built for this ticket should
  reuse this exact fallback pattern (or import `_load_runs_and_events` directly) rather than
  reimplementing index-vs-JSONL fallback logic a second time.
- `compute_retro_metrics(runs, events, tickets_root=None) -> dict` (lines 309-558): pure function,
  zero I/O beyond its parameters, returns a plain dict — the established shape for a "metrics"
  function this ticket's own report generator should mirror. It already computes, and this new
  ticket can reuse without reimplementing:
  - `_resolve_status(r)` (128-136) / `_is_gate_fail(r)` (147-152): `final_status`-or-`status`
    fallback and terminal-vs-non-terminal classification — directly reusable for AC4's
    "test/gate outcome ... derived only from existing fields."
  - `reason_code_breakdown` (line 347, from `reason_code` field): directly reusable for AC4's
    "review rework" signal insofar as `reason_code` disambiguates *why* a Review/Architecture-
    Verify gate failed within a single run, but see Risks below — it does NOT by itself indicate
    that a ticket was reworked and resubmitted.
  - `durations = [r["duration_s"] for r in runs if r.get("duration_s")]` (line 331) and the "Slow
    Runs"/"Duration outliers" sections (466-479, 491-505): both consume raw `duration_s` directly,
    with **no gap-awareness** — this is the exact contamination the sibling idea doc
    (`docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md`) documents (see
    Mechanics/Engine Constraints below).
  - `tool_call_count`/`cost_proxy_score` filtering pattern (`scored_events = [e for e in events if
    e.get("cost_proxy_score") is not None]`, line 436): the established "exclude null, never coerce
    to 0" convention this ticket's own tool_call_count-based metric must follow.
- `main()` (784-825) writes `agent-monitoring/retro/RETRO-*.md` files — this ticket's own report
  must **not** write into that directory (would conflate a one-off baseline snapshot with the
  recurring weekly retro cadence); see Anti-Drift Hazards.

### `manifest.py` / `legacy_reader.py` — the read-only-tool precedent this ticket must reuse, not reimplement

`tools/agent-monitoring/manifest.py` (TCK-20260721-BASELINE-MONITORING-MANIFEST, done) is the
direct architectural precedent for "a new, strictly read-only tool over `agent-monitoring/*.jsonl`":

- `_scan_file()`/`build_manifest()` (30-66): streams each file once, computing `line_count`,
  `byte_size`, `sha256`, `parser_result`, `legacy_warning_count` — never a full
  `read_text()`/`read()`/`readlines()`.
- `capture_lines()`/`assert_prefix_preserved()` (69-94): pre/post snapshot + prefix-preservation
  assertion — reused verbatim by `tools/agent_codex_pilot_guardrails/baseline_manifest_gate.py` via
  `importlib.util.spec_from_file_location`, confirming this module's functions are already treated
  as a stable, reusable read-only API elsewhere in the repo.
- `_assert_safe_output_path()` (97-104): refuses to write manifest output under
  `agent-monitoring/` itself — the pattern this ticket's own report tool must copy for whatever
  output path it picks (this ticket's own AC/Out of Scope explicitly requires zero mutation of
  `agent-monitoring/*.jsonl`, matching this precedent's own invariant).

`tools/agent-monitoring/legacy_reader.py`'s `classify_provenance(record, source)` (33-92) is the
ticket's named reuse target for "handle >=5-6 legacy schema generations via the existing
`LEGACY_COMPLETION_FIELDS` pattern, not reimplemented":

- `_classify_runs()` (46-75): checks, in order, the `shape6_type_checker_exception` (the one
  permanently-documented residual exception), `shape5_folder_epic_bare_status`,
  `shape1_started_finished_notes`, `shape2_final_status_no_end_ts`, `shape3_ts_start_ts_end_result`,
  `shape4_completed_at_status`, else `frozenset()` ("current").
- `_classify_tools()`/`_classify_events()` (78-92): `tools.jsonl`'s `interactive_null` vs.
  `tools_phase_agent_null_gap`, and `events.jsonl`'s `reason_code`/`tool_call_count`
  absence-flags — two independently-toggleable labels, not a single enum.
- Imports `LEGACY_COMPLETION_FIELDS`/`LEGACY_TERMINAL_STATUS_VALUES` read-only from `validate.py`
  (lines 16, 26-30) — this ticket's own baseline tool should import `classify_provenance` the same
  way (read-only), never duplicate the shape rules inline.

### `validate.py` (`tools/agent-monitoring/validate.py`)

- `LEGACY_COMPLETION_FIELDS = ("end_ts", "finished_at", "completed_at", "ts_end")` (line 58) and
  `LEGACY_TERMINAL_STATUS_VALUES` (64-68): the single source of truth for "this run reached a
  terminal state," already reused by `legacy_reader.py`.
- `_record_is_complete(rec)` (71-78): the completion predicate this ticket's derived
  test/gate-outcome metric should reuse (via import) rather than re-deriving completion logic a
  third time.
- `compute_drift_report()`/`compute_tool_count_drift_report()`/
  `compute_multi_invocation_collision_report()` (88-220): three precedents for "pure function,
  read-only over `runs`/`events`/`tools` lists, never gates anything, returns a formatted string" —
  the shape a new baseline-report function should follow.

### `vocabulary.py` (`tools/agent-monitoring/vocabulary.py`)

`WORKFLOW_PHASES`, `WORKFLOW_AGENTS`, `WORKFLOW_AGENT_PREFIXES`, `infer_workflow()`,
`is_known_agent()` (16-95): single source of truth for phase/agent/tier vocabulary, confirmed by
grepping each workflow's actual `phase(...)`/`pushEvent(...)` call sites, not schema.md's prose
(which was already found stale once). Any per-phase or per-workflow breakdown this ticket adds
must key off `infer_workflow(run_id)` the same way `generate_retro.py`'s `_normalize_phase`/
`_normalize_agent` (170-193) already do — do not hardcode a second phase/agent vocabulary.

### `cost_proxy.py` (`tools/agent-monitoring/cost_proxy.py`)

`compute_cost_proxy_score()` (35-47): `W_BASH * Σ(Bash duration_ms) + W_AGENT * count(Agent
spawns) + W_EDIT * count(Read/Edit/Write/MultiEdit)`. Confirms (module docstring, line 6): "Real
token/cost telemetry is platform-blocked" — directly supports AC1's "context-tokens... unavailable"
framing; this is not a documentation gap to fix, it is a confirmed platform limitation, restated
independently in `docs/agent-monitoring/README.md`'s "What It Does NOT Capture" section (line
24-26) and `docs/agent-monitoring/schema.md`'s "What is not recorded" section (lines 74-78).

### Real corpus data checked directly (not assumed)

- Current corpus sizes: `agent-monitoring/runs.jsonl` = 721 lines, `events.jsonl` = 3,831 lines,
  `tools.jsonl` = 68,538 lines (measured 2026-07-28; grown from the 702/3,642/65,023 the
  TCK-20260721-BASELINE-MONITORING-MANIFEST investigation measured a week earlier — expected, this
  is append-only live data, not a static fixture).
- `tools.jsonl`'s `tool` field distribution (full-corpus count, ~2M-line-bounded scan): `Bash`
  38,303, `Read` 15,473, `Edit` 7,035, `Write` 2,688, `Agent` 2,098,
  `mcp__knowledge-search__search_docs` 1,016, `ToolSearch` 649, `WebSearch` 13,
  `mcp__knowledge-search__search_health` 7. **`Grep` never appears as a distinct `tool` value** —
  raw grep-style searching happens through the generic `Bash` tool (confirmed: 88 `Bash` calls have
  an `input_summary` containing `search_mcp`/`knowledge_search`/`search_docs`, i.e. even
  search-flavored Bash calls are indistinguishable from any other Bash call by tool name alone).
  This means a *literal* per-tool-name "search count" (filtering `tool ==
  "mcp__knowledge-search__search_docs"` or `"ToolSearch"` or `"WebSearch"`) is a real, derivable
  signal already present in `tools.jsonl` — a materially different, more precise option than
  reusing the coarse `tool_call_count` aggregate the ticket's AC names literally. See Risks below —
  this is a Plan-phase interpretation decision, not resolved here.
- `duration_utils.py` (the module the sibling idea doc names as where gap-awareness should live)
  **does not exist** — confirmed via direct directory listing of `tools/agent-monitoring/`. The
  "gap-aware active-duration view" branch of AC3 is therefore not available; only the
  "visibly flag raw `duration_s` as pause-contaminated" branch can be satisfied today, exactly as
  the ticket's own Out of Scope anticipates ("this ticket proceeds with an explicit
  raw-duration-contamination caveat if that idea has not been picked up").
- Confirmed via `.claude/workflows/implement-ticket.js` (grepped, not assumed): a `NEEDS_CHANGES`/
  `BLOCKED` verdict at the `Review` phase (`phase('Review')`, line 550) or the post-Implement
  Architecture-Verify phase (line ~742) **terminates that run** (`pushEvent(..., 'failed', ...)`
  then the workflow exits with that `final_status`) — it does not loop back into a second Review
  cycle within the same run. There is no in-workflow "review round count." Any "review rework"
  signal can therefore only be a **cross-run** proxy: multiple `runs.jsonl` records sharing the
  same `run_id` (ticket ID) where an earlier record's `final_status` is `NEEDS_CHANGES`/`BLOCKED`
  and a later record for the same `run_id` reaches `DONE` — `validate.py`'s own
  `runs_grouped_by_id` (`main()`, lines 271-276) already anticipates multiple `runs.jsonl` records
  per `run_id` as a real, handled case, which supports this being a legitimate reuse of existing
  grouping logic rather than new speculative data modeling.

## Mechanics / Engine Constraints

N/A — this ticket touches agent-tooling observability infrastructure
(`tools/agent-monitoring/`, `agent-monitoring/*.jsonl`), not simulation mechanics. No chapter of
`docs/mechanics/` or contract in `docs/engine/` governs this area, consistent with the identical
finding in `stored_artifacts/TCK-20260721-BASELINE-MONITORING-MANIFEST/investigation.md`'s own
"Mechanics / Engine Constraints" section for the same code area.

The one constraining "engine contract" for this ticket is process-internal, not simulation-domain:
`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`'s
"Sequenced Future Epic" list, item 1 ("Baseline and evaluation fixtures — audit retrieval behavior,
repair stale expectations, define scenarios and outcome joins; **no workflow change**") and its
"Baseline" subsection under "Evaluation and Decision Follow-Up" ("Record only available, safe
metadata; unknown values must be explicitly marked rather than synthesized"). This ticket is the
direct operationalization of that paragraph. The doc's own maturity banner ("does not authorize a
new mandatory workflow gate, a production monitoring writer change, or a new external retrieval
service") is a hard constraint already reflected in this ticket's Out of Scope.

`docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md` (status: idea, not yet
implemented) is the second constraining doc: its "Confirmed on real data" table demonstrates that
`duration_s` for several historical runs is 71-99% session-pause gap, not real work — this is the
evidentiary basis for AC3's "never presented as clean" requirement.

## Parity Ledger Overlap

**None of `docs/parity_ledger/*.yaml`'s entries cover this ticket's scope.** Grepped all 8 files for
`monitoring|retro|manifest|legacy_reader|context.token|tool_call_count|duration` — every hit in
`infrastructure.yaml` is one of two unrelated categories:

1. Simulation-domain "monitoring"/"manifest" entries (`INFRA-038`, `INFRA-039`, `INFRA-042`,
   `INFRA-055`, `INFRA-067`, `INFRA-155`, `INFRA-156`, `INFRA-192`, `INFRA-218`, `INFRA-230`,
   `INFRA-256`) — these concern the simulation engine's own health-monitor/replay-manifest/
   campaign-manifest subsystems (`src/observability/`, `src/certification/`, `src/engine/`), not
   agent-tooling.
2. Prior agent-monitoring **tooling** tickets that *do* have entries (`INFRA-265`, `INFRA-274`
   through `INFRA-291`) — e.g. `INFRA-289`/`INFRA-290`/`INFRA-291` (the three most recent
   index-migration entries: `query.py`, `validate.py`, `generate_retro.py` reads migrated to the
   SQLite index), `INFRA-283`/`INFRA-284`/`INFRA-286` (phase-agent case-fold, outlier flagging,
   stats-phase-outliers-expose), `INFRA-288` (pause-resume seq-collision fix). These establish that
   this *class* of agent-tooling change is tracked in `infrastructure.yaml` as P2 entries — **this
   ticket should add its own new P2 entry to `infrastructure.yaml`** once implemented (no existing
   entry to update; this is net-new tooling behavior, not a change to already-ledgered behavior).
   No existing entry's `status` needs to change.

Notably, **`TCK-20260721-BASELINE-MONITORING-MANIFEST`** (the closest sibling precedent, same
"new read-only tool over `agent-monitoring/*.jsonl`" shape) has **no parity ledger entry at all** —
confirmed by grepping `infrastructure.yaml` for its ticket ID (zero hits) and by that ticket's own
investigation.md explicitly concluding "No parity ledger entry needs updating... and none should be
added — the parity ledger tracks Mechanics Bible/engine-contract semantic parity, not agent-tooling
infrastructure." That conclusion conflicts with the more recent precedent set by INFRA-281 through
INFRA-291 (all of which *are* agent-tooling infrastructure entries, added after
TCK-20260721-BASELINE-MONITORING-MANIFEST landed). **This is a real, unresolved inconsistency in
how this repo's parity ledger scope has been applied to `tools/agent-monitoring/` changes over
time** — flagged as an open question below rather than assumed either way.

No `P0` parity entries are touched by this ticket in either interpretation.

## Prior Work

- **`stored_artifacts/TCK-20260721-BASELINE-MONITORING-MANIFEST/`** (investigation.md + plan.md, both
  read in full) — the direct architectural precedent for this ticket: a new, strictly read-only
  tool over `agent-monitoring/*.jsonl`, built on `legacy_reader.py`'s `classify_provenance` and a
  streaming-scan discipline. Its plan.md's "Decided" section (deterministic manifest schema, no
  wall-clock field, output-path safety guard, byte-identical-reproducibility test, zero-mutation
  integration test mirroring `tests/agent_replay/test_no_mutation_snapshot.py`) is the template this
  ticket's own plan.md should follow almost verbatim, adapted from "corpus inventory" to "baseline
  behavior metrics."
- **`TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE`/`-VALIDATE-INDEX-MIGRATE`/`-RETRO-INDEX-MIGRATE`**
  (all done, `INFRA-289`/`INFRA-290`/`INFRA-291`) — migrated `query.py`/`validate.py`/
  `generate_retro.py`'s read paths from linear JSONL scans to the derived SQLite index, with a
  JSONL-fallback contract preserved (`generate_retro.py`'s `_load_runs_and_events`, the one
  exception that must never hard-fail). This ticket's own baseline tool should reuse this same
  index-with-fallback pattern for its own data loading, not add a fourth independent loader.
- **`TCK-20260719-RETRO-OUTLIER-FLAGS`** (`INFRA-284`) — established the "flag a value as an
  outlier without claiming to explain *why*" framing (`_flag_outliers()`, `OUTLIER_MEDIAN_MULTIPLIER
  = 3`, `_OUTLIER_MIN_GROUP_SIZE = 3`) that this ticket's phase-duration reporting should likely
  reuse for surfacing pause-contaminated runs, rather than inventing a new significance threshold.
- **`TCK-20260719-PHASE-AGENT-CASE-FOLD`** (`INFRA-283`) and **`TCK-20260706-MONITORING-REASON-CODE`**
  — both establish that this codebase already treats "derive a coarse signal from existing fields,
  document it as a proxy, do not fabricate precision" as the house style for agent-monitoring
  reporting — directly the posture this ticket's AC demands for all 4 of its metric categories.
- **`TCK-20260728-PHASE0-PREREQ-CONFIRMATION`** (done, sibling ticket in this same epic) — confirmed
  the execution-identity/writer/consent-gate prerequisite is satisfied; this ticket does not need to
  re-verify that (it is a read-only *reporting* tool, not a writer change) but inherits the same
  "monitoring write failure must never fail the workflow" posture as a non-goal to preserve (this
  ticket writes nothing to `agent-monitoring/` at all).
- **`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`**
  — source doc; this ticket operationalizes exactly one line of its "Sequenced Future Epic" item 1
  ("Baseline and evaluation fixtures"). No later phase (2-7) of that doc is in scope here.
- No stored artifact anywhere in `stored_artifacts/` computes context-tokens/follow-up-search-count/
  gap-aware-duration/review-rework specifically — this is genuinely new reporting logic, not a
  duplicate of prior work.

## Risks and Open Questions

1. **Parity ledger scope inconsistency (see above) is unresolved and blocks a clean answer to "does
   this ticket need a parity ledger entry."** Recent precedent (`INFRA-281`-`INFRA-291`) says yes;
   the most structurally similar sibling ticket (`TCK-20260721-BASELINE-MONITORING-MANIFEST`) says
   no. Recommendation for Plan phase: follow the more recent precedent (add one new P2
   `infrastructure.yaml` entry once implemented) since it is both more recent and more numerous, but
   this is a judgment call, not a settled rule — do not silently pick one without noting the
   inconsistency in plan.md.
2. **"Follow-up-search-count" has two materially different valid derivations, and the ticket AC's
   literal wording ("derived only from existing `tool_call_count` data") points at the coarser one.**
   Option A (literal AC wording): reuse the existing aggregate `tool_call_count` field per
   `(run_id, seq)` event as a coarse total-tool-activity proxy — simple, matches AC text exactly,
   but conflates "did a search" with "did any tool call at all." Option B (more precise, also
   "existing data," just at finer grain): filter `tools.jsonl` by literal `tool` values already
   proven to exist (`mcp__knowledge-search__search_docs`, `ToolSearch`, `WebSearch`, possibly
   `Skill` for `/graphify`-style invocations) — this directly answers "how many follow-up searches"
   rather than "how much tool activity," but is a filter over `tools.jsonl` rather than literally
   "`tool_call_count` data," so it is a stricter reading of what counts as reuse vs. new logic. This
   is a genuine open question for the Plan phase — implementing Option B without flagging the
   AC-wording tension would risk an implementer believing they satisfied AC2 when a literal reading
   might disagree. Do not assume an answer.
3. **"Review rework" can only be a cross-run proxy (see Current Behavior), and its exact grouping
   rule is undefined by the ticket.** The most defensible derivation given only existing fields:
   group `runs.jsonl` records by `run_id`, sort by `start_ts`, and flag a `run_id` as "reworked" if
   any record's `final_status`/`status` is `NEEDS_CHANGES`/`BLOCKED`/`TESTS_FAILED`/`DOD_BLOCKED` and
   a chronologically later record for the same `run_id` reaches `DONE`. This needs an explicit
   Plan-phase decision on which non-terminal statuses count as "rework-triggering" versus which are
   simply abandoned (never resumed) — the data cannot distinguish "resumed and fixed" from "a
   different, unrelated later ticket coincidentally reusing the same `run_id`" (should not happen
   given `run_id` = ticket ID uniqueness, but is worth a defensive note, not a blocking risk).
4. **Report output location is unspecified by the ticket**, mirroring
   TCK-20260721-BASELINE-MONITORING-MANIFEST's own open question #5. Given this is explicitly a
   one-off/periodic baseline snapshot (not the recurring weekly retro), writing into
   `agent-monitoring/retro/` (shared with `RETRO-*.md`) would conflate the two report families. A
   dedicated location (e.g. a new script under `tools/agent-monitoring/` printing to stdout by
   default, with an optional `--output` guarded the same way `manifest.py`'s
   `_assert_safe_output_path()` guards its own output) is the pattern to follow, but the exact path
   is a Plan-phase decision.
5. **Corpus counts will have grown again by the time this ticket is implemented** (721/3,831/68,538
   lines measured now vs. 702/3,642/65,023 a week ago in the manifest ticket) — any specific counts
   cited in plan.md/tests should be treated as illustrative, re-measured at implementation time, not
   hardcoded as "the" corpus size.
6. **AC1's "unavailable" framing for context-tokens is a factual restatement, not new discovery** —
   `docs/agent-monitoring/schema.md` (lines 74-78), `docs/agent-monitoring/README.md` (lines 24-26),
   and `cost_proxy.py`'s own docstring (line 6) all already say the same thing independently. This
   metric is the simplest of the 5 (report a literal `"unavailable"` marker with a citation), and
   the only real risk is citing the wrong doc location or letting a downstream consumer coerce it to
   `0`/`null` without the explicit marker string.

## Anti-Drift Hazards

- **Do not modify `generate_retro.py`, `validate.py`, `manifest.py`, `legacy_reader.py`,
  `vocabulary.py`, or `cost_proxy.py`.** All are named "Related Code Areas" for *reading and
  reusing*, not editing — this ticket's own Out of Scope requires "reuse... not reimplement," and
  every one of these modules is actively depended on by other tools (dashboard, `weight_sensitivity_check.py`,
  `baseline_manifest_gate.py`) that must not regress.
- **Do not write into `agent-monitoring/retro/`.** That directory is `generate_retro.py`'s own
  output space, tied to its weekly-cadence `index.md` rebuild (`_update_index()`); a baseline
  snapshot tool writing there would pollute that index or be silently overwritten by the next retro
  run.
- **Do not conflate `duration_s` (raw) with an "active duration" that does not exist yet.** The
  ticket's own Out of Scope is explicit that this must not depend on
  `idea_agent_monitoring_active_duration.md` — a tempting shortcut would be to informally
  approximate gap-awareness (e.g. "assume the largest inter-event gap is idle") without building the
  real `duration_utils.py` module; doing so half-implements a documented future idea inside a ticket
  explicitly scoped not to depend on it. The correct move is the flag-as-contaminated branch, not an
  ad hoc gap heuristic.
- **Do not fabricate a review-rework count from anything other than existing `final_status`/
  `reason_code`/multi-record-per-`run_id` grouping.** It would be easy to (incorrectly) treat
  `reason_code_breakdown`'s existing counts as a rework signal — they count *why* a single gate
  failed, not whether the same ticket was later resubmitted and passed.
- **Do not let this ticket become a second data-loading implementation.** Given
  `generate_retro.py::_load_runs_and_events()` already has the index-with-JSONL-fallback contract,
  a bespoke loader here (e.g. calling `sqlite3.connect()` directly, or a fourth `load_jsonl`) would
  duplicate a pattern this repo has explicitly consolidated 3 times already
  (`INFRA-289`/`INFRA-290`/`INFRA-291`).
- **Do not silently drop the AC-mandated caveat text.** Every one of the ticket's 4 substantive ACs
  requires an explicit, visible marker string in the report output ("unavailable",
  "not_yet_instrumented", pause-contaminated flag, "derived proxy not fabricated") — a report that
  merely omits a metric instead of stating why is not equivalent to satisfying the AC, and a
  reviewer diffing against the AC text specifically should be able to find each marker string
  verbatim in the output.
- **This ticket must remain read-only end-to-end**, including its own tests — any test exercising
  the new tool against the real corpus must follow `test_agent_monitoring_manifest.py`'s
  zero-mutation integration-test pattern (dirty-tree-aware pre/post hash snapshot), not merely
  assert "no exception was raised."
