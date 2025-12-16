
# formatting.py
# Pretty-format validation results for console output.

from typing import Dict, List


def format_summary(checks: List[dict]) -> str:
    # Build a readable PASS/FAIL summary from a list of check dicts.
    header = "\nPDF VALIDATION RESULTS\n" + "-" * 60 + "\n"
    passed_lines = []
    failed_lines = []

    for c in checks:
        name = c.get("name", "unknown_check")
        ok = bool(c.get("pass"))
        if ok:
            passed_lines.append(f"  {name}: PASS")
        else:
            msg = c.get("message") or "FAIL"
            failed_lines.append(f"  {name}: {msg}")

    out = [header]
    if passed_lines:
        out.append("PASSED:")
        out.extend(passed_lines)
    if failed_lines:
        out.append("\nFAILED:")
        out.extend(failed_lines)

    out.append("\n" + "-" * 60 + "\n")
    return "\n".join(out)


def summarize_full_doc(checks: List[dict]) -> str:
    # Return a single-line verdict for full-doc existence checks.
    if all(c.get("pass") for c in checks if c.get("name", "").endswith("__exists")):
        return "PASSED FULL DOC CHECK"
    
    failed = [c for c in checks if c.get("name", "").endswith("__exists") and not c.get("pass")]

    if not failed:
        return "FULL DOC CHECK: NO EXISTENCE CHECKS FOUND"
    details = "; ".join(f"{c['name'].replace('__exists','')}: {c.get('message','FAIL')}" for c in failed)
    return f"FAILED"
