---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-DOC-COVERAGE-REVERSE-CHECK
artifact_type: plan
tags: [testing, ai, documentation, process-improvement]
---

# Implementation Plan — TCK-20260904-DOC-COVERAGE-REVERSE-CHECK

## Summary

Extend `check_docs_to_update_coverage` (`tools/gate_checks/done_checker_static.py:482-558`)
in-place to also check the reverse direction: a `docs/` path that real `git status` shows touched
during the ticket's diff but that never made it into the resolved `## Files Changed` or
`## Related Docs` body-section text of the ticket file itself. The reverse check reuses
`check_tag_drift`'s (lines 769-809) path-resolution and `_extract_section_text` mechanics, and
`_path_touched`'s (lines 416-426) directory-collapse tolerance, but keeps `PASS`/`FAIL`/`NA`
vocabulary and stays wired into the existing blocking `run_static_precheck` aggregation — it does
**not** adopt `check_tag_drift`'s `CLEAN`/`FLAGGED` advisory contract. The check is tier-agnostic
(no hotfix `NA` branch), scoped to `docs/` paths only, and lands as a same-function extension
rather than a new tuple entry — this keeps the existing `docs_to_update_coverage` condition name,
the function's locked `["ticket_id", "tier", "base_dir"]` signature
(`tests/tools/test_done_checker_static.py:1616-1623`), and `run_static_precheck`'s existing
8-condition tuple shape all unchanged. A second, independent line of work bakes an explicit
self-check instruction into `.claude/agents/doc-updater.md`'s prompt (AC #4, generation-time
defense-in-depth only — not the acceptance bar). Four doc updates follow from the Scope text and
from the three resolved decisions below; `docs/parity_ledger/infrastructure.yaml` is explicitly
excluded from this plan's steps — that edit belongs to the Parity phase's own `parity-updater`
agent, not to Plan/Implement.

## Resolved Decisions

**Decision 1 — Coexist with the JS/awk early-warning check.** The prior check
(`.claude/workflows/implement-ticket.js:903-918`, from
`TCK-20260831-HOTFIX-FILES-CHANGED-DOC-OMISSION-EARLY-WARNING`) runs inside the Document-Update
phase, checks only `## Files Changed` (via `awk`) against `docUpdate.docs_updated`'s own
self-report, and only logs a non-blocking `⚠`. The new check runs at Verify time, checks both
`## Files Changed` and `## Related Docs` against real `git status`, and blocks. These differ in
phase, input source, and blocking behavior — they are not two implementations of the same fix, they
are the same "cheap early self-correction vs. deterministic blocking backstop" split this project
already uses elsewhere (mirrors doc-staleness's own Implement-time gate coexisting with this same
Verify-time function's forward direction). **Do not remove or modify the JS/awk check.**

**Decision 2 — `docs/` paths only, not all touched paths.** Matches the ticket's own Scope-text
wording ("a **docs/ path** touched"), the forward check's existing scope, and the function's own
name. Widening to all touched paths would require exclusion/tolerance rules for test files,
`staging_artifacts/` itself, and `tickets/working_log.csv` that are not designed here — explicitly
out of this ticket's Scope. **Disclosed consequence:** this means the reverse check structurally
cannot catch the `TCK-20260831-ITEM-INSTANCE-HISTORY` incident's actual gap
(`src/core/state.py`, not a `docs/` path — investigation.md, "The 3 named historical incidents"
§3). AC #3 only requires reproducing "at least one" of the three incidents, and the other two
(`RACE-RELATIONS-MATRIX`, `READINESS-SPEED-FORMULA`) are both genuine `docs/` paths, so this is not
a blocking AC gap — Completion Summary must state this limitation explicitly, not imply broader
coverage than what was built (see Anti-Drift Notes).

**Decision 3 — Tier-agnostic; no hotfix `NA` branch.** Follows `check_monitoring_write_recorded`'s
explicit precedent (`tools/gate_checks/done_checker_static.py:737-751`: "Deliberately has no
`tier` parameter and no NA branch") and `check_tag_drift`'s own signature (no `tier` parameter at
all). The forward check's `tier == "hotfix"` → `NA` branch (line 515-516) exists because its
required input, `investigation.md`, structurally does not exist for hotfix tickets — a real
absence, not a policy choice. The reverse check's required inputs — real `git status` and the
ticket's own `## Files Changed`/`## Related Docs` body-section text — exist for every tier per the
Ticket Format (hotfix tickets carry the identical body-section set). There is no structural reason
to `NA` here, and doing so would leave the exact recurring gap this ticket targets unguarded on
the one tier where scrutiny is already lower elsewhere. Consequence: `docs/ai/ticket-lifecycle.md:360`
("Hotfix tier has no equivalent backstop... an accepted, pre-existing gap") becomes stale for the
reverse direction and must be corrected (Step 8).

**Decision 4 — In-place extension of `check_docs_to_update_coverage`, not a new function/tuple
entry.** Keeps the function's signature exactly `["ticket_id", "tier", "base_dir"]`, which
`test_docs_coverage_ignores_behavior_changed_entirely`
(`tests/tools/test_done_checker_static.py:1616-1623`) locks in as a design guard — verified by
reading that test directly; it is a real signature-shape assertion, not a name I am inferring.
Keeps `run_static_precheck`'s existing `docs_to_update_coverage` condition name unchanged
(`test_run_static_precheck_includes_docs_to_update_coverage_condition`, line 1631), so its own
docstring's "Aggregate all 8 Part A checks" (line 589) and `docs/ai/ticket-lifecycle.md`'s
condition-6 backing prose need no renumbering. The alternative (a new tuple entry) would ripple
into `run_static_precheck`'s docstring, the Verify-prompt's "conditions 3, 4, 6, 7, 10, 12" list
(`implement-ticket.js:1444`), and `DONE_SCHEMA`'s checklist shape — none of which this ticket's
Scope asks to touch. In-place extension is the narrower change and is explicitly offered by the
ticket's own Scope wording ("Extend check_docs_to_update_coverage... to additionally check the
reverse direction").

**Unresolved Questions: none.** All four decisions above are resolved with reasoning and cited
evidence; no open question remains that requires human input before Implement begins.

## Steps

### Step 1 — Add reverse-direction logic to `check_docs_to_update_coverage`
**Files:** `tools/gate_checks/done_checker_static.py`

**Change:**
1. Add a new module-level regex, e.g. `_DOCS_PROSE_TOKEN_RE = re.compile(r"docs/[^\s\`]+")`,
   placed near the existing `_DOCS_BULLET_RE` (line 328). **Evidence this is needed, not
   assumed:** the existing `_DOCS_BULLET_RE` (`^-\s+\`(docs/[^\`]+?)(?::\d+)?\``, line 328)
   only matches a line-starting, backtick-wrapped bullet — it cannot be reused as-is for
   `## Files Changed`/`## Related Docs` prose, because those two sections use **two different
   real formats**, confirmed by reading the actual DONE ticket files (not inferred): `##
   Files Changed` entries are backtick-wrapped
   (`tickets/done/TCK-20260831-RACE-RELATIONS-MATRIX.md:210`, `` - `docs/mechanics/02_combat_laws.md`
   — new "Race-hostility escalation..." ``), while `## Related Docs` entries are bare, no backticks
   (`tickets/done/TCK-20260831-READINESS-SPEED-FORMULA.md:56-57`,
   `- docs/mechanics/02_combat_laws.md`). The new regex must match both forms — it intentionally
   drops `_DOCS_BULLET_RE`'s line-start-bullet anchor and backtick requirement, matching any
   `docs/...` token anywhere in the section text up to the next whitespace or backtick.
2. Add a small helper, e.g. `_prose_docs_paths(section_text: str) -> set[str]`, that runs
   `_DOCS_PROSE_TOKEN_RE.findall(section_text)` and strips trailing punctuation (`.,;:)`) from
   each match — mirrors `_parse_docs_to_update`'s own trailing-suffix-stripping precedent (line
   439-445) applied to a different suffix shape.
