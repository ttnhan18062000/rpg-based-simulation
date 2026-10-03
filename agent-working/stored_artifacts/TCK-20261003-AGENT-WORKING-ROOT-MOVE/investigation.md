---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261003-AGENT-WORKING-ROOT-MOVE
artifact_type: investigation
tags: [ai, process-improvement, governance]
---

# Investigation (retroactive)

**Written after the fact.** This ticket was drafted, implemented and merged (PR #289, 243e798ad, 2026-10-03) without
the standard-tier staging artifacts, because the work was designed in conversation and then run as three staged
commits. This record reconstructs what was actually investigated and found, from the measurements taken at the time,
the implementer's reports, and checks made against git after the merge. It adds nothing that was not known then. Each
line says who established it; "implementer-reported" means not independently re-run.

## What was measured before the move (design session, 2026-10-03, origin/main 5d49a67c7)

The knowledge search (`search_docs`) returned nothing useful on repo layout, and `graphify query` returned unrelated
api-checklist nodes; the sizing below is therefore from `git grep` and `find`, as follow-up steps.

| Folder | Tracked files | Live refs (files in src, tools, tests, .github, Makefile, .claude, .mcp.json, pyproject naming `<folder>/`) |
|---|---|---|
| `tickets/` | 2,465 | 163 |
| `stored_artifacts/` | 4,963 | 78 |
| `staging_artifacts/` | 16 | 77 |
| `agent-monitoring/` | 153 | 215 |
| `agent-orchestration/` | 22 | 43 |
| `pilot_requests/` | 2 | 13 |
| `reviews/` | 1 | 10 |
| generated, untracked: `agent-monitoring-index/`, `knowledge-index/`, `parity-index/` | 0 | 12 / 20 / 7 |

Files naming a moved root, by group (a lower-bound grep, not an inventory): `tools/` 138, `tests/` 172, `docs/` outside
the archive 197, `.claude/workflows/` 8, `.claude/agents/` 9, `.claude/skills/` 5 and the mirrored `.agents/` 8,
`agent-orchestration/` 9, `src/` 13, plus `Makefile`, `.claude/settings.json`, `CLAUDE.md`, `AGENTS.md`.
Closed history citing the old paths: about 1,500 files (frozen by decision, below).

Repo-level facts that shaped the design: `.gitattributes` has `merge=union` rules for `agent-monitoring/data/*/*.jsonl`
and `tickets/working_log.csv`; `.gitignore` had rules for `reviews/*`, `stored_artifacts/**/*.json` (with a
`manifest.json` exception) and the three index folders; the CI job named `agent-orchestration` and its junit file have no
trailing slash; a first count found 6 `Path(__file__)` users naming these roots (a lower bound).

## Owner decisions (2026-10-03)

One `agent-working/` root; `registries/` stays out; closed history is frozen; `tools/` stays out; `experiments/` stays
out (its `PROPOSAL.md` files are not all agent-working); `reviews/` moves; the move lands inside PR #289 as Stages 1 to 3,
and the generated indexes go to `agent-working/.index/`. Layout rule: prefix-only, so one rewrite rule covers it.

## Findings after the move (checked by the design session against git)

- #289 squash-merged as 243e798ad. Stage 2a (`7c10d1243`) is 7,640 renames, all R100, none other.
- At 9175b8770 the only old-root name left at the tree root is `agent-working/`; nothing under `agent-working/tickets/done`,
  `agent-working/stored_artifacts` or `docs/archive` changed between the rename and the final stage commit.
- A scan for old-root paths outside the frozen set found 7 files: the two session-layer tickets, the path map, the constants
  module and `docs/REGISTRY.yaml`, which name old roots on purpose; not each read.
- Implementer-reported (the PR #289 body and the implementer's handover), not re-run: scoped suites green in a clean clone at
  9175b8770 except 7 `codebase_health` tests that need `complexipy`, absent from that venv and failing identically on the
  pre-move tree. The implementer's records say "scoped suites", not the full suite, and do not contain a "4,328 passed" figure;
  that number came from the design session and is not confirmed.
- Verified by the implementer against git on 2026-10-03: Stage 1 `33ee17bd1`, Stage 2a `7c10d1243` (`git diff -M --name-status
  33ee17bd1 7c10d1243` shows 7,640 entries, all R100), Stage 2b `888c0a686`, Stage 3 `9175b8770`. A fifth commit, `e720c4edb`,
  made `pr_render.py` cap its file listing and ignore pure renames; PR #289's head was `e720c4edb`.

## Defects found after the merge, and where they were fixed

- Index ignore rules were rewritten to the new paths, leaving old-root index residue committable (reported by
  rpg-feature-planning; fixed by `TCK-20261003-OLD-ROOT-RESIDUE-GUARD`, #293).
- `.claude/workflows/implement-ticket.js` used two helpers before defining them, so a native run fails at Scope; present
  before the move, found while attempting the AC 9 run (fixed by `TCK-20261003-IMPLEMENT-TICKET-JS-USE-BEFORE-DEFINE`, #295).
- A running session's `search_docs` MCP server kept pointing at the old index path until restarted.
- A stale monitoring shard at an old path held a row the new shard lacked; documented in the path map's cleanup section.

## Not established

Whether any consumer builds these paths without writing the slash (the guard test covers live Python); the exact count of
open tickets that cited moved paths.
