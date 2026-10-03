---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260817-HOTFIX-KGMCP-MISSING-JSONSCHEMA-DEPENDENCY
phase: done
date: 2026-08-17
tags: [ai, mcp, bug]
---

# TCK-20260817-HOTFIX-KGMCP-MISSING-JSONSCHEMA-DEPENDENCY

## Title
Add `jsonschema` and `mcp` (plus their real transitive dependencies) to `requirements.txt` — both
missing since first used by the Knowledge Gateway MCP gateway module. (Ticket ID kept as originally
filed; scope genuinely widened mid-Implement to cover `mcp` once `jsonschema`'s fix revealed it as
the next real blocker — see Implementation Notes.)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
The user asked to check why recent GitHub Actions CI runs were failing. Investigation via `gh run
view`/the GitHub API (after the user authenticated `gh` CLI) found the real root cause for 2 of the
9 failing jobs (`API / tools / logging`, `Migration lanes`) on the most recent run
(`https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/31975893078`, commit
`7dd19840`): a hard `ModuleNotFoundError: No module named 'jsonschema'` at test-collection time for
`tests/tools/test_knowledge_gateway_mcp.py` and `tests/tools/test_knowledge_gateway_failure_semantics.py`,
both of which import `jsonschema` because `tools/knowledge_gateway_mcp.py` (the real gateway module)
uses `jsonschema.RefResolver`/`jsonschema.validate` for response-schema validation. `jsonschema` was
never added to `requirements.txt`, only ever installed ad hoc in local dev environments — it works
locally in this session's own `.venv` (confirmed: `jsonschema==4.26.0` present) but CI's clean `pip
install -r requirements.txt` never installs it, so any job whose scope includes `tests/tools/` fails
at collection time before a single test even runs.

