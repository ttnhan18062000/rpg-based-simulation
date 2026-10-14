---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# investigation — TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL

Source: brief section 3 B3. `package.json` (graphology, graphology-layout, graphology-layout-forceatlas2, sigma) has one consumer: `tools/graphify_to_html.py:33-34`, which read `node_modules/` relative to the working directory. Guideline `docs/guidelines/repo_tooling_layout.md`: `tools/` is the home; flat `tools/*.py` need not move; JSON data beside tools exists (`tools/eval/queries.json`, `tools/delivery/pr_template_spec.json`). `.gitignore` already ignores `node_modules/` at any depth. `tools_orphan_check` token-matches bare stems, so a hyphenated lockfile stem cannot match (report-only).
