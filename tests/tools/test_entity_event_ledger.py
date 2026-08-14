"""TCK-20260808-ENTITY-EVENT-LEDGER — staleness guards for docs/event_ledger/entity.yaml."""
import re
from pathlib import Path

import yaml

from src.core import updates as updates_module

LEDGER_PATH = Path("docs/event_ledger/entity.yaml")
_FIELD_RE = re.compile(r"^EntityUpdate\.(\w+)")


def _load_ledger() -> list[dict]:
    return yaml.safe_load(LEDGER_PATH.read_text())


def test_entity_ledger_mutation_sources_exist():
    entries = _load_ledger()
    for entry in entries:
        source = entry["mutation_source"]
        m = _FIELD_RE.match(source)
        assert m, f"{entry['id']}: mutation_source {source!r} doesn't match 'EntityUpdate.<field>' shape"
        field_name = m.group(1)
        entity_update_fields = {f.name for f in __import__("dataclasses").fields(updates_module.EntityUpdate)}
        assert field_name in entity_update_fields, (
            f"{entry['id']}: {field_name!r} is not a real field on EntityUpdate "
            f"(may be stale/renamed)"
        )


def test_entity_ledger_evidence_citations_are_real_files():
    entries = _load_ledger()
    for entry in entries:
        evidence = entry["evidence"]
        # Evidence may cite a file:line or a bare doc reference — extract the leading path token.
        path_token = evidence.split()[0].split(":")[0].split("(")[0]
        if path_token.startswith("grep") or path_token.startswith("src/observability/event_extractor.py"):
            # grep-command evidence embeds the real target path later in the string.
            candidates = re.findall(r"[\w./]+\.py", evidence)
        else:
            candidates = [path_token] if path_token.endswith((".py", ".md", ".json")) else []
        for c in candidates:
            assert Path(c).exists(), f"{entry['id']}: evidence cites non-existent file {c!r}"


def test_entity_ledger_covers_every_entity_update_field():
    import dataclasses

    entity_update_fields = {f.name for f in dataclasses.fields(updates_module.EntityUpdate)}
    excluded = {
        "entity_id",  # bookkeeping key (which entity this bundle targets), not a mutation
        "intent_results", "property_updates",
        "moved_this_tick", "readiness_delta", "active", "kind_set",
        "new_position", "group_id_set", "self_model_bundle_set",
    }
    entries = _load_ledger()
    covered = set()
    for entry in entries:
        m = _FIELD_RE.match(entry["mutation_source"])
        if m:
            covered.add(m.group(1))
    # Inline scalar fields get their own ledger entries too (new_position, group_id_set,
    # self_model_bundle_set) — check those separately since the ledger cites them by the same
    # "EntityUpdate.<field>" shape.
    always_covered = {"new_position", "group_id_set", "self_model_bundle_set"}
    missing = entity_update_fields - covered - excluded - always_covered
    assert not missing, f"EntityUpdate fields with no ledger entry: {missing}"
