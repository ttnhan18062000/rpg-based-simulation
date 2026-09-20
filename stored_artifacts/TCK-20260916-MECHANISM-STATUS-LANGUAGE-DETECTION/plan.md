---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION
artifact_type: plan
tags: [architecture, schema, simulation-quality]
---

# Plan — TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION

## Goal
Build a report-only detector for status vocabulary embedded in the atlas/capabilities/wiring-map's
own hand-written description/label prose, per the ticket's own rule: prose describes what a
mechanism does; it never states whether it currently works.

## Design
1. `mechanism_status_language_check.py`: three scan functions (`scan_atlas`, `scan_capabilities`,
   `scan_wiring_map_labels`), each returning `Hit` records (artifact, location, phrase, snippet).
2. Scan only the genuinely duplicated free-text surface — atlas/capabilities `desc` fields, wiring
   map node labels. Never `badges`/`tier`/`tierLabel`, which already are the registry's own
   intentional status surface, kept converged by the existing regenerate tools.
3. Word list derived from a real corpus scan, not guessed — seeded from the ticket's own examples,
   extended with what the scan actually found.
4. Report-only main(): always exits 0, prints every hit grouped by artifact.
5. `make mechanism-status-language-check` target.
6. Scope item 3's own concrete cleanup: strip redundant status language from the wiring map's
   Entity Operating Loop node labels specifically (its own classDef already derives status).

## Non-goals
- Consolidating the three documents or building a which-document-owns-what table.
- A CLAUDE.md workflow rule requiring authors to remember to update status prose.
- Bulk-editing every hit the scan surfaces — see the ticket's own Completion Summary for the
  documented disposition on the ~94 hits that are accurate, non-stale prose.
