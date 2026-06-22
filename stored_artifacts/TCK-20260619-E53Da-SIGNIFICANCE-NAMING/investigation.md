---
status: active
ticket_id: TCK-20260619-E53Da-SIGNIFICANCE-NAMING
artifact_type: investigation
date: 2026-06-22
---

# Investigation — TCK-20260619-E53Da-SIGNIFICANCE-NAMING

## Current Behavior

### 1. `src/domains/chronicle/significance.py`

**File:** `src/domains/chronicle/significance.py`, L22–L31

`BASE_SIGNIFICANCE` currently contains 8 keys:

```python
BASE_SIGNIFICANCE: dict[str, float] = {
    "entity_death": 0.5,
    "faction_destroyed": 0.9,
    "quest_completed": 0.7,
    "calamity": 0.85,
    "LEGENDARY_ARRIVAL": 0.75,
    "KNOWN_TRAITOR_SPOTTED": 0.6,
    "betrayal_desertion": 0.7,
    "INFLATION_SPIRAL": 0.5,
}
```

**No faction war/diplomatic event types exist** (`war_declared`, `siege_begins`, `territory_transferred`, `alliance_formed`, `peace_treaty`, `betrayal`). All six faction events score `0.1` (the default) — below `CHRONICLE_THRESHOLD = 0.5` (L34). They are silently excluded from the chronicle.

**Key case inconsistency:** Some keys are uppercase (`LEGENDARY_ARRIVAL`, `KNOWN_TRAITOR_SPOTTED`, `INFLATION_SPIRAL`) and some lowercase (`entity_death`, `faction_destroyed`, etc.). E53Bd wires faction events with lowercase event_type strings.

**CHRONICLE_THRESHOLD = 0.5** (L34).

### 2. `src/domains/chronicle/naming.py`

**File:** `src/domains/chronicle/naming.py`, L34–L42

`TEMPLATES` dict has 7 keys, of which 3 are uppercase:

```python
TEMPLATES: dict[str, str] = {
    "entity_death": "The Death of {subject}",
    "faction_destroyed": "The Fall of {subject}",
    "quest_completed": "The Quest of {subject}",
    "calamity": "The Calamity at Tick {tick}",
    "WAR_DECLARED": "The {subject} War Declaration",        # UPPERCASE KEY — will miss
    "TERRITORY_TRANSFERRED": "The Fall of {subject}",      # UPPERCASE KEY — will miss
    "ALLIANCE_FORMED": "The Alliance with {subject}",      # UPPERCASE KEY — will miss
}
```

`WAR_DECLARED`, `TERRITORY_TRANSFERRED`, `ALLIANCE_FORMED` will never match because E53Bd emits lowercase `event_type` strings.

The existing war/alliance templates also use `{subject}` (single entity name) — they do not support the dual-faction `{source_faction}–{target_faction}` format required for faction events.

**`ERA_NAMES`** (L44–L48) has only 3 keys — all lowercase:

```python
ERA_NAMES: dict[str, str] = {
    "entity_death": "The Age of Conflict",
    "faction_destroyed": "The Age of Collapse",
    "calamity": "The Age of Calamity",
}
```

No faction war/diplomatic era names exist.

**`name_milestone()` signature** (L51–L78):

```python
@staticmethod
def name_milestone(
    entry: NarrativeLedgerEntry,
    entity_names: dict[int, str],
) -> str:
```

- Only accepts `entity_names` (int-keyed dict). No `faction_names` or `region_names` parameters.
- Resolution: `int(entry.subject_id)` lookup in `entity_names`; on ValueError/TypeError falls back to raw `subject_id` string.
- Template call: `template.format(subject=subject, tick=entry.tick)` — only two format vars.

For faction events with `subject_id="ALPHA:BETA"` (colon-pair format from E53Bd), the `int()` cast will raise `ValueError` and fall back to raw `"ALPHA:BETA"` as subject — then `"WAR_DECLARED"` key misses the TEMPLATES dict and `{subject}` returns `"ALPHA:BETA"`.

### 3. `NarrativeLedgerEntry` — `subject_id` field type

**File:** `src/domains/campaigns/state.py`, L144–L166

```python
@dataclass(frozen=True)
class NarrativeLedgerEntry:
    episode: int
    tick: int
    event_type: str
    subject_id: str       # entity/faction/node id (empty string if unavailable)
    payload: dict
    significance: float
    entry_id: str = ""
```

**`subject_id` is `str`** — not `int`. The int-cast in `name_milestone()` is a safe conversion attempt (with fallback), not a type guarantee.

