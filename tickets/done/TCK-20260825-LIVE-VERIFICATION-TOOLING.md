---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260825-LIVE-VERIFICATION-TOOLING
phase: open
date: 2026-08-25
tags: [rendering, websocket, setup]
---

# TCK-20260825-LIVE-VERIFICATION-TOOLING

## Title
Add repeatable, agent-invokable live-verification tooling for the live map and visual-quality
pipeline -- no more one-off manual checks

## Status
DONE

## Tier
hotfix

## Type
feature

## Priority
P1

## Request Summary
Direct user instruction: this session's live-map/visual-quality verification work (manual `curl`/
raw WS clients, manual `python3 -c` pipeline runs) needs to become real, committed, repeatable
tooling an agent can run on its own in future sessions -- "we need to do this multiple times in the
future, manual approach by me is not efficient for our agent working." This ticket is the tooling
itself; `TCK-20260825-V2-ENGINE-MANAGER-MISSING-TERRAIN` is the real bug this tooling found.

## Scope
- **`tools/review_pipeline_check.py`** (new): live, repeatable CLI check of
  `src/rendering/review_pipeline.py`'s full Tier 0 -> Tier 1 -> Tier 2 escalation pipeline, both
  branches -- a real compiled world (no escalation expected) and a deliberately disconnected
  synthetic state (escalation + annotated-PNG-write expected, same fixture recipe as
  `tests/unit/rendering/test_review_pipeline.py`'s own, kept in sync deliberately). Neither
  `tools/calibrate_rendering.py` nor any other existing tool exercises the escalation/grading half
  of the pipeline live -- only raw metric facts.
- **Headless-browser live-map verification** (Playwright, already a `frontend/package.json`
  devDependency but never wired to a test runner or config):
  - `frontend/playwright.config.ts` (new) -- `webServer` reuses the exact `make dev` command (not
    a parallel/simplified startup sequence), `--no-sandbox` launch arg (required in this sandboxed
    environment).
  - `frontend/e2e/live_map.spec.ts` (new) -- navigates to the real dev server, asserts neither
    blocking screen (loading gate, metadata hard-block) is stuck, asserts the terrain canvas has
    real non-blank pixel content (not just DOM presence), asserts the Header's tick counter
    actually advances over time (live WS proof, not a static snapshot), saves a screenshot
    artifact.
  - `@playwright/test` added as a devDependency (the bare `playwright` package was already present
    but is the library-only package, not the test runner).
  - `npm run test:e2e` script added.
  - Environment note documented in the config's header comment: this sandbox's
    `chromium-headless-shell` binary download failed with `UNABLE_TO_VERIFY_LEAF_SIGNATURE`
    (the same corporate TLS-intercepting-proxy issue already on file from CI log-fetch/HuggingFace
    connectivity) until `NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt` was set for the
    one-time `npx playwright install chromium` step.
- **`Makefile` `PYTHON3` variable** (new): `dev`/`dev-backend`/`serve`/`serve-only` now resolve a
  pydantic-capable `python3` via the same discovery pattern already used by
  `knowledge-index-update`, extended with this worktree's absolute `.venv` path as a candidate.
  Found because Playwright's `webServer` spawns `make dev` as a subprocess without inheriting this
  session's interactive-shell `PATH` export -- bare `python3` (lacking pydantic in a git worktree,
  which gets no `.venv/` of its own) silently crashed the backend, which the frontend's
  `ECONNREFUSED`-tolerant retry logic masked well enough that only a real browser/canvas check
  caught it.

