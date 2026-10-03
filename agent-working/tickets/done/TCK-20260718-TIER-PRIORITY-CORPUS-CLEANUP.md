---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260718-TIER-PRIORITY-CORPUS-CLEANUP
phase: done
date: 2026-07-18
tags: [data-quality]
---

# TCK-20260718-TIER-PRIORITY-CORPUS-CLEANUP

## Title
Re-scan the full ticket corpus for Tier/Priority drift and fix everything found

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
The user explicitly asked for a full corpus re-validation, not just fixing
the 2 already-known `"P1: High"` cases: "maybe we should maintain a list of
attribute that applied to the tickets (Tier, Layer) stored somewhere and
checked as hard-rule... Also, maybe we should also re-scan the full corpus."
Using the canonical `TIER_VALUES`/`PRIORITY_VALUES` and the check function
built by TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM (a hard dependency — this
ticket cannot start until that one lands), scan `tickets/done/`,
`tickets/inprogress/`, and `tickets/todos/` for every Tier/Priority value
that doesn't match the canonical set, and fix each one — following this
session's established investigation discipline
(TCK-20260718-STATUS-DRIFT-REPAIR/-SUFFIX-TRIM/-MULTILINE-FIX all found that
blindly overwriting drifted values without reading the actual file first
either lost context or, in one case, revealed the "drift" was actually a
different, real bug). A preliminary ad-hoc scan (not using the real
canonical-enum machinery, just a quick corpus grep) found 2 `"P1: High"`
tickets and zero Tier drift — but this ticket must re-run the scan using the
actual shipped check function once it exists, not trust that preliminary
number, since the real check may have different extraction semantics
(multi-line body sections, colon-suffixed formats, etc. — exactly the kind
of gap the STATUS-MULTILINE-FIX ticket found when its predecessor's
first-token-only regex missed real drift a first naive scan didn't catch).

## Scope
- Run the real `TIER_VALUES`/`PRIORITY_VALUES` check function (from
  TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM) against the full corpus.
- For every finding: read the actual file, determine the correct fix (a
  straightforward typo/format fix like `"P1: High"` -> `P1`; a genuinely
  different bug in disguise, per the `TCK-20260628-E-RESOURCE-ECOLOGY`
  precedent from STATUS-MULTILINE-FIX; or a legitimate exemption, per the
  pre-TCK-naming legacy-file precedent from STATUS-DRIFT-REPAIR) — apply
  judgment per-file, do not blindly regex-replace across the whole set.
- Document any exemptions found with the same rigor as prior tickets
  (value-based/pattern-based, never a hardcoded filename list, so future
  legitimate cases stay correctly exempt without a checker update).
- Confirm zero remaining findings via the real check function, independently
  re-run (not just trusted from a prior tool call's stdout).

## Out of Scope
- The check function's own implementation/design — that is
  TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM, a hard prerequisite.
- Any Status/Layer drift — already fully handled by prior tickets this
  session; this ticket is Tier/Priority only.
- Dashboard-facet changes.

## Acceptance Criteria
- [ ] The real canonical-enum check function (not an ad-hoc script) is run
      against the full corpus and its output is the basis for scope, not
      the preliminary 2-file estimate in this ticket's Request Summary.
- [ ] Every finding is either fixed (with the fix's reasoning documented) or
      explicitly, narrowly exempted (with reasoning documented) — no
      finding is silently ignored.
- [ ] A live re-run of the check function after all fixes land shows zero
      remaining findings, independently confirmed (run it yourself, don't
      just trust the implementer's report).
- [ ] Existing test suites remain green; any ticket file touched still
      passes `tools/validate_frontmatter.py` frontmatter validation.

## Related Tickets
- Parent epic: TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC
- Depends on: TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM
- Prior art: TCK-20260718-STATUS-DRIFT-REPAIR, TCK-20260718-STATUS-SUFFIX-TRIM,
  TCK-20260718-STATUS-MULTILINE-FIX (same investigation discipline expected)

## Related Docs
- docs/plans/agent_ops_dashboard/proposal_canonical_ticket_field_enums.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tickets/done/**/*.md (any file the real check function flags)
- tickets/inprogress/**/*.md
- tickets/todos/**/*.md

## Assumptions / Open Questions
- The exact set of drifted files is unknown until TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM's
  check function actually exists and is run — this ticket's Scope is
  process-defined (how to investigate/fix), not a frozen file list.

## Implementation Notes

Same execution-context deviation as the rest of this epic (no Agent tool
access — every phase executed directly, self-flagged per this session's
established precedent). Ran the real (not ad-hoc)
`tools/ticket_field_values.py::check_ticket_field_values` — shipped by the
now-DONE prerequisite ticket — against every `*.md` file under
`tickets/done/`, `tickets/inprogress/`, `tickets/todos/`. Found exactly the
2 already-known `"P1: High"` cases, nothing more:
`tickets/done/TCK-20260326-HYSTERESIS.md`,
`tickets/done/TCK-20260326-NARRATIVE.md`. Both are same-era (2026-03-26)
pre-standard-format sub-tickets with no `## Tier` heading at all — the check
function's "absent section = PASS" design (chosen during the prerequisite
ticket) correctly did not flag this as drift, avoiding forcing a modern
`## Tier` heading onto genuinely older files. Fixed both `## Priority`
values from `P1: High` to `P1` — a one-line body-text edit each, nothing
else in either file touched. `TCK-20260326-NARRATIVE.md`'s same-line
colon-suffixed `## Status: DONE` was left alone, per the existing, already-
documented deferral from `TCK-20260718-STATUS-DRIFT-REPAIR`.

## Test Summary

- `python3 -m pytest tests/tools/test_ticket_field_values.py -q` — 8/8
  passing (unaffected by this ticket, confirms no regression).
- `python3 tools/validate_frontmatter.py --content-type ticket
  tickets/done/TCK-20260326-HYSTERESIS.md` /
  `tickets/done/TCK-20260326-NARRATIVE.md` — both `OK: no violations`.
- **Live corpus re-scan** (the actual proof this ticket's ACs require): ran
  `check_ticket_field_values` against every file in
  `tickets/{done,inprogress,todos}/` — **0 remaining findings**,
  independently re-confirmed after the fix (not just trusted from the
  pre-fix scan).

## Files Changed
- tickets/done/TCK-20260326-HYSTERESIS.md (`## Priority`: `P1: High` → `P1`)
- tickets/done/TCK-20260326-NARRATIVE.md (`## Priority`: `P1: High` → `P1`)

## Completion Summary
All acceptance criteria met: the real canonical-enum check function (not a
preliminary estimate) was the basis for scope; it found exactly 2 findings,
both fixed with reasoning documented (a genuine typo-style drift, not a
disguised different bug this time — unlike the `TCK-20260628-E-RESOURCE-
ECOLOGY` precedent from `STATUS-MULTILINE-FIX`); the missing `## Tier`
heading on both files was investigated and correctly left alone as a
structural, pre-dating-the-field exemption rather than retrofitted; a live
post-fix re-scan independently confirms 0 remaining findings. No `src/` file
touched, no behavior change — Parity phase is skip-eligible per this
session's established `parityNoSrcChange && !behavior_changed` pattern.
