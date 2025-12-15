
# json_work/python_files/build_template_from_pdf.py
# Build a JSON template from rectangles drawn in a "boxes" PDF.
# Exposes functions only; orchestrated by main.py.

from pathlib import Path
from typing import Dict, List
import json

# PyMuPDF (fitz) is expected to be available in the runtime environment.
import fitz  # type: ignore


def _normalize_rect(rect, page_w: float, page_h: float) -> List[float]:
    # Convert absolute rect to normalized [x0, y0, x1, y1] in 0..1 range.
    return [rect.x0 / page_w, rect.y0 / page_h, rect.x1 / page_w, rect.y1 / page_h]


def build_template_first_two_pages(pdf_path: str) -> Dict:
    # Create a template dict from the first two pages of a "boxes" PDF.
    doc = fitz.open(pdf_path)
    pages_to_process = min(2, len(doc))
    template = {
        "doc_type": Path(pdf_path).stem.replace("_boxes", ""),
        "units": "normalized",
        "pages": []
    }

    for page_index in range(pages_to_process):
        page = doc[page_index]
        w, h = page.rect.width, page.rect.height
        page_entry = {"page_num": page_index, "fields": [], "tables": []}

        for idx, d in enumerate(page.get_drawings() or []):
            rect = d.get("rect")
            width = d.get("width")
            items = d.get("items", [])
            if rect is None or width is None:
                continue

            # Keep only rectangles (path command 're') with non-trivial area.
            is_rect = any(it[0] == "re" for it in items)
            if not is_rect:
                continue

            area = (rect.x1 - rect.x0) * (rect.y1 - rect.y0)
            if area < 1500:
                continue

            box_norm = _normalize_rect(rect, w, h)
            page_entry["fields"].append({
                "name": f"box_{page_index}_{idx}",
                "annotation_type": "RectangleDrawn",
                "box": box_norm,
                "extractor": "words",
                "parsers": []
            })

        template["pages"].append(page_entry)

    return template


def write_template_for_boxes_pdf(pdf_path: str, out_path: Path) -> Path:
    # Build and write the template JSON to out_path.
    template = build_template_first_two_pages(pdf_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)
    return out_path

