---
status: historical
layer: frontend
authority: P2
audience: agent
ticket_id: TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL
artifact_type: investigation
tags: [live-map, rendering, testing, architecture]
---

# Investigation — TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL

- **No frontend dependencies were installed** anywhere on this machine (no `node_modules`); `npm ci` from the lockfile (323 packages, 21 s) was the only way to run vitest, lint or the build. Nothing was added to `package.json`.
- Existing conventions: Vitest + jsdom, tests under `src/test/`; `tsconfig.app.json` has `erasableSyntaxOnly` (no constructor parameter properties: the first `npm run build` failed on them and the classes were rewritten); the live map draws with Canvas rectangles and `CELL_SIZE = 16` (`constants/colors.ts`).
- `esbuild` cannot run inside the jsdom environment (the `TextEncoder` invariant), so the isolation test, which runs a Vite production build, uses `// @vitest-environment node`.
- jsdom has no `import.meta.url` file URLs, so tests resolve paths from `process.cwd()` (vitest runs from `frontend/`).
- `useSimulation.test.tsx` failed once in a full parallel run (`transitions to CONNECTING_LIVE ...`), passed alone and in the next full run; unrelated to this ticket and not touched.
- Playwright 1.62.1 expects a Chromium build (1234) that is not cached; the cached 1223 headless shell was used through `REHEARSAL_CHROMIUM` (Chromium 148.0.7778.96).
- The capture exposed a real defect: the role letter of the hollow-frame fallback was drawn dark on the dark backdrop (invisible). Fixed (light letter where the glyph is hollow) and covered by a contrast test.
- The normal-path files are unchanged against the branch base (`git diff 2cfa8ab1 --stat` is empty for `src/`, the listed frontend directories, Vite config, `index.html`, `package*.json`).