This is unrelated to any of this session's own recent ticket work (`TCK-20260816-KGMCP-BUDGET-
TOLERANCE-DEDUP-COVERAGE-CLOSURE`, `TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP`) — it
predates them, tracing back to whichever earlier Knowledge Gateway MCP phase first added
`jsonschema.RefResolver` usage to `tools/knowledge_gateway_mcp.py`.

## Scope
- Add `jsonschema==4.26.0` (the exact version already installed and working in this session's local
  `.venv`) to `requirements.txt`, plus its real, non-optional transitive dependencies:
  `attrs==26.1.0`, `jsonschema-specifications==2025.9.1`, `referencing==0.37.0`,
  `rpds-py==2026.6.3` — matching `requirements.txt`'s own existing convention of listing resolved
  transitive dependencies explicitly, not just top-level packages.
- Verify all 5 pinned versions actually resolve and download from PyPI, including confirming a
  Python 3.13 wheel exists for the compiled `rpds-py` package (CI's own Python version, different
  from this local dev environment's 3.12).
- **Scope widened mid-Implement (disclosed)**: a real, isolated clean-venv install + test run
  (mirroring CI exactly, not just spot-checking imports) revealed `jsonschema`'s fix was necessary
  but not sufficient — `tools/knowledge_gateway_mcp.py:486`'s `from mcp.server.fastmcp import
  FastMCP` (the real MCP Python SDK, unrelated to this repo's own `.mcp.json` config) was *also*
  missing from `requirements.txt`, masked entirely by `jsonschema`'s earlier collection-time
  failure in the same test files. Added `mcp==1.28.1` plus its own real, non-optional transitive
  dependencies not already present: `httpx-sse==0.4.3`, `pydantic-settings==2.14.2`,
  `python-dotenv==1.2.2` (pydantic-settings's own dependency), `pyjwt==2.13.0`,
  `cryptography==49.0.0` (pyjwt's `[crypto]` extra, needed since `mcp` uses `pyjwt[crypto]`),
  `python-multipart==0.0.32`.

## Out of Scope
- The other 7 failing CI jobs on the same run, which have distinct, unrelated root causes (a
  missing world-data fixture file, a real assertion failure in movement/spatial regression tests, a
  malformed simulation-quality anchor file, a docs-hygiene violation in `design_patterns.md`, a mock
  comparison bug in observability tests, a scoring-constant drift in integration tests, and a
  perf-combat threshold failure) — each is a separate, real, pre-existing issue requiring its own
  investigation, not a dependency-declaration gap.
- Any change to `tools/knowledge_gateway_mcp.py`'s own use of `jsonschema`/`mcp` (already correct,
  tested, and working locally — this ticket only fixes the CI-environment dependency gap).
- `test_gateway_down_search_mcp_test_mode_still_works` — a real, further, genuinely different
  failure surfaced once `jsonschema`/`mcp` stopped masking it: it requires a built
  `knowledge-index/`, which CI's lean environment deliberately never builds (per
  `requirements.txt`'s own header comment). Not a dependency-declaration gap — filed as its own
  follow-up ticket, `TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX`.

## Acceptance Criteria
- [x] `jsonschema`/`mcp` and their real transitive dependencies are added to `requirements.txt`
      with exact versions already proven working in this session's local environment.
- [x] All 12 newly-pinned versions confirmed to resolve from PyPI (verified via
      `pip download --no-deps`), including a Python 3.13 wheel for the compiled `rpds-py` package.
- [x] `tests/tools/test_knowledge_gateway_mcp.py` and
      `tests/tools/test_knowledge_gateway_failure_semantics.py` collect successfully (2301 tests
      collected across the whole `tests/tools` lane with 0 collection errors, confirmed in a real,
      isolated, fresh clean venv) and all but 1 test in these 2 files pass — the 1 remaining
      failure is a real, different, disclosed gap (see Out of Scope), not a dependency issue.

## Related Tickets
- `TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX` (follow-up filed for the 1 real,
  different failure this ticket's own fix uncovered)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier, no staging artifacts).

## Related Code Areas
- `requirements.txt`
- `tools/knowledge_gateway_mcp.py` (the real `jsonschema` consumer, read-only reference)
- `tests/tools/test_knowledge_gateway_mcp.py`, `tests/tools/test_knowledge_gateway_failure_semantics.py`

## Implementation Notes
Investigation used the `gh` CLI (freshly authenticated by the user mid-session, after `gh auth
login`'s browser step failed in this headless environment and was completed manually via the
device-code flow) to pull real job logs for the most recent CI run
(`31975893078`, commit `7dd19840`) via `gh api .../actions/jobs/<id>/logs` (note: `gh run view
--log-failed` itself failed with a TLS cert error against
`results-receiver.actions.githubusercontent.com` — worked around by hitting the underlying
`api.github.com/.../logs` redirect target, `productionresultssa19.blob.core.windows.net`, directly
via `curl` once the network's earlier Fortinet DNS-filter block on that domain cleared).

Real root cause for 2 of the 9 failing jobs (`API / tools / logging`, `Migration lanes`):
`ModuleNotFoundError: No module named 'jsonschema'` at collection time for
`tests/tools/test_knowledge_gateway_mcp.py:28` and
`tests/tools/test_knowledge_gateway_failure_semantics.py:50`. `jsonschema` is a real, load-bearing
dependency of `tools/knowledge_gateway_mcp.py`'s own `_RESPONSE_SCHEMA_RESOLVER` (used via
`jsonschema.RefResolver`), never added to `requirements.txt` — it only ever worked because it
happened to be pre-installed in every local dev `.venv` this whole Knowledge Gateway MCP effort has
used.

Added `jsonschema==4.26.0` + `attrs==26.1.0` + `jsonschema-specifications==2025.9.1` +
`referencing==0.37.0` + `rpds-py==2026.6.3` to `requirements.txt` (exact versions matching what was
already installed and proven working locally). Verified all 5 resolve from PyPI via
`pip download --no-deps`, including confirming a `cp313` (Python 3.13, CI's own version) wheel
exists for the compiled `rpds-py` package.

A real, isolated verification (fresh `python3 -m venv`, clean `pip install -r requirements.txt`,
matching CI's own install step exactly) then surfaced that `jsonschema` alone was necessary but not
sufficient: `tools/knowledge_gateway_mcp.py:486`'s `from mcp.server.fastmcp import FastMCP` (the
real MCP Python SDK — distinct from this repo's own `.mcp.json` server config) was *also* never in
`requirements.txt`, entirely masked until now by `jsonschema`'s earlier collection-time failure in
the same 2 test files. Added `mcp==1.28.1` plus its own real (non-`extra==`) transitive
dependencies not already present: `httpx-sse==0.4.3`, `pydantic-settings==2.14.2` (itself needing
`python-dotenv==1.2.2`), `pyjwt==2.13.0` (needing the `[crypto]` extra's `cryptography==49.0.0`,
since `mcp` requires `pyjwt[crypto]`), `python-multipart==0.0.32`. All 12 newly-added package
versions verified to resolve from PyPI.

Re-verified in a fresh clean venv: `pytest tests/tools --collect-only` now collects all 2301 tests
with 0 collection errors (down from 2 collection errors before this fix). Running the 2 previously-
blocked files fully: 53/54 pass. The 1 remaining failure
(`test_gateway_down_search_mcp_test_mode_still_works`) is a real, different, disclosed gap — it
needs a built `knowledge-index/`, which CI's own lean environment deliberately never builds (per
`requirements.txt`'s own header comment excluding the heavy ML stack) — filed as its own follow-up
ticket rather than fixed here, since it requires a real architectural decision (build a CI fixture
index, skip the test, or move it out of the CI-covered path), not a dependency-declaration fix.

## Test Summary
- Fresh, isolated clean-venv verification (`python3 -m venv /tmp/ci_clean_venv`,
  `pip install -r requirements.txt`, mirroring CI's own install step exactly — not this local dev
  environment, which already had all these packages pre-installed):
  - `pytest tests/tools --collect-only -q`: **2301 tests collected, 0 collection errors** (down
    from 2 collection errors — `test_knowledge_gateway_mcp.py`,
    `test_knowledge_gateway_failure_semantics.py` — before this fix).
  - `pytest tests/tools/test_knowledge_gateway_mcp.py tests/tools/test_knowledge_gateway_failure_semantics.py -q`:
    **53 passed, 1 failed** (the 1 failure is the disclosed, out-of-scope `knowledge-index`-
    dependent test, filed separately — not a regression from this fix).
- All 12 newly-pinned package versions independently verified to resolve from PyPI via
  `pip download --no-deps` (not just installed from the pre-warmed local pip cache).
- `rpds-py==2026.6.3`'s `cp313` (Python 3.13, CI's exact interpreter version) wheel existence
  independently confirmed via the PyPI JSON API, since this local dev environment only has Python
  3.12 available and could not build/test against 3.13 directly.

## Files Changed
- `requirements.txt` — added 12 packages: `jsonschema`, `attrs`, `jsonschema-specifications`,
  `referencing`, `rpds-py` (for the `jsonschema` fix), `mcp`, `httpx-sse`, `pydantic-settings`,
  `python-dotenv`, `pyjwt`, `cryptography`, `python-multipart` (for the `mcp` fix).
- `tickets/todos/TCK-20260817-KGMCP-SEARCH-MCP-TEST-REQUIRES-UNBUILT-CI-INDEX.md` — new follow-up
  ticket for the 1 real, disclosed, different gap this fix's own verification uncovered.

## Completion Summary
Fixed the real root cause of 2 of the 9 failing CI jobs on the most recent run: two genuinely
missing pip dependencies (`jsonschema`, then `mcp` once `jsonschema`'s fix revealed it as the next
real blocker), both load-bearing imports in `tools/knowledge_gateway_mcp.py` that were never
declared in `requirements.txt` and only ever worked locally by accident (pre-installed in every dev
`.venv`). Verified via a real, isolated, fresh clean-venv install mirroring CI exactly — not just a
local spot-check — that both previously-blocked test files now collect and run correctly (53/54
pass; the 1 remaining failure is a real, different, disclosed gap filed as its own follow-up
ticket, not silently absorbed into this one or left unstated).

The other 7 failing CI jobs on the same run have distinct, unrelated, genuinely pre-existing root
causes (missing world-data fixtures, real assertion failures in movement/simulation-quality/
integration/perf tests, a docs-hygiene violation) — out of this hotfix's own scope, reported to the
user for a separate decision on how to proceed rather than silently expanded into.