3. Add a helper, e.g. `_touched_docs_paths_uncovered(touched: set[str], declared: set[str]) ->
   list[str]`, that for every `t` in `touched` filtered to `t.startswith("docs/")`, returns `t` if
   `not any(_path_touched(d, {t}) for d in declared)`. **This reuses `_path_touched`
   (line 416-426) with its arguments in the reverse role** — `d` (a declared path parsed from
   ticket prose, e.g. `docs/newsubsystem/foo.md`) is checked as "covered by" the single-element
   set `{t}` (a real git-touched path, possibly a directory-collapsed entry ending in `/`, e.g.
   `docs/newsubsystem/`). This correctly satisfies the directory-collapse case:
   `_path_touched("docs/newsubsystem/foo.md", {"docs/newsubsystem/"})` returns `True` because
   `"docs/newsubsystem/".endswith("/")` and `"docs/newsubsystem/foo.md".startswith("docs/newsubsystem/")`
   — reusing the exact existing helper rather than reimplementing path matching, per the ticket's
   own Scope instruction ("matching the existing directory-collapse tolerance").
4. Inside `check_docs_to_update_coverage` (lines 482-558), **after** the existing forward-direction
   logic returns something other than an early `FAIL`/`NA` (i.e., after line 546, once
   `required_docs`/`resolved_docs` bookkeeping is done and before the final forward-`PASS`
   evidence is constructed at lines 547-558): remove the `tier == "hotfix"` early-return's
   applicability to the *new* reverse logic specifically — the existing line 515-516 early
   return must be removed entirely and replaced with tier-conditional branching described in (5),
   since per Decision 3 the reverse check must still run under hotfix tier even though the forward
   check's `investigation.md`-dependent logic cannot.
5. Resolve the ticket's own file path the same way `check_tag_drift` does (lines 780-784):
   `tickets/done/{ticket_id}.md`, falling back to `tickets/inprogress/{ticket_id}.md` — do **not**
   extract this into a shared function that `check_tag_drift` itself calls; write it as a small
   new private helper (e.g. `_resolve_ticket_body_path`) so `check_tag_drift`'s own function body
   is not touched at all (Out of Scope: "Silently deciding..."; Anti-Drift: forward-direction
   contract must stay untouched — refactoring a sibling function's internals is a needless risk
   to a passing, mirrored-precedent function for no requirement in this ticket).
6. Read the resolved ticket file (if it exists — if not, this reverse sub-check reports
   `FAIL` with evidence naming the missing ticket file, since a missing ticket file at Verify
   time is itself a real problem, not a silent pass), extract `## Files Changed` and `##
   Related Docs` via the existing `_extract_section_text` (line 102-110), union their
   `_prose_docs_paths(...)` results into `declared`.
7. Compute `touched = _git_touched_paths()` (already computed once for the forward check at line
   547 — reuse that same call/variable, do not call it twice) and restrict to
   `docs/`-prefixed entries per Decision 2.
