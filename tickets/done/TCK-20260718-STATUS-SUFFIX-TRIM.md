---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-STATUS-SUFFIX-TRIM
phase: done
date: 2026-07-18
tags: [data-quality, observability]
---

# TCK-20260718-STATUS-SUFFIX-TRIM

## Title
Trim descriptive suffixes off `## Status: DONE` in 10 tickets/done/*.md files fragmenting the Agent Ops Dashboard's Status filter

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
10 files in `tickets/done/` have a body `## Status` section that reads `DONE` followed by extra
descriptive prose (a parenthetical or an em-dash-separated clause), e.g. `DONE (EPIC_SCOPED)`,
`DONE — CLOSED, WRONG PREMISE`, `DONE (all child tickets complete: E41F, E41G, E41H)`. The Status
value is semantically `done` in every case — this is not the OPEN/INPROGRESS staleness defect
class that `TCK-20260718-STATUS-DRIFT-REPAIR` already repaired. The problem is that
`tools/generate_registry.py`'s `parse_body_section(body, 'Status')` (also used by
`src/api/agent_ops_dashboard/ingest.py`'s `parse_ticket_file()` to derive `TicketSummary.workflow_status`)
captures the ENTIRE text up to the next `## ` heading, not just the first token, so each of these
10 files produces its own distinct non-canonical value. Confirmed live: the Agent Ops Dashboard's
Tickets view Status filter dropdown lists `DONE (EPIC_SCOPED)`, `DONE — DUPLICATE / CREATED IN ERROR`,
etc. as separate selectable options alongside plain `DONE`, fragmenting what should be one filter
value. Per explicit user decision, the fix normalizes the ticket data (trims `## Status` to plain
`DONE` and relocates the descriptive context into `## Completion Summary`), not the dashboard's
parser or `parse_body_section` itself.

## Scope
- Trim the `## Status` body section in the 10 named `tickets/done/*.md` files (see Related Code
  Areas) down to the single token `DONE`, with no trailing parenthetical or em-dash clause.
- For the 9 standard-12-section-format files (all except `TCK-20260408-PH3-STG1-HOUSEHOLD.md`),
  reword the trimmed-out context naturally into a sentence in the file's existing
  `## Completion Summary` section — do not paste the raw parenthetical/clause verbatim. Some of
  these files' `## Completion Summary` sections are currently empty (`TCK-20260628-E-PARTY-LOOP`,
  `TCK-20260628-E-PERSONALITY-CALIBRATION`) and need fresh content; others already have relevant
  prose (e.g. `TCK-20260619-E62-CULTURE-DRIFT`, `TCK-20260619-E63-FEATURE-PACKS`,
  `TCK-20260628-E-WORLD-EVOLUTION`, `TCK-20260701-SIMQ-EMIT-CAMP`,
  `TCK-20260701-SIMQ-KERNEL-WIRE`) that the trimmed context should be merged into idiomatically
  rather than duplicated.
- For `TCK-20260408-PH3-STG1-HOUSEHOLD.md` — a pre-12-section legacy-format ticket whose body ends
  at `## Status` with no `## Completion Summary` (or any other post-Status) section at all — decide
  and apply the minimal handling that preserves the "SUPERSEDED by
  TCK-20260408-PH3-PASS1-LIVED-MODELS" information without forcing the full 12-section format onto
  a file this project already treats as out-of-scope for restructuring (see Assumptions).
- Investigate whether `tools/gate_checks/status_drift_check.py`'s `TICKET_STATUS_RE` /
  `check_ticket_status_drift()` should be extended to also catch "first-token-is-DONE-but-trailing-
  prose-follows" as a distinct regression class, so this defect cannot silently recur. Make and
  record an explicit go/defer decision (see Assumptions and predecessor precedent for the
  equivalent call on the 6 colon-suffixed files).
- If the decision is "extend now": implement the check change, update
  `docs/parity_ledger/infrastructure.yaml` `INFRA-277` (or add a new entry) to reflect the widened
  check, and add/adjust coverage in `tests/tools/test_status_drift_check.py`. If "defer": record the
  recommendation for a future, separately-scoped ticket and make no code change to
  `status_drift_check.py` in this ticket — mirroring the predecessor's own precedent for its 6
  excluded colon-suffixed files.
- Verify post-fix (via `tools/generate_registry.py`'s `parse_body_section` extraction path, not by
  touching the dashboard) that all 10 files now resolve to the single canonical `workflow_status`
  value `DONE`.

## Out of Scope
- The 6 same-line colon-suffixed `## Status: X` files already identified and explicitly excluded by
  `TCK-20260718-STATUS-DRIFT-REPAIR`'s "Colon-Suffixed Files Decision" (`TCK-20260322-BWS_PROTO.md`,
  `TCK-20260401-FINAL-CONVERGENCE.md`, `TCK-20260401-FINAL-NON-PARTIAL-TASKS.md`,
  `TCK-20260403-FINAL-CONVERGENCE.md`, `TCK-20260405-SKILL-SCALING.md`,
  `TCK-20260407-PH0-FIX.md`) — disjoint set, not this ticket's concern.
- Any `tickets/done/*.md` file whose `## Status` is a genuinely wrong terminal value
  (OPEN/INPROGRESS left stale) — that defect class is already closed by
  `TCK-20260718-STATUS-DRIFT-REPAIR`. This ticket only touches files where the token is already
  `DONE`.
- Any `tickets/done/*.md` file not in this ticket's frozen 10-file list, even if it superficially
  resembles this defect class — re-verify against the frozen list only, do not re-scan and expand
  scope mid-implementation.
- Modifying `src/api/agent_ops_dashboard/ingest.py`, any file under `dashboard-frontend/`, or
  `tools/generate_registry.py`'s `parse_body_section()` — the approved fix approach is data
  normalization only; the parser's "capture everything to the next heading" behavior is
  intentionally left unchanged.
- The duplicated `## Tier\n## Tier` heading glitch the predecessor's plan noted as
  opportunistic-only in `TCK-20260628-E-NARRATIVE-CONSEQUENCE.md` / `TCK-20260628-E-WORLD-EVOLUTION.md`
  — not required by this ticket; do not seek it out.
- Restructuring `TCK-20260408-PH3-STG1-HOUSEHOLD.md`, or any other legacy/old-format ticket, up to
  the full current 12-section format — fix only what this ticket's scope requires.
- Actually implementing the `status_drift_check.py` regex extension, unless the go/defer
  investigation in Scope concludes "extend now" — if deferred, the code change itself is out of
  scope for this ticket.

## Acceptance Criteria
- All 10 named files' `## Status` body section reads exactly `DONE` (the regex
  `^## Status\s*\n+\s*DONE\s*\n` matches immediately followed by the next `## ` heading or EOF, with
  no other non-whitespace text in between).
- None of the 10 files' descriptive context is silently dropped: for the 9 standard-format files it
  is present in reworded (non-verbatim-pasted) form inside `## Completion Summary`; for
  `TCK-20260408-PH3-STG1-HOUSEHOLD.md` it is preserved per whatever minimal handling this ticket's
  implementation records.
- `tools/generate_registry.py`'s `parse_body_section(body, 'Status')` (or equivalent extraction used
  by `src/api/agent_ops_dashboard/ingest.py::parse_ticket_file`), run against each of the 10 files
  post-fix, returns exactly `"DONE"`.
- `python3 tools/gate_checks/status_drift_check.py` continues to report `PASS` for
  `check_ticket_status_drift` post-fix (no regression against the existing 71/12/83 baseline
  semantics).
- `git diff --stat tickets/done/` shows exactly the 10 named files changed — no unrelated
  `tickets/done/*.md` file touched, and no frontmatter field of any of the 10 files modified.
- The go/defer decision on extending `status_drift_check.py` is explicitly recorded (in
  Implementation Notes once implemented) with reasoning, regardless of which way it goes.
- If "extend now" is chosen: `pytest tests/tools/test_status_drift_check.py` passes with new/updated
  coverage for the extended check, and `docs/parity_ledger/infrastructure.yaml` `INFRA-277` reflects
  the change.

## Related Tickets
- `TCK-20260718-STATUS-DRIFT-REPAIR` (done) — predecessor / same defect family (`## Status` drift in
  `tickets/done/*.md`), but a different defect class: that ticket fixed genuinely-wrong terminal
  values (OPEN/INPROGRESS) and lowercase `runs.jsonl` `final_status` casing, and built
  `tools/gate_checks/status_drift_check.py`, whose `TICKET_STATUS_RE` captures only the first
  `\S+` token — so it does not flag any of this ticket's 10 files (their first token is already
  `DONE`). This ticket reuses that predecessor's file-structure/legacy-handling precedent and its
  own go/defer decision pattern (see the 6 colon-suffixed files).

## Related Docs
- `docs/observability/agent_ops_dashboard_contract.md` — documents `TicketSummary.workflow_status`
  as "the ticket body's `## Status` section, nullable — two distinct fields, never conflated" (vs.
  frontmatter `status`); confirms the dashboard's filter dropdown sources directly from this raw
  extracted text.
- `docs/agent-monitoring/schema.md` — "Historical Corrections" subsection documents the
  predecessor's one-time `runs.jsonl` data correction precedent; useful shape reference if this
  ticket's implementation needs to add its own historical-correction note, though this ticket's
  changes are to `tickets/done/*.md` files, not `agent-monitoring/*.jsonl`.
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-277` documents `status_drift_check.py`'s current
  scope and its own stated "byte-identical regex, do not widen" constraint; relevant if the
  go/defer decision in Scope is "extend now."

## Related Stored Artifacts
- `stored_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/investigation.md`,
  `stored_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/plan.md` (see "Colon-Suffixed Files Decision"
  section — direct precedent for this ticket's own go/defer scoping call),
  `stored_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/test_plan.md`,
  `stored_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/scripts/derive_status_drift_scope.py` (one-off
  scan script; useful pattern reference for re-verifying the frozen 10-file list, not for reuse
  as-is since its regex is intentionally narrower than what this ticket's files need).

## Related Code Areas
- `tickets/done/TCK-20260408-PH3-STG1-HOUSEHOLD.md`
- `tickets/done/TCK-20260619-E12-BALANCE-BASELINE.md`
- `tickets/done/TCK-20260619-E62-CULTURE-DRIFT.md`
- `tickets/done/TCK-20260619-E63-FEATURE-PACKS.md`
- `tickets/done/TCK-20260628-E-NARRATIVE-CONSEQUENCE.md`
- `tickets/done/TCK-20260628-E-PARTY-LOOP.md`
- `tickets/done/TCK-20260628-E-PERSONALITY-CALIBRATION.md`
- `tickets/done/TCK-20260628-E-WORLD-EVOLUTION.md`
- `tickets/done/TCK-20260701-SIMQ-EMIT-CAMP.md`
- `tickets/done/TCK-20260701-SIMQ-KERNEL-WIRE.md`
- `tools/gate_checks/status_drift_check.py` (scoping call only — see Scope/Out of Scope)
- `tests/tools/test_status_drift_check.py` (only touched if go/defer decision is "extend now")
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-277`; only touched if "extend now")

## Assumptions / Open Questions
- **Layer choice**: `layer: observability` was chosen to match the predecessor
  (`TCK-20260718-STATUS-DRIFT-REPAIR`, same defect family, same dashboard/data-quality surface).
  `tools/validate_frontmatter.py`'s `LAYER_VALUES` does contain a `"ticket"` value, which is
  arguably a closer literal fit since this ticket only edits ticket-body content — but a repo-wide
  search found zero existing tickets using `layer: ticket` (unused/unprecedented value), whereas
  `observability` has direct precedent for this exact defect family. If a future ticket establishes
  real precedent for `layer: ticket`, this choice should be revisited — it does not block this
  ticket's scope either way.
- **Legacy file handling for `TCK-20260408-PH3-STG1-HOUSEHOLD.md`**: confirmed via
  `grep '^## '` that this file's body ends immediately after `## Status` — no
  `## Completion Summary` or any of the other 7 standard-format trailing sections exist. Per this
  project's established "legacy data scope" precedent (don't force new-format structure onto
  genuinely old-format files), the recommended default is to append a minimal
  `## Completion Summary` section containing only the reworded superseded-by note — the smallest
  structural addition that avoids losing the "SUPERSEDED by TCK-20260408-PH3-PASS1-LIVED-MODELS"
  information, without adding the other 6 unused standard sections. This is a recommendation, not a
  final decision — Implement phase should confirm or reconsider it against the file's actual
  content once drafting the specific wording.
- **status_drift_check.py extension**: this ticket does not pre-decide go vs. defer. If wrong (e.g.
  a reviewer decides mid-implementation that extending the check is clearly out of this ticket's
  size budget), the Scope item degrades gracefully to "investigate + record recommendation only" —
  it does not invalidate the rest of the ticket's scope (the 10-file data fix stands independently).
- **No overlap with the predecessor's 6 excluded colon-suffixed files**: verified — the two file
  sets are entirely disjoint (different filenames, different Status format: same-line
  `## Status: X` vs. this ticket's two-line `## Status\nDONE (...)`). Recorded here so a future
  reader doesn't need to re-derive this.
- **Tags**: `data-quality` and `observability` were reused as-is from the predecessor's tag set
  (both already registered in `docs/guidelines/tag_registry.jsonl`). The predecessor's third tag,
  `agent-monitoring`, was deliberately dropped here — this ticket's changed artifacts are
  `tickets/done/*.md` files, not `agent-monitoring/*.jsonl`, so that tag would be a weaker fit.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260718-STATUS-SUFFIX-TRIM/plan.md` Steps 2-13.
No deviations from the plan occurred — all 10 files' pre-edit text matched the plan's and
investigation.md's captured snapshots verbatim (Step 1 re-confirmation), so every edit was applied
as pre-drafted.

**Edits applied (Steps 2-11):**
- `TCK-20260408-PH3-STG1-HOUSEHOLD.md` — trimmed `## Status` to `DONE`; appended a new, minimal
  `## Completion Summary` section (the file's only post-Status section addition) with one sentence
  preserving the superseded-by note. No other standard-format section added; frontmatter (`layer:
  misc`) left untouched.
- `TCK-20260619-E12-BALANCE-BASELINE.md` — trimmed `## Status` to `DONE`; appended a closing
  sentence to the existing Completion Summary.
- `TCK-20260619-E62-CULTURE-DRIFT.md` — trimmed `## Status` to `DONE`; appended one closing sentence
  after the existing staging-artifact-migration line.
- `TCK-20260619-E63-FEATURE-PACKS.md` — trimmed `## Status` to `DONE`; appended one closing sentence
  after the existing test-count line.
- `TCK-20260628-E-NARRATIVE-CONSEQUENCE.md` — trimmed `## Status` to `DONE`; appended a reworded
  sentence naming the 3 child tickets after the existing parity-ledger sentence.
- `TCK-20260628-E-PARTY-LOOP.md` — trimmed `## Status` to `DONE`; filled the previously-empty
  `## Completion Summary` with one sentence naming the 3 child tickets, stating only the literal
  trimmed content (no claim about BLOCKED-gate resolution, per Anti-Drift Notes).
- `TCK-20260628-E-PERSONALITY-CALIBRATION.md` — trimmed `## Status` to `DONE`; filled the
  previously-empty `## Completion Summary` with one sentence naming the 3 child-ticket components,
  same BLOCKED-gate caution applied.
- `TCK-20260628-E-WORLD-EVOLUTION.md` — trimmed `## Status` to `DONE`; appended a reworded sentence
  naming the 3 child tickets after the existing parity-ledger sentence. Confirmed the `## Tier\n##
  Tier` duplicate-heading glitch is not present — not touched, per Out of Scope.
- `TCK-20260701-SIMQ-EMIT-CAMP.md` — trimmed `## Status` to `DONE` only; Completion Summary left
  byte-identical (existing "Closed — premise incorrect" opening line already captures the trimmed
  tail; adding a sentence would have duplicated it).
- `TCK-20260701-SIMQ-KERNEL-WIRE.md` — trimmed `## Status` to `DONE` only; Completion Summary left
  byte-identical (existing "created in error" / "Closing as duplicate" lines already capture the
  trimmed tail).

**status_drift_check.py extend-vs-defer decision: DEFER.** Adopted the plan's resolved decision
as final, no override. No change made to `tools/gate_checks/status_drift_check.py`,
`tests/tools/test_status_drift_check.py`, or `docs/parity_ledger/infrastructure.yaml` (`INFRA-277`)
in this ticket. Reasoning (mirrors the predecessor `TCK-20260718-STATUS-DRIFT-REPAIR`'s own
"Colon-Suffixed Files Decision" almost exactly):
1. This ticket's ACs are anchored to a fixed, frozen 10-file list established at ticket-creation
   time. Extending the checker's detection logic inside this same ticket risks surfacing a
   different live count if any other `tickets/done/*.md` file shares this trailing-prose shape but
   was never part of the frozen list — that re-scan is explicitly out of scope.
2. `test_regex_matches_baseline_scan_pattern` pins `TICKET_STATUS_RE.pattern` to
   `r"^## Status\s*\n+\s*(\S+)"` byte-for-byte. Widening `check_ticket_status_drift`'s matching
   logic to also inspect tail text past the first token is a real, non-trivial design decision (new
   regex vs. new coexisting check function vs. changing the pinned assertion) — not a small tweak
   belonging in a data-normalization ticket.
3. Two structurally distinct checker gaps now exist (same-line colon-suffixed drift from the
   predecessor; trailing-prose-after-DONE from this ticket). A future ticket scoping both gaps
   together is likely to produce a cleaner design than two independently-bolted-on special cases
   added across two separate tickets.
4. This ticket's 10-file data fix is fully self-contained and independently valuable — it fixes the
   dashboard facet fragmentation today without depending on the checker extension. Recommendation
   is recorded here for a future, separately-scoped ticket to pick up; no such ticket is created by
   this one.

**Final verification (Step 13) — all 7 checks passed:**
1. `tools/generate_registry.py`'s `parse_body_section(body, 'Status')` returns exactly `"DONE"` for
   all 10 files.
2. Regex `^## Status\s*\n+\s*DONE\s*\n` matches all 10 files (next content is the next `## ` heading
   or EOF).
3. `python3 tools/gate_checks/status_drift_check.py` reports `PASS` for both
   `check_ticket_status_drift` and `check_runs_jsonl_final_status_drift` (exit 0).
4. `git diff --stat -- tickets/done/` shows exactly the 10 named files, no others.
5. Per-file diff hunks all start at line ≥15 (well past each file's frontmatter block, which ends
   around line 9-10) — no frontmatter field touched on any of the 10 files.
6. `pytest tests/tools/test_status_drift_check.py tests/tools/test_validate_frontmatter.py
   tests/tools/test_generate_registry.py -v` — 146 passed, 0 failed.
7. `grep -rn "workflow_status" tests/` found only an unrelated `None`-value assertion and a code
   comment in `tests/tools/test_agent_ops_dashboard_ingest.py` — no test asserts any of the 10 old
   fragmented `workflow_status` strings as a fixture expectation; no test file changed.

## Test Summary
No new tests added — this is a pure ticket-corpus markdown data fix with no code change. Existing
test coverage re-run and confirmed unaffected: `pytest tests/tools/test_status_drift_check.py
tests/tools/test_validate_frontmatter.py tests/tools/test_generate_registry.py -v` → 146 passed.
`python3 tools/gate_checks/status_drift_check.py` → PASS (both checks). Verification also included a
direct `parse_body_section` extraction re-run against all 10 files (see Implementation Notes) —
this is the acceptance-criteria-mandated verification path, not a pytest-based one, since the fix is
data-only.

## Files Changed
- `tickets/done/TCK-20260408-PH3-STG1-HOUSEHOLD.md`
- `tickets/done/TCK-20260619-E12-BALANCE-BASELINE.md`
- `tickets/done/TCK-20260619-E62-CULTURE-DRIFT.md`
- `tickets/done/TCK-20260619-E63-FEATURE-PACKS.md`
- `tickets/done/TCK-20260628-E-NARRATIVE-CONSEQUENCE.md`
- `tickets/done/TCK-20260628-E-PARTY-LOOP.md`
- `tickets/done/TCK-20260628-E-PERSONALITY-CALIBRATION.md`
- `tickets/done/TCK-20260628-E-WORLD-EVOLUTION.md`
- `tickets/done/TCK-20260701-SIMQ-EMIT-CAMP.md`
- `tickets/done/TCK-20260701-SIMQ-KERNEL-WIRE.md`

## Completion Summary
All 10 frozen `tickets/done/*.md` files' `## Status` body sections are trimmed to the bare token
`DONE`, eliminating the 10 distinct fragmented values the Agent Ops Dashboard's Tickets-view Status
filter dropdown previously listed alongside plain `DONE`. Every trimmed descriptive tail was
preserved: for the 9 standard-format files it was merged or appended as reworded (never
verbatim-pasted) prose into `## Completion Summary` (2 of these — `E-PARTY-LOOP`,
`E-PERSONALITY-CALIBRATION` — had empty Completion Summary sections and were filled fresh; 2 —
`SIMQ-EMIT-CAMP`, `SIMQ-KERNEL-WIRE` — needed no addition since existing prose already captured the
trimmed content); the one legacy-format file (`PH3-STG1-HOUSEHOLD`) got a single new minimal
`## Completion Summary` section, not full 12-section restructuring. The go/defer decision on
extending `tools/gate_checks/status_drift_check.py` was resolved as DEFER (reasoning in
Implementation Notes) — no code change to the checker, its tests, or `INFRA-277` in this ticket.
Post-fix verification confirms `parse_body_section(body, 'Status')` returns exactly `"DONE"` for all
10 files, `status_drift_check.py` still reports PASS, `git diff --stat tickets/done/` shows exactly
these 10 files with no frontmatter touched, and the scoped pytest suite (146 tests) passes unchanged.
