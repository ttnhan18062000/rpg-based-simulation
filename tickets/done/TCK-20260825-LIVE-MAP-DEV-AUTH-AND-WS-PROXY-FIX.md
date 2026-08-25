---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX
phase: open
date: 2026-08-25
tags: [websocket, setup]
---

# TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX

## Title
`make dev`'s documented live-map golden path is currently non-functional: two independent breaks
in API-key auth and Vite WS proxying

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Live-tested `make dev`'s exact golden path (backend on :8000, frontend on :5173, "Open
http://localhost:5173 to view the live map" -- the text this session's own
`TCK-20260825-HOTFIX-MAKEFILE-DEV-LIVE-MAP-DOC` added) and found it currently shows a non-functional
map. Two independent, real, live-reproduced bugs:

1. **API-key auth**: `TCK-20260823-HTTP-API-KEY-AUTH` added fail-closed API-key auth to every route
   the live map needs (`/api/v1/map`, `/api/v1/static`, `/api/v1/stats`, `/api/v1/ws`) after the
   live-map-reconnection epic (M1) had already finished. `frontend/src/hooks/useSimulation.ts` has
   zero code anywhere that sends an API key (no `X-API-Key` header on any `fetchJSON` call, no
   `?key=` query param on the WS connect). With `make dev`'s exact plain invocation (no
   `--api-key-hashes` flag), `RuntimeProfile.api_key_hashes` defaults to `""`, which is
   fail-closed-for-everyone by design (`docs/architecture/http_api_key_authentication.md`). Live
   reproduction: `curl http://127.0.0.1:8000/api/v1/stats` -> `401 {"detail":"Invalid or missing API
   key."}`; a raw WS client sending the exact same handshake `useSimulation.ts` sends, with no key,
   against `/api/v1/ws` -> rejected with HTTP 403 before the handshake is even read.
2. **Vite dev-proxy WS forwarding**: `frontend/vite.config.ts`'s `/api` proxy entry has no `ws: true`
   flag. Vite (via `http-proxy`) does not forward WebSocket upgrade requests through a proxy entry
   unless `ws: true` is set. Live reproduction: with the backend running unauthenticated (isolating
   this from bug 1), REST calls through the real Vite dev server (`curl
   http://127.0.0.1:5173/api/v1/stats`) proxy through correctly (401, as expected from bug 1 --
   confirms REST proxying itself works), but a WS client connecting to
   `ws://127.0.0.1:5173/api/v1/ws` (the exact URL `wsBase()` in `useSimulation.ts` constructs)
   times out during the opening handshake -- the upgrade request never reaches the backend at all.
   This means the live map's WebSocket stream has never worked through the real `npm run dev`/Vite
   dev-server setup at any point in this epic's history, independent of the auth question.

Both bugs must be fixed together for `make dev` to actually produce a working live map -- fixing
only one leaves the other blocking. Confirmed by the user: fix now, keep the fail-closed auth
default intact for anyone who doesn't configure it (do not weaken production auth posture to
patch local dev).

## Scope
- `frontend/vite.config.ts`: add `ws: true` to the existing `/api` proxy entry.
- `Makefile`'s `dev` target: pass a fixed, dev-only `--api-key-hashes "dev:<sha256 of a fixed dev
  raw key>"` to the backend `serve` invocation.
- Give the frontend a way to know and send that same raw dev key:
  - A new frontend dev-only env convention (`frontend/.env.development`, Vite's standard
    `import.meta.env.VITE_*` mechanism) holding the matching raw key.
  - `frontend/src/hooks/useSimulation.ts`: `fetchJSON` sends `X-API-Key` header when the env var is
    set; `connectWS`'s WS URL appends `?key=` when the env var is set. Must be a no-op (no header,
    no query param) when the env var is unset, so this does not alter behavior for any deployment
    that doesn't set it (e.g. a future production build with its own key-provisioning story).
- Verify end-to-end, live, through the real `make dev` invocation (not a bypassed/direct-to-backend
  test): backend + frontend both start, REST calls succeed, the WS stream connects and delivers live
  tick deltas, through `http://localhost:5173` exactly as documented.
- Add/update tests: a static guard that `vite.config.ts`'s `/api` proxy entry has `ws: true` (regression
  guard for bug 2, analogous to the project's other pinned-CI/config-snapshot guards); a test
  confirming `fetchJSON`/`connectWS` correctly attach the key when the env var is set and correctly
  omit it when unset.

