"""
Draw annotations (bounding boxes and polygons) on engineering drawings.

Outputs annotated images to outputs/review_images/ for visual QA.

Requires: Pillow  (pip install Pillow)

Usage:
    python src/draw_annotations.py \
        --annotations data/normalized/annotations.json \
        --drawings    data/drawings \
        --output      outputs/review_images
"""

from __future__ import annotations

import argparse
from pathlib import Path

from utils import get_logger, load_json, check_drawings_dir

log = get_logger(__name__)

# Colour palette per label (RGB)
LABEL_COLOURS: dict[str, tuple[int, int, int]] = {
    "pump":        (255, 87,  34),
    "valve":       (33,  150, 243),
    "pipe":        (76,  175, 80),
    "motor":       (156, 39,  176),
    "compressor":  (255, 193, 7),
    "sensor":      (0,   188, 212),
    "tank":        (121, 85,  72),
    "fitting":     (233, 30,  99),
    "junction":    (63,  81,  181),
    "label_text":  (158, 158, 158),
    "dimension":   (255, 235, 59),
    "wiring":      (255, 152, 0),
    "panel":       (96,  125, 139),
    "switch":      (0,   150, 136),
    "relay":       (244, 67,  54),
    "unknown":     (200, 200, 200),
}
DEFAULT_COLOUR = (200, 200, 200)


def _get_colour(label: str) -> tuple[int, int, int]:
    return LABEL_COLOURS.get(label.lower(), DEFAULT_COLOUR)


def draw_record(record: dict, drawings_dir: Path, output_dir: Path) -> bool:
    """Draw all regions for one annotation record onto its drawing image."""
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except ImportError:
        log.error("Pillow not installed. Run: pip install Pillow")
        return False

    image_name = record.get("image", "")
    image_path = drawings_dir / image_name

    if not image_path.exists():
        log.warning("Drawing not found: %s — skipping", image_path)
        return False

    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")

    try:
        font = ImageFont.truetype("arial.ttf", size=14)
    except (OSError, IOError):
        font = ImageFont.load_default()

    for region in record.get("regions", []):
        label = region.get("label", "unknown")
        colour = _get_colour(label)
        fill = (*colour, 50)   # semi-transparent fill
        outline = (*colour, 220)

        if region.get("type") == "bbox":
            x, y, w, h = region["bbox"]
            draw.rectangle([x, y, x + w, y + h], fill=fill, outline=outline, width=2)
            draw.text((x + 3, y + 3), label, fill=colour, font=font)

        elif region.get("type") == "polygon":
            pts = [tuple(p) for p in region.get("polygon", [])]
            if len(pts) >= 3:
                draw.polygon(pts, fill=fill, outline=outline)
                cx = sum(p[0] for p in pts) // len(pts)
                cy = sum(p[1] for p in pts) // len(pts)
                draw.text((cx, cy), label, fill=colour, font=font)

    annotator = record.get("annotator", "unknown").replace("@", "_at_")
    out_name = f"{image_path.stem}__{annotator}{image_path.suffix}"
    out_path = output_dir / out_name
    output_dir.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    log.info("Saved: %s", out_path)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw annotations on engineering drawings")
    parser.add_argument("--annotations", default="data/normalized/annotations.json")
    parser.add_argument("--drawings", default="data/drawings")
    parser.add_argument("--output", default="outputs/review_images")
    args = parser.parse_args()

    # ── Guard: fail immediately if drawings folder is missing or empty ──────
    check_drawings_dir(args.drawings)

    data = load_json(args.annotations)
    annotations = data.get("annotations", [])
    drawings_dir = Path(args.drawings)
    output_dir = Path(args.output)

    success = 0
    for rec in annotations:
        if draw_record(rec, drawings_dir, output_dir):
            success += 1

    log.info("Drew annotations on %d/%d images", success, len(annotations))


if __name__ == "__main__":
    main()
