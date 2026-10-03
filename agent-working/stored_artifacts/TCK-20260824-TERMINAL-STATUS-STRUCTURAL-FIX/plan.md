# Plan — TCK-20260824-TERMINAL-STATUS-STRUCTURAL-FIX

## Step 1 — `terminal_status_extractor.py`: add a content-based marker

- Add `_MESSAGE_CONTEXT_RE = re.compile(r"message:\s*'([^']*)'")` and `_CONTEXT_WINDOW_CHARS = 400`
  (a bounded lookahead, not full-file scan — keeps the search local to the call site).
- In `extract_literal_statuses()`: for each `_LITERAL_STATUS_RE` match, search
  `text[match.end():match.end() + _CONTEXT_WINDOW_CHARS]` with `_MESSAGE_CONTEXT_RE`; if found, set
  `context = m.group(1)`, else `context = None`. Add `context` to each entry's dict (now
  `{value, kind, line, context}`).
- In `extract_all_terminal_statuses()`: for literal entries, alongside the existing
  `bucket["call_sites"].append(entry["line"])`, add `bucket.setdefault("contexts",
  []).append(entry["context"])`. Bypass/verdict-derived buckets get `"contexts": []` alongside
  their existing `"call_sites": []`, mirroring the existing empty-list precedent exactly.
- Update the module/function docstrings to describe the new field and its purpose (distinctness
  marker, not a replacement for line-based provenance).

## Step 2 — Update the two hardcoded assertions

`test_terminal_status_extractor.py:101` and `test_terminal_status_conformance.py:69`: replace
`assert ...["call_sites"] == [1546, 1558]` with:

```python
finalize_incomplete_sites = by_value["FINALIZE_INCOMPLETE"]["call_sites"]
assert len(finalize_incomplete_sites) == 2, (
    f"expected exactly 2 distinct FINALIZE_INCOMPLETE call sites, found "
    f"{len(finalize_incomplete_sites)}: {finalize_incomplete_sites}"
)
assert finalize_incomplete_sites == sorted(finalize_incomplete_sites), (
    "call sites must be in strictly ascending source order"
)
assert len(set(finalize_incomplete_sites)) == 2, "call sites must be distinct, not duplicated"

finalize_incomplete_contexts = by_value["FINALIZE_INCOMPLETE"]["contexts"]
assert len(finalize_incomplete_contexts) == 2
assert all(c is not None for c in finalize_incomplete_contexts), (
    f"expected a message-literal context marker at both call sites, got "
    f"{finalize_incomplete_contexts}"
)
assert len(set(finalize_incomplete_contexts)) == 2, (
    f"the two FINALIZE_INCOMPLETE call sites must be genuinely distinct code paths (different "
    f"message text), not an accidental duplicate of the same branch: {finalize_incomplete_contexts}"
)
```

(`test_terminal_status_conformance.py` uses `live_finalize_incomplete` as its variable name instead
of `by_value["FINALIZE_INCOMPLETE"]` — same assertions, adapted to that file's existing local
variable.)

## Step 3 — New line-drift-tolerance test

Add `test_call_site_detection_tolerates_unrelated_line_insertion_above` to
`test_terminal_status_extractor.py`: write two small synthetic `.js` fixtures to `tmp_path` — one
mirroring the real two-call-site shape verbatim (message literals included), one identical but with
N extra blank/comment lines inserted above both call sites — and assert `extract_all_terminal_statuses()`
finds the same structural invariants (2 distinct ascending call sites, 2 distinct non-None contexts)
against both, proving the fix's assertions don't depend on absolute position.

## Step 4 — Repo-wide regression guard

Already confirmed via investigation (`grep -rln "implement-ticket.js" tests/ | xargs grep -lE "==
*\[[0-9]+"` finds only these same two files) — no additional file needs changing for this AC. Note
this finding in Implementation Notes rather than adding a new enforcement test, since the ticket's
own AC only asks to "confirm," not to build a new standing repo-wide gate (that would be a genuinely
separate, larger ticket if wanted later).

## Step 5 — Verify & Finalize

- Re-verify current live line numbers didn't drift again between Investigate and Implement (a real
  risk given this file's history) via a final `grep -n` before running tests.
- Run `pytest tests/agent_orchestration_claude_adapter tests/agent_orchestration -m "not slow and
  not extra_slow"`.
- No parity ledger entry: this is test-only + a docstring/marker addition to a Claude-agent-tooling
  extractor, no `src/` behavior changed, matching the existing `support_boundary` precedent other
  pure-workflow-tooling entries in `infrastructure.yaml` already use (e.g. INFRA-381's own
  "Claude-agent-workflow orchestration tooling only" framing) — but confirm during Parity phase
  whether the repo's own P0-safeguard scan agrees before skipping.
- Move ticket to `tickets/done/`, append `working_log.csv`, leave the shared `agent-monitoring-followups/`
  batch folder in place (2 sibling tickets still open in a separate worktree).
