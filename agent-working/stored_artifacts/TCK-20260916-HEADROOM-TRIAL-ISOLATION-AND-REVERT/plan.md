# Plan — TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT (second pass)

1. Ask the user to run the install themselves in their own shell (`.venv/bin/python3 -m pip install
   headroom-ai`, base package, no extras) — the sandbox's own `files.pythonhosted.org` block cannot
   be routed around from inside an agent session, and shouldn't be.
2. If it fails there too, return to `BLOCKED` and stop. It succeeded, so continue.
3. Verify `requirements.txt` and `.venv313` are untouched (hash/`pip show`), then record the
   dependency in `requirements-knowledge.txt` only.
4. Build `tools/start_headroom_mcp.sh`, modeled directly on `tools/start_search_mcp.sh`'s
   absolute-shared-path-first resolution, setting `HEADROOM_WORKSPACE_DIR` to an isolated,
   `.gitignore`d directory before invoking `headroom mcp serve`.
5. Register it in this repo's own `.mcp.json` by hand — never `headroom mcp install` or
   `headroom wrap`, both confirmed (the latter from the plan doc, the former newly from the real
   CLI's own `--help`) to write to every detected agent's user-scope config.
6. Demonstrate every acceptance criterion with real, observed evidence (`claude mcp list` from two
   different directories; a real file written under the isolated workspace dir; `~/.claude.json`
   parsed structurally before/after) rather than asserting from source or file location alone.
7. Write and execute the revert runbook as two paired git commits (setup, then revert) plus the
   matching filesystem cleanup, so the repo's tracked content and its installed dependency state
   both return to exactly their pre-ticket condition.
8. Update the ticket, the epic ticket, and the plan doc to reflect: this child is DONE; the network
   gate is resolved via the user's own shell but recurs per-session for any future child that needs
   the package actually present (registration itself an agent session can re-apply on its own).
9. Close via the standard hand-orchestrated path: `stored_artifacts/`, `record_hand_orchestrated_
   closure.py`, `docs/REGISTRY.yaml` regeneration.
