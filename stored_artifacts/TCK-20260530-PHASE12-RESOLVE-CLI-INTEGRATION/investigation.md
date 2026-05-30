# Investigation Notes - Phase 12 CLI and Lab Integration

## Current Findings
- `CompileContext` handles profile registrations but lacks clean JSON serialization/deserialization.
- `WorldRepository` load path detects compositions and redirects to resolved world yaml if exists, but does not load the compile context.
- `WorldCompiler` accepts a `context` parameter but does not load it from disk itself.
