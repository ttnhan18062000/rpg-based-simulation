---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261005-REGISTRY-REGEN-INDEXES-UNTRACKED-FILES-FROM-THE-WORKING-TREE
artifact_type: plan
tags: []
---

# Plan
Chosen shape: tracked-tree indexing (neither export nor refuse-and-warn), because it fixes every entry point at the one function they share.
1. `generate_registry()` indexes only files `git ls-files` returns (tracked or staged); a root that is not a git top level (a `git archive` export, tmp dirs) is indexed as before.
2. `include=` (and CLI `--include-untracked PATH`, repeatable; files, directories, globs) names untracked paths to index anyway.
3. The closure tool and `check_registry_entry_regenerated` pass the closing ticket (flat and nested `done/*/`) and its stored artifacts as `include`, so the closing ticket's own `done/` entry is still in the registry.
4. Post-merge hook and `make docs-registry` have no `include`: they index tracked plus staged only. A closing ticket must be `git add`ed before a bare `make docs-registry`. Documented in `delivery_process.md`; hook comment updated.
5. `implement-ticket.js` Finalize goes through `run_finalize_selfcheck` -> `check_registry_entry_regenerated`: covered. No other `generate_registry(` caller exists in `tools/` or `.claude/`.
