from __future__ import annotations

import copy
import json
import typing

import pytest
from pydantic import BaseModel

from tests.visual_assets.store.unit.conftest import dump, fixture_bytes, fixture_dict
from visual_assets.store import config
from visual_assets.store.contracts import (
    RECORD_TYPES,
    AdoptionRecord,
    CandidateHandoffPackage,
    IntakeResult,
    ReleaseCandidateManifest,
    RevocationRecord,
    SourceRecord,
    VisualKeyRegistry,
    canonical_json,
    parse_record,
)
from visual_assets.store.errors import ContractError


def code_of(cls, data: bytes) -> str:
    with pytest.raises(ContractError) as err:
        parse_record(cls, data)
    return err.value.code


# --------------------------------------------------------------------------- round trips


def test_fixture_round_trip_both_directions(record_cls):
    raw = fixture_bytes(record_cls)
    record = parse_record(record_cls, raw)
    assert canonical_json(record) == raw  # committed bytes are canonical
    assert parse_record(record_cls, canonical_json(record)) == record


def test_canonical_json_shape(record_cls):
    raw = fixture_bytes(record_cls)
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
    body = raw[:-1]
    assert b"\n" not in body  # insignificant whitespace is checked by the exact re-dump below
    data = json.loads(raw)
    assert json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() == body


def test_records_are_frozen(record_cls):
    record = parse_record(record_cls, fixture_bytes(record_cls))
    with pytest.raises(Exception):
        record.record_type = "x"  # type: ignore[misc]


# --------------------------------------------------------------------------- parse rejections


def test_rejects_unknown_field(record_cls):
    data = fixture_dict(record_cls)
    data["surprise"] = 1
    assert code_of(record_cls, dump(data)) == "unknown_field"


def test_rejects_unknown_nested_field(record_cls):
    data = fixture_dict(record_cls)
    nested = [k for k, v in data.items() if isinstance(v, dict) or (isinstance(v, list) and v and isinstance(v[0], dict))]
    for key in nested:
        mutated = copy.deepcopy(data)
        target = mutated[key] if isinstance(mutated[key], dict) else mutated[key][0]
        target["surprise"] = 1
        assert code_of(record_cls, dump(mutated)) == "unknown_field", key


def test_rejects_each_missing_required_field(record_cls):
    base = fixture_dict(record_cls)
    for field in base:
        data = {k: v for k, v in base.items() if k != field}
        assert code_of(record_cls, dump(data)) in {"missing_field", "wrong_record_type"}, field


def test_rejects_duplicate_key_top_level(record_cls):
    raw = fixture_bytes(record_cls).rstrip(b"\n")
    dup = raw[:-1] + b',"record_type":"' + json.loads(raw)["record_type"].encode() + b'"}'
    assert code_of(record_cls, dup) == "duplicate_key"


def test_rejects_duplicate_key_nested(record_cls):
    data = fixture_dict(record_cls)
    for key, value in data.items():
        holder = value if isinstance(value, dict) else (value[0] if isinstance(value, list) and value and isinstance(value[0], dict) else None)
        if holder is None:
            continue
        inner_key = next(iter(holder))
        text = json.dumps(data)
        needle = json.dumps(holder)
        dup_holder = needle[:-1] + f", {json.dumps(inner_key)}: {json.dumps(holder[inner_key])}" + "}"
        assert needle in text
        assert code_of(record_cls, text.replace(needle, dup_holder, 1).encode()) == "duplicate_key", key


def test_rejects_wrong_record_type(record_cls):
    data = fixture_dict(record_cls)
    data["record_type"] = "something_else"
    assert code_of(record_cls, dump(data)) == "wrong_record_type"
    other = next(c for c in RECORD_TYPES if c is not record_cls)
    assert code_of(record_cls, fixture_bytes(other)) == "wrong_record_type"


def test_rejects_unsupported_schema_version(record_cls):
    for bad in (2, 0, "1", True, 1.0):
        data = fixture_dict(record_cls)
        data["schema_version"] = bad
        # JSON `1.0` is a float, `true` a bool: neither is the integer 1
        assert code_of(record_cls, dump(data)) == "unsupported_schema_version", bad


def test_rejects_oversize_input(record_cls, monkeypatch):
    raw = fixture_bytes(record_cls)
    monkeypatch.setattr(config, "MAX_RECORD_BYTES", len(raw) - 1)
    assert code_of(record_cls, raw) == "oversize"
    monkeypatch.setattr(config, "MAX_RECORD_BYTES", len(raw))
    parse_record(record_cls, raw)  # exactly at the bound is fine


