
# extract_to_json.py
# Simple extractor:
# - Reads a PDF and writes a JSON containing:
#   - full_document (concatenated text of all pages)
#   - pages[x].full_text (text per page)
#   - pages[x].headers (expected values found on that page)
#   - headers_global (expected values found anywhere across the document)

import json
from pathlib import Path
import pdfplumber  # pip install pdfplumber


def expected_values() -> dict:
    # Central place to define expected values for discovery in the PDF text.
    return {
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
        "Date 3": "27/11/2025",
        # P45 section values:
        "NI Number": "WM764243B",
        "Leaving Date": "27 11 2025",
        "Tax Code": "1250L",
        "Total Pay to Date": "193,164.73",
        "Total Tax to Date": "85,305.15",
        "Date of Birth": "01 01 1995",
        "Month Number": "8",
        "Gender":"Male X"
    }


def contains(haystack: str, needle: str) -> bool:
    # Case-insensitive containment check with basic None safety.
    return (needle or "").lower() in (haystack or "").lower()


def extract_pdf_to_structured_json(pdf_path: str, output_json_path: str) -> Path:
    # Open the PDF and collect full text per page and discovered headers.
    pdf_path_p = Path(pdf_path).resolve()
    out_p = Path(output_json_path).resolve()

    if not pdf_path_p.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path_p}")

    exp = expected_values()
    pages_out = []
    full_document_parts = []

    with pdfplumber.open(str(pdf_path_p)) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            full_document_parts.append(text)

            # Discover which expected values appear on this page
            found_on_page = {}
            for label, value in exp.items():
                if contains(text, value):
                    found_on_page[label] = value

            pages_out.append({
                "page_number": idx,
                "full_text": text,
                "headers": found_on_page
            })

    # Build full document concatenation
    full_document = "\n".join(full_document_parts)

    # Discover which expected values appear anywhere in the doc
    headers_global = {}
    for label, value in exp.items():
        if contains(full_document, value):
            headers_global[label] = value

    data = {
        "pdf_path": str(pdf_path_p),
        "full_document": full_document,
        "headers_global": headers_global,
        "pages": pages_out
    }
    with out_p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

