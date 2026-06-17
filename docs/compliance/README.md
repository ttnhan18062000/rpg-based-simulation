---
status: active
layer: compliance
authority: P1
audience: developer
---

# Compliance & Certification

This directory contains the authoritative records of simulation integrity, logic verification, and technical debt tracking.

## 🗺️ Navigation

- **[Logic Checklist](checklist.md)**: The master exhaustive ledger of every gameplay law verified against V2.
- **[Gap Analysis](gap_analysis.md)**: A live record of discrepancies where the code has not yet reached full compliance with the documented laws.
- **[Divergence Log](../guidelines/intentional_divergences.md)**: Detailed rationale for every intentional change from the legacy engine.

## 🛡️ Certification Standards

The RPG Engine V2 uses a multi-tier certification process:
1.  **Semantic Parity**: Every law in the checklist must be verified by a test.
2.  **Deterministic Stability**: Every law must be bit-identical across seed-identical runs.
3.  **Resource Boundedness**: Every system must be O(1) or O(N) relative to actor density, never unbounded.
