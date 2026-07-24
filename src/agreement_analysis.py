"""
Inter-annotator agreement analysis for engineering drawing annotations.

Methods:
  - Pairwise IoU-based matching for bounding boxes
  - Label agreement percentage
  - Per-image and per-annotator summary statistics

Usage:
    python src/agreement_analysis.py \
        --input  data/normalized/annotations.json \
        --output reports/agreement_summary.json
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from itertools import combinations
from typing import Any

from utils import get_logger, load_json, save_json, iou

log = get_logger(__name__)

IOU_MATCH_THRESHOLD = 0.5   # IoU above this = matching annotation


# ── Pairwise matching ─────────────────────────────────────────────────────────

def _match_regions(regions_a: list[dict], regions_b: list[dict]) -> tuple[int, int, int]:
    """
    Greedy IoU matching between two region lists.
    Returns (matched, only_in_a, only_in_b).
    """
    bbox_a = [r for r in regions_a if r.get("type") == "bbox"]
    bbox_b = [r for r in regions_b if r.get("type") == "bbox"]

    matched = 0
    used_b: set[int] = set()

    for ra in bbox_a:
        best_iou = 0.0
        best_j = -1
        for j, rb in enumerate(bbox_b):
            if j in used_b:
                continue
            if ra.get("label") != rb.get("label"):
                continue
            score = iou(ra["bbox"], rb["bbox"])
            if score > best_iou:
                best_iou = score
                best_j = j

        if best_iou >= IOU_MATCH_THRESHOLD:
            matched += 1
            used_b.add(best_j)

    only_a = len(bbox_a) - matched
    only_b = len(bbox_b) - matched
    return matched, only_a, only_b


def _f1(matched: int, only_a: int, only_b: int) -> float:
    """Compute F1 score from matching stats."""
    precision = matched / (matched + only_a) if (matched + only_a) > 0 else 0.0
    recall = matched / (matched + only_b) if (matched + only_b) > 0 else 0.0
    if precision + recall == 0:
        return 0.0
    return round(2 * precision * recall / (precision + recall), 4)


# ── Grouping ──────────────────────────────────────────────────────────────────

def _group_by_image_and_annotator(annotations: list[dict]) -> dict[str, dict[str, dict]]:
    """Group annotations as {image_name: {annotator_id: record}}."""
    grouped: dict[str, dict[str, dict]] = defaultdict(dict)
    for rec in annotations:
        img = rec.get("image", "unknown")
        ann = rec.get("annotator", "unknown")
        # Last record wins if same annotator annotated same image twice
        grouped[img][ann] = rec
    return grouped


# ── Main analysis ─────────────────────────────────────────────────────────────

def analyse(annotations: list[dict]) -> dict:
    grouped = _group_by_image_and_annotator(annotations)

    image_results: list[dict] = []
    all_f1: list[float] = []
    annotator_f1: dict[str, list[float]] = defaultdict(list)

    for image_name, annotator_map in grouped.items():
        annotators = list(annotator_map.keys())

        if len(annotators) < 2:
            image_results.append({
                "image": image_name,
                "annotators": annotators,
                "pairs": [],
                "note": "Only one annotator — agreement cannot be computed",
            })
            continue

        pairs: list[dict] = []
        for ann_a, ann_b in combinations(annotators, 2):
            rec_a = annotator_map[ann_a]
            rec_b = annotator_map[ann_b]
            matched, only_a, only_b = _match_regions(rec_a["regions"], rec_b["regions"])
            f1 = _f1(matched, only_a, only_b)
            pairs.append({
                "annotator_a": ann_a,
                "annotator_b": ann_b,
                "matched_regions": matched,
                "only_in_a": only_a,
                "only_in_b": only_b,
                "f1_score": f1,
            })
            all_f1.append(f1)
            annotator_f1[ann_a].append(f1)
            annotator_f1[ann_b].append(f1)

        image_results.append({
            "image": image_name,
            "annotators": annotators,
            "pairs": pairs,
            "mean_f1": round(sum(p["f1_score"] for p in pairs) / len(pairs), 4),
        })

    overall_mean = round(sum(all_f1) / len(all_f1), 4) if all_f1 else 0.0

    per_annotator = {
        ann: {"mean_f1": round(sum(scores) / len(scores), 4), "pair_count": len(scores)}
        for ann, scores in annotator_f1.items()
    }

    log.info("Overall mean inter-annotator F1: %.4f", overall_mean)

    return {
        "summary": {
            "total_images": len(grouped),
            "images_with_multiple_annotators": sum(
                1 for v in grouped.values() if len(v) >= 2
            ),
            "iou_match_threshold": IOU_MATCH_THRESHOLD,
            "overall_mean_f1": overall_mean,
        },
        "per_annotator": per_annotator,
        "per_image": image_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute inter-annotator agreement")
    parser.add_argument("--input", default="data/normalized/annotations.json")
    parser.add_argument("--output", default="reports/agreement_summary.json")
    args = parser.parse_args()

    data = load_json(args.input)
    annotations = data.get("annotations", [])
    log.info("Analysing %d annotation records …", len(annotations))

    result = analyse(annotations)
    save_json(result, args.output)
    log.info("Agreement summary → %s", args.output)


if __name__ == "__main__":
    main()
