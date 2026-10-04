---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-PLAN-GATE-NONE-BODY-MARKDOWN-EMPHASIS-FALSE-POSITIVE
phase: open
date: 2026-10-04
tags: [ai, process-improvement]
---

# TCK-20261004-PLAN-GATE-NONE-BODY-MARKDOWN-EMPHASIS-FALSE-POSITIVE

## Title
`plan_gate_static` reads a bolded "**None.**" Unresolved Questions body as open

## Status
INPROGRESS

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Reported by `rpg-feature-planning` and verified here (2026-10-04): `_NONE_BODY_RE = re.compile(r"^none\b", re.IGNORECASE)` in `tools/gate_checks/plan_gate_static.py` is matched against the section body's first non-blank line, so a leading markdown marker defeats it. Measured with the real regex: `None.` matches; `**None.**`, `_None_`, `` `None` `` and `- None` do not. The gate then reports a resolved section as open and the Plan phase returns a false NEEDS_HUMAN_INPUT. Same bug class as `TCK-20260716`, `TCK-20260827` and `TCK-20260930` (the last one a false negative on a heading suffix that let real open decisions through), now in the body matcher.

## Scope
- Normalise the first non-blank body line before matching: strip leading markdown emphasis, code and list markers (`*`, `_`, backtick, `-`, `+`, `>` and spaces), via a small named helper. Do not broaden the regex and do not match "none" anywhere in the line: the word-boundary rule stays ("Nonetheless" must still read as open).
- Check the same normalisation need in any sibling matcher in the module that tests a body line.
- Tests in `tests/tools/test_plan_gate_static.py`: `**None.**`, `_None_`, `` `None` ``, `- None`, `* None`, `None.` read resolved; `Nonetheless, ...`, `**Nonetheless**`, `- Which owner decides X?` stay open.

## Out of Scope
- Editing the planner prompt, relaxing the heading rules, any change to plans to clear a gate.

## Acceptance Criteria
1. Every "resolved" form above returns resolved and every "open" form still returns open.
2. A body that is genuinely open is still caught (regression from `TCK-20260930` stays green).
3. Scoped tests (`tests/tools/test_plan_gate_static.py`) green.

## Related Tickets
- `TCK-20260716`, `TCK-20260827`, `TCK-20260930` (earlier rounds of this class, per the module docstring)

## Related Docs
- `tools/gate_checks/plan_gate_static.py` (module docstring)

## Related Stored Artifacts
- none

## Related Code Areas
- `tools/gate_checks/plan_gate_static.py`, `tests/tools/test_plan_gate_static.py`

## Assumptions / Open Questions
- Existing behaviour (docstring): any body starting with the word "None", with or without explanation, reads resolved. The normalisation must not change that for plain text, so `**None of the options fits**` reads resolved exactly as `None of the options fits` does today; do not tighten that here.

## Implementation Notes
Draft by `agent-working-design`, 2026-10-04, from a relayed and verified report. Activated and implemented by the implementer 2026-10-04. `_strip_markup` strips ` \t*_`-+>` from both ends of the first body line before the unchanged `^none\b` match (both ends because a trailing `_` is a word character, so `_None_` has no boundary after `None`). The loop in `plan_has_unresolved_questions_heading` is the module's only body matcher, so no sibling needed the change.

## Test Summary
`tests/tools/test_plan_gate_static.py`: 33 pass, including 10 parametrised cases (6 resolved forms, `**None of the options fits**`, `Nonetheless`, `**Nonetheless**`, `- Which owner decides X?` stay open).

## Files Changed
- `tools/gate_checks/plan_gate_static.py`
- `tests/tools/test_plan_gate_static.py`

## Completion Summary
Fixed and tested; not yet closed (ticket stays in inprogress until the bundle PR closes it).
