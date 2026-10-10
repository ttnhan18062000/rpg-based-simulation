"""Known vectors for the TypeScript `pixels-v1` hash (`frontend/src/visualAssets/pixelsV1.ts`; `TCK-20261010-VISUAL-ASSETS-EVIDENCE-CAPTURE-REAL-BUNDLE`).

The capture spec hashes what a page drew with a SECOND implementation of the store's hash. The vectors are written here by the Python implementation, from the three committed rehearsal
artifacts plus synthetic images (non-square, alpha, transparent pixels that carry a colour), and committed beside the frontend test that compares the TypeScript hash with them
(`frontend/src/visualAssets/__tests__/pixelsV1.test.ts`). This test keeps the committed file equal to a fresh Python computation, so it cannot rot or be edited to fit a drifting hash.

    python -c "from tests.visual_assets import test_pixelhash_vectors as t; t.write()"   # refresh the committed vectors
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

from visual_assets.store import pixels

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "frontend" / "src" / "visualAssets" / "__fixtures__" / "rehearsal"
VECTORS = REPO / "frontend" / "src" / "visualAssets" / "__fixtures__" / "pixelhash" / "vectors.json"


def _vector(name: str, width: int, height: int, rgba: bytes) -> dict:
    image = pixels.DecodedImage(width, height, rgba)
    return {"name": name, "width": width, "height": height, "rgba_base64": base64.b64encode(rgba).decode(), "pixel_hash": pixels.pixel_hash_of(image)}


def build() -> dict:
    manifest = json.loads((FIXTURE / "runtime_manifest.json").read_text())
    vectors = []
    for entry in sorted(manifest["entries"], key=lambda e: e["visual_key"]):
        decoded = pixels.decode_png((FIXTURE / entry["file"]).read_bytes(), max_dim=128)
        vector = _vector(f"artifact:{entry['visual_key']}", decoded.width, decoded.height, decoded.rgba)
        assert vector["pixel_hash"] == entry["pixel_hash"], "the Python hash must equal the committed manifest's own hash"
        vectors.append(vector)
    vectors.append(_vector("non-square 5x3", 5, 3, bytes(v for i in range(15) for v in (i * 17 % 256, (i * 29 + 5) % 256, (i * 41 + 9) % 256, 255))))
    vectors.append(_vector("alpha mix 4x2", 4, 2, bytes([255, 0, 0, 255, 0, 255, 0, 128, 0, 0, 255, 1, 9, 9, 9, 0, 10, 20, 30, 254, 40, 50, 60, 64, 70, 80, 90, 200, 1, 2, 3, 0])))
    vectors.append(_vector("transparent colour is not part of the hash 2x2", 2, 2, bytes([200, 100, 50, 0, 1, 2, 3, 255, 255, 255, 255, 0, 4, 5, 6, 255])))
    return {"record_type": "pixelhash_vectors", "schema_version": 1, "algorithm": "pixels-v1", "vectors": vectors}


def write() -> None:
    VECTORS.parent.mkdir(parents=True, exist_ok=True)
    VECTORS.write_text(json.dumps(build(), indent=1, sort_keys=True) + "\n")


def test_the_committed_vectors_equal_a_fresh_python_computation():
    assert json.loads(VECTORS.read_text()) == build(), "regenerate: python -c \"from tests.visual_assets import test_pixelhash_vectors as t; t.write()\""


def test_the_vectors_cover_the_committed_artifacts_a_non_square_image_alpha_and_transparent_colour():
    names = [v["name"] for v in build()["vectors"]]
    assert sorted(n for n in names if n.startswith("artifact:")) == ["artifact:fixture.rehearsal.frame", "artifact:fixture.rehearsal.gem", "artifact:fixture.rehearsal.rock"]
    assert {"non-square 5x3", "alpha mix 4x2", "transparent colour is not part of the hash 2x2"} <= set(names)
    assert any(v["width"] != v["height"] for v in build()["vectors"])


def test_a_transparent_pixels_colour_changes_nothing_and_any_visible_byte_does():
    base = bytes([10, 20, 30, 255, 7, 7, 7, 0])
    same = bytes([10, 20, 30, 255, 200, 100, 50, 0])
    assert _vector("a", 2, 1, base)["pixel_hash"] == _vector("b", 2, 1, same)["pixel_hash"]
    for index in (0, 1, 2, 3, 7):
        changed = bytearray(base)
        changed[index] ^= 1
        assert _vector("c", 2, 1, bytes(changed))["pixel_hash"] != _vector("a", 2, 1, base)["pixel_hash"], index