For faction-pair events (from E53Bd): `subject_id = ":".join(sorted([fid_a, fid_b]))` — e.g. `"ALPHA:BETA"`.
For region events (`siege_begins`, `territory_transferred`): `subject_id` = the `region_id` string.

### 4. Existing test file

**File:** `tests/unit/chronicle/test_chronicle_compiler.py` (L1–L576)

Single test file covers E51A through E51D. No separate `test_significance.py` or `test_naming.py` files exist. The ticket refers to these names — they must be created as new files.

**`_make_entry()` helper pattern** (L52–L67):

```python
def _make_entry(
    event_type: str,
    payload: dict | None = None,
    episode: int = 0,
    tick: int = 1,
    subject_id: str = "test-subject",
) -> NarrativeLedgerEntry:
    return NarrativeLedgerEntry(
        episode=episode,
        tick=tick,
        event_type=event_type,
        subject_id=subject_id,
        payload=payload or {},
        significance=0.0,
        entry_id=f"{episode}:{tick}:{event_type}:{subject_id}",
    )
```

**TC-4 hazard:** `test_known_event_types_score_correctly` (L122–L129) iterates over all keys in `BASE_SIGNIFICANCE`. When new faction keys are added, this test will automatically cover them — no change needed. But it will fail if the added scores differ from those declared in the dict (they should be identical by construction).

**TC-14 hazard:** `test_known_event_type_templates` (L311–L329) hard-codes cases for `WAR_DECLARED`, `TERRITORY_TRANSFERRED`, `ALLIANCE_FORMED` with uppercase keys and expects the old uppercase-key behavior. This test MUST be updated when the keys are renamed to lowercase and the template format changes.