8. Call `_touched_docs_paths_uncovered(touched_docs, declared)`. If non-empty, the overall function
   returns `FAIL` with evidence naming the specific uncovered path(s) and which two sections were
   checked (mirrors the forward check's own `missing` evidence shape at lines 549-554). This FAIL
   applies **regardless of tier** (Decision 3) and **regardless of whether the forward-direction
   check passed** — a ticket can have perfect forward coverage and still fail the reverse check,
   and vice versa; the function returns the first `FAIL` encountered (forward first, since that
   logic already exists and returns early; reverse checked only once forward has not already
   failed, to keep one `FAIL` evidence string per call, matching this function's existing
   single-tuple-return shape).
9. For `tier == "hotfix"`: skip the *forward* logic exactly as today (still returns early for
   the forward half — `investigation.md` genuinely does not exist), but *always* still run the
   reverse-direction check (6)-(8) before returning. Restructure the function so the hotfix branch
   no longer does a bare early `return ("NA", ...)` — it must fall through to the reverse check and
   return that check's own `PASS`/`FAIL`, not `NA`.
10. **`test_docs_coverage_hotfix_is_na` must be rewritten, not left untouched (NEEDS_CHANGES fix).**
    `test_docs_coverage_hotfix_is_na` (`tests/tools/test_done_checker_static.py:1399-1403`) builds a
    fixture with no ticket file present and asserts `check_docs_to_update_coverage("TCK-FAKE",
    "hotfix", base_dir=base)` returns `status == "NA"` unconditionally. Once (9) removes the bare
    hotfix early-return, this exact fixture no longer hits an `NA` path: with no `tickets/done/` or
    `tickets/inprogress/` file resolvable for `TCK-FAKE` (per (5)/(6)), the reverse sub-check now
    hits its own missing-ticket-file `FAIL` path — the same fixture would assert `FAIL`, not `NA`,
    contradicting the test's current name and assertion. Split this one test into two:
    - **(a) a forward-skip test** (e.g. `test_docs_coverage_hotfix_forward_half_still_skips`):
      confirms the *forward* half still does not require/read `investigation.md` under hotfix tier
      — build the fixture so the *reverse* half is made to `PASS` instead (e.g. mock
      `_git_touched_paths` to return no `docs/`-prefixed entries, or point at a resolvable ticket
      file whose `Files Changed`/`Related Docs` sections already cover every touched `docs/` path),
      then assert the returned evidence contains no `investigation.md`-missing `FAIL` reason —
      isolating "forward genuinely skips" from whatever the reverse half separately decides.
    - **(b) a reverse-runs-under-hotfix test**: confirms the reverse half now actually executes and
      can independently `FAIL` under `tier="hotfix"` — a touched `docs/` path absent from the
      ticket's sections, called with `tier="hotfix"`, must return `FAIL` (not `NA`). This may be
      satisfied by `test_reverse_docs_coverage_hotfix_tier_behavior` (already listed in this step's
      Verify list) *only if* that test explicitly exercises `tier="hotfix"` and a `FAIL`-producing
      case, not merely a `PASS` case — if it only covers `PASS`, add a distinct `FAIL`-under-hotfix
      test rather than assume coverage.
    The original `test_docs_coverage_hotfix_is_na` name/assertion (bare, unconditional `NA` for
    hotfix) must not survive after this step — it directly asserts the pre-Decision-3 behavior this
    plan intentionally changes.

**Do NOT touch:** `_parse_docs_to_update`, `_parse_resolved_not_applicable_docs`,
`_is_none_section`, `_DOCS_BULLET_RE`, `_DOCS_NONE_PHRASES`, `_DOCS_NONE_PREFIX_RE` — the entire
forward-direction bullet-format contract (Out of Scope, explicit). Do not touch `check_tag_drift`
(lines 769-809) or its `CLEAN`/`FLAGGED` vocabulary — do not import or reuse that vocabulary
anywhere in this function. Do not change the function's parameter list/signature.

**Verify:**
- `test_reverse_docs_coverage_fails_when_touched_doc_not_in_files_changed_or_related_docs`
- `test_reverse_docs_coverage_passes_when_touched_doc_appears_in_files_changed`
- `test_reverse_docs_coverage_passes_when_touched_doc_appears_in_related_docs_only`
- `test_reverse_docs_coverage_directory_collapse_tolerance`
- `test_reverse_docs_coverage_ITEM_INSTANCE_HISTORY_style_non_docs_path_is_out_of_scope`
- `test_reverse_docs_coverage_hotfix_tier_behavior` (asserts the tier-agnostic behavior positively,
  per Decision 3 — not merely absence of a crash)
- All existing `test_docs_coverage_*` tests (lines 1399-1623) unmodified and still passing,
  **except** `test_docs_coverage_hotfix_is_na` (lines 1399-1403), which per Change item 10 above
  must be **rewritten** (not left as-is) into:
  - `test_docs_coverage_hotfix_forward_half_still_skips` (new name; confirms no
    `investigation.md`-missing `FAIL` reason under hotfix tier, with the reverse half made to
    `PASS` by fixture construction)
  - `test_reverse_docs_coverage_hotfix_tier_behavior` (listed above) extended/confirmed to cover a
    `FAIL`-producing case under `tier="hotfix"` specifically, not only `PASS`
- `test_docs_coverage_ignores_behavior_changed_entirely` (signature lock) unmodified and passing

### Step 2 — Historical-incident regression fixture
**Files:** `tests/tools/test_done_checker_static.py`

**Change:** Add `test_reverse_docs_coverage_reproduces_RACE_RELATIONS_MATRIX_incident`. Build a
fixture ticket body (written to `tmp_path`, following the existing `monkeypatch`/fixture pattern
used by `test_docs_coverage_all_flagged_paths_touched_passes` etc., lines 1490-1526) whose `##
Files Changed`/`## Related Docs` sections **omit** `docs/mechanics/02_combat_laws.md` — reconstructing
the ticket's state *before* the real hand-patch (the real, current
`tickets/done/TCK-20260831-RACE-RELATIONS-MATRIX.md:210` line is the post-patch state and must not
be read/copied verbatim as the fixture; the fixture is a deliberately-incomplete reconstruction).
Mock `_git_touched_paths` (via `monkeypatch`, mirroring existing tests) to report
`docs/mechanics/02_combat_laws.md` as touched. Assert the function returns `FAIL` — proving the new
check would have caught this real incident before the hand-patch, satisfying AC #3.

