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
