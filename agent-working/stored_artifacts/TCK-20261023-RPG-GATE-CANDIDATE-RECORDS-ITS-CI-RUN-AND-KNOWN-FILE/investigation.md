---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261023-RPG-GATE-CANDIDATE-RECORDS-ITS-CI-RUN-AND-KNOWN-FILE
phase: done
date: 2026-10-26
tags: [testing, regression, simulation-quality]
---

# TCK-20261023-RPG-GATE-CANDIDATE-RECORDS-ITS-CI-RUN-AND-KNOWN-FILE: investigation

## Who builds the candidate (ticket Assumption, Scope 4)
The candidate is built in a GitHub Actions job, not locally: `.github/workflows/rpg-gate-report.yml`, step "Baseline candidate (best-effort)" runs `python -m tools.test_architecture.rpg_gate_candidate ... --known tools/test_architecture/rpg_gate_known.yaml` in the same job that has `GITHUB_RUN_ID`, `GITHUB_RUN_ATTEMPT`, `GITHUB_EVENT_NAME` and `GITHUB_REF` set by the runner for every step. So the assumption holds and **the workflow needs no change**: the CLI reads `os.environ` itself. The step's `env:` block names only REF_NAME and INPUT_REF, but a step inherits the runner's default variables.

`GITHUB_REF` is `refs/heads/main` for a scheduled run and for a dispatch on main. A dispatch with a `ref` input checks out another ref but is already marked `--evidence-only` by the step, so the new ci check is a second layer, not the only one.

## Findings
- Consumers of `provenance`: `rebaseline()` copies the candidate's provenance dict into the baseline, so the two new fields flow into version >= 2 files with no copy code. `staleness()` reads only `commit_sha`-independent fields (harness hash, worlds, seeds, ticks), so it is unaffected.
- `_lint_provenance(prov)` had no version parameter; it now takes `version` and applies the new rule only for an int version >= 2. `rpg_gate_v1.json` lints unchanged (tested against the committed file).
- Existing tests built candidates with no ci and ran `rebaseline()` (including the first-baseline path), so the fixtures gained a main CI run and a known hash. Two assertions were extended (the provenance equality), none removed or weakened.
- Test environment trap: `build_candidate` defaults `env` to `os.environ`; under GitHub Actions the GITHUB_* variables exist, so a test relying on the default would pass locally and differ in CI. Tests pass `env` explicitly; the CLI test sets or deletes the four variables with monkeypatch.

## Decisions (flagged for the reviewer)
1. `ci` is `null` unless all FOUR variables are set and non-empty (the ticket names only GITHUB_RUN_ID being unset). A partial environment records null rather than a half record; `rebaseline` then refuses it. Never a guess.
2. `known_file_sha256` is a REQUIRED keyword of `build_candidate` (no default), so a caller cannot forget it. `rebaseline` also refuses a candidate lacking it, with a message of its own, rather than leaving that to the lint.
3. The lint, beyond "both fields present", checks the hash is 64 lowercase hex and `ci.ref == refs/heads/main`, matching the rebaseline refusal. Shape of `run_id` etc. is non-empty strings (the values as the runner gives them).
4. `rebaseline()` applies the ci refusal to version 1 as well as later versions (no exemption in the ticket); v1 itself already exists and is not touched.
5. Not verified against the GitHub API (out of scope); the id is evidence for the reviewer.
