---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-KEY-USAGE-REPORT
phase: open
date: 2026-10-08
tags: [architecture, testing]
---

# TCK-20261008-VISUAL-ASSETS-KEY-USAGE-REPORT

## Title
A key-usage report: which visual keys the code references against the registry and manifest (report only)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Child 6 of `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING`. External research (Unreal Reference Viewer, Addressables Analyze, Knip): a reference graph finds unknown keys, unused adopted keys and keys that only resolve through a fallback. Report-only now; a CI gate belongs to activation.

## Scope
- A command that scans frontend (and any backend) sources for visual-key references and compares them with the registry and the latest runtime manifest: unknown keys, registered-but-unreferenced, adopted-but-unreleased, fallback-only. Deterministic output; tests with planted cases; documented in store_contract.md.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art. Failing CI on findings.

## Acceptance Criteria
- [ ] Report command tested; first run recorded in the ticket.

## Related Tickets


## Related Docs


## Related Stored Artifacts


## Related Code Areas


## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

