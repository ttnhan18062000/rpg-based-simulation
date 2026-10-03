---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261003-AGENT-WORKING-ROOT-MOVE
phase: open
date: 2026-10-03
tags: [ai, process-improvement, governance]
---

# TCK-20261003-AGENT-WORKING-ROOT-MOVE

## Title
Move agent-working state under one `agent-working/` root: path constants first, then one quiet-window move, history frozen

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary

Agent-working state is spread over the repo root: `tickets/`, `stored_artifacts/`, `staging_artifacts/`,
`agent-monitoring/`, `agent-orchestration/`, `pilot_requests/`, `reviews/`, plus three generated index folders.
The owner decided (2026-10-03) on **one `agent-working/` root**. This is milestone M-1 of
`TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION`, ahead of M0, because every later session-layer ticket cites these
paths and re-pathing afterwards would mean doing the work twice.

Owner decisions (2026-10-03): single root; `registries/` stays out; **closed history is frozen**; `tools/` stays
out; `experiments/` stays out; `reviews/` moves.

Measured on `origin/main` 5d49a67c7 (counts of tracked files; refs = files in `src tools tests .github Makefile
.claude .mcp.json pyproject.toml` that mention the path):

| Folder | Files | Live refs |
|---|---|---|
| `tickets/` | 2,465 | 163 |
| `stored_artifacts/` | 4,963 | 78 |
| `staging_artifacts/` | 16 | 77 |
| `agent-monitoring/` | 153 | 215 |
| `agent-orchestration/` | 22 | 43 |
| `pilot_requests/` | 2 | 13 |
| `reviews/` | 1 | 10 |
| `agent-monitoring-index/`, `knowledge-index/`, `parity-index/` (untracked, generated) | 0 | 12 / 20 / 7 |

## Scope

**Target layout (prefix-only: every moved path is `<old path>` with `agent-working/` in front; no renames
inside the root, so the live-reference rewrite is one rule).**

```
agent-working/tickets/  stored_artifacts/  staging_artifacts/  agent-monitoring/
agent-working/agent-orchestration/  pilot_requests/  reviews/
agent-working/.index/{agent-monitoring-index,knowledge-index,parity-index}   (generated, gitignored)
```

Stage 1 — **path constants (no folder moves).** One module (for example `tools/agent_working_paths.py`) is the
only place that names these roots. Migrate every live consumer onto it: `tools/`, `src/`, `tests/`, Makefile,
`.github/workflows/test.yml`, hooks, `Workflow` scripts, `.mcp.json`, and the `search_docs` / registry
generators. Add a test that fails on a hardcoded old root in live code. Ships and merges on its own.

Stage 2 — **the move, in one quiet window** (no open PRs, implementer idle, no other worktree writing
monitoring shards). `git mv` the folders; a rewrite script touches **live references only**; the constants
module changes value. Includes:
- `.gitignore` rules (`reviews/*`, `stored_artifacts/**/*.json` and its `manifest.json` exception, the three
  index folders) and `.gitattributes` merge rules (`agent-monitoring/data/*/*.jsonl`, `tickets/working_log.csv`);
  re-run `make setup-merge-drivers` and verify the driver patterns still match.
- CI: the `agent-orchestration` job's path filters and junit names in `.github/workflows/test.yml`.
- Instruction files: `CLAUDE.md`, `AGENTS.md`, `.claude/settings.json` hook commands, agent role prompts.
  **Governing files: the owner confirms each literal diff before it lands** (existing rule).
- Open work is live, so it is rewritten: `tickets/todos/**` and `tickets/inprogress/**`, `docs/**` (outside the
  archive), skill and agent prompts.

Stage 3 — **validate and rebuild.** Frontmatter, ticket-location-consistency, registry, `done_checker`, working-log
and monitoring validators; regenerate `docs/REGISTRY.yaml`; `make knowledge-index-update`; rebuild the index
folders; rebuild the `search_docs` index in every worktree; `graphify update .`.

**Everything that points at the old paths is updated, not only code** (owner, 2026-10-03). Folders in `tools/`,
`.claude/` and `.agents/` stay put; their *contents* change. Live files naming a moved root, first count
(lower bound; the investigation produces the exact list and a checklist the ticket closes against):

| Group | Files | Examples of what changes |
|---|---|---|
| `tools/` | 138 | path constants, hooks' data dirs, `agent-monitoring/`, `gate_checks/`, `delivery/`, working-log and registry generators |
| `tests/` | 172 | fixtures and pinned paths (check line pins and hook-shape tests before editing) |
| `docs/` (non-archive) | 197 | guides, plans, mechanics citations, `delivery_process.md`, `CLAUDE.md`-linked docs |
| `.claude/workflows/` | 8 | `implement-ticket.js`, `implement-epic`, `create-tickets`, simulation workflows: staging/stored/ticket paths in prompts and code |
| `.claude/agents/` | 9 | role prompts (investigator, planner, implementer, done-checker, ...) |
| `.claude/skills/` and `.agents/` | 5 + 8 | skill bodies and the mirrored `.agents` copies; keep both in sync |
| `agent-orchestration/` | 9 | contract, gate-policy, hook-surface and monitoring-schema YAML, role files |
| `.claude/settings.json`, `Makefile`, `.gitignore`, `.gitattributes`, `.mcp.json` | 1 + 1 + rules | hook commands, make targets, ignore and merge rules |
| `src/` | 13 | any runtime reads of these roots |
| `CLAUDE.md`, `AGENTS.md` | 2 | the Workflow, Ticket Format and After-Work rules; owner confirms each diff |

