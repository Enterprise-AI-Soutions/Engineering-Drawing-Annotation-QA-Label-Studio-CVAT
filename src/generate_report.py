"""
Generate a Markdown + JSON annotation quality report combining all pipeline outputs.

Usage:
    python src/generate_report.py \
        --validation reports/validation_report.json \
        --agreement  reports/agreement_summary.json \
        --queue      reports/review_queue.csv \
        --output     reports/annotation_report.md
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

from utils import get_logger, load_json, save_json

log = get_logger(__name__)


# ── Markdown builder ──────────────────────────────────────────────────────────

def _md_table(headers: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(str(h) for h in headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def generate_markdown(val: dict, agr: dict, queue_rows: list[dict]) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    vs = val.get("summary", {})
    ag = agr.get("summary", {})

    lines: list[str] = [
        "# Engineering Drawing Annotation QA Report",
        f"\n_Generated: {ts}_\n",
        "---",
        "\n## 1. Validation Summary\n",
        _md_table(
            ["Metric", "Value"],
            [
                ["Total records", vs.get("total", 0)],
                ["Passed", vs.get("passed", 0)],
                ["Failed", vs.get("failed", 0)],
                ["Pass rate", f"{vs.get('pass_rate_pct', 0)}%"],
                ["Total regions", vs.get("total_regions", 0)],
            ],
        ),
    ]

    # Validation failures detail
    failed = [r for r in val.get("records", []) if r.get("status") == "fail"]
    if failed:
        lines.append("\n### Failed Records\n")
        table_rows = [
            [r.get("image", ""), r.get("annotator", ""), "; ".join(r.get("issues", []))]
            for r in failed[:20]   # cap at 20 rows
        ]
        lines.append(_md_table(["Image", "Annotator", "Issues"], table_rows))
        if len(failed) > 20:
            lines.append(f"\n_…and {len(failed) - 20} more. See `validation_report.json`._")

    lines += [
        "\n\n---",
        "\n## 2. Inter-Annotator Agreement\n",
        _md_table(
            ["Metric", "Value"],
            [
                ["Images analysed", ag.get("total_images", 0)],
                ["Images with ≥2 annotators", ag.get("images_with_multiple_annotators", 0)],
                ["IoU match threshold", ag.get("iou_match_threshold", 0.5)],
                ["Overall mean F1", ag.get("overall_mean_f1", "N/A")],
            ],
        ),
    ]

    per_ann = agr.get("per_annotator", {})
    if per_ann:
        lines.append("\n### Per-Annotator Agreement\n")
        ann_rows = [
            [ann, d.get("mean_f1", "N/A"), d.get("pair_count", 0)]
            for ann, d in per_ann.items()
        ]
        lines.append(_md_table(["Annotator", "Mean F1", "Pairs"], ann_rows))

    lines += [
        "\n\n---",
        "\n## 3. Review Queue\n",
        f"**{len(queue_rows)} image(s)** flagged for review.\n",
    ]

    if queue_rows:
        q_rows = [
            [
                r.get("image", ""),
                r.get("priority", ""),
                r.get("reason", ""),
                r.get("validation_status", ""),
                r.get("mean_agreement_f1", "N/A"),
            ]
            for r in queue_rows[:30]
        ]
        lines.append(_md_table(
            ["Image", "Priority", "Reason", "Validation", "Mean F1"],
            q_rows,
        ))

    lines.append("\n\n---\n_End of report_")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate QA report")
    parser.add_argument("--validation", default="reports/validation_report.json")
    parser.add_argument("--agreement", default="reports/agreement_summary.json")
    parser.add_argument("--queue", default="reports/review_queue.csv")
    parser.add_argument("--output", default="reports/annotation_report.md")
    args = parser.parse_args()

    val = load_json(args.validation)
    agr = load_json(args.agreement)

    queue_rows: list[dict] = []
    queue_path = Path(args.queue)
    if queue_path.exists():
        with open(queue_path, newline="", encoding="utf-8") as fh:
            queue_rows = list(csv.DictReader(fh))

    md = generate_markdown(val, agr, queue_rows)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(md, encoding="utf-8")
    log.info("Report → %s", args.output)


if __name__ == "__main__":
    main()
