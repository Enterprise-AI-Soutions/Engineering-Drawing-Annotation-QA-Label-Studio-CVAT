"""Shared utility functions for the annotation QA pipeline."""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any


# ── Logging ───────────────────────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    """Return a configured logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(name)


# ── File I/O ──────────────────────────────────────────────────────────────────

def load_json(path: str | Path) -> Any:
    """Load and return JSON from *path*."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_json(data: Any, path: str | Path, indent: int = 2) -> None:
    """Save *data* as pretty-printed JSON to *path*."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=indent, ensure_ascii=False)


def ensure_dir(path: str | Path) -> Path:
    """Create directory (and parents) if it does not exist, return Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


# ── Drawings directory guard ───────────────────────────────────────────────────

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


def check_drawings_dir(drawings_dir: str | Path) -> list[Path]:
    """
    Verify that *drawings_dir* exists and contains at least one image file.

    Raises SystemExit with a descriptive message if the check fails.
    Returns the list of found image paths on success.
    """
    p = Path(drawings_dir)

    if not p.exists():
        log.error(
            "Drawings folder not found: %s\n"
            "  Create the folder and add your engineering drawing images (.png, .jpg, .tif)\n"
            "  before running the pipeline.",
            p,
        )
        raise SystemExit(1)

    images = [f for f in p.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]

    if not images:
        log.error(
            "No drawing images found in: %s\n"
            "  The pipeline requires at least one image file (.png, .jpg, .tif, .tiff).\n"
            "  Add your engineering drawings to that folder and re-run.\n"
            "  See README.md → 'Adding Your Own Drawings' for details.",
            p,
        )
        raise SystemExit(1)

    log.info("Found %d drawing image(s) in %s", len(images), p)
    return images


# ── Geometry helpers ──────────────────────────────────────────────────────────

def xywh_to_xyxy(x: float, y: float, w: float, h: float) -> tuple[float, float, float, float]:
    """Convert [x, y, w, h] bounding box to [x1, y1, x2, y2]."""
    return x, y, x + w, y + h


def xyxy_to_xywh(x1: float, y1: float, x2: float, y2: float) -> tuple[float, float, float, float]:
    """Convert [x1, y1, x2, y2] bounding box to [x, y, w, h]."""
    return x1, y1, x2 - x1, y2 - y1


def iou(box_a: list[float], box_b: list[float]) -> float:
    """Compute Intersection over Union for two [x, y, w, h] boxes."""
    ax1, ay1, ax2, ay2 = xywh_to_xyxy(*box_a)
    bx1, by1, bx2, by2 = xywh_to_xyxy(*box_b)

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union_area = area_a + area_b - inter_area

    return inter_area / union_area if union_area > 0 else 0.0


# ── Identifiers ───────────────────────────────────────────────────────────────

def new_id(prefix: str = "ann") -> str:
    """Generate a short unique identifier."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ── Annotation schema ─────────────────────────────────────────────────────────

NORMALIZED_SCHEMA_VERSION = "1.0"

VALID_LABELS = {
    "pump", "valve", "pipe", "motor", "compressor",
    "sensor", "tank", "fitting", "junction", "label_text",
    "dimension", "wiring", "panel", "switch", "relay",
}

def validate_label(label: str) -> bool:
    """Return True if *label* is a recognised annotation class."""
    return label.lower() in VALID_LABELS
