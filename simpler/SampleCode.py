
# SampleCode.py
# - Ensures extracted JSON exists (creates it if missing by calling extract_to_json).
# - Validates that expected values appear somewhere in the full document.
# - Prints a human-friendly summary and machine-readable JSON.
# No templates, no coordinates, no page/box logic.

import json
import sys
from pathlib import Path

from extract_to_json import extract_pdf_to_structured_json, expected_values


def contains(haystack: str, needle: str) -> bool:
    # Case-insensitive containment check with basic None safety.
    return (needle or "").lower() in (haystack or "").lower()


def format_summary(validations: dict) -> str:
    # Pretty-print PASS/FAIL per field.
    header = "\n📋 PDF VALIDATION RESULTS\n" + "=" * 60 + "\n"
    passed = []
    failed = []
    for k, v in validations.items():
        if v.startswith("PASS"):
            passed.append(f"  ✓ {k}: {v}")
        else:
            failed.append(f"  ✗ {k}: {v}")

    out = [header]
    if passed:
        out.append("PASSED:")
        out.extend(passed)
    if failed:
        out.append("\nFAILED:")
        out.extend(failed)
    out.append("\n" + "=" * 60 + "\n")
    return "\n".join(out)


def validate_full_document(full_document: str, exp: dict) -> dict:
    # Produce a dict of PASS/FAIL messages per expected field.
    results = {}
    for label, value in exp.items():
        ok = contains(full_document, value)
        results[label] = "PASS" if ok else f"FAIL - Expected '{value}'"

    return results


def main():
    # Usage: python SampleCode.py <pdf_path>
    # JSON will be created in ./json_work/json_files/<PDF_NAME>.json (if missing).
    if len(sys.argv) < 2:
        print("Usage: python SampleCode.py <pdf_path>")
        sys.exit(2)

    pdf_path = Path(sys.argv[1]).resolve()
    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        sys.exit(2)

    # Where we store the extracted JSON (in the same folder as PDF)
    json_out_path = pdf_path.with_suffix('.json')

    # Create the JSON if it doesn't exist
    if not json_out_path.exists():
        print("Step 1: Extracting PDF to JSON...")
        created = extract_pdf_to_structured_json(str(pdf_path), str(json_out_path))
        print(f"[OK] Saved JSON to {created}")

    # Load the JSON
    print("Step 2: Loading JSON for validation...")
    with json_out_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    full_document = data.get("full_document", "") or ""
    if not full_document.strip():
        print("ERROR: JSON has empty 'full_document'")
        sys.exit(2)

    # Run validations
    print("Step 3: Validating expected values in full document...")
    exp = expected_values()
    results = validate_full_document(full_document, exp)

    # Print human-friendly summary
    print(format_summary(results))

    # Also print machine-readable JSON
    print(json.dumps(results, indent=2))

    # Exit code: 0 if all PASS, 1 otherwise
    any_fail = any(val.startswith("FAIL") for val in results.values())
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
