"""Tests for Label Studio and CVAT converters."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from convert_labelstudio import convert as ls_convert
from convert_cvat import convert as cvat_convert


# ── Label Studio ──────────────────────────────────────────────────────────────

SAMPLE_LS_TASK = [
    {
        "id": 1,
        "data": {"image": "/data/drawings/pump_layout_001.png"},
        "meta": {"width": 1920, "height": 1080},
        "annotations": [
            {
                "id": 10,
                "completed_by": {"email": "annotator1@example.com"},
                "result": [
                    {
                        "id": "r1",
                        "type": "rectanglelabels",
                        "value": {
                            "x": 10.0,
                            "y": 20.0,
                            "width": 15.0,
                            "height": 10.0,
                            "rectanglelabels": ["pump"],
                        },
                    }
                ],
            }
        ],
    }
]


def test_ls_convert_returns_dict():
    result = ls_convert(SAMPLE_LS_TASK)
    assert isinstance(result, dict)
    assert "annotations" in result
    assert "schema_version" in result


def test_ls_convert_total_records():
    result = ls_convert(SAMPLE_LS_TASK)
    assert result["total_records"] == 1


def test_ls_bbox_pixel_conversion():
    result = ls_convert(SAMPLE_LS_TASK)
    region = result["annotations"][0]["regions"][0]
    assert region["type"] == "bbox"
    x, y, w, h = region["bbox"]
    # 10% of 1920 = 192, 20% of 1080 = 216
    assert x == 192
    assert y == 216
    assert w == round(0.15 * 1920)
    assert h == round(0.10 * 1080)


def test_ls_label_extracted():
    result = ls_convert(SAMPLE_LS_TASK)
    region = result["annotations"][0]["regions"][0]
    assert region["label"] == "pump"


def test_ls_annotator_extracted():
    result = ls_convert(SAMPLE_LS_TASK)
    ann = result["annotations"][0]
    assert ann["annotator"] == "annotator1@example.com"


def test_ls_empty_input():
    result = ls_convert([])
    assert result["total_records"] == 0
    assert result["annotations"] == []


def test_ls_skips_tasks_without_annotations():
    task = [{"id": 99, "data": {"image": "x.png"}, "annotations": []}]
    result = ls_convert(task)
    assert result["total_records"] == 0


# ── CVAT ──────────────────────────────────────────────────────────────────────

SAMPLE_CVAT_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<annotations>
  <meta>
    <job>
      <assignee>cvat_user@example.com</assignee>
    </job>
  </meta>
  <image id="1" name="valve_assembly_001.png" width="1920" height="1080">
    <box label="valve" xtl="100" ytl="200" xbr="300" ybr="400" occluded="0"/>
    <polygon label="pipe" points="50,50;150,50;100,150" occluded="0"/>
  </image>
</annotations>
"""


def test_cvat_convert_returns_dict(tmp_path):
    xml_file = tmp_path / "annotations.xml"
    xml_file.write_text(SAMPLE_CVAT_XML, encoding="utf-8")
    result = cvat_convert(str(xml_file))
    assert isinstance(result, dict)
    assert "annotations" in result


def test_cvat_total_records(tmp_path):
    xml_file = tmp_path / "annotations.xml"
    xml_file.write_text(SAMPLE_CVAT_XML, encoding="utf-8")
    result = cvat_convert(str(xml_file))
    assert result["total_records"] == 1


def test_cvat_box_parsed(tmp_path):
    xml_file = tmp_path / "annotations.xml"
    xml_file.write_text(SAMPLE_CVAT_XML, encoding="utf-8")
    result = cvat_convert(str(xml_file))
    regions = result["annotations"][0]["regions"]
    boxes = [r for r in regions if r["type"] == "bbox"]
    assert len(boxes) == 1
    x, y, w, h = boxes[0]["bbox"]
    assert x == 100 and y == 200 and w == 200 and h == 200


def test_cvat_polygon_parsed(tmp_path):
    xml_file = tmp_path / "annotations.xml"
    xml_file.write_text(SAMPLE_CVAT_XML, encoding="utf-8")
    result = cvat_convert(str(xml_file))
    regions = result["annotations"][0]["regions"]
    polys = [r for r in regions if r["type"] == "polygon"]
    assert len(polys) == 1
    assert len(polys[0]["polygon"]) == 3


def test_cvat_annotator_from_meta(tmp_path):
    xml_file = tmp_path / "annotations.xml"
    xml_file.write_text(SAMPLE_CVAT_XML, encoding="utf-8")
    result = cvat_convert(str(xml_file))
    assert result["annotations"][0]["annotator"] == "cvat_user@example.com"
