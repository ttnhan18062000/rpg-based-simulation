# codebase-m7-api-server: M7 refactor lane, batch 1 (`src/api/server.py`)

On 2026-10-24, in codebase-planner's terminal, the user approved the full split of `src/api/server.py` and chose to fold #704 item 2 into this batch. Logged: https://github.com/ttnhan18062000/rpg-based-simulation/issues/715#issuecomment-6384147652. rpg-planner cleared the file on #697.

1. `TCK-20261024-API-SERVER-CHARACTERIZATION-TESTS`: pin the HTTP surface first. The tests pass on origin/main with `src/` untouched. Commit this ticket before any move.
2. `TCK-20261024-API-SERVER-OBSERVABILITY-UI-STATIC-PAGE`: the 2,093-line page becomes a static file, served byte-identical.
3. `TCK-20261024-API-SERVER-INLINE-ROUTES-TO-ROUTERS`: the 16 remaining inline routes move into routers, the local imports move to module top, and the baselines ratchet down.
4. `TCK-20261024-IMPORT-LINTER-LAYERS-CONTRACT-NAME-NOT-ADVISORY` (hotfix, independent): drop "(advisory)" from the generated contract name.

**Order:** 1 before 2 before 3; 4 at any point. The whole folder ships as one PR. Tickets 2 and 3 must leave ticket 1's fixture unchanged.

**Before push:**
1. The implementer sends codebase-planner the SHA.
2. codebase-planner sends it to lead-planner, who asked for the SHA before any push.
3. The user approves the push.

**On the PR**, codebase-planner:
- notes the new locations of the CORS block and the `/metrics` route for rpg (their ask on #697);
- names the new `tests/api/` files, since that path is rpg's.
