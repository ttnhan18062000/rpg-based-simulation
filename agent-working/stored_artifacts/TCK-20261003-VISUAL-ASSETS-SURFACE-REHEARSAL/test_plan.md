---
status: historical
layer: frontend
authority: P2
audience: agent
ticket_id: TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL
artifact_type: test_plan
tags: [live-map, rendering, testing, architecture]
---

# Test Plan — TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL

Parser: every rejection case and duplicate JSON keys; frozen snapshot. Resolver: every fallback reason; unknown key (no lookup, no fetch, no registration, prototype-chain and path-like keys). Loader: two generations with out-of-order completions, late completions closed and recorded, missing file not fetched, corrupt and wrong-size images. Fallbacks: a glyph and letter per family, four distinct shapes, one shared palette, label contrast at least 3:1, text alternatives; fixture alpha masks differ. Scene: predeclared layout, native-scale drawing, smoothing off. Harness: cells, canvas sizes, invalid manifest alert, corrupt and missing images, no fetch. Isolation: static scans, module imports, cell size copy, real production build output. Mutants: loader keeps late completions; duplicate keys allowed; unknown key lookup; cross equals diamond; letter always dark; the app imports (and uses) the parser; the config builds the rehearsal page.

## Proof Plan

- Level: unit and component tests (jsdom) plus a production-build check (node), and one local real-browser capture.
- Proof kind: executable tests, recorded mutants, a local capture with an evidence file.
- Oracle source: the ticket's acceptance criteria and the M5 plan's deliverables and gates.
- Expected effect: every test passes and each mutant fails its named test; results per gate are recorded honestly (no pass by default).
- Selected commands: `npx vitest run`; `npx eslint src/visualAssets`; `npm run build`; `npx playwright test -c playwright.rehearsal.config.ts` (local).
