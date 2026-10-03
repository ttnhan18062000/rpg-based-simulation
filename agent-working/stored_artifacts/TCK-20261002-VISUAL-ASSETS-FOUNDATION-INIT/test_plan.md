---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT
artifact_type: test_plan
tags: [mcp, architecture, testing, documentation]
---

# Test Plan — TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT

Commands (worktree root; the worktree has no `.venv`):
- full: `/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python -m pytest tests/visual_assets -q -p no:cacheprovider`
- as CI sees it: `ASEPRITE_MCP_BINARY=/nonexistent <same command>`
- registration: `<python> -m pytest tests/tools/test_mcp_json_registration.py tests/tools/test_mcp_launcher_hardening.py -q`

| ID | Check | Kind | Must fail when |
|---|---|---|---|
| R1 | every pre-move test exists post-move and passes (209 baseline; account for any delta by name) | regression | n/a |
| R2 | `lua/ops.lua` sha256 unchanged; 15 tool names unchanged | regression | a tool is renamed or the template edited |
| R3 | no-Aseprite run: 0 failed; passed/skipped counts reported | CI parity | an integration test lacks the skip marker |
| R4 | `workspace` fixture really isolates (no test touches `~/.cache/rpg-aseprite-mcp`) | isolation | config imported by value (`from config import WORKSPACE`) |
| B1 | boundary: `technique` importing `api` | architecture | planted import |
| B2 | boundary: `drawing` importing `src` (and `src` importing `visual_assets`) | architecture | planted import |
| B3 | boundary: `drawing` writing to the catalog path | architecture | planted reference |
| L1 | launcher probes `mcp` quietly, cds to repo root, final error preserved | launcher | probe removed / bare-exists shortcut |
| L2 | `.mcp.json` new entry exact shape; old entries byte-identical | registration | entry altered |
| S1 | `python -m visual_assets.drawing.server` answers `list_tools` over stdio | protocol | package import broken |

R4 method: run the suite with `HOME` pointed at an empty temp dir and assert that dir stays empty afterwards, or
assert on the real workspace's mtime; record which.

## Proof Plan

- level: unit + integration (tooling refactor; no RPG behaviour change, no Mechanics Bible rule applies)
- proof kind: regression by test-name parity against the pre-move suite, plus planted-violation checks for the boundary test, the launcher and workspace isolation
- oracle source: the pre-move suite at commit d7775760 (209 tests), `lua/ops.lua` sha256, the 15 MCP tool names, and the layering table in `docs/plans/visual-asset-foundation/README.md`
- expected effect: identical behaviour under the new package layout; a forbidden import or a frozen config value fails a test; tests never touch the real workspace
- selected commands: `/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python -m pytest tests/visual_assets -q -p no:cacheprovider` (also with `ASEPRITE_MCP_BINARY=/nonexistent`), and `-m pytest tests/tools/test_mcp_json_registration.py tests/tools/test_mcp_launcher_hardening.py -q`

R1-R3 and S1 are run and their output recorded in the ticket's Test Summary; B1-B3, L1 and R4 each have their
planted violation applied, seen to fail, and reverted, one line each.

Not covered: store logic (none exists), CI execution of Aseprite-backed tests (no Aseprite in CI).
