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


def extract_pdf_to_json(pdf_path):
    """Extract all PDF data into a structured JSON object (plus layout)."""
    pdf_data = {
        "filename": os.path.basename(pdf_path),
        "extraction_date": datetime.now().isoformat(),
        "full_document": extract_text(pdf_path),
        "p45_section": extract_text(pdf_path, start_page=6),
        "tables": [],
        "layout": extract_pdf_layout(pdf_path)  # ▶ NEW
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
    if len(sys.argv) < 2:
        print("Usage: python SampleCode.py <pdf_path>", file=sys.stderr)
        sys.exit(2)

    pdf_path = sys.argv[1]
    json_filename = pdf_path.replace(".pdf", ".json")

    # Use existing JSON if present, otherwise extract and save JSON
    pdf_data = load_json(json_filename)
    if pdf_data is None:
        pdf_data = extract_pdf_to_json(pdf_path)
        save_json(pdf_data, json_filename)

    # Use JSON content as source of truth (do NOT re-extract text)
    full_text = pdf_data.get("full_document", "")
    p45_text = pdf_data.get("p45_section", "")

    # Validate PDF file integrity and that extraction produced data
    if not validate_pdf(full_text, pdf_path):
        print(json.dumps({"PDF Validation": "FAIL"}))
        return 

    # Fields to validate
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

    # Validate P45 section using JSON content
    p45_validations = validate_p45(p45_text, expected_values)

    # Cross-validate only where it makes sense (value appears in full doc)
    mismatches = cross_validate(full_text, p45_text, expected_values)

    # Combine results
    validations = p45_validations.copy()
    validations.update(mismatches)

    # Print human-friendly results to stderr and machine JSON to stdout
    print(format_results(validations), file=sys.stderr)
    print(json.dumps(validations))

if __name__ == "__main__":
    main()

 