def test_rejects_oversize_on_serialise(monkeypatch):
    record = parse_record(SourceRecord, fixture_bytes(SourceRecord))
    monkeypatch.setattr(config, "MAX_RECORD_BYTES", 10)
    with pytest.raises(ContractError) as err:
        canonical_json(record)
    assert err.value.code == "oversize"


def test_rejects_invalid_utf8(record_cls):
    assert code_of(record_cls, b'{"record_type":"\xff"}') == "invalid_utf8"
    assert code_of(record_cls, fixture_bytes(record_cls)[:-2] + b"\xc3(") == "invalid_utf8"


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_rejects_non_finite_numbers(record_cls, constant):
    raw = fixture_bytes(record_cls).rstrip(b"\n")
    data = raw[:-1] + b',"extra_number":' + constant.encode() + b"}"
    assert code_of(record_cls, data) == "non_finite_number"


def test_rejects_malformed_json_and_non_objects(record_cls):
    for data in (b"", b"{", b"[]", b"null", b"1", b'"x"', b"{'a':1}", b"[" * 10000):
        assert code_of(record_cls, data) in {"invalid_json", "invalid_record"}, data[:10]


def test_rejects_type_confusion(record_cls):
    # strict mode: a string never becomes a number, a list never becomes a mapping, etc.
    base = fixture_dict(record_cls)
    for key, value in base.items():
        if key in {"record_type", "schema_version"}:
            continue
        wrong = [] if isinstance(value, str) else ("x" if not isinstance(value, str) else 1)
        data = {**base, key: wrong}
        assert code_of(record_cls, dump(data)) == "invalid_record", key


# --------------------------------------------------------------------------- handoff package


def _handoff(**changes) -> bytes:
    data = fixture_dict(CandidateHandoffPackage)
    for key, value in changes.items():
        if value is ...:
            data.pop(key)
        else:
            data[key] = value
    return dump(data)


def test_handoff_requires_the_exact_assertion():
    assert code_of(CandidateHandoffPackage, _handoff(assertion=...)) == "missing_field"
    for bad in ("HANDOFF_IS_ADOPTION", "", "handoff_is_not_adoption_publication_or_activation", None, True):
        assert code_of(CandidateHandoffPackage, _handoff(assertion=bad)) == "invalid_record", bad
    with pytest.raises(Exception):  # no default: cannot even be constructed without it
        CandidateHandoffPackage.model_construct  # noqa: B018 (construct bypasses; validate instead)
        CandidateHandoffPackage(**{k: v for k, v in fixture_dict(CandidateHandoffPackage).items() if k != "assertion"})


@pytest.mark.parametrize("field", ["source_file_name", "preview_file_name"])
def test_handoff_file_names_come_from_the_allowlist(field):
    good = fixture_dict(CandidateHandoffPackage)[field]
    for bad in ("a/b", "../" + good, good + "/..", "..", "/etc/passwd", "sub/" + good, "x\\" + good, "other.png",
                "other.aseprite", good.upper(), " " + good, good + "\n", ""):
        assert code_of(CandidateHandoffPackage, _handoff(**{field: bad})) == "invalid_record", bad


def test_handoff_provenance_markers_and_values():
    for field in ("creator", "editor", "adapter", "tool", "tool_version", "brief_id", "human_review_ref",
                  "licence_evidence_ref"):
        for marker in ("NOT_APPLICABLE", "UNAVAILABLE"):
            record = parse_record(CandidateHandoffPackage, _handoff(**{field: marker}))
            assert getattr(record, field).value == marker
        record = parse_record(CandidateHandoffPackage, _handoff(**{field: "Some Name"}))
        assert getattr(record, field) == "Some Name"
        # only the exact markers are reserved; nothing is case-folded
        assert parse_record(CandidateHandoffPackage, _handoff(**{field: "unavailable"}))
        for bad in (None, "", " x", "x ", "x\ny", "x" * 257, 0):
            assert code_of(CandidateHandoffPackage, _handoff(**{field: bad})) == "invalid_record", (field, bad)
        # round trip keeps markers as markers
        r = parse_record(CandidateHandoffPackage, _handoff(**{field: "UNAVAILABLE"}))
        assert parse_record(CandidateHandoffPackage, canonical_json(r)) == r


