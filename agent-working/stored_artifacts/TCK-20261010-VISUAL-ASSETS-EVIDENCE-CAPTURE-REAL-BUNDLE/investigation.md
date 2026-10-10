---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-EVIDENCE-CAPTURE-REAL-BUNDLE
artifact_type: investigation
tags: [architecture, testing]
---

# Investigation (written at close from the work)
- The harness pages import fixtures with `import.meta.glob(... ?url)` and the manifest with `?raw`, so a build serves the PNGs as assets and inlines the manifest. Vite inlines assets under 4 KiB as `data:` URLs and the 16 px fixtures are far smaller, so the bundle config needs `assetsInlineLimit: 0` or there is no hashed image URL to check (a real app build may inline them; not tested).
- The existing rehearsal config matches `**/*.capture.ts`, so a bundle spec with that suffix would have run against the dev server; the spec is `bundle.check.ts`. Ports 5174 to 5176 are taken by the other configs; the bundle uses 5177 and 5178. `/usr/bin/google-chrome` is installed and is used through `REHEARSAL_CHROMIUM`; no new dependency.
- The icons page draws `<img>` elements, not canvases, and has no settle marker; the others expose `data-settled`.
- The in-browser hash is a second implementation of the store's `pixels-v1` hash, so it is proven on Python-written vectors (the three artifacts, a non-square image, an alpha mix, transparent pixels that carry colour) and by two deliberate mutants.
