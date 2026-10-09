---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-SET-REVISIONS-AND-DRAFT-DROP
artifact_type: investigation
date: 2026-10-09
tags: [architecture, testing]
---

# Security review of the human adoption gate after ADR D22

Scope: `adopt-set` with revisions, `draft keep --revises`, `draft drop`, the tightened `adopt --parent`. Method: read every changed path, list what an agent (no TTY, no typed confirmation, able to run `draft keep` and `draft drop`) or a stale or tampered file could do, and check each with a test or by reading the guard.

| # | Question | Result | Evidence |
|---|---|---|---|
| 1 | Can an agent adopt anything? | No. `adopt-set` and `adopt` still need a terminal on stdin and the typed id; neither is an MCP tool; the drawing server cannot import the gate layers (boundary test `GATE_LAYERS`). `draft keep --revises` and `draft drop` record no approval and are not MCP tools. | `test_boundaries.py`, `test_no_agent_surface_gained_a_draft_or_adopt_tool`, `test_every_human_gate_property_still_holds_for_a_mixed_set` (no terminal, wrong typed id) |
| 2 | Can an agent smuggle a revision of an adopted icon into a set the human reviews as new art? | Only visibly: the confirmation prints `REVISION of <id>: rN -> rM` for every such slot and an `N new, M revisions` line before the typed id; the human also states the review evidence. | `test_a_mixed_set_adopts_a_new_asset_and_a_revision_in_one_decision` |
| 3 | Stale or forged parent? | `parent_revision` in the file is only a claim: `adopt-set` re-reads the catalog and refuses unless it is the latest unrevoked revision NOW (`parent_not_latest_unrevoked`), before the human is asked to confirm. | `test_a_stale_parent_is_refused_and_nothing_is_written` |
| 4 | Moving a source to another slot through a revision? | Refused (`revision_changes_slot`) in the set path, in `draft keep` and, since the owner's approval of 2026-10-09, in `adopt --parent`. **This was a real gap of the per-slot gate before this ticket** (`check_slot` only excluded the source's own holder). | M2, M3, M4 caught; `test_adopt_parent_refuses_a_revision_that_moves...` |
| 5 | Partial writes, concurrent adoption between the check and the publish? | All files go through one `publish` of exclusive hard links with rollback of every earlier file; a collision (another adoption taking the same r000N) refuses and leaves the catalog byte-identical. | `test_a_concurrent_adoption_colliding_at_publish_time_rolls_the_whole_mixed_set_back`, `test_one_bad_revision_among_good_entries_writes_nothing` |
| 6 | Can `draft drop` alter what was approved or adopted? | No: refused for a set with a set adoption record and for an adopted entry; it only removes an UNADOPTED draft of an unadopted set and records the removal (`dropped`, with the reason). It changes the set hash, so a review of the old hash no longer matches what `adopt-set` prints; the hash is shown before the typed id. | M5, M6 caught; `test_drop_*` |
| 7 | Can a drop hide something? | The dropped slot, draft id and reason stay in the tracked set file and in git history; at most 8 per set. | `test_drop_removes_the_draft_records_it_and_changes_the_hash` |
| 8 | Same-bytes and revocation sidesteps through a revision? | Unchanged: `check_source_bytes_are_new`, the revoked-revision refusal (`all_revisions_revoked`), the store re-render match and the licence and approver checks all run per entry exactly as before. | `test_the_revision_needs_the_same_checks_as_any_entry...` |
| 9 | Do old records and hashes change? | No: new fields are absent unless used, so every existing `DraftSet`, `SetAdoptionRecord` and the recorded hashes keep their bytes. | `test_a_set_without_revisions_or_drops_serialises_exactly_as_before`, `test_icon_owner_fixes_adoption.py` still green |

**Residual risks (unchanged by this ticket, stated, not fixed):** the human gate does not authenticate the person (the approver name and role are recorded, not verified; `store_contract.md`, known gaps); an agent with shell access can still run any CLI command that does not need a terminal, which is why the gates require one; `draft drop` deliberately needs no confirmation (it records no approval and only shrinks what a human is later asked to adopt).
**Verdict: clean for this change; one pre-existing gate gap (finding 4) closed.**
