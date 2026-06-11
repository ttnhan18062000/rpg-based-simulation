---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-PHASE11-ASSEMBLY-HARDENING
artifact_type: investigation
tags: [phase11, assembly, hardening]
---

# Investigation Notes - Phase 11 Assembly Hardening

## Current Implementation Findings
- `ResolvedWorldBundle` is defined in `src/worldassembly/resolver.py`.
- It currently drops `CompileContext`.
- Recipe profiles (`stats_profile` etc.) are lost during structural merging to `WorldSpec`.
- `WorldCompiler.compile` handles context correctly, but needs the context to be passed in.
