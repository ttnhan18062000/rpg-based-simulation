---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261019-SEMGREP-BASELINE-FINDINGS-IN-SRC-TRIAGE
phase: done
date: 2026-10-19
tags: []
---

# TCK-20261019-SEMGREP-BASELINE-FINDINGS-IN-SRC-TRIAGE

## Title
Triage the baseline Semgrep findings in src/** from the new security-scan workflow (#665): fix the real ones, mark the false positives in code

## Status
DONE

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
- wildcard-cors (#228, src/api/server.py): REAL, in scope since the server.py split (#731) landed. `allow_origins` now comes from `src/api/cors.py::cors_origins_from_env()` (env BACKEND_CORS_ORIGINS, same helper style as metrics_port.py), default the local dev origins (Vite dev 5173, `vite preview` 4173 per frontend/package.json, compose frontend 8080, both loopback names). Credentials stay off; methods and headers stay `*` (the rule flags the origin only; no local semgrep to confirm, so the next scan on main decides). Frontend checked: it calls the relative `/api/v1` (Vite proxy in dev, docker/nginx.conf in compose), so it is same-origin and unaffected.
  DELIBERATE EXCEPTION to "a later change leaves ticket 1's characterization fixture unchanged": `tests/fixtures/api_server_http_surface.json` changes in three places, all the one intended CORS change: the `cors_preflight` entry (status 200 -> 400, `access-control-allow-origin: *` gone for Origin https://example.test) and the two recorded CORS middleware `allow_origins` options (default_profile, optional_routers_on). The rest of the fixture is byte-identical. `tests/api/test_cors_config.py` pinned `*` too and now pins the dev origin echo plus "no credentials header". New: tests/api/test_cors_origins.py (default, comma list, empty/whitespace/wildcard-only, preflight from a dev origin, from a configured origin, refusal of an unlisted one). Documented in docs/architecture/http_api_key_authentication.md (the API's runtime-config doc; feature_flags.md is flag-only).
Suppressed in code only; nothing dismissed in the Security tab (#701/#729 convention). No local semgrep binary: whether each nosemgrep silences its alert is confirmed only by the next security-scan run on main.
  Why a non-default FRONTEND_PORT (or any port not in the list) still works: the frontend's own traffic is same-origin (relative `/api/v1`; the Vite proxy, `vite preview` which per Vite's docs inherits `server.proxy` (read, not run here), and docker/nginx.conf's `proxy_pass` in compose), and a browser sends no CORS preflight for a same-origin request. Read in Starlette's CORSMiddleware.__call__: the preflight branch is taken only for OPTIONS with an Origin and Access-Control-Request-Method (a cross-origin browser request); any other request, including a same-origin POST that carries an Origin header, goes to simple_response, which only omits the allow-origin header for an unlisted origin and never rejects. So the default list matters only for a page served from a genuinely different origin; an unlisted cross-origin preflight gets 400 (pinned in test_cors_origins).
  Review notes for the PR body: (a) docs/architecture/http_api_key_authentication.md is lead-planner's path (ubuntu, off); lead-planner-u24 said keeping the CORS section there is fine but it is not a sign-off; it moves to docs/observability/how_to_run_simulation.md if architecture objects. (b) tests/fixtures/api_server_http_surface.json changes in three places (cors_preflight 200->400 plus the two recorded CORS middleware allow_origins lists), the deliberate exception to "a later change leaves ticket 1's fixture unchanged".

## Test Summary
- 140 passed on the touched modules (lab, replay, security, API CORS and HTTP-surface characterization, watchdog, world_emergence, genetics, warehouse); the CORS tests also pass with BACKEND_CORS_ORIGINS set in the shell.
- Determinism proof: `tools/rpg_measure/paired.py --neutral --jobs 1` (scratch cache), base cb4f95015177 (merge-base with origin/main) vs new f0f0e81a1d00, seed 42, 3 worlds: frontier_living_world d81e5b8b4b9ad077, urban_political dfb3f9d6f24dd0b5, crowded_frontier 4570a46c6c1ec186 - all IDENTICAL, NEUTRAL PASS. Run data cleaned by id.
- Not verifiable locally: whether each nosemgrep silences its alert (no semgrep binary); the next security-scan run on main decides.

## Files Changed
src/api/cors.py (new), src/api/server.py, src/domains/world_emergence/services.py, src/lab/context.py, src/lab/mutation.py, src/lab/workflows/{generate_simulation_setup,prepare_simulation_execution,propose_simulation_enhancements}.py, src/observability/warehouse/clickhouse.py, src/observability/watchdog.py, src/replay/fingerprint.py, src/systems/lifecycle_systems/genetics.py, docs/architecture/http_api_key_authentication.md, tests/api/{test_cors_config,test_cors_origins}.py, tests/api/test_server_http_surface_characterization.py, tests/fixtures/api_server_http_surface.json, tests/unit/security/test_md5_ids_are_not_for_security.py.

## Completion Summary
All baseline src/** Semgrep findings triaged: md5 x7 flagged non-security, yaml.dump -> safe_dump, reasoned nosemgrep on the intended/false-positive sites, wildcard CORS replaced by an env-configurable local-origin list. Simulation hashes unchanged (paired neutral IDENTICAL on 3 worlds). Nothing dismissed in the Security tab.
