---
status: active
layer: architecture
authority: P2
audience: agent
tags: [planning]
---

# Handoff — Codebase domain to the RPG-core sessions

**From:** `codebase-planner`, 2026-10-04, at `origin/main` `c049b9d65`.
**To:** `rpg-planner` (and the RPG implementer through it).
**Reply:** comment on the PR that adds this file, or commit an answer under "Responses" at the bottom. The codebase
sessions run on a different machine and do not see your handover notes.

Nothing here asks you to change your work order. Section 1 is a date that affects every `src/` PR you open. Sections
2 and 3 are findings and decisions that are yours, not ours: the codebase domain does not edit `src/` (owner decision
8.7, the Python Code Craft freeze).

## 1. Code-health gates become blocking: merge on or after 2026-10-18

From the merge of the gates-flip batch (`docs/plans/codebase_health/python_code_craft_gates_flip_ticket_brief.md`,
owner decisions 8.18 and 8.19), a PR that edits `src/` fails CI on any of these:
- a new or worse ruff, complexipy or line-count finding against `codebase/baselines/code_health_exceptions.jsonl`
- a new mypy error not in `codebase/baselines/mypy_baseline.txt`
- a new ast-grep N3/N4/E3 finding (`docs/guidelines/python_code_standard.md`)
- a new top-level `src/` package without a row in `codebase/structure/package_registry.jsonl`

Existing debt is grandfathered (3,728 rows, 1,569 mypy errors); only new or worse fails. jscpd stays report-only. The
SARIF changed-line feedback job stays advisory permanently. Check names change: `Code health (advisory)` →
`Code health`, `Type check (informational)` → `Type check`, both to be required on `main`.
Reproduce locally under the uv environment: `make code-health` and `make typecheck-py`.

**Until then, read the job summary, not the check colour.** The advisory jobs are always green. PR #319 merged green
with "1 new, 1 worse" in its summary, and PR #320 had to clean it up, because after the flip that debt would have failed
every domain's PR.

## 2. Two undefined names in `src/` are runtime bugs (re-verified on `c049b9d65`)

ruff F821 reports 111 undefined names in `src/`: 109 are inside quoted annotations (harmless at runtime), 2 are
real:
1. **`src/engine/kernel.py:157`**: `prov_manifest_data = json.load(f)` with no module-level `import json` (only
   function-local imports at lines 894 and 979). It sits in `try: ... except Exception: pass`, so the `NameError` is
   swallowed and **the provenance manifest is never loaded**, silently.
2. **`src/systems/social_systems/party.py:143`**: `return StrategicUpdate(...)` with `StrategicUpdate` not imported
   (the return annotation at line 128 is deferred). It raises `NameError` whenever that path runs.

Both are in the mypy baseline, so they will not block your PRs; fixing them only shrinks the baseline.
**Asked:** decide whether to ticket them.

## 3. `src/` package structure decisions for when `src/` reopens (M7)

`docs/plans/codebase_health/src_package_structure_audit.md` (M5, PR #315) audited the 36 top-level `src/` packages. It
records decisions only; nothing moved. The non-`keep` decisions that belong to you:
- `actions`: retire-candidate (0 src importers; overlaps `systems/harvest_system.py`, `systems/loot_system.py`)
- `logging`: investigate (1 file; consumers `cli/entry.py` and 2 `observability` files)
- `economy`: merge-candidate into `systems` (overlaps `systems/economy.py`, `systems/economy_systems/`)
- `quests`: investigate (`QuestGenerator`, `QuestTemplate` duplicated with `systems/world_systems/`)
- `replay`: investigate (import cycle with `core`)
- `runtime`: investigate (0 src importers)
- `strategy`: investigate (two `CapacityService` classes; relation to `cognition`)
- `views`: investigate (1 file, 0 src importers, named in `cognition_domain_ownership.md`)

Also: the `world*` family has two import cycles (audit finding 4), and `core` imports `engine`, `domains` and
`systems` although the D14 layer model says it imports nothing (finding 1).
**Asked:** none now. These are inputs for when the owner reopens `src/`. Comment if any decision is wrong.

## Responses
