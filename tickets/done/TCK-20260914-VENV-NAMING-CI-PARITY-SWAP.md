---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260914-VENV-NAMING-CI-PARITY-SWAP
phase: done
date: 2026-09-14
tags: [ai, process-improvement]
---

# TCK-20260914-VENV-NAMING-CI-PARITY-SWAP

> **Moved back to the backlog, 2026-09-20, at the user's direct instruction.** This is a
> **lifecycle correction only** — the ticket had sat in `tickets/inprogress/` with no further
> content change since 2026-09-15 (verified via `git log --follow`, not file mtime — mtime in a
> repo where worktrees are checked out constantly is close to meaningless as a staleness signal),
> and its presence there (along with several other stale `tickets/inprogress/` entries) was
> firing this repo's sidecar-check hook on every `Edit`/`Write` in every concurrent session on
> this machine. **Nothing about the ticket's own substance was investigated, debugged, or
> re-scoped as part of this move.**
>
> **The ticket's own premise is still live, worth recording so it isn't re-derived**: `.venv`
> (Python 3.12.3) holds the agent tooling; `.venv313` (Python 3.13.14) mirrors CI's own
> interpreter; and `.venv313` is **not matched by any `.gitignore` pattern** — untracked, but not
> ignored, in the main checkout. This is a real, current loose end this ticket exists to cover,
> not something that resolved itself while the ticket sat idle. Not fixed here — recorded so
> whoever picks this up next doesn't have to re-discover it.

> **Implemented and closed 2026-09-21.** The premise above was re-verified against current state
> before touching anything (`.venv` still 3.12.3, `.venv313` still 3.13.14 — unchanged) and found
> still live. The rename itself — the one specific step the prior investigation deliberately left
> for a live user decision — was authorized directly by the user via `AskUserQuestion` (literal `mv`
> commands shown, current concurrent-session count disclosed), not inferred from a peer's relay of
> batch approval alone. See Implementation Notes/Completion Summary below for what actually ran.

## Title
Default venv name points at the non-CI Python version — rename so `.venv` is the CI-matching environment

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
On u24desktop there are now two virtualenvs, deliberately (documented in
`docs/guidelines/agent_working_environment.md`):

- `.venv` — Python 3.12.3, holds the knowledge-search stack (`torch`, `sentence-transformers`)
- `.venv313` — Python 3.13.14, matches CI's declared `python-version: "3.13"`, used for engine/API/tests

**The naming is backwards relative to how the two are used.** `.venv` is the name every tool,
habit, and shell autocompletion reaches for by default, but it is the one that does *not* match CI.
A session running `.venv/bin/python3 -m pytest` — or bare `python3`, which is also 3.12 — gets a
green result that cannot rule out a version-specific CI failure.

That is not hypothetical: on 2026-09-14 two CI jobs failed with unreadable logs (network-filter
blocked), and the Python version gap could not be eliminated as a cause until a 3.13 venv was built
specifically to test it. Several hours were spent on a hypothesis that a correctly-named default
would have ruled out in one command. (The version gap turned out *not* to be the cause — 120 tests
passed identically on 3.13 against the failing commit — but ruling it out was only possible after
the fact.)

## Scope
- Rename so the CI-matching environment is the default-named one. Suggested shape, not mandated:
  `.venv` → `.venv-knowledge` (or similar explicit name), `.venv313` → `.venv`.
- Update `tools/start_search_mcp.sh`, which **hardcodes the absolute path**
  `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` as its first-priority
  candidate. This is deliberate — its own comment explains that per-worktree `$REPO_ROOT/.venv`
  never has the knowledge deps, so the absolute shared path must win. Any rename must update this
  or `search_docs` silently falls through to bare `python3` and stops working.
- Update `docs/guidelines/agent_working_environment.md`'s venv table to match.
- Check for any other hardcoded `.venv` references (Makefile targets, CI scripts, tooling).

## Out of Scope
- Migrating the knowledge stack to 3.13. **Not possible on this network**: `download.pytorch.org`
  is blocked by the content filter (`O = Fortinet, CN = Fortiguard SDNS Blocked Page`), so
  `torch==2.12.1+cpu` cannot be installed for any new Python version here. The 3.12 environment
  must be preserved as-is; it predates the block and cannot be rebuilt.
- Any change to which Python version CI uses.

## Acceptance Criteria
- [x] `.venv/bin/python3 --version` reports the same major.minor as `.github/workflows/test.yml`'s
      declared `python-version`. Confirmed: `Python 3.13.14` vs. CI's declared `"3.13"`.
- [x] `search_docs` still returns results after the rename — verified by a real query, not by the
      MCP server merely starting. `bash tools/start_search_mcp.sh --test <<< '{"query": "damage
      formula", "top_k": 3}'` returned 3 real results.