def test_handoff_expected_parent_is_a_revision_or_not_applicable():
    assert parse_record(CandidateHandoffPackage, _handoff(expected_parent="r0003")).expected_parent == "r0003"
    for bad in ("r0000", "UNAVAILABLE", None, "", "3"):
        assert code_of(CandidateHandoffPackage, _handoff(expected_parent=bad)) == "invalid_record", bad


def test_handoff_bounds(monkeypatch):
    for field, bad in (("width", 0), ("width", 129), ("height", -1), ("frame_count", -1), ("palette_size", 70000),
                       ("width", True), ("width", 16.0), ("declared_limitations", ["x"] * 17),
                       ("declared_limitations", ["x" * 257])):
        assert code_of(CandidateHandoffPackage, _handoff(**{field: bad})) == "invalid_record", (field, bad)
    monkeypatch.setattr(config, "MAX_DIM", 8)  # read at call time
    assert code_of(CandidateHandoffPackage, _handoff()) == "invalid_record"


# --------------------------------------------------------------------------- structure rules


def _walk_models():
    seen: dict[str, type[BaseModel]] = {}

    def visit(tp) -> None:
        if isinstance(tp, type) and issubclass(tp, BaseModel):
            if tp.__name__ in seen:
                return
            seen[tp.__name__] = tp
            for info in tp.model_fields.values():
                visit(info.annotation)
            return
        for arg in typing.get_args(tp):
            visit(arg)

    for cls in RECORD_TYPES:
        visit(cls)
    return seen


def _unconstrained(tp) -> bool:
    if tp in (typing.Any, dict, list, tuple, set, object):
        return True
    origin = typing.get_origin(tp)
    if origin is dict:
        return True
    if origin in (list, tuple, set, frozenset):
        return any(_unconstrained(a) for a in typing.get_args(tp) if a is not Ellipsis)
    if origin is typing.Union or str(origin) == "<class 'types.UnionType'>":
        return any(_unconstrained(a) for a in typing.get_args(tp))
    return False


def test_no_free_form_fields_in_any_model():
    models = _walk_models()
    assert {"CandidateHandoffPackage", "IntakeFinding", "IntakeTarget", "VariantAxis"} <= set(models)
    for name, model in models.items():
        cfg = model.model_config
        assert cfg.get("extra") == "forbid" and cfg.get("frozen") is True and cfg.get("strict") is True, name
        for field, info in model.model_fields.items():
            assert field not in {"metadata", "extra", "notes", "meta", "extras", "data"}, (name, field)
            assert not _unconstrained(info.annotation), (name, field, info.annotation)


def test_every_record_declares_type_and_version_literals():
    for cls in RECORD_TYPES:
        fields = cls.model_fields
        assert typing.get_origin(fields["record_type"].annotation) is typing.Literal, cls
        assert typing.get_args(fields["schema_version"].annotation) == (1,), cls
        assert fields["record_type"].is_required() and fields["schema_version"].is_required(), cls
    assert len({typing.get_args(c.model_fields["record_type"].annotation)[0] for c in RECORD_TYPES}) == len(RECORD_TYPES)


def test_release_manifest_names_no_active_release():
    names = set(ReleaseCandidateManifest.model_fields) | {
        f for m in _walk_models().values() if m.__name__.startswith("Release") for f in m.model_fields
    }
    assert not [n for n in names if "active" in n.lower() or "current" in n.lower()], names
    assert typing.get_args(ReleaseCandidateManifest.model_fields["status"].annotation) == ("CANDIDATE",)
    for bad in ("ACTIVE", "candidate", "RELEASED", "", None):
        data = fixture_dict(ReleaseCandidateManifest)
        data["status"] = bad
        assert code_of(ReleaseCandidateManifest, dump(data)) == "invalid_record", bad


def test_no_record_reads_a_clock_or_path_field():
    for model in _walk_models().values():
        for field, info in model.model_fields.items():
            assert "path" not in field.lower(), (model.__name__, field)


# --------------------------------------------------------------------------- cross-field rules


def _with(cls, **changes) -> bytes:
    data = fixture_dict(cls)
    for key, value in changes.items():
        data[key] = value
    return dump(data)


@pytest.mark.parametrize("cls", [AdoptionRecord, SourceRecord])
def test_parent_is_none_exactly_for_r0001(cls):
    assert parse_record(cls, _with(cls, source_revision="r0001", parent_revision=None))
    assert parse_record(cls, _with(cls, source_revision="r0002", parent_revision="r0001"))
    assert parse_record(cls, _with(cls, source_revision="r0005", parent_revision="r0002"))
    for revision, parent in (("r0001", "r0001"), ("r0002", None), ("r0002", "r0002"), ("r0002", "r0003"),
                             ("r0001", "r0002")):
        assert code_of(cls, _with(cls, source_revision=revision, parent_revision=parent)) == "invalid_record", (
            revision, parent)


