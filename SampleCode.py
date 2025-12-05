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
from pypdf import PdfReader
from pypdf.errors import PdfReadError

def extract_text(pdf_path, start_page=1):
    """
    Extract text from a PDF starting at a 1-based page number.
    Default start_page=1 (extract whole document). To check text after page 5,
    pass start_page=6.
    """
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            if index < start_page:
                continue
            txt = page.extract_text()
            if txt:
                full_text += txt + "\n"
    return full_text

def validate_pdf(fulltext, pdf):
    #Validated file type as pdf
    try:
        PdfReader(pdf)
    except PdfReadError:
        print("Invalid PDF file")
    else:
        pass

    #Validating pdf has data 
    if pdf:
        file1 = open("pdf_info.txt", "w+")
        file1.writelines(fulltext)

        print(file1.read()) #(internal purposes)
        file1.close()

        print("PDF has data \n")
    
    else:
        print("No data found")

def validate_p45(fulltext, p45_indicators):

    # Validate presence of P45 indicators
    for indicator in p45_indicators:
        if indicator not in fulltext:
            print(f"P45 validation failed: Missing '{indicator}'")
            return False
    print("P45 validation passed")
    return True

def validate_field(label, expected, text):
    if expected in text:
        return {label: "PASS"}
    else:
        return {label: f"FAIL — Expected '{expected}'"}
    
def validate_pdftext(pdf_path):
    pass

def main():
    pdf_path = sys.argv[1]

    text = extract_text(pdf_path)

    validate_pdf(text, pdf_path)

    # Check for P45 specific text
    p45_indicators = [
        "PAYE Reference",
        "NI Number",
        "Title",
        "Surname",
        "First Name",
        "Leaving Date",
        "Tax Code",
        "Total Pay to Date",
        "Total Tax to Date",
        "Date of Birth",
        "Address",
        "Postcode",
    ]

    p45_text = extract_text(pdf_path, start_page=5)
    validate_p45(text, p45_indicators)

    validations = {}

    # Fields to validate
    expected_values = {
        "PAYE Reference": "120 / ME60530",
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

    for key, value in expected_values.items():
        result = validate_field(key, value, text)
        validations.update(result)

    # Output JSON so WDIO can parse the result
    print(json.dumps(validations))

if __name__ == "__main__":
    main()

 
