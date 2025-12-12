
# #!/usr/bin/env python3
# """
# Build a JSON template from a PDF using ONLY drawn rectangles (vector path 're').
# - Ignores highlights / other annotation types.
# - Processes ONLY the first 2 pages.
# - Stores normalized coordinates (0..1) so later extraction is robust.

# Output:
# - Writes to ../json_files/<pdf_basename>_template.json relative to this script.
# - Expects ../json_files to already exist (no folder creation).
# """

import json
import argparse
from pathlib import Path
import fitz  # PyMuPDF


def normalize_rect(rect, page_w, page_h):
    return [rect.x0 / page_w, rect.y0 / page_h, rect.x1 / page_w, rect.y1 / page_h]


def build_template_first_two_pages(pdf_path: str):
    doc = fitz.open(pdf_path)
    pages_to_process = min(2, len(doc))
    template = {
        "doc_type": Path(pdf_path).stem,
        "units": "normalized",
        "pages": []
    }

    for page_index in range(pages_to_process):
        page = doc[page_index]
        w, h = page.rect.width, page.rect.height
        page_entry = {"page_num": page_index, "fields": [], "tables": []}

        # Scan drawn shapes and keep rectangles ('re') with a stroke width (outline rectangle).
        for idx, d in enumerate(page.get_drawings()):
            rect = d.get("rect")
            width = d.get("width")
            items = d.get("items", [])
            if rect is None or width is None:
                continue
            # Keep only rectangles (path command 're')
            is_rect = any(it[0] == "re" for it in items)
            if not is_rect:
                continue
            # Skip tiny boxes / lines (heuristic threshold)
            area = (rect.x1 - rect.x0) * (rect.y1 - rect.y0)
            if area < 1500:
                continue

            box_norm = normalize_rect(rect, w, h)
            page_entry["fields"].append({
                "name": f"box_{page_index}_{idx}",
                "annotation_type": "RectangleDrawn",
                "box": box_norm,
                "extractor": "words",
                "parsers": []
            })

        template["pages"].append(page_entry)

    return template


def resolve_output_path_in_json_files(pdf_path: str) -> Path:
    # ../json_files/<pdf_basename>_template.json
    script_dir = Path(__file__).resolve().parent
    json_files_dir = (script_dir / ".." / "json_files").resolve()
    if not json_files_dir.exists():
        raise FileNotFoundError(
            f"Expected output folder does not exist: {json_files_dir}\n"
            f"Create it before running."
        )
    base = Path(pdf_path).stem
    return json_files_dir / f"{base}_template.json"


def main():
    ap = argparse.ArgumentParser(
        description="Build JSON template from drawn rectangles on first 2 pages."
    )
    ap.add_argument("--pdf", required=True, help="Path to the PDF with drawn boxes.")
    args = ap.parse_args()

    pdf_arg = str(Path(args.pdf))
    template = build_template_first_two_pages(pdf_arg)

    # Quick sanity warnings
    for p in template["pages"]:
        names = [f["name"] for f in p["fields"]]
        dups = {n for n in names if n and names.count(n) > 1}
        if dups:
            print(f"[WARN] Page {p['page_num']} duplicate field names: {sorted(dups)}")

    out_path = resolve_output_path_in_json_files(pdf_arg)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)
    print(f"[OK] Wrote template to: {out_path}")


if __name__ == "__main__":
    main()
