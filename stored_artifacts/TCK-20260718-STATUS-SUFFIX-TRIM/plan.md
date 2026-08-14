---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260718-STATUS-SUFFIX-TRIM
artifact_type: plan
tags: [data-quality, observability]
---

# Implementation Plan — TCK-20260718-STATUS-SUFFIX-TRIM

## Summary

Trim the `## Status` body section of 10 frozen `tickets/done/*.md` files down to the bare token
`DONE`, relocating the trimmed descriptive tail into each file's `## Completion Summary` section as
reworded (never verbatim-pasted) prose. One file (`TCK-20260408-PH3-STG1-HOUSEHOLD.md`) is
pre-12-section legacy format with no `## Completion Summary` at all — this plan adopts the
investigation's recommendation to append a minimal, single-sentence `## Completion Summary` section
rather than restructuring the file. The go/defer decision on extending
`tools/gate_checks/status_drift_check.py` is resolved here as **DEFER** (reasoning below, adopted
from the investigation's recommendation, no override) — no code change to `status_drift_check.py`,
`tests/tools/test_status_drift_check.py`, or `docs/parity_ledger/infrastructure.yaml` occurs in this
ticket. Each of the 10 files is edited in its own step so it can be diffed and verified in isolation;
a final verification step re-runs `parse_body_section` extraction and `status_drift_check.py` against
the full batch and checks the `git diff --stat` scope guard.

## status_drift_check.py Extend-vs-Defer Decision (Resolved)

**Decision: DEFER.** No change to `tools/gate_checks/status_drift_check.py`,
`tests/tools/test_status_drift_check.py`, or `docs/parity_ledger/infrastructure.yaml` in this ticket.

This adopts the investigation's recommendation as final, for the following reasons (mirroring the
predecessor ticket's own "Colon-Suffixed Files Decision" precedent almost exactly):

1. This ticket's acceptance criteria are anchored to a fixed, frozen 10-file list established at
   ticket-creation time. Extending the checker's detection logic inside this same ticket risks
   surfacing a different live count if any other `tickets/done/*.md` file shares this trailing-prose
   shape but was never part of the frozen list — that re-scan is explicitly out of scope (see Scope
   Guards).
2. `test_regex_matches_baseline_scan_pattern` currently pins `TICKET_STATUS_RE.pattern` to
   `r"^## Status\s*\n+\s*(\S+)"` byte-for-byte. Widening `check_ticket_status_drift`'s matching logic
   to also inspect tail text past the first token is a real, non-trivial design decision (new regex
   vs. new coexisting check function vs. changing the pinned assertion) — not a small tweak that
   belongs bundled into a data-normalization ticket.
3. Two structurally distinct checker gaps now exist (same-line colon-suffixed drift, from the
   predecessor; trailing-prose-after-DONE, from this ticket). A future ticket scoping both gaps
   together is likely to produce a cleaner design (e.g. one `EXTRA_PROSE_RE` or a documented
   tri-state classification) than two independently-bolted-on special cases added in two separate
   tickets.
4. This ticket's 10-file data fix is fully self-contained and independently valuable — it fixes the
   dashboard facet fragmentation today without depending on the checker extension. Per CLAUDE.md's
   "never plan more work than the ticket scope... note adjacent problems as future tickets," this
   plan does not create that future ticket; it only records the recommendation (in the ticket's
   Implementation Notes at Verify time, per AC6) for a later, separately-scoped ticket to pick up.

This is not left as an "Unresolved Question" — it is a final, adopted design decision for this
ticket's implementation scope.

## Steps

### Step 1 — Freeze and re-confirm the 10-file list and current text
**Files:** none changed (read-only verification)
**Change:** Before editing anything, re-run a direct read (or `sed -n` / `grep -A2 '^## Status'`) over
all 10 files in the frozen list below and diff against the exact verbatim text already captured in
`staging_artifacts/TCK-20260718-STATUS-SUFFIX-TRIM/investigation.md` ("Exact current text of each of
the 10 files' `## Status` and `## Completion Summary` sections"). This step exists to catch any drift
between investigation time and implementation time (e.g. a concurrent edit landing on `main`) before
any write happens. The frozen list (do not add or remove entries from this list under any
circumstance):
1. `tickets/done/TCK-20260408-PH3-STG1-HOUSEHOLD.md`
2. `tickets/done/TCK-20260619-E12-BALANCE-BASELINE.md`
3. `tickets/done/TCK-20260619-E62-CULTURE-DRIFT.md`
4. `tickets/done/TCK-20260619-E63-FEATURE-PACKS.md`
5. `tickets/done/TCK-20260628-E-NARRATIVE-CONSEQUENCE.md`
6. `tickets/done/TCK-20260628-E-PARTY-LOOP.md`
7. `tickets/done/TCK-20260628-E-PERSONALITY-CALIBRATION.md`
8. `tickets/done/TCK-20260628-E-WORLD-EVOLUTION.md`
9. `tickets/done/TCK-20260701-SIMQ-EMIT-CAMP.md`
10. `tickets/done/TCK-20260701-SIMQ-KERNEL-WIRE.md`
**Do NOT touch:** No file writes in this step. Do not expand the list based on anything found during
the re-read — if drift is found, stop and reconcile against investigation.md before proceeding, do
not silently fold in a newly-noticed file.
**Verify:** Manual — re-read text matches investigation.md's captured snapshot for all 10 files
(or documented reconciliation if it doesn't).

---

### Step 2 — `tickets/done/TCK-20260408-PH3-STG1-HOUSEHOLD.md` (legacy-format handling)
**Files:** `tickets/done/TCK-20260408-PH3-STG1-HOUSEHOLD.md`
**Change:** This file's body ends immediately after `## Status` with no `## Completion Summary` or
any other post-Status section (pre-12-section legacy format, frontmatter `layer: misc`). **Decision
(confirming, not revising, the investigation's recommendation):** append a minimal
`## Completion Summary` section — only this one section, not the other 6 unused standard-format
sections — containing a single reworded sentence preserving the superseded-by information. This is
the smallest structural addition that avoids information loss without forcing full 12-section
restructuring onto a file this project's "legacy data scope" precedent treats as out of scope for
restructuring.

Exact edit — replace:
```
## Status
DONE (SUPERSEDED by TCK-20260408-PH3-PASS1-LIVED-MODELS)
```
with:
```
## Status
DONE

## Completion Summary
Superseded by TCK-20260408-PH3-PASS1-LIVED-MODELS.
```
**Do NOT touch:** Any of the other 6 standard-format sections (`## Related Tickets`, `## Related
Docs`, `## Related Stored Artifacts`, `## Related Code Areas`, `## Assumptions / Open Questions`,
`## Implementation Notes`, `## Test Summary`, `## Files Changed`) — do not add any of these. Do not
touch frontmatter (`layer: misc` stays as-is — do not "fix" it to match other files).
**Verify:** `^## Status\s*\n+\s*DONE\s*\n` matches with the next non-blank line being
`## Completion Summary`; `parse_body_section(body, 'Status')` returns exactly `"DONE"` for this file.

---

### Step 3 — `tickets/done/TCK-20260619-E12-BALANCE-BASELINE.md`
**Files:** `tickets/done/TCK-20260619-E12-BALANCE-BASELINE.md`
**Change:** Trim Status; merge the `EPIC_SCOPED` context into the existing (currently
forward-looking, not completion-confirming) Completion Summary sentence.

Status — replace:
```
## Status
DONE (EPIC_SCOPED)
```
with:
```
## Status
DONE
```

Completion Summary — replace:
```
## Completion Summary
_Epic completes when E12A + E12B + E12C are all DONE._
```
with:
```
## Completion Summary
_Epic completes when E12A + E12B + E12C are all DONE._ This epic-scoped ticket closes now that all
three child tickets are complete.
```
**Do NOT touch:** Any other section of this file. Do not touch frontmatter.
**Verify:** Status regex match; `parse_body_section(body, 'Status')` returns `"DONE"`.

---

### Step 4 — `tickets/done/TCK-20260619-E62-CULTURE-DRIFT.md`
**Files:** `tickets/done/TCK-20260619-E62-CULTURE-DRIFT.md`
**Change:** Trim Status. The existing Completion Summary already names `EPIC_SCOPED` and lists all 4
child tickets by ID, but never states they are now complete — append one closing sentence to make
completion explicit (merge idiomatically, do not duplicate the existing child-ticket list).

Status — replace:
```
## Status
DONE (EPIC_SCOPED)
```
with:
```
## Status
DONE
```

Completion Summary — append this sentence as a new final line after the existing
"All three staging artifacts (investigation.md, plan.md, test_plan.md) migrated to
stored_artifacts/TCK-20260619-E62-CULTURE-DRIFT/." line (keep every existing line unchanged):
```
This epic-scoped ticket closes now that all four child tickets are complete.
```
**Do NOT touch:** The existing child-ticket list, dependency chain line, or prerequisites line — do
not rephrase or shorten them. Do not touch frontmatter.
**Verify:** Status regex match; `parse_body_section(body, 'Status')` returns `"DONE"`.

---

### Step 5 — `tickets/done/TCK-20260619-E63-FEATURE-PACKS.md`
**Files:** `tickets/done/TCK-20260619-E63-FEATURE-PACKS.md`
**Change:** Trim Status. Existing Completion Summary already opens with "All 4 child tickets DONE
(2026-06-23):" and itemizes each — append one closing sentence naming the epic-scoped nature
explicitly (the word "EPIC_SCOPED" itself does not currently appear anywhere in this file's body).

Status — replace:
```
## Status
DONE (EPIC_SCOPED)
```
with:
```
## Status
DONE
```

Completion Summary — append this sentence as a new final line after the existing
"45 tests pass across all child tickets." line (keep every existing line unchanged):
```
This epic-scoped ticket closes now that all four child tickets are done.
```
**Do NOT touch:** The 4-item child-ticket bullet list — do not rephrase or shorten it. Do not touch
frontmatter.
**Verify:** Status regex match; `parse_body_section(body, 'Status')` returns `"DONE"`.

---

### Step 6 — `tickets/done/TCK-20260628-E-NARRATIVE-CONSEQUENCE.md`
**Files:** `tickets/done/TCK-20260628-E-NARRATIVE-CONSEQUENCE.md`
**Change:** Trim Status. The trimmed tail names three child tickets by ID that are not currently named
anywhere in the existing Completion Summary (which only discusses acceptance criteria and parity
ledger entries) — append a sentence naming them, reworded from the Status tail's list form into a
sentence, not pasted verbatim.

Status — replace:
```
## Status
DONE — all 3 child tickets complete: E43F (grief urgency), E43G (nemesis relation), E43H (observability surface)
```
with:
```
## Status
DONE
```

Completion Summary — append this sentence as a new final line after the existing
"Parity ledger entries SOC-231 and SOC-232 added." line (keep every existing line unchanged):
```
All 3 child tickets are complete: E43F (grief urgency), E43G (nemesis relation), E43H (observability
surface).
```
**Do NOT touch:** The acceptance-criteria sentence or the parity ledger sentence already present. Do
not touch frontmatter.
**Verify:** Status regex match; `parse_body_section(body, 'Status')` returns `"DONE"`.

---

### Step 7 — `tickets/done/TCK-20260628-E-PARTY-LOOP.md`
**Files:** `tickets/done/TCK-20260628-E-PARTY-LOOP.md`
**Change:** Trim Status. Completion Summary section exists but is currently empty (header only, file
ends immediately after) — fill it with a single reworded sentence naming the three child tickets.
Investigation flags this file as `BLOCKED`/deferred-epic (`layer: simulation`, tags include
`blocked`, `deferred`) with a separate in-prose `**Status: BLOCKED pending ...**` sentence elsewhere
in the body (inside `## Request Summary`/prose text, not the `## Status` body section) — the new
Completion Summary sentence must state only the trimmed Status tail's literal content, and must not
imply or re-litigate that the epic's original BLOCKED gate conditions were resolved differently than
what the rest of the file already says.

Status — replace:
```
## Status
DONE (all child tickets complete: E41F, E41G, E41H)
```
with:
```
## Status
DONE
```

Completion Summary — replace:
```
## Completion Summary
```
(empty, nothing follows) with:
```
## Completion Summary
All child tickets are complete: E41F, E41G, E41H.
```
**Do NOT touch:** The `**Status: BLOCKED pending ...**` in-prose sentence inside `## Request Summary`
or elsewhere in the body — that is a different, unrelated occurrence of the word "Status" and is not
part of this ticket's scope. Do not add any narrative beyond the literal trimmed content (no new
claims about gate resolution). Do not touch frontmatter.
**Verify:** Status regex match; `parse_body_section(body, 'Status')` returns `"DONE"`.

---

### Step 8 — `tickets/done/TCK-20260628-E-PERSONALITY-CALIBRATION.md`
**Files:** `tickets/done/TCK-20260628-E-PERSONALITY-CALIBRATION.md`
**Change:** Trim Status. Completion Summary section exists but is currently empty (header only) —
fill it with a single reworded sentence naming the three child-ticket components. Same BLOCKED/
deferred-epic caution as Step 7 applies here (`layer: simulation`, tags include `blocked`,
`deferred`) — state only the trimmed Status tail's literal content.

Status — replace:
```
## Status
DONE (E11B audit + E11C weight-tuning + E11D abandonment-rate all complete)
```
with:
```
## Status
DONE
```

Completion Summary — replace:
```
## Completion Summary
```
(empty, nothing follows) with:
```
## Completion Summary
All child tickets are complete: E11B (audit), E11C (weight-tuning), E11D (abandonment-rate).
```
**Do NOT touch:** Any in-prose BLOCKED sentence elsewhere in the body. Do not add any narrative beyond
the literal trimmed content. Do not touch frontmatter.
**Verify:** Status regex match; `parse_body_section(body, 'Status')` returns `"DONE"`.

---

### Step 9 — `tickets/done/TCK-20260628-E-WORLD-EVOLUTION.md`
**Files:** `tickets/done/TCK-20260628-E-WORLD-EVOLUTION.md`
**Change:** Trim Status. Existing Completion Summary discusses acceptance criteria and parity ledger
entries (WORLD-105/106/107) but does not name the three child tickets by ID — append a sentence doing
so, reworded from the em-dash list form into a sentence.

Status — replace:
```
## Status
DONE — E52E (seasonal propagation), E52F (trauma motivation), E52G (sovereignty events)
```
with:
```
## Status
DONE
```

Completion Summary — append this sentence as a new final line after the existing
"Parity ledger entries WORLD-105, WORLD-106, WORLD-107 added." line (keep every existing line
unchanged):
```
All 3 child tickets are complete: E52E (seasonal propagation), E52F (trauma motivation), E52G
(sovereignty events).
```
**Do NOT touch:** The acceptance-criteria sentence or the parity ledger sentence already present. Do
not seek out or fix the "`## Tier\n## Tier` duplicate heading glitch" mentioned in prior work notes —
confirmed not present in this file's current content; do not go looking for it. Do not touch
frontmatter.
**Verify:** Status regex match; `parse_body_section(body, 'Status')` returns `"DONE"`.

---

### Step 10 — `tickets/done/TCK-20260701-SIMQ-EMIT-CAMP.md`
**Files:** `tickets/done/TCK-20260701-SIMQ-EMIT-CAMP.md`
**Change:** Trim Status only. The trimmed tail ("CLOSED, WRONG PREMISE") is already fully captured by
the existing Completion Summary's opening line ("**Closed — premise incorrect, no viable engine
path.**") — no new sentence is needed; adding one would duplicate existing content, which Scope
explicitly discourages ("merged into idiomatically rather than duplicated"). Confirm this at edit
time by re-reading the existing Completion Summary before concluding no addition is needed.

Status — replace:
```
## Status
DONE — CLOSED, WRONG PREMISE
```
with:
```
## Status
DONE
```
**Do NOT touch:** The Completion Summary body — leave it exactly as-is (no addition, no rewording of
existing text). Do not touch frontmatter.
**Verify:** Status regex match; `parse_body_section(body, 'Status')` returns `"DONE"`.

---

### Step 11 — `tickets/done/TCK-20260701-SIMQ-KERNEL-WIRE.md`
**Files:** `tickets/done/TCK-20260701-SIMQ-KERNEL-WIRE.md`
**Change:** Trim Status only. The trimmed tail ("DUPLICATE / CREATED IN ERROR") is already fully
captured by the existing Completion Summary's opening line ("**Ticket created in error.**") and
closing line ("Closing as duplicate.") — no new sentence is needed.

Status — replace:
```
## Status
DONE — DUPLICATE / CREATED IN ERROR
```
with:
```
## Status
DONE
```
**Do NOT touch:** The Completion Summary body — leave it exactly as-is. Do not touch frontmatter.
**Verify:** Status regex match; `parse_body_section(body, 'Status')` returns `"DONE"`.

---

### Step 12 — Record the status_drift_check.py go/defer decision
**Files:** `tickets/inprogress/TCK-20260718-STATUS-SUFFIX-TRIM.md` (`## Implementation Notes`
section only)
**Change:** Record the DEFER decision and its reasoning (as finalized above under "status_drift_
check.py Extend-vs-Defer Decision (Resolved)") into the ticket's own `## Implementation Notes`
section, satisfying AC6 ("The go/defer decision ... is explicitly recorded ... with reasoning,
regardless of which way it goes"). No change to `tools/gate_checks/status_drift_check.py`,
`tests/tools/test_status_drift_check.py`, or `docs/parity_ledger/infrastructure.yaml`.
**Do NOT touch:** `tools/gate_checks/status_drift_check.py`, `tests/tools/test_status_drift_check.py`,
`docs/parity_ledger/infrastructure.yaml` (`INFRA-277`) — all three stay byte-identical to their
pre-ticket state, per the DEFER decision. Do not add a new parity ledger entry either — INFRA-277's
existing text/v2_evidence is not falsified by a defer.
**Verify:** Manual read of the ticket's Implementation Notes section confirms the decision and
reasoning are present.

---

### Step 13 — Final verification pass
**Files:** none changed (read-only verification); optionally a one-off script at
`staging_artifacts/TCK-20260718-STATUS-SUFFIX-TRIM/scripts/verify_status_trim.py` per test_plan.md's
"New Tests Required" item 1/2 (not committed to `tests/`)
**Change:**
1. Re-run `tools/generate_registry.py`'s `parse_body_section(body, 'Status')` against all 10 files
   post-fix; confirm every one returns exactly `"DONE"` (AC3).
2. Confirm the exact-match regex `^## Status\s*\n+\s*DONE\s*\n` (next content is the next `## `
   heading or EOF, no other non-whitespace text in the section) against all 10 files (AC1).
3. Run `python3 tools/gate_checks/status_drift_check.py` and confirm it still reports `PASS` for
   `check_ticket_status_drift` (AC4) — expected to be trivially true since `TICKET_STATUS_RE`'s
   first-token capture already saw `DONE` for all 10 files before this ticket's edits.
4. Run `git diff --stat tickets/done/` and confirm exactly the 10 named files are listed, no other
   file appears (AC5, part 1).
5. Per-file: run `git diff tickets/done/<file>.md` for each of the 10 files and confirm the diff hunk
   never touches the `---...---` frontmatter block (AC5, part 2).
6. Run the scoped pytest commands from test_plan.md:
   `pytest tests/tools/test_status_drift_check.py tests/tools/test_validate_frontmatter.py -v`
   (and `tests/tools/test_generate_registry.py -v` if that file exists — confirm existence first).
   All must pass unchanged (no test file is modified under the DEFER decision).
7. `grep -rn "workflow_status" tests/` to confirm no test asserts one of these 10 files' old
   fragmented `workflow_status` string as a fixture expectation (test_plan.md's flagged
   not-exhaustively-verified check) — update only if such an assertion is found, and only to reflect
   the new `"DONE"` value (do not touch unrelated assertions in that test file).
**Do NOT touch:** Any file outside the 10-file list, `tools/generate_registry.py`,
`src/api/agent_ops_dashboard/ingest.py`, `dashboard-frontend/`, `tools/gate_checks/status_drift_check.py`.
**Verify:** All 7 checks above pass. This step is the final gate before moving the ticket to
`tickets/done/`.

## Scope Guards

Explicit list of things this plan must not touch (from the ticket's Out of Scope and the
investigation's Anti-Drift Hazards):

- The 6 same-line colon-suffixed `## Status: X` files already excluded by the predecessor ticket's
  "Colon-Suffixed Files Decision" (`TCK-20260322-BWS_PROTO.md`, `TCK-20260401-FINAL-CONVERGENCE.md`,
  `TCK-20260401-FINAL-NON-PARTIAL-TASKS.md`, `TCK-20260403-FINAL-CONVERGENCE.md`,
  `TCK-20260405-SKILL-SCALING.md`, `TCK-20260407-PH0-FIX.md`) — disjoint set, not touched.
- Any `tickets/done/*.md` file whose `## Status` first token is genuinely wrong
  (OPEN/INPROGRESS stale) — already closed by `TCK-20260718-STATUS-DRIFT-REPAIR`, not this ticket's
  concern.
- Any `tickets/done/*.md` file not in the frozen 10-file list from Step 1 — do not re-scan
  `tickets/done/` or expand the list mid-implementation, even if a file superficially resembles this
  defect class.
- `src/api/agent_ops_dashboard/ingest.py`, any file under `dashboard-frontend/`, and
  `tools/generate_registry.py`'s `parse_body_section()` — the approved fix is data normalization
  only; the parser's "capture everything to the next heading" behavior stays unchanged.
- The `## Tier\n## Tier` duplicate-heading glitch noted by the predecessor's plan for
  `E-NARRATIVE-CONSEQUENCE.md` / `E-WORLD-EVOLUTION.md` — confirmed not present in current content;
  do not go looking for it.
- Restructuring `TCK-20260408-PH3-STG1-HOUSEHOLD.md` (or any other legacy/old-format ticket) up to
  the full current 12-section format — Step 2 adds only the single minimal `## Completion Summary`
  section, nothing more.
- `tools/gate_checks/status_drift_check.py`, `tests/tools/test_status_drift_check.py`,
  `docs/parity_ledger/infrastructure.yaml` — DEFER decision means zero code change to any of these in
  this ticket (Step 12 records the decision in the ticket file only).
- Frontmatter of any of the 10 files — no field on any file's frontmatter block changes.
- The in-prose `**Status: BLOCKED pending ...**` sentences inside `## Request Summary` in
  `E-PARTY-LOOP.md` and `E-PERSONALITY-CALIBRATION.md` — distinct from the `## Status` body section
  being trimmed; not touched.
- Verbatim-pasting any trimmed parenthetical/clause into Completion Summary — every addition in
  Steps 3–9 is a reworded sentence, never a direct copy of the Status tail text.

## Dependency Map

- Step 1 must complete before Steps 2–11 (edits must be based on a confirmed, non-stale snapshot).
- Steps 2–11 are mutually independent — each touches exactly one distinct file and can be done, and
  verified, in any order or in parallel.
- Step 12 is independent of Steps 2–11 (it edits a different file — the ticket itself — and records
  a decision that does not depend on the data-fix edits landing first), but is logically grouped after
  them for narrative flow.
- Step 13 depends on Steps 2–11 (all data edits) and benefits from Step 12 being done (so the final
  Implementation Notes check has content to verify), and must run last as the closing verification
  gate.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| All 10 files' `## Status` reads exactly `DONE`, matching `^## Status\s*\n+\s*DONE\s*\n` | Steps 2–11 | Step 13 item 2 (regex check); `verify_status_trim.py` |
| None of the 10 files' descriptive context silently dropped (reworded in Completion Summary / minimal legacy section) | Steps 2–11 | Manual diff review per step; Step 13 item 1 (content presence spot-check) |
| `parse_body_section(body, 'Status')` returns exactly `"DONE"` for all 10 files | Steps 2–11 (produce the state) | Step 13 item 1 |
| `status_drift_check.py` continues to report PASS for `check_ticket_status_drift` | Steps 2–11 (no first-token change), Step 12 (no code change) | Step 13 item 3; `pytest tests/tools/test_status_drift_check.py` |
| `git diff --stat tickets/done/` shows exactly the 10 named files, no frontmatter modified | Steps 2–11 (discipline per step) | Step 13 items 4–5 |
| go/defer decision on `status_drift_check.py` explicitly recorded with reasoning | Step 12 | Manual read of Implementation Notes |
| (Conditional) If "extend now": pytest coverage + INFRA-277 update | Not applicable — decision is DEFER | N/A |

## Anti-Drift Notes

- **Regex/AC precision**: after each edit, the line immediately following `DONE` must be either a
  blank line leading straight into the next `## ` heading or EOF — no stray whitespace-only line, no
  reintroduced parenthetical anywhere in the `## Status` section. Preserve each file's existing
  blank-line convention between sections; do not standardize spacing differently across the 10 files.
- **Verbatim-paste hazard**: Steps 3, 4, 5, 6, 9 add a *reworded* sentence, not a copy of the Status
  tail. Double-check each addition reads as a natural sentence, not the bracketed/em-dash fragment
  moved as-is.
- **Steps 10 and 11 intentionally add nothing** to Completion Summary — the trimmed context is already
  present in existing prose. Do not add a redundant sentence here; that would violate the "merged
  ... rather than duplicated" instruction.
- **BLOCKED/deferred-epic caution (Steps 7, 8)**: `E-PARTY-LOOP.md` and `E-PERSONALITY-CALIBRATION.md`
  carry `blocked`/`deferred` tags and contain an unrelated in-prose BLOCKED sentence elsewhere in the
  body. The new Completion Summary sentence must state only the trimmed Status tail's literal content
  — do not invent or imply resolution of the epic's original gate conditions.
  frontmatter `layer` values intentionally vary across the 10 files (`misc`, `simulation` ×3,
  `world` ×2, `architecture`, `observability` ×2) — do not homogenize them as a drive-by fix.
- **Legacy file (Step 2)**: only one new section (`## Completion Summary`) is added to
  `TCK-20260408-PH3-STG1-HOUSEHOLD.md` — resist any urge to add the other 6 standard-format sections
  "for consistency."
- **Do not re-derive the 10-file list.** The list frozen in Step 1 (matching the ticket's Related Code
  Areas) is authoritative for the entire implementation — do not re-scan `tickets/done/` at any point.
