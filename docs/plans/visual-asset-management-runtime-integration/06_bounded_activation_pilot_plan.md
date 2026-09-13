---
status: active
layer: architecture
authority: P1
audience: agent
date: 2026-09-10
tags: [assets, activation, pilot, rollback, planning]
---

# AM-M6 — Bounded Activation Pilot

## Outcome

Define a dormant `ASSET-4` plan for one later, human-selected, noncritical semantic visual role. The plan
tests a bounded normal-path activation with compatibility fencing, monitoring and immediate rollback. It is
not authorization to choose the role, adopt art, build a release, deploy, or activate anything.

## Repository evidence and assumptions

Deployment topology, supported production clients, release authority, monitoring path and normal frontend
activation mechanism were `UNVERIFIED` at drafting time. M1 must select exactly one deployment profile and
later investigation must revalidate all operational facts. Current primitive rendering is the rollback
control unless separately retired after evidence.

## Prerequisites and dependencies

- M1, M2, M4 and M5 `PASS` (with M0 inherited through M1); complete valid evidence for
  `AM-C01`–`AM-C09` at the intended client/environment scope. M3 remains independent and optional.
- One exact noncritical role, source and artifact separately reviewed and adopted under named human authority.
- Selected profile's compatible client/release matrix, cache-generation policy and snapshot protocol.
- Tested per-role fallback, previous compatible release, rollback authority, monitoring and stop thresholds.
- Tested post-activation rights/provenance recall authority and procedure covering current, stale, offline,
  service-worker/CDN-cached and late-completion cases without erasing required audit/legal evidence.
- A new explicit authorization covering build, publication/deployment and bounded activation; none exists now.
- CAP-A and CAP-B are not prerequisites.

## Deliverables and acceptance criteria

| ID | Deliverable | Objective acceptance |
|---|---|---|
| `AM6-W01` | Pilot charter | Names one noncritical role, clients, environment, exposure, duration, owners, forbidden scope and predeclared thresholds |
| `AM6-W02` | Reviewed release candidate | Immutable release/manifest/artifact hashes, provenance, compatibility and authorization records are complete |
| `AM6-W03` | Activation mechanism | Selected profile exposes one human-controlled, authenticated, auditable transition with no caller-selected locator |
| `AM6-W04` | Cache/generation fence | Old, late, offline and stale-client cases cannot mix incompatible releases or overwrite current state |
| `AM6-W05` | Fault and rollback drill | Corrupt/missing/slow/incompatible cases fall back safely and restore the last compatible release within the approved objective |
| `AM6-W06` | Monitoring record | Bounded semantic failures, performance, accessibility and fallback signals are attributable without sensitive/unbounded labels |
| `AM6-W07` | Pilot disposition | Human owner records retain, rollback or abandon; no automatic expansion follows `PASS` |
| `AM6-W08` | Authoritative-state proof | Activation affects presentation only and cannot create a `StateUpdate` or bypass the 39-phase mutation pipeline |
| `AM6-W09` | Rights/provenance recall drill | A newly ineligible source/artifact/release stops further distribution and activation, current and stale clients reach a safe fallback/compatible release, late work is fenced, and required audit/legal evidence is retained |

## Applicable gates

M6 targets `AM-C10` and requires fresh validity of `AM-C01`–`AM-C09`. Any changed contract, release,
client, fallback or environment reruns its affected earlier gate. Passage authorizes no M7 family.

## Retained evidence

Signed/approved charter; adoption and authorization records; release/manifest/artifact hashes; supported
client and compatibility matrices; build/validation attestations; activation audit; cache/fault/rollback
results; bounded monitoring extracts; native-scale/accessibility captures; final human disposition.
The bundle also retains the recall trigger, authority, affected identities, current/stale/offline-client
results, cache/CDN/service-worker invalidation evidence, late-completion fencing and legal-hold disposition.

## Security and recovery

Separate build, publish and activate roles; least-privilege credentials; authenticated immutable releases;
allowlisted locators; origin/root, integrity, freshness and compatibility validation; bounded decode/cache/log
behavior; no secrets in artifacts. Recovery chooses the prevalidated compatible release or role-safe
primitive fallback. An incompatible or recalled manifest is rejected rather than partially rendered.
Rights/provenance recall stops new distribution and activation immediately; inaccessible offline clients
remain explicitly unresolved until they reconnect and prove safe reconciliation.

## Explicit non-goals

- Selecting the pilot role now, creating/adopting art, or executing `ASSET-4`.
- Broad asset rollout, renderer migration, HUD redesign or primitive retirement.
- Dynamic runtime IDs, user/mod uploads, hot reload, CAP-B or autonomous activation.
- Treating pilot passage as permission for incremental migration.

## Authorization required to start

`NO-GO`. Requires a future explicit human authorization naming role, release, profile, environment, client
scope, duration, activation and rollback owners, credentials, thresholds and approved implementation ticket.

## Result classification

| Result | M6 condition |
|---|---|
| `PASS` | C10 and all still-applicable prior gates pass, including the rights/provenance recall drill; pilot stays bounded and human disposition accepts the evidence |
| `FAIL` | Critical information, compatibility, security, accessibility, performance, cache isolation or rollback objective fails |
| `BLOCKED` | Any prior gate, adopted candidate, profile/client fact, owner, rollback route or new authorization is absent |
| `INCONCLUSIVE` | Exposure, telemetry, client coverage, environment identity or fault evidence cannot support a safe decision |

## Rollback, abandonment, and stop conditions

Immediately activate the prevalidated compatible release or disable the role's asset route and use its safe
fallback. Preserve audit/evidence and quarantine the failed release. Stop on threshold breach, mixed
generation, unsupported client, invalid signature/hash, provenance change, inaccessible critical cue,
rights/license/authorship eligibility change, failed distribution stop, unbounded telemetry, rollback/recall
uncertainty or any scope expansion.

## Decisions remaining unfrozen

Pilot role and timing, asset content/style/resolution/palette, production renderer, deployment details beyond
M1's selected profile, broader client support, animation, migration order and all M7 authorization.
