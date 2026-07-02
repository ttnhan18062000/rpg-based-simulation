---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260702-CI-REQUIREMENTS-SPLIT
phase: done
date: 2026-07-02
tags: [ci, requirements, torch, knowledge-search]
---

# TCK-20260702-CI-REQUIREMENTS-SPLIT

## Title
CI Tests workflow fails on every job — requirements.txt bundles local-agent-only torch/ML stack

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
Every job in `.github/workflows/test.yml` (Integration, Unit x3, API/tools, Migration lanes,
Type check, Architecture/docs, Perf/cert, Slow) fails identically at the
`pip install -r requirements.txt` step. Root cause: `requirements.txt` pins
`torch==2.12.1+cpu`, a CPU-only local-version wheel that only exists on
`download.pytorch.org/whl/cpu`, not on public PyPI. CI runs plain
`pip install -r requirements.txt` with no extra index URL, so resolution fails and the
install step exits 1 before any tests run.

`requirements.txt` was never meant to be a CI dependency file — per
`docs/guidelines/agent_working_environment.md`, it is the local agent working environment
setup file for the knowledge-search MCP tooling (`sentence-transformers`, `sqlite-vec`,
`rank_bm25`, torch as their backend). `pyproject.toml` already models the correct split:
core `dependencies` vs. the `knowledge` optional-dependency extra. CI's `test.yml` just
happens to `pip install -r requirements.txt` wholesale, pulling in packages no test job
actually needs — confirmed no module in `tools/search_*.py` imports torch/sentence_transformers/
sqlite_vec/rank_bm25 at module level (all lazy, function-local, wrapped in try/except).

## Scope
- Move `torch`, `sentence-transformers`, `sqlite-vec`, `rank-bm25` out of `requirements.txt`
  into a new `requirements-knowledge.txt` (local agent tooling only).
- `requirements.txt` keeps all other pinned versions unchanged (core app + test deps used by
  CI) so no package version used by CI jobs shifts.
- Update `docs/guidelines/agent_working_environment.md` first-time setup steps to install
  `requirements-knowledge.txt` (with the CPU wheel index for torch) as an explicit second step.
- Add a static guard test so the ML/knowledge-search stack can't silently return to
  `requirements.txt`.
- `.github/workflows/test.yml` is unchanged — it keeps installing `requirements.txt`, which is
  now safe to resolve from public PyPI.

## Out of Scope
- Do not change `pyproject.toml` (already correctly modeled).
- Do not switch CI to install from `pyproject.toml` instead of `requirements.txt` — that would
  drift CI off the currently-pinned versions of unrelated packages (duckdb, pyarrow, starlette,
  etc.) which is a larger, unvalidated change.
- Do not add `--extra-index-url` to CI — CI should not need torch at all.

## Acceptance Criteria
- [ ] `requirements.txt` contains no `torch`, `sentence-transformers`, `sqlite-vec`, `rank-bm25`
- [ ] `requirements-knowledge.txt` exists with those four packages + CPU wheel index instructions
- [ ] `docs/guidelines/agent_working_environment.md` documents the two-file install
- [ ] Static guard test fails if the ML stack reappears in `requirements.txt`
- [ ] `pip install -r requirements.txt` resolves cleanly against public PyPI (verified locally
      via `pip install --dry-run` or equivalent)
- [ ] All existing tests under `tests/tools/` and `tests/static/` still pass

## Related Tickets
- TCK-20260612-LOCAL-CTX-HTTP-API (introduced requirements.txt as agent tooling install file)
- TCK-20260612-LOCAL-CTX-HYBRID-SEARCH (added rank-bm25 to requirements.txt)

## Related Docs
- `docs/guidelines/agent_working_environment.md`

## Related Stored Artifacts
- none (hotfix)

## Related Code Areas
- `requirements.txt`
- `requirements-knowledge.txt` (new)
- `docs/guidelines/agent_working_environment.md`
- `tests/static/`

## Assumptions / Open Questions
- Assuming no CI job needs actual embedding/search behavior exercised — confirmed via
  try/except ImportError guards in `tools/knowledge_search.py` and no module-level ML imports.

## Implementation Notes
1. `requirements.txt`: removed `torch==2.12.1+cpu`, `sentence-transformers==5.6.0`,
   `sqlite-vec==0.1.9`, and the (duplicated) `rank-bm25==0.2.2` lines. Replaced the old
   torch-index comment block with a header explaining the split and pointing to
   `requirements-knowledge.txt`.
2. `requirements-knowledge.txt` (new): holds the four removed packages, with the CPU wheel
   index instructions for torch preserved (torch must be installed separately before this
   file, same constraint as before — just scoped to local tooling only now).
3. `docs/guidelines/agent_working_environment.md`: prerequisites table now lists both
   requirements files with their distinct purposes; first-time setup gained an explicit
   step 1b installing torch from the CPU wheel index then `requirements-knowledge.txt`.
4. `tests/static/test_ci_requirements_no_ml_stack.py` (new): guards against the ML stack
   reappearing in `requirements.txt`, and asserts `requirements-knowledge.txt` still carries it.
5. `.github/workflows/test.yml` left untouched — every job's existing
   `pip install -r requirements.txt` step now resolves against public PyPI with no code change
   needed there.
6. Verified via `pip install --dry-run -r requirements.txt` in a throwaway clean venv (matches
   CI's `ubuntu-latest` + `actions/setup-python` flow): resolves cleanly, no torch involved.
7. Ran `make knowledge-index-update` since a docs/ file changed (per CLAUDE.md After Work rule).

## Test Summary
```
pytest tests/static/test_ci_requirements_no_ml_stack.py tests/tools/ -q -m "not slow"
# 418 passed, 28 deselected, 2 pre-existing failures (test_search_mcp.py — .mcp.json
# command/args drift, confirmed pre-existing via git stash, unrelated to this change,
# out of scope)

pytest tests/static tests/architecture tests/docs -q -m "not slow"
# 71 passed, 1 skipped

pip install --dry-run -r requirements.txt   # in clean venv — resolves cleanly, no errors
```

## Files Changed
- `requirements.txt` — removed torch/sentence-transformers/sqlite-vec/rank-bm25 (CI-breaking
  ML stack); now only core app + test deps
- `requirements-knowledge.txt` (new) — local agent knowledge-search tooling deps
- `docs/guidelines/agent_working_environment.md` — documents two-file install
- `tests/static/test_ci_requirements_no_ml_stack.py` (new) — regression guard

## Completion Summary
Root cause of every CI Tests-workflow job failing identically at `pip install -r
requirements.txt`: the file bundled the local agent knowledge-search tooling's ML stack
(torch CPU wheel + sentence-transformers + sqlite-vec + rank-bm25) into what CI treats as its
test dependency file. Torch's `+cpu` local-version wheel isn't resolvable from public PyPI
without `--index-url https://download.pytorch.org/whl/cpu`, which CI never supplied, so every
job's install step exited 1 before any test ran. No test/module needs these packages at import
time (all lazy, function-local, try/except-guarded) — confirmed no regression. Split them into
`requirements-knowledge.txt` (local tooling only, documented in
`agent_working_environment.md`), left `requirements.txt` with unchanged pinned versions for
everything else, and added a static guard test to prevent recurrence. `pyproject.toml` already
modeled this split correctly via its `knowledge` optional-dependency extra; `requirements.txt`
just hadn't followed it.
