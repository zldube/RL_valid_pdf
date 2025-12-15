
#!/usr/bin/env python3
import json
import argparse
from pathlib import Path

def load_json(p: str):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def check_exists(value: str, text: str, label: str):
    ok = bool(value) and (value in (text or ""))
    return {"name": f"{label}_exists", "pass": ok, "message": None if ok else f"Expected '{value}' not found"}

def check_in_box(value: str, box_text: str, label: str, box_name: str):
    present = bool(value) and (value in (box_text or ""))
    return {
        "name": f"{label}_in_{box_name}",
        "pass": present,
        "message": None if present else f"Value '{value}' not found in box {box_name}"
    }

def run(extraction_json: str, expected_json: str = None):
    ex = load_json(extraction_json)
    expected = load_json(expected_json) if expected_json else {}

    # Compose aggregated text over first-half pages
    full_text = ex.get("full_text", "")
    boxes = ex.get("boxes", {})

    checks = []

    # Example targets (you can supply via expected.json)
    cid = expected.get("customer_id")
    date_top = expected.get("date_top")
    postcode = expected.get("postal_postcode")
    dob = expected.get("dob")  # for demo failure

    # Existence
    if cid:
        checks.append(check_exists(cid, full_text, "customer_id"))
    if date_top:
        checks.append(check_exists(date_top, full_text, "date_top"))
    if postcode:
        checks.append(check_exists(postcode, full_text, "postal_postcode"))

    # Position (box membership)
    # Map which box should contain which value (you can drive this via expected.json too)
    wanted = expected.get("boxes", {
        "customer_id": ["box_0_3"],       # example
        "date_top": ["box_0_1"],          # example
        "postal_postcode": ["box_0_0"]    # example
    })

    for label, box_list in wanted.items():
        val = expected.get(label)
        if not val:
            continue
        for bname in box_list:
            btext = boxes.get(bname, {}).get("raw_text", "")
            checks.append(check_in_box(val, btext, label, bname))

    # Demo failure: Box 4 does not contain DoB
    if dob:
        b4_text = boxes.get("box_0_4", {}).get("raw_text", "")
        checks.append(check_in_box(dob, b4_text, "dob", "box_0_4"))  # intentionally likely FAIL

    return {
        "doc_path": ex.get("doc_path"),
        "checks": checks
    }

def main():
    ap = argparse.ArgumentParser(description="Validate first-half extraction: existence + position in boxes.")
    ap.add_argument("--extraction", required=True)
    ap.add_argument("--expected")  # path to expected.json
    args = ap.parse_args()
    res = run(args.extraction, args.expected)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
