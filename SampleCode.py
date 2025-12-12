# import { execSync } from "child_process";
# import path from "path";


# When(/^I validate the PDF document "(.+)"$/, async function (pdfName: string) {
#     const pdfPath = `./${pdfName}.pdf`;
#     validatePdf(pdfPath);
# });


# export const validatePdf = (pdfFilePath: string): Record<string, string> => {
#     try {
#         const absolutePath = path.resolve(pdfFilePath);
#         const pythonPath = `"C:\\Python312\\python.exe"`;

#         const result = execSync(
#             `${pythonPath} ./validate_pdf.py "${absolutePath}"`,
#             { encoding: "utf8" }
#         );

#         const parsed: Record<string, string> = JSON.parse(result);

#         console.log("🔍 PDF Validation Output:");
#         console.table(parsed);

#         // Perform assertion for each field
#         for (const [field, value] of Object.entries(parsed)) {
#             if (!value.includes("PASS")) {
#                 throw new Error(`❌ Validation failed for ${field}: ${value}`);
#             }
#         }

#         return parsed;

#     } catch (error) {
#         console.error("❌ PDF validation script failed:", error);
#         throw error;
#     }
# };


# And I validate the PDF document "UMS025"

import pdfplumber
import sys
import re
import json
import os
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from datetime import datetime
from extract_to_json import extract_pdf_lines_layout

