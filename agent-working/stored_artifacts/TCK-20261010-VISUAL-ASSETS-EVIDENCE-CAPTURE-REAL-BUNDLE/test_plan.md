---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-EVIDENCE-CAPTURE-REAL-BUNDLE
artifact_type: test_plan
tags: [architecture, testing]
---

# Test plan (as executed)
- TypeScript hash: 9 vitest cases against the Python vectors; two mutants (keep a transparent pixel's colour, drop the NUL after the magic) fail 3 and 6 of them. Python side: the committed vectors equal a fresh computation.
- The record's rules on 22 planted violations (unhashed or non-fixture image, inlined or failed or dev-server request, a non-identical or wrong-scale or missing pixel verdict, pixel verdicts claimed for a page without them, an uncaught or misdirected planted proof, a moved gate result, HiDPI, shape errors); the planted PNG differs in exactly one byte; the hashed-URL pattern.
- Real run: `make visual-assets-bundle-capture`: five pages from hashed URLs, the three rehearsal cells identical, and a copy of the bundle with one pixel of the gem changed fails the same spec on exactly that image.
- Regression: frontend vitest, `tsc`, ESLint on the new files, the whole `tests/visual_assets` suite.
