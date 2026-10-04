---
status: historical
layer: frontend
authority: P2
audience: agent
ticket_id: TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL
artifact_type: plan
tags: [live-map, rendering, testing, architecture]
---

# Plan — TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL

1. Install the locked frontend dependencies (`npm ci`; none existed on this machine).
2. `frontend/src/visualAssets/`: strict parser (own JSON reader that rejects duplicate keys), pure resolver, typed per-family fallbacks, single-generation loader, scene drawing, harness component, fixture source, dev-only entry; `frontend/rehearsal.html` (not in the production build).
3. Tests next to the code (`__tests__/`): parser, resolver, loader, fallback, scene, harness, isolation (static scan + a real production Vite build into a temp directory, in a node environment).
4. Local-only Playwright capture with its own config and spec (not in CI).
5. Result record `docs/assets/surface_rehearsal_result.md` with a result per `AM5-W01..W09` and gate `AM-C05/C06/C07/C09`; plan and README status notes; store contract "Not built".
6. Close the epic (folder to `done/`), run `make knowledge-index-update` once under the cap.

Scope guard: no change to `src/`, `App.tsx`, hooks, components, Vite config, `package.json`; no new npm dependency; no workflow change.
