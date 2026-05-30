# Investigation Notes - Phase 11 Assembly Hardening

## Current Implementation Findings
- `ResolvedWorldBundle` is defined in `src/worldassembly/resolver.py`.
- It currently drops `CompileContext`.
- Recipe profiles (`stats_profile` etc.) are lost during structural merging to `WorldSpec`.
- `WorldCompiler.compile` handles context correctly, but needs the context to be passed in.
