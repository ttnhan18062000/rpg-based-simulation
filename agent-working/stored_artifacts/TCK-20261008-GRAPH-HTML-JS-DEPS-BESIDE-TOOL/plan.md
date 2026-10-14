---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# plan — TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL

1. `git mv package.json package-lock.json tools/graphify_html/`.
2. `graphify_to_html.py`: resolve `node_modules/` from `Path(__file__)`, add `require_js_assets()` with an actionable error, update the usage docstring.
3. New test pinning the resolution and the error without network or npm.
4. One clause in each of the two docs that name the tool.

Scope guard: the tool is not moved or rewritten; no npm step added to CI or the Makefile.
