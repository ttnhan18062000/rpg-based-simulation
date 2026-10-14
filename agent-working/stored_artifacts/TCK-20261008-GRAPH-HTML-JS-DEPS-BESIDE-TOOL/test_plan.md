---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# test_plan — TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL

Normal flow: deps dir and manifests resolve beside the tool; paths absolute.
Edge: cwd independence (chdir to tmp); present assets pass.
Failure mode: missing assets raise SystemExit naming the paths and `npm ci`.
Regression: no root package.json/package-lock.json tracked; orphan check and domain-root layout tests still pass.

## Proof Plan
- level: unit (paths and a fake file tree)
- proof kind: automated tests
- oracle source: the repo's own file layout and `git ls-files`
- expected effect: resolution beside the tool, independent of cwd; clear error when missing; no root manifests
- selected commands: `pytest tests/tools/test_graphify_to_html_js_assets.py tests/tools/test_tools_orphan_check.py tests/codebase/test_domain_root_layout.py` (45 passed)
