---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261019-VISUAL-ASSETS-ICON-SPRITES-SOURCE-IS-R0001
artifact_type: test_plan
tags: [architecture, testing]
---

# Test plan

- Pin test (new, read-only): accessor == store artifacts for 36 keys; revisions r0002 x7 / r0001 x29; permanent negative test: drop one revision from the overlay (`icon.item.tool`) and the shared comparison helper reports exactly that key; key coverage over all 65 store icon sources (36 + excluded 18 object + 11 entity) with three failure cases; the Test Summary also shows the failure output. No lock, no write, no build, no subprocess.
- Existing icon tests (`test_icon_compliance`, `test_icon_lookalikes`, `test_icon_recognition`, `test_icon_silhouette_sheet`, `test_icon_owner_fixes_draft_set`, `test_icon_sets_review_cli`-style review tests) stay green; the rename must not change any R1 site's value.
- Entity-marker sheet test (if any) unchanged output.
- Static: `grep -rn all_icon_sprites` matches exactly the one stored-artifact script (ICON-THEME-FIT/drawing/fix.py), nothing else.
- Guarded-set check after the repoint edits; paths guard; then slots (a) and (b) with lead's GO.

## Proof Plan
| criterion | proof |
|---|---|
| every call site classified | investigation.md table vs `grep -c` |
| one accessor, NOW sites use it | grep + the pin test |
| pin fails when a revision is dropped | the negative test output in the Test Summary |
| no guarded file | the guarded-set check after the edits |
| scope | `git diff --stat origin/main...HEAD` |
