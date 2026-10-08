---
status: active
layer: guidelines
authority: P1
audience: developer
---

# Repo Tooling Layout

## The rule

`tools/` is the home for repo tooling, with one exception: a **domain root** may own its own tooling.
`agent-working/` (data), `visual_assets/` and `codebase/` (their own Python packages) are domain roots; the codebase
domain's tooling moved to `codebase/` in `TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE`. Every other tool still goes in a
`tools/` subpackage. There is no `scripts/` directory, and none should be recreated.

A domain root is a deliberate owner decision, not a place to put a tool that does not fit a `tools/` subpackage. The direction is
one-way: a domain root may import `tools`, `tools` must not import a domain root (`tests/codebase/test_domain_root_layout.py`
checks it for `codebase/`).

A new tool goes into a domain subpackage under `tools/` — a real Python package with its own
`__init__.py`, imported via package imports (`from tools.perf.foo import bar`), never a bare
top-level script relying on a `sys.path.insert` hack. This follows the existing
`tools/gate_checks/` and `tools/mechanism_registry/` precedent
(`TCK-20260916-MECHANISM-REGISTRY-TOOLS-PACKAGE`).

Domain subpackages under `tools/` today: `agent_codex_*`, `agent_orchestration_*`,
`agent_replay_*` (Codex integration, out of scope for reorganization —
`TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC`), `delivery/`, `gate_checks/`, `maintenance/`,
`mechanism_registry/`, `perf/`, `release/`, `semantic_control_plane/`.

The ~70 existing flat top-level `tools/*.py` files are not required to move into a subpackage
retroactively — they stay where they are and move later, one domain at a time, as a separate
decision (out of scope for `TCK-20260929-RETIRE-SCRIPTS-DIR`, which only retired `scripts/`
itself).

## Why `scripts/` was retired instead of kept as a second tooling home

Investigated 2026-08-19/20 and again 2026-09-29 (`docs/plans/scripts_tools_governance_epic.md`):
`scripts/` and `tools/` coexisted with no documented rule distinguishing them, and no mechanism
caught files that stopped being used. `tools/` was demonstrably the pattern that stayed
maintained (only 2 of 52 top-level files had zero live cross-references, both from 2026-03-17,
the earliest stretch of this repo's history); `scripts/` was not (6 of 28 files, plus a further
file found live during the retirement itself, had zero live references anywhere — some never
referenced by even a single historical ticket). The user's decision
(`TCK-20260820-SCRIPTS-TOOLS-GOVERNANCE-EPIC`, 2026-09-29) was to retire `scripts/` entirely
rather than codify the split, since a second, less-maintained tooling home only recreates the
same orphan-accumulation problem the split already caused.

## Catching new orphans

`tools/gate_checks/tools_orphan_check.py` (`TCK-20260929-TOOLS-ORPHAN-FILE-CHECK`) reports every
`tools/` file (and every `.py`/`.sh` file under `codebase/`) with no live cross-reference, on demand via a Makefile target — report-only, not a
CI gate, since checks over agent tooling should stay proportionate to the risk. Run it
periodically, not automatically, to catch drift before it accumulates the way `scripts/` did.

## Repo root

The tracked top level of the repository is an allowlist, not a convention. A new root entry (file or directory) needs an
owner decision, the same as a new domain root; a tool, config or data file that is not on the list goes into a
`tools/` subpackage, a domain root, `docker/`, `config/` or `docs/` instead. The list below is the root after the repo-root
cleanup (`TCK-20261008-OPS-FILES-INTO-DOCKER-DIR`, `TCK-20261008-DROP-MAKE-BAT`,
`TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL`); `tests/codebase/test_repo_root_allowlist.py` reads it from this section and
compares it with `git ls-files`, so changing the root means changing this list in the same PR, with the owner's decision.
Only first path components count: adding a file under `src/`, `tools/` or a domain root never touches the list.

<!-- repo-root-allowlist:begin -->
Directories: `.agents`, `.claude`, `.codex`, `.github`, `agent-working`, `codebase`, `config`, `content`,
`dashboard-frontend`, `data`, `docker`, `docs`, `experiments`, `frontend`, `registries`, `src`, `tests`, `tools`,
`visual_assets`, `website`.

Files: `.dockerignore`, `.gitattributes`, `.gitignore`, `.gitmessage`, `.graphifyignore`, `.mcp.json`,
`.pre-commit-config.yaml`, `.python-version`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `LICENSE`, `Makefile`,
`README.md`, `compose.yaml`, `perf_baselines.json`, `pyproject.toml`, `requirements-knowledge.txt`, `skills-lock.json`,
`uv.lock`.
<!-- repo-root-allowlist:end -->

Two entries are listed on purpose and may move later by their owners' decision, not this guard's: `perf_baselines.json`
(perf domain; perf-planner asked to keep it at the root for now and will say before moving it) and `skills-lock.json`
(the external `npx skills` CLI's file). Local untracked clutter (`tmp/`, `scratch/`, `reports/`, logs) is not tracked, so
it is not checked.
