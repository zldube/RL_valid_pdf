
# main.py
# One-command orchestrator:
# - Ensures a *boxes_template* exists (else tries to create it; else reports "no template found").
# - Extracts first-half JSON from the main PDF using the template.
# - Runs full-doc existence validation and right-place per-box validation.
# - Prints a human-readable summary and exits non-zero on failures (for CI).

import sys
from pathlib import Path
import json

from json_SL import load_json, save_json
from formatting import format_summary, summarize_full_doc
from validations import full_doc_checks, box_checks

# Internal modules (no own mains)
from json_work.python_files.build_template_from_pdf import write_template_for_boxes_pdf
from json_work.python_files.extract_boxes_to_json import extract_to_json


def _resolve_paths(pdf_path_arg: str):
    # Resolve core folders and paths used by the pipeline.
    pdf_path = Path(pdf_path_arg).resolve()
    json_work_root = Path("./json_work").resolve()
    jw_py = json_work_root / "python_files"
    jw_json = json_work_root / "json_files"
    jw_samples = json_work_root / "sample_pdfs"

    # Conventional names: <DOC>_boxes_template.json and <DOC>.first_half.json
    doc_base = pdf_path.stem
    tpl_path = jw_json / f"{doc_base}_boxes_template.json"
    first_half_json = jw_json / f"{doc_base}.first_half.json"
    boxes_pdf = jw_samples / f"{doc_base}_boxes.pdf"

    return pdf_path, tpl_path, first_half_json, boxes_pdf, jw_json


def _expected_values_and_mapping():
    # Expected values for first half of the doc (from your spec).
    expected_values = {
        "Title": "MR",
        "Surname": "UATjmfC",
        "First Name": "TDMjmfC",
        "Address": "Avenue Street",
        "City": "London",
        "Postcode": "W2 4BA",
        "Date 1": "29 November 2025",
        "Date 2": "26 November 2025",
        "Customer ID": "7700049486",
        "Pension Plan": "1000059054L",
        "Plan Value": "190,664.73",
        "Cash Withdrawal": "190,664.73",
        "Plan Value Post Withdrawal": "0.00",
        "Date 3": "27/11/2025"
    }

    # Box content expectations (keys are actual box names produced by the template).
    # Note: Your note used "Last Name" once; we alias it to "Surname" below.
    # Note: Your note used "CustomerID"; we alias it to "Customer ID".
    box_mapping = {
        "box_0_1": ["Title", "First Name", "Surname", "Address", "City", "Postcode"],
        "box_0_2": ["Date 1", "Customer ID"],
        "box_0_3": ["First Name", "Last Name"],
        "box_0_4": ["Pension Plan"],
        "box_0_5": ["Plan Value", "Cash Withdrawal", "Date 3", "Plan Value Post Withdrawal"],
        "box_0_6": ["Cash Withdrawal"],
        "box_0_7": ["Date 2"]
    }

    # Aliases to tolerate minor label differences.
    aliases = {
        "Last Name": "Surname",
        "CustomerID": "Customer ID"
    }

    return expected_values, box_mapping, aliases


def _ensure_template(tpl_path: Path, boxes_pdf: Path) -> Path:
    # Step 1: Ensure a "*boxes_template" JSON exists; try to build it from <DOC>_boxes.pdf if missing.
    if tpl_path.exists():
        return tpl_path

    if boxes_pdf.exists():
        out = write_template_for_boxes_pdf(str(boxes_pdf), tpl_path)
        print(f"[OK] Wrote template to: {out}")
        return out

    print("no template found")
    sys.exit(2)


def _extract_first_half(pdf_path: Path, tpl_path: Path, first_half_json: Path) -> Path:
    # Step 2: Use the template to extract information into <pdf>.first_half.json.
    out = extract_to_json(str(pdf_path), str(tpl_path), first_half_json, overwrite=True)
    print(f"[OK] Wrote extraction JSON: {out}")
    return out


def _validate(first_half_json: Path):
    # Step 3: Run full-doc and right-place validations using in-code expectations.
    data = load_json(first_half_json)
    if not data:
        print(f"[ERROR] Cannot load extraction JSON: {first_half_json}", file=sys.stderr)
        sys.exit(1)

    expected_values, box_mapping, aliases = _expected_values_and_mapping()

    full_text = data.get("full_text", "")
    boxes = data.get("boxes", {})

    checks = []
    checks.extend(full_doc_checks(expected_values, full_text))
    checks.extend(box_checks(expected_values, boxes, box_mapping, aliases))

    print(summarize_full_doc(checks))
    print(format_summary(checks))

    # Exit non-zero if any failures are present.
    any_fail = any(not c.get("pass") for c in checks)
    if any_fail:
        # Also print raw JSON for pipeline debugging if needed.
        print(json.dumps({"checks": checks}, indent=2))
        sys.exit(1)
    else:
        sys.exit(0)


def main():
    # Minimal CLI: python main.py <path_to_main_pdf>
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_main_pdf>")
        sys.exit(2)

    pdf_path_arg = sys.argv[1]
    pdf_path, tpl_path, first_half_json, boxes_pdf, jw_json = _resolve_paths(pdf_path_arg)

    if not jw_json.exists():
        print(f"[ERROR] Expected folder missing: {jw_json}", file=sys.stderr)
        sys.exit(2)

    tpl = _ensure_template(tpl_path, boxes_pdf)
    _extract_first_half(pdf_path, tpl, first_half_json)
    _validate(first_half_json)


if __name__ == "__main__":
   main()
