#!/usr/bin/env pwsh
# run_pipeline.ps1 — Full annotation QA pipeline for Windows (PowerShell)
# Usage: .\scripts\run_pipeline.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = Split-Path -Parent $PSScriptRoot
$SRC  = "$ROOT\src"

Write-Host "`n=== Engineering Drawing Annotation QA Pipeline ===" -ForegroundColor Cyan

# ── Step 1: Convert Label Studio export ──────────────────────────────────────
Write-Host "`n[1/6] Converting Label Studio export..." -ForegroundColor Yellow
python "$SRC\convert_labelstudio.py" `
    --input  "$ROOT\data\exports\labelstudio\engineering_annotations.json" `
    --output "$ROOT\data\normalized\ls_annotations.json"

# ── Step 2: Convert CVAT export ──────────────────────────────────────────────
Write-Host "`n[2/6] Converting CVAT XML export..." -ForegroundColor Yellow
python "$SRC\convert_cvat.py" `
    --input  "$ROOT\data\exports\cvat\annotations.xml" `
    --output "$ROOT\data\normalized\cvat_annotations.json"

# ── Step 3: Merge and normalize ───────────────────────────────────────────────
Write-Host "`n[3/6] Merging and normalizing annotations..." -ForegroundColor Yellow
python "$SRC\normalize_annotations.py" `
    --inputs "$ROOT\data\exports\labelstudio\engineering_annotations.json" `
             "$ROOT\data\exports\cvat\annotations.xml" `
    --output "$ROOT\data\normalized\annotations.json"

# ── Step 4: Validate ──────────────────────────────────────────────────────────
Write-Host "`n[4/6] Validating annotations..." -ForegroundColor Yellow
python "$SRC\validate_annotations.py" `
    --input  "$ROOT\data\normalized\annotations.json" `
    --output "$ROOT\reports\validation_report.json"

# ── Step 5: Agreement analysis ────────────────────────────────────────────────
Write-Host "`n[5/6] Running inter-annotator agreement analysis..." -ForegroundColor Yellow
python "$SRC\agreement_analysis.py" `
    --input  "$ROOT\data\normalized\annotations.json" `
    --output "$ROOT\reports\agreement_summary.json"

# ── Step 6: Review queue + report ────────────────────────────────────────────
Write-Host "`n[6/6] Building review queue and generating report..." -ForegroundColor Yellow
python "$SRC\create_review_queue.py" `
    --validation "$ROOT\reports\validation_report.json" `
    --agreement  "$ROOT\reports\agreement_summary.json" `
    --output     "$ROOT\reports\review_queue.csv"

python "$SRC\generate_report.py" `
    --validation "$ROOT\reports\validation_report.json" `
    --agreement  "$ROOT\reports\agreement_summary.json" `
    --queue      "$ROOT\reports\review_queue.csv" `
    --output     "$ROOT\reports\annotation_report.md"

Write-Host "`n=== Pipeline complete! ===" -ForegroundColor Green
Write-Host "  Normalized : $ROOT\data\normalized\annotations.json"
Write-Host "  Validation : $ROOT\reports\validation_report.json"
Write-Host "  Agreement  : $ROOT\reports\agreement_summary.json"
Write-Host "  Queue      : $ROOT\reports\review_queue.csv"
Write-Host "  Report     : $ROOT\reports\annotation_report.md"
