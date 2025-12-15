
# json_work/python_files/extract_boxes_to_json.py
from pathlib import Path
from typing import Dict, List
import json
import pdfplumber 


def _denorm(box: List[float], w: float, h: float) -> tuple:
    return (box[0] * w, box[1] * h, box[2] * w, box[3] * h)


def _intersects(b: tuple, wdict: Dict) -> bool:
    x0, y0, x1, y1 = b
    return not (wdict["x1"] < x0 or wdict["x0"] > x1 or wdict["bottom"] < y0 or wdict["top"] > y1)


def extract_to_json(pdf_path: str, template_path: str, out_path: Path, overwrite: bool = True) -> Path:
    # Load template
    with open(template_path, "r", encoding="utf-8") as f:
        template = json.load(f)

    extraction = {
        "doc_path": str(Path(pdf_path).resolve()),
        "doc_type": template.get("doc_type"),
        "boxes": {},
        "full_text": ""
    }

    # Extract content
    with pdfplumber.open(pdf_path) as pdf:
        # Full text (first two pages per template)
        full_text_parts = []
        for page_entry in template.get("pages", []):
            pnum = page_entry["page_num"]
            t = pdf.pages[pnum].extract_text() or ""
            full_text_parts.append(t)
        extraction["full_text"] = "\n".join(full_text_parts)

        # Boxes
        for page_entry in template.get("pages", []):
            pnum = page_entry["page_num"]
            page = pdf.pages[pnum]
            w, h = page.width, page.height
            words = page.extract_words() or []

            for field in page_entry.get("fields", []):
                x0, y0, x1, y1 = _denorm(field["box"], w, h)
                in_box = [wd for wd in words if _intersects((x0, y0, x1, y1), wd)]
                in_box.sort(key=lambda wd: (wd["top"], wd["x0"]))
                text = " ".join(wd["text"] for wd in in_box).strip()

                extraction["boxes"][field["name"]] = {
                    "page": pnum,
                    "raw_text": text,
                    "count_words": len(in_box),
                    "box_denorm": [x0, y0, x1, y1]
                }

    # Write JSON
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and not overwrite:
        i = 1
        while True:
            alt = out_path.with_name(out_path.stem + f"_{i}").with_suffix(".json")
            if not alt.exists():
                out_path = alt
                break
            i += 1

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(extraction, f, indent=2)

