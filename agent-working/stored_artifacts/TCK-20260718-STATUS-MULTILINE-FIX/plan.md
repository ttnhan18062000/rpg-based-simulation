---
artifact_type: plan
ticket_id: TCK-20260718-STATUS-MULTILINE-FIX
date: 2026-07-18
---

# Implementation Plan — TCK-20260718-STATUS-MULTILINE-FIX

## Summary

Fix three classes of `tickets/done/*.md` body `## Status` fragmentation the two predecessor
tickets' first-token-only regex missed, by using the actual dashboard extraction function
(`parse_body_section`) to find and verify every fix. Also rewrite
`tools/gate_checks/status_drift_check.py` to call that same function directly, closing the gap
that let these three classes go undetected in the first place.

## Steps

### Step 1 — Class A: delete stray `INPROGRESS` lines (3 files)
Files: `TCK-20260504-CORE-TEST-STABILIZATION.md`, `TCK-20260506-TOWN-TEST-STABILIZATION.md`,
`TCK-20260507-TEST-BASE-REWORK.md`. Mechanical single-line deletion each, verified via a Python
`re.sub` with an `assert new != text` guard per file (fails loudly if the expected pattern isn't
found, rather than silently no-op'ing).

### Step 2 — Class B: convert bold Tier/Type/Priority block to headings (11 files)
Verified byte-identical trailing text across all 11 files first. Applied
`str.endswith(old_block)` assertion per file before transforming — any file whose trailing text
didn't match exactly would raise, not silently corrupt. Converts:
```
**Tier:** standard
**Type:** chore
**Priority:** P1
```
to:
```
## Tier
standard

## Type
chore

## Priority
P1
```

### Step 3 — Class C: normalize the one true drift found (1 file)
`TCK-20260628-E-RESOURCE-ECOLOGY.md` — full-file read revealed this ticket is actually complete
(its own Completion Summary confirms), not merely scoped like its 6 EPIC_SCOPED siblings. Fixed
`## Status` to `DONE` and frontmatter `phase: scoped` → `phase: done` (deviation from the literal
"normalize to EPIC_SCOPED" instruction — see investigation.md's Class C section for full
reasoning).

### Step 4 — Regenerate `docs/REGISTRY.yaml`
Step 2's fix makes `Tier`/`Type` newly parseable for those 11 files via
`generate_registry.py::collect_tickets()`, which also uses `parse_body_section`. Regenerated via
`python3 tools/generate_registry.py --output docs/REGISTRY.yaml` after confirming
`test_check_flag_detects_no_drift_against_real_registry` failed pre-regeneration (proving the
drift was real) and passed after.

### Step 5 — Rewrite `status_drift_check.py`'s extraction to use `parse_body_section` directly
Removed the first-token-only `TICKET_STATUS_RE` regex; import and call
`tools.generate_registry.parse_body_section`/`_strip_frontmatter` instead. Verified the existing
colon-format-skip behavior (`## Status: X` same-line format resolving to `""`) is preserved
identically under the new extraction — both the old regex and the real function require a newline
directly after the heading before capturing a value, so same-line colon format still isn't
matched by either. Updated `tests/tools/test_status_drift_check.py`: removed the now-obsolete
pinned-regex test (`test_regex_matches_baseline_scan_pattern`), added 4 new tests proving the
rewritten checker now actually catches Class A/B shapes and still passes clean multi-section
files.

### Step 6 — Full verification
- All 12 original `test_status_drift_check.py` tests still pass unmodified (colon-format skip,
  epic-tier exemption, legacy-naming exemption, CLI contract, read-only guard, etc.).
- 4 new tests added and passing.
- `check_status_drift()` run live against the current corpus: 0 findings (both scans PASS).
- `validate_frontmatter.py --content-type ticket` passes on all 15 touched files.
- `test_generate_registry.py`'s drift-detection test passes after regeneration.
- Full `tests/tools/test_generate_registry.py` + `test_validate_frontmatter.py` +
  `test_status_drift_check.py` suite: 149/149 passing.

## Scope Guards

- Do NOT touch `dashboard-frontend/` or `src/api/agent_ops_dashboard/` — the user has chosen to
  normalize ticket data, not change the parser (this constraint carried over from the two
  predecessor tickets).
- Do NOT re-audit or fix the 78 tickets found (in a prior, separate investigation) to resolve to
  an empty `workflow_status` — out of scope, flagged as a future candidate only.
- Do NOT revisit the same-line colon-suffixed `## Status: X` exclusion (12 files, 6 non-`DONE`) —
  TCK-20260718-STATUS-DRIFT-REPAIR's original scope decision stands.
- Do NOT attempt a broader modernization of the 11 Class B legacy-format files (no remapping
  `Description` → `Request Summary`, no adding missing `## Title`/`## Completion Summary`
  sections) — only the Tier/Type/Priority heading conversion, nothing else.
- Do NOT touch the stale `**Status: BLOCKED...**` prose sentence inside
  `TCK-20260628-E-RESOURCE-ECOLOGY.md`'s `## Request Summary` — not a structured field the
  dashboard reads, out of this ticket's scope.

## Dependency Map

Steps 1-3 are independent of each other (different file sets, no shared state). Step 4 depends on
Step 2 (only Step 2 changes registry-relevant fields). Step 5 is independent of Steps 1-4 (checker
code vs. ticket data) but was verified against the Step 1-3 fixes as live-corpus proof. Step 6
depends on all prior steps.

## Acceptance Criteria Map

| AC | Step |
|---|---|
| Class A files' Status resolves to bare `DONE` via the real dashboard parser | Step 1, verified Step 6 |
| Class B files' Status resolves to bare `DONE`, Tier/Type/Priority independently parseable | Step 2, verified Step 6 |
| Class C file's Status accurately reflects its actual (complete) state | Step 3, verified Step 6 |
| `docs/REGISTRY.yaml` reflects newly-parseable Tier/Type fields | Step 4 |
| `status_drift_check.py` would now catch all three classes if they recurred | Step 5, verified via new tests |
| No regression in existing checker/registry/frontmatter test coverage | Step 6 |

## Anti-Drift Notes

- This ticket found and fixed a **second-order bug**: the very checker introduced to prevent
  status drift (`status_drift_check.py`) was itself insufficiently rigorous (regex-based
  first-token capture vs. the real multi-line-capturing dashboard function), and this gap was
  discovered twice in a row across two independent follow-up tickets. The Step 5 rewrite closes
  this permanently by construction (same extraction function, not a parallel reimplementation)
  rather than adding a fifth regex for a fifth future shape.
- Deviated from the literal request for Class C (normalize to `EPIC_SCOPED`) after full-file
  reading revealed the ticket was actually complete, not merely scoped — documented in
  investigation.md rather than silently following an instruction contradicted by the file's own
  content.
