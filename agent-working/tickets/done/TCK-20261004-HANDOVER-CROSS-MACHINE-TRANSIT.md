---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-HANDOVER-CROSS-MACHINE-TRANSIT
phase: done
date: 2026-10-04
tags: [ai, hooks, process-improvement]
---

# TCK-20261004-HANDOVER-CROSS-MACHINE-TRANSIT

## Title
Carry session handover notes (and untracked drafts) between machines through a committed, temporary transit bundle under `agent-working/`

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner request (2026-10-04): three sessions (roles) must move from another machine to this one and keep their handover. Today `.claude/handover/` is gitignored (`.gitignore:318`), so notes and the untracked `.claude/handover/drafts/` tree exist only on the machine that wrote them. A session transcript does not cross machines either (resume is keyed by session id and the transcript lives under the local `~/.claude/projects/` dir), so the handover note is the only continuity that can cross. Nothing in the repo moves it.

## Scope
- New `tools/handover_transit.py` with four subcommands:
  - `export [--roles a,b,c] [--no-drafts] [--no-memory]`: copies selected `.claude/handover/<role>.md` (default: all) into `agent-working/handover-transit/<host>/` (one rolling bundle per source host: each export replaces that host's previous bundle, so `main` carries at most one small current bundle per machine), writes `MANIFEST.jsonl` (one row per file: relative path, sha256, bytes, source host, source `git rev-parse HEAD`, exported-at). Drafts: the whole `.claude/handover/drafts/` tree, because it is untracked and lost otherwise. Memory: the local project memory dir (`~/.claude/projects/<slug>/memory/`, `MEMORY.md` plus topic files), included by default (owner 2026-10-04: the remote is acceptable for it); `--no-memory` opts out.
  - `import <host>`: verifies every sha256, copies to `.claude/handover/` (and the local memory dir, mapping the slug for this machine's checkout path), never overwrites a differing local file silently: writes `<name>.local-backup-<ts>` first and prints each replacement. `--dry-run` lists actions. Idempotent (re-import of identical bytes is a no-op).
  - `status`: lists bundles on disk with age and whether this machine already imported each (marker file `.imported-<host>` inside the bundle).
  - `discard <host>`: `git rm -r` the bundle once every machine that needs it has imported. Refuses if no destination has an `.imported-*` marker unless `--force`.
- Storage rule: files are stored with a `.txt` suffix appended (`agent-working-design.md.txt`) so doc registry, frontmatter validators and the knowledge index never see them as docs; import strips it. Implementer verifies this against `validate_frontmatter.py`, `docs/REGISTRY.yaml` generation and the `.gitignore` rules for `agent-working/` (precedent: stored_artifacts `.json` is dropped by gitignore, use `.jsonl`/`.txt`).
- Delivery rule (owner 2026-10-04): the bundle is committed with every PR that is opened. `export` is a step of the PR lifecycle in `docs/guides/delivery_process.md` (run before the final commit that precedes opening the PR; the implementer decides whether `tools/delivery/` calls it or the guide lists it). The bundle is rolling and temporary in content, never a history store: git history keeps old versions, the tree holds one. Pushes still need the owner's go as today.
- `session_start_handover_hook.py`: on `source` of `startup`, `resume` or `clear`, when `agent-working/handover-transit/` holds a bundle without this host's `.imported-` marker, add one line naming the bundle id and the `import` command. Read-only, fails open, same contract as today's hook.
- `docs/guides/agent_session_reset_boundaries.md`: a short "Moving sessions between machines" section (export, push the transit branch, pull, import, start a fresh session per role, discard). Handover note format unchanged.
- Tests: manifest round-trip, sha mismatch aborts before any write, differing local file gets a backup, `--dry-run` writes nothing, idempotent re-import, memory slug mapping, `.txt` suffix strip, `discard` refusal without an import marker, hook notice present/absent and fails open.

## Out of Scope
- Moving session transcripts or `claude --resume` across machines.
- Any automatic push, pull or merge. Export only writes files into the working tree.
- Encrypting the bundle (owner accepted the remote's visibility).
- Changing the handover note format or the reset-boundary map.

## Acceptance Criteria
1. `export` then `import` on a second checkout reproduces notes, drafts (and memory when requested) byte-for-byte; manifest hashes match.
2. A corrupted or tampered file aborts the whole import before any local write.
3. No local file is lost: a differing destination file is backed up and reported.
4. A transit bundle in the tree (including on `main`) produces no docs-registry row, no frontmatter-validator failure and no knowledge-index entry.
5. The hook lists a pending bundle once per session start and prints nothing when none is pending or on any error.
6. `discard` removes the bundle and refuses without an import marker unless `--force`.
7. The guide section and `delivery_process.md` name the per-PR export step and the one-bundle-per-host rule.

## Related Tickets
- `TCK-20260921-SESSION-CONTEXT-RESET-TRIAL` (origin of the hook and the note format)
- Session-layer epics under `agent-working/tickets/todos/session-layer/` (M2 role-state dir and recovery by role id; this ticket is the cross-machine counterpart, same role-keyed identity)

## Related Docs
- `docs/guides/agent_session_reset_boundaries.md`
- `docs/plans/agent_infrastructure/session_layer_working_process.md` (section 6.1, recovery keyed by role id)

## Related Stored Artifacts
none

## Related Code Areas
- `tools/agent-monitoring/session_start_handover_hook.py`
- `tools/handover_transit.py` (new)
- `.gitignore` (line 318)

## Assumptions / Open Questions
- Assumes the two machines share the git remote. If they cannot, the same bundle works over any file copy (the manifest is self-contained); no code change.
- Decided by the owner: the remote may carry memory files; the bundle rides along with each PR.
- Risk to check: a stale rolling bundle on `main` overwriting a newer local note on import. Import backs up differing files and prints timestamps; the guide says to export on the machine being left, then import on the new one.
- Open for the implementer: whether the M2 role-state dir should also be a bundle member once it exists (not needed for this ticket).

## Implementation Notes
Bundle layout: `<host>/MANIFEST.jsonl` plus `files/{handover,memory}/<path>.txt`. Import verifies all sha256 and rejects absolute/`..` manifest paths before any write. The hook matcher was already `*`, so widening to startup/resume/clear needed no settings.json edit; the note listing stays clear-only. Open question (M2 role-state dir as a bundle member) left for the M2 work.

Amendments (owner, 2026-10-04, same PR): (1) the export carries only OPEN state: a draft is skipped when its ticket is in `done/` or tracked on `origin/main`, under an `evidence` directory, in a folder whose ticket drafts are all finished, or byte-identical to a file on `origin/main` (`--include-all` restores); (2) every manifest row records `belongs_to` {role, domain, ticket_id, branch, kind} plus the exporting worktree and branch, drafts take the exporting role (`--role`, or `SESSION_ROLE`, never guessed; unresolved is `unattributed` and flagged); (3) `import --role` copies only that role's items plus memory and lists the rest as skipped; `status` and the SessionStart line group by role. Result on the author's machine: 228 files -> 172 (40 handover, 132 memory); the remaining handover drafts are patches and READMEs with no ticket id that the tool cannot prove merged.

## Test Summary
`tests/tools/test_handover_transit.py` (32 tests) + `tests/tools/test_session_start_handover_hook.py`: all pass. Real export of 223 files produced no registry row; registry regen clean.

## Files Changed
tools/handover_transit.py (new); tools/agent-monitoring/session_start_handover_hook.py; tests/tools/test_handover_transit.py (new); docs/guides/agent_session_reset_boundaries.md; docs/guides/delivery_process.md; agent-working/handover-transit/ (first rolling bundle).

## Completion Summary
Export/import/status/discard shipped with the hook notice and the per-PR export step documented. Pushes remain the owner's go.
