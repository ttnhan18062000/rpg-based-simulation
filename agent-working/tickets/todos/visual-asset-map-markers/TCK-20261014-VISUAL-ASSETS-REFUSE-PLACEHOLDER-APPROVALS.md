---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261014-VISUAL-ASSETS-REFUSE-PLACEHOLDER-APPROVALS
phase: open
date: 2026-10-14
tags: [architecture, testing]
---

# TCK-20261014-VISUAL-ASSETS-REFUSE-PLACEHOLDER-APPROVALS

## Title
Store: adopt, adopt-set and revoke refuse template-placeholder approver, role and licence-evidence values; record the owner's erratum for sa-6690e2619d4abb3e

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Child 5 of `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS`. The owner ran `adopt-set object-markers-v1` with the command template asset-planner handed over. The template's placeholders were recorded literally in the immutable provenance: set adoption `sa-6690e2619d4abb3e` and its 18 adoption records hold approver `<your name>`, role `<your role>` and licence evidence `<your own licence evidence reference>`. `check_licence_and_approver` (`visual_assets/store/adoption.py:208`) refuses only empty values and the `NOT_APPLICABLE`/`UNAVAILABLE` markers. Owner answers (AskUserQuestion, 2026-10-14): "Keep, add an owner erratum"; store guard "Yes, queue a store fix"; approver "nhan / owner"; licence evidence "Own pixels, Aseprite + API".

## Scope
- **Guard:** `check_licence_and_approver` (used by `adopt` and `adopt-set`) and `revoke` refuse an approver, role, licence evidence or revoke reason that looks like a template placeholder: any `<...>` span, or text that is only a placeholder word (for example `TODO`, `TBD`, `xxx`, `your name`, case-insensitive). Use a new refusal code `placeholder_value` with a message naming the field. Records that already exist are never re-validated: the loader and `verify` keep reading `sa-6690e2619d4abb3e` as it is.
- **Tests:** each field and command refuses `<your name>`, `<x>`, and a value with a `<...>` span inside it; normal values such as the earlier records' "nhan" / "owner" and the D20 licence sentences pass; nothing is written on refusal; the existing placeholder records still load and `verify` stays 0.
- **Erratum (docs, no record edit):** a dated section in `docs/assets/store_contract.md` ("Provenance errata"), mirrored in child 2's done ticket, for `sa-6690e2619d4abb3e` and its 18 adoption ids. It states that the owner's real values (AskUserQuestion, 2026-10-14) are approver `nhan`, role `owner`, and licence evidence "Own pixels drawn in this repo with the Aseprite MCP tools and the visual_assets drawing API they wrap, from palette icons-v1; no outside art copied or traced, no AI generator (ADR D20, theme D21)". Records are immutable, so the erratum is the correction, and any tool that reports provenance must not hide it.
- Check whether `visual_assets.review` folder READMEs or docs print owner command templates with `<...>` placeholders. List them; do not change their wording beyond adding "replace every <...> before running".

## Out of Scope
- No edit, revoke or re-adoption of the 18 records (owner's choice: keep plus erratum).
- No `src/` or `frontend/` change.

## Acceptance Criteria
- [ ] The guard refuses placeholder values in adopt, adopt-set and revoke with `placeholder_value`; tests cover each field and command; nothing is written on refusal.
- [ ] Existing records (including `sa-6690e2619d4abb3e`) still load; `verify` exit 0.
- [ ] The erratum is in store_contract.md and child 2's ticket, quoting the owner's answers.

## Related Tickets
- Parent: `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS`; `TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS` (the adoption)

## Related Docs
- `docs/assets/store_contract.md`, `docs/assets/drawing_tools.md`, `docs/assets/icon_style_guide.md` (owner gate commands)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS/`

## Related Code Areas
- `visual_assets/store/adoption.py` (`check_licence_and_approver`), `visual_assets/store/setadoption.py`, `visual_assets/store/revoke.py`, `visual_assets/store/cli.py`, `tests/visual_assets/store/**`

## Assumptions / Open Questions
- A real approver name never contains `<` or `>`.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

