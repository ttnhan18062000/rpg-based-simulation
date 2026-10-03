---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-ASEPRITE-MCP-SPIKE-HARDENING
artifact_type: test_plan
tags: [mcp, testing, security]
---

# Test Plan — TCK-20261002-ASEPRITE-MCP-SPIKE-HARDENING

Command: `.venv/bin/python -m pytest experiments/aseprite_mcp -q -p no:cacheprovider`. Do not run `tests/` wholesale.
Baseline before this ticket: 54 passed.

## New tests
| ID | File | Behaviour guarded | Mutation that must break it |
|---|---|---|---|
| N1 | test_negative | timeout -> `timed out`, no revision, `.jobs/` empty, no orphan aseprite | remove `timeout=` from `subprocess.run` |
| N2 | test_negative | corrupt file with matching sidecar hash -> `AdapterError`, no revision | skip the "no result" check in `_run_lua` |
| N3 | test_negative | `os.link` failure -> no partial revision / orphan sidecar, later edit works | write sidecar before link |
| N4 | test_negative | N-way same-base race -> exactly 1 success, others stale, chain gap-free | remove `_SpriteLock` |
| N5 | test_negative | first-creation race -> exactly one `r0001` | remove the exists-check in `new_sprite` |
| N6 | test_negative | `.jobs/` empty after success and every failure path | remove `rmtree` in `_Job.__exit__` |
| N7 | test_negative | oversize output rejected, nothing published | remove the size check in `_publish` |
| N8 | test_negative | `..`, `/abs`, NUL, unicode look-alike, symlinked sprite dir rejected or confined | loosen `_NAME_RE` |
| O1 | test_ops | `delete_layer` removes the layer and its cels; last layer refused | skip the guard |
| O2 | test_ops | `delete_frame` renumbers frames/durations; last frame refused; tag behaviour documented | skip the guard |
| O3 | test_ops | `resize_canvas` crop and pad keep pixel positions (top-left anchor), all layers/frames | wrong anchor |
| O4 | test_ops | the three ops reject bad input before Aseprite runs (extend the parametrized test) | n/a (validation) |
| S1 | test_server_stdio | exact tool set | add/remove a tool |
| S2 | test_server_stdio | bad call -> `isError` with adapter message; stale base -> error | swallow errors in `_call` |
| S3 | test_server_stdio | `preview` / `filmstrip` return `image/png` with expected dimensions | wrong scale arg order |

Each "Mutation" must be actually applied once by the implementer, the test seen to fail, and the change reverted;
record one line per test in the ticket's Test Summary. This is the guard against the earlier-observed risk of
tests that pass on the first run without being able to fail.

## Regression
All 54 existing tests unchanged and green. `LUA_SHA256` re-pinned after the Lua edit (the existing
`test_template_hash_is_enforced` covers the gate itself).

## Determinism / flake budget
Race tests use barriers, no `sleep`. Loop the race tests 20x in shell; any single failure blocks closure.

## Non-goals
No performance budgets (U-05), no CI lane, no cross-platform claims.

## Proof Plan
- Level: unit and integration against the real Aseprite binary and real MCP stdio transport (experiments/ only).
- Proof kind: mutation-checked tests; each guarded behaviour was broken once and the test seen to fail (results in the ticket's Test Summary).
- Oracle source: observable adapter outcomes (error text, revision files, sidecars, `.jobs/` contents, PNG sizes); Aseprite 1.3.18.6 behaviour probed on this machine.
- Expected effect: 196 tests pass, 0 skipped; race tests 20/20.
- Selected commands: `.venv/bin/python -m pytest experiments/aseprite_mcp -q -p no:cacheprovider`
