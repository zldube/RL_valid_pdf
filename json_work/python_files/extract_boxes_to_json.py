
# #!/usr/bin/env python3
# """
# Extract text inside normalized-box regions defined by a template JSON, and write
# an extraction JSON into ../json_files.

# - Reads boxes from a template JSON (normalized 0..1 coords).
# - Denormalizes per target PDF page width/height.
# - Intersects words inside each box (reading order top->bottom, left->right).
# - Writes <pdf_basename>.first_half.json into ../json_files by default.
# - Avoids FileExistsError via --overwrite or auto-suffixing.

# Usage (PowerShell from json_work/python_files):
#     python .\extract_boxes_to_json.py --pdf ..\sample_pdfs\REAL_DOC.pdf --template ..\json_files\UMS025_boxes_template.json
#     # Optional explicit out path:
#     python .\extract_boxes_to_json.py --pdf ..\sample_pdfs\REAL_DOC.pdf --template ..\json_files\UMS025_boxes_template.json --out ..\json_files\REAL_DOC.first_half.json
#     # Overwrite existing file:
#     python .\extract_boxes_to_json.py --pdf ..\sample_pdfs\REAL_DOC.pdf --template ..\json_files\UMS025_boxes_template.json --overwrite
# """

import json
import argparse
from pathlib import Path
import pdfplumber


def denorm(box, w, h):
    """Convert normalized [x0,y0,x1,y1] into absolute coordinates for this page."""
    return (box[0] * w, box[1] * h, box[2] * w, box[3] * h)


def intersects(b, wdict):
    """Axis-aligned rectangle intersection: box b vs word dict from pdfplumber."""
    x0, y0, x1, y1 = b
    return not (wdict["x1"] < x0 or wdict["x0"] > x1 or wdict["bottom"] < y0 or wdict["top"] > y1)


def resolve_default_out(pdf_path: str) -> Path:
    """
    Default output path:
      ../json_files/<pdf_basename>.first_half.json
    relative to this script.
    """
    script_dir = Path(__file__).resolve().parent
    json_files_dir = (script_dir / ".." / "json_files").resolve()
    if not json_files_dir.exists():
        raise FileNotFoundError(
            f"Expected output folder does not exist: {json_files_dir}\n"
            f"Create json_work\\json_files before running."
        )
    base = Path(pdf_path).stem
    return json_files_dir / f"{base}.first_half.json"


def safe_write_json(obj, out_path: Path, overwrite: bool = False) -> Path:
    """Write JSON safely: overwrite if requested, else auto-suffix to avoid FileExistsError."""
    out_path = out_path.resolve()
    if out_path.exists() and not overwrite:
        i = 1
        while True:
            alt = out_path.with_name(out_path.stem + f"_{i}").with_suffix(".json")
            if not alt.exists():
                out_path = alt
                break
            i += 1
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    return out_path


def run(pdf_path: str, template_path: str, out_path: str = None, overwrite: bool = False):
    # Load template
    with open(template_path, "r", encoding="utf-8") as f:
        template = json.load(f)

    # Prepare extraction skeleton
    extraction = {
        "doc_path": str(Path(pdf_path).resolve()),
        "doc_type": template.get("doc_type"),
        "boxes": {},
        "full_text": ""
    }

    # Extract per page/box
    with pdfplumber.open(pdf_path) as pdf:
        # Compose full_text only for pages enumerated in template (first two pages)
        full_text_parts = []
        for page_entry in template["pages"]:
            pnum = page_entry["page_num"]
            t = pdf.pages[pnum].extract_text() or ""
            full_text_parts.append(t)
        extraction["full_text"] = "\n".join(full_text_parts)

        # Extract text in each box
        for page_entry in template["pages"]:
            pnum = page_entry["page_num"]
            page = pdf.pages[pnum]
            w, h = page.width, page.height
            words = page.extract_words() or []

            for field in page_entry.get("fields", []):
                x0, y0, x1, y1 = denorm(field["box"], w, h)
                in_box = [wd for wd in words if intersects((x0, y0, x1, y1), wd)]
                in_box.sort(key=lambda wd: (wd["top"], wd["x0"]))
                text = " ".join(wd["text"] for wd in in_box).strip()
                extraction["boxes"][field["name"]] = {
                    "page": pnum,
                    "raw_text": text,
                    "count_words": len(in_box),
                    "box_denorm": [x0, y0, x1, y1]  # handy for debugging later
                }

    # Resolve output path
    final_out = Path(out_path) if out_path else resolve_default_out(pdf_path)
    final_out = safe_write_json(extraction, final_out, overwrite=overwrite)
    print(f"[OK] Wrote extraction JSON: {final_out}")


def main():
    ap = argparse.ArgumentParser(description="Extract text inside template-defined boxes into JSON.")
    ap.add_argument("--pdf", required=True, help="Target PDF (without red boxes).")
    ap.add_argument("--template", required=True, help="Template JSON with normalized boxes.")
    ap.add_argument("--out", help="Output JSON path (default ../json_files/<pdf_basename>.first_half.json).")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite output if it already exists.")
    args = ap.parse_args()
    run(args.pdf, args.template, args.out, args.overwrite)


if __name__ == "__main__":
    main()
