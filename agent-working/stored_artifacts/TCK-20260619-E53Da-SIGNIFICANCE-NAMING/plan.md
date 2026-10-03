---
status: active
ticket_id: TCK-20260619-E53Da-SIGNIFICANCE-NAMING
artifact_type: plan
date: 2026-06-22
---

# Implementation Plan — TCK-20260619-E53Da-SIGNIFICANCE-NAMING

## Scope Guards (Do NOT Touch)

- `src/domains/chronicle/grouper.py` (ChronicleGrouper) — out of scope
- `src/domains/chronicle/renderer.py` (ChronicleRenderer) — out of scope
- `src/domains/chronicle/compiler.py` (ChronicleCompiler) — out of scope
- Any NarrativeLedger wiring in `src/domains/` (belongs to E53Bd, already DONE)
- `siege_begins` and `betrayal` NarrativeLedger emission (belongs to E53Db)
- `docs/simulation/domains/chronicle_contract.md` — doc update deferred to E53Dd

---

## Dependency Map

```
Step 1 (significance.py BASE_SIGNIFICANCE)
    └─ blocks Step 6 (test_significance.py — needs the new scores to exist)

Step 2 (naming.py TEMPLATES rename + 3 missing templates)
    └─ blocks Step 4 (name_milestone() — template dict must be correct before format logic)
    └─ blocks Step 5 (TC-14 update — old uppercase keys must be gone)
    └─ blocks Step 7 (test_naming.py — templates must resolve correctly)

Step 3 (naming.py ERA_NAMES additions)
    └─ blocks Step 7 (test_naming.py::test_faction_era_names)

Step 4 (name_milestone() signature + format_map)
    └─ blocks Step 5 (TC-14 test calls name_milestone with new params)
    └─ blocks Step 7 (test_naming.py — all naming tests call name_milestone)

Steps 1–4 must all complete before running any tests.

Step 5 (TC-14 update) — independent once Steps 2+4 done; no new deps
Step 6 (test_significance.py) — independent once Step 1 done
Step 7 (test_naming.py) — independent once Steps 2+3+4 done
Step 8 (parity ledger) — independent; can run any time after Steps 1+4 done
```

Recommended execution order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → run tests.

---

## Step 1 — Add 6 faction entries to BASE_SIGNIFICANCE

**File:** `src/domains/chronicle/significance.py`

**Change:** Append 6 new keys to `BASE_SIGNIFICANCE` dict (lines 22–31), immediately after the existing 8 entries. Add a block comment to group them.

New entries (exact values, lowercase keys):
```python
# Faction war / diplomatic events (E53Da — TCK-20260619-E53Da-SIGNIFICANCE-NAMING)
"war_declared":           0.95,
"siege_begins":           0.80,
"territory_transferred":  0.85,
"alliance_formed":        0.80,
"peace_treaty":           0.75,
"betrayal":               0.85,
```

**Key collision check:** `"betrayal"` (new) is distinct from existing `"betrayal_desertion"` (0.7). These are different event types from different sources; no conflict.

**Verification:** After change, `BASE_SIGNIFICANCE` has 14 keys. `score()` and `is_chronicle_worthy()` require no changes — they already use `.get()` with the dict.

**Acceptance criteria satisfied:**
- `score(entry)` returns `0.95` for `war_declared` (≥ 0.9 AC)
- `score(entry)` returns `0.75` for `peace_treaty` (AC)
- `score(entry)` returns `0.85` for `territory_transferred` (AC)

---

## Step 2 — Fix TEMPLATES uppercase→lowercase + add 3 missing templates

**File:** `src/domains/chronicle/naming.py`

**Change 2a — Rename 3 uppercase keys to lowercase and upgrade their templates:**

Remove from `TEMPLATES`:
```python
"WAR_DECLARED": "The {subject} War Declaration",
"TERRITORY_TRANSFERRED": "The Fall of {subject}",
"ALLIANCE_FORMED": "The Alliance with {subject}",
```

Replace with (lowercase keys, dual-faction format strings using em-dash U+2013):
```python
"war_declared":          "The {source_faction} War against {target_faction}",
"territory_transferred": "The Conquest of {region_name}",
"alliance_formed":       "The {source_faction}–{target_faction} Alliance",
```

