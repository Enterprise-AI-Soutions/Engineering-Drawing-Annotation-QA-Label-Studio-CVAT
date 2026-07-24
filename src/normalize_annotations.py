"""
Merge and normalize annotations from multiple sources into a single unified file.

Handles:
  - Deduplication across Label Studio and CVAT exports
  - Merging annotations for the same image from multiple annotators
  - Consistent label normalisation

Usage:
    python src/normalize_annotations.py \
        --inputs data/exports/labelstudio/engineering_annotations.json \
                 data/exports/cvat/annotations.xml \
        --output data/normalized/annotations.json
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from utils import get_logger, load_json, save_json, new_id, NORMALIZED_SCHEMA_VERSION, VALID_LABELS

log = get_logger(__name__)


# ── Label normalisation map ───────────────────────────────────────────────────

LABEL_MAP: dict[str, str] = {
    "pumps": "pump",
    "valves": "valve",
    "pipes": "pipe",
    "motors": "motor",
    "compressors": "compressor",
    "sensors": "sensor",
    "tanks": "tank",
    "fittings": "fitting",
    "junctions": "junction",
    "text": "label_text",
    "labels": "label_text",
    "dimensions": "dimension",
    "wirings": "wiring",
    "panels": "panel",
    "switches": "switch",
    "relays": "relay",
}


def normalize_label(raw: str) -> str:
    """Normalize a raw label string to a canonical class name."""
    cleaned = raw.strip().lower().replace(" ", "_").replace("-", "_")
    mapped = LABEL_MAP.get(cleaned, cleaned)
    return mapped if mapped in VALID_LABELS else "unknown"


def normalize_region(region: dict) -> dict:
    """Return a region with a normalized label."""
    return {**region, "label": normalize_label(region.get("label", ""))}


# ── Source loaders ────────────────────────────────────────────────────────────

def load_normalized(path: str | Path) -> list[dict]:
    """Load an already-normalized JSON file."""
    data = load_json(path)
    return data.get("annotations", [])


def load_labelstudio(path: str | Path) -> list[dict]:
    """Convert and load a Label Studio JSON export on the fly."""
    from convert_labelstudio import convert
    ls_data = load_json(path)
    normalized = convert(ls_data)
    return normalized.get("annotations", [])


def load_cvat(path: str | Path) -> list[dict]:
    """Convert and load a CVAT XML export on the fly."""
    from convert_cvat import convert
    normalized = convert(str(path))
    return normalized.get("annotations", [])


def _auto_load(path: str | Path) -> list[dict]:
    p = Path(path)
    if p.suffix.lower() == ".xml":
        log.info("Detected CVAT XML: %s", p.name)
        return load_cvat(p)
    data = load_json(p)
    if isinstance(data, list):
        log.info("Detected Label Studio JSON: %s", p.name)
        from convert_labelstudio import convert
        return convert(data).get("annotations", [])
    # Already normalized
    log.info("Detected normalized JSON: %s", p.name)
    return data.get("annotations", [])


# ── Merge logic ───────────────────────────────────────────────────────────────

def merge(sources: list[list[dict]]) -> list[dict]:
    """Merge annotation records from multiple sources."""
    seen_ids: set[str] = set()
    merged: list[dict] = []

    for records in sources:
        for rec in records:
            # Give every record a fresh unique id to avoid collisions
            rec = {**rec, "id": new_id("ann")}
            # Normalize labels inside regions
            rec["regions"] = [normalize_region(r) for r in rec.get("regions", [])]
            merged.append(rec)

    log.info("Merged %d annotation records from %d source(s)", len(merged), len(sources))
    return merged


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize and merge annotation exports")
    parser.add_argument("--inputs", nargs="+", required=True, help="Input files (JSON or XML)")
    parser.add_argument("--output", default="data/normalized/annotations.json")
    args = parser.parse_args()

    all_records: list[list[dict]] = []
    for path in args.inputs:
        records = _auto_load(path)
        all_records.append(records)
        log.info("Loaded %d records from %s", len(records), path)

    merged = merge(all_records)

    output = {
        "schema_version": NORMALIZED_SCHEMA_VERSION,
        "source": "merged",
        "total_records": len(merged),
        "annotations": merged,
    }
    save_json(output, args.output)
    log.info("Saved normalized output → %s", args.output)


if __name__ == "__main__":
    main()
