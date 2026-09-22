---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260922-TOOL-CALL-COUNT-MISMATCH-RATCHET-REPORT-ONLY
phase: done
date: 2026-09-22
tags: [agent-monitoring, data-quality, testing]
---

# TCK-20260922-TOOL-CALL-COUNT-MISMATCH-RATCHET-REPORT-ONLY

## Title
`tool_call_count_mismatch_check.py`'s ratchet ceiling went 49 → 50 → 53 in two days, each time on
a fully-diagnosed hand-orchestration-sidecar incident — remove the blocking gate, keep the
measurement, matching the precedent already set for `sidecar_attribution_coverage_check.py`

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
User-approved 2026-09-22. `tools/gate_checks/tool_call_count_mismatch_check.py`'s
`MISMATCH_CEILING` moved twice in two days — 49 → 50
(`TCK-20260921-HAND-ORCHESTRATION-SIDECAR-STALENESS-INCIDENT`) → 53
(`TCK-20260922-HAND-ORCHESTRATION-SIDECAR-POST-SNAPSHOT-ACCUMULATION-INCIDENT`) — each raise the
product of a real, fully-diagnosed incident, not an unexplained drift. Both incidents share the
same root-cause class: the count tracks *how hand-orchestrated work happens to attribute its own
tool calls* (a `.claude/current_run` sidecar either carried over stale, or left live after its own
snapshot), not a defect in the underlying data. This is the exact working-style-vs-defect
conflation `TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-UNMEETABLE` already diagnosed and
resolved for the sibling `sidecar_attribution_coverage_check.py` check, by removing that check's
own blocking floor rather than re-pinning it further — per that ticket's own governing principle:
agent-monitoring telemetry records *how work happened*, not a simulation property, and does not
warrant a blocking gate over it.

**Context for the ticket's own record**, per the design session's request — the 14-day real-token
retro baseline (`TCK-20260921-REAL-TOKEN-TELEMETRY`), unrelated to this ratchet's own mechanism but
recorded here as the "before" snapshot this batch's cost-awareness work is measured against: 14
days to 2026-09-21, 40,039 API requests, cache-read tokens 19.07B (~78% of cost), average context
481k/request, Bash accounting for 63% of context-attributed tokens (`grep` alone: 5.1k calls, 2.3B
tokens), `search_docs` used only 184 times.

## Scope
- `tools/gate_checks/tool_call_count_mismatch_check.py`: remove `MISMATCH_CEILING` and the FAIL
  path. `check_tool_call_count_mismatches()` always returns `PASS` with the count and the run_ids
  as evidence. Module docstring rewritten to mirror `sidecar_attribution_coverage_check.py`'s own
  precedent shape (gate removed, why, measurement kept, narrower-detector pointer for later).
- `Makefile`'s `tool-call-count-mismatch-check` target help text: "(non-blocking; see module
  docstring)", matching the sidecar precedent's own exact wording.
- `tools/gate_checks/monitoring_anomaly_validator.py`: no code change needed — it aggregates this
  check generically (`FAIL if ANY sub-check FAILs`); once the sub-check can no longer FAIL, the
  aggregate simply never sees one from it. Confirmed by re-running both the CLI (exit 0) and its
  test suite.
- `tests/tools/test_tool_call_count_mismatch_check.py`: delete the four ceiling-shaped tests
  (`test_ceiling_matches_its_own_documented_history`, the two ceiling pass/fail tests,
  `test_real_corpus_is_at_or_below_the_ratchet_ceiling`); keep the `find_*` detection tests,
  `test_fix_date_constant_unchanged`, and the Makefile test; add
  `test_large_mismatch_count_still_returns_non_fail_with_count_in_evidence`.
- `tests/tools/test_monitoring_anomaly_validator.py`: checked for any `MISMATCH_CEILING` import or
  ceiling assumption — none found; no change needed.
- `tools/agent-monitoring/record_hand_orchestrated_closure.py`: updated the one comment describing
  the ratchet as something a mismatch could push "over its ceiling" (a ceiling that no longer
  exists).
- Searched `docs/` and CLAUDE.md-adjacent guide files for `MISMATCH_CEILING`/re-pin guidance — none
  found outside the auto-regenerated `docs/REGISTRY.yaml`.

## Out of Scope
- The three sibling ratchets (`working_log_content_duplicate_check.py`,
  `duplicate_run_record_check.py`, `monitoring_integrity_backlog_check.py`) — not touched. Checked
  their own commit history over the last 14 days per the design session's explicit request: none
  has been re-pinned more than once. `working_log_content_duplicate_check.py`'s
  `DUPLICATE_PAIR_CEILING` and `duplicate_run_record_check.py`'s `IDENTICAL_OUTCOME_CEILING` each
  show exactly one touching commit in that window (their own introduction, `#194`/`#204` — not a
  re-pin of a pre-existing value). `monitoring_integrity_backlog_check.py`'s five ceilings show two
  touching commits (`#204` introduction, `#211` "ratchet-conflation widening") — one genuine
  adjustment, not a repeated chase. None currently shows this ticket's own two-re-pins-in-two-days
  pattern; no follow-up recommended from this ticket, left to the design session's own judgment.
- Any change to the `record_hand_orchestrated_closure.py` mitigations
  (`check_sidecar_matches_ticket()`, `clear_sidecar_if_matches()`) added by the two precedent
  incidents — those stand as real, working mitigations; this ticket only removes the downstream
  gate that kept re-triggering despite them.

