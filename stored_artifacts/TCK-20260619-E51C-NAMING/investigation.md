---
status: active
ticket_id: TCK-20260619-E51C-NAMING
artifact_type: investigation
date: 2026-06-22
---

# Investigation — TCK-20260619-E51C-NAMING

## Current Behavior

No `src/domains/chronicle/naming.py` exists. Chronicle entries produced by E51B
(ChronicleGrouper) carry no human-readable names — only raw event_type strings and
numeric subject_id values are available.

## What Already Exists

| Component | File | Notes |
|---|---|---|
| EventSignificanceScorer | `src/domains/chronicle/significance.py` | E51A — stateless, deterministic |
| ChronicleGrouper + Incident/Episode/Era/ChronicleHierarchy | `src/domains/chronicle/grouper.py` | E51B — stateless, deterministic |
| NarrativeLedgerEntry | `src/domains/campaigns/state.py:L144` | fields: episode, tick, event_type, subject_id, payload, significance, entry_id |

## Key Findings

1. **`subject_id` is a `str`**: the field is typed `str` not `int`. The ticket spec
   calls `int(entry.subject_id)` to key into `entity_names: dict[int, str]`. This
   must be handled safely — subject_id may not be an integer string (e.g. "test-subject").
   Implementation will do a safe int-cast with fallback to the raw str.

2. **Determinism constraint**: both `name_milestone` and `name_era` must be pure
   functions of their inputs. No RNG or timestamp in naming path. Template substitution
   from a fixed dict satisfies this.

3. **TEMPLATES coverage**: ticket defines 7 event_type → template mappings. Unknown
   types fall back to `"{subject}"` (the raw subject name). `calamity` uses `{tick}` not
   `{subject}`. This needs separate handling in name_milestone for the calamity template
   since `{subject}` is not used.

4. **Era naming**: `name_era` maps dominant_event_type to an age name; falls back to
   `f"Era {era_index + 1}"` (1-based ordinal for human readability).

5. **No engine imports**: consistent with E51A and E51B design constraints.

6. **`__init__.py`**: currently empty (1 line). Will add ChronicleNamer to exports.

## Risk Assessment

- Low risk. Pure function, no state, no side effects.
- Edge case: subject_id that is not a digit string → safe fallback to raw str.
- Edge case: calamity template uses {tick} but {subject} is also in format call — safe
  because Python's str.format() ignores extra kwargs; however the template string only
  uses {tick}, so we must pass tick= in the format call. Current ticket spec passes
  both subject= and tick= → works correctly.
