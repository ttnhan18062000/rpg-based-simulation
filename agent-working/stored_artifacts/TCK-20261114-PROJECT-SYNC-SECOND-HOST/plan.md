---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261114-PROJECT-SYNC-SECOND-HOST
phase: done
date: 2026-11-14
tags: [planning, delivery]
---

# Plan

## 1. Encoding of `Host facts` (text field)
One segment per host, joined by `; `:
`u24desktop: state=progress seat=rpg-implementer-u24 domain=rpg; ubuntu: state=blocked seat=rpg-implementer domain=rpg`
- `host` is the host tag (`host_names`). Keys fixed order `state`, `seat`, `domain`; `seat` and `domain` are comma lists without spaces, sorted, empty list omitted.
- `state` is one of `filing | progress | stale | blocked`, from that host's own branch copies of the ticket: `blocked` if any of its copies is blocked; else `progress` if some copy is in inprogress/ or done/; `stale` if every such working branch is older than `stale_branch_days`; else `filing`. No copies on the host: no segment.
- Parser `parse_host_facts(text) -> dict[host, Segment]` ignores a malformed segment and records a finding rather than raising. Writer `format_host_facts(dict)` sorts hosts. `merge_host_facts(current, mine, host)` replaces only the `host:` segment, like `merge_host_entries`.
- Branch display keeps its `[filing]` suffix (display only; nothing reads it for state once a segment exists).

## 2. Status from the union (`derive_status`)
New parameter `segments: dict[str, Segment]` (this host's freshly derived segment plus every other host's from the live item) replaces `other_host_branches`.
- Rules 1, 2 unchanged (Done, In review).
- Blocked: any segment `blocked`; origin's BLOCKED copy counts only when the union is empty.
- In progress: any segment `progress` or `stale`, unless the Stale rule below applies.
- Stale: at least one non-filing segment and every non-filing segment is `stale`.
- Then To do; the orphaned-inprogress finding fires only when the union is empty.

## 3. Legacy segment (migration)
An item whose `Branch` has an entry tagged by host H but whose `Host facts` has no H segment gets a synthesized segment for H: `state=progress` if any H entry lacks `[filing]`, else `filing`; seat/domain unknown. While any legacy segment exists, Seat and Domain keep their current entries and add this host's (no shrinking), exactly as today. When H writes its own segment the item is fully segment-based. Written nowhere: derived on read.

## 4. Seat and Domain
Union of all segments' seats and domains, sorted, so they shrink when a host drops its segment. Seat is empty when Status is To do (as now).

## 5. Content fields
Title, Tier, Layer, Priority, Tags, Epic: this host's branch copy if it has one; else if another host has a non-filing segment and the item exists, keep the current value; else origin's copy. Both hosts holding a branch copy: last writer wins; the plan prints a note.

## 6. Archive guard
"no ticket file for this ID" does not archive an item carrying another host's segment (or a legacy other-host Branch entry); it adds the finding `<id>: not archived, carries facts of <host>`. An item with no segment of another host archives as before. "duplicate Ticket ID" is unchanged.

## 7. Plumbing
- `HASH_FIELDS_V3 = HASH_FIELDS + ("Host facts",)`; `CURRENT_HASH_VERSION = "v3"`; `HASH_VERSIONS` gains v3. A v2 hash still verifies against v2 fields (no false hand edit).
- `project_client.TEXT_FIELDS` gains `Host facts`; `VALUE_ORDER` gains it before `Source`. `--init` creates it by name; a second `--init` writes nothing (existing behaviour).
- `registries/session_project.yaml`: `ubuntu: ubuntu` in `host_names`.
- `docs/guidelines/session_roles/project_sync_dry_run.md`: the two-host rule, the encoding, the legacy rule, and the corrected design §5 line ("rules 1, 2, 3 and 5 depend only on origin" is true only for Done and In review).

## 8. Size
About 120 lines of code in project_sync.py, 3 in project_client.py, 2 in the yaml, about 60 lines of doc, 9 tests.

## 9. Live order (ticket AC3), stop on any refusal with the redacted error
1. Dry run (live read) → plan to planner for u24's OK. 2. `--init`, then a second `--init` (must print "left alone"). 3. Dry run with the new code → plan to u24's planner (no u24 archive; hash-only rewrites called out). 4. `--apply` only on u24's OK. 5. u24 read-only dry run, then ubuntu final dry run = nothing to do. The token file is never read, printed or copied by me.

## Amendments approved 2026-11-14 (agent-working-planner-u24, agent-working-designer-u24; supersede the text above where they differ)
- M1 legacy segment: a host never makes one for itself; it counts in every union rule (Status, Seat/Domain, archive guard, M4); derived on read, never written.
- M2 seats: a segment stores recorded seat names only; placeholders ("(seat not recorded)", "unknown") are made at render time; a filing segment gives no seat; Domain comes from all segments, filing included.
- M3 Stale comes only from the host that wrote the segment; the doc states the gap (a stopped host leaves its segment at progress; the stale-host flag is P3).
- M4 content rule (replaces plan 5 and ticket Scope 4): no holder → origin; one holder = this host → own copy; one holder = other host → keep current (origin if no item); two or more holders with an origin copy → origin on every host; two or more and no origin copy → only the lowest host tag writes its own copy, the others keep current. A plan note names the rule when two or more hold it.
- M5 build_plan's `changed` loops over HASH_VERSIONS[CURRENT], not a hard-coded tuple. M6 the dry-run plan for step 3 counts hash-only rewrites and Host facts writes separately.
- M7/M7c convergence tests: one holder per ticket A→B→A (3rd plan empty); two holders with and without origin A→B→A→B (4th empty); both segments present, different titles, no origin, A→B→A: 3rd plan empty and only A's title ever written. Plus a lowest-tag test and an M5 test.
- M8 AC3.5: u24's read-only dry run may plan u24's own first segment writes and Seat/Domain moving from legacy values to the union; it fails only on a change to a ubuntu segment, any archive, or a Status change on an item where only ubuntu is a holder. ubuntu's final dry run must then show nothing to do.
- M9 P1c code reads "v3:" as an unknown version: a P1c-code u24 dry run reports a hand edit on every v3 item (expected noise). No u24 --apply until the u24 checkout that runs the sync is on P2 code.
- M10 transport: ubuntu commits; the owner OKs an S2 push of that exact sha (no PR); planner-u24 checks it out read-only in a scratch worktree on u24 and runs --dry-run only. M11: hiding Host facts in the views is an owner UI step.
- M12 (planner-u24, after the step 3 dry run): in derive_status, after Done and In review, when this host has NO own segment, every other segment is legacy and a current item exists, return the item's current Status unchanged. This host's own segment present: normal union. The current Status is not copied into a legacy segment's state. Replaces the "known effect" of ubuntu writing In progress over u24's Stale. Tests: legacy-only keeps Stale, keeps Blocked, origin done/ gives Done.
