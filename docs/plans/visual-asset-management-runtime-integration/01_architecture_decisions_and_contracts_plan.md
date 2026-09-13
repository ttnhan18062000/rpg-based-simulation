---
status: active
layer: architecture
authority: P1
audience: agent
date: 2026-09-10
tags: [assets, architecture, contracts, deployment, planning]
---

# AM-M1 — Architecture Decisions and Contracts

## Outcome

Resolve `ASSET-0` from accepted M0 evidence: select exactly one deployment profile, define the minimum four
logical contracts, establish compatibility/fallback/provenance/authorization boundaries, and produce the
charters required for synthetic validation. M1 decides architecture for planning; it implements nothing.

## Repository evidence and assumptions

M1 may use only M0 `PASS` evidence and must distinguish current implementation, approved P1 planning, and
proposal decisions. Current Vite use makes Profile A the smaller candidate, not an automatic selection.
Unknown hosting, clients, roles, or policy remain blockers rather than assumed requirements.

## Prerequisites and dependencies

- M0 `PASS` and human acceptance of its evidence as M1 input.
- Accountable architecture, frontend/release, Live Map, HUD, accessibility, security, art-adoption,
  provenance/license, and rollback roles are named or explicitly block the affected decision.
- Numeric budgets may remain downstream only when M1 defines their owner and blocking gate.
- No dependency on CAP-A/CAP-B or real art.

## Deliverables and acceptance criteria

| ID | Deliverable | Objective acceptance |
|---|---|---|
| `AM1-W01` | Deployment-profile ADR | Selects Profile A or B from repository needs; rejects speculative dual implementation; records reversal trigger |
| `AM1-W02` | Semantic registry contract | Finite key namespace, derivation owner, normalization, bounds, unknown behavior, family model and safety-class link |
| `AM1-W03` | Surface descriptor contract | Deterministic variant axes/precedence, limits, fallback depth/cycles, Live Map/HUD ownership and compatibility ranges |
| `AM1-W04` | Runtime release contract | Minimal shipped fields, exact-byte/canonical-hash decision, strict parser, trusted locators, bounds and required fallbacks |
| `AM1-W05` | Protected audit/provenance contract | Adoption/activation identities, source/build lineage, license, approver/audit separation and retention references |
| `AM1-W06` | Fallback-safety framework | Safety classes define preserved information, allowed primitive/text/HUD alternatives and activation/runtime failure policy |
| `AM1-W07` | Compatibility/rollback contract | Client, schema, renderer, capability and fallback ranges plus profile-specific rollback and retirement rules |
| `AM1-W08` | Trust/authority model | Integrity, authenticity, authorization, freshness, roles, rotation/recovery and minimum channel/signature decision |
| `AM1-W09` | Build/provenance boundary | Allowlisted build, validation/publication separation and required repeatability/provenance level |
| `AM1-W10` | Retention/GC contract | Reachability roots, leases/pins, grace, locks, dry run, deletion audit and storage-pressure disposition |
| `AM1-W11` | M2 evidence charter | Synthetic fixtures, supported conditions, exact gate setup, retained evidence and allowed conclusions predeclared |
| `AM1-W12` | Candidate handoff/intake contract | Asset-owned versioned `CandidateHandoffPackage`, bounded quarantine copy, producer-neutral validation and explicit non-adoption/publication/activation semantics |
| `AM1-W13` | Rights/provenance recall contract | Named post-activation authority, release/build eligibility revocation, distribution stop, stale/offline/cache handling, audit retention and tested rollback |

## Applicable gates

M1 may close `AM-C01` only when one smallest deployment profile is selected and all material unresolved
profile prerequisites are either resolved or explicitly block implementation. It defines, but does not pass,
`AM-C02`–`AM-C10`. It passes no CAP gate.

## Retained evidence

Approved M0 dossier; ADRs with options/trade-offs/reversal triggers; versioned contract drafts; role and
authority matrix; threat model; contradiction dispositions; updated UNVERIFIED register; M2 charter.

## Security and recovery

No contract may accept server/caller paths or URLs, unbounded runtime keys, direct build-to-activation
authority, or asset-driven simulation mutation. Manual and CAP-A producers enter the same quarantine and
validation boundary; neither can assert adoption. Profile B requires a client bootstrap design; Profile A
requires complete frontend-release rollback. Rights/provenance recall must fail closed for new distribution
and fence late/stale cache work without destroying required legal/audit evidence. Withdraw unaccepted ADRs
and retain M0 facts; no runtime state or repository asset needs rollback.

## Explicit non-goals

- Schema implementation, synthetic harness execution, build, deployment, or profile pilot.
- Selecting asset content, art style, renderer, atlas, or physical folder layout without evidence.
- Designing CAP-A or CAP-B again.
- Treating M1 `PASS` as implementation authorization.

## Authorization required to start

A separate human planning decision must accept M0 as complete and authorize M1 architecture drafting. Any
prototype, command execution beyond read-only checks, dependency change, or external service access requires
another scope.

## Result classification

| Result | M1 condition |
|---|---|
| `PASS` | `AM-C01` passes, one profile and minimum contracts are coherent, owners/charter exist, and no implementation authority is implied |
| `FAIL` | A valid decision violates authority, requires both profiles without evidence, or conflicts with Live Map/HUD/CAP owners |
| `BLOCKED` | M0 did not pass or a required profile/authority/security owner decision is absent |
| `INCONCLUSIVE` | Evidence cannot distinguish profiles or a material contract choice lacks sufficient repository support |

## Rollback, abandonment, and stop conditions

Supersede unaccepted ADRs, retain evidence, and keep current Canvas/Vite behavior unchanged. Stop if profile
selection relies on imagined deployment needs, the minimum contract cannot preserve critical information,
or ownership conflicts remain unresolved. M2 execution cannot start without M1 `PASS` and new authority.

## Decisions remaining unfrozen

All art decisions, renderer, final schema syntax/technology, numeric budgets, physical paths, asset format,
packing, storage implementation, and any optional Profile-B machinery not selected.

## Ticket-ready slices after later approval

Profile ADR; semantic/descriptor contracts; runtime/audit split; fallback/compatibility; trust/build boundary;
retention/GC; M2 charter review. Do not combine contract decisions with harness implementation.
