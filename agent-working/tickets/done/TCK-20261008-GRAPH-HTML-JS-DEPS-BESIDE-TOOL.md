---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL

## Title
Move the graph-html JS dependencies next to the tool that uses them

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
`package.json` and `package-lock.json` at the root are used only by `tools/graphify_to_html.py:33-34`, which reads `node_modules/` relative to the working directory. No Makefile target, no CI, no root `npm install` exists (brief section 1, 3 B3). Filed from `docs/plans/codebase_health/repo_root_layout_ticket_brief.md` by codebase-planner (owner-approved 2026-10-08), sequence in `SEQUENCE.md`. Order: after A (batch A merged).

## Scope
- Move `package.json` and `package-lock.json` next to the tool (directory name per `docs/guidelines/repo_tooling_layout.md`)
- `graphify_to_html.py` resolves `node_modules/` relative to that directory, not the working directory, with a clear error if it is missing; update its usage line and the two docs that mention it

## Out of Scope
- Adding an npm install step to CI or the Makefile
- A JS workspace (the three JS apps are unrelated, brief section 2)
- Any file under `src/`
- Tests that pin CI or the Makefile may be edited under owner decision 8.11, with a notice to testing in the batch PR's handoff

## Acceptance Criteria
- [x] A test pins the resolution path (no network, no npm in CI)
- [x] No `package.json` at the repo root
- [x] `git diff --stat` lists no path under `src/`

## Related Tickets
- TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK
- TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT
- TCK-20261008-NOJEKYLL-TO-DOCS-SITE-STATIC
- TCK-20261008-OPS-FILES-INTO-DOCKER-DIR
- TCK-20261008-DROP-MAKE-BAT
- TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD

## Related Docs
- docs/plans/codebase_health/repo_root_layout_ticket_brief.md
- docs/guidelines/repo_tooling_layout.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/graphify_to_html.py
- package.json
- package-lock.json
- docs/guidelines/repo_tooling_layout.md

## Assumptions / Open Questions
- Evidence and the owner's decisions are in the brief (sections 1 to 5); no open question beyond what the brief lists.

## Implementation Notes
- Directory: `tools/graphify_html/`, beside `tools/graphify_to_html.py`. Rule followed (`docs/guidelines/repo_tooling_layout.md`): `tools/` is the home for repo tooling and there is no `scripts/`; the ~70 flat top-level `tools/*.py` files "are not required to move into a subpackage retroactively", so the tool stays where it is (moving it is a separate decision), and its JS manifests are data beside it, as `tools/eval/queries.json` and `tools/delivery/pr_template_spec.json` already are. No Python package is created (no `__init__.py`): the directory holds `package.json`, `package-lock.json` and, after `npm ci`, a git-ignored `node_modules/`.
- `tools/graphify_to_html.py`: `JS_DEPS_DIR = Path(__file__).resolve().parent / "graphify_html"`; `SIGMA_JS` and `GRAPHOLOGY_JS` are absolute paths under it, no longer relative to the working directory. New `require_js_assets()` runs before the libraries are read and exits with the missing paths and `cd .../tools/graphify_html && npm ci`. The usage docstring now has the one-time setup line.
- Docs: one clause each in `docs/ai/code_test_index_boundaries_decision.md` and `docs/engine/contracts/knowledge_gateway_mcp_contract.md` (the two that name the tool) pointing at `tools/graphify_html/`.
- `tools_orphan_check` (report-only, exit 0): `tools/graphify_html/package.json` LIVE; `tools/graphify_html/package-lock.json` NO_REFERENCES. A hyphenated stem such as `package-lock` can never match an identifier token, so this is the same false report any lockfile under `tools/` gets; no workaround was applied (flagged to codebase-planner). `tests/tools/test_tools_orphan_check.py` and `tests/codebase/test_domain_root_layout.py` pass.

## Test Summary
- New `tests/tools/test_graphify_to_html_js_assets.py` (5 tests, no network, no npm): the deps dir is `tools/graphify_html` and holds both manifests; the resolved paths are absolute and unchanged after `chdir` to a temp dir; no `package.json`/`package-lock.json` tracked at the repo root; missing assets exit with the install command; present assets pass.
- Also run: `tests/tools/test_tools_orphan_check.py` + `tests/codebase/test_domain_root_layout.py` (40 passed); `python3 -m codebase.health check` -> `OK: 0 new, 0 worse` (same improved/gone slack as main).
- The tool itself was not run end to end (needs `npm ci` and a `graphify-out/graph.json`; both are out of scope here). `make knowledge-index-update` not run (times out under the cap).

## Files Changed
- moved: `package.json`, `package-lock.json` -> `tools/graphify_html/`
- `tools/graphify_to_html.py`, new `tests/tools/test_graphify_to_html_js_assets.py`
- docs: `docs/ai/code_test_index_boundaries_decision.md`, `docs/engine/contracts/knowledge_gateway_mcp_contract.md`

## Completion Summary
The graph-html JS dependencies sit beside the tool, the tool finds them from its own location with a clear error when they are missing, and the repo root has no `package.json`. The one open observation is the report-only orphan-check line for the lockfile.
