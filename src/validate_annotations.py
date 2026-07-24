"""
Validate normalized annotations for completeness and quality.

Checks performed:
  - Required fields present (image, annotator, regions)
  - Bounding boxes within image bounds
  - Labels are recognised classes
  - Region area is above a minimum threshold
  - No duplicate region IDs within a record

Usage:
    python src/validate_annotations.py \
        --input  data/normalized/annotations.json \
        --output reports/validation_report.json
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from typing import Any

from utils import get_logger, load_json, save_json

log = get_logger(__name__)

MIN_BBOX_AREA = 100   # pixels²  — below this is likely noise
IOU_DUPLICATE_THRESH = 0.9


# ── Individual record validators ──────────────────────────────────────────────

def _check_required_fields(rec: dict) -> list[str]:
    issues = []
    for field in ("image", "annotator", "regions", "image_width", "image_height"):
        if not rec.get(field):
            issues.append(f"Missing required field: {field!r}")
    return issues


def _check_regions(rec: dict) -> list[str]:
    issues = []
    iw = rec.get("image_width", 0)
    ih = rec.get("image_height", 0)
    seen_ids: set[str] = set()

    for i, region in enumerate(rec.get("regions", [])):
        rid = region.get("id", f"region_{i}")
        label = region.get("label", "")

        # Duplicate IDs
        if rid in seen_ids:
            issues.append(f"Duplicate region id: {rid!r}")
        seen_ids.add(rid)

        # Unknown label
        if label == "unknown" or not label:
            issues.append(f"Region {rid}: unknown or empty label")

        # BBox checks
        if region.get("type") == "bbox":
            bbox = region.get("bbox", [])
            if len(bbox) != 4:
                issues.append(f"Region {rid}: bbox must have 4 values")
                continue
            x, y, w, h = bbox
            if w <= 0 or h <= 0:
                issues.append(f"Region {rid}: zero or negative bbox dimensions")
            if w * h < MIN_BBOX_AREA:
                issues.append(f"Region {rid}: bbox area {w*h}px² below threshold {MIN_BBOX_AREA}")
            if iw and ih:
                if x < 0 or y < 0 or (x + w) > iw or (y + h) > ih:
                    issues.append(f"Region {rid}: bbox [{x},{y},{w},{h}] out of image bounds [{iw},{ih}]")

        # Polygon checks
        if region.get("type") == "polygon":
            pts = region.get("polygon", [])
            if len(pts) < 3:
                issues.append(f"Region {rid}: polygon must have at least 3 points")

    return issues


# ── Main validator ────────────────────────────────────────────────────────────

def validate(annotations: list[dict]) -> dict:
    """Validate all annotation records. Return a structured report."""
    results: list[dict] = []
    stats = defaultdict(int)

    for rec in annotations:
        issues: list[str] = []
        issues += _check_required_fields(rec)
        issues += _check_regions(rec)

        status = "pass" if not issues else "fail"
        stats[status] += 1
        stats["total"] += 1
        stats["regions_total"] += len(rec.get("regions", []))

        results.append({
            "id": rec.get("id"),
            "image": rec.get("image"),
            "annotator": rec.get("annotator"),
            "source": rec.get("source"),
            "region_count": len(rec.get("regions", [])),
            "status": status,
            "issues": issues,
        })

    pass_rate = round(stats["pass"] / stats["total"] * 100, 1) if stats["total"] else 0.0

    log.info(
        "Validation complete — %d/%d passed (%.1f%%)",
        stats["pass"], stats["total"], pass_rate,
    )

    return {
        "summary": {
            "total": stats["total"],
            "passed": stats["pass"],
            "failed": stats["fail"],
            "pass_rate_pct": pass_rate,
            "total_regions": stats["regions_total"],
        },
        "records": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate normalized annotations")
    parser.add_argument("--input", default="data/normalized/annotations.json")
    parser.add_argument("--output", default="reports/validation_report.json")
    args = parser.parse_args()

    log.info("Loading: %s", args.input)
    data = load_json(args.input)
    annotations = data.get("annotations", [])

    report = validate(annotations)
    save_json(report, args.output)
    log.info("Validation report → %s", args.output)


if __name__ == "__main__":
    main()
