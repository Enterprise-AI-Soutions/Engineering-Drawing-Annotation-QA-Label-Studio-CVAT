"""Tests for inter-annotator agreement analysis."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agreement_analysis import analyse, _match_regions, _f1


def _ann(image, annotator, regions):
    return {
        "id": f"ann_{annotator}_{image}",
        "image": image,
        "annotator": annotator,
        "source": "test",
        "image_width": 1920,
        "image_height": 1080,
        "regions": regions,
    }


BBOX_PUMP = {"id": "r1", "label": "pump", "type": "bbox", "bbox": [100, 100, 200, 150]}
BBOX_PUMP_CLOSE = {"id": "r2", "label": "pump", "type": "bbox", "bbox": [105, 105, 195, 145]}
BBOX_VALVE = {"id": "r3", "label": "valve", "type": "bbox", "bbox": [400, 300, 100, 80]}


def test_perfect_agreement():
    annotations = [
        _ann("pump_layout_001.png", "ann_a", [BBOX_PUMP]),
        _ann("pump_layout_001.png", "ann_b", [BBOX_PUMP]),
    ]
    result = analyse(annotations)
    assert result["summary"]["overall_mean_f1"] == 1.0


def test_no_overlap_zero_agreement():
    # Different labels → no match
    annotations = [
        _ann("valve_assembly_001.png", "ann_a", [BBOX_PUMP]),
        _ann("valve_assembly_001.png", "ann_b", [BBOX_VALVE]),
    ]
    result = analyse(annotations)
    pairs = result["per_image"][0]["pairs"]
    assert pairs[0]["f1_score"] == 0.0


def test_close_boxes_match():
    annotations = [
        _ann("motor_wiring_001.png", "ann_a", [BBOX_PUMP]),
        _ann("motor_wiring_001.png", "ann_b", [BBOX_PUMP_CLOSE]),
    ]
    result = analyse(annotations)
    pairs = result["per_image"][0]["pairs"]
    assert pairs[0]["f1_score"] > 0.8


def test_single_annotator_note():
    annotations = [
        _ann("piping_layout_001.png", "ann_a", [BBOX_PUMP]),
    ]
    result = analyse(annotations)
    entry = result["per_image"][0]
    assert "note" in entry
    assert "Only one annotator" in entry["note"]


def test_match_regions_returns_tuple():
    matched, only_a, only_b = _match_regions([BBOX_PUMP], [BBOX_PUMP])
    assert matched == 1
    assert only_a == 0
    assert only_b == 0


def test_f1_perfect():
    assert _f1(5, 0, 0) == 1.0


def test_f1_zero():
    assert _f1(0, 5, 5) == 0.0


def test_per_annotator_summary():
    annotations = [
        _ann("pump_layout_001.png", "ann_a", [BBOX_PUMP]),
        _ann("pump_layout_001.png", "ann_b", [BBOX_PUMP]),
    ]
    result = analyse(annotations)
    assert "ann_a" in result["per_annotator"]
    assert "ann_b" in result["per_annotator"]


def test_multiple_images():
    annotations = [
        _ann("pump_layout_001.png", "ann_a", [BBOX_PUMP]),
        _ann("pump_layout_001.png", "ann_b", [BBOX_PUMP]),
        _ann("valve_assembly_001.png", "ann_a", [BBOX_VALVE]),
        _ann("valve_assembly_001.png", "ann_b", [BBOX_VALVE]),
    ]
    result = analyse(annotations)
    assert result["summary"]["total_images"] == 2