**Change 2b — Add 3 missing faction templates** (append to `TEMPLATES` dict):
```python
"peace_treaty": "The Peace of {source_faction} and {target_faction}",
"betrayal":     "The Betrayal of {source_faction} by {target_faction}",
"siege_begins": "The Siege of {region_name}",
```

**Safety note:** The uppercase→lowercase rename is safe. No existing code path produces a `NarrativeLedgerEntry` with `event_type="WAR_DECLARED"` (uppercase). E53Bd (the only wiring ticket, DONE) uses lowercase. Document in commit message.

**After change:** `TEMPLATES` has 10 keys (4 original + 3 renamed + 3 new).

---

## Step 3 — Add ERA_NAMES entries for faction eras

**File:** `src/domains/chronicle/naming.py`

**Change:** Append 3 entries to `ERA_NAMES` dict (currently at lines 44–48):
```python
"war_declared":          "The Age of War",
"alliance_formed":       "The Age of Alliances",
"territory_transferred": "The Age of Conquest",
```

**TC-16 guard:** The existing test `test_era_naming_matches_dominant_type` asserts `name_era(4, "ALLIANCE_FORMED") == "Era 5"`. This assertion uses an uppercase string (`"ALLIANCE_FORMED"`) that will NOT match the new lowercase key `"alliance_formed"`. The assertion must NOT be removed — it guards against accidentally making `ERA_NAMES` case-insensitive. No change to TC-16.

**After change:** `ERA_NAMES` has 6 keys.

---

## Step 4 — Extend name_milestone() signature + switch to format_map

**File:** `src/domains/chronicle/naming.py`

**Change 4a — Extend signature** (lines 51–54) to add two optional params:
```python
@staticmethod
def name_milestone(
    entry: NarrativeLedgerEntry,
    entity_names: dict[int, str],
    faction_names: dict[str, str] | None = None,
    region_names: dict[str, str] | None = None,
) -> str:
```

**Change 4b — Add import** at top of file:
```python
import collections
```

**Change 4c — Replace the resolution + template call block** (lines 72–78):

Replace current:
```python
# Resolve subject display name (safe int-cast with raw-str fallback)
try:
    subject = entity_names.get(int(entry.subject_id), entry.subject_id)
except (ValueError, TypeError):
    subject = entry.subject_id

template = ChronicleNamer.TEMPLATES.get(entry.event_type, "{subject}")
return template.format(subject=subject, tick=entry.tick)
```

With:
```python
# Resolve faction pair, region, or entity subject depending on subject_id format
source_faction: str = ""
target_faction: str = ""
region_name: str = ""
subject: str = ""

if ":" in entry.subject_id:
    # Faction-pair format: "factionA:factionB" (sorted, colon-separated)
    parts = entry.subject_id.split(":", 1)
    _fn = faction_names or {}
    source_faction = _fn.get(parts[0], parts[0])
    target_faction = _fn.get(parts[1], parts[1])
    subject = source_faction  # fallback for templates using {subject}
else:
    # Region or entity subject
    _rn = region_names or {}
    region_name = _rn.get(entry.subject_id, entry.subject_id)
    try:
        subject = entity_names.get(int(entry.subject_id), entry.subject_id)
    except (ValueError, TypeError):
        subject = entry.subject_id

template = ChronicleNamer.TEMPLATES.get(entry.event_type, "{subject}")
fmt_vars = dict(
    subject=subject,
    source_faction=source_faction,
    target_faction=target_faction,
    region_name=region_name,
    tick=entry.tick,
)
return template.format_map(collections.defaultdict(str, fmt_vars))
```

**Why format_map with defaultdict(str):** Any template with an unexpected `{key}` will silently substitute an empty string rather than raising `KeyError`. This preserves determinism and prevents runtime errors when templates evolve.

**Backward compatibility:** All existing callers pass only `entry` and `entity_names`. The two new params default to `None`. The int-cast resolution path (`entity_names.get(int(...))`) is unchanged for non-colon subject_ids. TC-13 (`test_milestone_naming_deterministic`) and TC-18 (`test_subject_id_not_integer_fallback`) remain unaffected.

**Acceptance criteria satisfied:**
- `name_milestone(entry, entity_names={})` with `war_declared` + `subject_id="ALPHA:BETA"` → `"The ALPHA War against BETA"` (AC)
- `name_milestone(entry, entity_names={})` with `alliance_formed` + `subject_id="ALPHA:BETA"` → `"The ALPHA–BETA Alliance"` (AC)
- `name_milestone(entry, entity_names={})` with `territory_transferred` + `subject_id="border_region"` → `"The Conquest of border_region"` (AC)

