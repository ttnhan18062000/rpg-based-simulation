---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260803-RETRO-TOOL-SAFETY-AUDIT
artifact_type: investigation
tags: [agent-monitoring, retro]
---

# Investigation — TCK-20260803-RETRO-TOOL-SAFETY-AUDIT

## Current Behavior

**`tools/agent-monitoring/generate_retro.py`** (2026-08-03 snapshot, 1157 lines) has no code path
that reads `agent-monitoring/tools.jsonl` at all. Its three `compute_*` functions
(`compute_retro_metrics(runs, events, tickets_root)` at :322, `compute_retrieval_metrics(events)`
at :574, `compute_shadow_baseline_comparison(events)` at :682) each take only `runs`/`events` as
input. `_load_runs_and_events()` (:66-100) sources `runs`/`events` from the derived SQLite index
(`agent-monitoring-index/monitoring.db`, on-demand-built if missing, falling back to
`load_jsonl(RUNS_FILE)`/`load_jsonl(EVENTS_FILE)` on any failure) and is `main()`'s (:1088) sole
data-loading call — `main()` never loads `tools.jsonl`. `generate()` (:699-1085) renders
`compute_retro_metrics()` + `compute_retrieval_metrics()` + `compute_shadow_baseline_comparison()`
output to Markdown; there is no tools.jsonl-derived section anywhere in its output.

A sibling module, **`tools/agent-monitoring/retrieval_baseline_metrics.py`**, already establishes
the exact reusable "load runs/events via `_load_runs_and_events()`, load tools separately via
`load_jsonl(DEFAULT_TOOLS_FILE)`" pattern this ticket needs (`load_all_sources()` at :50-53:
`runs, events = _load_runs_and_events(); tools = load_jsonl(DEFAULT_TOOLS_FILE); return runs,
events, tools`). It also already classifies tool records by literal `tool` name
(`SEARCH_TOOL_NAMES = {"mcp__knowledge-search__search_docs", "ToolSearch", "WebSearch"}` at :36-40)
for an unrelated "follow-up search count" metric — **not** directly reusable for this ticket's
search-before-grep check, since that check's own tool-identification rule is different (a
`graphify` Bash call also counts as satisfying the hard rule; `ToolSearch`/`WebSearch` do not) —
see Anti-Drift Hazards below.

**`agent-monitoring/tools.jsonl`** rows (sampled from this session's own live data, e.g.
`agent-monitoring/tools.jsonl` tail) carry: `session_id`, `run_id`, `seq`, `phase`, `agent`, `ts`,
`tool`, `input_summary`, `status`, `duration_ms`, plus three fields not documented in
`docs/agent-monitoring/schema.md` — `execution_id`, `provider`, `ticket_id` (all `null` in the
sampled rows; `execution_id` is populated for `Agent`/downstream calls in this live session,
`provider":"claude"`). This is a pre-existing, ticket-adjacent documentation gap — schema.md's
tools.jsonl field table (lines 351-364) lists 9 fields, the live data has 12 — but it is not this
ticket's concern to fix (no new field is introduced by this ticket's own work), so it is noted
here as an observed gap, not folded into scope.

`seq` is `null`-safe by contract (schema.md: "`null` if the sidecar was not yet written at hook
time") and the negative-`seq` shadow-packet convention (schema.md's "Provenance" section,
`seq <= 0` for `context-packet-wrapper` rows) is a second documented edge case a
per-`(run_id, seq)` cross-reference must not crash on.

**`tools/parity_index.py`** (:1-120 read) is confirmed read-only by design and by two completed
epics (`TCK-20260731-PARITY-INDEX-EPIC` and its four children). `DEFAULT_DB_PATH = Path("parity-
index/parity.db")` (:63) is the real repo-relative default the `build` CLI subcommand writes to
when `--db-path` is not passed (`build_parser.add_argument("--db-path", default=str
(DEFAULT_DB_PATH))` at :655) — this is exactly the "real repo's ... `parity-index/` location"
described in the ticket's Scope. `docs/parity_ledger/*.yaml` is never opened in write mode anywhere
in this module — `IndexNotBuiltError`/`_connect_readonly` (:83-92) opens the derived DB with
`mode=ro`; the importer reads YAML via `yaml.safe_load`-style parsing only. `TCK-20260731-PARITY-
INDEX-EPIC`'s Completion Summary states explicitly: "no `docs/parity_ledger/*.yaml` file ... was
modified" across all four child tickets, and `TCK-20260731-PARITY-READPATH-GATE`'s own
`TestNoMutation` (byte-hash guard) independently confirms this. So the two invariants this
ticket's new check must verify (zero `Edit`/`Write` into `docs/parity_ledger/*.yaml`, zero
`parity_index.py build` invocation targeting the real `parity-index/` path) are currently true —
this session's own `tools.jsonl` (checked live) shows every historical `parity_index.py build`
Bash call and zero `docs/parity_ledger/` `Edit`/`Write` calls, matching the ticket's own
hand-verified numbers.

