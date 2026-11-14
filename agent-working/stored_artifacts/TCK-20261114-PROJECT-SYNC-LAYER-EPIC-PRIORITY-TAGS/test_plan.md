---
status: historical
layer: ticket
authority: P2
audience: agent
phase: done
ticket_id: TCK-20261114-PROJECT-SYNC-LAYER-EPIC-PRIORITY-TAGS
artifact_type: test_plan
tags: [planning, delivery]
---

# Test plan
Scoped: `tests/tools/test_session_project_sync.py`, `tests/tools/test_project_client.py`, `tests/tools/test_session_status*.py`. No network; fake runner and fake client as in P1b.

1. parse_copy: layer, priority, tags (space-joined) from a ticket text; empty and unknown layer/priority leave the field empty and produce a note.
2. Epic (a): a `todos/<folder>/` copy with an EPIC file in the folder -> the epic id; without one -> the folder name.
3. Epic (b): id named in exactly one folder's SEQUENCE.md `## Order` -> that folder's epic; named in two folders -> `standalone` + a note naming both.
4. Epic (c): no match -> `standalone`; `## Related Tickets` is ignored.
5. merge_options: existing options keep ids and order; a new option is appended with no id; none is dropped.
6. `set_select_options` sends the `id` for kept options (fake runner records the input).
7. Hash migration: an item whose stored hash is the V1 hash of its fields gives no hand-edit line and still gets an update for the new fields.
8. `--init`: creates Layer (registry options), Priority, Epic, Tags; adds an option the registry gained via merge_options; second run creates and updates nothing; wrong-type Layer refuses.
9. apply: new fields are set in `VALUE_ORDER` (Layer/Priority by option id), `Sync hash` last.
