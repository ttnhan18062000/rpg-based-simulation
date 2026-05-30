# Investigation: Simple Procedural Generation Foundation (Phase 8)

## Technical Challenges & Architecture

1. **RNG Management**: Python's global `random` must not be mutated. The generator must construct an isolated `random.Random(seed)` instance and pass it along helper methods to guarantee thread-safety and byte-identical determinism.
2. **Bounds & Spacing Invariants**: All generated regions must stay inside map boundaries, and all resources/buildings must reside inside applicable parent region coordinate bounds.
3. **Pydantic Validation**: Because `WorldSpec` requires typed entities and validated schemas, the generator must directly construct specs using native Pydantic constructors so they are validated upon instantiation.
