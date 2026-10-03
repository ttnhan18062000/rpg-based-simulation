---
status: active
ticket_id: TCK-20260619-E51C-NAMING
artifact_type: plan
date: 2026-06-22
---

# Plan — TCK-20260619-E51C-NAMING

## Implementation Steps

### Step 1 — Create `src/domains/chronicle/naming.py`

New module with `ChronicleNamer`:

- `TEMPLATES: dict[str, str]` — 7 known event_type → template strings
- `ERA_NAMES: dict[str, str]` — 3 dominant_event_type → age name strings
- `name_milestone(entry, entity_names) -> str` — looks up template, resolves subject
  (safe int-cast of subject_id with fallback to raw str), formats with subject= and
  tick= so any template variant is covered
- `name_era(era_index, dominant_event_type) -> str` — looks up era name or returns
  `f"Era {era_index + 1}"`

### Step 2 — Add test `test_milestone_naming_deterministic` (required by AC)

In `tests/unit/chronicle/test_chronicle_compiler.py`:

- TC-13: `test_milestone_naming_deterministic` — same NarrativeLedgerEntry called twice
  returns identical string both times (determinism check)
- TC-14: `test_known_event_type_templates` — each template key produces the expected
  human-readable name
- TC-15: `test_unknown_event_type_falls_back_to_subject` — unknown event_type returns
  raw subject name
- TC-16: `test_era_naming_matches_dominant_type` — each ERA_NAMES key returns its age
  name; unknown type returns "Era N" (1-based)
- TC-17: `test_calamity_includes_tick_not_subject` — calamity template embeds tick
- TC-18: `test_subject_id_not_integer_fallback` — subject_id="non-numeric" falls back
  to the raw string

### Step 3 — Update `src/domains/chronicle/__init__.py`

Export `ChronicleNamer`.

### Step 4 — Add parity ledger entry SOC-CHRON-003

In `docs/parity_ledger/social_narrative.yaml`.

## Files Changed

- `src/domains/chronicle/naming.py` (new)
- `src/domains/chronicle/__init__.py` (update exports)
- `tests/unit/chronicle/test_chronicle_compiler.py` (add TC-13 through TC-18)
- `docs/parity_ledger/social_narrative.yaml` (add SOC-CHRON-003)

## Out of Scope

- Integrating ChronicleNamer into REST endpoints (E51E)
- Rendering to human-readable text output (E51D)
- Named incident titles (ticket only specifies milestone and era naming)
