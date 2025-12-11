def format_results(validations):
    #Format all validation results in a neat summary.
    
    output = "\n📋 PDF VALIDATION RESULTS\n" + "=" * 50 + "\n"
    passed = [f"✓ {k}: {v}" for k, v in validations.items() if "PASS" in v]
    failed = [f"✗ {k}: {v}" for k, v in validations.items() if "FAIL" in v or "Mismatch" in v]

    if passed:
        output += "PASSED:\n" + "\n".join(f"  {p}" for p in passed) + "\n"

    if failed:
        output += "\nFAILED:\n" + "\n".join(f"  {f}" for f in failed) + "\n"

    output += "=" * 50 + "\n"
    return output
