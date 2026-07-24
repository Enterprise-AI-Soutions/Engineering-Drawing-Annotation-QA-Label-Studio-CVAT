"""Tests for annotation validation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from validate_annotations import validate


def _make_record(**kwargs):
    base = {
        "id": "ann_test",
        "image": "pump_layout_001.png",
        "annotator": "tester@example.com",
        "source": "labelstudio",
        "image_width": 1920,
        "image_height": 1080,
        "regions": [
            {"id": "r1", "label": "pump", "type": "bbox", "bbox": [100, 100, 200, 150]},
        ],
    }
    base.update(kwargs)
    return base


def test_valid_record_passes():
    report = validate([_make_record()])
    assert report["summary"]["passed"] == 1
    assert report["summary"]["failed"] == 0


def test_missing_image_fails():
    rec = _make_record(image="")
    report = validate([rec])
    assert report["records"][0]["status"] == "fail"
    assert any("image" in i for i in report["records"][0]["issues"])


def test_missing_annotator_fails():
    rec = _make_record(annotator="")
    report = validate([rec])
    assert report["records"][0]["status"] == "fail"


def test_empty_regions_fails():
    rec = _make_record(regions=[])
    report = validate([rec])
    assert report["records"][0]["status"] == "fail"


def test_out_of_bounds_bbox_flagged():
    rec = _make_record(regions=[
        {"id": "r1", "label": "valve", "type": "bbox", "bbox": [1900, 1000, 200, 200]},
    ])
    report = validate([rec])
    issues = report["records"][0]["issues"]
    assert any("out of image bounds" in i for i in issues)


def test_tiny_bbox_flagged():
    rec = _make_record(regions=[
        {"id": "r1", "label": "pump", "type": "bbox", "bbox": [10, 10, 5, 5]},
    ])
    report = validate([rec])
    issues = report["records"][0]["issues"]
    assert any("below threshold" in i for i in issues)


def test_unknown_label_flagged():
    rec = _make_record(regions=[
        {"id": "r1", "label": "unknown", "type": "bbox", "bbox": [100, 100, 200, 100]},
    ])
    report = validate([rec])
    issues = report["records"][0]["issues"]
    assert any("unknown" in i for i in issues)


def test_duplicate_region_ids_flagged():
    rec = _make_record(regions=[
        {"id": "dup", "label": "pump", "type": "bbox", "bbox": [100, 100, 200, 100]},
        {"id": "dup", "label": "valve", "type": "bbox", "bbox": [300, 100, 200, 100]},
    ])
    report = validate([rec])
    issues = report["records"][0]["issues"]
    assert any("Duplicate" in i for i in issues)


def test_polygon_needs_three_points():
    rec = _make_record(regions=[
        {"id": "p1", "label": "pipe", "type": "polygon", "polygon": [[0, 0], [100, 0]]},
    ])
    report = validate([rec])
    issues = report["records"][0]["issues"]
    assert any("3 points" in i for i in issues)


def test_pass_rate_calculation():
    good = _make_record(id="good")
    bad = _make_record(id="bad", image="")
    report = validate([good, bad])
    assert report["summary"]["pass_rate_pct"] == 50.0
