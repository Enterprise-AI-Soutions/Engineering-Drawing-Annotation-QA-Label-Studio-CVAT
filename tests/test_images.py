"""Tests for annotation drawing/visualization on engineering images."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from draw_annotations import _get_colour, LABEL_COLOURS


def test_known_label_colour():
    colour = _get_colour("pump")
    assert colour == LABEL_COLOURS["pump"]
    assert len(colour) == 3


def test_unknown_label_returns_default():
    colour = _get_colour("nonexistent_label")
    assert colour == (200, 200, 200)


def test_case_insensitive():
    assert _get_colour("Pump") == _get_colour("pump")
    assert _get_colour("VALVE") == _get_colour("valve")


def test_all_colours_are_rgb_tuples():
    for label, colour in LABEL_COLOURS.items():
        assert len(colour) == 3, f"Colour for {label!r} has wrong length"
        for channel in colour:
            assert 0 <= channel <= 255, f"Channel {channel} out of range for {label!r}"


@pytest.mark.skipif(
    not __import__("importlib").util.find_spec("PIL"),
    reason="Pillow not installed",
)
def test_draw_record_missing_image(tmp_path):
    from draw_annotations import draw_record

    record = {
        "image": "nonexistent_drawing.png",
        "annotator": "test",
        "regions": [
            {"id": "r1", "label": "pump", "type": "bbox", "bbox": [10, 10, 100, 80]},
        ],
    }
    result = draw_record(record, tmp_path / "drawings", tmp_path / "out")
    assert result is False  # should gracefully skip missing files


@pytest.mark.skipif(
    not __import__("importlib").util.find_spec("PIL"),
    reason="Pillow not installed",
)
def test_draw_record_creates_output(tmp_path):
    from PIL import Image
    from draw_annotations import draw_record

    drawings = tmp_path / "drawings"
    drawings.mkdir()
    # Create a minimal blank image
    img = Image.new("RGB", (200, 200), color=(240, 240, 240))
    img.save(drawings / "test_drawing.png")

    record = {
        "image": "test_drawing.png",
        "annotator": "tester",
        "regions": [
            {"id": "r1", "label": "valve", "type": "bbox", "bbox": [10, 10, 80, 60]},
        ],
    }

    out_dir = tmp_path / "output"
    result = draw_record(record, drawings, out_dir)
    assert result is True
    outputs = list(out_dir.glob("*.png"))
    assert len(outputs) == 1
