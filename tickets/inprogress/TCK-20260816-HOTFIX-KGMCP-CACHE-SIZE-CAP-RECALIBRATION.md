---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION
phase: open
date: 2026-08-16
tags: [ai, mcp, bug]
---

# TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION

## Title
Recalibrate the Level 1 cache's 8KB payload size cap using real measured gateway payload sizes

## Status
INPROGRESS

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §5 set
`MAX_PAYLOAD_BYTES = 8192` at Phase 0 ratification time (`docs/plans/knowledge-gateway-mcp-proposal.md`
§24 item 1, "cache bounded... payloads"), before any real gateway existed and with no real payload
data to derive the number from. `TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON`'s honest real-corpus
measurement found this cap rejects **every** real gateway response as `oversized_payload`: the 7
frozen corpus entries' real response payloads range 10,612–30,548 bytes (`gateway_tokens` 2653–7637
via `kgmcp_char_heuristic_v1`), all exceeding the 8192-byte cap by 1.3x–3.7x. The Level 1
provider-result cache is therefore structurally inert for real usage today — the redaction/size-cap
machinery itself works exactly as designed (real, tested, correctly gated), but the numeric
threshold was never calibrated against real data.

Per explicit user decision, this is fixed now, before Phase 3 (which builds Level 2 — assembled
multi-provider packets, likely comparable-or-larger in size) is scoped, so Phase 3 inherits a
working Level 1 foundation and real payload data rather than repeating the identical miscalibration
at a higher layer.

