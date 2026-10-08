---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-RECORD-ICON-OWNER-FIXES-ADOPTION
artifact_type: plan
tags: [architecture, testing, documentation]
---

# Plan

1. Commit the owner's 7 adoptions (adoption records, intake provenance, r0002 sources) byte for byte.
2. Re-point guards by equality in `adopted_facts.py` (ADOPTION_COUNT 77, INTAKE_FILE_COUNT 154, REVISION_COUNT 77, ICON_FIX_* facts) and fix the sites that counted adoptions or revisions.
3. New `test_icon_owner_fixes_adoption.py`.
4. Move the README decisions and findings into `visual_assets/icons/owner_fixes_decisions.yaml`, read by the generator; make the README adoption-aware.
5. Review doc, handoff snapshots, SEQUENCE; close folder; PR #418 body.
