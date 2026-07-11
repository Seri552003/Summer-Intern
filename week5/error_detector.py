# error_detector.py
# Error Detection System — Process Plan mein errors dhundho
# Week 5 | LLM-CAPP Project
# FIXED: (1) "VALID_TRANSITIONS" import tootne wala tha kyunki fsm_validator.py
#        me ab wo "_LEGACY_VALID_TRANSITIONS" hai. (2) ALL_KNOWN_OPS sirf 8
#        operations tak limited tha — ab routes.py ke 41-operation registry
#        se aata hai, isliye naye operations (Tapping, Pocket Milling, etc.)
#        false-positive "UNKNOWN_OPERATION" error nahi denge.

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week4")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week2")))

from fsm_validator import validate_sequence
from routes import ALL_OPERATIONS

# ── Error Types ───────────────────────────────────
ERROR_TYPES = {
    "MISSING_FACING":      "Sequence 'Facing' se start nahi hoti",
    "MISSING_INSPECTION":  "Sequence 'Inspection' pe khatam nahi hoti",
    "INVALID_TRANSITION":  "Invalid operation sequence",
    "UNKNOWN_OPERATION":   "Unknown/unsupported operation",
    "EMPTY_SEQUENCE":      "Empty sequence — koi steps nahi",
    "DUPLICATE_OPERATION": "Ek hi operation baar baar repeat ho raha hai",
}

ALL_KNOWN_OPS = set(ALL_OPERATIONS)  # 41 canonical operations — routes.py se, single source of truth


def detect_errors(steps: list) -> dict:
    """
    Process plan mein saare errors detect karo.
    Returns detailed error report.
    """
    errors = []
    warnings = []
    error_types = []

    # Check 1: Empty sequence
    if not steps:
        return {
            "has_errors": True,
            "error_types": ["EMPTY_SEQUENCE"],
            "errors": ["Sequence empty hai!"],
            "warnings": [],
            "fixable": False
        }

    # Check 2: Unknown operations
    for step in steps:
        if step not in ALL_KNOWN_OPS:
            errors.append(f"Unknown operation: '{step}'")
            error_types.append("UNKNOWN_OPERATION")

    # Check 3: Missing Facing
    if steps[0] != "Facing":
        errors.append(f"Sequence 'Facing' se start honi chahiye, '{steps[0]}' se nahi")
        error_types.append("MISSING_FACING")

    # Check 4: Missing Inspection
    if steps[-1] != "Inspection":
        errors.append(f"Sequence 'Inspection' pe khatam honi chahiye, '{steps[-1]}' pe nahi")
        error_types.append("MISSING_INSPECTION")

    # Check 5: Invalid transitions (ab precedence_graph.py ke 32 comprehensive rules se, fsm_validator.py ke through)
    fsm_result = validate_sequence(steps)
    if not fsm_result["valid"]:
        for e in fsm_result["errors"]:
            if e not in errors:
                errors.append(e)
                error_types.append("INVALID_TRANSITION")

    # Check 6: Duplicate operations
    seen = []
    for step in steps:
        if step in seen and step != "Inspection":
            warnings.append(f"'{step}' duplicate hai")
            error_types.append("DUPLICATE_OPERATION")
        seen.append(step)

    # Fixable hai agar sirf missing facing/inspection ya invalid transition hai
    fixable_types = {"MISSING_FACING", "MISSING_INSPECTION", "INVALID_TRANSITION", "DUPLICATE_OPERATION"}
    non_fixable = set(error_types) - fixable_types
    fixable = len(non_fixable) == 0 and len(errors) > 0

    return {
        "has_errors": len(errors) > 0,
        "error_types": list(set(error_types)),
        "errors": errors,
        "warnings": warnings,
        "fixable": fixable
    }


def print_error_report(steps: list, report: dict):
    """Error report print karo."""
    print(f"\n  Sequence : {' → '.join(steps)}")
    if not report["has_errors"]:
        print(f"  Status   : ✅ No errors detected")
    else:
        print(f"  Status   : ❌ {len(report['errors'])} error(s) found")
        print(f"  Fixable  : {'🔧 Yes' if report['fixable'] else '❌ No'}")
        for e in report["errors"]:
            print(f"    ⚠️  {e}")
        for w in report["warnings"]:
            print(f"    💡 Warning: {w}")


if __name__ == "__main__":
    print("=== Error Detection Tests ===")

    # Test 1: Valid sequence
    print("\n─── Test 1: Valid Sequence ───")
    seq1 = ["Facing", "Drilling", "Reaming", "Inspection"]
    r1 = detect_errors(seq1)
    print_error_report(seq1, r1)

    # Test 2: Missing Facing
    print("\n─── Test 2: Missing Facing ───")
    seq2 = ["Drilling", "Reaming", "Inspection"]
    r2 = detect_errors(seq2)
    print_error_report(seq2, r2)

    # Test 3: Invalid transition
    print("\n─── Test 3: Invalid Transition ───")
    seq3 = ["Facing", "Reaming", "Drilling", "Inspection"]
    r3 = detect_errors(seq3)
    print_error_report(seq3, r3)

    # Test 4: Unknown operation (genuinely fake operation)
    print("\n─── Test 4: Unknown Operation ───")
    seq4 = ["Facing", "LaserCut", "Inspection"]
    r4 = detect_errors(seq4)
    print_error_report(seq4, r4)

    # Test 5: NAYA — operation jo purane 8-op system me "unknown" flag hota (ab nahi hoga)
    print("\n─── Test 5: New Operation (Tapping) — false-positive check ───")
    seq5 = ["Facing", "Center Drilling", "Drilling", "Tapping", "Inspection"]
    r5 = detect_errors(seq5)
    print_error_report(seq5, r5)

    # Test 6: Route Builder ka asli output — bilkul clean aana chahiye
    print("\n─── Test 6: Actual route_builder.py output (Thread+Fillet) ───")
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week1")))
    from route_builder import generate_valid_routes
    seq6 = generate_valid_routes(["Thread", "Fillet"], max_routes=1)[0]
    r6 = detect_errors(seq6)
    print_error_report(seq6, r6)