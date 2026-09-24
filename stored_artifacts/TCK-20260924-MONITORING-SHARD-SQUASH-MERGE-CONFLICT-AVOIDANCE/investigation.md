---
status: active
layer: observability
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE
date: 2026-09-24
tags: [agent-monitoring, data-quality, process-improvement]
---

# Investigation — TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE

## Confirmed facts (all writer/reader modules read in full before any edit)

- **`tools/agent-monitoring/writer.py`'s `write_line`/`write_lines` already take an arbitrary
  `target_path: Path` parameter** — the per-file locking, stale-lock recovery, and diagnostic
  sidecar are all already path-agnostic. Switching which file gets written is entirely a
  caller-side decision; `writer.py` itself needs zero changes.
- **`tools/agent-monitoring/post_tool_hook.py` already resolves `ticket_id` from the sidecar**
  before it computes `tools_file`'s path — the per-ticket write target is a same-scope, minimal
  edit at the exact point the path is already being built, not a new lookup.
- **`record_run.py`/`record_events.py`'s `record`/`records` already require `run_id`** (`REQUIRED`
  set) — `run_id` is the ticket ID (or a scope-failure fallback ID) throughout this repo's own
  convention, confirmed by every `record_hand_orchestrated_closure.py` invocation this session.
- **Load-bearing consumer found only by reading the file, not by inspection of the ticket's own
  Related Code Areas list**: `record_events.py::compute_tool_stats()` globs
  `agent-monitoring/data/*/tools.jsonl` specifically to compute `tool_call_count`/
  `cost_proxy_score` for the very same run's own events being written in this call. **Switching
  `post_tool_hook.py` to per-ticket files without also widening this glob would silently zero out
  `tool_call_count`/`cost_proxy_score` for every ticket using the new write path** — a real
  regression this investigation caught before it shipped, not a hypothetical.
- **A second, more serious tension found the same way**: `tools/gate_checks/
  done_checker_static.py::check_working_log_exactly_one_row()` reads `tickets/working_log.csv`
  **synchronously, at every ticket's own close** — it is not a periodic/retro-time check like the
  JSONL consumers. Its logic (`_rows_for_ticket`/`_status_for_row`) is deliberately nuanced: it
  distinguishes a legitimate reopen from a real duplicate by inspecting each matching row's own
  status, not just counting rows. Deferring `working_log.csv`'s actual CSV write to retro-cadence
  consolidation (the ticket's own Assumption 2 recommendation) would make this check **fail for
  every ticket closed via the new path**, until the next retro run folds the pending row in —
  directly contradicting AC5 ("done_checker_static.py's working_log_exactly_one_row condition...
  confirmed to still pass identically").

## Decision: scope reduction, disclosed rather than silently dropped

**This ticket implements the per-ticket write path and consolidation for the three
`agent-monitoring/data/*/*.jsonl` files only. It does not change `tickets/working_log.csv`'s write
path.** `append_working_log_row()` is untouched; `record_hand_orchestrated_closure.py` continues
writing directly to the shared CSV exactly as today, and AC3 (working_log.csv's own squash-merge
duplication cannot recur) is **not satisfied by this ticket**.

Reasoning: fixing `working_log.csv` correctly requires either (a) teaching
`check_working_log_exactly_one_row()` to also recognize a pending, not-yet-consolidated per-ticket
row as satisfying "exactly one row" — a real, non-trivial change to a 13-condition gate-checker
function that every ticket closure in this repo depends on, whose existing reopen-vs-duplicate
logic must be preserved exactly — or (b) some other synchronization mechanism not yet designed.
Both are a correctly-scoped ticket of their own, not a rushed addition to this one. Per this
repo's own Gate Integrity rule, applied to scope rather than test results: reporting an honest,
bounded fix for the two-thirds of the problem that's safe to ship now is better than a rushed
attempt at the synchronous-gate third that risks breaking every ticket close in the repo if gotten
wrong. `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP`'s existing detection-only mitigation
(a squash-merge duplicate is caught by `tests/integrity/test_no_duplicate_content_blocks.py` after
the fact, with a documented manual recovery rule) remains the standing mitigation for
`working_log.csv` until a follow-up ticket designs the synchronization fix properly.

## Design decisions for the in-scope JSONL fix

1. **Per-ticket file naming**: `agent-monitoring/data/YYYY-Www/<run_id>.{runs,events,tools}.jsonl`
   (Assumption 1's recommended shape — three files, mirroring today's split, not one combined
   file). `post_tool_hook.py` falls back to the shared `tools.jsonl` when `ticket_id` is null
   (ad-hoc, non-ticket work) — zero change for that case, since two untracked ad-hoc sessions can't
   collide on "which ticket" in the first place.
2. **`compute_tool_stats()`'s glob is widened** to also read `agent-monitoring/data/*/*.tools.jsonl`
   alongside the existing `agent-monitoring/data/*/tools.jsonl` — additive, not a rewrite; both
   patterns are read and merged before grouping by `(run_id, seq)`.
3. **Consolidation is delete-after-fold, not manifest-tracked.** A manifest file recording "which
   per-ticket files have already been consolidated" would itself become a small, non-append-only
   JSON file with its own merge-conflict exposure — reintroducing, at a smaller scale, the exact
   class of problem this ticket exists to remove. Deleting a per-ticket file only after its lines
   are successfully appended to the canonical file is simpler and idempotent by construction:
   nothing is left to reprocess on a second run. **Disclosed residual risk**: a crash between a
   successful canonical write and the delete could cause that one per-ticket file's lines to be
   folded in twice on the next run. This would inflate `tools.jsonl` row counts slightly (already
   an existing, tolerated, advisory-only signal — see the current corpus's own logged tool-count
   mismatches from unrelated causes) or, for `runs.jsonl`/`events.jsonl`, would be caught by the
   *already-existing* `duplicate_run_record_check.py`/`event_seq_integrity_check.py` anomaly
   detectors — a real detector already exists for exactly this failure shape, so it surfaces rather
   than silently corrupts.
4. **No new `.gitattributes` entry is needed.** The existing pattern
   `agent-monitoring/data/*/*.jsonl` already matches `<TCK-ID>.tools.jsonl` (a glob `*` matches any
   characters including `.`), so per-ticket files already inherit `merge=union`/`eol=lf` for the
   real-git-merge case, with zero additional configuration.
5. **Canonical per-week files stay committed** (Assumption 3's recommendation) — no change to
   `.gitignore`; this ticket only changes which file a session writes to, never whether the result
   is tracked.