## Acceptance Criteria
- [x] `MISMATCH_CEILING` and the FAIL path removed; `check_tool_call_count_mismatches()` always
      returns `PASS`.
- [x] Module docstring rewritten, mirroring the `sidecar_attribution_coverage_check.py` precedent's
      shape (gate removed, why, measurement kept, narrower-detector pointer).
- [x] `Makefile` help text updated to "(non-blocking)".
- [x] `monitoring_anomaly_validator.py` confirmed to no longer be able to exit 1 because of this
      sub-check — verified live (CLI exit 0) and via its own test suite (12 passed).
- [x] Ceiling-shaped tests deleted; detection/FIX_DATE/Makefile tests kept; new large-count
      non-FAIL test added. 8 passed.
- [x] `test_monitoring_anomaly_validator.py` checked for ceiling assumptions — none found.
- [x] `record_hand_orchestrated_closure.py`'s stale-ceiling comment updated.
- [x] `docs/`/CLAUDE.md-adjacent guides checked for stale re-pin guidance — none found outside the
      auto-regenerated registry.
- [x] Sibling-ratchet re-pin frequency reported (see Out of Scope) — none re-pinned more than once.

## Related Tickets
- `TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-UNMEETABLE` (done) — the precedent this ticket
  directly mirrors, for the sibling `sidecar_attribution_coverage_check.py` check.
- `TCK-20260921-HAND-ORCHESTRATION-SIDECAR-STALENESS-INCIDENT` (done) — first ceiling raise, 49→50.
- `TCK-20260922-HAND-ORCHESTRATION-SIDECAR-POST-SNAPSHOT-ACCUMULATION-INCIDENT` (done) — second
  ceiling raise, 50→53, the immediate trigger for this ticket.
- `TCK-20260915-TOOL-CALL-COUNT-MISMATCH` (done) — introduced the check and its original ceiling.
- `TCK-20260921-REAL-TOKEN-TELEMETRY` (done) — source of the 14-day token-retro baseline recorded
  in this ticket's Request Summary.

## Related Docs
- None — no docs/ content changed; `docs/REGISTRY.yaml` regenerates unconditionally at close.

## Related Stored Artifacts
- None — hotfix tier, self-evident intent captured here, matching the precedent's own tier choice.

## Related Code Areas
- `tools/gate_checks/tool_call_count_mismatch_check.py` (`MISMATCH_CEILING` removed,
  `check_tool_call_count_mismatches()` rewritten)
- `tests/tools/test_tool_call_count_mismatch_check.py`
- `Makefile` (`tool-call-count-mismatch-check` help text)
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` (one comment updated)

## Assumptions / Open Questions
None — scope was fully specified by the batch brief and the precedent ticket it mirrors.

## Implementation Notes
Mirrored `tools/gate_checks/sidecar_attribution_coverage_check.py`'s own post-fix shape closely:
same "used to gate, gate removed, do not rebuild it" opening, same "measurement stays, only the
threshold is gone" framing, same "if a real detector is wanted later" closing pointer — scoped this
check's own narrower-detector suggestion to the formal `implement-ticket.js` pipeline population
(never sidecar-dependent), the closest analogue to the sidecar precedent's own "pipeline runs that
opened a run_id whose own tool rows lack one" suggestion.

`monitoring_anomaly_validator.py` needed no code change — its aggregation is already generic
(`FAIL if ANY sub-check FAILs`), so removing the FAIL path at the source was sufficient; confirmed
this rather than assumed it, per the batch brief's own instruction.

## Test Summary
```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest \
  tests/tools/test_tool_call_count_mismatch_check.py \
  tests/tools/test_monitoring_anomaly_validator.py -q
# 20 passed
```
`python3 tools/gate_checks/tool_call_count_mismatch_check.py` run standalone: prints
`MARKER:[{"status": "PASS", "evidence": "53 post-2026-07-19 tool_call_count/tools.jsonl
mismatch(es). Full set: [...]"}]` — reports the same real count, always PASS.
`python3 tools/gate_checks/monitoring_anomaly_validator.py` run standalone against the real
corpus: exit code 0.

## Files Changed
- `tools/gate_checks/tool_call_count_mismatch_check.py` — removed `MISMATCH_CEILING` and the FAIL
  path; rewrote the module docstring; `check_tool_call_count_mismatches()` always PASS.
- `tests/tools/test_tool_call_count_mismatch_check.py` — removed 4 ceiling-shaped tests, added 1
  large-count non-FAIL test.
- `Makefile` — `tool-call-count-mismatch-check` help text now says "(non-blocking; ...)".
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` — one comment updated to not
  reference a ceiling that no longer exists.
- `docs/REGISTRY.yaml` — regenerated unconditionally as part of this closure.

## Completion Summary
Removed the `tool_call_count_mismatch_check.py` blocking gate, mirroring
`TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-UNMEETABLE`'s own already-established resolution
for the sibling `sidecar_attribution_coverage_check.py` check: a ratchet that chases hand-
orchestration working-style volume rather than a stable defect signal cannot converge on any fixed
value, and repeatedly re-pinning it (twice in two days here) is the same anti-pattern that
precedent ticket diagnosed and rejected. The measurement survives for retro/incident-diagnosis use;
only the threshold and its FAIL path are gone. `monitoring_anomaly_validator.py`'s own aggregate
exit behavior confirmed unaffected in the direction that matters (can no longer FAIL because of
this sub-check). Checked the three sibling ratchets' own re-pin history per the design session's
request: none shows this same repeated-re-pin pattern, so no follow-up is recommended from this
ticket.
