---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT
phase: inprogress
date: 2026-09-07
tags: [registry, process-improvement, data-quality]
---

# TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT

## Title
227 of 1850 tickets/done/*.md files have stale `status: active`/`phase: open` frontmatter instead of `status: historical`/`phase: done`

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
While closing `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP` (which added a correction
note to `tickets/done/TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS.md`'s Completion Summary), the
Finalize step noticed that sibling ticket's frontmatter reads `status: active`/`phase: open` despite
sitting in `tickets/done/` — the opposite of the `status: historical`/`phase: done` convention every
other DONE ticket in this repo follows. A repo-wide check (`grep` for `status: active` + `phase: open`
across every file in `tickets/done/`) found this is not an isolated case: **227 of 1850** files in
`tickets/done/` (~12.3%) carry this same mismatch. `git show` on the original commit that closed
`TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS.md` (`eedf7d5b`, PR #87) confirms the frontmatter was
already wrong at the moment the ticket was first closed — this is not drift introduced later, it is
a Finalize-time gap that has recurred intermittently across many ticket closures over time.
`tools/validate_frontmatter.py` does not catch this because `status: active`/`phase: open` are both
individually valid enum values — the check missing is a cross-field consistency rule ("a ticket's
frontmatter `phase`/`status` must agree with which top-level `tickets/` directory it physically sits
in"), not a schema violation of either field in isolation.

## Scope
- Investigate whether this is truly an intermittent random gap or correlates with a specific
  closure path (e.g. hand-orchestrated closures before a certain date, a specific Finalize-agent
  prompt variant, batch-folder closures, etc.) — the 227-file list itself is real evidence worth
  mining for a pattern before assuming it's uniformly random.
- Decide and implement a durable fix: most likely a new cross-field consistency check in
  `tools/validate_frontmatter.py` (or a sibling `tools/gate_checks/` script) asserting a ticket's
  `phase`/`status` frontmatter values are consistent with its physical location
  (`tickets/inprogress/` implies `phase != done`; `tickets/done/` implies `phase: done` and
  `status: historical`), wired into whatever check already runs at Finalize/Verify time
  (`done_checker_static.py`'s `frontmatter_valid` condition is the natural home, or a new dedicated
  condition) so this stops recurring for future ticket closures.
- Decide whether/how to remediate the 227 already-affected files: a bulk, reviewed, mechanical
  frontmatter-only correction (2-line change per file: `status: active` → `status: historical`,
  `phase: open` → `phase: done`) is a strong candidate given the fix is narrow and mechanical, but
  this is Plan's decision — investigate for any reason a specific file's mismatch might be
  intentional (unlikely, but check a sample) before assuming a blanket bulk-fix is safe.

## Out of Scope
- Any change to a DONE ticket's body content (Completion Summary, Files Changed, etc.) — this
  ticket is frontmatter-only.
- Re-litigating or auditing the substance of any of the 227 tickets' original closure decisions —
  this is a metadata-consistency fix, not a re-review of old work.
- `tickets/inprogress/` or `tickets/todos/` frontmatter consistency — scope this to the
  `tickets/done/` mismatch class found here; a symmetric check for the other directories may be a
  natural follow-on but is not required by this ticket's own evidence.

### Scope amendment (Investigate, 2026-09-11)
- **The count is 395, not 227, and ~138 of them are schema-invalid.** Values like `status: done` /
  `open` and `phase: epic_scoped` are rejected by the existing single-field enum. That means the
  validator never runs on them, which is a second root cause beyond the missing cross-field rule.
- **Root cause is the closing path.** Drift is 16.2% for pipeline closes, 41.0% for
  hand-orchestrated closes, and 53.5% for closes with no monitoring record. `validate_frontmatter.py`
  runs only in `done_checker`, and only for the ticket being closed; nothing checks `tickets/done/` as
  a whole. `implement-ticket.js:1671` does instruct `historical`/`done`, yet 24.6% of its closes still drift;
  no workflow closes epic tickets at all, so epics are moved by hand with no instruction (91.7% drift).
  *(Corrected twice after Review.)*
- **Fix widened accordingly:** cross-field rule + `done_checker` wiring (as proposed), **plus** a
  path-independent corpus test over all of `tickets/done/`, **plus** a test pinning `implement-ticket.js:1671`'s existing instruction, **plus** parity updates to
  INFRA-180/305. A missing epic-close step in `implement-epic.js` is a follow-on ticket.
- **9 epic-tier tickets use `phase: epic_scoped` deliberately.** Plan recommends normalizing them to
  `done` rather than adding the value to the enum. The decision gets recorded before the bulk edit.
- Full evidence: `staging_artifacts/TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT/`.

## Acceptance Criteria
- [x] A durable, evidence-based root-cause finding for why this gap recurs (a specific closure
      path, or genuinely random/inconsistent Finalize execution) is documented
- [x] A new automated check catches this class of mismatch going forward, wired into an existing
      gate (Finalize/Verify) rather than left as a manual audit
- [x] A corpus-wide test enforces the rule over every file in `tickets/done/`, independent of the
      closing path
- [x] `implement-ticket.js`'s existing Finalize instruction (line 1671) is pinned by a test
- [x] A follow-on ticket is filed for the missing epic-close step in `implement-epic.js`
- [x] INFRA-180 and INFRA-305 reflect the new cross-field rule, written via `write_entry()`
- [x] The `epic_scoped` decision (normalize vs. enum addition) is recorded before remediation
- [x] An explicit, evidence-based decision is made and recorded on remediating the already-affected
      files (395 as of 2026-09-11; re-count at implementation) — not silence
- [x] If a bulk fix is performed, a before/after count confirms the changed-file count equals the
      fresh before-count, only the 2 frontmatter fields touched, and zero body-content bytes altered

## Related Tickets
- `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS` (done) — the specific instance that surfaced this
  finding; not itself in scope to re-fix beyond its frontmatter, per this ticket's Scope.
- `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP` (done) — the ticket during whose Finalize
  this was discovered.
- `TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING` (todos, standard) — follow-on filed at Implement
  for the missing `implement-epic.js` epic-close step (investigation.md §8, second correction).

## Related Docs
None yet — Investigate should determine whether `tools/validate_frontmatter.py`'s own docstring/
CLAUDE.md's ticket-format documentation needs a note once the new check exists.

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/validate_frontmatter.py`
- `tools/gate_checks/done_checker_static.py` (`frontmatter_valid` condition)
- `tickets/done/*.md` (395 affected files as of 2026-09-11, per the Scope amendment — re-count at
  implementation time; superseding the original 227 estimate)

## Assumptions / Open Questions
- Whether the 227-file count is stable or would grow if re-checked later (more tickets close between
  now and Implement) — Investigate should re-run the count fresh rather than trust this ticket's
  snapshot number.
- Whether a bulk mechanical fix across 227 files should land as one commit or be batched — a Plan
  decision, informed by how this repo's shared-worktree/PR conventions handle a large but
  mechanically-uniform diff.

## Implementation Notes
Investigate and Plan are complete; see
`staging_artifacts/TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT/`. Plan order:
cross-field rule → `epic_scoped` decision → bulk remediation (separate commit, dry-run script) →
corpus test → pin line 1671's instruction → parity (INFRA-180/305) → file the epic-close follow-on. Revised after
Review NEEDS_CHANGES; see investigation.md §8. Implementation is handed to `agent-working-implementer`.

### Step 1 — cross-field rule (implemented)
`tools/validate_frontmatter.py` gains `TICKET_LOCATION_RULES` + `check_ticket_location_consistency(path, fm)`
(tickets/done/ → status: historical + phase: done; tickets/inprogress/ → phase != done). Deliberately
**not** folded into `_validate_ticket`/`validate_file` — it's called explicitly by the two consumers
(`done_checker_static.check_frontmatter_valid()` and the new corpus test) so an unrelated
`validate_file`/`validate_directory` sweep over `tickets/` doesn't silently start enforcing directory
placement too, and so the ~15 pre-existing `test_validate_frontmatter.py` fixtures that write ticket
frontmatter into `tmp_path/tickets/done/` with non-canonical defaults keep passing unmodified (verified:
all 206 pre-existing tests in `test_validate_frontmatter.py`/`test_done_checker_static.py` still pass
with no edits). `done_checker_static.check_frontmatter_valid()` (tools/gate_checks/done_checker_static.py:287-327)
now additionally parses the ticket's frontmatter via the already-imported `extract_frontmatter` and calls
`check_ticket_location_consistency` on it, merging any errors into `ticket_errors`.

### Step 2 — `epic_scoped` decision (recorded before Step 3's bulk edit)
Per plan.md's recommendation: the 9 closed epics with `phase: epic_scoped` (E13, E21, E31, E32, E33,
E41, E42, E43, E53A) are normalized to `status: historical` / `phase: done` by Step 3's bulk script,
using the same mapping as every other non-canonical file. `epic_scoped` is **not** added to
`PHASE_VALUES`. Their body `## Status` fields are left untouched, per the ticket's own Out of Scope.

**Disclosed consequence, stated before the files are touched:** of those 9, **2 bodies say
`## Status: EPIC_SCOPED`** (E13, E53A) and **7 say `## Status: DONE`**. After Step 3, all 9 have
frontmatter `phase: done`, which agrees with the 7 `DONE` bodies but **visibly disagrees** with the 2
`EPIC_SCOPED` bodies (E13, E53A) — frontmatter will say `done`, body will still say `EPIC_SCOPED`. This
is an accepted, disclosed consequence of the no-body-edits rule (this ticket's Out of Scope forbids
touching `## Status`), not an oversight, and not something Step 1/4's frontmatter-only rule can or
should catch (body `## Status` is validated by a different mechanism, `tools/ticket_field_values.py` /
`status_drift_check.py`, out of this ticket's scope).

**A 10th epic-scoped-shaped file, found at implementation time, not in investigation's list of 9:**
`tickets/done/TCK-20260619-E53D-HISTORY.md` has `status: epic_scoped` / `phase: scoped` — the two
values transposed relative to the other 9's `status: done` / `phase: epic_scoped` pattern, so
investigation §5's `grep "^phase: epic_scoped"` didn't find it. It is tier `epic`, body
`## Status: EPIC_SCOPED`. Same decision applied for consistency: normalized to `historical`/`done` by
Step 3, body left alone (so it joins E13/E53A in the disclosed frontmatter/body mismatch above — 3 of
the 10, not 2 of 9).

### Step 3 — bulk remediation (executed)
Fresh recount at implementation time (2026-09-11), scoped to real ticket files only — `ticket_id`
matching `^TCK-\d{8}-` under `tickets/done/**/*.md` — which excludes 77 folder-level `SEQUENCE.md`
files (no frontmatter at all) and 37 files whose `ticket_id` doesn't match the TCK- shape:
`tickets/done/README.md` (`ticket_id: INDEX`, a docs-site index page, missing a `phase` field
entirely — a distinct, pre-existing, out-of-scope schema gap unrelated to this ticket's status/phase
drift) and 36 pre-TCK-convention legacy files (`METRICS-01.md`, `RESTRUCTURE-01.md`,
`bug-01-diagonal-hunt-move-conflict.md`, `infra-0X-*.md`, `resource_v2_*.md`, etc. — all predate the
`TCK-YYYYMMDD-` ticket ID convention and were never ticket-schema files to begin with). Fresh
non-canonical count with this scoping: **395** (same number as investigation's 2026-09-11 snapshot —
tickets closing and the 10th epic file both entering the corpus since then netted to zero change).

One-off script (`scratchpad/remediate_ticket_frontmatter.py`, not committed — dry-run mode first,
then real run) rewrote only the `status:` line (→ `historical`) and `phase:` line (→ `done`) inside
each of the 395 files' leading `---` block. All 395 already had literal `status:` and `phase:` lines
present (confirmed before running — no line insertions were needed). Verified after:
- After-count of non-canonical (in the same 395-file scope) is 0.
- Every changed file's diff touches only the `status:`/`phase:` lines (git diff inspected).
- Every changed file's body bytes (everything after the closing `---`) are SHA-256-identical
  before/after (see verification output referenced in Files Changed).
- Committed separately from the Step 1/4/5/6 code changes.

### Step 4 — corpus enforcement (implemented)
New tests in `tests/tools/test_validate_frontmatter.py` (`TestTicketLocationConsistencyCorpus`):
`test_real_tickets_done_corpus_is_fully_canonical` runs `check_ticket_location_consistency` over
every real `tickets/done/**/*.md` file (same TCK-ID scoping as Step 3, plus the pre-existing
SEQUENCE.md skip) and asserts zero errors. Confirmed failing pre-Step-3 (686 errors from the 395
non-canonical files, ~1.7 errors/file average) and passing post-Step-3.
`test_corpus_check_catches_a_reverted_file` builds a synthetic `tmp_path` corpus (never touches the
real tree) with one canonical and one drifted file, proving the corpus check actually catches a
regression rather than only passing on already-clean data.

### Step 5 — pin instruction (implemented)
`implement-ticket.js:1671`'s `phase: done` / `status: historical` Finalize instruction is unchanged.
New file `tests/tools/test_finalize_phase_status_instruction_pin.py` (3 tests) pins the instruction
text, that it lives inside the Finalize phase block, and that it precedes the physical move to
`tickets/done/` — following `tests/tools/test_finalize_knowledge_index_refresh.py`'s established
raw-source-text-parsing pattern (no JS test runner exists in this repo for `.claude/workflows/*.js`).

### Step 6 — parity ledger (implemented)
`INFRA-180` and `INFRA-305` updated via `tools/parity_ledger_writer.write_entry()`. `INFRA-180`'s
`text`/`v2_evidence` now describe the location-aware cross-field rule alongside the existing
per-field/tag enforcement. `INFRA-305`'s `check_frontmatter_valid()` line-number citation refreshed
to `tools/gate_checks/done_checker_static.py:287-327` (its real current location — the entry's old
`:238-284` citation was already stale before this ticket, from unrelated intervening edits).
`INFRA-278` untouched, confirmed unrelated across 2 prior review rounds (documents
`check_ticket_field_values_valid()`, a different function/mechanism).

### Follow-on ticket filed
`implement-epic.js` has no step that closes an epic ticket itself (frontmatter to
`historical`/`done`, move to `tickets/done/`) once all children are done — see investigation.md §8's
second correction. Filed as a real ticket rather than left as a note: see Related Tickets.

## Test Summary
Scoped run (venv `.venv/bin/python3`):
```
pytest tests/tools/test_validate_frontmatter.py tests/tools/test_done_checker_static.py \
       tests/tools/test_add_frontmatter_tickets.py tests/tools/test_finalize_phase_status_instruction_pin.py \
       tests/tools/test_parity_ledger_writer.py -q
```
→ 285 passed, 0 failed. Includes the new `TestTicketLocationConsistency` (7 fixture tests),
`TestTicketLocationConsistencyCorpus` (2 tests — the real-corpus test and the reverted-file
negative-path test) in `test_validate_frontmatter.py`, and the 3 new tests in
`test_finalize_phase_status_instruction_pin.py`. All 206 pre-existing tests in
`test_validate_frontmatter.py`/`test_done_checker_static.py` pass **unmodified** — confirms Step 1's
explicit (not auto-wired) design caused zero collateral test breakage.

Confirmed the corpus test (`test_real_tickets_done_corpus_is_fully_canonical`) fails before the
Step 3 commit (686 errors from 395 files) and passes after — the fail→pass transition Step 4's
plan required as proof the check catches a real regression.

Full-suite regression check: `pytest tests/tools/ -q -m "not slow"` → **2502 passed, 1 failed, 17
skipped, 28 deselected, 1 xfailed**. The 1 failure
(`tests/tools/test_retrieval_baseline_metrics.py::test_baseline_report_cli_runs_against_real_corpus_and_prints_json`)
is unrelated to this ticket: it's a pre-existing bug in `tools/agent-monitoring/build_index.py`'s
`build()`, which unconditionally prints a `"runs: N rows, events: N rows, tools: N rows (N
skipped)"` summary line to stdout whenever `generate_retro.py::_load_runs_and_events()` triggers an
on-demand index rebuild for a stale `agent-monitoring/` SQLite index — polluting the JSON-only
stdout this CLI test expects. This session's own continuous tool-call volume kept
`agent-monitoring/data/2026-W37/tools.jsonl`'s mtime ahead of the index DB's mtime throughout, so
the rebuild (and the pollution) reproduces on every re-run within this session regardless of this
ticket's own code changes — confirmed unrelated to `validate_frontmatter.py`,
`done_checker_static.py`, or `docs/parity_ledger/` by inspection (none of this ticket's changed
files are anywhere in that test's call chain). Not fixed here — a different subsystem
(`tools/agent-monitoring/`), out of this ticket's scope; fixing it would be the kind of unrelated
gate patch the project's Gate Integrity rule forbids doing silently mid-ticket.

Also ran `python3 tools/validate_frontmatter.py tickets/done` (the full per-field schema check, not
just the location rule): 94 violations remain, all in the 77 `SEQUENCE.md` files (no frontmatter)
and the ~17 pre-existing, unrelated `layer`/`authority` enum violations already in the corpus
(e.g. `layer: social`, `layer: infrastructure`, `authority: P3`) plus `tickets/done/README.md`'s
pre-existing missing-`phase`-field gap — confirmed **zero** of the 94 are `status`/`phase` drift;
this ticket's own scope is fully remediated.

## Files Changed
- `tools/validate_frontmatter.py` — added `TICKET_LOCATION_RULES`, `_ticket_directory()`,
  `check_ticket_location_consistency()` (Step 1).
- `tools/gate_checks/done_checker_static.py` — `check_frontmatter_valid()` now also calls
  `check_ticket_location_consistency()` on the ticket's parsed frontmatter (Step 1).
- `tests/tools/test_validate_frontmatter.py` — added `TestTicketLocationConsistency` (7 tests) and
  `TestTicketLocationConsistencyCorpus` (2 tests, Step 4); added `check_ticket_location_consistency`
  import and `import re`.
- `tests/tools/test_finalize_phase_status_instruction_pin.py` (new file) — 3 tests pinning
  `implement-ticket.js:1671`'s Finalize instruction (Step 5).
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-180` and `INFRA-305` updated via
  `tools/parity_ledger_writer.write_entry()` (Step 6). No other entries touched (confirmed: no
  `id:` line added/removed, diff limited to these 2 entries' `text`/`v2_evidence` fields).
- `tickets/done/*.md` (395 files, frontmatter-only) — Step 3 bulk remediation, committed separately
  (commit `8cd24e08`, see `git log`) from the code/test changes above. `status:` → `historical`,
  `phase:` → `done`, nothing else changed (body bytes SHA-256-verified identical, diff lines
  verified to touch only `status:`/`phase:`).
- `tickets/todos/TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING.md` (new file) — follow-on ticket
  filed for the missing `implement-epic.js` epic-close step.
- `tickets/inprogress/TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT.md` — this file
  (Implementation Notes, Acceptance Criteria, Related Tickets, Test Summary, Files Changed,
  Completion Summary).
- `staging_artifacts/TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT/plan.md` — added a
  `## Deviations` section documenting the explicit-vs-implicit Step 1 design choice, the TCK-ID
  scoping decision for Steps 3/4, and the 10th epic file found beyond investigation's 9.
- `CLAUDE.md` (Doc phase: added a note on the new location-consistency rule in the Ticket Format
  section).
- `docs/guidelines/frontmatter_schema.md` (Doc phase: added a "Cross-field rule (location
  consistency)" subsection to the ticket content-type schema).
- `docs/ai/ticket-lifecycle.md` (Doc phase: expanded DoD condition 12's table row to cite the new
  check).
- Not committed (one-off, not a durable tool): `scratchpad/remediate_ticket_frontmatter.py`,
  `scratchpad/verify_body_hashes.py`, `scratchpad/update_parity_entries.py` (all under this
  session's scratchpad directory, outside the repo).

## Completion Summary
Added a location-aware cross-field frontmatter rule (`tools/validate_frontmatter.py::check_ticket_location_consistency`)
that catches drift where a ticket's `status`/`phase` are each individually enum-valid but disagree
with which `tickets/` subdirectory the file physically sits in — the exact class of drift the
existing per-field enum validator could never catch. Wired it explicitly into
`done_checker_static.check_frontmatter_valid()` (per-ticket enforcement at Verify time) and into a
new corpus-wide test that sweeps the entire real `tickets/done/` tree independent of how each
ticket was closed (fixing the investigation's cause 2: hand-orchestrated/unrecorded closes never
ran the per-ticket check at all). Bulk-remediated the 395 real already-affected `tickets/done/*.md`
files (frontmatter-only, two lines per file, verified byte-identical bodies) in a separate,
independently-reviewable commit, including the 9 `phase: epic_scoped` epics found by investigation
plus a 10th (`E53D-HISTORY`) found at implementation time with transposed field values — normalized
per the recorded Step 2 decision (no `epic_scoped` enum addition) with the resulting body/frontmatter
disagreement for 3 of the 10 epics explicitly disclosed rather than silently accepted. Pinned
`implement-ticket.js`'s existing Finalize instruction with a static test, updated `INFRA-180`/
`INFRA-305` via `write_entry()`, and filed `TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING` as the
durable follow-on for the still-missing `implement-epic.js` epic-close workflow step. No `src/`
files touched; this is pure tooling/data — no parity subsystem is affected and no simulation
behavior changed.