**Do NOT touch:** the real `tickets/done/TCK-20260831-RACE-RELATIONS-MATRIX.md` file itself — it
is historical record, not a fixture input to edit.

**Verify:** the new test itself (this step's whole purpose); confirms AC #3.

**Depends on:** Step 1 (the reverse-check logic must exist to exercise).

### Step 3 — `run_static_precheck` wiring confirmation
**Files:** `tests/tools/test_done_checker_static.py`

**Change:** Add `test_run_static_precheck_wires_reverse_check_blocking`. Since Decision 4 keeps
this an in-place extension, `run_static_precheck` (lines 588-606) needs **no code change** — it
already calls `check_docs_to_update_coverage(ticket_id, tier)` and folds the returned
`(status, evidence)` into the `"docs_to_update_coverage"` entry (line 600). This test scaffolds a
repo (mirroring `_scaffold_precheck_repo`, line 597) where the reverse check specifically would
`FAIL` (a touched `docs/` path absent from both sections) and asserts
`run_static_precheck(...)`'s `docs_to_update_coverage` entry shows `status == "FAIL"` — proving the
reverse-check `FAIL` surfaces through the existing aggregation rather than being silently absorbed
into a `PASS` from the (still-passing) forward half.

**Do NOT touch:** `run_static_precheck`'s tuple structure, condition names, or ordering (lines
593-602) — per Decision 4, this step is verification-only, not a wiring code change.

**Verify:** the new test; also re-confirms `test_run_static_precheck_includes_docs_to_update_coverage_condition`
(line 1631) still passes unmodified.

**Depends on:** Step 1.

### Step 4 — Update Verify-prompt static text describing the check's meaning
**Files:** `.claude/workflows/implement-ticket.js`

**Change:** Lines 1446-1447 currently read: "condition 6, 'Docs updated', is now backed by the
script's docs_to_update_coverage check, added by TCK-20260802-DOC-COVERAGE-CHECK — it
independently re-verifies Investigate's flagged docs were touched, regardless of what
behavior_changed was self-reported at Implement time". This describes only the forward direction
and is now incomplete post-extension. Reword to additionally state that the same check also
independently re-verifies the reverse direction — that every `docs/` path git shows touched is
itself reflected back into the ticket's own `Files Changed`/`Related Docs` text — citing this
ticket's ID for the extension, mirroring how the existing sentence already cites
`TCK-20260802-DOC-COVERAGE-CHECK` for the forward half.

**Do NOT touch:** the "Tier-specific N/A rules" text at lines 1440-1442 (Condition 4/staging
artifacts hotfix N/A — unrelated to this check), the "conditions 3, 4, 6, 7, 10, 12" list at line
1444 (Decision 4 keeps this unchanged — no new condition number), or the JS/awk early-warning
block (lines 903-918, Decision 1 — coexist, do not modify).

