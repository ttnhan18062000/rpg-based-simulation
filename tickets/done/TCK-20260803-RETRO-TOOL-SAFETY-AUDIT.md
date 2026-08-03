---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260803-RETRO-TOOL-SAFETY-AUDIT
phase: done
date: 2026-08-03
tags: [agent-monitoring, retro]
---

# TCK-20260803-RETRO-TOOL-SAFETY-AUDIT

## Title
Add a retro report section auditing parity_index.py safe-usage and search-before-grep hard-rule compliance

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
While reviewing this session's own work, the user asked whether the retro/agent-monitoring system
can verify that the new parity read-path tooling (`tools/parity_index.py`) and the project's
context-search hard rule (CLAUDE.md: `search_docs` + `graphify` before any grep/raw file read) were
actually used correctly. Answering that required hand-querying `agent-monitoring/tools.jsonl`
directly — the weekly retro report (`tools/agent-monitoring/generate_retro.py`) has no section that
would have surfaced either answer on its own.

Concretely verified by hand this session, across all 7 real Investigate-phase agent calls and all 4
parity-epic ticket runs:
1. `mcp__knowledge-search__search_docs` and `graphify` (via Bash) both fired within the first 3-6
   tool calls of every Investigate phase, always before the first `grep` (which never appeared
   earlier than call #11 in any of the 7). The hard rule was genuinely honored, not just claimed.
2. Zero `Edit`/`Write` tool calls ever targeted any `docs/parity_ledger/*.yaml` file across the 4
   parity-epic runs, and every live `parity_index.py build` CLI invocation pointed at a scratch path
   (e.g. `/tmp/pi_smoke2/parity.db`), never the real repo DB path.

Both checks are real and currently only answerable by a one-off manual query. This ticket adds them
as a standing, automatically-computed retro section so future weeks don't require the same manual
`tools.jsonl` archaeology.

## Scope
- Add a new pure-computation function to `tools/agent-monitoring/generate_retro.py` (mirroring
  `compute_retrieval_metrics(events)`'s existing shape — a standalone function taking already-loaded
  data and returning a dict, no file I/O of its own) that reads `agent-monitoring/tools.jsonl` rows
  (not `events.jsonl` — `tools.jsonl` is the raw per-tool-call log this audit needs) and computes,
  per run_id/seq where a real `Investigate` phase occurred (cross-referenced against
  `events.jsonl`'s `phase` field the same way `compute_shadow_baseline_comparison` already
  cross-references event data):
  - **Search-before-grep compliance**: for each Investigate-phase seq, whether
    `mcp__knowledge-search__search_docs` (or a `graphify` Bash call) appears before the first
    `Grep` tool call or Bash call containing `grep` in its `input_summary` — a boolean per
    (run_id, seq), aggregated into a compliance rate for the period.
  - **`parity_index.py` write-safety**: across the whole period, whether any `Edit`/`Write` tool
    call's `input_summary` names a `docs/parity_ledger/*.yaml` path, and whether any
    `parity_index.py build` Bash invocation's `input_summary` targets a path under the real repo's
    `docs/parity_ledger/`-adjacent `parity-index/` location rather than a scratch/tmp path — both
    should be zero; report the actual count, never assume it's zero.
- Wire the new section into `generate()`'s markdown output, following the existing conditional-
  render convention (e.g. "Shadow vs. Baseline Retrieval Comparison"'s pattern: omitted entirely
  when there's no real Investigate-phase data in the period, never rendered as an empty table).
- Add a row to `docs/guides/agent_monitoring.md`'s "Report Sections" table describing what to look
  for in the new section, matching that table's existing terse per-row style.
- Add tests to `tests/tools/test_generate_retro.py` mirroring `TestComputeRetrievalMetrics`'s
  fixture-based structure: at minimum, a compliant-ordering fixture (search_docs before grep) that
  reports 100% compliance, a violating-ordering fixture (grep before search_docs) that reports the
  violation, a clean parity-safety fixture (zero writes to `docs/parity_ledger/`, all builds to
  scratch paths) that reports zero violations, and a synthetic violating fixture (a fabricated
  `Edit` call targeting `docs/parity_ledger/combat_movement.yaml`) that the new function correctly
  flags — do not rely solely on the real, currently-clean `tools.jsonl` data to prove the check
  works, since a check that has never seen a violation could be silently broken.

## Out of Scope
- Retroactively re-auditing or re-writing any historical `tools.jsonl`/`events.jsonl` data — this
  is a new, forward-looking read-only report section over existing append-only logs.
- Making this a blocking gate anywhere in `.claude/workflows/implement-ticket.js` — matches every
  other retro section's status as a human-reviewed report, not a workflow gate. If a future ticket
  wants to promote search-before-grep compliance or parity-write-safety into an actual blocking
  check (e.g. a new `PreToolUse` hook), that is a separate, explicitly-scoped decision, not implied
  by this ticket.
- Generalizing the "write-safety" check beyond `docs/parity_ledger/*.yaml` to any other tool/data
  path (e.g. a general "which tools touched which protected paths" audit) — scope this specifically
  to `parity_index.py`'s read-only guarantee, the concrete case that prompted this ticket. A more
  general protected-path audit is a plausible future ticket, not this one.
- Any change to `tools/parity_index.py`, `tools/context_packet_assembler.py`, or the `PostToolUse`
  hook that writes `tools.jsonl` itself (`tools/agent-monitoring/post_tool_hook.py` or equivalent) —
  this ticket only reads existing log data, it does not change what gets logged.
- Adding the shadow-`ContextPacket` mechanism's "correctness" to this ticket — that mechanism
  (`compute_retrieval_metrics`) already has its own retro section; it remains structurally empty
  today because no real retrieval pipeline is wired into its call site (a separate, already-known,
  already-out-of-scope gap — not something this ticket resolves).

## Acceptance Criteria
- [x] A new pure-computation function in `tools/agent-monitoring/generate_retro.py`, given
      `runs`/`events`/`tools` fixture data, correctly reports search-before-grep compliance rate
      per Investigate-phase (run_id, seq) pair and a `parity_index.py` write-safety violation count,
      matching what a manual query against real `tools.jsonl` independently confirms for the same
      period.
- [x] The new function never crashes on legacy/malformed rows (missing `input_summary`, missing
      `seq`, tool-call rows with no matching `phase`/`events.jsonl` cross-reference) — same
      graceful-skip discipline `_is_legacy_event`/`_resolve_status` already use elsewhere in this
      file.
- [x] `generate()`'s markdown output includes the new section, conditionally rendered (omitted, not
      empty, when the period has zero real Investigate-phase tool-call data), matching the existing
      "Shadow vs. Baseline Retrieval Comparison" section's render-gating pattern.
- [x] `docs/guides/agent_monitoring.md`'s "Report Sections" table has a new row for this section.
- [x] New tests in `tests/tools/test_generate_retro.py` include at least one synthetic fixture that
      proves each check can detect a real violation (not just confirm today's clean data stays
      clean) — a compliance-ordering violation and a `docs/parity_ledger/` write violation, each
      with a corresponding passing/compliant fixture for contrast.
- [x] Running `compute_tool_safety_metrics()` (via `python3 tools/agent-monitoring/generate_retro.py
      --all` or an equivalent filtered invocation) against this repo's real
      `agent-monitoring/*.jsonl` data, scoped to the ticket's own hand-verified sample — the 4
      tickets under `TCK-20260731-PARITY-INDEX-EPIC` (`TCK-20260731-PARITY-INDEX-BASELINE`,
      `TCK-20260731-PARITY-INDEX-IMPORTER`, `TCK-20260731-PARITY-IMPACT-PROOF`,
      `TCK-20260731-PARITY-READPATH-GATE`) — shows: (a) 100% search-before-grep compliance across
      their real (non-blocked-retry) Investigate phases (4/4 as independently re-verified during
      this ticket's own close-out), and (b) 0 confirmed real `docs/parity_ledger/*.yaml` write
      violations. NOTE (narrowed from the original "0 violations across the whole period" framing,
      per this ticket's own close-out decision — the original framing was checkable only against
      the full multi-month corpus, where real drift exists and is out of this ticket's scope to
      fix): the `unsafe_parity_build_count` sub-check may additionally flag build-invocation
      candidates purely as an artifact of `tools.jsonl`'s 80-char `input_summary` truncation (see
      Assumptions / Open Questions) — any such flagged candidate must be individually traced back to
      its full historical command before being treated as a real violation; this AC is satisfied
      once every flagged candidate in the 4-ticket window is confirmed a false positive (as the one
      found during this ticket's own verification was), not by the raw count reading exactly 0.

## Related Tickets
- TCK-20260731-PARITY-INDEX-EPIC (built the `parity_index.py` read-only tooling this audit checks)
- TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT, TCK-20260729-RETRIEVAL-RETRO-VIEWS,
  TCK-20260729-SHADOW-BASELINE-COMPARISON (established the `compute_*_metrics(events)` /
  conditionally-rendered-section precedent this ticket's implementation should mirror)
- TCK-20260704-RETRO-LOOP-ENFORCEMENT (established the retro cadence/nudge convention this new
  section becomes part of)

## Related Docs
- docs/guides/agent_monitoring.md (Report Sections table — gets a new row)
- docs/agent-monitoring/schema.md (tools.jsonl field reference)

## Related Stored Artifacts
None yet (scoped, not yet investigated/planned).

## Related Code Areas
- tools/agent-monitoring/generate_retro.py (new function + `generate()` wiring)
- tests/tools/test_generate_retro.py (new tests)
- agent-monitoring/tools.jsonl (read-only data source — the field this audit reads that no existing
  retro computation reads)
- tools/parity_index.py (read-only reference — the tool being audited, not modified)

## Assumptions / Open Questions
- Assumes `tools.jsonl`'s existing `run_id`/`seq` fields are sufficient to cross-reference against
  `events.jsonl`'s `phase` field to identify "which tool calls happened during an Investigate
  phase" — this matches the manual query technique already proven working this session, but
  Investigate should confirm no edge case (e.g. a tool call recorded with `seq: null`, per this
  project's own documented sidecar-attribution-gap precedent) silently breaks the cross-reference
  rather than degrading gracefully.
- Whether the write-safety check should also cover `.gitignore`/Makefile paths (mirroring the
  parity-epic tickets' own protected-file lists) or stay narrowly scoped to
  `docs/parity_ledger/*.yaml` is left for Investigate/Plan to decide — this ticket's Scope
  deliberately names only the parity-ledger YAML case as the concrete, already-verified example.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260803-RETRO-TOOL-SAFETY-AUDIT/plan.md`'s 8
ordered steps, in `tools/agent-monitoring/generate_retro.py`:

- Added four module-level pure predicates near `_normalize_agent`/`_collect_inprogress_tagged_tickets`:
  `_is_search_or_graphify_call`, `_is_grep_call`, `_is_parity_ledger_yaml_write`,
  `_is_unsafe_parity_build_call` — all literal to plan.md's spec, no deviation.
- Added `compute_tool_safety_metrics(events, tools) -> dict` after
  `compute_shadow_baseline_comparison`, computing `search_before_grep` (scoped to Investigate-phase
  `(run_id, seq)` pairs derived from `events.jsonl`'s `phase` field via `_normalize_phase`) and
  `parity_write_safety` (unscoped — scans the whole `tools` argument, per plan.md Step 2's explicit
  "not scoped to Investigate-phase pairs" instruction and the ticket's own "across the whole period"
  Scope text).
- `generate()` gained a trailing `tools=None` parameter, defaults to `[]` internally, calls
  `compute_tool_safety_metrics(events, tools)`, and renders a new "## Tool Safety Audit" section
  (gated solely on `investigate_pair_count` nonzero) after "## Shadow vs. Baseline Retrieval
  Comparison" and before "## Notes".
- `main()` now loads `all_tools = load_jsonl(DEFAULT_TOOLS_FILE)` and window-filters it alongside
  `runs`/`events` in all three branches (`--all`, `--days`, default/`--week`), passing it to
  `generate(..., tools=tools)`.
- `docs/guides/agent_monitoring.md`'s Report Sections table got a new "Tool Safety Audit" row.
- `docs/parity_ledger/infrastructure.yaml` got a new `INFRA-315` entry (P2, `status: verified`),
  mirroring INFRA-300's shape; validated standalone against `docs/parity_ledger/schema.json` via
  `jsonschema` (a pre-existing, unrelated schema violation at index 284 — `proof_type: feature`,
  not one of this ledger's own valid enum values — was found while validating the whole file; it
  predates this ticket and is out of scope to fix here).

**Step 8 finding (important — read before closing this ticket):** running
`python3 tools/agent-monitoring/generate_retro.py --all` against the real, whole-history
`agent-monitoring/*.jsonl` corpus (739 runs, 3973 events) does **not** match AC5's hand-verified
expectation. Actual output:
- Search-before-grep: **63.4% (71/112)**, not "100% across the 7 real Investigate phases."
- Parity ledger write-safety: **355** `docs/parity_ledger/*.yaml` write violations (not 0), plus
  **1** flagged "unsafe" `parity_index.py build` invocation (not 0).

Root cause, confirmed by inspecting the matched rows directly:
1. **Search-before-grep gap is real, not a bug.** The ticket's "7 real Investigate phases" figure
   was a narrow, session-scoped hand count (presumably this session's own recent Investigate calls),
   not the whole corpus. The whole-history corpus has 112 real Investigate-phase `(run_id, seq)`
   pairs, and 41 of them (36.6%) genuinely did not search-before-grep historically. This is the
   audit tool correctly surfacing a real historical compliance gap the narrow manual check missed —
   working as intended, not a defect in this implementation.
2. **Parity write-safety's 355 figure is a scope/semantics gap between the ticket's Request Summary
   and its Scope text, not a real read-only-guarantee violation.** The 355 matched rows span 114
   distinct, unrelated `run_id`s (e.g. `TCK-20260614-CERT-*`, `TCK-20260619-E*` epic children,
   `TCK-20260627-P*`, dozens of `TCK-20260629`..`TCK-20260730` tickets) — every one of these is a
   normal, authoritative `parity-updater`-agent edit to `docs/parity_ledger/*.yaml` during that
   ticket's own Parity workflow phase, exactly as CLAUDE.md's Authoritative Mechanics Rule requires
   ("If logic changes, update the corresponding doc AND the parity ledger entry"). None of them
   involve `tools/parity_index.py` at all — the actual invariant this ticket's Request Summary named
   ("Zero Edit/Write tool calls ever targeted any docs/parity_ledger/*.yaml file across the 4
   parity-epic runs") was scoped to the 4 `TCK-20260731-PARITY-INDEX-EPIC` child runs specifically,
   but the Scope text ("across the whole period... report the actual count, never assume it's zero")
   and plan.md Step 2 (explicitly unscoped) both call for scanning every run in the period. Both
   readings are individually defensible and both are followed exactly as written in their respective
   source documents — but they are mutually inconsistent at real-corpus scale, and only the
   real-corpus run in Step 8 surfaces that inconsistency.
3. **The single "unsafe build" flag is a false positive from `input_summary` truncation.** The
   matched row (`TCK-20260731-PARITY-IMPACT-PROOF`) is a truncated multi-line Bash command —
   `'python3 tools/parity_index.py --help 2>&1\necho "---build---"\npython3 tools/parit'` — whose
   logged `input_summary` was cut off mid-command. It matches `_is_unsafe_parity_build_call`'s
   substring test (`"parity_index.py"` and `"build"` both present — the latter from the `echo
   "---build---"` separator comment, not a real build invocation) purely because the truncation cut
   off the real command's `--db-path /tmp/...` argument before it could be logged. The actual build
   invocation in that same run (a separate tools.jsonl row) correctly targets a scratch path and is
   not flagged.

Per CLAUDE.md's hard rule ("never edit an artifact to make a gate pass instead of fixing the
underlying substance... stop and report it truthfully") and this ticket's own architecture-review
approval covering the plan as written, I did **not** alter `_is_parity_ledger_yaml_write` or
`_is_unsafe_parity_build_call` to narrow their scope, and did not touch the correctly-computed
search-before-grep logic. The implementation matches plan.md exactly; AC5's literal wording ("match
this ticket's own hand-verified findings... for the equivalent time window") is not satisfied by the
real `--all` corpus, for the reasons above.

The `agent-monitoring/retro/RETRO-ALL.md` file that this verification run wrote to disk was reverted
(`git checkout --`) after inspection — no output file from Step 8 is committed, per plan.md's
explicit instruction.

**Human decision (post-implementation, before close-out):** AC5 is narrowed to the ticket's own
original hand-verified sample — the 4 `TCK-20260731-PARITY-INDEX-EPIC` child-ticket runs — rather
than the whole multi-month corpus. Rationale: the Request Summary's claim was always specifically
about those 4 runs, and the whole-corpus number (355 matches, 114 unrelated tickets) is dominated by
normal `parity-updater` edits the Authoritative Mechanics Rule requires — not a `parity_index.py`
read-only-guarantee violation of the kind this ticket set out to audit. Rescoping the check's own
semantics (e.g. filtering by whether a run's tools also touch `parity_index.py`) or accepting the
full-corpus 63.4%/355 numbers as a new baseline are both left to a future ticket if wanted; neither
was required to close this one.

Re-verified against the real, current corpus for the narrowed window (after independently rebuilding
the derived SQLite index, which had gone stale — see `TCK-20260803-AGENT-MONITORING-INDEX-PHONY-FIX`,
the hotfix this discovery led to): filtering `events`/`tools` to the 4 named run_ids and calling
`compute_tool_safety_metrics()` directly gives `search_before_grep.compliance_rate = 1.0` (4/4 real,
non-blocked-retry Investigate phases) and `parity_write_safety.parity_ledger_yaml_write_count = 0`.
`unsafe_parity_build_count` is `1`, but that single flagged row
(`TCK-20260731-PARITY-IMPACT-PROOF` seq 5) is confirmed a false positive: its `input_summary` is a
truncated multi-line Bash script cut off before the real `--db-path /tmp/pi_smoke2/parity.db`
argument was logged, matching `"build"` only via an unrelated `echo "---build---"` separator line —
the actual build invocation (the very next `tools.jsonl` row for the same run) correctly targets a
scratch path. AC5 as narrowed above is satisfied.

## Test Summary

96/96 tests pass in `tests/tools/test_generate_retro.py`
(`.venv/bin/python3 -m pytest tests/tools/test_generate_retro.py -q`), including 20 new tests added
by this ticket:
- 6 search-before-grep compliance tests (Step 1: compliant via `search_docs`, compliant via
  `graphify` Bash call, non-compliant via `Grep` tool, non-compliant via Bash `grep`, aggregated
  rate across 3 Investigate pairs, non-Investigate-phase calls ignored).
- 3 parity write-safety tests (Step 2: zero-violation clean fixture, detects an `Edit` targeting
  `docs/parity_ledger/combat_movement.yaml`, detects both a no-`--db-path` and a real-repo-path
  `build` invocation while excluding a scratch-path one).
- 1 malformed-row graceful-degradation test and 1 I/O-purity architecture-guard test (Step 3).
- 2 rendering tests (Step 5: section present with correct compliance-rate/violation-count text when
  Investigate tool data exists; section fully omitted — not empty-rendered — both when `tools` is
  omitted and when `tools=[]`).
- Regression: all 74 pre-existing tests in this file still pass unmodified, confirming `generate()`'s
  new trailing `tools=None` parameter is backward-compatible with every existing call site (the
  fixed-corpus byte-identical test and the shadow-comparison suite both call `generate()` without a
  `tools` argument and are unaffected).

Step 8 real-corpus verification (`python3 tools/agent-monitoring/generate_retro.py --all` against
739 runs / 3973 events): ran successfully, section renders correctly, but whole-corpus numbers do
not match the original hand-verified expectation — see Implementation Notes above for the full
finding and root cause. Following the post-implementation decision to narrow AC5 to the ticket's
own original 4-run sample, a second, targeted re-verification (filtering `events`/`tools` to just
`TCK-20260731-PARITY-INDEX-BASELINE`, `-IMPORTER`, `-IMPACT-PROOF`, `-READPATH-GATE` and calling
`compute_tool_safety_metrics()` directly) confirms: 100% search-before-grep compliance (4/4),
0 real `docs/parity_ledger/*.yaml` write violations, and the 1 flagged build-invocation candidate
confirmed a truncation-driven false positive by tracing it to its full historical command. AC1-AC5
are all satisfied as of this narrowed, close-out verification.

## Files Changed
- `tools/agent-monitoring/generate_retro.py`
- `tests/tools/test_generate_retro.py`
- `docs/guides/agent_monitoring.md`
- `docs/parity_ledger/infrastructure.yaml`

## Completion Summary
Added `compute_tool_safety_metrics(events, tools)` to `generate_retro.py`, a new pure function
auditing search-before-grep hard-rule compliance for real Investigate-phase tool calls and
`parity_index.py` write-safety (zero-tolerance `docs/parity_ledger/*.yaml` write / unsafe real-path
`build` invocation counts), wired into `generate()`'s Markdown output as a new, conditionally-gated
"## Tool Safety Audit" section, with `tools.jsonl` now threaded through `main()`. Docs
(`agent_monitoring.md`) and the parity ledger (`INFRA-315`) were updated to match. All 20 new tests
plus all 76 pre-existing tests in `tests/tools/test_generate_retro.py` pass (96/96 total).

The whole-corpus `--all` verification run (Step 8) found the numbers did not match the original
hand-verified expectation (63.4% not 100% search-before-grep compliance; 355 not 0 parity-ledger-yaml
write matches) — explained in Implementation Notes as, respectively, a genuine historical compliance
gap the audit correctly surfaces, and a scope/semantics mismatch between the ticket's Request Summary
(narrowly meant "parity_index.py's own read-only guarantee," scoped to 4 specific runs) and its
literally-implemented Scope text (unscoped "across the whole period," which also counts the many
legitimate, expected `parity-updater`-agent ledger edits from unrelated tickets as "violations"). No
code was altered to force a match — this was reported truthfully per CLAUDE.md's gate-truthfulness
rule, then resolved by a post-implementation human decision to narrow AC5 to the ticket's own
original 4-run sample (`TCK-20260731-PARITY-INDEX-EPIC`'s children) rather than the whole corpus.
Re-verified against that narrowed window directly: 100% search-before-grep compliance (4/4), 0 real
parity-ledger write violations, and the one flagged build-invocation candidate confirmed a
truncation-driven false positive (traced to its full historical command). AC1-AC5 are all satisfied.
The whole-corpus 63.4%/355 numbers remain real and are left for an optional future ticket to address
(rescope `parity_write_safety` to runs whose own tool-call history touches `parity_index.py`, or
accept the full-corpus baseline) — not required by this ticket's now-narrowed scope.
