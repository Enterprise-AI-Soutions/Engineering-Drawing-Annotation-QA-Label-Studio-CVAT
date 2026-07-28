"""Tests for report generation and review queue builder."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from generate_report import generate_markdown
from create_review_queue import build_queue


# ── Review queue tests ────────────────────────────────────────────────────────

SAMPLE_VAL = {
    "summary": {"total": 2, "passed": 1, "failed": 1, "pass_rate_pct": 50.0, "total_regions": 5},
    "records": [
        {"image": "pump_layout_001.png", "annotator": "a1", "status": "fail",
         "issues": ["Missing required field: 'annotator'"], "region_count": 3},
        {"image": "valve_assembly_001.png", "annotator": "a2", "status": "pass",
         "issues": [], "region_count": 2},
    ],
}

SAMPLE_AGR = {
    "summary": {"total_images": 2, "images_with_multiple_annotators": 1,
                "iou_match_threshold": 0.5, "overall_mean_f1": 0.75},
    "per_annotator": {"a1": {"mean_f1": 0.75, "pair_count": 1}},
    "per_image": [
        {"image": "pump_layout_001.png", "annotators": ["a1", "a2"],
         "pairs": [{"annotator_a": "a1", "annotator_b": "a2", "f1_score": 0.75,
                    "matched_regions": 2, "only_in_a": 0, "only_in_b": 1}],
         "mean_f1": 0.75},
        {"image": "valve_assembly_001.png", "annotators": ["a2"],
         "note": "Only one annotator — agreement cannot be computed"},
    ],
}


def test_build_queue_returns_list():
    queue = build_queue(SAMPLE_VAL, SAMPLE_AGR)
    assert isinstance(queue, list)


def test_failed_validation_highest_priority():
    queue = build_queue(SAMPLE_VAL, SAMPLE_AGR)
    entries = {r["image"]: r for r in queue}
    assert entries["pump_layout_001.png"]["priority"] == 1


def test_queue_sorted_by_priority():
    queue = build_queue(SAMPLE_VAL, SAMPLE_AGR)
    priorities = [r["priority"] for r in queue]
    assert priorities == sorted(priorities)


def test_queue_csv_roundtrip(tmp_path):
    from create_review_queue import save_csv
    queue = build_queue(SAMPLE_VAL, SAMPLE_AGR)
    csv_path = tmp_path / "queue.csv"
    save_csv(queue, str(csv_path))
    assert csv_path.exists()
    with open(csv_path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(queue)


# ── Report generation tests ───────────────────────────────────────────────────

def test_generate_markdown_returns_string():
    md = generate_markdown(SAMPLE_VAL, SAMPLE_AGR, [])
    assert isinstance(md, str)


def test_report_contains_headings():
    md = generate_markdown(SAMPLE_VAL, SAMPLE_AGR, [])
    assert "## 1. Validation Summary" in md
    assert "## 2. Inter-Annotator Agreement" in md
    assert "## 3. Review Queue" in md


def test_report_shows_pass_rate():
    md = generate_markdown(SAMPLE_VAL, SAMPLE_AGR, [])
    assert "50.0%" in md


def test_report_shows_mean_f1():
    md = generate_markdown(SAMPLE_VAL, SAMPLE_AGR, [])
    assert "0.75" in md


def test_report_with_queue_rows():
    queue = build_queue(SAMPLE_VAL, SAMPLE_AGR)
    md = generate_markdown(SAMPLE_VAL, SAMPLE_AGR, queue)
    assert "pump_layout_001.png" in md


def test_report_empty_queue():
    md = generate_markdown(SAMPLE_VAL, SAMPLE_AGR, [])
    assert "0 image(s)" in md
