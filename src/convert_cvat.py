"""
Convert CVAT XML annotation exports to the normalized annotation format.

CVAT XML structure (CVAT for Images 1.1):
  <annotations>
    <image id="..." name="..." width="..." height="...">
      <box label="..." xtl="..." ytl="..." xbr="..." ybr="..." .../>
      <polygon label="..." points="x1,y1;x2,y2;..." .../>
    </image>
  </annotations>

Usage:
    python src/convert_cvat.py \
        --input  data/exports/cvat/annotations.xml \
        --output data/normalized/annotations.json
"""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

from utils import get_logger, save_json, new_id, NORMALIZED_SCHEMA_VERSION

log = get_logger(__name__)


# ── Parsers ───────────────────────────────────────────────────────────────────

def _parse_box(elem: ET.Element) -> dict | None:
    """Parse a <box> element into a normalized bbox region."""
    label = elem.get("label", "").lower()
    try:
        xtl = float(elem.get("xtl", 0))
        ytl = float(elem.get("ytl", 0))
        xbr = float(elem.get("xbr", 0))
        ybr = float(elem.get("ybr", 0))
    except ValueError:
        return None

    x = round(xtl)
    y = round(ytl)
    w = round(xbr - xtl)
    h = round(ybr - ytl)

    return {
        "id": new_id("cvat"),
        "label": label,
        "bbox": [x, y, w, h],
        "type": "bbox",
        "confidence": float(elem.get("confidence", 1.0)),
        "occluded": elem.get("occluded", "0") == "1",
    }


def _parse_polygon(elem: ET.Element) -> dict | None:
    """Parse a <polygon> element into a normalized polygon region."""
    label = elem.get("label", "").lower()
    points_str = elem.get("points", "")
    if not points_str:
        return None

    points = []
    for pair in points_str.split(";"):
        try:
            px, py = pair.split(",")
            points.append([round(float(px)), round(float(py))])
        except ValueError:
            continue

    if not points:
        return None

    return {
        "id": new_id("cvat"),
        "label": label,
        "polygon": points,
        "type": "polygon",
        "confidence": float(elem.get("confidence", 1.0)),
    }


def _parse_polyline(elem: ET.Element) -> dict | None:
    """Parse a <polyline> element into a normalized polyline region."""
    label = elem.get("label", "").lower()
    points_str = elem.get("points", "")
    if not points_str:
        return None

    points = []
    for pair in points_str.split(";"):
        try:
            px, py = pair.split(",")
            points.append([round(float(px)), round(float(py))])
        except ValueError:
            continue

    if not points:
        return None

    return {
        "id": new_id("cvat"),
        "label": label,
        "polyline": points,
        "type": "polyline",
        "confidence": float(elem.get("confidence", 1.0)),
    }


# ── Main converter ────────────────────────────────────────────────────────────

def convert(xml_path: str) -> dict:
    """Parse CVAT XML and return normalized annotation dict."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Determine annotator from <meta> if present
    annotator = "cvat_annotator"
    meta = root.find("meta")
    if meta is not None:
        job = meta.find("job")
        if job is not None:
            # Real CVAT exports have <assignee><email>...</email></assignee>
            assignee_elem = job.find("assignee")
            if assignee_elem is not None:
                email = assignee_elem.findtext("email")
                username = assignee_elem.findtext("username")
                annotator = email or username or annotator
            else:
                # Fallback: plain text <assignee> tag
                assignee_text = job.findtext("assignee")
                if assignee_text and assignee_text.strip():
                    annotator = assignee_text.strip()

    records: list[dict] = []

    for image_elem in root.iter("image"):
        image_name = Path(image_elem.get("name", "unknown.png")).name
        image_w = int(image_elem.get("width", 1920))
        image_h = int(image_elem.get("height", 1080))

        regions: list[dict] = []
        for child in image_elem:
            if child.tag == "box":
                parsed = _parse_box(child)
            elif child.tag == "polygon":
                parsed = _parse_polygon(child)
            elif child.tag == "polyline":
                parsed = _parse_polyline(child)
            else:
                parsed = None

            if parsed:
                regions.append(parsed)

        if not regions:
            continue

        records.append({
            "id": new_id("ann"),
            "image": image_name,
            "annotator": annotator,
            "source": "cvat",
            "image_id": image_elem.get("id"),
            "image_width": image_w,
            "image_height": image_h,
            "regions": regions,
        })

    return {
        "schema_version": NORMALIZED_SCHEMA_VERSION,
        "source": "cvat",
        "total_records": len(records),
        "annotations": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert CVAT XML export to normalized format")
    parser.add_argument("--input", required=True, help="Path to CVAT annotations.xml")
    parser.add_argument("--output", default="data/normalized/annotations.json", help="Output path")
    args = parser.parse_args()

    log.info("Loading CVAT XML: %s", args.input)
    normalized = convert(args.input)

    save_json(normalized, args.output)
    log.info("Saved %d annotation records → %s", normalized["total_records"], args.output)


if __name__ == "__main__":
    main()
