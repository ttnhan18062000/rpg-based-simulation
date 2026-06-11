---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

Below is the **high-level implementation plan for Phase 10** in the same milestone style as the earlier high-level phase plans.

This plan is grounded in the corrected roadmap and the remaining system-surface replacement scope described in [resource_phases.md](sandbox:/mnt/data/resource_phases.md), plus the V2 completion rules in [src_principle.md](sandbox:/mnt/data/src_principle.md). It also follows the earlier correction that full replacement is **not** just semantic subsumption of gameplay. It also requires **legacy system-compatibility closure**.

---

# High-Level Implementation Plan — Phase 10 of `src`

This plan assumes Phase 9 has already produced:

- a supported long-horizon strategic/cognitive slice,
- a supported blocker/lead/knowledge slice,
- a supported social/contract slice,
- a supported progression/class/skill/reward slice,
- explicit divergences and unsupported remainder for those long-horizon semantics,
- and a formal Phase 9 exit package that later phases are required to trust.

It also assumes the project has stopped pretending that semantic recovery alone is the same thing as full system replacement.

Phase 10 is not the phase where the project should widen into new gameplay semantics, rewrite the runtime again, or begin legacy retirement.

It is the phase where `src` must recover the remaining **legacy system-compatibility surface** required for true replacement of original `src`.

The purpose of Phase 10 is:

- close the preserved CLI and entrypoint behavior where replacement is required,
- close environment-flag, broker-disabled, and infrastructure-isolation behavior where replacement is required,
- close replay/logging/metrics/observability compatibility surfaces where replacement is required,
- close API/protocol/transport compatibility surfaces where replacement is required,
- close headless/final-system execution compatibility where replacement is required,
- prove the supported Phase 10 compatibility slice against original `src` where preservation is required,
- and publish the supported compatibility boundary honestly for Phase 11 and later phases.

This is the phase where the project stops being “a new engine with lots of old semantics recovered” and becomes “a real candidate to replace the old system surface.”

---

# [Milestone 1] - Phase 9 Exit Closure and Phase 10 Readiness

## [Milestone Description]

Milestone 1 is the entry gate for Phase 10.

Its purpose is to stop the team from starting system-compatibility closure while the Phase 9 semantic baseline is still unstable, overstated, or not actually trusted.

By this point, the branch may already have:

- a much more complete gameplay-semantic surface,
- a formal Phase 9 exit package,
- and strong pressure to “just cut over to V2.”

That is still not enough.

This milestone exists because Phase 10 should not proceed while:

- compatibility rows are still mixed with semantic rows already owned by Phases 5 through 9,
- compatibility rows are still mixed with Phase 11 proof-ratification work,
- closure conditions for compatibility rows remain vague,
- or the current support boundary still overstates consumer/system compatibility that has not been proven yet.

This milestone does not close compatibility behavior itself.

It closes the semantics-to-system-surface handoff honestly.

## [Milestone technical implementation]

Create one explicit entry gate for Phase 10.

This milestone must:

- freeze the exact set of replacement-ledger rows owned by Phase 10,
- separate compatibility rows from semantic rows already owned by earlier phases,
- separate compatibility rows from Phase 11 proof-ratification rows and Phase 12 cutover rows,
- restate the current support boundary honestly for system/consumer compatibility scope,
- confirm downstream work is not assuming unsupported compatibility closure,
- and publish one formal “Phase 10 begins from this compatibility gap set” record.

This milestone must not:

- reopen Phase 9 semantic closure except where a genuine handoff defect exists,
- start cutover or retirement work under the excuse of “compatibility prep,”
- or allow compatibility ownership to blur into “general cleanup.”

## [Milestone important notes]

The trap here is familiar and dangerous: calling compatibility “polish.”

It is not polish.

If original CLI, replay/report expectations, broker-disabled imports, and consumer-facing protocol behavior still matter, then this phase is part of real replacement scope.

## [Milestone acceptance criteria]

At the end of this milestone:

- the exact Phase 10 row set is frozen,
- compatibility scope is separated from semantic closure and later cutover scope,
- closure conditions for Phase 10 rows are explicit,
- the current compatibility support boundary is restated honestly,
- and the branch has an explicit “Phase 10 ready” gate.

---

# [Milestone 2] - CLI, Entrypoint, and Execution-Mode Compatibility Closure

## [Milestone Description]

Milestone 2 closes the user- and operator-facing entry surface.

