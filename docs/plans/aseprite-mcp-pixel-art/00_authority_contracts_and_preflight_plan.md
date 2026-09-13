---
status: active
layer: architecture
authority: P1
audience: agent
date: 2026-09-10
tags: [architecture, aseprite, mcp, security, planning]
---

# Milestone 00 — Authority, Contracts, and Preflight

## Outcome

Resolve whether a bounded supervised drawing experiment can be safely scoped and choose what, if anything,
should be proposed for implementation. M0 produces reviewed contracts and an option disposition. It installs,
registers, builds, and executes nothing and does not change NO-GO.

## Prerequisites

- Human accepts this package as a planning input only.
- Proposal commit/revision and all source candidates are pinned for review.
- Security, art-review, dependency, renderer, and evidence owner roles are named or marked `UNVERIFIED`.

## Deliverables

| ID | Deliverable | Objective acceptance |
|---|---|---|
| `M0-W01` | Authority and data-flow map | Aseprite, adapter, orchestrator, evidence, browser harness, repository, and human boundaries are explicit; no path mutates simulation state |
| `M0-W02` | Option comparison | Project-owned stdio adapter, reduced pinned fork, and non-MCP script compared under identical safety, effort, latency, readback, and maintenance criteria |
| `M0-W03` | Source/dependency dossier | Exact candidate commits, transitive dependencies, licenses, tool registrations, network/update behavior, and test types classified |
| `M0-W04` | Host/confinement decision record | One proposed OS/filesystem/process boundary with denied paths, network, credentials, repository, production assets, and cleanup behavior |
| `M0-W05` | Minimal schemas | Session identity, immutable revision, bounded operation batch, result, error, manifest, and capability descriptors drafted with limits |
| `M0-W06` | Evidence charter template | Question, control, fixture hash, platform, thresholds, raw evidence, status rules, reviewer, allowed conclusion, rollback, and retention fields |
| `M0-W07` | Dependency-change route | Exact files and validation needed for Python/MCP or frontend changes; mismatch between pinned requirements and broad optional extra resolved in plan |
| `M0-W08` | UNVERIFIED resolution report | Every `U-01`–`U-14` item is resolved, scoped downstream, or named as a blocker without invented values |

## Non-goals

- Choosing an art style, palette, resolution, roster, Place representation, animation scope, or production pipeline.
- Installing Aseprite or dependencies, running candidate code, registering MCP, or drawing an asset.
- Assuming MCP is preferable to a narrower script.
- Designing adaptive ranking, embeddings, or external scoring.

## Authorization boundary

Allowed now: repository/source/document reading and writing this plan package. Future source fetching,
package installation, binary inspection, builds, or execution require separate explicit authorization and a
scoped ticket. Human review of M0 authorizes at most the next ticket investigation, not M1 execution.

## Covered capability gates

M0 passes no `CAP-A` or `CAP-B` gate. It defines prerequisites and falsifiable charters for `CAP-A01`–
`CAP-A08`, `CAP-A10`, `CAP-A11` **(2026-09-13, added by review — authorization boundary and probing)**,
and B0. Any claim that a paper review proves those gates is invalid.

## Required evidence and security checks

- Final exposed tool manifest and reachability trace, not README promises.
- Path flow from request through staging, open/save/export, publication, and cleanup.
- Proof plan for symlink, hard-link, reparse/junction, case/Unicode collision, TOCTOU, overwrite, timeout,
  crash, disk-full, malformed input, oversized input/output, and concurrent request cases.
- Classification of unit, mocked, skipped-editor, and real-Aseprite tests.
- Exact OS sandbox and network-denial assumptions; unsupported platforms remain `UNVERIFIED`.
- Dependency/license/provenance review and reproducible acquisition plan without performing acquisition.
- Confirmation that adapter and evidence paths cannot reach authoritative simulation state or production art.

## Objective exit criteria

M0 is `PASS` only when one minimal option is recommended or all are rejected; every mandatory contract,
owner, platform assumption, dependency route, evidence rule, and negative-test plan is reviewable; and a
human records the bounded disposition. Missing host, licensing, confinement, or rollback facts are
`BLOCKED`, not assumptions. Equal candidates or insufficient evidence are `INCONCLUSIVE`.

## Dependencies and sequencing

M0 precedes any M1 execution. Its renderer-facing contract coordinates with the existing Live Map/Surface
package. Evidence schema work may inform B0, but raw Aseprite operations and adaptive memory remain separate.

## Rollback path

Withdraw the unaccepted decision record, retain review evidence, and leave the repository, dependency
manifests, MCP configuration, machine, Canvas renderer, and production assets unchanged.

## Stop conditions

Stop if no candidate can remove arbitrary code from the reachable surface, binary/license provenance is
unacceptable, confinement cannot deny repository/credential/network access, immutable publication cannot
be designed for the selected filesystem, or MCP adds no justified value over the script baseline.

## Ticket-ready slices after human approval

Candidate source audit; dependency/license review; schema/limit design; confinement spike design; option
comparison; evidence-charter review. Do not combine these with installation or a drawing pilot.
