---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261015-VISUAL-ASSETS-SANDBOX-BWRAP-USERNS-ERROR
phase: done
date: 2026-10-15
tags: [architecture, testing]
---

# TCK-20261015-VISUAL-ASSETS-SANDBOX-BWRAP-USERNS-ERROR

## Title
Drawing sandbox: one clear error naming the host fix when bwrap cannot set up its network namespace, and an honest skip in tests (#555)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
GitHub #555. On u24desktop (Ubuntu 24.04+, `kernel.apparmor_restrict_unprivileged_userns = 1`, and no AppArmor profile for `/usr/bin/bwrap`), `bwrap --unshare-all` fails with `bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`. Every Aseprite job in `visual_assets/drawing/backend/sandbox.py::bwrap` then fails (drawing tools/MCP, `store build`), and 191 `needs_aseprite` tests fail opaquely instead of being skipped. CI is unaffected (no Aseprite there). This host works because the `apparmor` package ships `/etc/apparmor.d/bwrap-userns-restrict`. The host fix is the owner's (sudo); this ticket only makes the repo say so clearly.

## Scope
- `visual_assets/drawing/backend/sandbox.py`: when the bwrap run fails and stderr contains the userns signature (`Failed RTM_NEWADDR: Operation not permitted`, matched on that stable substring), raise the existing `AdapterError` with one message. The message names the cause (AppArmor unprivileged-userns restriction), the narrow host fix (install or upgrade the `apparmor` package that ships `/etc/apparmor.d/bwrap-userns-restrict`, or add a bwrap profile with `userns`) and #555. All other failures stay as they are.
- A cheap, cached probe that tells "bwrap works here" apart from "bwrap is installed": `bwrap --unshare-all --ro-bind / / true` (or the minimal equivalent), run at most once per process. Put it in one place that both the backend and the test conftest can use. Do not import tests from `visual_assets/`.
- `tests/visual_assets/conftest.py`: `aseprite_available()` also requires the probe to pass. When the binary and bwrap exist but the probe hits the userns signature, the skip reason names it (for example, `requires aseprite and a working bwrap: AppArmor userns restriction, see #555`). **Strict mode (`strict_aseprite.strict_requested()`) must still FAIL, not skip.** The skip must never hide a broken sandbox where strict proof is asked for. Keep `tools/ci_aseprite_skip_line.py`'s `SKIP_MARKER` matching (it greps the reason prefix `requires aseprite and bwrap`). Either keep that prefix or update the tool and its test together.
- Tests: unit tests with the subprocess faked (the signature produces the clear `AdapterError`; another failure does not; the probe result is cached; a probe failure gives a skip, and gives a failure in strict mode). No real-bwrap test is needed beyond what already runs on this host.

## Out of Scope
- No host change (no sudo, no AppArmor edits). Applying the fix is the owner's job on u24desktop.
- No change to the sandbox's isolation flags (no dropping `--unshare-net` or `--unshare-all`). Isolation stays as ADR D10 requires.
- No CI workflow change.

## Acceptance Criteria
- [ ] With the subprocess faked to the userns stderr, `bwrap()` raises `AdapterError` whose message contains `AppArmor`, `bwrap-userns-restrict` and `#555`.
- [ ] The conftest skips `needs_aseprite` tests with the named reason when the probe fails, and fails them in strict mode. Both are covered by tests.
- [ ] `tools/ci_aseprite_skip_line.py` and its test still pass.
- [ ] Scoped runs, one at a time under `systemd-run --user --scope -q -p MemoryMax=3G`: the new unit tests, `tests/visual_assets/drawing/` unit tests, and the `ci_aseprite_skip_line` tests. Then one real Aseprite-backed file on this host (for example `tests/visual_assets/drawing/integration/test_ops.py`) to show the probe passes here and nothing is skipped. No full `tests/visual_assets` run without asking asset-planner first (the lead's heavy-run gate is closed).
- [ ] #555 gets a closing comment (asset-planner posts it after the merge).

## Related Tickets
- Same batch: `TCK-20261015-VISUAL-ASSETS-ICON-SCENE-RC11-KEYS` (#598)

## Related Docs
- `docs/architecture/visual_asset_foundation_adr.md` (D10 sandbox), `docs/plans/aseprite-mcp-pixel-art/`

## Related Stored Artifacts

## Related Code Areas
- `visual_assets/drawing/backend/sandbox.py` (`bwrap`, `AdapterError`), `visual_assets/drawing/config.py`, `tests/visual_assets/conftest.py`, `tests/visual_assets/strict_aseprite.py` (or wherever `strict_requested` lives), `tools/ci_aseprite_skip_line.py`

## Assumptions / Open Questions
- Assumed: bubblewrap's stderr text `Failed RTM_NEWADDR: Operation not permitted` is stable across 0.9.x. The match is on that substring only.

## Implementation Notes
- `sandbox.py`: `USERNS_SIGNATURE`/`USERNS_MESSAGE`; `bwrap()` raises `AdapterError(USERNS_MESSAGE)` when the exit is non-zero and stderr holds the signature (a successful run is never turned into an error; the timeout path is untouched). `bwrap_problem()` is the `functools.cache`d probe (`bwrap --unshare-all --ro-bind / / true`), returning None or one reason string (userns message, "not installed", or the exit and first stderr text).
- `tests/visual_assets/conftest.py`: `aseprite_available()` also needs `bwrap_problem() is None`; `skip_reason()` keeps the `requires aseprite and bwrap` prefix (so `SKIP_MARKER` and `ci_aseprite_skip_line` are unchanged) and appends the host cause. Strict mode never skips: `_strict_problem` passes `bwrap_problem` to `strict_aseprite.strict_problem` (new optional keyword), which fails with `strict mode: bwrap cannot run here: ...`.
- The host fix itself stays the owner's (no sudo here).

## Test Summary
All scoped, one at a time, under `systemd-run --user --scope -q -p MemoryMax=3G`:
- new `tests/visual_assets/drawing/unit/test_sandbox_userns_error.py` (fake subprocess: error message, other failure unchanged, success with the signature is no error, probe cached, probe causes) + `test_strict_aseprite.py` and `test_ci_aseprite_skip_line.py`: 31 passed.
- `tests/visual_assets/drawing/unit`: 137 passed.
- real Aseprite on this host, `tests/visual_assets/drawing/integration/test_ops.py`: 62 passed, none skipped (the probe passes here).

## Files Changed
- `visual_assets/drawing/backend/sandbox.py`, `tests/visual_assets/conftest.py`, `tests/visual_assets/strict_aseprite.py`, `tests/visual_assets/test_strict_aseprite.py`, `tests/visual_assets/drawing/unit/test_sandbox_userns_error.py`

## Completion Summary
bwrap() raises one AdapterError naming AppArmor, bwrap-userns-restrict and #555 on the RTM_NEWADDR signature; a cached probe lets the conftest skip with a named reason (SKIP_MARKER prefix kept) and strict mode still fails. 31 new/related, 137 drawing-unit and 62 real-Aseprite tests pass, scoped. Approved by asset-planner. Host fix remains the owner's.