Its purpose is to recover the original system’s execution contracts where replacement requires them.

This milestone covers:

- default entry behavior,
- serve/cli/inspect contract behavior where preserved,
- argument compatibility,
- execution-mode defaults,
- expected output-path and startup/shutdown behavior,
- and equivalent headless-entry semantics where required.

It is about how the system is entered and run, not internal gameplay semantics.

It does not yet close broker-disabled behavior, observability compatibility, or API/protocol surfaces.

## [Milestone technical implementation]

Recover the supported CLI and entrypoint surface in native `src` terms.

This milestone must:

- recover preserved default entry semantics where required,
- recover preserved subcommand and argument behavior where required,
- recover preserved startup/shutdown expectations where required,
- recover expected replay/output-path semantics where required,
- and define what parts of entry/CLI behavior are preserved, intentionally divergent, or unsupported.

This milestone must not:

- silently change operator-visible behavior and call it cleanup,
- absorb protocol or observability work owned by later milestones,
- or overclaim compatibility where only internal equivalents exist.

## [Milestone important notes]

The trap here is underestimating “how people run the system.”

If V2 cannot stand in for the real entry surface, it is not replacement-ready, no matter how strong its internals are.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported entry/CLI behavior is explicit,
- startup/shutdown semantics are explicit where supported,
- execution-mode compatibility is explicit where supported,
- preserved versus divergent entry behavior is explicit,
- and the project has one credible entry-surface compatibility slice.

---

# [Milestone 3] - Environment Flags, Broker-Disabled Mode, and Infrastructure-Isolation Closure

## [Milestone Description]

Milestone 3 closes the infrastructure-optional and import-time isolation surface.

Its purpose is to recover the old system’s safe behavior when optional infrastructure is disabled, absent, or intentionally bypassed.

This milestone covers:

- environment-flag behavior where preserved,
- broker-disabled mode behavior,
- safe imports when optional infrastructure is unavailable,
- no-op or fallback behavior where preserved,
- and integration-time isolation expectations.

It is about infrastructure compatibility and safety, not consumer-facing API behavior.

It does not yet close replay/logging/metrics compatibility or API/protocol closure.

## [Milestone technical implementation]

Recover the supported infrastructure-isolation and disabled-mode surface in native `src` terms.

This milestone must:

- recover preserved environment-flag behavior where required,
- recover preserved broker-disabled semantics where required,
- recover safe import-time behavior when optional infrastructure is absent,
- recover safe no-op/fallback accessors where required,
- and define what infrastructure behavior is preserved, divergent, or unsupported.

This milestone must not:

- reintroduce hidden infrastructure dependencies,
- quietly remove disabled-mode behavior and call it simplification,
- or confuse internal architecture cleanliness with external compatibility closure.

## [Milestone important notes]

The trap here is architectural vanity.

A cleaner V2 architecture does not excuse breaking the safe behavior that let the old system run without certain infrastructure present.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported environment-flag behavior is explicit,
- supported broker-disabled behavior is explicit,
- infrastructure-isolation guarantees are explicit where supported,
- preserved versus divergent disabled-mode behavior is explicit,
- and the project has one credible infrastructure-compatibility slice.

---

# [Milestone 4] - Replay, Logging, Metrics, and Observability Compatibility Closure

## [Milestone Description]

Milestone 4 closes the operational artifact surface.

Its purpose is to recover the parts of the old system that operators, tooling, and release workflows depended on outside pure gameplay semantics.

This milestone covers:

- replay artifact compatibility where preserved,
- structured logging expectations where preserved,
- metrics/observability compatibility where preserved,
- report/artifact shape expectations where preserved,
- and compatibility of truth-bearing operational surfaces used by humans or automation.

It is not about inventing new observability. It is about recovering the required compatibility surface honestly.

It does not yet close API/protocol behavior or final-system/headless compatibility.

## [Milestone technical implementation]

Recover the supported operational-artifact compatibility surface in native `src` terms.

This milestone must:

- recover preserved replay/report artifact behavior where required,
- recover preserved structured logging behavior where required,
- recover preserved metrics/observability behavior where required,
- ensure compatibility surfaces remain truthful and bounded,
- and define what operational artifact behavior is preserved, divergent, or unsupported.

This milestone must not:

- let better internal observability excuse broken external artifact expectations,
- blur release-proof/report truth with broader product truth,
- or overclaim compatibility where only a new artifact shape exists.