## Out of Scope
- Wiring either new check into CI -- both are meant for on-demand, agent-invoked local
  verification (matching the visual-quality system's own on-demand, never-CI-gated posture, and
  because the Playwright check needs a real backend+frontend dev-server pair, a materially
  different setup than this project's existing `pytest`-based CI lanes).
- Fixing the terrain bug the Playwright check found -- `TCK-20260825-V2-ENGINE-MANAGER-MISSING-TERRAIN`,
  filed and fixed separately.
- Broader Makefile `python3` cleanup -- dozens of other targets still use bare `python3`; only the
  4 `serve`-invoking targets this ticket's own tooling actually exercises were touched.

## Acceptance Criteria
- [x] `tools/review_pipeline_check.py` runs live and passes both branches (no-escalation,
      escalation-with-real-PNG) against real data
- [x] `frontend/e2e/live_map.spec.ts` runs live via `npx playwright test` and passes, with a real
      screenshot artifact as evidence
- [x] `make dev` (and the 3 other affected targets) resolve a real, pydantic-capable `python3` from
      any worktree, not just the main checkout
- [x] Existing `tests/tools/test_dashboard_makefile_targets.py` pinned-snapshot guard updated and
      passing
- [x] Both new tools are documented well enough (module/file header comments) that a future
      session can re-run them without rediscovering the environment quirks (NODE_EXTRA_CA_CERTS,
      `--no-sandbox`) from scratch

## Related Tickets
- TCK-20260825-V2-ENGINE-MANAGER-MISSING-TERRAIN (the real bug this tooling found)
- TCK-20260825-LIVE-MAP-DEV-AUTH-AND-WS-PROXY-FIX (this session's earlier live-map fixes, whose own
  completion notes explicitly flagged "no real browser was available" as a caveat -- this ticket
  closes that gap)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- tools/review_pipeline_check.py (new)
- frontend/playwright.config.ts (new)
- frontend/e2e/live_map.spec.ts (new)
- frontend/package.json (`@playwright/test` devDependency, `test:e2e` script)
- Makefile (`PYTHON3` variable; `dev`/`dev-backend`/`serve`/`serve-only`)
- tests/tools/test_dashboard_makefile_targets.py (pinned snapshot updated)

## Assumptions / Open Questions
- The `NODE_EXTRA_CA_CERTS` requirement for installing Chromium is sandbox-specific (this machine's
  corporate TLS-intercepting proxy) -- documented in `playwright.config.ts`'s header comment so a
  future session hitting the same download failure doesn't have to rediscover the fix, but not
  assumed to be universal across every future environment.
- `--no-sandbox` is kept unconditionally rather than only under a sandbox-detection check -- harmless
  everywhere for this suite (never opens untrusted content), simpler than conditional logic.

## Implementation Notes
`tools/review_pipeline_check.py`'s disconnected-state fixture (`_build_disconnected_state`) is a
deliberate, comment-flagged duplicate of `tests/unit/rendering/test_review_pipeline.py`'s own
fixture, not a shared import -- keeping the tool self-contained (no test-module import from
production tooling) was judged more valuable than avoiding the small duplication, given the two
call sites' different purposes (pytest assertion vs. human-readable live CLI report).

`live_map.spec.ts`'s non-blank-pixel check reads real `ImageData` via `canvas.getContext('2d').getImageData(...)`
rather than trusting DOM presence alone -- this is the same class of gap a `toBeVisible()`-only
assertion would have missed (a canvas can be "visible" per the accessibility/layout tree while
carrying zero real draws, which is exactly what the pre-terrain-fix state looked like: a
0-width/0-height canvas element that was still technically present in the DOM).

The Makefile `PYTHON3` fix and the terrain fix were both discovered through the same debugging
session (this tooling surfacing them one after another): first `ECONNREFUSED` (Makefile), then a
`0x0` canvas that traced to an empty `/api/v1/map` response (the terrain bug) -- kept as two
separate tickets since they are genuinely independent, differently-scoped fixes that happened to
surface via the same investigation.

## Test Summary
- `tools/review_pipeline_check.py` -- live run, both branches PASS (`grade=B combined_score=0.262
  escalate=False` for the real world; `grade=F combined_score=-1.000 escalate=True` with a real
  98x98/322-byte annotated PNG written for the synthetic disconnected state)
- `npx playwright test` -- 1/1 passing, with `frontend/e2e-artifacts/live_map_render.png` as
  visual evidence (not committed -- a local run artifact, regenerated on each run)
- `tests/tools/test_dashboard_makefile_targets.py` -- 3/3 passing after updating the pinned `dev`/
  `dev-backend`/`serve`/`serve-only` recipe snapshots

## Files Changed
- `tools/review_pipeline_check.py` (new)
- `frontend/playwright.config.ts` (new)
- `frontend/e2e/live_map.spec.ts` (new)
- `frontend/package.json`, `frontend/package-lock.json`
- `Makefile`
- `tests/tools/test_dashboard_makefile_targets.py`

## Completion Summary
Both gaps this session's own earlier work explicitly flagged as caveats -- no live Tier-2-escalation
trigger, no real browser check -- now have real, repeatable, committed tooling. Running the
browser check immediately surfaced a genuine, severe, independent bug
(`TCK-20260825-V2-ENGINE-MANAGER-MISSING-TERRAIN`), which is exactly the value this kind of tooling
is meant to provide going forward.