## Mechanics / Engine Constraints

None. This ticket is pure agent-orchestration/observability tooling — it does not touch
`src/`, does not change simulation state, formulas, or any Mechanics Bible (`docs/mechanics/`) or
Engine Contract (`docs/engine/`) law. No chapter/contract constrains this work.

## Docs Requiring Update

- `docs/guides/agent_monitoring.md`: AC explicitly requires a new row in the "Report Sections"
  table (§"Report Sections", currently rows for Run Summary through Outliers) describing what to
  look for in the new search-before-grep-compliance / parity-write-safety section, matching that
  table's existing terse per-row style (see the Outliers/Phase Status Distribution rows for the
  house style).
- `docs/parity_ledger/infrastructure.yaml`: every one of the four prior tickets that added a new
  `generate_retro.py` report section and left a discoverable trace in this ledger did add an
  entry under this file (INFRA-283 for `TCK-20260719-PHASE-AGENT-CASE-FOLD`'s new "Phase Status
  Distribution" section, INFRA-284 for `TCK-20260719-RETRO-OUTLIER-FLAGS`'s "Outliers" section,
  INFRA-298 for `TCK-20260729-RETRIEVAL-RETRO-VIEWS`'s "Retrieval Quality" section, INFRA-300 for
  `TCK-20260729-SHADOW-BASELINE-COMPARISON`'s "Shadow vs. Baseline" section), each tagged
  `support_boundary: Agent-orchestration/monitoring-pipeline tooling only -- no simulation
  behavior is involved`. The current highest ID is INFRA-314, so the next entry would be
  INFRA-315. This ticket's new report section is the same shape (new pure `compute_*` function +
  new conditionally-rendered `generate()` section) as all four precedents, so it should follow
  the same convention. See Risks and Open Questions below — one prior ticket in the same family
  (`TCK-20260708-RETRO-TAG-BREAKDOWN`) did *not* add an entry, so this is a strong-majority
  pattern (4/5), not an absolute one; flagged for Plan/human confirmation rather than assumed.

## Parity Ledger Overlap

No existing `docs/parity_ledger/*.yaml` entry currently documents `generate_retro.py`'s tools.jsonl
read path (there is none to document yet) or `parity_index.py`'s write-safety guarantee as a
monitoring/observability claim — `tools/parity_index.py`'s own read-only behavior is documented via
its module docstring and the `TCK-20260731-PARITY-INDEX-EPIC` family's tickets/stored artifacts,
not via a parity ledger entry (it has no legacy counterpart to be "in parity" with — it's new
tooling, not a reimplementation of prior mechanics). The closest related IDs, all `status:
verified`, `priority: P2`, in `docs/parity_ledger/infrastructure.yaml`:
- INFRA-283 (`TCK-20260719-PHASE-AGENT-CASE-FOLD`) — precedent for a new generate_retro.py
  aggregation + report section.
- INFRA-284 (`TCK-20260719-RETRO-OUTLIER-FLAGS`) — precedent for a new generate_retro.py
  aggregation + report section.
- INFRA-298 (`TCK-20260729-RETRIEVAL-RETRO-VIEWS`), INFRA-300 (`TCK-20260729-SHADOW-BASELINE-
  COMPARISON`) — precedent for a new pure `compute_*(events)`-shaped function plus a matching
  conditionally-gated Markdown section, the closest structural analog to this ticket's own two new
  checks.
None of these are P0, and none require a passing `test_path` as a blocking condition (only P0
entries do, per the Authoritative Mechanics Rule) — but the established convention in this
specific file is to still supply one. No P0 entries are touched by this ticket.

## Prior Work

- `TCK-20260731-PARITY-INDEX-EPIC` (+ its 4 children `PARITY-INDEX-BASELINE`/`-IMPORTER`,
  `PARITY-IMPACT-PROOF`, `PARITY-READPATH-GATE`): established and proved `tools/parity_index.py`'s
  read-only guarantee — the exact invariant this ticket's write-safety check now needs to keep
  verifying automatically going forward. `TCK-20260731-PARITY-READPATH-GATE`'s stored artifacts
  include `tests/tools/test_gate_a_readpath_review.py::TestNoMutation`, a source-hash-based
  no-mutation guard over 6 protected surfaces (including every `docs/parity_ledger/*.yaml` file and
  `tools/parity_index.py` itself) — a different mechanism (static source hashing at test time) from
  what this ticket needs (a retro-report-time audit of *historical tool-call log* evidence), but
  confirms the same invariant from a different angle.
