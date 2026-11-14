---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261114-PROJECT-SYNC-SECOND-HOST
phase: done
date: 2026-11-14
tags: [planning, delivery]
---

# Investigation: a second host writes Project 1

Read at origin/main fc62c8557 (#910). Code: `tools/sessions/project_sync.py` (derive_status 380, derive_item 473, build_plan 539), `project_client.py` (TEXT_FIELDS 195, init_fields 215, apply_plan 285).

## What the code does today (confirms the ticket's table)
1. `derive_status` takes this host's `branches` plus `other_host_branches`, which are the other hosts' `Branch` entries from the live item. The only per-host state the other host can see is the `[filing]` suffix. Blocked and Stale have no other-host carrier at all: Blocked reads only this host's branch copies (origin's copy only when this host has none), Stale reads only this host's `working` branches and is vetoed by a non-filing other-host entry.
2. `derive_item` builds Seat and Domain from this host's `mine` branches and falls back to the current value only when empty, so two hosts on one ticket drop each other's seat and a value never shrinks.
3. Title, Tier, Layer, Priority, Tags, Epic come from `best` = this host's branch copy, else origin's.
4. `build_plan` archives "no ticket file for this ID" when `tid not in known`, and `known` = origin's index plus this host's branch copies only.
5. Hash: `HASH_VERSIONS` v1, v2; stored as `v2:<sha>`; `hand_edits` checks the stored hash against that version's fields only, and an older-version hash with unchanged values becomes a `Sync hash`-only update. So adding v3 follows an existing path.
6. `apply_plan` writes `VALUE_ORDER` fields; `init_fields` creates every `TEXT_FIELDS` name that is missing and leaves existing ones; a second `--init` prints "left alone" and writes nothing.
7. Ubuntu's hostname is `ubuntu`; an unlisted hostname is already used as is, so the `host_names` entry is documentation plus a guard against the hostname changing.

## Findings that shape the design
- **Seat names carry the host but not uniformly.** u24 seats end `-u24`; ubuntu seats are bare (`agent-working-implementer`) or `-ubuntu` (rpg). So Seat cannot be attributed to a host from its name. Per-host segments must therefore store the seat list themselves.
- **Migration state exists.** u24 wrote P1c items with `Branch` entries and no `Host facts`. Until u24 runs the P2 code (the ticket holds u24 off `--apply` until P2 merges), u24's items have no segment. A first ubuntu `--apply` must neither drop u24's Seat/Domain nor archive its items. Needs a *legacy segment* rule (below).
- **The API cannot hide a field in a view.** `createProjectV2Field` makes the field visible in table views; hiding it is a UI step in the view settings. The ticket's "shown on no view" is therefore an owner step; the sync does not depend on visibility.
- **Hash change touches every item once.** Any item that gains a Host facts value shows `Host facts` as changed in the first plan, which is real new data. Items whose derived Host facts is empty get a `Sync hash`-only update.

## Open questions for the reviewers
1. Hiding the field (above): accept an owner UI step, noted in the doc?
2. Legacy segment rule (plan §3): OK to treat an other-host `Branch` entry with no segment as a "legacy segment" that never shrinks Seat/Domain until that host writes its own segment?
3. `Stale` for the other host: a segment carries `state=stale` only from the writing host's own staleness test; the reading host never recomputes it (no cross-host timestamps). OK?
