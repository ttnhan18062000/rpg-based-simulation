---
status: active
layer: architecture
authority: P1
audience: agent
date: 2026-09-10
tags: [assets, aseprite, cap-a, coordination, planning]
---

# AM-M3 — Experimental Drawing Capability Coordination

## Outcome

Connect this package to the already planned supervised Aseprite `CAP-A` branch without redefining it or
making it a production prerequisite. This milestone produces a contract crosswalk only. It does not run
Aseprite, install or register an MCP server, create art, or grant asset-adoption authority.

## Repository evidence and assumptions

The repository has a separate
[Aseprite MCP pixel-art plan package](../aseprite-mcp-pixel-art/README.md), including discovery,
supervised headless drawing, display-harness support, evidence, recovery, and capability gates. No working
Aseprite/MCP integration is assumed. Its proposal remains `NO-GO`, and its facts must be reverified by its
own M0 before execution.

## Prerequisites and dependencies

- Planning may begin from the accepted CAP-A package; execution remains subject to its own prerequisites.
- CAP-A is independent of AM-M0–M2 and AM-M4–M7 and must remain deliverable without CAP-B.
- AM-M4 may accept a disposable manual or synthetic candidate and therefore never requires CAP-A.
- Any future CAP-A output offered to AM-M4 must cross a human-controlled, immutable handoff boundary.

## Deliverables and acceptance criteria

| ID | Deliverable | Objective acceptance |
|---|---|---|
| `AM3-W01` | Authority crosswalk | Every CAP-A gate and owning plan is linked; no gate is redefined or weakened |
| `AM3-W02` | Candidate handoff envelope | Names immutable source/artifact hashes, tool/script/config versions, provenance, license, review status and evidence location |
| `AM3-W03` | State-boundary map | Experimental output, disposable candidate, adopted source and active release are explicitly distinct states |
| `AM3-W04` | Independence proof | CAP-A can stop without blocking M0–M2; M4 can rehearse without CAP-A; CAP-B failure cannot invalidate CAP-A |
| `AM3-W05` | Authorization matrix | Drawing, acceptance, adoption, build, publication and activation are separate human authorities |
| `AM3-W06` | Contradiction review | Crosswalk has no conflict with Live Map/HUD, manual experiment or existing Aseprite plans |

## Applicable gates

Execution and evidence are governed only by the existing `CAP-A01`–`CAP-A10` gates and their milestone
owners. M3 passes no `AM-C*` gate and no CAP gate. A passing coordination review is not evidence that
agent-controlled drawing works.

## Retained evidence

Crosswalk revision, reviewed handoff schema, dependency/authority matrix, source links, reviewer findings,
and unresolved `UNVERIFIED` items. Actual drawing evidence stays with the CAP-A package.

## Security and recovery

The handoff allows data and hashes, not executable commands, plugins, arbitrary paths, URLs, credentials,
or activation instructions. Treat tool output as untrusted candidate data. Recovery is deletion of the
coordination draft or rejection of a candidate; neither changes source assets or runtime state.

## Explicit non-goals

- Installing, registering, launching or controlling Aseprite/MCP.
- Performing drawing experiments or proving CAP-A.
- Adopting, building, publishing or activating assets.
- Duplicating the detailed CAP-A plans or changing their order.
- Freezing art direction or a production drawing pipeline.

## Authorization required to start

This planning crosswalk is authorized by the current request. Any CAP-A execution requires the distinct
authorization and prerequisites declared in the Aseprite package; it is not inherited from this document.

## Result classification

| Result | M3 condition |
|---|---|
| `PASS` | Crosswalk is complete, non-contradictory and preserves all state and authority separations |
| `FAIL` | It weakens a CAP gate, makes CAP-A a production prerequisite, or conflates generated and adopted state |
| `BLOCKED` | The governing CAP-A documents or ownership boundary cannot be identified |
| `INCONCLUSIVE` | Links or contracts remain ambiguous enough that an output could cross boundaries implicitly |

## Rollback, abandonment, and stop conditions

Withdraw the crosswalk and keep both packages independent. Stop on implicit tool execution, candidate
promotion, duplicated gate ownership, mutable handoff identity, or any claim that coordination proves
drawing capability. CAP-A/manual experiments remain valid independent work when production integration
is abandoned.

## Decisions remaining unfrozen

Aseprite/MCP feasibility, tool transport, drawing commands, skill/rule corpus, art style, resolution,
palette, animation, candidate acceptance, and all production asset/runtime choices.

## Existing execution owner

If separately authorized, follow
[supervised headless drawing](../aseprite-mcp-pixel-art/01_supervised_headless_drawing_plan.md) and the
subsequent CAP-A plans in their package; do not create replacement implementation tickets from M3.