---

## Step 5 — Update TC-14 in test_chronicle_compiler.py

**File:** `tests/unit/chronicle/test_chronicle_compiler.py`

**Change:** Replace the `cases` list in `test_known_event_type_templates` (lines 315–322).

Remove old uppercase-key cases:
```python
("WAR_DECLARED", "7", 40, "The Ironhold War Declaration"),
("TERRITORY_TRANSFERRED", "7", 50, "The Fall of Ironhold"),
("ALLIANCE_FORMED", "9", 60, "The Alliance with Thornwood Guild"),
```

Replace entire `cases` list with (preserving the 3 entity cases, adding 6 faction cases):
```python
cases = [
    ("entity_death", "7", 10, "The Death of Ironhold"),
    ("faction_destroyed", "7", 20, "The Fall of Ironhold"),
    ("quest_completed", "9", 30, "The Quest of Thornwood Guild"),
    # Renamed + upgraded dual-faction templates:
    ("war_declared", "ALPHA:BETA", 40, "The ALPHA War against BETA"),
    ("alliance_formed", "ALPHA:BETA", 50, "The ALPHA–BETA Alliance"),
    ("territory_transferred", "border_region", 60, "The Conquest of border_region"),
    ("peace_treaty", "ALPHA:BETA", 70, "The Peace of ALPHA and BETA"),
    ("betrayal", "ALPHA:BETA", 80, "The Betrayal of ALPHA by BETA"),
    ("siege_begins", "castle_north", 90, "The Siege of castle_north"),
]
```

**Note on entity_names arg:** The test currently passes `entity_names` to `name_milestone`. The new params `faction_names` and `region_names` default to `None`. The faction-pair cases use raw IDs (no faction_names dict needed for this test). No change to the call site — `ChronicleNamer.name_milestone(entry, entity_names)` is still valid.

---

## Step 6 — Create tests/unit/chronicle/test_significance.py

**File (new):** `tests/unit/chronicle/test_significance.py`

**Contents:** Import `EventSignificanceScorer`, `NarrativeLedgerEntry`. Define a `_make_entry()` helper matching the one in `test_chronicle_compiler.py`. Implement these test functions (see test_plan.md for full specs):

1. `test_war_declared_scores_at_or_above_threshold` — asserts `score == approx(0.95)` and `is_chronicle_worthy` is `True`
2. `test_peace_treaty_scores_correctly` — asserts `score == approx(0.75)` and worthy
3. `test_territory_transferred_scores_correctly` — asserts `score == approx(0.85)` and worthy
4. `test_alliance_formed_scores_correctly` — asserts `score == approx(0.80)`
5. `test_siege_begins_scores_correctly` — asserts `score == approx(0.80)`
6. `test_betrayal_scores_correctly` — asserts `score == approx(0.85)`
7. `test_all_six_faction_events_are_chronicle_worthy` — parametrize over all 6 types, each must return `is_chronicle_worthy() is True`
8. `test_faction_war_declared_event_in_narrative_ledger` — E53D parent epic AC verbatim: `score >= 0.9` and `is_chronicle_worthy` True
9. `test_faction_events_do_not_receive_hero_bonus` — `war_declared` + `entity_role=HERO` payload → capped at `approx(1.0)`

---

## Step 7 — Create tests/unit/chronicle/test_naming.py

**File (new):** `tests/unit/chronicle/test_naming.py`

**Contents:** Import `ChronicleNamer`, `NarrativeLedgerEntry`. Define a `_make_entry()` helper. Implement these test functions (see test_plan.md for full specs):