## Out of Scope
- Any change to the backend auth mechanism itself (`src/api/auth.py`, fail-closed default) -- that
  design is intentional and correct, per `docs/architecture/http_api_key_authentication.md`; this
  ticket only wires the already-existing mechanism through for local dev.
- A real production key-provisioning/secrets story -- the `VITE_API_KEY`-style env convention this
  ticket adds is explicitly dev-only (`.env.development`, gitignored value or a fixed placeholder
  documented as dev-only), not a production deployment mechanism.
- `require_admission`/rate-limiting behavior -- unrelated to this ticket's two bugs.
- Any change to `src/api/ws/stream.py`'s protocol/payload shape -- already confirmed correct and
  working (this session's earlier `TCK-20260825-LIVE-MAP-TPS-BUDGET-RECHECK` and a direct
  backend-only WS client both received real, correctly-shaped tick deltas).

## Acceptance Criteria
- [x] `frontend/vite.config.ts`'s `/api` proxy entry has `ws: true`
- [x] `make dev` (or its equivalent direct commands) starts a backend with a dev API key configured
      and a frontend that sends that same key on every REST call and the WS connect
- [x] Live-verified end-to-end through `http://localhost:5173` (not bypassing the frontend/proxy):
      REST calls succeed (200, not 401), and the WS stream connects and delivers real tick-delta
      frames (not rejected, not timed out)
- [x] Behavior is unchanged (no header, no query param) when the new env var is unset -- confirmed by
      a test, not just code inspection
- [x] New regression tests pass; existing frontend (`vitest`) and backend auth test suites still pass

## Related Tickets
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION (built `useSimulation.ts`'s current fetch/WS logic, before
  API-key auth existed)
- TCK-20260823-HTTP-API-KEY-AUTH (added the fail-closed auth this ticket must work around, not
  weaken)
- TCK-20260825-HOTFIX-MAKEFILE-DEV-LIVE-MAP-DOC (this session's own prior ticket that documented
  "Open http://localhost:5173 to view the live map" without live-verifying it actually worked --
  the gap this ticket closes)

## Related Docs
- docs/architecture/http_api_key_authentication.md
- Makefile (`dev` target)
- frontend/vite.config.ts

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- frontend/vite.config.ts
- frontend/src/hooks/useSimulation.ts
- Makefile
- src/api/auth.py (read-only reference, not modified)

## Assumptions / Open Questions
- Exact dev-key value and its hash are arbitrary as long as they match between the Makefile flag and
  the frontend env var -- not a real secret, dev-only, fine to commit in plaintext form as a fixed
  placeholder (mirrors how many OSS projects ship a fixed insecure dev-only credential).
- Whether `.env.development` should be gitignored or committed with the fixed dev value: leaning
  committed (simplicity, matches "one command works out of the box" goal), to be confirmed during
  Implement against `frontend/.gitignore`'s existing `.env*` handling, if any.

## Implementation Notes

**Fixed dev key**: raw `dev-local-key-do-not-use-in-prod`, hash
`3e90488c475fb2c2997525497f1e72e82dec6d68b5738dc7cebba4371f9f0ee2`. Not a real secret -- local dev
only, committed in plaintext by design (matches the "one command works out of the box" goal; see
Assumptions).

**`frontend/vite.config.ts`**: added `ws: true` to the existing `/api` proxy entry. This was the
more fundamental of the two bugs -- it means the live map's WebSocket stream has never worked
through the real `npm run dev` dev server at any point since the epic that built it, independent of
the auth question below.

**`Makefile`'s `dev` target**: backend invocation now passes
`--api-key-hashes "dev:3e90488c475fb2c2997525497f1e72e82dec6d68b5738dc7cebba4371f9f0ee2"`. No other
line changed.

**`frontend/.env.development`** (new): `VITE_API_KEY=dev-local-key-do-not-use-in-prod`, matching the
Makefile's hash. Confirmed NOT caught by the repo's existing `.gitignore` (`.env` there is a bare,
exact-filename pattern -- it does not match `.env.development`).

**`frontend/src/hooks/useSimulation.ts`**: added a module-level `API_KEY` read from
`import.meta.env.VITE_API_KEY`, plus two small helpers (`wsUrl(path)`, `authHeaders()`) used by
every REST call site (`fetchJSON`, and the four bare `fetch()` calls in `sendControl`/`setSpeed`/
`clearEvents` -- these were in the ticket's "wire the frontend" intent even though not spelled out
call-by-call in Scope, since leaving pause/resume/speed/clear-events broken while claiming the fix
complete would be dishonest) and the one `new WebSocket(...)` call site. Both helpers are no-ops
(`undefined` header / no query param) when `API_KEY` is falsy, so any build without the env var set
is byte-identical to pre-fix behavior.

