---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE
phase: done
date: 2026-08-07
tags: [agent-monitoring, data-quality]
---

# TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE

## Title
`generate_retro.py`'s "Parity Ledger Write-Safety" metric still counts every normal
`parity-updater` edit as a "violation" — confirmed still misleading, exactly as
`TCK-20260803-RETRO-TOOL-SAFETY-AUDIT` already found and explicitly left for a future ticket

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found during a 2026-08-07 agent-monitoring retro (`agent-monitoring/retro/RETRO-2026-W32.md`
Notes §3). `compute_tool_safety_metrics()` (`tools/agent-monitoring/generate_retro.py`) flags
`parity_ledger_yaml_write_count` as a "zero-tolerance" count of every `Edit`/`Write` tool call
targeting `docs/parity_ledger/*.yaml`, rendered in the report under a "Parity Ledger Write-Safety"
heading. Directly re-verified this week's fresh number: **14 "violations," 100% of which
decompose to completely ordinary, correct `docs/parity_ledger/infrastructure.yaml` edits across 9
real ticket runs** (`TCK-20260702-OBSISO-*`, `TCK-20260803-DOC-UPDATER-*`,
`TCK-20260803-RETRO-TOOL-SAFETY-AUDIT`, `TCK-20260803-AGENT-MONITORING-INDEX-PHONY-FIX`,
`TCK-20260803-RETRIEVAL-EVENT-TS-OVERRIDE`) — every single one is exactly the
`parity-updater`-agent workflow CLAUDE.md's own Authoritative Mechanics Rule requires ("If logic
changes, update the corresponding doc AND the parity ledger entry"), not an actual
`parity_index.py` read-only-guarantee violation (the real, narrow thing this metric was built to
catch).

