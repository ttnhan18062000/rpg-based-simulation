---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES
artifact_type: test_plan
tags: [architecture, testing, hud]
---

# Test plan — TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES

- `test_icon_silhouette_sheet.py` (proposals well-formed, committed sheet equals a fresh build, numbers are the rule's own), `test_icon_owner_fixes_draft_set.py` (six revisions, distinct draft source ids, adopted slots, silhouettes equal the approved rows, spec rows met, adopted icons untouched, fixture equals a fresh export, flipped byte caught), `test_icon_compliance.py` (planted defects fail their own rows), `test_icon_specs.py` (revision status; the sword the only blade), frontend `IconHarness.test.tsx` (silhouette sheet, before/after table, recorded result), `isolation.test.ts` (PNG count 191).
- Mutants A to D (mutant_proof.txt).
