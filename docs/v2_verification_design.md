# V2 Logic Verification Design

## Purpose
The purpose of this design is to establish a rigorous, evidence-based audit of the `src` engine and `tests` proof suite against the logic claims inherited from the original `src` (as documented in `legacy_checklist.md` and `legacy_checklist_marked.md`).

## Core Principles
1. **Evidence-First**: Every claim of completion (`[x]`) must be backed by specific code locations and test cases.
2. **V2 Alignment**: Verification must confirm that implementations obey V2 principles (singular apply path, determinism, boundedness, lifecycle safety).
3. **Transparency**: Gaps in proof (missing tests for implemented logic) must be explicitly flagged.

## Audit Methodology: Iterative Subsystem Audit
We will proceed subsystem by subsystem, mapping each checklist item to its V2 implementation.

### 1. Verification Ledger (`legacy_checklist_verified.md`)
A new file at the repository root will serve as the authoritative record of verification. It will mirror the structure of the marked checklist but include:
- **[Code]**: Path to implementation.
- **[Test]**: Path to test coverage.
- **[Status]**: `VERIFIED` or `PROOF_GAP`.

### 2. Audit Workflow
For each subsystem:
- **Step A: Code Mapping**: Grep and static analysis of `src` to identify the implementation of the atomic logic.
- **Step B: Test Mapping**: Static analysis of `tests` to identify the specific tests that validate the logic.
- **Step C: Cross-Reference**: Ensure the implementation follows the "Authoritative Mutation Path" and "Deterministic Baseline" requirements.
- **Step D: Documentation**: Update the ledger with the findings.

## Subsystem Priorities
1. Authoritative Action and Update Model
2. Combat / Movement / Legality / Tactics
3. Strategic Mind / Cognition
4. Social / Contracts / Relationships
5. World / Deterministic Substrate
6. Progression / Rewards

## Success Criteria
- 100% of items marked `[x]` in `legacy_checklist_marked.md` are audited.
- Every audited item has a clear `VERIFIED` status with evidence or a `PROOF_GAP` status with a remediation note.
- The `legacy_checklist_verified.md` file is complete and accurate.