- [x] No remaining hardcoded reference resolves to the wrong environment (grep, don't assume).
      Full-repo sweep after the rename: zero live-tooling hits pointing at the old meaning; only
      correctly-unchanged `$(PYTHON3)` remained (intentionally still `.venv`, now CI-matching).
      Found and fixed 4 references beyond the ticket's own original Scope/plan: `tools/start_
      headroom_mcp.sh` (didn't exist when this ticket was investigated), `.gitignore` (would have
      recreated this exact ticket's own root problem for the new name), `pyproject.toml`'s pytest
      `norecursedirs`, and `tools/codebase_health_baseline.py`'s scan exclusion set.
- [x] The environment doc's venv table matches reality. Table swapped, "Run tests as" sentence,
      "must be preserved" paragraph, and first-time-setup `uv venv` recipe all updated to the new
      names; verified against real `--version` output.

## Related Tickets
- None directly. Adjacent in spirit to the CI-triage guidance in CLAUDE.md, which already documents
  the network-filter block for GitHub Actions log fetching — the same filter, different host.

## Related Docs
- `docs/guidelines/agent_working_environment.md` — the venv table, the network-block explanation,
  and the sudo-free `uv` install recipe were added 2026-09-14 alongside this ticket.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260914-VENV-NAMING-CI-PARITY-SWAP/` — `investigation.md` (baseline +
  hazards + a 2026-09-21 implementation-time addendum with 4 new hazards and one correction),
  `plan.md` (the exact diffs/commands, now marked executed), `test_plan.md` (the Step 3 checklist,
  now marked verified).

## Related Code Areas
- `tools/start_search_mcp.sh`
- `docs/guidelines/agent_working_environment.md`
- `.mcp.json` (references the launcher, not a venv path directly)

## Assumptions / Open Questions
- **Timing matters more than the change does.** The rename breaks `search_docs` for any session
  running at that moment, and this machine routinely has 8+ concurrent sessions sharing the one
  venv. Do it when sessions are quiet, not opportunistically.
- Unresolved: whether the knowledge stack should eventually move to a container (the search server
  already has a Docker path, `make search-server-docker`) so it stops depending on a host-installed
  torch that can no longer be reinstalled here. That would make the whole venv split unnecessary,
  but it is a larger question than this ticket.

## Implementation Notes
**2026-09-21: rename executed, at the user's direct go/no-go.** The prior pass (2026-09-15) left the
rename itself unexecuted by design — see the blockquote at the top and `plan.md`'s own preserved
"why this plan originally stopped short" section. This pass re-verified the premise was still live,
re-swept for new hazards (a week had passed and new tooling landed in between), then asked the user
directly rather than treating a peer's relay of batch approval as authorization for a shared-state
mutation the plan's own author had explicitly deferred:

- Showed the literal `mv` commands and the real current concurrent-session count (4 other
  interactive sessions, shown idle but not provably safe) via `AskUserQuestion`.
- User answered **"Proceed now"**, and separately confirmed **`.venv-knowledge`** as the final name.
- Executed Step 1 (file edits) and Step 2 (the `mv`) atomically, immediately back-to-back, per the
  plan's own ordering requirement.

**Two hazards from the original investigation, applied as planned:**
1. `tools/start_search_mcp.sh`'s hardcoded absolute path — updated to `.venv-knowledge/bin/python3`.
2. `Makefile`'s `knowledge-index`/`knowledge-index-update`/`eval-search` — now use a new top-level
   `PYTHON_KNOWLEDGE` variable instead of `$(PYTHON3)`. (Used `command -v`, not the plan's own
   literal `[ -x "$$py" ]` snippet, for the bare-`python3` fallback — matching the already-fixed
   `PYTHON` variable's own documented reasoning a few lines above it in the Makefile; reproducing a
   known bug in brand-new code next to the comment explaining why it's a bug would have been
   careless.)

**Four more hazards found during this implementation pass, beyond the original investigation**
(full detail in `investigation.md`'s Addendum): `Makefile`'s `mcp-server-test` target (same inline
discovery-loop shape as `eval-search`, missed by the original Hazard #2 list); `tools/
start_headroom_mcp.sh` (didn't exist at investigation time — the Headroom trial landed 2026-09-16
onward — hardcoded `.venv/bin/headroom`, same shape as Hazard #1); `.gitignore` (its `.venv` line is
an exact-name match, not a prefix — would have silently recreated this ticket's own root problem,
"untracked but not ignored," for the new `.venv-knowledge` name); `pyproject.toml`'s pytest
`norecursedirs` (same exact-name-match gap — a bare `.venv/bin/python3 -m pytest` run would have
tried to collect tests from inside the renamed knowledge venv's installed packages).

**One correction to the original investigation, caught this pass**: its Hazard #3 called
`tools/codebase_health_baseline.py`'s directory-skip set "directory-name-agnostic... unaffected by a
rename." That was wrong — it's an exact-string set, so it excludes the literal name `.venv`, not
"whichever env is the knowledge one." Added `.venv-knowledge` to the set.

**One genuinely stale test, updated rather than forced or ignored** (Gate Integrity):
`tests/tools/test_dashboard_makefile_targets.py::test_knowledge_index_targets_use_python3_variable`
pinned `$(PYTHON3)` for the knowledge-stack targets, correct when written
(`TCK-20260826-KNOWLEDGE-INDEX-PYTHON3-FIX`) but now genuinely wrong given this ticket's own
intentional change. Renamed and re-pointed at `$(PYTHON_KNOWLEDGE)`, extended to also cover
`eval-search`/`mcp-server-test` (a pre-existing coverage gap, closed while already there for the
rename's sake).

**Verified NOT hazards** (checked directly, not assumed): `tools/perf/live_map_ws_payload_measure.py`'s
docstring already says `.venv/bin/python3` and becomes correct, not stale, after the rename — no
edit needed, and editing it would have been a no-op miswrite. `tools/agent_codex_posttool_adapter/
command.py`, `.mcp.json`, and the two `experiments/spatial_rendering/` scripts are all general
app-deps tooling, same reasoning. `docs/parity_ledger/`, `tickets/working_log.csv`,
`registries/capability_envelope_registry.jsonl`, and `docs/ai/codex_posttool_adapter_exact_config_
diff_for_review.md` are historical evidence/baseline records — correctly left untouched, since
rewriting them would misrepresent what actually ran at the time.

## Test Summary
- Step 3 verification checklist (AC #1/#2/#3/#4): all passed — see `test_plan.md` for the exact
  commands and outputs.
- `pytest tests/tools/test_dashboard_makefile_targets.py -v` — 5 passed (1 updated for the
  intentional design change, matching Gate Integrity).
- `pytest tests/tools/ -k "codebase_health or knowledge or agent_codex_posttool or dashboard_makefile"
  -m "not slow and not extra_slow"` — 123 passed, 7 skipped, 0 failed.
- `pytest tests/tools/test_generate_registry.py tests/tools/test_done_checker_static.py tests/tools/
  test_done_checker_audit.py tests/docs/ -m "not slow and not extra_slow"` — 261 passed, 1 skipped,
  1 xfailed, 1 deselected (the real-registry drift check, expected-stale mid-implementation from
  this ticket's own in-progress ticket-location move — resolved by Finalize's registry
  regeneration).
- All commands run via `.venv/bin/python3` (now 3.13.14) post-rename, confirming the environment
  itself works for ordinary app testing, not just its own verification checklist.

## Files Changed
- `tools/start_search_mcp.sh`, `tools/start_headroom_mcp.sh` — absolute/relative knowledge-venv
  paths updated to `.venv-knowledge`.
- `Makefile` — new `PYTHON_KNOWLEDGE` variable; `knowledge-index`, `knowledge-index-update`,
  `eval-search`, `mcp-server-test` now use it instead of `$(PYTHON3)` or an inline discovery loop.
- `docs/guidelines/agent_working_environment.md` — venv table swapped, "Run tests as" sentence,
  "must be preserved" paragraph, first-time-setup `uv venv` recipe, all updated to match reality.
- `.gitignore` — added `.venv-knowledge`.
- `pyproject.toml` — added `.venv-knowledge` to pytest's `norecursedirs`.
- `tools/codebase_health_baseline.py` — added `.venv-knowledge` to the scanner's skip-dir set.
- `tests/tools/test_dashboard_makefile_targets.py` — updated the one genuinely stale pinned test.
- Host filesystem (not tracked by git): `mv .venv .venv-knowledge && mv .venv313 .venv`.
- `staging_artifacts/TCK-20260914-VENV-NAMING-CI-PARITY-SWAP/` (all 3 files updated with the
  implementation-time addendum and executed/verified status).

## Completion Summary
Executed the rename this ticket's own prior investigation deliberately deferred, at the user's
direct, specific go/no-go — not inferred from a peer's relay of general batch approval, since the
plan's own author had explicitly called out that this specific step needed a live decision on
timing and naming that no relay could substitute for. All 4 Acceptance Criteria met and verified
with real commands, not assumed. Found and fixed 4 hazards beyond the original investigation's own
scope (2 of which — the Headroom launcher and the `.gitignore`/`pyproject.toml` untracked-but-not-
ignored gap — the rename would have silently reintroduced or broken without this pass's own
re-sweep), corrected one wrong claim in the original investigation, and updated one genuinely stale
pinned test rather than force it to keep passing against outdated behavior. No known material gap
left unstated.