## Scope
- Recalibrate `MAX_PAYLOAD_BYTES` in `tools/knowledge_gateway_redaction.py` using the real observed
  payload-size data from `tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json`
  (and any other real measurement available) — not an arbitrary guess. The new value must
  comfortably exceed the real observed maximum with reasonable headroom for organic corpus growth,
  while still being a genuine, meaningful bound (not simply "large enough to never reject anything,"
  which would make §5's own "bounded" framing meaningless).
- Update `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §5's documented
  value and rationale to reflect the real, data-derived number — replacing the "consistent with the
  'bounded/redacted' framing" placeholder rationale with the real derivation.
- Re-run `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py` (or an equivalent real
  measurement) after the fix to confirm genuine cache hits now actually occur for the real corpus —
  this hotfix is not complete until verified against real, live behavior, not just a raised
  constant.
- Update `tests/tools/test_knowledge_gateway_redaction.py`'s existing size-cap tests
  (`TestSizeCap`) to reflect the new real value where they assert the literal `MAX_PAYLOAD_BYTES`
  constant.

## Out of Scope
- Redesigning what gets cached (e.g. shrinking the response envelope, excluding low-value fields,
  compressing content) — that is Phase 3's own explicit "Enforce caller budgets using measured
  output size" deliverable, not this hotfix's job. This hotfix only recalibrates the existing cap's
  numeric value against real data.
- Any change to the redaction/allowlist/secret-scan/never-cache logic — only §5's size cap is in
  scope.
- Any change to `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, or the cache read/write orchestration in
  `tools/knowledge_gateway_cache.py`/`tools/retrieval_cache.py` — this is a pure constant/doc fix.
- Scoping or building Phase 3 itself — that follows this hotfix as separate work.

## Acceptance Criteria
- [x] `MAX_PAYLOAD_BYTES` is recalibrated to a real, data-derived value that comfortably covers the
      observed real corpus's maximum payload size, with documented headroom rationale.
- [x] `redaction_retention_policy.md` §5's rationale is updated to cite the real derivation, not the
      original placeholder framing.
- [x] Re-running the Phase 2 recomparison runner against the real corpus after the fix shows a
      genuine improvement in cache-hit rate (ideally 7/7, honestly reported whatever the real result
      is — not assumed). **Real result: 7/7**, measured against a genuinely cold cache state (see
      Implementation Notes).
- [x] `TestSizeCap` tests updated to the new real constant value; no test weakened to hide a
      still-failing cap.

## Related Tickets
- TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON (DONE; the honest measurement that found this defect)
- TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH (DONE; originally implemented `MAX_PAYLOAD_BYTES` per
  the then-unmeasured Phase 0 placeholder value)
- TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE2-EPIC (DONE; closed with this finding explicitly
  recorded and deferred to a separate later ticket — this is that ticket)

## Related Docs
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §5
- `docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md` (the real
  measurement this hotfix responds to)

## Related Stored Artifacts
None (hotfix — no staging artifacts).

## Related Code Areas
- `tools/knowledge_gateway_redaction.py` (`MAX_PAYLOAD_BYTES`, `check_size_cap()`)
- `tests/tools/test_knowledge_gateway_redaction.py` (`TestSizeCap`)

## Assumptions / Open Questions
- The exact new numeric value is not decided here — Implement must derive it from the real
  measured data cited above, not pick an arbitrary round number without justification.

## Implementation Notes

**1. Real data derivation.** Read `tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json`
directly (not the ticket's own summary numbers) and extracted each of the 7 corpus entries' real
cold `gateway_tokens` (`kgmcp_char_heuristic_v1(json.dumps(response_cold))`, i.e.
`ceil(len(text.encode("utf-8"))/4)` per `tools/knowledge_gateway_packet_assembly.py:81-87`):
Q1=2653, Q2=4993, Q3=2851, Q4=2739, Q5=4939, Q6=2822, Q7=7637. Cross-checked against
`docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md`'s own committed
"implied bytes (≈ tokens×4)" table, which gives the same real observed range:
**~10,612–30,548 bytes**, real max = Q7_negative_knowledge at **~30,548 bytes**. Note: this is the
size of the full `json.dumps(response)` payload the token heuristic measures, not the exact
post-redaction byte count `check_size_cap()` itself gates on (redaction only shrinks, never grows,
so the real gate-relevant size is <= this), so this range is a safe, real, non-underestimating basis
for the new cap.

**2. New value: `MAX_PAYLOAD_BYTES = 65536` (64 KiB).** Derivation: 65536 / 30548 ≈ **2.15x** the
real observed maximum — comfortably covers organic corpus/response growth (more providers, larger
evidence sets) without collapsing back to "always rejects" on the next reasonably-sized entry, while
rounding to the nearest clean power of two (2^16) keeps the bound itself simple/inspectable and
still genuinely meaningful: a payload an order of magnitude past today's real max (e.g. a runaway or
malformed response) is still rejected outright, not silently accepted. This is not "large enough to
never reject anything" — it's the smallest clean power-of-two multiple that clears the real max with
reasonable margin, per the ticket's own guidance (1.5x-2x rounded to a clean value).

**3-4. Code + doc updates.** `tools/knowledge_gateway_redaction.py`: `MAX_PAYLOAD_BYTES` changed
8192 -> 65536, its inline comment and `check_size_cap()`'s docstring updated to cite the new value
and `redaction_retention_policy.md:121` (the §5 section's line moved because of the new rationale
prose added). `redaction_retention_policy.md` §5 rewritten: kept "reject not truncate" behavior
unchanged, replaced the old "consistent with the 'bounded/redacted' framing... proposed policy"
placeholder with a "Recalibration history" paragraph citing the real observed range, the real old
cap's 7/7 rejection finding, the new value, and the 2.15x/power-of-two headroom reasoning.

**5. Test updates (`tests/tools/test_knowledge_gateway_redaction.py`).** Read `TestSizeCap` and the
one other test outside that class hardcoding a cap-relative literal
(`test_secret_scan_match_short_circuits_before_size_cap_or_redaction_store`) before touching
anything, per the task's explicit instruction not to blind find-and-replace:
- `test_payload_exactly_at_cap_is_accepted`: `"a" * 8192` -> `"a" * kgr.MAX_PAYLOAD_BYTES`.
- `test_payload_over_cap_is_rejected_not_truncated`: `"a" * 8193` -> `"a" * (kgr.MAX_PAYLOAD_BYTES + 1)`
  (both the `check_size_cap` call and the `evaluate_write_candidate` call).
- `test_secret_scan_match_short_circuits_before_size_cap_or_redaction_store` (outside `TestSizeCap`,
  found by grepping for hardcoded byte literals near cap assertions, not part of the class the
  ticket named but genuinely broken by the constant change): `("x" * 9000)` -> hardcoded 9000 no
  longer exceeded 65536, breaking the test's own `len(...) > kgr.MAX_PAYLOAD_BYTES` precondition;
  changed to `("x" * (kgr.MAX_PAYLOAD_BYTES + 1))` so it tracks the constant automatically.
- `test_size_cap_measured_on_redacted_not_raw_payload`: the raw fixture string's repeat count (300)
  no longer produced a raw payload exceeding the new 65536-byte cap (16,200 bytes at 300 reps);
  raised to 1300 reps (70,200 raw bytes > cap; redacted collapses to ~16,900 bytes, still comfortably
  under cap) so the test's own "raw exceeds cap, redacted does not" premise still holds. Verified via
  a standalone Python check before editing, not guessed.
- `test_payload_under_cap_is_accepted` (`"a" * 8000`) was left unchanged: 8000 is still genuinely
  under the new 65536-byte cap, it was never a literal `8192`, and the task's own instruction limited
  required edits to tests hardcoding the literal old constant.

**6. Live re-verification (real, honest result: 7/7 genuine cache hits).** `run_corpus()` in
`tools/agent-monitoring/kgmcp_phase2_gateway_runner.py` (not `main()`, which would have overwritten
the frozen `tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json` — explicitly
forbidden by this ticket) was called directly from a throwaway driver script in scratchpad, against
the real live gateway, real live providers, and the real local (gitignored, untracked,
`knowledge-index/retrieval_cache.db`) cache DB.
  - First pass (cache DB already had leftover rows from earlier exploratory runs during this same
    session): `cache_write_rejection_reason` was `None` for all 7 (confirming the size-cap defect
    itself is fixed — no more `oversized_payload`), but `genuine_cache_hit_count` still read **0/7**.
    Investigated rather than assumed away, per this ticket's own Gate Integrity instruction. Root
    cause (confirmed via `_run_single_entry` instrumentation): the runner's own DD2 dual-signal
    hit-detector requires the *cold* call to be a genuine MISS (1 provider round trip) so the total
    `assemble_packet` call count across cold+warm equals 1 on a genuine warm hit. Because earlier
    exploratory runs in this same session had already written real rows for these exact 7 queries,
    the *cold* call in this particular pass was itself already served from cache (0 round trips), so
    the round-trip-count signal read 0 (implying MISS) while the independent SQL `hit_count` delta
    signal correctly read `+1` (implying HIT) — the two signals disagreed, and DD2's own
    conservative rule reports MISS whenever they disagree. This is a real measurement-methodology
    artifact of re-running the (intentionally non-cache-clearing, per its own docstring) runner
    against an already-warmed cache, not a defect in this hotfix's fix.
  - To get a valid, honest measurement matching the runner's own documented one-clean-run design
    (`tools/agent-monitoring/kgmcp_phase2_gateway_runner.py`'s docstring: "Run once, by hand...";
    "this runner does not pre-clear the cache DB"), the local `knowledge-index/retrieval_cache.db`
    Level 1 table (`retrieval_provider_result_cache_rows`) was cleared (`DELETE FROM ...`) — this
    file is gitignored, untracked, ephemeral local dev-machine state (confirmed via
    `git check-ignore -v knowledge-index/retrieval_cache.db`), not a committed artifact of any kind,
    so this is legitimate environment hygiene restoring the runner's own documented precondition, not
    an edit to any tracked file, test, or fixture.
  - Re-ran `run_corpus()` once against this genuinely cold cache. **Real result:
    `genuine_cache_hit_count: {"count": 7, "of": 7}`.** All 7 entries: `cache_status_warm == "HIT"`,
    `cache_write_rejection_reason == None`, cold `gateway_tokens` matching the original fixture's
    recorded values almost exactly (2653/4997/2851/2739/4918/2822/7637 vs. the frozen fixture's
    2653/4993/2851/2739/4939/2822/7637 — the two providers' real output has minor run-to-run
    variation, same as the frozen fixture's own §4.2 warm-vs-cold note already documents).
  - Honestly reported, not cherry-picked: the other three §4 threshold categories (§4.1 latency,
    §4.2 token-reduction cold+warm, §4.3 recall) all remained **FAIL, 0/7** in this same clean run —
    exactly as expected, since none of them are size-cap-related and none are in this hotfix's scope
    (Out of Scope explicitly excludes "redesigning what gets cached" / response-size reduction,
    which is what §4.2 would require, and §4.3's recall gap is the pre-existing `doc_id`-vs-
    `source_path` structural issue documented elsewhere). Only the cache-hit mechanism this hotfix
    targets is claimed fixed.

**7. Scoped regression suite: 107 passed, 1 known/explained failure.** Ran
`tests/tools/test_knowledge_gateway_redaction.py`, `tests/docs/test_redaction_retention_policy_doc.py`,
`tests/tools/test_knowledge_gateway_cache.py`, `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`
together (108 tests total). 107 pass. The 1 failure —
`tests/tools/test_kgmcp_phase2_baseline_recomparison.py::test_no_frozen_kgmcp_dependency_edited` —
was read in full before concluding anything, per the task's explicit "confirm this by reading it,
don't assume" instruction, and the task's own prediction ("this last one's own tests should NOT need
to change") turned out to be wrong for this one test; reported honestly rather than silently patched.
Root cause: that test is a scope guard written by the completed sibling ticket
`TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON` to assert *that ticket's own* implementation never
touched a list of "frozen" files, including `tools/knowledge_gateway_redaction.py`. Its mechanism is
a live `git diff --stat HEAD` check, not a check scoped to that historical ticket's own commit
range — so it does not distinguish "the now-completed, merged sibling ticket touched this file" from
"any ticket, ever, touches this file while this test exists unmodified." This hotfix's Scope and
Related Code Areas explicitly, deliberately name `tools/knowledge_gateway_redaction.py` as the file
to edit (`MAX_PAYLOAD_BYTES`) — that edit is required, not optional, and is the entire point of this
ticket. Per this repo's Gate Integrity hard rule ("Never edit an artifact to make an automated
gate/check pass instead of fixing the underlying substance... stop and report it truthfully, even if
it looks trivially resolvable"), this guard test's banned-path list was **not** edited to remove
`tools/knowledge_gateway_redaction.py` — doing so would be routing around the gate rather than
reporting it. This is flagged here, honestly and explicitly, as a known, explained, unresolved test
failure for Test/Parity/Verify to adjudicate (likely resolution: a small follow-up either narrows
that guard test's scope now that its own ticket is closed, or the guard is accepted as permanently
retired once its purpose — protecting a specific historical ticket's own diff — has been served).
No other regression was found; all other 107 tests, including every other `TestSizeCap` test and
every other Phase 2 recomparison structural/honesty guard, pass unchanged.

## Test Summary
`pytest tests/tools/test_knowledge_gateway_redaction.py tests/docs/test_redaction_retention_policy_doc.py tests/tools/test_knowledge_gateway_cache.py tests/tools/test_kgmcp_phase2_baseline_recomparison.py`
-> **107 passed, 1 failed** (see Implementation Notes §7 for the single, known, explained failure —
a stale scope-guard from a completed sibling ticket, not a regression caused by this hotfix's actual
logic).

Live re-verification (not a pytest run; a real, manual, one-time invocation of
`tools/agent-monitoring/kgmcp_phase2_gateway_runner.py::run_corpus()` against the live gateway, per
this ticket's own Scope): **genuine_cache_hit_count 7/7** against a genuinely cold cache state (see
Implementation Notes §6 for the full derivation, including the honestly-reported false-negative 0/7
result from an earlier, cache-polluted pass, before the root cause was found and a valid clean-state
measurement was taken).

## Files Changed
- `tools/knowledge_gateway_redaction.py` — `MAX_PAYLOAD_BYTES` 8192 -> 65536; updated inline
  comment, `check_size_cap()` docstring, and module docstring's "§5 8 KB" reference.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` — §5 rewritten with
  the real, data-derived value and rationale; "reject not truncate" rule unchanged.
- `tests/tools/test_knowledge_gateway_redaction.py` — `TestSizeCap`'s two boundary tests and one
  other cap-relative test outside that class updated to the new constant (see Implementation Notes
  §5 for exact diffs and why each one needed to change).
- `tickets/inprogress/TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION.md` — this file
  (Implementation Notes, Test Summary, Files Changed, Completion Summary, Acceptance Criteria).

Not changed (deliberately, per this ticket's own Scope/Out of Scope and the "never edit a sibling
ticket's historical measurement doc" precedent): `docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md`,
`tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json`,
`docs/parity_ledger/infrastructure.yaml` (left for this hotfix's own Parity phase, per the hotfix
pipeline's Scope -> Implement -> Test -> Parity -> Verify -> Finalize ordering),
`tools/agent-monitoring/kgmcp_phase2_gateway_runner.py` (its docstring's "8192-byte" mention is a
historical description of a prior real measurement, not a live assertion — no test breaks on it).

## Completion Summary
Recalibrated the Level 1 provider-result cache's write-path size cap from the never-measured
Phase-0-placeholder `8192` bytes to a real, data-derived `65536` bytes (~2.15x the real observed
7-entry-corpus maximum of ~30,548 bytes, rounded to the nearest clean power of two), updated
`redaction_retention_policy.md` §5's rationale to cite that real derivation, updated the affected
`TestSizeCap`-and-related unit tests to track the new constant, and re-verified against the real
live gateway (not assumed): the cache's genuine-hit rate went from the historically-measured 0/7 to
a real, confirmed **7/7** once the cache DB was in a genuinely cold state matching the verification
runner's own documented one-clean-run design. One pre-existing, unrelated scope-guard test
(`test_no_frozen_kgmcp_dependency_edited`, written by a different, now-completed sibling ticket) now
fails as a direct, expected, honestly-reported consequence of this hotfix's required edit to
`tools/knowledge_gateway_redaction.py` — left failing and documented rather than silently patched,
per this repo's Gate Integrity rule, for Test/Parity/Verify to adjudicate.
