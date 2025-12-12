import sys
import json
from datetime import datetime
from json_SL import load_json, save_json
from validations import validate_pdf, validate_p45, cross_validate
from formatting import format_results
from extract_to_json import extract_pdf_to_json  

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <pdf_path>", file=sys.stderr)
        sys.exit(2)

    pdf_path = sys.argv[1]
    json_filename = pdf_path.replace(".pdf", ".json")

    # Step 1: Load cached JSON or extract fresh data
    pdf_data = load_json(json_filename)
    
    if pdf_data is None:
        pdf_data = extract_pdf_to_json(pdf_path)
        save_json(pdf_data, json_filename)

    # Step 2: Access fields
    full_text = pdf_data.get("full_document", "")
    p45_text = pdf_data.get("p45_section", "")

    # Step 3: Validate the extracted PDF data
    if not validate_pdf(full_text, pdf_path):
        print(json.dumps({"PDF Validation": "FAIL"}))
        return

    expected_values = {
        "NI Number": "WM764243B",
        "Title": "MR",
        "Surname": "UATJMFC",
        "First Name": "TDMJMFC",
        "Leaving Date": "27 11 2025",
        "Tax Code": "1250L",
        "Total Pay to Date": "193,164.73",
        "Total Tax to Date": "85,305.15",
        "Date of Birth": "01 01 1995",
        "Address": "AVENUE STREET",
        "Postcode": "W2 4BA"
    }

    # Step 4: Validate P45 fields and cross-compare
    p45_validations = validate_p45(p45_text, expected_values)
    mismatches = cross_validate(full_text, p45_text, expected_values)

    # Step 5: Combine and print results
    validations = {**p45_validations, **mismatches}
    print(format_results(validations), file=sys.stderr)
    print(json.dumps(validations))

if __name__ == "__main__":
    main()
