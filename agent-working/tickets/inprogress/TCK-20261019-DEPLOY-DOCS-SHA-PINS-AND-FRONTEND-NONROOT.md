---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261019-DEPLOY-DOCS-SHA-PINS-AND-FRONTEND-NONROOT
phase: open
date: 2026-10-19
tags: [platform, delivery, security]
---

# TCK-20261019-DEPLOY-DOCS-SHA-PINS-AND-FRONTEND-NONROOT

## Title
Platform's two Semgrep baseline findings: pin deploy-docs.yml's actions by commit SHA, run the frontend image as non-root; record the repo-wide pin rule

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
The first main run of `security-scan.yml` (#665, run 39233931697) reported two platform-owned findings:
`github-actions-mutable-action-tag` ×5 in `.github/workflows/deploy-docs.yml` (lines 35, 40, 57, 60, 66) and
`dockerfile.security.missing-user` at `docker/frontend.Dockerfile:26`.

**Owner decisions (2026-10-19):**
- Pin rule, relayed by lead-planner-u24: every workflow pins actions by full commit SHA with a `# vX.Y.Z` comment,
  GitHub-owned actions included, kept current by Dependabot github-actions (grouped, monthly). Each owner converts its
  own files; the rule is recorded as one line in an existing doc.
- In the platform-planner-u24 terminal: #609 closed (done). The pins take the newest majors directly. Then file and
  dispatch this ticket.

## Scope
1. **`.github/workflows/deploy-docs.yml`**: replace each `uses:` tag with a full 40-hex commit SHA plus a
   `# vX.Y.Z` comment. Target the newest release of each major:
   - `actions/checkout`: reuse `3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1` (as in security-scan.yml/iac.yml);
   - `actions/setup-node`: v7 (latest v7.x);
   - `actions/configure-pages`: **v6** (was v4; #609's bump);
   - `actions/upload-pages-artifact`: v5 (latest v5.x);
   - `actions/deploy-pages`: **v5** (was v4; #609's bump).
   Resolve each SHA from the release tag with `gh api repos/<owner>/<repo>/git/ref/tags/<tag>`, dereferencing an
   annotated tag to its commit. Record the tag→SHA table in Implementation Notes. Check the v6/v5 release notes for
   input changes, and change nothing else in the workflow.
2. **`docker/frontend.Dockerfile`, runtime stage**: switch to `nginxinc/nginx-unprivileged` at the same nginx/alpine
   line as today (`1.31.6-alpine3.24`, or the closest tag that exists), pinned by digest like the current base. Add an
   explicit `USER` (the image's non-root uid, 101) after the COPY lines, and `EXPOSE 8080`. The build stage is
   unchanged.
3. **`docker/nginx.conf`**: `listen 80;` → `listen 8080;`. Nothing else.
4. **`compose.yaml`, `frontend` service only**: `ports: "${FRONTEND_PORT:-8080}:8080"` (the host port is unchanged)
   and the healthcheck URL becomes `http://127.0.0.1:8080/`. Pre-announced on #618 (issuecomment-6264713484). Re-read
   #618 before editing; if ubuntu replied that something reaches frontend:80, stop and tell platform-planner-u24.
5. **`docs/guides/delivery_process.md`**: one line recording the rule (owner, 2026-10-19), placed where CI conventions
   are described. This path is unregistered; lead-planner-u24 suggested this doc.

6. **Scope addition A (owner, 2026-10-19; relayed by platform-planner-u24)**: `.github/workflows/security-scan.yml` strips in-source-suppressed results
   (`suppressions[].kind == "inSource"`) from the copy of the SARIF uploaded to code scanning (`semgrep-upload.sarif`); the full `semgrep.sarif` stays the artifact;
   the summary counts unsuppressed findings and adds a "Suppressed in source: N" line. Root cause: PR #667 run 39234929819 (Semgrep writes `# nosemgrep` results
   into its SARIF and code scanning alerts on them anyway).
7. **Scope addition B**: one more line in `docs/guides/delivery_process.md` next to the pin rule: the Semgrep OSS and code-health check runs are advisory (failure
   threshold None, set by the owner, not by this ticket), and the suppression convention is `# nosemgrep: <rule id>` plus a reason, never a Security-tab dismissal.

## Out of Scope
- Pinning any other workflow (test.yml, slow-regression*, rpg-gate-report.yml: testing's; pr-body-lint.yml:
  agent-working's).
- publish-images.yml, iac.yml and security-scan.yml (already SHA-pinned).
- Any other compose service, `docker/prometheus.yml` and the Grafana files (ubuntu step 2/3's).
- Running deploy-docs end to end (Pages is disabled; the workflow is dispatch-only).

## Acceptance Criteria
- Every `uses:` in deploy-docs.yml is `owner/repo@<40-hex> # vX.Y.Z`, and configure-pages / deploy-pages are on
  v6 / v5. YAML parses; `actionlint` is clean if available.
- Locally ("running locally"):
  - `docker compose build frontend` succeeds;
  - `docker compose up -d frontend` (with its backend dependency) reaches `healthy`;
  - `docker compose exec frontend id -u` is not 0;
  - `curl -fsS http://127.0.0.1:${FRONTEND_PORT:-8080}/` serves the SPA;
  - `/api/` proxies to the backend (one 2xx call).
- The PR's own `security-scan.yml` Semgrep run reports **no** finding in deploy-docs.yml or frontend.Dockerfile.
  Read it from the run's SARIF artifact, not the total.
- `publish-images.yml` on the PR builds the frontend image (path match), and Trivy reports as before.
- `tests/static` passes. Only the frontend service changes in the compose diff.

## Related Tickets
`TCK-20261019-SECRET-STATIC-SCAN-WORKFLOW` (the scan, #665), `TCK-20261014-IMAGE-SBOM-SCAN-SIGN`, #609 (closed;
superseded by these pins), #632 (deploy-docs Node 24), testing's pin ticket (to come), agent-working's pr-body-lint pin.

## Related Docs
`docs/guides/delivery_process.md`, `docs/architecture/devops_baseline_adr.md` (D3, D7), GitHub issue #618.

## Related Stored Artifacts
`agent-working/stored_artifacts/TCK-20261019-SECRET-STATIC-SCAN-WORKFLOW/`

## Related Code Areas
`.github/workflows/deploy-docs.yml`, `docker/frontend.Dockerfile`, `docker/nginx.conf`, `compose.yaml` (frontend
service), `docs/guides/delivery_process.md`

## Assumptions / Open Questions
- **Disk is low (about 6.8 GB free).** Run `python3 tools/sessions/disk_headroom.py` before building. Remove only the
  images and containers this ticket builds. Never `compose down -v`, and never prune shared images without the user.
- If `nginxinc/nginx-unprivileged` has no tag at the current nginx/alpine line, take the nearest newer patch and
  record it.
- Dependabot's docker ecosystem picks up the new base image name. Check that `.github/dependabot.yml` doesn't ignore
  it by name.

## Implementation Notes
Pins (tag -> commit, deploy-docs.yml): checkout v7.0.1 `3d3c42e5aac5ba805825da76410c181273ba90b1`; setup-node v7.1.0 `949feb2413d6458794dcd2491c4babbbce0c15c1`;
configure-pages v6.0.0 `45bfe0192ca1faeb007ade9deae92b16b8254a0d`; upload-pages-artifact v5.0.0 `fc324d3547104276b827a68afc52ff2a11cc49c9`;
deploy-pages v5.0.1 `368f82528645a54fb793d4d04e342629a3f51346`. Release notes of configure-pages v6 and deploy-pages v5: Node 24 upgrade, no input changes; upload-pages-artifact v5
adds an optional `include-hidden-files` input (unused). Frontend base: `nginxinc/nginx-unprivileged:1.31.6-alpine3.24@sha256:884e0b7f42f303641b0f4e78755aea647521dca0b89ca3be7992ad78b5c07434`.
Local compose test used a scratch `./data` override because `data/runs` in this worktree is root-owned by an older container (environmental, untouched).
Every `/api` route needs an API key, so the proxy check compared the backend's 401 body through the frontend with the direct call (identical).
Addition A tested on #667's artifact: 89 results -> 87 uploaded; the two inSource `use-defused-xml-parse` results dropped and the other 4 stayed.
Repo settings (code scanning check-run failure threshold) are the owner's to set; not changed here.

## Test Summary
(filled by the implementer)

## Files Changed
(filled by the implementer)

## Completion Summary
(filled by the implementer)
