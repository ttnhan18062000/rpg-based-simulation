# Investigation — Milestone 73 Worldbuilding Test Strategy

## Target Verification Checklist

We need to review the source code of the `WorldSpec` schema, the `WorldValidator`, the `WorldCompiler`, and the existing simulation pipelines to ensure the tests we build align perfectly with internal structures.

### Key Findings
1. **Validation & Schema Versioning**: Unrecognized top-level sections trigger warnings, while mismatched schema versions raise `InvalidWorldSpecError` immediately via `WorldSpec.model_validate`. We need to verify these boundaries.
2. **Quest References**: Inside `WorldCompiler.compile()`, invalid target regions/factions/roles/resources are compiled but raise distinct warnings returned in the `warnings` list inside the compile report. This fulfills the warning requirement without immediately throwing if compilation is requested directly, but CLI compiler runs validation first and aborts if there are ERROR level validation issues.
3. **Determinism**: Fingerprint hash uses `StateFingerprinter.get_fingerprint(state)["state_hash"]`, which is stable and deterministic. We must ensure our test captures this exact pipeline.
4. **Smoke Simulation**: The simulation can tick cleanly by refining a `StateUpdate` using `AuthoritativeApplyPipeline.refine` and executing with `ApplyPath.apply_generation`.
