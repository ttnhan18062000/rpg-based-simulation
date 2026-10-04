---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-FALLBACK-SAFETY-FRAMEWORK
phase: done
date: 2026-10-04
tags: [architecture, documentation, live-map]
---

# TCK-20261004-VISUAL-ASSETS-FALLBACK-SAFETY-FRAMEWORK

## Title
`AM1-W06` fallback-safety framework: what each role must still show when its image fails, written from the built terrain behaviour

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Child 2 of `TCK-20261004-EPIC-VISUAL-ASSET-M1-CONTRACTS`. `AM1-W06` asks for safety classes that define the preserved
information, the allowed primitive/text/HUD alternatives, and the activation/runtime failure policy. The built system
already has one answer for terrain (flat fill per terrain code, typed `?` fallback for unknown keys, recall shows the
flat fill), but it is spread over tests and result docs and has no general rule for the next kinds.

## Scope
- New `docs/assets/fallback_safety.md`, status line `PROPOSED` (the planner asks the owner a blocking question to
  approve it at review; on a yes it becomes `APPROVED <date>`).
- **Safety classes**, small: at most three, e.g. `decorative` (may vanish), `identifying` (the fact the image carries
  must survive, e.g. "this cell is forest"), `critical` (a fact whose loss misleads play or safety, needs text/HUD
  redundancy). Each: preserved information, allowed alternatives, what "fail" means.
- **Terrain as built**: map the current behaviour onto the classes, with evidence (the resolver/fallback code in
  `frontend/src/visualAssets/`, `rollbackDrill.test.ts`, the detail fallback order missing variant -> default -> role
  fallback). Detail variants are `decorative` over an `identifying` base: say so.
- **Colour vision**: the flat fills are the fallback, so a fallback pair that is hard to tell apart is a safety
  question. Cite the existing finding (`cvd_pairs.txt`) as a known, open risk against the `identifying` class; do not
  fix palettes here.
- **Failure policy**: at activation (a release whose key lacks an allowed fallback is refused?) and at runtime (load
  error, decode error, late/stale load, recall). State what is built and mark what is not as a `GAP` for later, not a
  requirement this ticket meets.
- **Rule for new kinds** (entities, buildings, items, UI, when unparked): every new visual key declares a class, and
  `identifying`/`critical` keys must name their non-image alternative before adoption. Written as policy only, no
  schema field is added.
- Update the register's `W06` rows to point at this doc.

## Out of Scope
- Any code, schema field, palette or art change; any HUD redesign (the HUD package owns the HUD).
- Assigning classes to kinds that do not exist yet beyond the general rule.

## Acceptance Criteria
- [ ] Each class states preserved information, allowed alternatives and failure policy; at most three classes.
- [ ] Every claim about terrain behaviour cites a code symbol or test that exists on the branch.
- [ ] The colour-vision finding is cited as an open risk, not described as resolved.
- [ ] Status `PROPOSED` unless the owner approved it in a blocking question (then the date and their words).
- [ ] Register `W06` rows updated; no file outside `docs/` and `agent-working/` changes.

## Related Tickets
- Parent: TCK-20261004-EPIC-VISUAL-ASSET-M1-CONTRACTS; after TCK-20261004-VISUAL-ASSETS-M1-CONTRACT-REGISTER

## Related Docs
- docs/assets/surface_rehearsal_result.md, pilot_terrain_m5_criteria.md, retention_and_rollback.md, store_contract.md
- Proposal §6-§9.6 (fallback and safety-class wording), Live Map/HUD package `docs/plans/render-and-art/README.md`

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET/cvd_pairs.txt

## Related Code Areas
- Read only: frontend/src/visualAssets/ (resolver, pickDetail, loader, terrainDrafts.ts), visual_assets/store/contracts/definitions.py

## Assumptions / Open Questions
- Whether the semantic registry already carries a safety-class link (`AM1-W02` mentions one): check
  `contracts/definitions.py`; if it does, use its names instead of inventing new ones.

## Implementation Notes
Wrote `docs/assets/fallback_safety.md`, status `PROPOSED` (no owner approval exists): three classes (`decorative`, `identifying`, `critical`) each with preserved information, allowed alternatives and what failure means; the terrain role mapped onto them (Forest `identifying`, bush/tree `decorative` over it) with a code symbol or test title for every behaviour claim; the colour-vision finding (`cvd_pairs.txt`) as an open risk, not resolved; runtime failure policy as built; activation policy as a stated gap; a policy-only rule for new kinds.
The assumption check came back negative: `VisualKeyDefinition` has no safety-class field, so the names are new. Findings worth the planner's eye: terrain's fallback is the flat fill plus hover text, while the typed family glyph (`fallbackFor`) is used only by the synthetic rehearsal scene; a still-loading terrain cell shows the fill; `assemble_release`'s `key_without_artifact` is an artifact requirement, not a fallback check. The register's `W06` rows now point at the doc and stay `GAP` (not approved); the register generator was rerun, counts unchanged (40/24/4).

## Test Summary
Docs-only. Every backticked path and symbol in the new doc exists, and each quoted test title is found in its cited test file; the register's 186 evidence entries resolve (scratch script). `tools/validate_frontmatter.py` clean; `pytest tests/docs tests/static` under a 2 GB cap: 124 passed, 2 skipped, 1 xfailed; `make knowledge-index-update` ran.

## Files Changed
- `docs/assets/fallback_safety.md` (new, PROPOSED)
- `docs/assets/m1_contract_register.md` (W06 rows, W02.7 and W06 follow-ups)
- `agent-working/` ticket, stored artifacts, monitoring shards; `docs/REGISTRY.yaml`

## Completion Summary
Done as PROPOSED. Nothing is written as an owner decision; approval is the planner's blocking question at review. No code, schema, palette, art or HUD change.
