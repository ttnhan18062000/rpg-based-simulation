---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG
phase: done
date: 2026-08-19
tags: [architecture]
---

# TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG

## Title
Fix spec-invalid CORSMiddleware allow_origins=["*"] + allow_credentials=True combination

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
Item 1 of `TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC`, extracted into its own standalone ticket:
that epic's broader scope (auth, admission control) stays explicitly deferred per the user's
confirmed decision (2026-08-19) that this API surface stays on a trusted network — but the CORS
fix was always scoped as "regardless of the broader auth decision... a pure config correctness
fix," independent of the deployment question. Live-confirmed still present:
`src/api/server.py:73-78` configures `CORSMiddleware` with `allow_origins=["*"]` and
`allow_credentials=True` simultaneously — a combination the CORS spec disallows (a credentialed
request cannot use a wildcard origin). Browsers already reject the actual credentialed-wildcard
case today, so this is a config-hygiene/correctness fix (the middleware config is misleading about
what it actually permits), not a live exploit — consistent with staying low-priority while the
API remains on a trusted network.

## Scope
- Fix the CORS configuration in `src/api/server.py` to be spec-valid: either drop
  `allow_credentials=True` (if credentialed cross-origin requests aren't actually needed), or
  replace `allow_origins=["*"]` with an explicit, real origin allowlist.
- Confirm which of the two is actually correct by checking whether any real caller depends on
  credentialed cross-origin requests today (check `dashboard-frontend/` and any other real client)
  before picking a fix direction — don't guess.

## Out of Scope
- Authentication, rate limiting, or admission control — remains `TCK-20260817-HTTP-ADMISSION-
  CONTROL-EPIC`'s bundled scope, explicitly deferred pending a future deployment-plan change (this
  API surface is confirmed staying on a trusted network as of 2026-08-19).

## Acceptance Criteria
- [x] `CORSMiddleware`'s configuration no longer combines a wildcard origin with credentials.
- [x] Any real, currently-working caller (dashboard frontend or otherwise) is confirmed unaffected
      by the fix — verified, not assumed.

## Related Tickets
- TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC (item 1 extracted from here; that epic's remaining
  scope — auth, admission control — stays explicitly deferred, not touched by this ticket)
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic of the wider audit line)

## Related Docs
- docs/plans/http_admission_control_epic.md
- docs/audits/D23_architecture_resilience.md

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- src/api/server.py

## Assumptions / Open Questions
- Whether to drop credentials or scope origins to an allowlist depends on whether any real caller
  needs credentialed cross-origin requests — left to the implementer to verify first.

## Implementation Notes
Verified no real caller depends on credentialed cross-origin requests before picking a fix
direction: grepped `dashboard-frontend/src` and `frontend/src` for `credentials.*include` /
`withCredentials` / `Authorization`/`Bearer` — zero real hits (one `phasePalette.ts` false
positive, substring match on "author"). Confirmed `frontend/` (not `dashboard-frontend/`, which
targets an entirely different backend on a different port per its own `vite.config.ts`) is the
real client of `src/api/server.py`'s `create_v2_app()` — its `fetch()` calls pass no `credentials`
option, and its dev proxy (`frontend/vite.config.ts`) makes all `/api` traffic same-origin from
the browser's perspective regardless. No cookie-setting anywhere in `src/api/`. This confirmed
dropping `allow_credentials=True` (not building an origin allowlist) is the correct fix — nothing
depends on it.

Applied the fix to `src/api/server.py`'s `CORSMiddleware` registration, with a comment citing this
ticket and the evidence. Added `tests/api/test_cors_config.py` (new file, in-process `TestClient`
pattern matching `tests/api/test_health_liveness.py`) asserting the real response headers a
credentialed cross-origin request receives never combine a wildcard origin with
`access-control-allow-credentials`, for both a plain GET and a CORS preflight OPTIONS request —
no prior test coverage existed for this middleware config at all.

Updated `docs/plans/http_admission_control_epic.md`'s acceptance-signal line to mark this item
resolved, citing the evidence above. Left `docs/audits/D23_architecture_resilience.md` (the R6
finding) untouched — confirmed via its own R1 (RabbitMQ/Kafka) row, already fully resolved by
`TCK-20260817-DEAD-INFRA-REMOVAL-EPIC` earlier this session but never retroactively annotated,
that this doc is treated as a frozen point-in-time audit snapshot; the living epic doc is the
correct place to track resolution, not this one.

## Test Summary
`.venv/bin/python3 -m pytest tests/api/test_cors_config.py -v` — 2 passed (new tests).
`.venv/bin/python3 -m pytest tests/api/test_health_liveness.py tests/api/test_scenario_runtime_api.py -v`
— 12 passed (regression check on the same app factory, unaffected by the fix).

## Files Changed
- src/api/server.py — removed `allow_credentials=True` from `CORSMiddleware` registration
- tests/api/test_cors_config.py — new file, 2 tests
- docs/plans/http_admission_control_epic.md — marked the CORS acceptance-signal item resolved
- docs/parity_ledger/infrastructure.yaml — added `INFRA-364`; the diff also carries incidental
  line-wrap/escape reformatting of 3 unrelated pre-existing entries, a known side effect of
  `parity_ledger_writer.py`'s whole-shard YAML round-trip on write — confirmed no semantic content
  changed in any of the 3 (byte-diffed against `git diff`, only wrap width / `—`→`—` escaping
  differs), not a content edit or another ticket's contamination

## Completion Summary
Fixed the spec-invalid `allow_origins=["*"]` + `allow_credentials=True` CORSMiddleware combination
in `src/api/server.py` by dropping `allow_credentials=True`. Verified first (not assumed) that no
real caller — `frontend/`, the actual client of this API — depends on credentialed cross-origin
requests, so this is a pure config-hygiene fix with no behavior impact on any real request path.
Added test coverage that previously didn't exist for this middleware config, and updated the
tracking epic doc's acceptance signal. `TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC`'s remaining
scope (auth, admission control) stays explicitly deferred, untouched by this ticket.
