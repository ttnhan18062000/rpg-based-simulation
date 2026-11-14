---
status: historical
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20261114-PROJECT-SYNC-LAYER-EPIC-PRIORITY-TAGS
phase: done
date: 2026-11-14
tags: [planning, delivery]
---

# TCK-20261114-PROJECT-SYNC-LAYER-EPIC-PRIORITY-TAGS

## Title
`project_sync.py` P1c: Layer, Epic, Priority and Tags fields, so that one domain's board can be split further (rpg lane, u24)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child P1c of TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW. The owner asked: "a domain is still a big view, can we separate more using
categories or tags ? or maybe I wonder that a specific ticket is standalone or belong to any epic". The owner decided on #715
6874493351: "(A) P1c now (Recommended)", rpg lane only.

Inputs:
- the best-practice study, main-checkout `.claude/handover/drafts/github-project-best-practice-2026-11-14.md` (sections 3 and 7, and
  recommendations 14-16);
- the planner's epic measurement below.

P1c builds on P1b (#909, TCK-20261114-PROJECT-SYNC-INIT-AND-APPLY). **Write code only on a branch cut from origin/main after #909 has merged.**

## Scope
1. **Option-preservation probe, first, before any other code.** The live schema says `ProjectV2SingleSelectFieldOptionInput.id` should be
   included "to preserve the option's identity during updates, preventing item field values from being cleared". Prove that on
   Project rpg-sim-lab/1 with a throwaway probe:
   - Create a single-select field `zz-option-probe` with options a and b. Set it to `a` on one item.
   - Update the options to a, b and c, passing the existing ids for a and b.
   - Read the item back. Its value must still be `a`.
   - Then **delete the probe field**. This is the only delete this ticket allows, it applies to that probe field only, and it is
     run by hand, never by the sync.
   - Send the read-back to the planner before you delete the field.
   - If the value is cleared, Layer becomes a TEXT field, and the planner is told before you go on.
2. **`set_select_options` keeps option ids.** Fetch the current options, keep each existing option's id, and append new ones. Never
   drop an existing option. This also makes the P1b Status-options path safe; keep `--replace-status-options` as it is.
3. **New fields**, created by `--init` by name:
   - `Layer`: SINGLE_SELECT. Its options are the values of `registries/layer_registry.jsonl`, 22 today.
     `--init` adds any option the registry has gained, using scope 2. It is TEXT instead if the probe fails.
   - `Priority`: SINGLE_SELECT, P0, P1, P2, P3.
   - `Epic`: TEXT.
   - `Tags`: TEXT, the frontmatter tags joined by single spaces in registry order. TEXT because draft items can't carry labels, and
     88 tags is likely past any option limit.
4. **Derivation**, from the same ticket copy P1b already picks (`best`):
   - Layer and Tags come from the frontmatter. Priority comes from `## Priority`. An empty or unknown value leaves the field empty
     and adds a note; never guess.
   - **Epic, first match wins:**
     - (a) The ticket's own path on origin/main, or the branch copy, is `todos/<folder>/`. Use the id of the folder's
       `TCK-*-EPIC-*.md` if there is one, otherwise the folder name.
     - (b) The ticket id appears in exactly one folder's `SEQUENCE.md` `## Order` section, under `todos/` or `done/`. Use that
       folder, with the same epic-or-folder rule.
     - (c) Otherwise `standalone`.
     - If (b) matches more than one folder, use `standalone` and add a note naming the folders.
     - Don't read `## Related Tickets`: it isn't reliable.
     - Measured on origin/main: since 10-01, 296 of the 872 done tickets are named in some SEQUENCE.md, 12 of them in more than one.
5. **Sync hash migration.** Adding fields to `HASH_FIELDS` changes the hash, so on the first run all 30 live items would show as hand
   edits. Prevent that, for example with a hash version, so that an item whose stored hash matches the old field set is treated as
   synced and updated, and doesn't produce a hand-edit report. Exactly one test covers it.
6. **Docs.** `docs/guidelines/session_roles/project_sync_dry_run.md`: the 4 fields, the Epic rule, and the probe result.
7. **Tests, no network** (about 9):
   - Layer, Priority and Tags derived from the frontmatter and body, with empty and unknown values;
   - Epic rules (a), (b) and (c), plus the ambiguous case of (b);
   - option ids kept, and a new option appended without dropping any;
   - the hash migration does not report hand edits;
   - `--init` adds a newly registered layer option.

## Out of Scope
- Domain as a single-select, one board sliced by Domain, and the other 8 domain boards: these are P3.
- Write pacing and retry-after: TCK-20261114-PROJECT-CLIENT-WRITE-PACING, before P3.
- New views. Grouping or slicing by Layer or Epic in a view is set by hand by the owner, or by a separate owner ask.
- Lanes other than rpg (P3), and ubuntu (P2).
- Writing anything back to ticket files.

## Acceptance Criteria
1. The probe result (scope 1) goes to the planner before scope 2 code. The probe field is deleted afterwards and its deletion is read
   back.
2. Scope items 2-7 are built, and the scoped tests pass: test_session_project_sync, test_project_client, test_session_status*.
3. **Live run on Project 1, in the P1b order:**
   - dry run, then `--init`, then a second `--init` that must be a no-op;
   - the `--apply` plan goes to the planner for an OK; it should be about 30 updates, with no hand-edit lines;
   - `--apply`;
   - a final dry run that must show nothing to do.
   Stop on any refusal and report it, redacted.
4. The PR body carries the probe read-back, the plan and the outputs of the final runs, redacted.
5. Staging artifacts exist. agent-working-designer-u24 reviews plan.md before any code.
6. A grep of the diff and of the outputs finds no token value. The token is never printed.

## Related Tickets
- TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW (parent)
- TCK-20261114-PROJECT-SYNC-INIT-AND-APPLY (P1b, #909)
- TCK-20261114-PROJECT-CLIENT-WRITE-PACING (P3 prerequisite)

## Related Docs
- docs/guidelines/session_roles/project_sync_dry_run.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261114-PROJECT-SYNC-INIT-AND-APPLY/
- Study (main checkout): `.claude/handover/drafts/github-project-best-practice-2026-11-14.md`

## Related Code Areas
- tools/sessions/project_sync.py, tools/sessions/project_client.py, tests/tools/test_session_project_sync.py,
  tests/tools/test_project_client.py

## Assumptions / Open Questions
- **Simpler-fix check (6698958617).** The simplest form would be all four fields as TEXT, with no probe and no option handling. The
  cost is that Layer couldn't be used for group-by or slice-by, which is the owner's ask. A single-select Layer costs only the probe
  and the option-id fix, about 30 lines, and the option-id fix also hardens P1b's Status path. Total: about 130 lines and 9 tests,
  plus one live update pass over 30 items (about 120 mutations, within the rate limit).
- Tags matched by wildcard also match substrings (`*ai*` matches "chain"). That's accepted for a filter-only field.

## Implementation Notes
Probe first (by hand, Project 1, 2026-11-14 08:29Z): a single-select updated with the existing option ids kept every item's value, so Layer is SINGLE_SELECT. `set_select_options` now takes (name, colour, id); `merge_options` is append-only and keeps ids and colours; `replace_options` (the `--replace-status-options` path) sends exactly STATUSES in order with existing ids. `--init` adds Layer (registry options), Priority (P0-P3), Epic and Tags and appends missing options. Derivation in `project_sync.py`: `TicketCopy` gains layer, priority (leading P0-P3 token), tags (registry order, unknown last); Epic = folder epic by `## Tier: epic` (todos/ or done/ folder), else exactly-one SEQUENCE.md (exact basename; `## Order` or whole file), else standalone. Sync hash is versioned (`v2:<sha>`; unprefixed = v1), a v1 item is updated once, not reported as a hand edit. Designer amendments A-E and E2 in plan.md. The probe field `zz-option-probe` was deleted by hand afterwards (the only delete); the owner's approval for that delete is #715 6874643227, posted after the delete ran (timeline logged by the lead on #715).

## Test Summary
tests/tools/test_session_project_sync.py and test_project_client.py plus test_session_status*: 113 passed at 4cca60a8c, the commit `--init` ran on; final scoped count with test_generate_registry's no-drift test is in the PR body. Live runs on rpg-sim-lab/1: dry run, `--init` (created Epic, Tags, Priority, Layer), second `--init` (all left alone), `--apply` 160 steps (30 updates), final dry run: nothing to do, 0 hand edits. Token-value grep over the diff and outputs: no match.

## Files Changed
tools/sessions/project_client.py, tools/sessions/project_sync.py, tests/tools/test_project_client.py, tests/tools/test_session_project_sync.py, docs/guidelines/session_roles/project_sync_dry_run.md, SEQUENCE.md, this ticket and stored artifacts, TCK-20261114-PROJECT-CLIENT-WRITE-PACING.md (filing only, in todos/).

## Completion Summary
P1c built and applied on the org Project: 30 items now carry Layer, Priority, Epic and Tags; a rerun is a no-op. 29 of 30 are Epic=standalone (the planner audited that against origin/main). Not covered: P3 (Domain single-select, other boards, pacing ticket), P2.

