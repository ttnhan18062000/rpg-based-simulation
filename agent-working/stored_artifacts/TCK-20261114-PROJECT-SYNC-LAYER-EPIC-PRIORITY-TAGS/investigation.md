---
status: historical
layer: ticket
authority: P2
audience: agent
phase: done
ticket_id: TCK-20261114-PROJECT-SYNC-LAYER-EPIC-PRIORITY-TAGS
artifact_type: investigation
tags: [planning, delivery]
---

# Investigation

Owner decision #715 6874493351 ("(A) P1c now"), rpg lane only. Study: main-checkout `.claude/handover/drafts/github-project-best-practice-2026-11-14.md` §3, §7. Builds on P1b (#909, merged 6b8b56eda).

## Facts from the code (origin/main 6b8b56eda)
- `TicketCopy` carries id, folder, path, title, tier, blocked, date. It has no layer, priority or tags: `parse_copy` reads only `## Title`, `## Tier`, `## Status` and `date:`. P1c adds `layer`, `priority` (from `## Priority`) and `tags` (frontmatter list).
- `derive_item` fills `fields` from the `best` copy and `HASH_FIELDS` (9 names) feeds `sync_hash`; `hand_edits` calls a stored hash a hand edit when `sync_hash(item) != item["Sync hash"]`. Adding names to `HASH_FIELDS` therefore makes all 30 live items look hand-edited on the first run (scope 5).
- `project_client.py`: `set_select_options(field_id, [(name, color)])` sends options without ids, so every option id is replaced (that is why P1b's `--init` refuses on a Project with items). `init_fields` knows `TEXT_FIELDS`, `Tier`, `Status`. `apply_plan` writes `VALUE_ORDER` fields and `SELECT_FIELDS = (Status, Tier)`.
- `registries/layer_registry.jsonl`: one JSON object per line, field `layer`; 22 entries today.

## Epic derivation inputs
- `read_main_index` gives every ticket id -> [(folder, path)] on origin/main; the epic file of a folder is the `TCK-*-EPIC-*.md` in the same directory (read from the same index by path prefix).
- `SEQUENCE.md` files live in `agent-working/tickets/{todos,done}/<folder>/SEQUENCE.md`. Their `## Order` section names ticket ids. `git ls-tree` and `git show` are already allowed by `_guard`.
- A branch copy under `todos/<folder>/` is visible through the existing `BranchFact.copies` paths.

## Risks and open points
- The option-preservation probe is unconfirmed (schema says `id` preserves identity; no live proof). It decides Layer SINGLE_SELECT vs TEXT. Run once by hand on Project 1 with the throwaway field `zz-option-probe`; its deletion is the only delete allowed.
- 22 Layer options + 4 Priority options are far below the 50-option limit.
- Tags TEXT with wildcard filter matches substrings (accepted by the owner).
- A ticket whose frontmatter `layer` is not in the registry leaves Layer empty and adds a note (never guess).