**TC-16 hazard:** `test_era_naming_matches_dominant_type` (L348–L357) has an assertion: `ChronicleNamer.name_era(4, "ALLIANCE_FORMED") == "Era 5"` — this expects `ALLIANCE_FORMED` to NOT be in ERA_NAMES (fallback to "Era 5"). After this ticket adds `"alliance_formed"` to ERA_NAMES, this assertion remains safe because the test passes uppercase `"ALLIANCE_FORMED"` (which won't match the new lowercase key). No change needed here, but it is a subtle trap.

---

## Mechanics/Engine Constraints

- `chronicle_contract.md` Significance Scoring section (line 46–58): The doc lists a different BASE_SIGNIFICANCE dict than the actual source — doc has `entity_death=0.6`, actual source has `entity_death=0.5`. The doc is **out-of-date** (pre-E51A divergence). The source is authoritative. New entries must be documented in the contract after implementation.
- `chronicle_contract.md` Naming section (line 86): Documents `name_milestone(entry, entity_names)` with only 2 params. Must be updated after E53Da extends the signature.
- Parity ledger `SOC-CHRON-003` (social_narrative.yaml L2652–L2673): Current entry documents the old 2-param `name_milestone()` signature. Must be updated after implementation.
- Parity ledger `SOC-CHRON-001` (social_narrative.yaml L2608–L2628): Documents the current BASE_SIGNIFICANCE dict exhaustively. Must be updated to include faction event scores.
- **Architecture:** `EventSignificanceScorer` and `ChronicleNamer` are pure stateless classes — no durable state, no engine imports. Additions must preserve that constraint.
- **Determinism:** `template.format(**fmt_vars)` must be deterministic. The ticket spec recommends `str.format_map(collections.defaultdict(str, fmt_vars))` to avoid KeyError for templates with unexpected format variables.
- **E53Bd confirmed** (stored_artifacts/TCK-20260619-E53Bd-LEDGER-WIRING/investigation.md): event_type strings are **lowercase** (`war_declared`, not `WAR_DECLARED`). Format: `subject_id = ":".join(sorted([fid_a, fid_b]))` for faction-pair events.

---

## Parity Ledger Overlap

**File:** `docs/parity_ledger/social_narrative.yaml`

Highest current IDs found:
- Sequential `SOC-001` through `SOC-230` series (general social/group entries)
- `SOC-CROSS-EP-001` through `SOC-CROSS-EP-005` (cross-episode social memory)
- `SOC-CHRON-001` through `SOC-CHRON-005` (chronicle pipeline)

**Entries directly affected by this ticket:**

| ID | Text | Action Required |
|---|---|---|
| `SOC-CHRON-001` | EventSignificanceScorer BASE_SIGNIFICANCE dict | Update `text` and `v2_evidence` to include 6 new faction event types after implementation |
| `SOC-CHRON-003` | ChronicleNamer.name_milestone() signature | Update `text` and `v2_evidence` to reflect new 4-param signature and faction/region resolution logic |

**New entries to add:** `SOC-FAC-001` through `SOC-FAC-006` (one per faction event type). The ticket specifies these IDs; no collision with existing IDs (the `SOC-FAC-*` namespace is unused).

---

## Prior Work

- **E51A** (TCK-20260619-E51A-SIGNIFICANCE, DONE): Created `significance.py` with `EventSignificanceScorer`, `BASE_SIGNIFICANCE` (8 keys), `CHRONICLE_THRESHOLD=0.5`. Working log: `score() uses BASE_SIGNIFICANCE dict + 0.3 hero_bonus capped at 1.0`.
- **E51C** (TCK-20260619-E51C-NAMING, DONE): Created `naming.py` with `ChronicleNamer`, `TEMPLATES` (7 event types including 3 uppercase), `ERA_NAMES` (3 keys), `name_milestone(entry, entity_names)` 2-param signature.
- **E53Bd** (TCK-20260619-E53Bd-LEDGER-WIRING, DONE stored_artifact): Confirmed lowercase `event_type` strings for faction events. Confirmed `subject_id = ":".join(sorted([fid_a, fid_b]))` colon-pair format. `WorldEvent.payload: Dict[str, float]` constraint noted.
- **E53D-HISTORY** (scoped epic, stored_artifact `investigation.md`): Scoped into 4 child tickets: E53Da (this ticket), E53Db (SIEGE-BETRAYAL-LEDGER), E53Dc (COMPILER-INTEGRATION), E53Dd (DOC-ARCHIVE).

---

## Risks and Open Questions

1. **TC-14 uppercase regression**: `test_known_event_type_templates` in `test_chronicle_compiler.py` currently tests `"WAR_DECLARED"`, `"TERRITORY_TRANSFERRED"`, `"ALLIANCE_FORMED"` as uppercase keys and expects old template output. This test must be updated in this ticket — it will fail after the rename. The test update is part of scope (no regression should remain from the uppercase key removal).

2. **`str.format_map` vs `str.format(**kwargs)` safety**: The ticket specifies using `collections.defaultdict(str, fmt_vars)` with `str.format_map()` to prevent `KeyError` from templates that use unknown format variables. This is the correct approach. The current `template.format(subject=subject, tick=entry.tick)` call will raise `KeyError` if any template uses `{source_faction}` (which the new templates will). Must switch to `format_map` approach.

3. **`territory_transferred` significance value**: Ticket specifies `0.85` (citing E53Cc as authoritative). The parent epic E53D spec said `0.9`. The ticket is correct to use `0.85` per the implementing ticket's authority — but the parity ledger entry must note this.

4. **`siege_begins` subject_id format**: Ticket scope says `subject_id` for `siege_begins` and `territory_transferred` is the `region_id` string. This should be confirmed from E53Cb/E53Cc implementation artifacts if those are available. The investigation note in the ticket marks this as an open question.

5. **`betrayal` key collision**: `BASE_SIGNIFICANCE` already has `"betrayal_desertion": 0.7`. The new key is `"betrayal"` (plain). Confirm E53Bd emits `"betrayal"` not `"betrayal_desertion"` for faction-level betrayal events. These are different event types from different sources.

6. **chronicle_contract.md out-of-date**: The Significance Scoring section documents a different (pre-E51A) `BASE_SIGNIFICANCE` dict and formula. This divergence should be fixed in E53Dd (DOC-ARCHIVE) or as part of this ticket's "update related docs" step.

---

## Anti-Drift Hazards

- **TC-4 auto-coverage**: Adding keys to `BASE_SIGNIFICANCE` automatically expands `test_known_event_types_score_correctly`. If score values are wrong at implementation time, TC-4 will catch it. Do not skip TC-4 run.
- **TC-14 must be updated**: The test hard-codes uppercase key cases (`"WAR_DECLARED"`, etc.) and expects old single-faction template output. Failing to update it leaves a false-red test.
- **TC-16 safe but subtle**: The `name_era(4, "ALLIANCE_FORMED")` assertion (expects `"Era 5"`) remains correct because the new ERA_NAMES key is lowercase `"alliance_formed"`. Uppercase test string will not match. This assertion does NOT need to change.
- **SOC-CHRON-001 and SOC-CHRON-003** parity ledger entries must be updated — they document the pre-E53Da state. Leaving them as-is creates a divergence between ledger and source.
- **`format_map` defaultdict**: If `template.format(**fmt_vars)` is used instead of `format_map`, any template with `{source_faction}` or `{target_faction}` that is called with a non-faction entry will raise `KeyError`. Always use `str.format_map(collections.defaultdict(str, fmt_vars))`.