- `TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT`, `TCK-20260729-RETRIEVAL-RETRO-VIEWS`,
  `TCK-20260729-SHADOW-BASELINE-COMPARISON`: established the precise `compute_*(events) -> dict`
  pure-function shape (no file I/O inside the function itself, loading happens in the caller) and
  the "omit the whole section when the period has zero relevant data, never render it empty" gating
  convention this ticket's Scope explicitly says to mirror. `compute_shadow_baseline_comparison`
  (:682-696) is the closest precedent for cross-referencing/partitioning by provenance
  (`vocabulary.infer_workflow(run_id) is not None`) the way this ticket needs to partition
  tools.jsonl rows by "did this happen during a real Investigate phase."
- `TCK-20260704-RETRO-LOOP-ENFORCEMENT`: established the retro-cadence nudge hook
  (`retro_nudge_hook.py`) this new section becomes one more input to (no direct code dependency —
  informational precedent only, per the ticket's own "Related Tickets" framing).
- `tools/agent-monitoring/retrieval_baseline_metrics.py::load_all_sources()` (:50-53): the direct,
  reusable precedent for loading `tools.jsonl` alongside `runs`/`events` in this module family —
  `runs, events = _load_runs_and_events(); tools = load_jsonl(DEFAULT_TOOLS_FILE)`. This ticket's
  `main()`/`generate()` wiring should follow the same shape rather than inventing a new loader.
- No stored artifact for `TCK-20260731-PARITY-INDEX-EPIC` or `TCK-20260704-RETRO-LOOP-ENFORCEMENT`
  exists under `stored_artifacts/` (both are `tickets/done/` only — the epic is scope-only by
  design, and RETRO-LOOP-ENFORCEMENT's `tickets/done/` file has no linked staging artifacts folder,
  consistent with it plausibly having shipped as a smaller-scope change). This is noted as a
  gap only insofar as it means this investigation could not cross-check RETRO-LOOP-ENFORCEMENT's
  own investigation/plan reasoning directly — its `tickets/done/` ticket body was not separately
  re-read in full for this investigation beyond the registry-derived summary, since it is
  informational precedent only and out of this ticket's direct code dependency path.

## Risks and Open Questions

- **Open question (ticket's own, unresolved):** whether the write-safety check should cover
  `.gitignore`/Makefile paths in addition to `docs/parity_ledger/*.yaml`. The ticket's own Scope
  text names only the YAML case as in-scope; Out of Scope explicitly defers generalizing beyond
  `parity_index.py`'s guarantee to a future ticket. Recommendation: Plan should scope narrowly to
  `docs/parity_ledger/*.yaml` only, per the ticket's own Out-of-Scope framing — do not expand.
  This does not block implementation either way since the ticket already states the narrow
  reading is acceptable ("This ticket's Scope deliberately names only the parity-ledger YAML case
  as the concrete, already-verified example").
- **Parity ledger entry precedent is 4/5, not 5/5** (see Docs Requiring Update above) —
  `TCK-20260708-RETRO-TAG-BREAKDOWN` added a new report section to `generate_retro.py` without a
  matching `infrastructure.yaml` entry. This investigation recommends following the majority
  pattern (add an entry) since the Authoritative Mechanics Rule's parity requirement is triggered
  by "logic changes," and three of the four precedent entries are for changes of the same shape
  (new pure compute function + new conditionally-rendered section) as this ticket. This is a
  judgment call for Plan/human review to confirm, not a hard blocker.
- **`generate()`'s data-loading signature change is a cross-cutting risk.** `generate(runs, events,
  label, week_str=None, tickets_root=None)` (:699) has no `tools` parameter today, and `main()`
  calls it as `generate(runs, events, label, week_str)` (:1119) after computing `runs`/`events`
  window-filtering. Adding the new section requires either (a) adding a `tools` parameter to
  `generate()` with a default (e.g. `None`/`()`) so existing callers/tests that construct
  `generate(runs, events, label)` without a `tools` arg keep working, or (b) loading `tools.jsonl`
  fresh inside `generate()` itself (violates the "no file I/O inside compute functions" precedent
  only if done inside the `compute_*` function itself — `generate()` doing its own I/O is already
  precedented, e.g. it never does today, but `main()` doing the I/O and passing it in is the
  existing convention judging by `_load_runs_and_events()`). Recommend (a), threading `tools`
  through `main()` exactly like `retrieval_baseline_metrics.py::load_all_sources()` already does,
  to keep `compute_*` functions themselves free of I/O per the module's established test guard
  (`test_function_is_read_only_no_write_call_or_file_open_in_write_mode` pattern in
  `tests/tools/test_generate_retro.py:1136`) — this is Plan's call, not asserted as the only valid
  design here.
- **`--days`/`--week` windowing currently filters `events` by `run_id in {r["run_id"] for r in
  runs}`** (main() :1105-1107, :1113-1115) — the new section will need the equivalent filter
  applied to `tools` (by `run_id`, not by `(run_id, seq)`, since a whole run's tool calls should be
  in-window together) for period-scoped reports (`--days N`, default current-week) to be
  consistent with how `runs`/`events` are already windowed. `--all` needs no such filter. This is
  an implementation detail Plan should pin down, not a design risk per se.
- **Not a genuine open question, but worth flagging for Plan:** the ticket's AC5 requires the new
  section's real-corpus numbers to match "100% search-before-grep compliance across the 7 real
  Investigate phases checked, 0 `docs/parity_ledger/*.yaml` write violations across the 4 parity
  runs checked" for "the equivalent time window" — this is only checkable once the function exists
  and is run with `--all` (the historical window spans multiple weeks/months), not `--days 7` or
  the current ISO week. Plan/Test should confirm the AC5 verification step explicitly uses `--all`.

## Anti-Drift Hazards

- **Do not conflate `retrieval_baseline_metrics.py`'s `SEARCH_TOOL_NAMES`
  (`{"mcp__knowledge-search__search_docs", "ToolSearch", "WebSearch"}`) with this ticket's
  search-before-grep tool-identification rule.** The ticket's own Scope text is explicit:
  "`mcp__knowledge-search__search_docs` (or a `graphify` Bash call)" satisfies the hard rule —
  `ToolSearch`/`WebSearch` are not named as satisfying it, and a `graphify` Bash call (`tool ==
  "Bash"` with `input_summary` starting with/containing `"graphify"`) is not a member of
  `SEARCH_TOOL_NAMES` at all. These are two different, purpose-built vocabularies for two
  different questions ("how many follow-up searches happened" vs. "was the CLAUDE.md hard rule
  honored") — importing the wrong one would silently produce a wrong compliance rate.
- **Do not use `_is_legacy_event`'s `agent is None` predicate as a proxy for "this tools.jsonl row
  predates phase/agent attribution."** `tools.jsonl` rows have their own, separate nullability
  story for `phase`/`agent` (schema.md: `null` for records predating
  `TCK-20260719-LIVE-PHASE-AGENT-LABEL`, or for out-of-workflow interactive calls) — do not reuse
  `events.jsonl`'s legacy-event discriminator against `tools.jsonl` rows; they are different files
  with different schema-evolution histories.
- **Do not assume `tools.jsonl`'s `seq` is always `>= 1`.** The negative-`seq` shadow-packet
  convention (`context-packet-wrapper` rows, `seq <= 0`) is real, documented, and disjoint from the
  normal per-phase range — a per-`(run_id, seq)` grouping that assumes positivity will silently
  misattribute or crash on these rows. `seq: null` (sidecar not yet written) must also degron
  gracefully, matching this file's existing pattern of excluding rather than crashing.
- **Do not make this section a workflow gate.** Explicitly Out of Scope — this stays a
  human-reviewed report section like every other `generate()` section, never wired into
  `.claude/workflows/implement-ticket.js`'s `phase(...)` gating.
- **Do not widen the write-safety check beyond `docs/parity_ledger/*.yaml`.** Explicitly Out of
  Scope per the ticket — a general "which tools touched which protected paths" audit is a
  plausible future ticket, not this one. Resist scope-creep into auditing other protected
  surfaces (e.g. `tools/gate_checks/`, `.claude/workflows/*.js`) even though the same
  cross-reference machinery would trivially extend to them.
- **Do not retroactively re-audit or rewrite historical `tools.jsonl`/`events.jsonl` data.**
  Explicitly Out of Scope — this is a forward-looking read-only report over the existing
  append-only logs; the function must never write to any `agent-monitoring/*.jsonl` file.
- **Do not modify `tools/parity_index.py`, `tools/context_packet_assembler.py`, or the
  `PostToolUse` hook that writes `tools.jsonl`.** All three are explicitly Out of Scope — this
  ticket only reads existing log data.
