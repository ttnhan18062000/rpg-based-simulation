---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261019-SEMGREP-BASELINE-FINDINGS-IN-SRC-TRIAGE
phase: implement
date: 2026-10-19
tags: []
---

# TCK-20261019-SEMGREP-BASELINE-FINDINGS-IN-SRC-TRIAGE

## Title
Triage the baseline Semgrep findings in src/** from the new security-scan workflow (#665): fix the real ones, mark the false positives in code

## Status
INPROGRESS

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
platform-planner-u24 (2026-10-19) reported the first report-only Semgrep scan of main (run 39233931697, SARIF artifact "semgrep", code-scanning category semgrep). Nothing blocks. This ticket triages each src/** finding. A first read (rpg-planner) is below; confirm each one against the code.

## Scope
For each finding, record a verdict (real / false positive) with a reason. Fix the real ones. Mark a false positive at its line in a way the scanner honours (for example `hashlib.md5(..., usedforsecurity=False)` for non-security hashing), never by disabling the rule repo-wide.

The findings, with the first read:
- **md5:** `src/domains/world_emergence/services.py` lines 90, 138 and 152; `src/lab/mutation.py:440`; `src/observability/warehouse/clickhouse.py:44`; `src/replay/fingerprint.py:119`; `src/systems/lifecycle_systems/genetics.py:84`.
  - First read: deterministic seeding, fingerprinting or ids, not security. Likely a false positive. Use `usedforsecurity=False`, provided the hash value is unchanged, since determinism and fingerprints depend on it.
- **request-with-http:** `src/observability/watchdog.py` lines 29, 47 and 74.
  - First read: internal compose-network calls to the health endpoint, Prometheus and Loki. Low risk. Confirm the URLs are env-configured and internal only.
- **wildcard-cors:** `src/api/server.py:109`.
  - First read: deliberate (TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG). The wildcard origin has no credentials, and auth is the API key header. Confirm, and record the rationale for the scanner.
- **src/lab:**
  - `context.py:93` request-data-write;
  - `workflows/generate_simulation_setup.py:489` directly-returned-format-string;
  - `workflows/prepare_simulation_execution.py:174` insecure-file-permissions;
  - `workflows/propose_simulation_enhancements.py:184` avoid-insecure-deserialization.
  - First read: dev or lab tooling. The deserialization one (184) needs a real look (what is loaded, from where), as does the file permissions one.

## Out of Scope
- `.github/workflows/rpg-gate-report.yml` (9 mutable-action-tag). The workflow belongs to the testing-owned gate harness, so it goes to testing-planner.
- Changing any hash VALUE: determinism, replay fingerprints and the paired tool depend on them.

## Acceptance Criteria
- Every listed finding has a verdict with a reason. The real ones are fixed with a test where behaviour changes, and the false positives are marked at the line.
- The final hashes are identical on 3 gate worlds × seed 42 (the md5 call-site changes must not move a hash).
- The next security-scan run on main shows the src/** findings resolved or justified.

## Related Tickets
- #665 (security-scan workflow)
- TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG

## Related Docs
- none

## Related Stored Artifacts
- none

## Related Code Areas
- the files listed in Scope

## Assumptions / Open Questions
- After v1, unless a finding turns out to be a real exposure, in which case it's raised at once.

- 2026-10-23 lead-planner-u24 triage of the 14 open code-scanning alerts (all first seen 10-19; https://github.com/ttnhan18062000/rpg-based-simulation/security/code-scanning). Low priority: after HUNGER, H1/H2 and F3/F4.
  - REAL: #228 src/api/server.py:110 CORSMiddleware allow_origins=["*"] (plus methods/headers *). Read the allowed origins from config, defaulting to the local dev origins. COORDINATE with the codebase M7 refactor of server.py (#697): land after it, or on top of it.
  - FALSE POSITIVE, fix in code with usedforsecurity=False (add a reasoned nosemgrep too if the rule still fires): hash output unchanged, so hash-neutral; prove it with the 3-world check where hashed state is touched. MD5 at #241 src/replay/fingerprint.py, #242 src/systems/lifecycle_systems/genetics.py, #229/#230/#231 src/domains/world_emergence/services.py, #233 src/lab/mutation.py, #237 src/observability/warehouse/clickhouse.py.
  - SUPPRESS IN CODE, never dismissed in the Security tab (repo convention from #701, followed by #729): `# nosemgrep: <full rule id>` with a one-line reason: #236 propose_simulation_enhancements.py:184 (yaml.dump writes, not load); #235 prepare_simulation_execution.py:174 (chmod 0o755 on a generated script, intended); #238/#240 watchdog.py (http to Loki on the internal Docker network).
  - TO READ: #232 src/lab/context.py (request-data-write); #234 src/lab/workflows/generate_simulation_setup.py (directly returned format string).

## Implementation Notes
Branch rpg-semgrep-src-findings (dispatch rpg-planner, owner-approved on #715 issuecomment-6407266343). Verdicts, confirmed against the code:
- md5 x7: not security (ids, seeds, fingerprints, manifest checksum). `usedforsecurity=False` added; digests unchanged (pinned by tests/unit/security/test_md5_ids_are_not_for_security.py).
- propose_simulation_enhancements.py:184: `yaml.dump` of plain dicts -> `yaml.safe_dump`; output identical for this data (checked before/after).
- prepare_simulation_execution.py:174: chmod 0o755 on the generated launcher is intended -> reasoned nosemgrep.
- watchdog.py request-with-http x2 (BACKEND_URL, LOKI_URL): from env, internal compose network -> reasoned nosemgrep.
- lab/context.py:93 request-data-write and generate_simulation_setup.py:489 directly-returned-format-string: FALSE POSITIVES. `request` is the lab's local pydantic WorkflowRequest; the writes go to fixed names under get_stage_dir(), session_id validated (^[a-zA-Z0-9_-]+$) and resolved inside the sandbox by resolve_session_dir; the returned string is a markdown file body, not a web response. Reasoned nosemgrep (planner GO).
- wildcard-cors: see the CORS commit (in scope since #731 landed).
Suppressed in code only; nothing dismissed in the Security tab (#701/#729 convention). No local semgrep binary: whether each nosemgrep silences its alert is confirmed only by the next security-scan run on main.

## Test Summary

## Files Changed

## Completion Summary
