
# extract_to_json.py

from datetime import datetime
from pypdf import PdfReader
import pdfplumber
import os

def _get_page_rotation(reader, page_index):
    """Get page rotation for reference (0/90/180/270)."""
    try:
        page = reader.pages[page_index]
        rot = getattr(page, "rotation", 0)
        return int(rot) if rot else 0
    except Exception:
        return 0

def extract_pdf_lines_layout(pdf_path, x_tol=1.0, y_tol=1.0, line_tol=2.0):
    """
    Extract PDF into a layout JSON (line-by-line).
    Each textItem = {"text": <line>, "x": <left>, "y": <bottom-origin y>, "page": <pageNumber>}
    """
    layout = {"pages": []}
    reader = PdfReader(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            height = float(page.height)
            rotation = _get_page_rotation(reader, page_idx)

            # Extract words, then group into lines
            words = page.extract_words(x_tolerance=x_tol, y_tolerance=y_tol)
            ordered = sorted(words, key=lambda w: (-float(w["top"]), float(w["x0"])))

            lines = []
            current_line = []
            current_line_top = None

            for w in ordered:
                x0 = float(w["x0"])
                top = float(w["top"])

                if current_line_top is None:
                    current_line_top = top
                    current_line = [{"text": w["text"], "x0": x0, "top": top}]
                else:
                    if abs(top - current_line_top) <= line_tol:
                        current_line.append({"text": w["text"], "x0": x0, "top": top})
                    else:
                        lines.append(current_line)
                        current_line_top = top
                        current_line = [{"text": w["text"], "x0": x0, "top": top}]
            if current_line:
                lines.append(current_line)

            # Convert lines to textItems (minimal fields: text, x, y, page)
            text_items = []
            for line_words in lines:
                line_text = " ".join(w["text"] for w in line_words)
                x_min = min(w["x0"] for w in line_words)
                top_min = min(w["top"] for w in line_words)
                y_bottom_origin = float(height - top_min)

                text_items.append({
                    "text": line_text,
                    "x": round(x_min, 3),
                    "y": round(y_bottom_origin, 3),
                    "page": page_idx + 1
                })

            layout["pages"].append({
                "pageNumber": page_idx + 1,
                "rotation": rotation,
                "textItems": text_items
            })

    return layout

def extract_pdf_to_json(pdf_path, p45_start_page=6):
    """
    The JSON that main.py will use to run:
      - full_document: plain text joined from all lines - (do we need this???)
      - p45_section: plain text joined from lines from p45_start_page onwards - (do we need this???)
      - layout: the line-by-line coordinates (for later positional validation)
    """
    layout = extract_pdf_lines_layout(pdf_path)

    full_text_lines = []
    p45_text_lines = []

    for page in layout["pages"]:
        page_num = page["pageNumber"]
        lines_on_page = [item["text"] for item in page["textItems"]]
        full_text_lines.extend(lines_on_page)
        if page_num >= p45_start_page:
            p45_text_lines.extend(lines_on_page)

    return {
        "filename": os.path.basename(pdf_path),
        "extraction_date": datetime.now().isoformat(),
        "full_document": "\n".join(full_text_lines),
        "p45_section": "\n".join(p45_text_lines),
        "layout": layout
    }
