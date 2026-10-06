---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261006-HANDOVER-NOTES-RESOLVE-FROM-MAIN-CHECKOUT
phase: done
date: 2026-10-06
tags: []
---

# TCK-20261006-HANDOVER-NOTES-RESOLVE-FROM-MAIN-CHECKOUT

## Title
Handover notes resolve from the main checkout, not from the tree a tool or session runs in

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`.claude/handover/` is gitignored, so handover notes and drafts exist only in the main checkout. Seats now run in
worktrees (`launch.py` puts each seat in `<main checkout>/.claude/worktrees/<name>`), and the main checkout lacks
`launch.py`, so the owner must run it from a worktree too. Four sites resolve the handover dir against the
current tree instead of the main checkout, so from any worktree they see no notes.

Found by the designer seat's `launch.py agent-working-designer --dry-run` from a detached origin/main worktree
(`ae4388854`), 2026-10-06: the real `agent-working-designer.md` exists in the main checkout, yet the dry run
printed "no handover note yet: a stub will be created". A real launch would write an empty stub into that tree and
the new session would start from the stub. This blocks the owner's live probe (LIVE-SESSIONS AC5, epic D's M7 clock).

Sites on origin/main:
1. `tools/sessions/launch.py:291` (`plan_launch`) and `:372` (`main`, the stub write): `root / role.handover`,
   where `root` is `_REPO_ROOT` (the tree that holds the running `launch.py`). The worktree path (`main_checkout(root)`)
   and the state dir (`st.state_root`, git common dir) already resolve from the main checkout; the handover is the
   odd one out.
2. `tools/agent-monitoring/session_start_handover_hook.py:22`: `HANDOVER_DIR = Path(".claude/handover")`, relative
   to the session's cwd. A launched seat's cwd is its worktree, so on `/clear` it lists nothing.
3. `tools/handover_transit.py:38`: same cwd-relative `HANDOVER_DIR`. `memory_dir_candidates()` in the same file
   already resolves the main checkout through `git rev-parse --git-common-dir`; the handover dir should follow.
   (#376's export refusal from a worktree that lacks the main-checkout drafts is this bug's symptom.)
4. The generated `.claude/agents/session-*.md` text: "handover `.claude/handover/<role>.md`" and "Drafts:
   `.claude/handover/drafts/`". Read relative to the worktree cwd, these paths do not exist.

## Scope
- One shared helper that returns `<main checkout>/.claude/handover` (git common dir's parent, the same rule as
  `launch.main_checkout` / `handover_transit.memory_dir_candidates`). Put it where sites 1–3 can all import it
  without a new cross-package cycle. Reuse `main_checkout` if that fits.
- Sites 1–3 use it. Keep the existing injectable parameters (`handover_dir=` in transit, the hook's
  `build_additional_context(handover_dir)`) so tests still pass a tmp dir.
- Site 4: the generator states that the handover and drafts paths are on the main checkout (absolute or
  "on the main checkout"; implementer's choice), then regenerate `.claude/agents/session-*.md` with
  `tools/sessions/generate_agents.py`.
- Fallback when git is unavailable: the current behaviour (cwd-relative). That matches `memory_dir_candidates`.

## Out of Scope
- Moving existing notes that sit in worktrees today (for example `agent-working-implementer`'s note in the
  `doc-tag-enforcement` worktree). Report them in the completion summary. The owner moves them.
- Creating the `.claude/worktrees/agent-working` seat worktree, or recording a branch for the role
  ("no branch is recorded for this role, so it is not recreated"). That is owner-side, before the live probe.
- Symlinking `.claude/handover` into worktrees. Rejected: the gitignore pattern `.claude/handover/` matches
  directories only, so a symlink would show as untracked in every seat worktree.

## Acceptance Criteria
1. Run from a secondary worktree with a note present only in the main checkout, `launch.py <role> --dry-run` does
   not print "no handover note yet", and a real (non-dry) path writes no stub in the secondary worktree. Test
   in `tests/tools/test_session_launch.py` with a real `git worktree add` in tmp.
2. The SessionStart hook, run with cwd = a secondary worktree, lists the main checkout's notes. Test in
   `tests/tools/test_session_start_handover_hook.py`.
3. `handover_transit export --dry-run` from a secondary worktree collects the main checkout's notes and drafts.
   Test in the transit suite.
4. Regenerated `session-*.md` files name the main-checkout location for the handover and drafts paths;
   `test_session_agent_generator.py` passes and covers the new wording.
5. No-git fallback is unchanged (existing tests still pass).

## Related Tickets
- TCK-20261004-HANDOVER-CROSS-MACHINE-TRANSIT, #376 (transit export guard)
- session-layer epics (LIVE-SESSIONS AC5; epic D's M7 clock waits on the first real launch)
- TCK-20260921-SESSION-CONTEXT-RESET-TRIAL (made `.claude/handover/` gitignored, one note per role)

## Related Docs
- `docs/guides/agent_session_reset_boundaries.md` (handover note location; update it if it implies cwd-relative)
- `docs/guides/delivery_process.md` ("Worktree & Branch Isolation")

## Related Stored Artifacts
None.

## Related Code Areas
`tools/sessions/launch.py`, `tools/sessions/state.py`, `tools/sessions/generate_agents.py`,
`tools/agent-monitoring/session_start_handover_hook.py`, `tools/handover_transit.py`, `.claude/agents/session-*.md`

## Assumptions / Open Questions
- Assumes the main checkout stays the single home for handover notes, as #376's export already treats it.
  No question is open for the owner.

## Implementation Notes
Hand-orchestrated hotfix: record closure with `record_hand_orchestrated_closure.py --tier hotfix`.
Pass `--path-reason` if you take the hotfix path deliberately.

## Test Summary
New: 3 launch tests (real `git worktree add`: dry run, real launch writes no stub, plan_launch), 1 hook test (cwd = secondary worktree), 1 transit test (default dir resolves to the main checkout from a worktree), 1 generator wording test. Existing transit tests now patch `_main_handover_dir`. `pytest tests/tools -k "session or handover or card or roster or frontmatter or guard or agent_working_paths"`: 1108 passed.

## Files Changed
`tools/handover_home.py` (new), `tools/sessions/launch.py`, `tools/sessions/session_start_hook.py`, `tools/sessions/card.py`, `tools/agent-monitoring/session_start_handover_hook.py`, `tools/handover_transit.py`, `.claude/agents/session-*.md` (regenerated), `docs/guides/agent_session_reset_boundaries.md`, tests under `tests/tools/`.

## Completion Summary
One stdlib-only helper (`handover_home.py`: git common dir's parent, cwd-relative fallback without git) now serves launch.py (2 sites), the old SessionStart hook, `handover_transit`, and a fifth site the draft did not list: `tools/sessions/session_start_hook.py` (`_handover_text` and the clear fallback). Card wording: the role line now reads "Worktree X; main-checkout `.claude/handover/<role>.md`"; the card budget (400 tokens) had zero slack, so the designer "Drafts:" line is unchanged (drafts sit under that same dir). Not moved (owner): notes that sit in worktrees today, e.g. `agent-working-implementer`'s note in the `doc-tag-enforcement` worktree.
