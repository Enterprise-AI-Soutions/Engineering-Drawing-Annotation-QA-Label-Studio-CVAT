# Engineering Drawing Annotation QA

[![CI](https://github.com/Enterprise-AI-Soutions/Engineering-Drawing-Annotation-QA-Label-Studio-CVAT/actions/workflows/ci.yml/badge.svg)](https://github.com/Enterprise-AI-Soutions/Engineering-Drawing-Annotation-QA-Label-Studio-CVAT/actions)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

A lightweight, **zero-heavy-dependency** Python pipeline for converting, validating, and quality-assuring annotations on engineering drawings exported from **Label Studio** and **CVAT**.

---

## ⚠️ Before You Run

**The pipeline requires your engineering drawing images to be present in `data/drawings/`.**  
It will refuse to run and display a clear error if that folder is missing or empty.

```
ERROR: No drawing images found in: data/drawings/
  The pipeline requires at least one image file (.png, .jpg, .tif, .tiff).
  Add your engineering drawings to that folder and re-run.
  See README.md -> 'Adding Your Own Drawings' for details.
```

See [Adding Your Own Drawings](#adding-your-own-drawings) below.

---

## What It Does

| Step | Script | Input | Output |
|---|---|---|---|
| 1. Convert Label Studio | `convert_labelstudio.py` | LS JSON export | Normalized JSON |
| 2. Convert CVAT | `convert_cvat.py` | CVAT XML export | Normalized JSON |
| 3. Merge & Normalize | `normalize_annotations.py` | Any of the above | Unified JSON |
| 4. Validate | `validate_annotations.py` | Normalized JSON | `validation_report.json` |
| 5. Agreement Analysis | `agreement_analysis.py` | Normalized JSON | `agreement_summary.json` |
| 6. Review Queue | `create_review_queue.py` | Reports | `review_queue.csv` |
| 7. Report | `generate_report.py` | Reports + queue | `annotation_report.md` |
| 8. Visualise | `draw_annotations.py` | Normalized JSON + images | Annotated PNGs |

---

## Repository Structure

```
Engineering-Drawing-Annotation-QA/
│
├── .github/
│   └── workflows/ci.yml              # GitHub Actions — test on Python 3.10/3.11/3.12
│
├── data/
│   ├── drawings/                      # ← Your engineering drawing images go here
│   │   ├── pump_layout_001.png        #   (pipeline will not run without these)
│   │   ├── piping_layout_001.png
│   │   ├── gearbox_section_001.png
│   │   ├── hydraulic_system_001.png
│   │   ├── motor_wiring_001.png
│   │   ├── electrical_panel_001.png
│   │   ├── valve_assembly_001.png
│   │   ├── compressor_layout_001.png
│   │   └── process_flow_001.png
│   ├── exports/
│   │   ├── labelstudio/
│   │   │   └── engineering_annotations.json   # Label Studio JSON export
│   │   └── cvat/
│   │       └── annotations.xml                # CVAT XML export
│   └── normalized/
│       └── annotations.json                   # Merged normalized output
│
├── outputs/
│   └── review_images/                 # Annotated images written by draw_annotations.py
│
├── reports/
│   ├── validation_report.json         # Per-record validation results
│   ├── agreement_summary.json         # Inter-annotator F1 scores
│   ├── review_queue.csv               # Prioritised images for review
│   └── annotation_report.md           # Full Markdown QA report
│
├── scripts/
│   ├── run_pipeline.ps1               # Windows (PowerShell)
│   └── run_pipeline.sh                # macOS / Linux (Bash)
│
├── src/
│   ├── convert_labelstudio.py
│   ├── convert_cvat.py
│   ├── normalize_annotations.py
│   ├── validate_annotations.py
│   ├── agreement_analysis.py
│   ├── create_review_queue.py
│   ├── generate_report.py
│   ├── draw_annotations.py
│   ├── utils.py
│   └── __init__.py
│
├── tests/
│   ├── test_converter.py
│   ├── test_validation.py
│   ├── test_agreement.py
│   ├── test_reports.py
│   └── test_images.py
│
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── pyproject.toml
```

---

## Adding Your Own Drawings

> **The pipeline will not run without drawings.** This is intentional — running without images produces meaningless output.

**Step 1 — Add your drawings:**

```
data/drawings/
    your_drawing_001.png
    your_drawing_002.png
    ...
```

Accepted formats: `.png` `.jpg` `.jpeg` `.tif` `.tiff` `.bmp`

**Step 2 — Annotate them in Label Studio or CVAT:**

| Tool | How to export | Save to |
|---|---|---|
| **Label Studio** | Project → Export → **JSON** | `data/exports/labelstudio/engineering_annotations.json` |
| **CVAT** | Actions → Export dataset → **CVAT for Images 1.1** (XML) | `data/exports/cvat/annotations.xml` |

> The filename inside the annotation export (e.g. `"image": "your_drawing_001.png"`) must exactly match the filename in `data/drawings/`.

---

## Quick Start

### Requirements

- Python 3.10+
- No mandatory external libraries — the full pipeline uses only the Python standard library
- `Pillow` is optional (only for `draw_annotations.py`)

### 1. Clone & install

```bash
git clone https://github.com/Enterprise-AI-Soutions/Engineering-Drawing-Annotation-QA-Label-Studio-CVAT.git
cd Engineering-Drawing-Annotation-QA
pip install -r requirements.txt
```

### 2. Add your drawings and annotation exports

See [Adding Your Own Drawings](#adding-your-own-drawings) above.

### 3. Run the full pipeline

**Windows (PowerShell):**

```powershell
.\scripts\run_pipeline.ps1
```

**macOS / Linux:**

```bash
bash scripts/run_pipeline.sh
```

### 4. Run individual steps

**Convert Label Studio export:**

```bash
python src/convert_labelstudio.py \
    --input  data/exports/labelstudio/engineering_annotations.json \
    --output data/normalized/annotations.json
```

**Convert CVAT XML export:**

```bash
python src/convert_cvat.py \
    --input  data/exports/cvat/annotations.xml \
    --output data/normalized/annotations.json
```

**Merge multiple sources:**

```bash
python src/normalize_annotations.py \
    --inputs data/exports/labelstudio/engineering_annotations.json \
             data/exports/cvat/annotations.xml \
    --output data/normalized/annotations.json
```

**Validate:**

```bash
python src/validate_annotations.py \
    --input  data/normalized/annotations.json \
    --output reports/validation_report.json
```

**Inter-annotator agreement:**

```bash
python src/agreement_analysis.py \
    --input  data/normalized/annotations.json \
    --output reports/agreement_summary.json
```

**Build review queue:**

```bash
python src/create_review_queue.py \
    --validation reports/validation_report.json \
    --agreement  reports/agreement_summary.json \
    --output     reports/review_queue.csv
```

**Generate full report:**

```bash
python src/generate_report.py \
    --validation reports/validation_report.json \
    --agreement  reports/agreement_summary.json \
    --queue      reports/review_queue.csv \
    --output     reports/annotation_report.md
```

**Draw annotations on images (requires Pillow):**

```bash
python src/draw_annotations.py \
    --annotations data/normalized/annotations.json \
    --drawings    data/drawings \
    --output      outputs/review_images
```

---

## Running Tests

```bash
pytest tests/ -v
```

With coverage:

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## Annotation Classes

| Class | Description |
|---|---|
| `pump` | Centrifugal, gear, or positive displacement pumps |
| `valve` | Gate, ball, check, control valves |
| `pipe` | Pipes, tubes, conduits |
| `motor` | Electric motors |
| `compressor` | Air/gas compressors |
| `sensor` | Pressure, flow, temperature sensors |
| `tank` | Storage tanks and vessels |
| `fitting` | Elbows, tees, reducers |
| `junction` | Pipe junctions and manifolds |
| `label_text` | Text labels on drawings |
| `dimension` | Dimension lines and annotations |
| `wiring` | Electrical wiring |
| `panel` | Electrical panels |
| `switch` | Electrical switches |
| `relay` | Relays and contactors |

---

## Normalized Annotation Format

```json
{
  "schema_version": "1.0",
  "source": "merged",
  "total_records": 6,
  "annotations": [
    {
      "id": "ann_a1b2c3d4",
      "image": "pump_layout_001.png",
      "annotator": "annotator1@example.com",
      "source": "labelstudio",
      "image_width": 1920,
      "image_height": 1080,
      "regions": [
        {
          "id": "ls_r001",
          "label": "pump",
          "type": "bbox",
          "bbox": [192, 162, 230, 86],
          "confidence": 1.0
        }
      ]
    }
  ]
}
```

---

## Supported Export Formats

| Tool | Format | Notes |
|---|---|---|
| **Label Studio** | JSON | Rectangle labels, polygon labels. Percentages converted to pixels. |
| **CVAT** | XML (v1.1) | `<box>` and `<polygon>` elements. Annotator read from `<meta>`. |

---

## License

MIT — see [LICENSE](LICENSE)
