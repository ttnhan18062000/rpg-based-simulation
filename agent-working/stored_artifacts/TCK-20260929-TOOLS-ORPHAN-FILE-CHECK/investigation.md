# Investigation — TCK-20260929-TOOLS-ORPHAN-FILE-CHECK

The ticket's own Scope/Acceptance Criteria (produced by `create-tickets`) already specify the
exact module shape, classification buckets, and precedents to model. What follows is what I
verified directly before/while implementing.

## Precedents confirmed
- `tools/gate_checks/status_drift_check.py` and `working_log_duplicate_check.py`: both use the
  `check_*() -> list[dict]` + `MARKER:`+json `__main__` shape. Neither is report-only in the exit
  code sense (both `sys.exit(1)` on findings) — this module deliberately diverges and always
  exits 0, per the ticket's explicit report-only/no-ratchet requirement.
- `tools/gate_checks/ci_workflow_test_coverage.py::git_ls_test_files` is the established
  `git ls-files` (not a raw walk) + injectable-file-list-for-tests pattern. Reused directly for
  `git_ls_tracked_files` / the `tracked_files` parameter.
- `tools/audit_unreachable_code.py::IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")` is the
  word-boundary identifier-token regex. Reimplemented locally (not imported — that module's CLI
  surface isn't a stable import target for this narrower purpose), matching the ticket's explicit
  instruction.
- `tools/agent-monitoring/epic_scope_orphan_check.py` — confirmed its "orphan" means an entirely
  different defect (epic ticket dual-presence in `tickets/inprogress/` + `tickets/todos/**`).
  Disambiguated in this module's own docstring.

## Key design decision: bare-stem matching already covers "paths" too
The ticket's scope says "match on bare stems as well as paths". Since `IDENT_RE` splits on
non-identifier characters (`/`, `.`), a path citation like `tools/maintenance/audit_logs.py`
appearing literally in a docstring or the Makefile already tokenizes to include the bare stem
`audit_logs` — so a single bare-stem token-index lookup naturally catches both bare-stem sibling
imports AND path-form citations, without a second matching mechanism. Verified against the real
corpus: `tools/perf/perf_baseline.py`'s only reference is `docs/compliance/checklist.md`'s literal
path citation (`TEST: scripts/perf_baseline.py` in `docs/compliance/checklist.md:302` before
`TCK-20260929-RETIRE-SCRIPTS-DIR` rewrote it) — correctly classified via bare-stem matching alone.

## Classification priority resolved: LIVE > TEST_ONLY > DOC_ONLY > NO_REFERENCES
Not explicitly stated as a priority order in the ticket, but required by construction (each file
lands in exactly one bucket) and directly implied by the ticket's own investigation finding
("counting any doc mention hides every real orphan" — doc mentions are the weakest, most easily
overridden signal). A file with both a doc mention and a real code reference is LIVE, not
DOC_ONLY; a file with both a doc mention and a test reference is TEST_ONLY, not DOC_ONLY.

## Codex-subtree content exclusion — caught by re-reading Out of Scope
Initial implementation excluded Codex subtree files from *classification* (the `excluded`
bucket) but still read their *content* into the token index as a reference source for other
files. Re-reading the ticket's Out of Scope ("Scanning the codex subtrees' contents beyond
listing them as excluded") caught this: fixed so codex files are skipped entirely from
`build_token_index`, never contributing evidence for or against any other file's classification.

## Real-corpus measurement (post scripts/ retirement, as the ticket's Assumptions anticipated)
268 tracked `tools/` files (excluding `__init__.py`/`__pycache__`) classify as: 189 LIVE, 63
excluded (Codex subtrees), 7 TEST_ONLY, 7 DOC_ONLY, 2 NO_REFERENCES
(`tools/hooks/post-commit-reindex.sh`, `tools/search/docker-compose.yml`). Full run: ~2 seconds.
Per the ticket's own Assumptions, these numbers are a measurement, not an acceptance target, and
will shift over time — not asserted by any test.