This is not a new finding — `TCK-20260803-RETRO-TOOL-SAFETY-AUDIT`'s own Implementation Notes
already discovered and fully documented this exact scope/semantics gap at real-corpus scale (355
matches historically, spanning 114 unrelated tickets) and explicitly recommended a fix
("rescope `parity_write_safety` to runs whose own tool-call history touches `parity_index.py`, or
accept the full-corpus baseline") — but that ticket's own human decision at close-out narrowed
its *own* acceptance criteria to a 4-run sample instead of fixing the metric's implementation,
deliberately leaving the underlying rescope "to a future ticket if wanted." This ticket is that
future ticket.

## Scope
1. **Investigate** (mandatory before Plan):
   - Confirm `_is_parity_ledger_yaml_write()`'s exact current matching logic
     (`tools/agent-monitoring/generate_retro.py`) and `compute_tool_safety_metrics()`'s call site.
   - Design the rescope: only count a `docs/parity_ledger/*.yaml` `Edit`/`Write` as a real
     "violation" if that SAME `run_id`'s own tool-call history (within the same `tools.jsonl`
     window) also includes at least one `parity_index.py` invocation — i.e. an agent editing the
     YAML source AND separately touching the derived read-only index/db in the same run is the
     actual dangerous pattern this metric exists to catch, not a normal parity-ledger edit alone.
   - Confirm this rescoped definition still correctly flags the 4
     `TCK-20260731-PARITY-INDEX-EPIC` child runs the metric was originally built and validated
     against (per `TCK-20260803-RETRO-TOOL-SAFETY-AUDIT`'s own re-verification: those 4 runs
     showed `parity_ledger_yaml_write_count = 0` under the CURRENT unscoped logic already, since
     none of them touched the yaml directly — confirm the rescoped logic doesn't change that
     result, since it's the known-correct baseline).
2. **Plan**: design the exact code change to `_is_parity_ledger_yaml_write()`/
   `compute_tool_safety_metrics()`, and whether the report's own heading/copy needs updating to
   describe the narrower, now-accurate semantics (e.g. "Parity YAML edits made in the same run as
   a `parity_index.py` invocation" rather than "write violations").
3. **Implement**: apply the rescope; re-run `--all` against the real corpus and confirm the
   count drops to a number that genuinely reflects only runs where both conditions co-occur (very
   likely 0 or near-0, matching the original ticket's own intent).
4. Update `tests/tools/test_generate_retro.py`'s existing 3 parity-write-safety tests (Step 2 of
   the original ticket) to match the new, narrower semantics — do not just widen tolerances, since
   the whole point is the check should mean something different now.

## Out of Scope
- Any change to `_is_unsafe_parity_build_call()` — that check is already correctly narrow (flags
  `parity_index.py build` invocations missing a `--db-path` override or pointing at the real repo
  path) and was NOT the source of this week's or the original ticket's own false-signal finding.
- Backfilling/reinterpreting historical retro reports already committed to
  `agent-monitoring/retro/` — those reflect the metric's behavior at the time they were generated
  and are historical record, not live numbers to correct retroactively.
- Re-litigating `TCK-20260803-RETRO-TOOL-SAFETY-AUDIT`'s own already-closed AC5 narrowing decision
  — that ticket is done; this one implements the fix it explicitly deferred.

## Acceptance Criteria
- [ ] `investigation.md` confirms the exact rescope logic and that it preserves the known-correct
      4-run baseline result
- [ ] `_is_parity_ledger_yaml_write()` (or a new function) rescoped to require co-occurring
      `parity_index.py` tool usage in the same run
- [ ] Report heading/copy updated to accurately describe the narrower check if the label itself
      stays potentially misleading otherwise
- [ ] `tests/tools/test_generate_retro.py`'s parity-write-safety tests updated to the new semantics
- [ ] Real-corpus re-verification: `python3 tools/agent-monitoring/generate_retro.py --all`
      (output not committed, per the original ticket's own precedent) shows a count that no longer
      includes ordinary parity-updater edits from unrelated tickets
- [ ] Scoped pytest run passes

## Related Tickets
- TCK-20260803-RETRO-TOOL-SAFETY-AUDIT (built the metric, found this exact gap, explicitly
  deferred the fix to a future ticket — DONE)
- TCK-20260731-PARITY-INDEX-EPIC (built `parity_index.py`'s read-only tooling this metric is
  meant to protect — the 4 child runs are this ticket's own regression baseline)

## Related Docs
- `docs/guides/agent_monitoring.md` (Tool Safety Audit section)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260803-RETRO-TOOL-SAFETY-AUDIT/investigation.md` (the original
  discovery, Step 8 real-corpus verification)

## Related Code Areas
- `tools/agent-monitoring/generate_retro.py` (`_is_parity_ledger_yaml_write`,
  `compute_tool_safety_metrics`)
- `tests/tools/test_generate_retro.py`

## Assumptions / Open Questions
- Whether "same run" should mean strictly the same `run_id`, or something narrower (e.g. within
  the same `(run_id, seq)` phase pair) — not assumed; Investigate should confirm against what
  granularity actually distinguishes a genuinely risky sequence (YAML edit immediately followed by
  a real-path index build within one agent's own turn) from two unrelated events that merely share
  a `run_id`.

## Implementation Notes
Subagent spawn cap (200/200) reached before this ticket started — Investigate/Plan/Implement/Verify
performed directly, disclosed as with the prior ticket; all real gate scripts run for real.

Added `_is_parity_index_build_call()` as the shared "did this Bash call invoke parity_index.py's
build path" precondition, refactoring `_is_unsafe_parity_build_call` to reuse it. Rescoped
`parity_yaml_writes` in `compute_tool_safety_metrics` to require the yaml-write row's `run_id` to
also appear in `run_ids_with_build_calls` (any row anywhere in that same run satisfying
`_is_parity_index_build_call`).

Initial design considered a broad `"parity_index.py" in input_summary` co-occurrence signal, but a
real-corpus check found this would still incorrectly flag 2 runs (`TCK-20260803-RETRO-TOOL-SAFETY-AUDIT`,
whose only mentions are inside grep PATTERN TEXT searching for the filename; `TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION`,
a harmless `--help` call) — corrected to require the `build` subcommand specifically, matching
`_is_unsafe_parity_build_call`'s own existing narrower precondition. Real-corpus re-verification
(`generate_retro.py --all`, output not committed) confirms `parity_ledger_yaml_write_count == 0`
corpus-wide (121 run_ids have a yaml write, 0 overlap with the 1 run_id that has a real build call)
— the false-signal population drops to 0 without discarding any genuine risk case, since none
currently exists in the corpus.

## Test Summary
`tests/tools/test_generate_retro.py` — 100 passed (was 99 before; renamed 1 existing test to match
new semantics + added 3 new tests: lone-edit-no-longer-counts, different-run-ids-not-flagged,
help-call-does-not-count; updated 1 rendered-text assertion to the new heading copy).

## Files Changed
- `tools/agent-monitoring/generate_retro.py` (`_is_parity_index_build_call` new helper,
  `_is_unsafe_parity_build_call` refactored to reuse it, `compute_tool_safety_metrics` rescoped,
  docstring + rendered heading updated)
- `tests/tools/test_generate_retro.py` (1 test renamed/repurposed, 3 new tests, 1 rendered-text
  assertion updated)
- `docs/guides/agent_monitoring.md` (Tool Safety Audit row updated to describe new semantics)

## Completion Summary
Confirmed `TCK-20260803-RETRO-TOOL-SAFETY-AUDIT`'s own deferred finding was still real (14 fresh
"violations" this week, 100% ordinary parity-updater edits) and implemented the rescope it
explicitly left for a future ticket. The known-correct `TCK-20260731-PARITY-INDEX-EPIC` 4-run
baseline is preserved by construction (rescoped condition is a strict superset restriction of the
old one — anything that was already 0 stays 0). Caught and corrected my own initial over-broad
co-occurrence signal via a real-corpus check before finalizing, rather than assuming the naive
substring match was safe.
