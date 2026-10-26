---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261024-API-SERVER-OBSERVABILITY-UI-STATIC-PAGE
phase: done
date: 2026-10-24
tags: [architecture, api-design, observability]
---

# TCK-20261024-API-SERVER-OBSERVABILITY-UI-STATIC-PAGE

## Title
The 2,093-line observability UI page leaves create_v2_app: served byte-identical from a static file by a router under src/api/routes/

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
M7 batch 1, ticket 2 of 3. User approval 2026-10-24, logged at https://github.com/ttnhan18062000/rpg-based-simulation/issues/715#issuecomment-6384147652. rpg-planner cleared the file on #697.

`get_observability_ui` (`src/api/server.py:335`) is 2,093 lines of HTML, CSS and JS in a Python string literal. That is 86% of the module and of `create_v2_app`. This ticket moves the page out and serves it unchanged.

## Scope
1. **The page becomes a static file**, for example `src/api/static_pages/observability_ui.html`; plan.md settles the name. Do not put it next to `src/api/routes/static.py`: that module is the `/api/v1/static` world-objects route, not static files.
2. **Write the file from the evaluated string, never by copying its source text.**
   - The literal is a non-raw `"""..."""`, so Python interprets today any `\n`, `\\`, `\'` or `\u` escape in the JS.
   - Write the file from the runtime value: for example, a one-off script that builds the app, requests the page, and writes the bytes.
   - Then confirm the sha256 pinned by ticket 1 matches.
3. **A router module serves it**, for example `src/api/routes/observability_ui.py`, holding the three routes:
   - `/api/v1/observability/ui`, `/observability/ui` and `/api/v1/observability/live/ui`;
   - each with the same endpoint function name, `response_class`, status code, redirect target and dependency list (`require_api_key_header_or_query`, `require_admission_header_or_query`) as today;
   - included in `create_v2_app` **at the same point in the registration order** as today. They are currently the last routes registered.
4. **Read the file once**: at module level or through `functools.cache`, located with `importlib.resources` or a path relative to the module. No disk read per request, and no dependence on the working directory.
5. **Packaging.**
   - `[tool.setuptools.packages.find]` declares no package-data, so a wheel would not carry the `.html`.
   - Find out whether anything builds or installs a wheel: Dockerfile, compose, CI or Makefile.
   - If something does, the fix is a `package-data` entry in `pyproject.toml`. That is **lead-planner's file**: send codebase-planner the exact before/after and do not edit it yourself.
   - If nothing does, record that in investigation.md.
6. **Ratchet.** These rows in `codebase/baselines/code_health_exceptions.jsonl` drop to the new measured values or are removed:
   - `module-length`;
   - `function-length`, both for `create_v2_app` and for `create_v2_app.<locals>.get_observability_ui`;
   - `cognitive-complexity`.

   Use the baseline's own sync tooling and never raise anything by hand. The new router module must not add a row.

## Out of Scope
- Any change to the page's content, the routes' auth or their paths. The page ships byte-identical. Restyling it or splitting its JS is a separate decision owned by rpg or frontend.
- The other inline routes (ticket 3).

## Acceptance Criteria
- Ticket 1's characterization tests pass and its fixture is untouched (`git diff` on the fixture is empty): the same OpenAPI, route order, UI sha256 and redirects.
- `src/api/server.py` is about 340 lines and no longer contains `get_observability_ui`.
- The code-health gate reports 0 new and 0 worse, and the baseline rows above shrink or disappear.
- `tests/api`, `tests/architecture/test_api_read_model_guard.py` and `tests/codebase` pass.

## Related Tickets
- Previous: `TCK-20261024-API-SERVER-CHARACTERIZATION-TESTS`. Next: `TCK-20261024-API-SERVER-INLINE-ROUTES-TO-ROUTERS`.

## Related Docs
- `docs/plans/codebase_health/python_code_craft_roadmap.md` (M7 row, decision 7 amendment, section 9)
- `docs/guidelines/python_code_standard.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260823-HTTP-API-KEY-AUTH/plan.md` (Decision 3: browser-facing pages accept the key as a query parameter)

## Related Code Areas
- `src/api/server.py:335-2437`, `src/api/routes/`
- `codebase/baselines/code_health_exceptions.jsonl`
- `pyproject.toml` (read only)

## Assumptions / Open Questions
- Assumed: a `.html` file under `src/` trips no gate, because ruff, ast-grep and paths-guard read only `.py` files. Verify with `make code-health` and the paths-guard check before push.

## Implementation Notes
The 2,093-line page now lives in src/api/static_pages/observability_ui.html, written from the served bytes (sha256 081c122a...5f91b, identical). src/api/routes/observability_ui.py serves it and its two redirects, read once with functools.cache, registered last as before. No packaging change needed (see investigation.md).

## Test Summary
Snapshot test passes with the fixture unchanged; code-health 0 new/0 worse after tighten; 691 passed across tests/api, the guard and tests/codebase.

## Files Changed
src/api/server.py, src/api/routes/observability_ui.py, src/api/static_pages/observability_ui.html, codebase/baselines/code_health_exceptions.jsonl

## Completion Summary
server.py went from 2437 to 338 lines; module-length and the get_observability_ui function-length rows are gone.
