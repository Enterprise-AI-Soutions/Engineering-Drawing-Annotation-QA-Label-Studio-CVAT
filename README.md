# Engineering Drawing Annotation QA
### Label Studio + CVAT + Python

---

## Overview

Engineering Drawing Annotation QA is a lightweight Python project that validates annotations exported from Label Studio and CVAT.

It simulates the workflow used by AI data annotation teams responsible for reviewing engineering drawings, industrial diagrams and manufacturing documentation.

Instead of performing annotation itself, the project validates annotation quality, compares reviewer agreement, generates review queues and produces QA reports.

---

## Features

✔ Label Studio JSON support

✔ CVAT XML support

✔ Common annotation schema

✔ Annotation validation

✔ Image existence validation

✔ Bounding box validation

✔ Reviewer agreement analysis

✔ Review queue generation

✔ Markdown reports

✔ JSON reports

✔ CSV reports

✔ Review image generation

✔ Unit tests

---

## Architecture

Engineering Drawings

↓

Label Studio / CVAT

↓

Export

↓

Normalization

↓

Validation

↓

Agreement Analysis

↓

Review Queue

↓

Reports

↓

Visualization

---

## Folder Structure

data/

Engineering drawings

↓

exports/

Label Studio

CVAT

↓

normalized/

Common annotation schema

↓

reports/

QA reports

↓

outputs/

Annotated review images

---

## Supported Annotation Tools

- Label Studio
- CVAT

---

## Technologies

Python

Label Studio

CVAT

Pillow

pytest

XML

JSON

CSV

Markdown

---

## Run

### Windows

```powershell
.\scripts\run_pipeline.ps1
```

### Linux / GitHub Codespaces

```bash
chmod +x scripts/run_pipeline.sh

./scripts/run_pipeline.sh
```

---

## Reports Generated

validation_report.json

agreement_summary.json

review_queue.csv

annotation_report.md

---

## Output

Automatically generated review images

QA reports

Reviewer agreement

Review queue

---

## Future Improvements

Polygon annotations

Segmentation masks

OCR annotations

Engineering symbol validation

Document layout analysis

---

## License

MIT