## [Milestone important notes]

The trap here is thinking “nobody cares about logs/reports/metrics if the engine works.”

That is false.

Those surfaces are often what automation, operators, and release processes actually depend on.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported replay/logging/metrics/report behavior is explicit,
- truth-bearing operational surfaces remain bounded and honest,
- preserved versus divergent artifact behavior is explicit,
- and the project has one credible operational-compatibility slice.

---

# [Milestone 5] - API, Protocol, Transport, and Headless Final-System Compatibility Closure

## [Milestone Description]

Milestone 5 closes the remaining consumer-facing system surface.

Its purpose is to recover the runtime interfaces and final-system execution behavior that make V2 a plausible drop-in replacement for supported consumers.

This milestone covers:

- API route/metadata behavior where preserved,
- websocket or protocol expectations where preserved,
- JSON/MessagePack/compression behavior where preserved,
- headless/final-system execution expectations where preserved,
- and consumer-facing transport semantics that the old system exposed.

It is the broadest compatibility milestone, but it is still bounded to declared replacement scope.

## [Milestone technical implementation]

Recover the supported API/protocol/headless system surface in native `src` terms.

This milestone must:

- recover preserved API/metadata behavior where required,
- recover preserved protocol/transport/compression behavior where required,
- recover preserved headless/final-system execution semantics where required,
- ensure consumer-facing contracts are explicit and testable,
- and define what API/protocol/headless behavior is preserved, divergent, or unsupported.

This milestone must not:

- silently narrow external behavior and call it modernization,
- let internal correctness substitute for external contract compatibility,
- or absorb cutover work that belongs to later phases.

## [Milestone important notes]

The trap here is believing that if the engine core is correct, the system surface is automatically replaceable.

It is not.

Compatibility lives at the edges.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported API/protocol/headless behavior is explicit,
- consumer-facing contracts are explicit and testable,
- preserved versus divergent interface behavior is explicit,
- unsupported remainder is explicit,
- and the project has one credible consumer/system-surface compatibility slice.

---

# [Milestone 6] - Differential Proof, Compatibility Ratification, and Phase 10 Exit Package

## [Milestone Description]

Milestone 6 turns the recovered Phase 10 compatibility slices into auditable replacement truth and closes the phase honestly.

Its purpose is to ensure compatibility support is proven rather than merely approximated.

This milestone covers:

- characterization of preserved legacy compatibility behavior,
- differential old-vs-new proof where preservation is required,
- explicit divergence logging where preservation is not required,
- support-boundary ratification,
- replacement-ledger updates,
- and the handoff baseline for Phase 11.

It does not widen scope.
It proves, classifies, and packages the supported compatibility slice.

## [Milestone technical implementation]

Create one proof and ratification pass across the supported Phase 10 compatibility slice.

This milestone must:

- add or consolidate characterization tests against original `src` where needed,
- add differential tests for preserved compatibility behavior,
- log intentional divergences explicitly,
- ratify the supported boundary for preserved and divergent compatibility behavior,
- update the replacement ledger for completed Phase 10 rows,
- publish known unsupported remainder,
- and publish one formal “Phase 10 complete” package that later phases must inherit.

This milestone must not:

- confuse “works for us” with preserved compatibility,
- defer divergence logging until cutover time,
- or overclaim system replacement because the branch now has a broad surface area.

## [Milestone important notes]

The trap here is the last comforting lie before cutover work:

“It’s basically compatible enough.”

That phrase destroys replacement integrity.

Either a supported compatibility surface is proven and classified, or it is not.

## [Milestone acceptance criteria]

At the end of this milestone:

- preserved Phase 10 compatibility behavior has proof where required,
- intentional divergences are logged,
- unsupported remainder remains explicit,
- the compatibility boundary is ratified from evidence,
- replacement-ledger updates are complete,
- and the branch has a formal “Phase 10 complete” handoff baseline.

---

## Why these milestones do not duplicate each other

Milestone 2 is about **CLI and execution entry compatibility**.

Milestone 3 is about **environment flags, disabled infrastructure, and isolation compatibility**.

Milestone 4 is about **operational artifacts: replay, logs, metrics, reports**.

Milestone 5 is about **consumer-facing API/protocol/transport/headless compatibility**.

Milestone 6 is about **proof, ratification, and handoff**, not more implementation.

If you merge these, you will get a fake “systems cleanup” phase that sounds efficient and guarantees missed contracts.
