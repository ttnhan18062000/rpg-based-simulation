---
status: active
layer: architecture
authority: P1
audience: agent
date: 2026-09-10
tags: [architecture, aseprite, mcp, pixel-art, security, testing]
---

# Milestone 01 — Supervised Headless Drawing Capability

## Outcome

Under a later explicit authorization, demonstrate or reject the core claim that an agent can construct,
observe, correct, and preserve small editable pixel-art candidates through a bounded headless interface.
M1 is complete without adaptive memory. A non-MCP interface may be the winning implementation.

## Prerequisites

- M0 `PASS` with a selected option, exact host, confinement, limits, schemas, and evidence charter.
- Separate authorization for every required install, build, registration, Aseprite execution, and artifact root.
- Exact source/dependency/binary/license manifest and offline availability.
- Disposable OS-confined workspace, rollback owner, and real-Aseprite test access.

## Deliverables

| ID | Deliverable | Objective acceptance |
|---|---|---|
| `M1-W01` | Isolated control surface | Only allowlisted typed tools/commands and fixed hash-verified templates are reachable |
| `M1-W02` | Immutable revision engine | Expected input hash, same-filesystem staging, reopen validation, collision-safe publication, and no-clobber behavior pass |
| `M1-W03` | Structured document operations | Bounded pixels, primitives, layers, palettes, frames, cels, timing, tags, inspection, previews, and exports match schema |
| `M1-W04` | Agent observation/correction loop | Agent locates a seeded defect from bounded readback/preview and publishes only the intended correction |
| `M1-W05` | Candidate variation and group workflow | Controlled variants and small multi-asset groups preserve identity, parentage, unchanged variables, and failure isolation |
| `M1-W06` | Real-editor negative suite | Crash, timeout, malformed/oversized input, disk failure, stale hash, concurrency, path attacks, and publication collision classified |
| `M1-W07` | Performance result | Cold/repeated startup, mutation, validation, preview, and end-to-end latency meet preregistered experimental budgets |
| `M1-W08` | Capability disposition | `CAP-A01`–`CAP-A08` and `CAP-A11` **(2026-09-13, added by review)** each has raw evidence and PASS/FAIL/BLOCKED/INCONCLUSIVE status |
| `M1-W09` | Optional static-first animation trial | Only after core static pass, exercise 2–4-frame anchoring/timing for `CAP-A10`; failure cannot invalidate static capability |

## Non-goals

- Adaptive feedback, case retrieval, rule promotion, or `CAP-B` passage.
- Native gameplay conclusions; those require M2 and `CAP-A09`.
- Live-editor control. It remains a separate future proposal unless headless evidence reveals a named need.
- Production assets, automatic production promotion, final art decisions, or repository asset imports.
- Direct same-file mutation, raw Lua/Python/shell, remote downloads, or broad filesystem access.

## Authorization boundary

Each mutation batch requires an approved brief/revision request and can produce one new immutable candidate.
The agent chooses bounded pixel coordinates, colors, document operations, and corrections; the adapter only
validates and executes typed data. A human remains the authority for visual acceptance and every next batch.
Passing this plan authorizes evidence review only.

## Covered capability gates

- Mandatory: `CAP-A01` control surface, `A02` deterministic construction, `A03` editable preservation,
  `A04` observation, `A05` correction, `A06` variation, `A07` multi-asset collaboration, `A08` safety,
  recovery, and latency, `A11` **(2026-09-13, added by review)** authorization boundary and probing.
- Optional after static pass: `CAP-A10` animation control.
- Explicitly not covered: `CAP-A09` native display and every `CAP-B` gate.

## Required evidence

- Exact environment, OS/filesystem, source/binary/dependency hashes, tool manifest, template hashes, and limits.
- Immutable input/output `.aseprite` revisions, SHA-256 identities, operation manifests, full structural and
  pixel validation, bounded previews, and redacted operational logs.
- Repeat runs of known 16×16 constructions and seeded-defect corrections.
- `ART-W01`–`ART-W03`-shaped synthetic or approved experimental fixtures; exact art judgments remain human.
- Failure artifacts that prove previous revisions and unrelated group members remain unchanged.
- Median and worst observed latency with all validation and confinement enabled.

## Security checks

- Final manifest contains no caller-supplied code, shell, URLs, asset downloads, plugins, or undeclared tools.
- Adapter cannot read repository, production assets, credentials, SSH agent, arbitrary home paths, or network.
- Canonicalization and open/publish paths withstand traversal, links, case/Unicode aliases, TOCTOU, and collision.
- Size, dimensions, operations, frames/layers/cels, duration, preview, output, time, and concurrency limits fail closed.
- Errors/logs are bounded and redact paths, environment data, credentials, file contents, and control characters.
- Real Aseprite reopen validation is distinguished from mocks and skipped tests.
- **(2026-09-13, added by review)** Unauthorized and nonexistent workspace/tool/session targets produce
  observationally equivalent responses (same category, message shape, and timing); no operation commits
  after mid-session authorization revocation or a forced process restart.

## Objective exit criteria

M1 `PASS` requires `CAP-A01`–`CAP-A08` and `CAP-A11` **(2026-09-13, added by review)** all pass under the
same approved environment. Drawing quality cannot compensate for a safety, recovery, or authorization-
boundary failure. `CAP-A10` is reported separately. A file-producing tool that fails observation,
correction, variation, or collaboration is classified as a scripted editor, not a supervised drawing
capability.

## Dependencies

M1 depends on M0 only. It does not depend on M2 or any B milestone. M1 may supply sanitized candidates to
M2 and complete case evidence to B0 after their independent controls pass.

## Rollback path

Stop processes; unregister only the scoped experimental configuration; revoke access; preserve approved
evidence; remove/quarantine disposable candidate dependencies and workspaces through the approved cleanup
procedure; verify repository, production assets, and prior revisions are unchanged. Canvas is unaffected.

## Stop conditions

Stop on any `CAP-A08` or `CAP-A11` **(2026-09-13, added by review)** failure; unexpected
code/tool/path/network reachability; inability to reopen and fully validate outputs; source overwrite;
ambiguous session/document targeting; unsafe latency workaround; or loss of real-Aseprite evidence. Do not
proceed to live mode or CAP-B as compensation.

## Ticket-ready slices after authorization

Isolation harness; schema validator; immutable revisions; document operations; readback/preview; correction
loop; variation/group lifecycle; negative/security suite; performance charter; optional animation proof.
