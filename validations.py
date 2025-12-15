
# validations.py
# Validation helpers: full-document existence and per-box position checks.

from typing import Dict, List


def _norm_label(label: str, aliases: Dict[str, str]) -> str:
    # Normalize labels via alias mapping (e.g., "Last Name" -> "Surname").
    if label in aliases:
        return aliases[label]
    return label


def full_doc_checks(expected_values: Dict[str, str], full_text: str) -> List[dict]:
    # Ensure each expected value appears somewhere in the full extracted text.
    checks = []
    corpus = full_text or ""
    for label, value in expected_values.items():
        name = f"{label}__exists"
        if value and (value in corpus):
            checks.append({"name": name, "pass": True})
        else:
            checks.append({
                "name": name,
                "pass": False,
                "message": f"Expected '{value}' not found in full first-half text"
            })
    return checks


def box_checks(
    expected_values: Dict[str, str],
    boxes: Dict[str, Dict],
    box_mapping: Dict[str, List[str]],
    aliases: Dict[str, str] | None = None
) -> List[dict]:
    # Validate that the right values are inside the right boxes.
    # box_mapping keys are actual box names in the extraction JSON (e.g., "box_0_1").
    # aliases map friendly labels to canonical expected_values keys.
    checks = []
    aliases = aliases or {}

    for box_name, labels in box_mapping.items():
        box_text = (boxes.get(box_name, {}) or {}).get("raw_text", "")
        if box_text is None:
            box_text = ""
        if box_name not in boxes:
            checks.append({
                "name": f"{box_name}__box_present",
                "pass": False,
                "message": f"Box '{box_name}' missing from extraction JSON"
            })
            # Still continue to report missing label checks for visibility
        else:
            checks.append({"name": f"{box_name}__box_present", "pass": True})

        for label in labels:
            canon = _norm_label(label, aliases)
            if canon not in expected_values:
                checks.append({
                    "name": f"{label}__expected_missing",
                    "pass": False,
                    "message": f"No expected value provided for '{label}' (canonical: '{canon}')"
                })
                continue

            exp_val = expected_values[canon]
            name = f"{canon}__in_{box_name}"
            if exp_val and exp_val in box_text:
                checks.append({"name": name, "pass": True})
            else:
                checks.append({
                    "name": name,
                    "pass": False,
                    "message": f"Expected '{exp_val}' not found in {box_name}"
                               })

