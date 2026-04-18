# Investigation: Resource-Safe Engine Milestone 3

## Goal
Design the runtime state shape to prevent unbounded growth and high hot-path overhead.

## Structural Separation

### 1. Runtime vs Export vs Diagnostic
- **Runtime Model**: Optimized for simulation speed. Use `dataclasses` with `__slots__` and no Pydantic validation in the hot path.
- **Export Model**: Used for persistence/API. These can use Pydantic or complex serialization logic. They are "built from" runtime state but never "are" runtime state.
- **Diagnostic Model**: Used for debugging/observability. Contains high-fidelity traces. These are produced only when requested or internally buffered with strict retention.

### 2. Bounded Collections
- **Problem**: Python lists and dicts grow until RAM exhausts.
- **Solution**: Create `BoundedList` (circular buffer) and `BoundedDict` (LRU or count-limited) in a new `src_v2/core/collections.py`.
- **Overflow Policy**: 
    - `TRUNCATE`: Remove oldest.
    - `REJECT`: Stop adding.
    - `COMPACT`: Summarize (e.g., aggregate float values).

### 3. Case Study: World History
- Instead of storing every state generation forever, `src_v2` will maintain a `HistoricalWindow`.
- Default: 100 ticks. Older states are dropped unless explicitly exported to a separate persistence layer.

### 4. Case Study: Event Logs
- Current logs in the legacy engine are often just lists of strings.
- In `src_v2`, `EventLog` will be a `BoundedList[AuthoritativeEvent]`.

## Technical Risks
- **Overhead of Wrapping**: Custom collections might be slower than native ones.
- **Solution**: Use simple `list` and `dict` subclasses or thin wrappers. Keep it lean.
- **Complexity of Separation**: Copying data from Runtime to Export models repeatedly.
- **Solution**: Implement `to_export()` as a separate factory function rather than a method on the state, to keep the hot path lean.