def extract_pdf_to_json(pdf_path):
    """Extract all PDF data into a structured JSON object (plus layout)."""
    pdf_data = {
        "filename": os.path.basename(pdf_path),
        "extraction_date": datetime.now().isoformat(),
        "tables": [],
        "layout": extract_pdf_lines_layout(pdf_path)
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    pdf_data["tables"].append({
                        "page": page_num,
                        "data": table
                    })

    return pdf_data


def save_json(data, filename):
    """Save data as JSON file"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ JSON saved to {filename}", file=sys.stderr)

def load_json(filename):
    """Load existing JSON if present"""
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def validate_pdf(fulltext, pdf_path):
    """Validate file is readable PDF and has content"""
    try:
        PdfReader(pdf_path)
    except PdfReadError:
        print("Invalid PDF file", file=sys.stderr)
        return False

    if fulltext and fulltext.strip():
        return True
    else:
        print("No data found in PDF extraction", file=sys.stderr)
        return False
    
def validate_p45(fulltext, expected_values):
    """Validate P45 section contains expected fields and values"""
    validations = {}
    
    for key, value in expected_values.items():
        result = validate_field(key, value, fulltext)
        validations.update(result)
    
    return validations

def validate_field(label, expected, text):
    if expected in text:
        return {label: "PASS, is valid"}
    else:
        return {label: f"FAIL — Expected '{expected}'"}
    
def cross_validate(full_text, p45_text, expected_values):
    """Ensure P45 values match the rest of the PDF"""
    mismatches = {}
    
    for key, value in expected_values.items():
        in_full = value in full_text
        in_p45 = value in p45_text
        
        if in_full != in_p45:
            mismatches[key] = f"Mismatch - Full doc: {in_full}, P45: {in_p45}"
        if in_full and not in_p45:
            mismatches[key] = f"Mismatch — Full doc: {in_full}, P45: {in_p45}"
    
    return mismatches

def format_results(validations):
    """Format validation results as a neat list"""
    output = "\n📋 PDF VALIDATION RESULTS\n"
    output += "=" * 50 + "\n"
    
    passed = []
    failed = []
    
    for key, value in validations.items():
        if "PASS" in value:
            passed.append(f"✓ {key}: {value}")
        else:
            failed.append(f"✗ {key}: {value}")
    
    # Print passed validations
    if passed:
        output += "PASSED:\n"
        for item in passed:
            output += f"  {item}\n"
    
    # Print failed validations
    if failed:
        output += "\nFAILED:\n"
        for item in failed:
            output += f"  {item}\n"
    
    output += "=" * 50 + "\n"
    return output

def main():
    """Validate using an existing .json file only (no text extraction)."""
    if len(sys.argv) < 2:
        print("Usage: python SampleCode.py <pdf_path>  (requires <pdf>.json next to the pdf)", file=sys.stderr)
        sys.exit(2)

    pdf_path = sys.argv[1]
    json_filename = pdf_path.replace(".pdf", ".json")

    # Do NOT extract text here — require JSON to be present
    if not os.path.exists(json_filename):
        print(f"ERROR: JSON not found: {json_filename}\nCreate the JSON (once) and re-run.", file=sys.stderr)
        sys.exit(2)

    pdf_data = load_json(json_filename)
    if pdf_data is None:
        print(f"ERROR: Failed to load JSON: {json_filename}", file=sys.stderr)
        sys.exit(2)

    # Source-of-truth text from JSON
    full_text = pdf_data.get("full_document", "") or ""
    p45_text = pdf_data.get("p45_section", "") or ""
    pre5_text = pdf_data.get("pre5_section", "") or ""

    # Basic sanity check
    if not (full_text.strip() or p45_text.strip()):
        print(json.dumps({"PDF Validation": "FAIL - empty JSON content"}))
        return

    # --- Test definitions (adjust values as needed) ---
    expected_p45values = {
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
        "Postcode": "W2 4BA",
        "Month Number": "8"
    }

    Additional_Validations = [
        "26 November 2025",
        "Plan Value: £190,664.73",
        "Cash Withdrawal: £190,664.73",
        "Plan value after withdrawal: £0.00",
        "Customer ID: 7700049486",
        "Pension Plan: 1000059054L",
    ]

    expected_comparisons = {
        "NI Number": "WM764243B",
        "Title": "MR",
        "First Name": "TDMJMFC",
        "Surname": "UATJMFC",
        "Leaving Date": "27 11 2025",
        "Tax Code": "1250L",
        "Address": "AVENUE STREET",
        "Postcode": "W2 4BA",
        "Date": "29 11 2025"
    }

    # --- Run validations ---
    # Validate only P45 area (pages after 5)
    p45_validations = validate_p45(p45_text, expected_p45values)

    # Validate additional values expected on pages 1-5
    pre5_validations = {}
    for val in Additional_Validations:
        pre5_validations[val] = "PASS, is valid" if val in pre5_text else f"FAIL — Expected '{val}' on pages 1-5"

    # Compare expected keys between full PDF and P45
    comparison_validations = {}
    for key, val in expected_comparisons.items():
        in_full = val in full_text
        in_p45 = val in p45_text
        if in_full and in_p45:
            comparison_validations[key] = "PASS, present in both full PDF and P45"
        elif in_full and not in_p45:
            comparison_validations[key] = "Mismatch — Present in full PDF but missing from P45"
        elif (not in_full) and in_p45:
            comparison_validations[key] = "Notice — Present in P45 only (not in full PDF)"
        else:
            comparison_validations[key] = f"FAIL — Expected '{val}' not found anywhere"

    # Combine results into a single machine-readable dict
    validations = {
        "P45 Validations": p45_validations,
        "Pages 1-5 Additional Validations": pre5_validations,
        "P45 vs Full PDF Comparisons": comparison_validations
    }

    # Human-friendly prints to stderr
    print(format_results(p45_validations), file=sys.stderr)
    # Print comparisons and pre5 succinctly
    print("\n📋 P45 vs Full PDF COMPARISONS\n" + "="*50 + "\n", file=sys.stderr)
    for k, v in comparison_validations.items():
        prefix = "✓" if "PASS" in v else "✗"
        print(f"{prefix} {k}: {v}", file=sys.stderr)
    print("\n📋 Pages 1-5 ADDITIONAL VALIDATIONS\n" + "="*50 + "\n", file=sys.stderr)
    for k, v in pre5_validations.items():
        prefix = "✓" if "PASS" in v else "✗"
        print(f"{prefix} {k}: {v}", file=sys.stderr)

    # Machine-readable JSON on stdout (for your test runner)
    print(json.dumps(validations))

if __name__ == "__main__":
    main()

 