**Real, live end-to-end verification** (not just unit tests): ran the actual `make dev` command,
then hit `http://127.0.0.1:5173/api/v1/{map,static,stats}` with the dev key header -- all 200 (were
401 before this fix). Connected a raw WS client to
`ws://127.0.0.1:5173/api/v1/ws?key=dev-local-key-do-not-use-in-prod` (the exact URL shape
`useSimulation.ts` constructs) through the real Vite dev-server proxy -- received the initial
handshake payload plus 3 consecutive live tick-delta frames (ticks 201-204), each carrying real
`changed`/`removed` entity arrays. This is the same class of test this session's earlier live-map
work used (backend WS + real request/response cycles, live-driven not assumed) -- genuinely
verifies the fix, not just that the code compiles. **Caveat, stated plainly**: no actual browser was
used (none available in this sandbox) -- `import.meta.env.VITE_API_KEY` resolution inside a real
Chrome/Vite runtime was not directly observed; confidence instead comes from two independent pieces
of evidence that together cover the same ground: (1) the frontend component tests exercise the exact
same Vite env-var mechanism (`vi.stubEnv` + module re-import) a real browser's dev-server-injected
`import.meta.env` uses, and (2) the raw WS/curl client reproduces byte-for-byte the same URL/header
shape `useSimulation.ts`'s source constructs. This is the same "no full browser E2E possible, but the
real code paths were live-driven" caveat this session's earlier live-map work also stated honestly.

**Second bug found and fixed during Implement, not originally in the plan's exact file list**: the
four bare `fetch()` calls in `sendControl`/`setSpeed`/`clearEvents` were not named individually in
Scope (which only named `fetchJSON`/`connectWS`), but they hit the same `require_admission`-gated
routes and would have stayed silently broken (pause/resume/speed/clear-events buttons non-functional)
if left alone -- fixed via the same `authHeaders()` helper, in scope of "wire the frontend" intent.

## Test Summary
- `frontend`: `npx vitest run` -- 28/28 passing (26 pre-existing, updated for the new
  `authHeaders()`-added second `fetch()` argument; 2 new, covering both the key-set and key-unset
  cases via `vi.stubEnv` + `vi.resetModules()` + fresh dynamic import, since `API_KEY` is a
  module-level const read once at import time).
- `frontend`: `npm run build` -- succeeds (`tsc -b && vite build`, no type errors).
- `tests/static/test_vite_dev_proxy_ws_forwarding.py` (new) -- 3/3 passing.
- `tests/tools/test_dashboard_makefile_targets.py` -- 3/3 passing (updated `_EXISTING_RECIPE_SNAPSHOT["dev"]`
  for the new `--api-key-hashes` flag on the pinned backend-invocation line).
- `tests/api/test_ws_protocol.py`, `tests/api/test_api_key_auth.py` -- 19/19 passing (unaffected;
  backend `src/api/auth.py` was not modified, per Out of Scope).
- Live, real `make dev` end-to-end run: see Implementation Notes.

## Files Changed
- `frontend/vite.config.ts` (added `ws: true`)
- `Makefile` (`dev` target: added `--api-key-hashes` flag)
- `frontend/.env.development` (new)
- `frontend/src/hooks/useSimulation.ts` (API-key wiring on every REST/WS call site)
- `frontend/src/test/useSimulation.test.tsx` (updated 5 pinned assertions for the new `fetch()`
  second argument; added 2 new tests)
- `tests/static/test_vite_dev_proxy_ws_forwarding.py` (new)
- `tests/tools/test_dashboard_makefile_targets.py` (updated pinned Makefile `dev` recipe snapshot)

## Completion Summary
Both live-reproduced bugs blocking `make dev`'s documented golden path are fixed and live-verified
end-to-end through the real dev-server setup: Vite's `/api` proxy now forwards WebSocket upgrades
(`ws: true`), and the frontend now sends a matching dev API key on every REST call and the WS
connect, wired through a new `.env.development` convention that is a byte-identical no-op when
unset. The backend's fail-closed auth default (`TCK-20260823-HTTP-API-KEY-AUTH`) was not weakened --
this ticket only wires the frontend to use the already-existing mechanism correctly for local dev.
`make dev` now produces a genuinely working live map through `http://localhost:5173`, closing the
gap this session's own earlier `TCK-20260825-HOTFIX-MAKEFILE-DEV-LIVE-MAP-DOC` documented without
live-verifying.
