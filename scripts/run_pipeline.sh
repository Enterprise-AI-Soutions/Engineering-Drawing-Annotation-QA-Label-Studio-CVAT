#!/usr/bin/env bash
# run_pipeline.sh — Full annotation QA pipeline for macOS / Linux
# Usage: bash scripts/run_pipeline.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/src"
DRAWINGS_DIR="$ROOT/data/drawings"

echo ""
echo "=== Engineering Drawing Annotation QA Pipeline ==="

# ── Pre-flight: verify drawings folder exists and contains images ─────────────
echo ""
echo "[CHECK] Verifying drawings folder..."

if [ ! -d "$DRAWINGS_DIR" ]; then
    echo ""
    echo "ERROR: Drawings folder not found: $DRAWINGS_DIR" >&2
    echo "" >&2
    echo "  Please create the folder and add your engineering drawing images:" >&2
    echo "    mkdir -p data/drawings" >&2
    echo "    # Copy your .png / .jpg / .tif files into data/drawings/" >&2
    echo "" >&2
    echo "  See README.md -> 'Adding Your Own Drawings' for details." >&2
    exit 1
fi

image_count=$(find "$DRAWINGS_DIR" -maxdepth 1 -type f \
    \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \
       -o -iname "*.tif" -o -iname "*.tiff" -o -iname "*.bmp" \) \
    | wc -l)

if [ "$image_count" -eq 0 ]; then
    echo "" >&2
    echo "ERROR: No drawing images found in: $DRAWINGS_DIR" >&2
    echo "" >&2
    echo "  The pipeline requires at least one image file." >&2
    echo "  Supported formats: .png  .jpg  .jpeg  .tif  .tiff  .bmp" >&2
    echo "" >&2
    echo "  Add your engineering drawings to data/drawings/ and re-run." >&2
    echo "  See README.md -> 'Adding Your Own Drawings' for details." >&2
    exit 1
fi

echo "  Found $image_count drawing image(s) in data/drawings/"

# ── Step 1: Convert Label Studio export ──────────────────────────────────────
echo ""
echo "[1/6] Converting Label Studio export..."
python "$SRC/convert_labelstudio.py" \
    --input  "$ROOT/data/exports/labelstudio/engineering_annotations.json" \
    --output "$ROOT/data/normalized/ls_annotations.json"

# ── Step 2: Convert CVAT export ──────────────────────────────────────────────
echo ""
echo "[2/6] Converting CVAT XML export..."
python "$SRC/convert_cvat.py" \
    --input  "$ROOT/data/exports/cvat/annotations.xml" \
    --output "$ROOT/data/normalized/cvat_annotations.json"

# ── Step 3: Merge and normalize ───────────────────────────────────────────────
echo ""
echo "[3/6] Merging and normalizing annotations..."
python "$SRC/normalize_annotations.py" \
    --inputs "$ROOT/data/exports/labelstudio/engineering_annotations.json" \
             "$ROOT/data/exports/cvat/annotations.xml" \
    --output "$ROOT/data/normalized/annotations.json"

# ── Step 4: Validate ──────────────────────────────────────────────────────────
echo ""
echo "[4/6] Validating annotations..."
python "$SRC/validate_annotations.py" \
    --input  "$ROOT/data/normalized/annotations.json" \
    --output "$ROOT/reports/validation_report.json"

# ── Step 5: Agreement analysis ────────────────────────────────────────────────
echo ""
echo "[5/6] Running inter-annotator agreement analysis..."
python "$SRC/agreement_analysis.py" \
    --input  "$ROOT/data/normalized/annotations.json" \
    --output "$ROOT/reports/agreement_summary.json"

# ── Step 6: Review queue + report ────────────────────────────────────────────
echo ""
echo "[6/6] Building review queue and generating report..."
python "$SRC/create_review_queue.py" \
    --validation "$ROOT/reports/validation_report.json" \
    --agreement  "$ROOT/reports/agreement_summary.json" \
    --output     "$ROOT/reports/review_queue.csv"

python "$SRC/generate_report.py" \
    --validation "$ROOT/reports/validation_report.json" \
    --agreement  "$ROOT/reports/agreement_summary.json" \
    --queue      "$ROOT/reports/review_queue.csv" \
    --output     "$ROOT/reports/annotation_report.md"

echo ""
echo "=== Pipeline complete! ==="
echo "  Normalized : $ROOT/data/normalized/annotations.json"
echo "  Validation : $ROOT/reports/validation_report.json"
echo "  Agreement  : $ROOT/reports/agreement_summary.json"
echo "  Queue      : $ROOT/reports/review_queue.csv"
echo "  Report     : $ROOT/reports/annotation_report.md"
