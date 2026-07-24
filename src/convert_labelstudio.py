"""
Convert Label Studio JSON exports to the normalized annotation format.

Label Studio export format (JSON):
  Each task has an 'annotations' list. Each annotation has a 'result' list
  of region objects with type 'rectanglelabels', 'polygonlabels', etc.

Usage:
    python src/convert_labelstudio.py \
        --input  data/exports/labelstudio/engineering_annotations.json \
        --output data/normalized/annotations.json
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from utils import get_logger, load_json, save_json, new_id, NORMALIZED_SCHEMA_VERSION

log = get_logger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_rectangle(result: dict[str, Any], image_w: int, image_h: int) -> dict | None:
    """Convert a rectanglelabels result item to a normalized bbox dict."""
    value = result.get("value", {})
    labels = value.get("rectanglelabels", [])
    if not labels:
        return None

    # Label Studio stores percentages; convert to absolute pixels
    x_pct = value.get("x", 0)
    y_pct = value.get("y", 0)
    w_pct = value.get("width", 0)
    h_pct = value.get("height", 0)

    x = round(x_pct / 100 * image_w)
    y = round(y_pct / 100 * image_h)
    w = round(w_pct / 100 * image_w)
    h = round(h_pct / 100 * image_h)

    return {
        "id": result.get("id", new_id("ls")),
        "label": labels[0].lower(),
        "bbox": [x, y, w, h],
        "type": "bbox",
        "confidence": value.get("score", 1.0),
    }


def _parse_polygon(result: dict[str, Any], image_w: int, image_h: int) -> dict | None:
    """Convert a polygonlabels result item to a normalized polygon dict."""
    value = result.get("value", {})
    labels = value.get("polygonlabels", [])
    points_pct = value.get("points", [])
    if not labels or not points_pct:
        return None

    points = [
        [round(px / 100 * image_w), round(py / 100 * image_h)]
        for px, py in points_pct
    ]

    return {
        "id": result.get("id", new_id("ls")),
        "label": labels[0].lower(),
        "polygon": points,
        "type": "polygon",
        "confidence": value.get("score", 1.0),
    }


def _parse_result(result: dict, image_w: int, image_h: int) -> dict | None:
    rtype = result.get("type", "")
    if rtype == "rectanglelabels":
        return _parse_rectangle(result, image_w, image_h)
    if rtype == "polygonlabels":
        return _parse_polygon(result, image_w, image_h)
    log.debug("Skipping unsupported result type: %s", rtype)
    return None


# ── Main converter ────────────────────────────────────────────────────────────

def convert(ls_data: list[dict]) -> dict:
    """Convert a Label Studio task list to normalized format."""
    records: list[dict] = []

    for task in ls_data:
        image_path = task.get("data", {}).get("image", "")
        image_name = Path(image_path).name if image_path else "unknown.png"

        # Image dimensions — fall back to defaults if not embedded
        meta = task.get("meta", {})
        image_w = meta.get("width", 1920)
        image_h = meta.get("height", 1080)

        for ann in task.get("annotations", []):
            annotator = ann.get("completed_by", {})
            annotator_id = (
                annotator.get("email") or annotator.get("username") or str(annotator.get("id", "unknown"))
            )
            regions: list[dict] = []
            for result in ann.get("result", []):
                parsed = _parse_result(result, image_w, image_h)
                if parsed:
                    regions.append(parsed)

            if not regions:
                continue

            records.append({
                "id": new_id("ann"),
                "image": image_name,
                "annotator": annotator_id,
                "source": "labelstudio",
                "task_id": task.get("id"),
                "annotation_id": ann.get("id"),
                "image_width": image_w,
                "image_height": image_h,
                "regions": regions,
            })

    return {
        "schema_version": NORMALIZED_SCHEMA_VERSION,
        "source": "labelstudio",
        "total_records": len(records),
        "annotations": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Label Studio export to normalized format")
    parser.add_argument("--input", required=True, help="Path to Label Studio JSON export")
    parser.add_argument("--output", default="data/normalized/annotations.json", help="Output path")
    args = parser.parse_args()

    log.info("Loading Label Studio export: %s", args.input)
    ls_data = load_json(args.input)

    log.info("Converting %d tasks …", len(ls_data))
    normalized = convert(ls_data)

    save_json(normalized, args.output)
    log.info("Saved %d annotation records → %s", normalized["total_records"], args.output)


if __name__ == "__main__":
    main()
