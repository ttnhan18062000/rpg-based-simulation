---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-11
tags: [architecture, planning]
---

# Batch brief: knowledge-lock-transit-test (codebase-planner, 2026-10-11)

Requested by lead-planner (work message 2026-10-11, owner-authorized), confirmed by the owner in the
codebase-planner session ("Yes, take both"). Tier: hotfix, one ticket each, ONE PR.
Branch `knowledge-lock-transit-test`, a fresh worktree `~/Work/rpg-knowledge-lock-transit-test` off
origin/main (e87091592 at brief time). Do NOT touch `~/Work/rpg-import-linter-flip`.

Cross-domain exception (state it in BOTH tickets and the PR body): #513 and #514 are labelled
for:agent-working-planner, and `tests/tools/**` / `tools/**` belong to agent-working. That seat is unstaffed, so
codebase takes this batch on lead-planner's request with the owner's confirmation. `pyproject.toml`, `uv.lock`
and `Makefile` are lead-owned: lead-planner approved the edit and reviews the diff by PR comment.

## T1: TCK-20261011-HANDOVER-TRANSIT-TEST-HOME-ISOLATION (Refs #513, part 1 only). START HERE.

- Problem: `tests/tools/test_handover_transit.py::test_default_memory_dir_slug_maps_checkout_path` calls
  `ht.default_memory_dir()` against the real `~/.claude/projects`. It fails on this VM because both
  `-data-vboxuser-Work-rpg-based-simulation/memory` and `-home-vboxuser-Work-rpg-based-simulation/memory` hold files.
- Fix: test-only. Point `HOME` (monkeypatch env + `Path.home` if `memory_dir_candidates`/`_root_aliases` use
  it) at `tmp_path`, so candidates resolve under a tmp `.claude/projects`. Keep the slug assertions. Add one
  case each: (a) one filled candidate → that one; (b) two filled → `TransitError` (the refusal is correct
  behavior; pin it). No change to `tools/handover_transit.py` unless the HOME redirect is impossible without
  a seam; if it is, stop and tell me first.
- NEVER read, write, move or merge the real memory dirs. Part (2) (the merge) is the owner's.
- Verify: the test passes on this VM (it fails on main now: show red → green), plus
  `.venv/bin/python3 -m pytest tests/tools/test_handover_transit.py -q`.

## T2: TCK-20261011-KNOWLEDGE-TORCH-CPU-INDEX-IN-LOCK (Closes #514). RELEASED 2026-10-11: lead chose OPTION 2.

Why: download.pytorch.org is blocked on u24desktop-Virtual-Machine (agent_working_environment.md, "Why the knowledge
stack is stuck on 3.12"), so a lock that owns a CPU index could not be re-resolved there. Option 2 makes the lock and
the comments tell the truth at zero risk. (Rename the ticket title to match; keep the ID.)

Scope:
1. `pyproject.toml` `knowledge` extra comment, stated plainly: `uv.lock` resolves torch from PyPI (the CUDA build);
   `.venv-knowledge` (3.12) is built by the manual CPU-wheel step instead, so it is NOT lock-reproducible; do not
   `uv sync --extra knowledge` expecting the CPU env. Cite agent_working_environment.md for the why.
2. `Makefile` `PYTHON_KNOWLEDGE`: drop the `/home/u24desktop/...` candidate. Add an env/make override
   (`KNOWLEDGE_PYTHON`, used verbatim when set), then the main checkout's `.venv-knowledge` via
   `git rev-parse --path-format=absolute --git-common-dir`, then the repo-relative `.venv-knowledge`, then `python3`.
3. `tools/start_headroom_mcp.sh`: the same swap (drop the u24desktop literal; honour `KNOWLEDGE_PYTHON`), ONLY if it
   is a path swap. `tests/tools/test_mcp_launcher_hardening.py` asserts on candidate ORDER: updating an assertion
   that names the removed literal is part of the change; never weaken an ordering check to pass. If it needs more
   than that, leave it out and note it in the ticket as an agent-working follow-up.
4. Docs: `requirements-knowledge.txt` header + `docs/guidelines/agent_working_environment.md` mention of the Makefile
   path / override, if any. Then `make knowledge-index-update`.
5. On close, the #514 closing comment carries the REVISIT TRIGGER: option 1 becomes viable once download.pytorch.org
   is reachable from every working host (unblocking the filter is the owner's call).

Guards: `uv.lock` MUST NOT change. If it does, STOP and tell me. Verify `uv lock --check` passes, the Makefile
resolves on this VM (`make -n` / `make print`-style check of PYTHON_KNOWLEDGE, with and without KNOWLEDGE_PYTHON), and
`pytest tests/tools/test_mcp_launcher_hardening.py` is green.

## Close
Hotfix closure per CLAUDE.md (hand-orchestrated → `record_hand_orchestrated_closure.py`, done_checker_static,
mechanism-registry advisory). Commit subjects `TCK-...: ...`. No push: report shas to me; push/PR/merge = owner.