**Verify:** `test_verify_prompt_mentions_reverse_check_or_updated_condition_language` (new,
mirrors `test_verify_prompt_cites_condition_6_alongside_static_conditions`'s pattern, line 1649).
Also re-confirms `test_verify_prompt_cites_condition_6_alongside_static_conditions` and
`test_verify_prompt_condition_6_precedes_static_precheck_invocation` still pass unmodified (the
"conditions 3, 4, 6, 7, 10, 12" line itself is not edited).

**Depends on:** Step 1 (the prompt text must describe the actual finished behavior).

### Step 5 — Add self-check instruction to `doc-updater.md`
**Files:** `.claude/agents/doc-updater.md`

**Change:** Add an explicit self-check instruction, most naturally as a new final numbered item
under "## What to Do" (currently 5 items, lines 61-67) or a short new subsection immediately
before "## Output" (line 69): before returning, cross-reference the actual `docs_updated` paths
this turn touched against what will land in the ticket's own `Files Changed`/`Related Docs`
sections, and flag any mismatch in the same turn (via the existing `blocker` field, already
defined in Output, line 76, rather than inventing a new output field). This satisfies AC #4
("agent-interpreted, matching this file's existing test-surface limitation" — the ticket's own
wording; this file has no runtime prompt-execution test harness, only static text presence can be
asserted).

**Do NOT touch:** "## Per-Family Rules" (lines 28-59), specifically the existing
`docs/parity_ledger/*.yaml`-out-of-scope carve-out (line 30-31) — the new self-check instruction
is about doc-updater's own *reporting* discipline for docs it already legitimately touches, not
about narrowing or widening what doc-updater is allowed to edit. Do not relitigate the
`parity_ledger/`/`archive/`/`scenarios/`/`entity/`/`audits/` exclusions.

**Verify:** `test_doc_updater_prompt_includes_self_check_instruction` (new; static text-presence
assertion against `.claude/agents/doc-updater.md`'s raw content, mirroring
`test_document_update_phase_appears_in_workflows_md_table`'s file-read-and-assert pattern per test
plan item 10). Also re-confirms `test_document_update_runs_unconditionally_no_hotfix_guard`
(`tests/tools/test_document_update_phase_wiring.py`) still passes — this edit must not introduce
any hotfix-conditional guard into the Document-Update phase itself.

**Depends on:** none (independent of Step 1's code change — this is a prompt-text-only addition).

### Step 6 — Reword `docs/architecture/doc_updater_agent.md`'s "Error handling" section, and
correct `docs/ai/workflows.md`'s stale Document-Update-row phrasing
**Files:** `docs/architecture/doc_updater_agent.md`, `docs/ai/workflows.md`

**Change:**

**(A) `docs/architecture/doc_updater_agent.md` lines 142-148** state today: "The Verify-time gate
(`check_docs_to_update_coverage`) stays **fully decoupled** from doc-updater's own output — it
continues re-deriving ground truth from `investigation.md` + real `git status` only, exactly as it
does today... No new coupling is added." Reword precisely to state that a reverse-direction check
now also exists within the same function (per Decision 4), while preserving the load-bearing
meaning this section exists to state: ground truth for **both** directions is still derived from
`investigation.md`/the ticket's own body-section text plus real `git status` — **never** from
doc-updater's own `docs_updated` self-report. The "never trust the self-report" principle is
genuinely unchanged; only the fact that a second (reverse) direction now exists needs stating. Do
not claim "no new coupling is added" verbatim any longer — a coupling (ticket-body-text-vs-git-status)
now exists that did not before, even though it still excludes doc-updater's self-report
specifically.

**(B) `docs/architecture/doc_updater_agent.md` lines 162-169** (read verbatim, not inferred —
current text): "**Hotfix tier has no equivalent backstop.** `check_docs_to_update_coverage`
returns `NA` for hotfix tier unconditionally (no `investigation.md` exists to check against) —
this is existing, unchanged behavior, not something this design introduces. It means case 1 above
has no safety net on hotfix tickets: if doc-updater misjudges that a hotfix's docs don't need
updating, nothing in the pipeline catches it. This is an accepted, pre-existing gap (the same gap
exists today for the generalist implementer's own hotfix-tier doc edits — this design does not
make it worse), not a new risk introduced by adding doc-updater. Any future ticket that wants a
hotfix-tier doc coverage backstop is a separately-scoped decision, not implied here." This is a
**different paragraph** than (A) above (a different section concern: the *hotfix-tier* gap, not
the *decoupling* principle) and makes the same class of now-false claim Decision 3 falsifies. It
must be corrected precisely, without overclaiming: the *forward* half genuinely still returns no
usable signal for hotfix (`investigation.md` still doesn't exist — unchanged), so case 1 (doc-updater
wrongly judges a doc doesn't need touching, and so never touches it — git then shows nothing
touched at all) still has **no** safety net on hotfix tickets; that slice of the gap is genuinely
unchanged and stays accepted. But the *reverse* half (this ticket) now runs unconditionally,
including hotfix tier: if doc-updater (or the generalist implementer) does touch a `docs/` file
during a hotfix ticket but that touch never lands in the ticket's own `Files Changed`/`Related
Docs` text, the reverse check now catches that specific failure mode tier-agnostically. Reword to
state both halves precisely — the broader omission-never-touched case remains an open, accepted
gap on hotfix tier; the narrower touched-but-undeclared case is now closed on hotfix tier too. Do
not claim the full "no equivalent backstop" framing survives, and do not claim the gap is fully
closed either — state the actual split.

**(C) `docs/ai/workflows.md` line 88** (read verbatim, not inferred — current text, inside the
Document-Update row of the phase table): "...a doc-updater blocker is reported via a `failed`-status
event but does not stop the pipeline — Verify's `check_docs_to_update_coverage` remains the actual
backstop for standard/epic tier". The trailing "for standard/epic tier" now overclaims an
exclusion that only applies to the *forward* half. Reword this clause (staying inside the same
table cell, introducing no `|` characters that would break the table) to state that
`check_docs_to_update_coverage` remains the actual backstop overall, with its forward-direction
half standard/epic-tier only (needs `investigation.md`) and its reverse-direction half (added by
this ticket, `TCK-20260904-DOC-COVERAGE-REVERSE-CHECK`) now running tier-agnostically, including
hotfix. This is a **narrow, single-cell edit** — it does not add a new table row and does not
touch any other phase's row or `docs/ai/system_overview.md`, consistent with the Scope Guards'
"no new phase/agent, no new row" reasoning (see revised Scope Guards entry below, which now
permits this one existing-cell correction).

**Do NOT touch:** the rest of `docs/architecture/doc_updater_agent.md`'s "Output contract" section
(lines just above 142) or any other section describing doc-updater's own scope/Per-Family rules —
(A) and (B) are limited to the "Error handling" section's two stale passages. In
`docs/ai/workflows.md`, do not touch any other phase's table row, the table's column structure, or
`docs/ai/system_overview.md` — (C) is limited to the one clause in the Document-Update row's
existing cell.

**Verify:** no automated test exists for either doc's prose (`docs/ai/system_overview.md` remains
excluded per the Scope Guards below — no new phase/agent is added there, so no wiring-table test
applies to it; `docs/ai/workflows.md` gets a narrow existing-cell edit here, not a new row, so no
new wiring-table test is needed for it either). Verified by human/Verify-phase review that: the
"Error handling" reword (A) preserves the "never trust self-report" principle statement; the
hotfix-gap reword (B) states the accepted-vs-closed split accurately (does not overclaim full
closure, does not leave the false "no equivalent backstop" framing); and the `workflows.md` reword
(C) accurately reflects that only the forward half remains standard/epic-tier-only.

**Depends on:** Step 1 (must describe the actually-implemented behavior) and Step 5 (references
doc-updater's own self-check addition contextually, though does not require Step 5's exact
wording).

### Step 7 — Update `guardrail_enforcement_epic.md`'s M2 acceptance-signal note
**Files:** `docs/plans/agent_infrastructure/ai_first_hardening_epics/guardrail_enforcement_epic.md`

**Change:** Lines 143-151 ("## Acceptance signal for this epic") currently list M2 as an open
acceptance bar: "`check_docs_to_update_coverage` (or its replacement) is confirmed as the primary
control... verified against at least one of the three real historical tickets". Once Steps 1-2
land and the historical-incident regression test passes, add a note marking M2 satisfied —
mirroring this same doc's own existing "M1 is superseded — do not implement, already done"
precedent (lines 23-41): name which ticket closed it (this ticket), which historical incident was
reproduced (Step 2's choice — `RACE-RELATIONS-MATRIX`), and that the prompt self-check (Step 5)
exists as defense-in-depth but is not itself the acceptance bar (already stated in the existing
text, lines 150-151 — do not contradict it).

**Do NOT touch:** the M1 section (lines 9-25, already superseded/closed by a different ticket) or
the M3 acceptance-signal text (background-hang guard — unrelated to this ticket).

**Verify:** no automated test (plan-doc prose); Verify-phase/human review that the M2 note
accurately reflects what Steps 1-2 actually built (docs/-only scope, one incident reproduced, per
Decision 2's disclosed limitation — do not imply the check also covers the `ITEM-INSTANCE-HISTORY`
`src/`-path case).

**Depends on:** Steps 1 and 2 (must describe the actually-finished, actually-tested state).

### Step 8 — Correct `docs/ai/ticket-lifecycle.md`'s hotfix-backstop-gap passage
**Files:** `docs/ai/ticket-lifecycle.md`

**Change:** Line 360 states: "Hotfix tier has no equivalent backstop
(`check_docs_to_update_coverage` returns `NA` unconditionally for hotfix) — an accepted,
pre-existing gap, not something this phase introduces." Per Decision 3 (tier-agnostic, no hotfix
`NA` for the reverse direction), this passage is now stale for the reverse direction specifically
and must be corrected: state that the *forward* direction still returns `NA` for hotfix (genuinely
unchanged — `investigation.md` still does not exist for hotfix tickets) but the *reverse*
direction now runs identically under hotfix tier and provides the backstop this passage previously
said did not exist. Do not claim the forward-direction gap is closed — only the reverse-direction
gap is closed by this ticket.

**Do NOT touch:** the surrounding paragraph's description of Document-Update's own phase-level
gate behavior (lines 355-359, describing `docs_updated` merging and the doc-staleness gate) — this
step is limited to the one sentence describing the hotfix backstop gap.

**Verify:** no automated test (doc prose); Verify-phase/human review that the correction is
accurate and does not overstate what changed (forward direction is unaffected).

**Depends on:** Step 1 (Decision 3's actual implemented behavior must match what this passage now
claims).

## Scope Guards

Explicit list of things this plan must not touch, derived from the ticket's Out of Scope section
and the investigation's Anti-Drift Hazards:

- `_parse_docs_to_update`, `_parse_resolved_not_applicable_docs`, `_is_none_section`,
  `_DOCS_BULLET_RE`, `_DOCS_NONE_PHRASES`, `_DOCS_NONE_PREFIX_RE` — the forward-direction
  bullet-format contract (`tools/gate_checks/done_checker_static.py:328-479`). Explicitly Out of
  Scope; hardened by two prior tickets against real false positives.
- `check_tag_drift` (lines 769-809) and its `CLEAN`/`FLAGGED` vocabulary — mechanics (path
  resolution, `_extract_section_text`) are reused; the status contract is not.
- `docs/parity_ledger/infrastructure.yaml` — this is Parity phase's (`parity-updater`'s)
  exclusive territory per `doc-updater.md`'s own Per-Family Rules (line 30-31); no step in this
  plan edits it. It is listed in investigation.md's Docs Requiring Update purely for completeness
  of what the parity-updater agent will do automatically in its own later phase — not a
  Plan/Implement action item.
- `run_static_precheck`'s tuple structure, condition names/ordering, and docstring's "8 Part A
  checks" count (lines 588-606) — Decision 4 keeps this unchanged.
- `check_docs_to_update_coverage`'s parameter signature — must remain exactly `["ticket_id",
  "tier", "base_dir"]` (locked by `test_docs_coverage_ignores_behavior_changed_entirely`).
- The JS/awk early-warning check (`implement-ticket.js:903-918`) — Decision 1, coexist, no
  removal or modification.
- `doc-updater.md`'s Per-Family Rules boundaries (`docs/parity_ledger/`, `docs/archive/`,
  `docs/scenarios/`, `docs/entity/`, `docs/audits/`) — Step 5's self-check instruction must not
  relitigate what doc-updater is allowed to fix/edit, only its own reporting discipline.
- `docs/ai/workflows.md` and `docs/ai/system_overview.md` — no new phase/agent is introduced by
  this ticket, so neither file's tables need a **new row** (investigation.md, "Docs Requiring
  Update" exclusions). **Revised per NEEDS_CHANGES fix:** this guard is about not adding a new row,
  not about leaving an existing cell's now-false claim uncorrected — Step 6(C) makes one narrow
  edit to the Document-Update row's existing cell text in `docs/ai/workflows.md:88` (Decision 3
  makes its "remains the actual backstop for standard/epic tier" phrasing stale for the reverse
  half). `docs/ai/system_overview.md` is unaffected by this narrowing and remains fully out of
  scope — no known stale claim was found there.
- `docs/mechanics/*.md` and `docs/engine/*.md` — no simulation law/formula/pipeline behavior is
  touched by this ticket.
- The real `tickets/done/TCK-20260831-*.md` historical-incident files — cited as evidence only,
  never edited; Step 2's fixture is a fresh reconstruction, not an edit to the real record.

## Dependency Map

```
Step 1 (core reverse-check logic)
 ├─→ Step 2 (historical fixture test)
 ├─→ Step 3 (run_static_precheck wiring confirmation test)
 ├─→ Step 4 (implement-ticket.js prompt text update)
 ├─→ Step 6 (doc_updater_agent.md reword + docs/ai/workflows.md:88 cell correction)
 ├─→ Step 7 (guardrail_enforcement_epic.md M2 note)   [also depends on Step 2]
 └─→ Step 8 (ticket-lifecycle.md hotfix passage correction)

Step 5 (doc-updater.md self-check instruction) — independent, no dependency on Step 1
 └─→ Step 6 (doc_updater_agent.md reword references Step 5 contextually, non-blocking)
```

Steps 1, 5 can be implemented in either order or in parallel. Steps 2, 3, 4, 6, 7, 8 all require
Step 1's finished behavior to describe or exercise correctly. Step 7 additionally requires Step 2
(cites which historical incident was actually reproduced). Step 6 references Step 5 for
completeness but does not require its exact final wording to be written correctly.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — new/extended check FAILs when a touched `docs/` path is missing from Files Changed/Related Docs | Step 1 | `test_reverse_docs_coverage_fails_when_touched_doc_not_in_files_changed_or_related_docs` |
| AC #2 — same check PASSes when every touched `docs/` path appears in one of those sections, and blocks Verify (not just advises) | Step 1, Step 3 | `test_reverse_docs_coverage_passes_when_touched_doc_appears_in_files_changed`, `test_reverse_docs_coverage_passes_when_touched_doc_appears_in_related_docs_only`, `test_run_static_precheck_wires_reverse_check_blocking` |
| AC #3 — at least one of the three named historical incidents reproduced as a regression fixture proving pre-hand-patch FAIL | Step 2 | `test_reverse_docs_coverage_reproduces_RACE_RELATIONS_MATRIX_incident` |
| AC #4 — doc-updater.md's base prompt gains an explicit self-check instruction | Step 5 | `test_doc_updater_prompt_includes_self_check_instruction` |

## Anti-Drift Notes

- **Do not copy `check_tag_drift`'s `CLEAN`/`FLAGGED` status vocabulary.** The reverse check must
  return `PASS`/`FAIL`/`NA` (in this case, `NA` only ever applies to the *forward* half under
  hotfix tier — see Decision 3; the reverse half never returns `NA`). Reusing `check_tag_drift`'s
  path-resolution/section-reading *mechanics* is correct and expected; reusing its *status
  contract* would silently produce a non-blocking check and fail AC #2.
- **Do not touch the forward-direction bullet-format contract** (`_parse_docs_to_update` and
  siblings) — several prior tickets hardened this against real false positives; any incidental
  edit reopens that risk.
- **Disclose, do not silently absorb, Decision 2's coverage gap.** The `docs/`-only scope cannot
  structurally catch the `ITEM-INSTANCE-HISTORY` incident's `src/core/state.py` gap. Completion
  Summary and Step 7's epic-doc note must state this limitation explicitly rather than imply the
  reverse check covers all Files-Changed-omission classes.
- **`doc-updater` fixing a code bug outside its documented scope (the real `to_readonly()`
  incident) is itself disclosed drift** from doc-updater.md's stated mandate — Step 5's self-check
  instruction is about doc-updater's own *reporting* discipline, not about narrowing or widening
  what it is allowed to fix. Do not conflate the two while editing `doc-updater.md`'s prompt.
- **`docs/parity_ledger/infrastructure.yaml`'s edit is Parity phase's job, not this ticket's** —
  despite appearing in investigation.md's Docs Requiring Update list, no step here routes through
  it; do not have `doc-updater` or any Implement step touch it.
- **The module-level docstring's stale "5 pre-Finalize conditions" (line 8-9) predates this
  ticket** — not something this ticket is required to fix; do not fix it as an incidental
  side-effect of Step 1's edit (would blur the diff and is out of this ticket's Scope).
- **Reverse-check evidence must name the specific missing path(s)**, mirroring the forward check's
  own `missing` evidence shape (lines 549-554) — a generic "reverse check failed" evidence string
  would not meet this project's traceability standard for a blocking gate.
- **Step 6(B)'s hotfix-gap correction must state the accepted/closed split precisely, not overclaim
  full closure.** `docs/architecture/doc_updater_agent.md:162-169`'s "no equivalent backstop" claim
  is only *partially* falsified by Decision 3: the touched-but-undeclared `docs/` case is now
  caught on hotfix tier (reverse half), but the never-touched-at-all omission case (doc-updater
  wrongly judging a doc doesn't need touching, so git shows nothing touched) remains genuinely
  uncaught on hotfix tier — unchanged. Do not reword this passage to imply the hotfix backstop gap
  is now fully closed; state both halves.
- **`test_docs_coverage_hotfix_is_na`'s rewrite (Step 1, item 10) must not silently vanish the
  forward-still-skips assertion.** The point of Decision 3 is that only the *reverse* half stops
  returning bare `NA` for hotfix — the forward half's genuine skip (no `investigation.md`
  dependency) must still be independently assertable after the rewrite, not merely implied by the
  new test's name.

## Revision History

**2026-09-05 — NEEDS_CHANGES fixes (architecture review round 1).** Architecture review returned
`NEEDS_CHANGES` citing two gaps; both are fixed in this revision, nothing else in the plan was
changed:

1. **Internal inconsistency in Step 1's Verify claim vs. Decision 3.** Step 1's Verify list
   originally claimed "All existing `test_docs_coverage_*` tests (lines 1399-1623) unmodified and
   still passing," which silently contradicted Decision 3: `test_docs_coverage_hotfix_is_na`
   (`tests/tools/test_done_checker_static.py:1399-1403`) asserts a bare, unconditional `NA` for
   hotfix tier with no ticket file present — a fixture that, once Decision 3's fall-through
   restructuring lands, would actually assert `FAIL` (missing-ticket-file path), not `NA`. Fixed by
   adding Change item 10 to Step 1 (explicit rewrite instructions: split into a forward-skip test
   and a reverse-runs-under-hotfix test) and correcting the Verify list to carve out this one test
   by name instead of claiming blanket unmodified survival.
2. **Two additional stale doc locations from Decision 3, beyond the one Step 8 already fixed.**
   Step 6 previously only reworded `docs/architecture/doc_updater_agent.md` lines 142-148 (the
   "Error handling" decoupling paragraph). Review found two more locations making the same
   now-falsified "hotfix has no backstop" claim: (a) the *same file*'s lines 162-169 (a different
   paragraph, read verbatim before writing the fix), and (b) `docs/ai/workflows.md:88`'s
   Document-Update table-row cell ("remains the actual backstop for standard/epic tier"). Fixed by
   extending Step 6 into three sub-changes (A, B, C) covering all three passages, correcting the
   Scope Guards' `docs/ai/workflows.md` entry to permit this one narrow existing-cell edit (while
   still refusing a new table row), and adding two Anti-Drift Notes warning against overclaiming
   full gap closure in the reworded text.

No other step, decision, or scope boundary was changed. The core reverse-check design (in-place
extension, `docs/`-only scope, tier-agnostic reverse check, PASS/FAIL vocabulary,
`_resolve_ticket_body_path` new-helper pattern), the INFRA-322/INFRA-396 parity ledger precedent
citations, and all other steps (2, 3, 4, 5, 7, 8) remain exactly as originally written.

## Deviations (recorded during Implement)

1. **Step 1's Verify claim that all pre-existing `test_docs_coverage_*` tests would remain
   "unmodified" except `test_docs_coverage_hotfix_is_na` did not hold, for two evidence-based
   reasons discovered by actually running the suite after implementing the reverse check** (not
   speculative — both were empirically confirmed):
   - `test_docs_coverage_all_flagged_paths_touched_passes`,
     `test_docs_coverage_line_suffix_bullet_matches_bare_git_path`, and
     `test_docs_coverage_resolved_conditional_bullet_touched_anyway_still_passes` each `git init` a
     fresh `tmp_path` repo and touch a real `docs/` file, but never create a resolvable ticket file
     for `TCK-FAKE`. The reverse check's own designed behavior (plan Step 1 item 6: a missing
     ticket file at Verify time is a real `FAIL`, not a silent pass) then broke all three, since
     each has at least one touched `docs/` path with no ticket to check it against. Fixed by adding
     a minimal resolvable ticket file (via a new `_write_reverse_ticket` helper) declaring the same
     touched path to each of the three fixtures. This is not a workaround: real Verify-time calls
     always have a resolvable ticket file (that's what `check_ticket_location` itself requires
     elsewhere in `run_static_precheck`) — these three fixtures' prior absence of one was a gap in
     the fixture, not a case the reverse check should tolerate, and the fix does not weaken what
     the tests were originally built to verify (forward-direction bullet-format parsing).
   - `test_docs_coverage_no_section_heading_passes`, `test_docs_coverage_explicit_none_passes`, and
     `test_docs_coverage_none_with_trailing_rationale_passes` never called
     `monkeypatch.chdir(tmp_path)` — harmless under the old forward-only logic, which never invoked
     `_git_touched_paths()` at all for an empty-required-docs fixture. The new reverse half always
     invokes it, so these three tests were unknowingly reading the *real* repo's own uncommitted
     `docs/` changes (confirmed via `git status --porcelain` in this shared worktree at
     implementation time — real, unrelated modifications to `docs/REGISTRY.yaml`,
     `docs/agent-monitoring/README.md`, `docs/ai/README.md`, `docs/parity_ledger/infrastructure.yaml`
     from concurrent work). Fixed by adding the missing `monkeypatch.chdir(tmp_path)` to each — a
     pre-existing test-isolation gap the new always-on git call exposed, not a new design choice.

   Neither fix touches `check_docs_to_update_coverage`'s actual logic or the reverse check's
   designed behavior — both are test-fixture corrections. Recorded here per the project's
   Deviations-disclosure convention rather than silently patching around the plan's inaccurate
   Verify claim.

2. **Step 2's "mirroring existing tests" phrasing for mocking `_git_touched_paths` was not
   literally accurate** — no test in `tests/tools/test_done_checker_static.py` mocked
   `_git_touched_paths` (or any git-related function) prior to this ticket; every existing
   `check_docs_to_update_coverage` test uses a real `git init`+file-write fixture instead. The
   historical-incident regression test
   (`test_reverse_docs_coverage_reproduces_RACE_RELATIONS_MATRIX_incident`) instead introduces the
   first such mock in this file, via `monkeypatch.setattr("gate_checks.done_checker_static._git_touched_paths", ...)`
   (patching the module attribute, since the test file only imports specific names, not the module
   object — a plain rebind of the test file's own imported alias would not affect the internal call
   inside `done_checker_static.py`). This is a minor implementation-level judgment call, not a
   scope or behavior change.
