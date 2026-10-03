---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260529-OBS-PHASE22-BEHAVIOR-NORMALIZATION
artifact_type: investigation
tags: [obs, phase22, behavior, normalization]
---

# Investigation Notes — Phase 22

## Architecture Findings

### Event attribute access (QuestEvent, LifecycleEvent, GoldTransactionEvent)
Pydantic model event subclasses store key fields (e.g. `status`, `action`, `transaction_kind`)
as **direct model fields**, not inside the `.payload` dict. The normalizer must read these
via `getattr(event, field, None)` first, then fall back to `payload.get(field)` for
envelope-based events where only a payload dict is available.

### ObservabilityEventEnvelope vs SimulationEvent
Both types are supported as normalization inputs. The normalizer routes by `event_category`
regardless of the specific class type. Envelope events carry only `payload` dict; Pydantic events
carry typed attributes + a separate `.payload` field.

### BehaviorWorker failure isolation
The `_crashing_output` pattern in tests confirms that exceptions in the output callback
during JSONL processing must set `health_status = "DEGRADED"` and continue (not re-raise).
The queue drain worker loop catches exceptions at the loop level too.

## Test Design

- Used `tmp_path` pytest fixture for JSONL integration tests (no persistent files).
- Used `time.sleep()` with tight bounds for queue drain tests (0.15s max).
- Worker stop tests verify `is_running == False` after stop.
