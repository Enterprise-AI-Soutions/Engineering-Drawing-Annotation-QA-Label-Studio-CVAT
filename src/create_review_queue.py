"""
Build a prioritised review queue from validation and agreement reports.

Images are ranked by:
  1. Failed validation (highest priority)
  2. Low inter-annotator agreement F1 (next priority)
  3. High region count with single annotator (needs second opinion)

Output: reports/review_queue.csv

Usage:
    python src/create_review_queue.py \
        --validation reports/validation_report.json \
        --agreement  reports/agreement_summary.json \
        --output     reports/review_queue.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from utils import get_logger, load_json

log = get_logger(__name__)

LOW_AGREEMENT_THRESH = 0.6   # F1 below this triggers review
SINGLE_ANNOTATOR_MIN_REGIONS = 5  # flag if solo annotator has many regions


# ── Scoring ───────────────────────────────────────────────────────────────────

def _compute_priority(
    failed_validation: bool,
    mean_f1: float | None,
    single_annotator: bool,
    region_count: int,
) -> tuple[int, str]:
    """Return (priority_score, reason) — lower score = higher priority."""
    if failed_validation:
        return 1, "validation_failed"
    if mean_f1 is not None and mean_f1 < LOW_AGREEMENT_THRESH:
        return 2, "low_agreement"
    if single_annotator and region_count >= SINGLE_ANNOTATOR_MIN_REGIONS:
        return 3, "single_annotator_complex"
    return 4, "ok"


# ── Main ──────────────────────────────────────────────────────────────────────

def build_queue(validation_report: dict, agreement_report: dict) -> list[dict]:
    # Index validation failures by image
    failed_images: set[str] = set()
    val_issues: dict[str, list[str]] = {}
    for rec in validation_report.get("records", []):
        img = rec.get("image", "")
        if rec.get("status") == "fail":
            failed_images.add(img)
            val_issues[img] = rec.get("issues", [])

    # Index agreement F1 by image
    agreement_f1: dict[str, float | None] = {}
    single_annotator: set[str] = set()
    for item in agreement_report.get("per_image", []):
        img = item.get("image", "")
        if "mean_f1" in item:
            agreement_f1[img] = item["mean_f1"]
        else:
            single_annotator.add(img)
            agreement_f1[img] = None

    # Collect all unique images
    all_images: set[str] = (
        {r.get("image", "") for r in validation_report.get("records", [])}
        | {i.get("image", "") for i in agreement_report.get("per_image", [])}
    )

    queue: list[dict] = []
    for img in all_images:
        if not img:
            continue
        region_count = next(
            (r.get("region_count", 0) for r in validation_report.get("records", []) if r.get("image") == img),
            0,
        )
        is_failed = img in failed_images
        f1 = agreement_f1.get(img)
        is_single = img in single_annotator
        priority, reason = _compute_priority(is_failed, f1, is_single, region_count)

        queue.append({
            "image": img,
            "priority": priority,
            "reason": reason,
            "validation_status": "fail" if is_failed else "pass",
            "validation_issues": "; ".join(val_issues.get(img, [])),
            "mean_agreement_f1": f1 if f1 is not None else "N/A",
            "single_annotator": "yes" if is_single else "no",
            "region_count": region_count,
        })

    queue.sort(key=lambda r: (r["priority"], r["image"]))
    return queue


def save_csv(rows: list[dict], path: str) -> None:
    if not rows:
        log.warning("Empty queue — no CSV written")
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build annotation review queue")
    parser.add_argument("--validation", default="reports/validation_report.json")
    parser.add_argument("--agreement", default="reports/agreement_summary.json")
    parser.add_argument("--output", default="reports/review_queue.csv")
    args = parser.parse_args()

    log.info("Loading validation report: %s", args.validation)
    val_report = load_json(args.validation)

    log.info("Loading agreement report: %s", args.agreement)
    agr_report = load_json(args.agreement)

    queue = build_queue(val_report, agr_report)
    save_csv(queue, args.output)
    log.info("Review queue (%d items) → %s", len(queue), args.output)

    high_priority = [r for r in queue if r["priority"] <= 2]
    if high_priority:
        log.warning("%d image(s) require urgent review!", len(high_priority))


if __name__ == "__main__":
    main()
