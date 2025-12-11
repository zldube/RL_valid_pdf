from pypdf import PdfReader
from pypdf.errors import PdfReadError
import sys

def validate_pdf(fulltext, pdf_path):
    # Validate file is readable PDF and has text content.
    try:
        PdfReader(pdf_path)
    except PdfReadError:
        print("Invalid PDF file", file=sys.stderr)
        return False

    if not fulltext.strip():
        print("No data found in PDF extraction", file=sys.stderr)
        return False
    
    return True

def validate_field(label, expected, text):
    if expected in text:
        return {label: "PASS, is valid"}
    else:
        return {label: f"FAIL — Expected '{expected}'"}

def validate_p45(fulltext, expected_values):
    #Check if all expected P45 fields exist.
    validations = {}
    for key, value in expected_values.items():
        validations.update(validate_field(key, value, fulltext))
    return validations

def cross_validate(full_text, p45_text, expected_values):
    #Check that P45 values appear consistently in both sections.

    mismatches = {}
    for key, value in expected_values.items():
        in_full = value in full_text
        in_p45 = value in p45_text
        if in_full != in_p45:
            mismatches[key] = f"Mismatch — Full doc: {in_full}, P45: {in_p45}"
    return mismatches