Also: update the `docs/REGISTRY.yaml` generator inputs, the `search_docs` / knowledge-index source globs, the
graphify inputs, the `docs/` frontmatter-validator location rules (`check_ticket_location_consistency` for
`tickets/done/`), and each skill or agent that embeds a command line (`tools/...`) with a moved path argument.
Done criterion: a repo-wide search for each old root (excluding the frozen set) returns zero hits, and a
`Workflow` dry run of `implement-ticket` on a hotfix-shaped test ticket finds every path it needs.

**History is frozen.** Not rewritten: `tickets/done/**`, `stored_artifacts/**` content, `tickets/working_log.csv`
rows, `docs/archive/**`, past monitoring shards. They keep citing the pre-move paths. A short
**pre-move path map** (a doc plus a resolver helper used by registry and validators) says how to resolve an old
citation. Validators that follow citations must accept a frozen pre-move path and resolve it through the map.

## Out of Scope

- `registries/`, `tools/`, `experiments/`, `docs/` (shared documentation tree), `config/`, `data/`, `src/`,
  `.claude/`, `.agents/`, `CLAUDE.md`, `AGENTS.md`, `skills-lock.json` stay where they are (this ticket changes
  their *contents* only where they cite a moved path).
- Renaming anything inside the new root (for example `agent-monitoring` to `monitoring`); a later ticket may.
- Rewriting closed tickets, stored artifacts, archived docs or past shards.
- Moving agent-working tools out of `tools/`.
- Any session-layer feature (registry, launcher, recovery); this ticket only makes their paths stable.

## Acceptance Criteria

1. After Stage 1, no live code names a moved root outside the constants module; the guard test fails on a
   seeded hardcoded path.
2. After Stage 2, none of the seven root folders (or the three index folders) exists at the repo root; all are
   under `agent-working/`; `git log --follow` works on a sampled ticket and a sampled shard.
3. No frozen file is modified (diff of `tickets/done/`, `stored_artifacts/`, `docs/archive/`, `working_log.csv`
   rows and past shards is rename-only).
4. The pre-move path map resolves a sampled old citation from each of the seven folders; registry and validators
   pass with frozen citations present.
5. Every validator named in Stage 3 passes; `docs/REGISTRY.yaml` regenerated; indexes rebuilt; `search_docs`
   returns a moved ticket and a moved stored artifact.
6. Monitoring still records after the move: a hook-recorded event and a `record_hand_orchestrated_closure.py`
   run both land in `agent-working/agent-monitoring/data/YYYY-Www/`; a second worktree writing a shard merges
   cleanly under the `merge=union` rule.
7. `make` targets, the CI workflow and the documented commands in `CLAUDE.md` / `docs/guides/delivery_process.md`
   work with the new paths on a clean clone at the PR's head SHA (not from `/tmp`).
8. Every `CLAUDE.md` / `settings.json` change was confirmed by the owner against the literal diff.
9. **Config sweep.** A search of the live set (tools, tests, docs outside the archive, `.claude/{skills,agents,
   workflows}`, `.agents/`, `agent-orchestration/`, Makefile, CI, ignore and attribute files) finds no old
   root; the checklist in the investigation shows each group closed. A hand-run `implement-ticket` hotfix on
   a throwaway ticket (the owner's opt-in for the `Workflow` run) completes with its monitoring records in the
   new location.

## Related Tickets

- Parent epic: `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (milestone M-1, before M0).
- Evidence for the ripple: `TCK-20260903-MONITORING-DATA-DOCS-SWEEP` (an earlier path-sweep that missed
  references), `TCK-20260802-STORED-ARTIFACT-KIND` (`stored_artifacts/` as a registry-indexed kind).

## Related Docs

- `docs/guides/delivery_process.md`, `docs/guides/agent_session_reset_boundaries.md`
- `docs/plans/agent_infrastructure/session_layer_working_process.md` (needs the M-1 milestone line)
- `agent-orchestration/README.md`

## Related Stored Artifacts
(None yet.)

## Related Code Areas
`tools/` (all path consumers), `tools/agent-monitoring/`, `tools/gate_checks/`, `tools/delivery/`,
`tools/generate_registry.py`, `.claude/settings.json`, `.claude/workflows/`, `.github/workflows/test.yml`,
`Makefile`, `.gitignore`, `.gitattributes`, `tests/`.

## Assumptions / Open Questions

- Assumed: prefix-only layout (the owner may prefer renames later; deferred).
- To measure in the investigation, not assume: how many live consumers compute paths from `__file__` or cwd
  (a first count found 6 `Path(__file__)` users naming these roots, which is a lower bound); how many open
  `tickets/todos/` files cite moved paths; whether any worktree or branch has unmerged shard writes at move time.
- The quiet window needs the owner's go and the implementer idle; no open PRs at that time.

## Implementation Notes
Stages 1 and 3-prep merge independently; Stage 2 is one PR. The implementer commits (design hands drafts).

## Test Summary
Defined at planning.

## Files Changed
(Open.)

## Completion Summary
(Open.)
