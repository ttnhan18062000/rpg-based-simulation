"""`build-config/export.toml`: strict parsing (unknown keys rejected, one scale class)."""

from __future__ import annotations

import pytest

from visual_assets.store import config
from visual_assets.store.build.exportconfig import load_export_config
from visual_assets.store.errors import BuildError
from visual_assets.store.intake.validator import file_hash

GOOD = 'format = "png"\nframe = 1\n\n[[scale_class]]\nname = "x1"\nscale = 1\n'


def write(tmp_path, text, name="export.toml"):
    path = tmp_path / name
    path.write_bytes(text.encode() if isinstance(text, str) else text)
    return path


def test_the_committed_export_rules_load_and_are_hashed():
    cfg = load_export_config(config.CATALOG_ROOT / "build-config" / "export.toml")
    assert (cfg.format, cfg.frame, [(c.name, c.scale) for c in cfg.scale_classes]) == ("png", 1, [("x1", 1)])
    assert cfg.file_hash == file_hash((config.CATALOG_ROOT / "build-config" / "export.toml").read_bytes())


@pytest.mark.parametrize("text", [
    GOOD + 'extra = 1\n',                                        # unknown top-level key
    GOOD.replace('scale = 1', 'scale = 1\nfoo = "x"'),          # unknown key inside a class
    GOOD.replace('format = "png"\n', ''),                        # missing key
    GOOD.replace('"png"', '"gif"'),                              # unsupported format
    GOOD.replace('frame = 1', 'frame = 2'),                      # only the first frame
    GOOD.replace('frame = 1', 'frame = true'),                   # bool is not an int
    GOOD.replace('scale = 1', 'scale = 0'), GOOD.replace('scale = 1', 'scale = 17'), GOOD.replace('scale = 1', 'scale = 1.5'),
    GOOD.replace('"x1"', '"X1"'), GOOD.replace('"x1"', '""'), GOOD.replace('"x1"', '1'),
    GOOD.replace('scale = 1', 'scale = 2'),                      # one class only, and it is x1 at scale 1
    GOOD + '[[scale_class]]\nname = "x2"\nscale = 2\n',          # more than one class is out of scope
    GOOD + '[[scale_class]]\nname = "x1"\nscale = 1\n',          # duplicate name
    'format = "png"\nframe = 1\nscale_class = []\n', 'format = "png"\nframe = 1\nscale_class = "x1"\n',
    "", "not toml = = =", "\xff",
])
def test_anything_unexpected_is_rejected(tmp_path, text):
    with pytest.raises(BuildError) as err:
        load_export_config(write(tmp_path, text.encode("latin-1") if text == "\xff" else text))
    assert err.value.code == "export_config_invalid"


def test_missing_oversize_and_non_utf8_files_are_rejected(tmp_path, monkeypatch):
    with pytest.raises(BuildError):
        load_export_config(tmp_path / "absent.toml")
    monkeypatch.setattr(config, "MAX_RECORD_BYTES", 5)
    with pytest.raises(BuildError):
        load_export_config(write(tmp_path, GOOD))


def test_the_hash_is_of_the_exact_bytes(tmp_path):
    a = load_export_config(write(tmp_path, GOOD))
    b = load_export_config(write(tmp_path, "# a comment\n" + GOOD, "other.toml"))
    assert a.file_hash != b.file_hash and a.scale_classes == b.scale_classes
