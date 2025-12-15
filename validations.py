
# validations.py
from typing import Dict, List


def _norm_label(label: str, aliases: Dict[str, str]) -> str:
    return aliases.get(label, label)


def full_doc_checks(expected_values: Dict[str, str], full_text: str) -> List[dict]:
    checks: List[dict] = []
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
    checks: List[dict] = []
    aliases = aliases or {}

    # Basic type guards to prevent NoneType failures
    if not isinstance(expected_values, dict):
        checks.append({"name": "expected_values__type", "pass": False, "message": "expected_values is not a dict"})
        return checks
    if not isinstance(box_mapping, dict):
        checks.append({"name": "box_mapping__type", "pass": False, "message": "box_mapping is not a dict"})
        return checks
    if not isinstance(boxes, dict):
        checks.append({"name": "boxes__type", "pass": False, "message": "boxes is not a dict"})
        return checks

    for box_name, labels in box_mapping.items():
        box_text = (boxes.get(box_name, {}) or {}).get("raw_text", "") or ""

        # Confirm presence of the box in extraction
        if box_name not in boxes:
            checks.append({
                "name": f"{box_name}__box_present",
                "pass": False,
                "message": f"Box '{box_name}' missing from extraction JSON"
            })
        else:
            checks.append({"name": f"{box_name}__box_present", "pass": True})

        # Normalize labels to an iterable list
        if labels is None:
            labels = []
        elif not isinstance(labels, list):
            labels = list(labels)

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
            if exp_val and (exp_val in box_text):
                checks.append({"name": name, "pass": True})
            else:
                checks.append({
                    "name": name,
                    "pass": False,
                    "message": f"Expected '{exp_val}' not found in {box_name}"
                               })
    return checks