1. `test_war_declared_dual_faction_template` — raw IDs, `faction_names=None`, expect `"The ALPHA War against BETA"`
2. `test_alliance_formed_dual_faction_template` — expect `"The ALPHA–BETA Alliance"` (verify U+2013 em-dash)
3. `test_territory_transferred_region_template` — `subject_id="border_region"`, expect `"The Conquest of border_region"`
4. `test_peace_treaty_dual_faction_template` — expect `"The Peace of ALPHA and BETA"`
5. `test_betrayal_dual_faction_template` — expect `"The Betrayal of ALPHA by BETA"`
6. `test_siege_begins_region_template` — `subject_id="castle_north"`, expect `"The Siege of castle_north"`
7. `test_faction_names_resolved_via_faction_names_dict` — pass `faction_names={"ALPHA": "Iron Legion", "BETA": "Shadow Court"}`, `war_declared` → `"The Iron Legion War against Shadow Court"`
8. `test_region_names_resolved_via_region_names_dict` — pass `region_names={"border_region": "The Northern Marches"}`, `territory_transferred` → `"The Conquest of The Northern Marches"`
9. `test_faction_era_names` — `name_era(0, "war_declared")` → `"The Age of War"`, `name_era(1, "alliance_formed")` → `"The Age of Alliances"`, `name_era(2, "territory_transferred")` → `"The Age of Conquest"`
10. `test_old_entity_path_unchanged_with_new_params` — `entity_death`, `subject_id="1"`, `entity_names={1: "Aldric"}`, `faction_names=None`, `region_names=None` → `"The Death of Aldric"` (backward compat guard)
11. `test_non_colon_subject_id_not_treated_as_faction` — `entity_death`, `subject_id="single_id"` (no colon) → resolves via int-cast/raw fallback, NOT split as faction pair
12. `test_format_map_no_keyerror_on_unknown_template_vars` — call `name_milestone` for an entry whose template contains `{source_faction}` but is rendered with a plain non-colon `subject_id`; assert no `KeyError`, result is a string (empty fields silently substituted)

---

## Step 8 — Add SOC-FAC-001..006 and update SOC-CHRON-001, SOC-CHRON-003 in parity ledger

**File:** `docs/parity_ledger/social_narrative.yaml`

### 8a — Update SOC-CHRON-001

Update the `text` field to include the 6 new faction event scores in the "Known event type weights" sentence:
```
... betrayal_desertion=0.7, INFLATION_SPIRAL=0.5. Faction war/diplomatic events
(E53Da): war_declared=0.95, siege_begins=0.80, territory_transferred=0.85,
alliance_formed=0.80, peace_treaty=0.75, betrayal=0.85.
```
Update `v2_evidence` to add `(TCK-20260619-E53Da-SIGNIFICANCE-NAMING)` reference.

### 8b — Update SOC-CHRON-003

Update the `text` field to reflect the new 4-param signature:
```
name_milestone(entry, entity_names, faction_names=None, region_names=None) — 
extended by E53Da to support: (1) colon-pair subject_id "fA:fB" → resolves via
faction_names dict (raw-ID fallback); (2) region subject_id → resolves via
region_names dict; (3) entity int subject_id path unchanged. Template substitution
uses str.format_map(defaultdict(str, fmt_vars)) to prevent KeyError on partial
templates. ERA_NAMES extended with war_declared→"The Age of War",
alliance_formed→"The Age of Alliances", territory_transferred→"The Age of Conquest".
```
Update `v2_evidence` to add `(TCK-20260619-E53Da-SIGNIFICANCE-NAMING)` reference.
Update `test_path` to include both test files.

### 8c — Add SOC-FAC-001 through SOC-FAC-006

Append 6 new entries after the last `SOC-CHRON-*` entry. One entry per faction event type:

```yaml
- id: SOC-FAC-001
  text: >
    war_declared events score 0.95 in EventSignificanceScorer (above CHRONICLE_THRESHOLD=0.5).
    First faction war/diplomatic type added to BASE_SIGNIFICANCE.
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    src/domains/chronicle/significance.py (BASE_SIGNIFICANCE["war_declared"]=0.95).
    (TCK-20260619-E53Da-SIGNIFICANCE-NAMING)
  proof_type: parity
  test_path: >
    pytest tests/unit/chronicle/test_significance.py::test_war_declared_scores_at_or_above_threshold -x -v
  divergence_note: null
  support_boundary: null

- id: SOC-FAC-002
  text: >
    alliance_formed events score 0.80 in EventSignificanceScorer.
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    src/domains/chronicle/significance.py (BASE_SIGNIFICANCE["alliance_formed"]=0.80).
    (TCK-20260619-E53Da-SIGNIFICANCE-NAMING)
  proof_type: parity
  test_path: >
    pytest tests/unit/chronicle/test_significance.py::test_alliance_formed_scores_correctly -x -v
  divergence_note: null
  support_boundary: null

- id: SOC-FAC-003
  text: >
    peace_treaty events score 0.75 in EventSignificanceScorer.
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    src/domains/chronicle/significance.py (BASE_SIGNIFICANCE["peace_treaty"]=0.75).
    (TCK-20260619-E53Da-SIGNIFICANCE-NAMING)
  proof_type: parity
  test_path: >
    pytest tests/unit/chronicle/test_significance.py::test_peace_treaty_scores_correctly -x -v
  divergence_note: null
  support_boundary: null

- id: SOC-FAC-004
  text: >
    betrayal events score 0.85 in EventSignificanceScorer. Distinct from existing
    betrayal_desertion (0.7) — different event type, different source (faction-level
    vs individual desertion).
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    src/domains/chronicle/significance.py (BASE_SIGNIFICANCE["betrayal"]=0.85).
    (TCK-20260619-E53Da-SIGNIFICANCE-NAMING)
  proof_type: parity
  test_path: >
    pytest tests/unit/chronicle/test_significance.py::test_betrayal_scores_correctly -x -v
  divergence_note: null
  support_boundary: null

- id: SOC-FAC-005
  text: >
    territory_transferred events score 0.85 in EventSignificanceScorer. Value is 0.85
    per E53Cc (the implementing ticket), not 0.9 from parent epic E53D spec; the
    implementing ticket is authoritative.
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    src/domains/chronicle/significance.py (BASE_SIGNIFICANCE["territory_transferred"]=0.85).
    (TCK-20260619-E53Da-SIGNIFICANCE-NAMING)
  proof_type: parity
  test_path: >
    pytest tests/unit/chronicle/test_significance.py::test_territory_transferred_scores_correctly -x -v
  divergence_note: >
    Parent epic E53D spec approximated 0.9; E53Cc (implementing ticket) set 0.85 as
    the authoritative value. No divergence from Mechanics Bible — faction event weights
    are engine-internal, not covered by Mechanics Bible formulas.
  support_boundary: null

- id: SOC-FAC-006
  text: >
    siege_begins events score 0.80 in EventSignificanceScorer.
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    src/domains/chronicle/significance.py (BASE_SIGNIFICANCE["siege_begins"]=0.80).
    (TCK-20260619-E53Da-SIGNIFICANCE-NAMING)
  proof_type: parity
  test_path: >
    pytest tests/unit/chronicle/test_significance.py::test_siege_begins_scores_correctly -x -v
  divergence_note: null
  support_boundary: null
```

---

## Test Run Order (after all steps complete)

```bash
# 1. New significance tests
pytest tests/unit/chronicle/test_significance.py -x -v

# 2. New naming tests
pytest tests/unit/chronicle/test_naming.py -x -v

# 3. Full chronicle suite (regression + updated TC-14)
pytest tests/unit/chronicle/ -x -v

# 4. Targeted AC verification for E53D parent epic
pytest tests/unit/chronicle/test_significance.py::test_faction_war_declared_event_in_narrative_ledger -x -v

# 5. TC-4 auto-expansion guard
pytest tests/unit/chronicle/test_chronicle_compiler.py::test_known_event_types_score_correctly -x -v

# 6. TC-14 update guard
pytest tests/unit/chronicle/test_chronicle_compiler.py::test_known_event_type_templates -x -v
```

---

## Post-Implementation

- Run `graphify update .` after modifying `significance.py` and `naming.py`
- Do NOT update `docs/simulation/domains/chronicle_contract.md` — deferred to E53Dd

---

## Unresolved Questions

None blocking implementation. Two notes for awareness:

1. **`siege_begins` subject_id format:** Ticket scope and investigation both state `subject_id` for `siege_begins` is the `region_id` string (not a colon-pair). This is consistent with the `{region_name}` template and the `":" in entry.subject_id` branch logic in Step 4. If E53Cb/E53Cc artifacts confirm otherwise, Step 4's else-branch already handles region resolution. No change needed to the plan.

2. **`betrayal` vs `betrayal_desertion`:** Investigation confirmed these are separate event types from separate sources. `"betrayal"` (faction-level, from E53Bd) and `"betrayal_desertion"` (individual desertion, pre-existing) are different entries in `BASE_SIGNIFICANCE` with different scores (0.85 vs 0.7). No collision.
