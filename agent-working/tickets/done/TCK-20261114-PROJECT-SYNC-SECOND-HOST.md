---
status: historical
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20261114-PROJECT-SYNC-SECOND-HOST
phase: done
date: 2026-11-14
tags: [planning, delivery]
---

# TCK-20261114-PROJECT-SYNC-SECOND-HOST

## Title
`project_sync.py` P2: host ubuntu writes Project 1 too, and neither host's run can rewrite or archive the other host's facts (rpg lane)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child P2 of TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW. The owner's go is #715 6875225978 item 2 ("so P2 can be cut once P1c
lands"). P1c merged in #910 (fc62c8557). lead-planner-u24 relayed it on 2026-11-14 and reported that the ubuntu token is in place: a
fine-grained token with resource owner rpg-sim-lab and Organization Projects read and write only, at
`~/.config/rpg-project-sync/token` on ubuntu, with the directory at mode 700 and the file at 600.

**Runs on:** host ubuntu, seat **agent-working-implementer** (ubuntu). Dispatch goes through ubuntu's lead-planner. It writes the
code, makes the live runs and opens nothing itself: push, PR and merge go to the owner through lead-planner-u24.

**Write code only on a branch cut from origin/main at or after fc62c8557 (#910).**

### The two-writer question, settled: host-scoped ownership
The epic says there is "one writer per host, doing a full reconcile". Design §5 says a host "replaces only the entries tagged with
its own name" and that "Status rules 1, 2, 3 and 5 depend only on origin". That is true for `Host` and `Branch`
(`merge_host_entries`). The planner read `derive_item` / `build_plan` at fc62c8557 and found it is **not** true for these:

| Field / action | What the code does now | Two-host failure |
|---|---|---|
| Status: Blocked (rule 3) | It reads this host's branch copies, and origin's copy only when this host has no copy | ubuntu's branch marks a ticket BLOCKED, so ubuntu writes Blocked. u24 has no copy and sees ubuntu's Branch entry, so it writes In progress. The value flips on every run. The reverse case also flips: main says BLOCKED and ubuntu's branch has unblocked it. |
| Status: Stale | `working` is this host's branches only | ubuntu writes Stale. u24 has no working branch, so it writes In progress. The value flips. |
| Seat | This host's working seats, or the current value when it has none | Both hosts working the same ticket: each run drops the other host's seat. |
| Domain | This host's branch domains, or the current value | The same drop. Kept as-is, it can also never shrink. |
| Title, Tier, Layer, Priority, Tags, Epic | `best` = this host's branch copy, else origin's copy | ubuntu writes its branch's title. u24 has no copy and writes origin's title. The value flips. |
| Archive "no ticket file for this ID" | `known` = origin's index plus **this host's** branch copies | A ticket filed only on a ubuntu branch: u24's next `--apply` **archives** ubuntu's item. |
| Archive "duplicate Ticket ID" | Keeps the item whose hash matches | Both hosts create the same item at the same moment: one is archived. This is acceptable, and it is what the code is for. |

**Decision: host-scoped ownership.** Each host writes only its own per-host facts. Every field that depends on more than one host is
computed from the union of all hosts' facts as read from the Project, so both hosts derive the same value.

The alternative, **one writer that reads both hosts**, is rejected:
- u24 can't see ubuntu's worktrees or its local-only branches without ssh or pushing per-host state, and neither exists.
- It would also break P3's per-host timer.

**Simpler-fix check (6698958617):** u24 stays the only writer and ubuntu only runs dry runs. That costs no code, but ubuntu's
in-flight tickets would show To do with no Seat until their PR opens, which is the gap P2 exists to close. Host-scoping is the
recommendation. It costs about 120 lines and 8 tests, up from the epic's estimate of about 40 lines and 3 tests, because of the gaps
in the table. If the owner wants the zero-code option instead, lead-planner-u24 relays that and this ticket shrinks to scope 6 run
as a dry run only.

## Scope
1. **A per-host facts field.** Add a TEXT field `Host facts`, created by `--init` by name and shown on no view. It holds one segment
   per host, for example `u24desktop: state=progress seat=rpg-implementer-u24 domain=rpg; ubuntu: state=blocked seat=... domain=...`.
   The exact encoding is the implementer's, and plan.md states it. The rules:
   - A host rewrites **only its own segment**, the way `merge_host_entries` does for Branch.
   - A host with no copy of the ticket removes its own segment.
   - `state` is one of `filing | progress | stale | blocked`, from that host's own branch copies. This replaces `[filing]` as the
     carrier of per-host state.
   - The `Branch` display may keep its suffix.
2. **Status from the union** (plus M12: when this host has no own segment and every other segment is a legacy one, Status stays the item's current value, after Done and In review). In `derive_status`:
   - Rules 1 and 2 (Done, In review) are unchanged.
   - **Blocked** when any host's segment is `blocked`. Origin's BLOCKED copy counts only when no segment has a branch copy.
   - **In progress** when any segment is `progress` or `stale`.
   - **Stale** only when every non-filing segment is `stale`.
   - Then To do. The orphaned-inprogress finding fires only when no host has a segment.
3. **Seat and Domain from the union** of all segments, sorted. They then shrink when a host removes its segment.
4. **Ticket-content fields** (Title, Tier, Layer, Priority, Tags, Epic, Body). Final rule M4 (reviewers' amendment, supersedes the first draft): no holder: origin's copy; exactly one holder and it is
   this host: this host's own copy; exactly one holder and it is another host: keep the current value (origin's copy if there is no item); two or more holders and origin has a copy: origin's
   copy on every host; two or more and no origin copy: only the holder with the lowest host tag writes its own copy, the others keep the current value. A plan note names the rule when two or more hold it.
   A "holder" is a host with a segment in any state, legacy segments included.
5. **Archive guard.** "no ticket file for this ID" never archives an item that carries another host's segment. It prints a finding
   naming that host instead. A host whose own segment is the only one archives as before.
6. **Config:** add ubuntu's real `hostname` to `host_names` in `registries/session_project.yaml` with the tag `ubuntu`.
7. **Hash:** add `Host facts` to `HASH_FIELDS` as a hash v3, using the P1c version mechanism. The first run must report no hand
   edits.
8. **Docs:** in `docs/guidelines/session_roles/project_sync_dry_run.md`, describe the two-host ownership rule and the table above in
   short. Correct design §5's line "rules 1, 2, 3 and 5 depend only on origin" in that doc, not in the draft.
9. **Tests, no network** (about 8):
   - Blocked from another host's segment;
   - Stale only when all hosts are stale;
   - Seat and Domain union and shrink;
   - content fields kept when only the other host has a copy;
   - the archive guard;
   - own segment replaced and the other kept;
   - the v3 hash migration produces no hand edits;
   - **convergence:** a run on A, then B, then A on fixed inputs leaves the third plan with no updates and no archives.

## Out of Scope
- The stale-host flag (`stale_host_hours` is config-only today and nothing reads it). It needs a stored last-run time per host; that
  goes to P3, where the timer makes it matter. This is a known gap, stated.
- Lanes other than rpg, Domain as a single-select and the prefix fallback in `attribute()`: these are P3.
- Write pacing: TCK-20261114-PROJECT-CLIENT-WRITE-PACING.
- Any delete. Items are only archived, as before.

## Acceptance Criteria
1. Staging artifacts exist. agent-working-designer-u24 reviews plan.md before any code. plan.md names the `Host facts` encoding.
2. Scope items 1-8 are built, and the scoped tests pass: test_session_project_sync, test_project_client, test_session_status*.
3. **Live order. Stop with the exact, redacted error on any refusal.**
   1. **No u24 `--apply` from this ticket's first ubuntu `--init` until P2 merges.** The P1c code on u24 would archive ubuntu-only
      items and drop ubuntu segments. lead-planner-u24 holds u24 to this.
   2. On ubuntu: a dry run, then `--init` (adds `Host facts`), then a second `--init`, which must do nothing.
   3. On ubuntu: a dry run with the new code. The plan goes to agent-working-planner-u24 through the leads. It must show no archive
      of a u24 item, and the hash v3 rewrite only for items whose values are unchanged.
   4. `--apply` on ubuntu **only after agent-working-planner-u24's OK**.
   5. On u24, with this ticket's branch code, agent-working-planner-u24 makes a read-only dry run. It must not change any ubuntu
      segment, Seat or Status. Then ubuntu makes a final dry run, which must show nothing to do (convergence).
4. The PR body carries the plan and the outputs of the final runs, redacted. A grep of the diff and of the outputs finds no token
   value.
5. Any delete (none is expected) goes to the owner through lead-planner-u24 before it runs.

## Related Tickets
- TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW (parent)
- TCK-20261114-PROJECT-SYNC-INIT-AND-APPLY (P1b, #909), TCK-20261114-PROJECT-SYNC-LAYER-EPIC-PRIORITY-TAGS (P1c, #910)
- TCK-20261114-PROJECT-CLIENT-WRITE-PACING (P3 prerequisite)

## Related Docs
- `docs/guidelines/session_roles/project_sync_dry_run.md`
- Design: main-checkout `.claude/handover/drafts/github-project-ticket-view-2026-11-12.md` §5

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261114-PROJECT-SYNC-LAYER-EPIC-PRIORITY-TAGS/`

## Related Code Areas
- `tools/sessions/project_sync.py`: `derive_status`, `derive_item`, `build_plan`, `merge_host_entries`
- `tools/sessions/project_client.py`: `init_fields`
- `registries/session_project.yaml`
- `tests/tools/test_session_project_sync.py`

## Assumptions / Open Questions
- Seat names already carry their host (the `-u24` / `-ubuntu` suffixes). The segment holds the seat as-is, so no roster lookup is
  needed.
- If the owner prefers the zero-code single-writer option, see the simpler-fix check above.

## Implementation Notes
- Plan, investigation, test plan: `agent-working/stored_artifacts/TCK-20261114-PROJECT-SYNC-SECOND-HOST/`. Reviewed by agent-working-planner-u24 and agent-working-designer-u24 (approved with M1-M11 and M7c; then M12 after the step 3 dry run), relayed by agent-working-planner and the leads.
- Built as `Segment` / `parse_host_facts` / `format_host_facts` / `legacy_segments` / `own_segment` in `tools/sessions/project_sync.py`; `derive_status` takes the union of segments; `content_source` implements rule M4; the archive guard and hash v3 follow the plan. `project_client.TEXT_FIELDS` and `VALUE_ORDER` gain `Host facts`; `registries/session_project.yaml` gains `ubuntu: ubuntu`.
- M12 (planner-u24, after the first live dry run): with no own copy and only legacy holders, Status stays the item's current value, so ubuntu does not overwrite u24's Stale/Blocked. Recorded limit: with only legacy u24 segments, Status freezes until u24 runs P2 code; the hold on u24 `--apply` lifts only after u24's first P2 `--apply`, soon after merge.
- Corrected a wrong statement of mine mid-run: the first four Status updates were Stale to In progress (not To do), found by reading the live items.
- Live order, all from the P2 branch code: dry run (new code), `--init` (created `Host facts`), second `--init` (nothing written), dry runs, transport pushes of c5869073e and a7af7e622 (owner #715 6876629201, 6876754593), `--apply` on a7af7e622 (planner-u24 OK): 2 creates, 23 hash-only updates, 0 archives, 74 steps, rc 0. u24's read-only run (M8): PASS. Final ubuntu dry run: `nothing to do`.
- No token value appears in any output or file; the token file was never read by me.
- The doc wording avoids authority-class names (for example the word for landing a PR) because `docs/guidelines/session_roles/` is generated-from-registry territory: `tests/tools/test_session_cards.py::test_define_once_templates_do_not_restate_authority_classes` fails on them. #913's first CI run failed on exactly this; my earlier scoped run had not included that test file.

## Test Summary
- `tests/tools/test_session_project_sync_second_host.py`: 18 tests (encoding round trip and malformed segment, placeholders at render time, Blocked, Stale, Seat/Domain union and shrink, own-segment replace, rule M4 all five cases and lowest tag, plan note, archive guard, legacy segments, M12 legacy-only status, hash v3, Host-facts-alone update, convergence one-holder A,B,A, two-holders with and without origin A,B,A,B, M7c). `tests/tools/test_project_client.py`: +1 (Host facts created by init, second init writes nothing). One P1c test moved to v3.
- Scoped runs: 119 pass (project_sync, second_host, project_client); paths-guard, ci_workflow_test_coverage, no_duplicate_content_blocks pass.
- Live: see Implementation Notes (final dry run `nothing to do`; u24 M8 PASS).

## Files Changed
- `tools/sessions/project_sync.py`, `tools/sessions/project_client.py`, `registries/session_project.yaml`, `docs/guidelines/session_roles/project_sync_dry_run.md`, `tests/tools/test_session_project_sync.py`, `tests/tools/test_session_project_sync_second_host.py` (new), `tests/tools/test_project_client.py`, `agent-working/tickets/` (this ticket and the epic folder's SEQUENCE.md), `agent-working/stored_artifacts/TCK-20261114-PROJECT-SYNC-SECOND-HOST/`.

## Completion Summary
Host ubuntu now writes Project 1 as a second host. A `Host facts` field holds one segment per host; each host rewrites only its own, Status, Seat and Domain come from the union of hosts, content fields follow rule M4, and nothing is archived while another host holds the ticket. Live: `Host facts` created, the first `--apply` wrote 2 creates and 23 hash-only updates, u24's read-only run passed, and the final ubuntu dry run shows nothing to do.

Known gap: with only legacy u24 segments, Status freezes until u24 runs P2 code; u24's first P2 `--apply` must follow soon after merge and the hold on u24 `--apply` lifts only then.
Known gap: a host that stops running leaves its segment saying progress; the stale-host flag that would catch it is P3.
Known gap: hiding `Host facts` in the Project views is an owner step in the view settings; the sync does not depend on it.
