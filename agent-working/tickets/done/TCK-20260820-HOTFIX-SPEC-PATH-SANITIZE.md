---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260820-HOTFIX-SPEC-PATH-SANITIZE
phase: done
date: 2026-08-20
tags: [security, architecture]
---

# TCK-20260820-HOTFIX-SPEC-PATH-SANITIZE

## Title
Constrain `restore_checkpoint`'s unsanitized `spec_path` request-body parameter to an allowed base directory before `open()`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
`src/api/routes/scenarios.py`'s `restore_checkpoint()` (line 60) opens the request-body field
`spec_path` directly via `open(spec_path, "r", encoding="utf-8")` with zero sanitization, while the
same function's other two identifiers — `scenario_id` and `checkpoint_name` — are both passed
through `sanitize_id()` two lines above (lines 53-54). This is finding **D22-F2** from
`experiments/audit_expansion/PROPOSAL.md` (Security Posture & Attack Surface audit), scored 15/15
(maximum) severity: an unauthenticated caller can supply any filesystem path as `spec_path` and get
(1) a file-existence oracle from the endpoint's differing error responses — `FileNotFoundError` →
HTTP 404 `"Spec file not found: {spec_path}"` vs. any parse/schema failure → HTTP 400
`"Invalid spec: {e}"` — and (2) a narrow, schema-gated content-injection path: if a guessed/supplied
path happens to contain YAML that parses into a valid `SimulationScenarioDefinition`, its content
becomes the restored scenario's spec. This is the sibling finding to D22-F1 (wildcard CORS +
credentials), already fixed today as `TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG`;
this ticket closes the other half of the same finding pair.

## Scope
- In `src/api/routes/scenarios.py`'s `restore_checkpoint()`, constrain `spec_path` to a path that,
  after resolution, must remain inside an allowed base directory before it is ever passed to
  `open()`. This must be a path-containment check (e.g. resolve the candidate path and verify it is
  a descendant of a fixed allowed base directory), **not** a blanket `sanitize_id()` call —
  `sanitize_id()`'s alphanumeric/`_`/`-`-only pattern is designed for bare identifiers and would
  reject legitimate relative/nested spec paths.
- Reject (with a clear 400, not a silent fallback) any `spec_path` that resolves outside the
  allowed base directory, before attempting `open()`.
- Preserve existing behavior for valid, in-bounds `spec_path` values and for the `spec_path is None`
  default-spec branch (lines 68-74) — both must continue to work unchanged.
- Add test coverage proving: (a) a legitimate in-bounds `spec_path` still restores successfully,
  (b) a `../`-style traversal attempt is rejected before any `open()` call, (c) an absolute path
  outside the allowed base directory is rejected, (d) the file-existence oracle is closed for
  out-of-bounds paths (traversal/absolute-path rejection must not leak whether the target file
  exists — it should fail on containment before any filesystem existence check).

## Out of Scope
- Authentication, rate limiting, or admission control on this or any other route — that is
  `TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC`'s explicitly deferred scope (deployment-plan decision
  confirmed 2026-08-19: this API surface stays on a trusted network). This ticket only closes the
  unauthenticated file-open primitive itself, not the broader lack of auth on the endpoint.
- Any change to `sanitize_id()` itself, or to how `scenario_id`/`checkpoint_name` are validated —
  those two are already correctly sanitized and untouched by this scope.
- `create_checkpoint()`'s checkpoint-name handling — already fully sanitized via `sanitize_id()`,
  not part of this finding.
- Changing the response shape/status codes of `restore_checkpoint()` beyond what's needed to close
  the file-existence oracle for out-of-bounds paths (e.g. do not redesign the 404/400 error scheme
  for in-bounds paths).
- Any change to `ScenarioCheckpointer.restore()` or the `.ckpt` checkpoint path handling
  (`path = Path(f"checkpoints/{scenario_id}/{checkpoint_name}.ckpt")`) — that path is already built
  from sanitized identifiers, not the vulnerable parameter.

## Acceptance Criteria
- [x] `spec_path` is resolved and checked against a fixed allowed base directory before any
      `open()` call in `restore_checkpoint()`.
- [x] A `spec_path` value that resolves outside the allowed base directory (via `../` traversal or
      an absolute path) is rejected with an HTTP 400 before any filesystem existence check —
      verified by a test that the rejection path does not distinguish "exists but out of bounds"
      from "doesn't exist" (closing the file-existence oracle for out-of-bounds paths).
- [x] A legitimate in-bounds `spec_path` still successfully restores a checkpoint (regression
      coverage), and the `spec_path is None` default-spec branch is unaffected.
