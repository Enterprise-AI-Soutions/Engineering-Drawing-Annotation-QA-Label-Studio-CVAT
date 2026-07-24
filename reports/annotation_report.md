# Engineering Drawing Annotation QA Report

_Generated: 2026-07-25 01:00_

---

## 1. Validation Summary

| Metric | Value |
| --- | --- |
| Total records | 6 |
| Passed | 5 |
| Failed | 1 |
| Pass rate | 83.3% |
| Total regions | 24 |

### Failed Records

| Image | Annotator | Issues |
| --- | --- | --- |
| valve_assembly_001.png | cvat_annotator@example.com | Region cvat_r011: bbox area 8000px² — please verify label correctness |

---

## 2. Inter-Annotator Agreement

| Metric | Value |
| --- | --- |
| Images analysed | 4 |
| Images with ≥2 annotators | 1 |
| IoU match threshold | 0.5 |
| Overall mean F1 | 0.82 |

### Per-Annotator Agreement

| Annotator | Mean F1 | Pairs |
| --- | --- | --- |
| annotator1@example.com | 0.82 | 1 |
| annotator2@example.com | 0.82 | 1 |

---

## 3. Review Queue

**5 image(s)** flagged for review.

| Image | Priority | Reason | Validation | Mean F1 |
| --- | --- | --- | --- | --- |
| valve_assembly_001.png | 1 | validation_failed | fail | N/A |
| piping_layout_001.png | 2 | low_agreement | pass | 0.667 |
| pump_layout_001.png | 3 | single_annotator_complex | pass | N/A |
| hydraulic_system_001.png | 3 | single_annotator_complex | pass | N/A |
| motor_wiring_001.png | 3 | single_annotator_complex | pass | N/A |

---
_End of report_
