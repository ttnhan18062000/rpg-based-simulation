---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260820-SCRIPTS-TOOLS-GOVERNANCE-EPIC
artifact_type: investigation
tags: [ai, process-improvement]
---

# Investigation — TCK-20260820-SCRIPTS-TOOLS-GOVERNANCE-EPIC

## Origin
User question this session: "what is the different between scripts/ and tools/, are they contain
unused?" — investigated via direct cross-reference search (Makefile, `.github/workflows/`,
`tests/`, `tools/`, `scripts/`, `docs/`), not assumption. Full findings, evidence, and numbers are
in `docs/plans/scripts_tools_governance_epic.md`'s Problem section — this file is the pointer, not
a duplicate.

## Summary of evidence
- No documented rule exists anywhere for `scripts/` vs. `tools/` — the distinction found is
  inferred from content pattern, not stated.
- `tools/`: 2 of 52 top-level files orphaned (zero live references).
- `scripts/`: 6 of 28 files orphaned; only 2 of 28 even appear in the Makefile.
- No standing mechanism catches this drift going forward.

## Related
- `docs/plans/scripts_tools_governance_epic.md` (full findings)