def test_parent_revision_is_required_not_defaulted():
    data = fixture_dict(SourceRecord)
    del data["parent_revision"]
    assert code_of(SourceRecord, dump(data)) == "missing_field"


def test_withdrawn_licence_cannot_be_adopted():
    assert code_of(AdoptionRecord, _with(AdoptionRecord, licence_state="WITHDRAWN")) == "invalid_record"
    for state in ("UNREVIEWED", "CLEARED", "RESTRICTED"):
        assert parse_record(AdoptionRecord, _with(AdoptionRecord, licence_state=state))


def test_adoption_names_a_real_approver():
    for field in ("approver_name", "approver_role"):
        for bad in ("", " ", "x" * 129, None, "a\nb"):
            assert code_of(AdoptionRecord, _with(AdoptionRecord, **{field: bad})) == "invalid_record", (field, bad)


def test_release_entries_have_unique_keys_and_a_bound(monkeypatch):
    data = fixture_dict(ReleaseCandidateManifest)
    data["entries"] = data["entries"] * 2
    assert code_of(ReleaseCandidateManifest, dump(data)) == "invalid_record"
    monkeypatch.setattr(config, "MAX_VISUAL_KEYS", 0)
    assert code_of(ReleaseCandidateManifest, fixture_bytes(ReleaseCandidateManifest)) == "invalid_record"


def test_revocation_target_is_a_typed_union():
    for target in ({"kind": "intake", "intake_id": "fixture-intake-0001"},
                   {"kind": "source_revision", "source_asset_id": "fixture-source-0001", "source_revision": "r0002"}):
        assert parse_record(RevocationRecord, _with(RevocationRecord, target=target))
    for bad in ({"kind": "intake"}, {"kind": "other", "intake_id": "x"}, {"intake_id": "x"}, "x", None,
                {"kind": "intake", "intake_id": "x", "source_revision": "r0001"},
                {"kind": "source_revision", "source_asset_id": "x", "source_revision": "r0000"}):
        assert code_of(RevocationRecord, _with(RevocationRecord, target=bad)) in {"invalid_record", "unknown_field", "missing_field"}, bad


def test_intake_verdict_must_agree_with_findings():
    finding = {"code": "HASH_MISMATCH", "detail": "source hash differs"}
    assert parse_record(IntakeResult, _with(IntakeResult, verdict="QUARANTINED", findings=[finding]))
    assert code_of(IntakeResult, _with(IntakeResult, verdict="PASSED", findings=[finding])) == "invalid_record"
    assert code_of(IntakeResult, _with(IntakeResult, verdict="QUARANTINED", findings=[])) == "invalid_record"
    assert code_of(IntakeResult, _with(IntakeResult, findings=[{"code": "NOPE", "detail": "x"}])) == "invalid_record"
    data = fixture_dict(IntakeResult)
    data["staged_files"] = data["staged_files"] + data["staged_files"][:1]
    assert code_of(IntakeResult, dump(data)) == "invalid_record"
    data = fixture_dict(IntakeResult)
    data["staged_files"][0]["name"] = "../handoff.json"
    assert code_of(IntakeResult, dump(data)) == "invalid_record"


def test_timestamps_must_be_real(record_cls):
    data = fixture_dict(record_cls)
    stamps = [k for k, v in data.items() if isinstance(v, str) and k.endswith(("_at",))]
    for key in stamps:
        for bad in ("2026-02-30T00:00:00Z", "2026-01-01", "2026-01-01T00:00:00+00:00"):
            assert code_of(record_cls, dump({**data, key: bad})) == "invalid_record", (key, bad)


def test_registry_record_rejects_bad_axes():
    data = fixture_dict(VisualKeyRegistry)
    data["keys"][0]["variant_axes"][0]["values"] = ["x1", "x1"]
    assert code_of(VisualKeyRegistry, dump(data)) == "invalid_record"
    data = fixture_dict(VisualKeyRegistry)
    data["keys"][0]["variant_axes"][0]["values"] = []
    assert code_of(VisualKeyRegistry, dump(data)) == "invalid_record"
    data = fixture_dict(VisualKeyRegistry)
    data["keys"][0]["variant_axes"] = data["keys"][0]["variant_axes"] * 2
    assert code_of(VisualKeyRegistry, dump(data)) == "invalid_record"
