---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261002-UV-FIRST-CI-JOB
artifact_type: plan
tags: [delivery]
---

# Plan — TCK-20261002-UV-FIRST-CI-JOB

1. `.github/workflows/test.yml`, job `simulation-quality` only: replace `actions/setup-python@v6` and `pip install -r requirements.txt` with `astral-sh/setup-uv@v10.2.0` (inputs `version: "0.11.2"`, `python-version: "3.13"`, `activate-environment: true`, `enable-cache: true`) and `uv sync --locked --no-install-project`. A comment says why.
2. `tests/static/test_ci_step_summary_reporting.py`: add `astral-sh/setup-uv@v10.2.0` to `_PRE_EXISTING_USES`, with a comment. Nothing else in the file changes.
3. Verify locally: static and tools tests, the job's own suite from an environment built the same way, no torch, no editable install.
4. Commit. Push and PR wait for the owner. After the PR run, record the run link and the install-step log evidence here, then close.

## Scope guards

Exactly one job changes. `migration-lanes` and `slow` are byte-identical. No other workflow line, Makefile, `src/`, `.claude/` or `CLAUDE.md` change.

## Acceptance-criteria map

| Criterion | Where |
|---|---|
| Exactly one `uv sync`; the other jobs still use pip | step 1; `grep -c` |
| Green real PR run, link recorded | step 4 (open until then) |
| Only new `uses:` is setup-uv, pinned, one job; allowlist +1; pinned jobs identical | steps 1, 2 |
| No knowledge stack in the install log | step 3 locally; PR log after |
| Static and Makefile tests pass; one allowlist edit | step 3 |
| mypy step still named `mypy`; typecheck and venv-path tests pass | step 3 |
| No `src/`, `.claude/`, `CLAUDE.md` in diff | step 3 |