- [x] `docs/parity_ledger/infrastructure.yaml`'s `INFRA-216` entry (Scenario Runtime REST API,
      covers this exact endpoint) is updated to reflect the new containment check, per this repo's
      parity rule (logic change → same-session parity ledger update).
- [x] New/updated tests pass: `pytest tests/api/test_scenario_runtime_api.py -v` and any new test
      file covering this fix.

## Related Tickets
- TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG (sibling finding, D22-F1, already fixed
  2026-08-19 — this ticket closes the other half of the same D22 finding pair from the same audit)
- TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC (broader auth/admission-control scope, explicitly
  deferred — not touched by this ticket)
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic of the wider audit line)

## Related Docs
- experiments/audit_expansion/PROPOSAL.md (D22-F2 finding, lines 154-173, 663, 749 — source of this
  ticket's scope)
- docs/engine/scenario_runtime_contract.md (documents the three scenario-runtime REST endpoints,
  including `restore_checkpoint`'s `spec_path` body field)
- docs/parity_ledger/infrastructure.yaml (`INFRA-216` — Scenario Runtime REST API entry covering
  this endpoint; needs status/evidence update per this ticket's acceptance criteria)
- docs/plans/http_admission_control_epic.md (broader HTTP-surface hardening tracking doc; this
  finding is narrower and doesn't require touching this doc, but note it for cross-reference)

## Related Stored Artifacts
None found — no prior investigation or plan specific to this finding exists in `stored_artifacts/`.

## Related Code Areas
- src/api/routes/scenarios.py (`restore_checkpoint()`, line 60 — the vulnerable `open()` call)
- src/observability/reporting/history_query.py (`sanitize_id()`, line 13 — the existing
  identifier-sanitization pattern already applied to `scenario_id`/`checkpoint_name`; NOT to be
  reused verbatim for `spec_path` since it's a path, not a bare identifier)
- src/engine/scenario_checkpoint.py (`ScenarioCheckpointer.restore()` — consumer of the validated
  `spec`, untouched by this fix)
- src/scenarios/schema.py (`SimulationScenarioDefinition` — the schema the loaded YAML is validated
  against; untouched, still the correct final gate after path containment)

## Assumptions / Open Questions
- Assumes an "allowed base directory" concept for scenario specs is either already established
  elsewhere in the codebase (e.g. a scenarios/specs directory convention) or needs to be introduced
  as a small fixed constant in this fix — implementer should check for an existing spec-directory
  convention (e.g. how scenario specs are loaded elsewhere, such as CLI scenario loading) before
  inventing a new one, to keep this a minimal hotfix rather than a new subsystem.
- Assumes `layer: architecture` is correct by precedent — this repo has no dedicated `api` or
  `security` layer in `registries/layer_registry.jsonl`; the sibling D22-F1 CORS ticket
  (`TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG`), the closest analogous prior ticket,
  also used `layer: architecture` for a fix in `src/api/`. If wrong, note during implementation
  rather than blocking scope.
- Priority set to P0 (vs. the CORS sibling's P3) because this finding, unlike the CORS one, is a
  currently-live, unauthenticated, no-mitigating-factor exploit primitive (arbitrary server-side
  file-open reachable by any caller) rather than a spec-invalid-but-browser-blocked config; open to
  downgrade if implementation reveals additional mitigating factors not visible from static review.
- If no fixed "allowed base directory" for scenario specs exists in the codebase today, the
  implementer must pick one (e.g. a `scenarios/specs/` or similar directory) — this choice should
  be documented in Implementation Notes, since it defines the actual security boundary.

## Implementation Notes
- `src/api/routes/scenarios.py`: added a module-level constant `ALLOWED_SPEC_BASE_DIR =
  Path("scenario_specs")` — a repo-root-relative fixed base directory chosen to mirror the
  existing `checkpoints/` relative-path convention used two lines below in the same function for
  the `.ckpt` path (no prior "scenario spec directory" convention existed anywhere in the codebase
  — grepped for `scenario_specs` and scanned `src/scenarios/`, `src/cli/`, `docs/engine/
  scenario_runtime_contract.md` first; the closest analog, `data/content/simulation_scenarios/`, is
  a catalog-list format (multiple scenarios per file) rather than a single ad-hoc
  `SimulationScenarioDefinition` YAML per file, so it wasn't reused). Neither `scenario_specs/` nor
  `checkpoints/` need to exist at repo root for the containment check itself — `Path.resolve()`
  doesn't require existence — they're created/populated by callers as needed, same as the existing
  `checkpoints/` handling.
- Added `_resolve_spec_path(spec_path: str) -> Path`, a local helper implementing the same
  resolve()/`is_relative_to()` containment idiom already established elsewhere in this repo
  (`src/worldbuilding/repository.py`, `src/lab/repository.py`, `src/lab/workflows/_path_safety.py`).
  Considered reusing `src.lab.workflows.safe_path_resolution` directly (functionally identical,
  already tested) but rejected it: importing it pulls in `src.lab.workflows.__init__`, which eagerly
  imports every lab workflow class — an unwarranted cross-domain coupling (no existing `src/api/*`
  file imports from `src/lab/*`) for a single ~10-line pure function. Inlining keeps the security
  check colocated with its call site and avoids a new API→Lab dependency for a hotfix-tier change.
  Per the ticket scope, this is a path-containment check, not `sanitize_id()` (which is
  alphanumeric/`_`/`-`-only and would reject legitimate nested spec paths).
- `_resolve_spec_path()` is called and raises `HTTPException(400)` *before* the existing
  `try/except FileNotFoundError` block that wraps `open()`, so the containment rejection is never
  reformatted by the broad `except Exception` handler and never reaches a filesystem existence
  check — closing the file-existence oracle for out-of-bounds paths per AC.
- The `spec_path is None` default-spec branch (lines ~90-96, unchanged) and the in-bounds
  `open()`/YAML/schema-validation flow are otherwise untouched.
- `docs/engine/scenario_runtime_contract.md`: documented the new containment behavior in the
  `POST /restore/{checkpoint_name}` section (base dir, 400 error condition, and that 404 for a
  missing spec file is now only reachable once the path is confirmed in-bounds).
- `docs/parity_ledger/infrastructure.yaml`: updated `INFRA-216`'s `text` and `test_path` to
  describe and cite the new containment check.
- Ran `make knowledge-index-update` after the docs edits per repo convention; it failed with an
  offline `huggingface.co` connection error inside `sentence_transformers` model loading — a
  pre-existing environment limitation on this machine unrelated to this change (this exact
  HuggingFace-offline issue is a known, previously logged environment gap on this machine, not
  something introduced or fixable within this hotfix's scope).
- Ran `graphify update .` after the `src/`/`tests/` edits — succeeded (33188 nodes, 98811 edges).

## Test Summary
Added 5 new tests to `tests/api/test_scenario_runtime_api.py` covering: (a) in-bounds `spec_path`
restores successfully, (b) `../`-traversal `spec_path` rejected with 400 before any `open()`,
(c) absolute out-of-bounds `spec_path` rejected with 400, (d) an existing-but-out-of-bounds path
and a nonexistent-and-out-of-bounds path both return the identical 400 response (closing the
file-existence oracle), (e) the `spec_path is None` default-spec branch still restores
successfully, unaffected by the new containment check. All tests use a `tmp_path`-backed
`allowed_spec_dir` fixture that monkeypatches `ALLOWED_SPEC_BASE_DIR` for isolation.

`pytest tests/api/test_scenario_runtime_api.py -v` — 16 passed (11 pre-existing + 5 new), 0 failed.

## Files Changed
- `src/api/routes/scenarios.py` — added `ALLOWED_SPEC_BASE_DIR` constant and
  `_resolve_spec_path()` helper; `restore_checkpoint()` now resolves/validates containment before
  `open()`.
- `tests/api/test_scenario_runtime_api.py` — added 5 tests + `allowed_spec_dir` fixture covering
  the containment fix.
- `docs/engine/scenario_runtime_contract.md` — documented the new `spec_path` containment
  behavior and updated the restore endpoint's error table.
- `docs/parity_ledger/infrastructure.yaml` — updated `INFRA-216` entry (`text`, `test_path`) to
  reflect the containment check and cite the new tests.
- `tickets/inprogress/TCK-20260820-HOTFIX-SPEC-PATH-SANITIZE.md` — this ticket, filled in during
  implementation (Implementation Notes, Test Summary, Files Changed, Completion Summary, Status,
  Acceptance Criteria checkboxes).

## Completion Summary
Closed finding D22-F2: `restore_checkpoint()`'s `spec_path` request-body field is no longer passed
unsanitized to `open()`. It is now resolved against a fixed, repo-root-relative allowed base
directory (`scenario_specs/`) and any path that resolves outside that directory — via `../`
traversal or an absolute path — is rejected with HTTP 400 before any filesystem existence check,
closing the file-existence oracle the finding described. Legitimate in-bounds `spec_path` values
and the `spec_path is None` default-spec branch continue to work unchanged. The parity ledger
(`INFRA-216`) and the scenario runtime contract doc were updated in the same session, and 5 new
tests plus the 11 pre-existing tests in `tests/api/test_scenario_runtime_api.py` all pass.
