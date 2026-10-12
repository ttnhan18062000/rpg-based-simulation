---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-12
tags: [architecture, planning]
---

# Brief: mypy pin hotfix + #520 shared search model (codebase-planner, 2026-10-12)

Requested by lead-planner (decision message 2026-10-12); confirmed by the owner in the codebase-planner session
("Both, (1) then (2)"). Order: (1) first, then (2). ONE PR EACH. Pushes: ask the owner as usual. lead-planner
reviews and merges (owner grant).

## (1) TCK-20261012-MYPY-DEV-PIN (hotfix, P3). Branch `mypy-dev-pin`, fresh worktree `~/Work/rpg-mypy-dev-pin` off origin/main.

- `pyproject.toml` dev group: `"mypy"` → `"mypy==2.1.0"`, with a short comment in the style of the neighbouring pins
  (TCK id; "equals the version uv.lock resolves; bump together"). lead-planner approved the edit as path owner.
- Guards: `uv.lock` resolves `mypy 2.1.0` today (uv.lock:1176-1177). After the edit, `uv lock --check` passes and
  `git diff origin/main -- uv.lock codebase/baselines/` is EMPTY. If the lock wants to change: STOP and tell me.
- Tests: `tests/static` (CI pin tests, cf. the memory "re-run CI pin tests after dep change") + `tests/codebase`.
- The flip batch brief lives only on the LOCAL branch `import-linter-flip` (~/Work/rpg-import-linter-flip, not on
  main), so the hotfix PR cannot edit it. Instead add one commit on `import-linter-flip` (TCK-20261005-IMPORT-LINTER-FLIP-
  AND-TEST-RETIREMENT subject) removing T2 from `docs/plans/codebase_health/import_linter_flip_batch_brief.md` with a
  one-line pointer "T2 landed standalone as TCK-20261012-MYPY-DEV-PIN (PR #N)". No push of that branch.

## (2) TCK-20261012-SEARCH-MCP-SHARED-MODEL (Refs #520). STANDARD tier: investigation + plan FIRST, no code until I approve.

Unstaffed-seat exception: `tools/**` is agent-working's; say so in the ticket and the PR. `.mcp.json` is lead-owned:
any change to it goes to lead for review.

Facts already established (planner scan, main e0f88c5f0):
- `tools/search_mcp.py` `_ensure_loaded()` is ALREADY lazy (model loads on the first query), but every session
  queries early (CLAUDE.md requires search_docs first), so in practice each session holds ~200–630 MB.
- Nothing listens on :8765 now. `make search-server-docker` image build is recorded "unverified"
  (agent_working_environment.md); `make search-server` is the uvicorn fallback.
- `tools/search_server.py` `/api/search` has its OWN search path (its own SQL, filters, excerpt), not
  `search_mcp._search` (hybrid/BM25 modes, section filter, staleness wrapper). A plain proxy would change results.

Investigation must answer (into investigation.md, with numbers):
1. Baseline: RSS per `search_mcp.py` process now (ps/smem), count of live processes, idle vs after first query.
2. Result parity: same query → same top-k from server vs in-process? Expect NO today; list the differences.
3. Server availability: can `make search-server-docker` build/run on this VM; which venv runs `make search-server`;
   which index it reads (main checkout's), and from a worktree session.
4. Who starts the shared server and keeps it alive (owner-run docker / systemd user unit / auto-spawn by
   `start_search_mcp.sh` with a lock), and what happens when it dies mid-session.

Plan options to compare in plan.md (recommend one):
- A. Proxy: `search_mcp.py` calls the shared server when it answers; the server and the MCP share ONE core search
  function (move it to a shared module), so results are identical by construction; in-process fallback.
- B. Idle unload: keep in-process, drop the model after N minutes idle (gc + malloc_trim), reload on demand. No
  daemon; measure reload latency and the saving with realistic query cadence.
- C. A + auto-spawn: first session starts a detached shared server (lockfile), others proxy.

Hard constraints: identical top-k for the same query between proxy and in-process (add the test); the staleness
warning keeps working; worktree sessions keep working (index fallback to the main checkout); `start_search_mcp.sh`'s
u24desktop candidate (#517) still resolves; do NOT remove it here. Measure RSS before/after for the chosen option
and put the numbers in the ticket.

Stop after investigation.md + plan.md are committed and send me the shas. I review, agree the option with lead
(`.mcp.json` impact), then release implementation.

## Close (each ticket)
Hand-orchestrated closure per CLAUDE.md. Commit subjects `TCK-...: ...`. Run tests/static + tests/tools for (2)
(Makefile/launcher lesson from #518). Report shas to me; no push without the owner's yes.
