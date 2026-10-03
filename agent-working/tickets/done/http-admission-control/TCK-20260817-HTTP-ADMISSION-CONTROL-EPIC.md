---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC
phase: done
date: 2026-08-17
tags: [architecture, observability]
---

# TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC

## Title
HTTP-layer auth, rate limiting, and admission control — gate on deployment plans

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
`src/api/server.py` registers no rate limiting, no authentication, and no per-client admission
control on any REST endpoint; `CORSMiddleware` is also configured with a spec-invalid
`allow_origins=["*"]` + `allow_credentials=True` combination. Resource governance exists and
works well elsewhere (intra-tick `WorkerManager` bulkhead, `RedisStreamAdapter`'s backpressure) —
the gap is specifically that governance stops at the HTTP process boundary. Both source audits
explicitly gate this epic's priority on actual deployment plans — do not front-load if this
system stays on a trusted network.

## Scope
Full findings, including a full mode-vocabulary design reusing the observability layer's existing
NORMAL/PRESSURE/DEGRADED/SURVIVAL states, are in `docs/plans/http_admission_control_epic.md`.

**(2026-08-19)** Deployment-plan decision confirmed by the requester: this API surface **stays on
a trusted network**, no public/untrusted exposure planned. Per this ticket's own gating criterion,
auth and admission control stay explicitly deferred — not investigated further, not scoped into
child tickets, until that decision changes. The one item that was always independent of the
deployment question — the CORS config fix — was extracted into
`TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG`.

**(2026-08-23) Deployment plan changed — this epic is now active.** The requester confirmed the
API surface will now be exposed on the **public internet, multi-tenant** (multiple distinct,
untrusted client identities, not just internal processes). This reopens the deferred scope for
real investigation and implementation:
- **Auth mechanism**: per-client API key (not a single global shared secret, and not OAuth/JWT)
  — chosen explicitly by the requester as sufficient for the current client model (a bounded,
  known-but-growing set of tenants, not third-party/end-user identity federation). Each client
  gets its own key so a single leaked/compromised key doesn't expose every tenant and individual
  keys can be revoked without rotating a shared secret.
- **Admission control**: extend the existing NORMAL/PRESSURE/DEGRADED/SURVIVAL vocabulary to the
  HTTP layer (per the original design in `docs/plans/http_admission_control_epic.md`), now with
  per-client (not just global) rate limiting, since "multi-tenant" means one noisy/compromised
  tenant must not be able to degrade service for others.

**(2026-08-23) Investigated and split into 2 child tickets — tier reverted to epic.** A full
Investigate pass (`staging_artifacts/TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC/investigation.md`,
kept as shared reference context for both children, not moved to `stored_artifacts/` since this
ticket itself does no direct implementation) found this bundles two substantially independent
subsystems with a real sequencing dependency, not just a scope-convenience grouping:
- **Auth** — per-client API-key authentication. No existing repo precedent for credential
  storage/constant-time comparison; a genuinely new subsystem, not a config tweak.
- **Admission control** — per-client HTTP rate limiting/mode-vocabulary extension. Structurally
  depends on auth landing first (needs a client identity to key per-client state on), and
  introduces new, previously-unbounded per-client state (a mode/dwell-tick dict keyed by client ID
  needs an eviction/TTL policy — a real design surface the original 2026-08-18 downgrade
  assessment didn't anticipate, since the deployment plan wasn't real at that time).

Split into `TCK-20260823-HTTP-API-KEY-AUTH` (implement first) and
`TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL` (implement second, depends on the first) — see
`tickets/todos/http-admission-control/SEQUENCE.md`. This reverses the 2026-08-18 downgrade to
standard tier, since that assessment predates the real (non-dormant) scope. This epic ticket now
tracks those 2 children only; no further direct implementation happens on this ticket itself.

## Out of Scope
- Any new message broker, service mesh, or distributed rate-limiting infrastructure.
- OAuth/JWT or any third-party identity federation — per-client API key only, per the requester's
  explicit 2026-08-23 choice.
- User-facing self-service key management UI/API (key issuance/rotation) — this ticket delivers
  the auth/admission-control mechanism itself; how keys are provisioned to real tenants
  operationally is a separate concern unless investigation finds it's trivially in-scope.

## Acceptance Criteria
- [x] CORS config item extracted — see `TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG`.
- [x] At least one auth mechanism (per-client API key) gates the API surface — implemented by
      `TCK-20260823-HTTP-API-KEY-AUTH`, which reached `tickets/done/` 2026-08-23.
- [x] HTTP requests are admitted/throttled/shed **per-client**, according to a mode vocabulary
      consistent with the observability layer's existing NORMAL/PRESSURE/DEGRADED/SURVIVAL states
      — implemented by `TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL`, which reached
      `tickets/done/` 2026-08-23.
- [x] Deployment-plan decision confirmed (2026-08-19, superseded 2026-08-23): now public internet,
      multi-tenant. This epic is active, no longer dormant.
- [x] Investigated and split into 2 child tickets (2026-08-23), per this ticket's own AC above
      requiring investigation before force-fitting a tier assessment made when scope was dormant.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)
- TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG (item 1 extracted from here, 2026-08-19)
- TCK-20260823-HTTP-API-KEY-AUTH (extracted here, 2026-08-23; implement first)
- TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL (extracted here, 2026-08-23; implement second,
  depends on TCK-20260823-HTTP-API-KEY-AUTH)

## Related Docs
- docs/plans/http_admission_control_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D23_architecture_resilience.md
- docs/architecture/observability_hot_path_safety_contract.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/api/server.py

## Assumptions / Open Questions
- **(2026-08-19) Superseded 2026-08-23:** deployment target was confirmed trusted-network-only,
  then changed to public internet, multi-tenant — see Scope.
- **(2026-08-23) Resolved:** auth mechanism is per-client API key, chosen explicitly by the
  requester over OAuth/JWT.
- **Downgraded from epic to standard tier (2026-08-18):** one of 10 sub-epics under
  `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`; the borderline case of the review — bigger than
  the other downgrades (auth is a real subsystem), but CORS+auth+admission-control-vocabulary
  still fit one standard ticket, especially since the mode vocabulary explicitly reuses an
  existing pattern rather than inventing one. Investigation should confirm this tier assessment
  still holds now that the scope is real (public multi-tenant) rather than dormant — if per-client
  key storage/validation and per-client admission control turn out to need more than one
  standard-tier ticket's worth of work, that's a legitimate finding to flag during Investigate,
  not something to force-fit.
  `staging_artifacts/TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC/` not yet created.

## Implementation Notes
Scope-only epic — no direct implementation. Its shared investigation
(`stored_artifacts/TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC/investigation.md`) served as the
context both child tickets' own Investigate phases read first rather than re-deriving. This
ticket's role was tracking, the 2026-08-23 investigate-and-split decision, and this closing
record.

## Test Summary
No direct tests for this epic ticket itself. Each of the 2 child tickets carried its own full
test suite (see each child ticket's own Test Summary in `tickets/done/`).

## Files Changed
No files changed by this epic ticket directly beyond its own body and its move from
`tickets/todos/http-admission-control/` to `tickets/done/http-admission-control/`. All
substantive files were changed by the 2 child tickets, tracked in their own individual Files
Changed sections.

## Completion Summary
Both child tickets reached `tickets/done/` 2026-08-23: `TCK-20260823-HTTP-API-KEY-AUTH`
(per-client API-key authentication, gating every route in `src/api/server.py` except `/health`)
and `TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL` (per-client admission control extending
`ObservabilityMode`'s NORMAL/PRESSURE/DEGRADED/SURVIVAL vocabulary to the HTTP layer, keyed by the
`ClientIdentity` the auth ticket resolves). The CORS item (extracted 2026-08-19) and the
deployment-plan gate (fired 2026-08-23, reopening this epic from dormant) are both resolved. All 5
Acceptance Criteria are satisfied. This epic closes.
