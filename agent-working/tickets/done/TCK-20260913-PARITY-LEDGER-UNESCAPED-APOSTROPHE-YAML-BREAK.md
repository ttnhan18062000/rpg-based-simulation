---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260913-PARITY-LEDGER-UNESCAPED-APOSTROPHE-YAML-BREAK
phase: done
date: 2026-09-13
tags: [testing]
---

# TCK-20260913-PARITY-LEDGER-UNESCAPED-APOSTROPHE-YAML-BREAK

## Title
`docs/parity_ledger/social_narrative.yaml` failed to parse — an edit to `SOC-272`'s `v2_evidence` field introduced an unescaped apostrophe inside a single-quoted YAML scalar

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
Real CI regression caught on PR #175 (`worker-utilization-degraded-mistrigger-batch`) in the
`API / tools / logging` job. Real logs (annotation: "Process completed with exit code 1") plus a
local reproduction of the exact CI command showed 11 real failures, all in
`tests/tools/test_parity_index.py`/`test_parity_index_baseline.py`/`test_parity_ledger_scan.py`,
each failing with the same root error:

```
yaml.scanner.ScannerError: while parsing a block mapping
  in "docs/parity_ledger/social_narrative.yaml", line 4107, column 3
expected <block end>, but found '<scalar>'
  in "docs/parity_ledger/social_narrative.yaml", line 4140, column 73
```

`SOC-272`'s `v2_evidence` field is a single-quoted YAML scalar. This repo's own convention within
that field (confirmed by reading the surrounding, pre-existing text — `apply.py''s`, `SOC-134''s`)
escapes every literal apostrophe as `''` (doubled single-quote), per YAML's own single-quoted
scalar rules. An edit made under `TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION`
(correcting this same entry's stale reachability claim) inserted the text "(this entry's own
subject)" with a single, unescaped apostrophe — YAML read this as the end of the quoted string,
treating everything after it as unexpected trailing content in the surrounding block mapping.

**First theory tried and ruled out, not guessed past**: initially suspected a colon-at-end-of-line
inside the same edited passage (`...DETERMINATION):` followed by a newline) as the cause, since
that is a real YAML plain-scalar hazard. Fixed that (replaced the colon with `--`) and re-validated
with `yaml.safe_load()` directly — the error persisted at the identical location, disproving that
theory before committing to it. Re-read the surrounding text for the file's own established
apostrophe-escaping convention, found the real single-apostrophe instance, fixed it, and confirmed
`yaml.safe_load()` succeeds (294 entries parsed) before considering it resolved.

## Scope
- Fix the one unescaped apostrophe (`entry's` -> `entry''s`) in `SOC-272`'s `v2_evidence` field.
- Re-validate the full file parses via `yaml.safe_load()` directly (not just trusting the
  downstream test suite) and scan the rest of the edited passage for any other unescaped
  apostrophes before considering this closed.

## Out of Scope
- Re-litigating `TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION`'s own content/decision
  — the substance of that edit is correct; this ticket only fixes the syntax break it introduced.
- A general audit of every other parity-ledger YAML file for the same class of error — not
  evidenced as a broader problem here, and out of this hotfix's narrow scope.

## Acceptance Criteria
- [x] `docs/parity_ledger/social_narrative.yaml` parses cleanly via direct `yaml.safe_load()`.
- [x] The specific edited passage scanned for any other unescaped apostrophes — none found.
- [x] `tests/tools/test_parity_index.py`, `test_parity_index_baseline.py`,
      `test_parity_ledger_scan.py` pass (61/61).
- [x] Full `API / tools / logging` CI job command re-run locally to confirm no other regression.

## Related Tickets
- `TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION` (the edit that introduced this —
  correct content, incomplete verification: the edit was validated by re-reading the doc for
  sense, not by directly parsing the YAML it lives in)

## Related Docs
- `docs/parity_ledger/social_narrative.yaml`

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
None (docs-only fix).

## Assumptions / Open Questions
None.

## Implementation Notes
Caught during CI Failure Triage on PR #175 — pulled the real check-run annotation and reproduced
the exact CI job command locally (`pytest tests/api tests/cli tests/tools tests/logging
tests/engine tests/observability -m "not slow and not extra_slow"`) rather than assuming root
cause. The failure's own traceback pointed directly at the YAML file and line range; ran
`yaml.safe_load()` directly against the file to isolate the parse error from the higher-level test
logic. First fix attempt (the colon theory) was verified wrong via the same direct
`yaml.safe_load()` check before moving on, rather than assuming it worked because it looked
plausible. Second, correct fix (the unescaped apostrophe) verified the same way.

**Standing lesson for future edits to any single-quoted block scalar in this file**: this repo's
own convention already handles this correctly elsewhere (`apply.py''s`, `SOC-134''s`) — any new
prose inserted into an existing single-quoted `text:`/`v2_evidence:` field must double every
literal apostrophe, and the fastest way to catch a mistake is a direct `python3 -c "import yaml;
yaml.safe_load(open('docs/parity_ledger/<file>.yaml'))"` check immediately after editing, before
trusting a downstream tool's silence as confirmation (`validate_frontmatter.py`,
`generate_registry.py`, and the knowledge-index build all ran clean after the original edit
without ever loading this file's own YAML content, so their silence was not evidence of
correctness here).

## Test Summary
- `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/social_narrative.yaml'))"` —
  passes, 294 entries.
- `pytest tests/tools/test_parity_index.py tests/tools/test_parity_index_baseline.py
  tests/tools/test_parity_ledger_scan.py -q` — 61 passed (was 11 failed before the fix).
- `pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not
  slow and not extra_slow" -q` — full local re-run of the exact CI job command, confirmed clean.

## Files Changed
- `docs/parity_ledger/social_narrative.yaml` — one unescaped apostrophe fixed
  (`entry's` -> `entry''s`); one colon-before-newline also replaced with `--` during triage
  (harmless either way, kept for readability, not the actual fix).

## Completion Summary
A real, self-caused YAML syntax break in the parity ledger, caught by real CI and root-caused via
direct `yaml.safe_load()` isolation rather than guessing from the test failure's higher-level
symptoms. One wrong theory was tested and ruled out before the real cause was found and fixed.
