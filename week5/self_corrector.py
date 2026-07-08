# self_corrector.py
# Self-Correction Loop — Invalid plans automatically fix karo
# Week 5 | LLM-CAPP Project

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week4")))

from fsm_validator import validate_sequence, fix_sequence, VALID_TRANSITIONS
from error_detector import detect_errors

MAX_CORRECTION_ATTEMPTS = 3


def self_correct(steps: list, verbose: bool = True) -> dict:
    """
    Invalid process plan ko automatically correct karo.
    Max 3 attempts karta hai.
    
    Returns:
    {
      "success": True/False,
      "original": [...],
      "corrected": [...],
      "attempts": 1,
      "changes_made": [...]
    }
    """
    original = list(steps)
    current = list(steps)
    changes_made = []
    
    if verbose:
        print(f"\n  Original  : {' → '.join(original)}")
    
    for attempt in range(1, MAX_CORRECTION_ATTEMPTS + 1):
        # Step 1: Errors detect karo
        error_report = detect_errors(current)
        
        if not error_report["has_errors"]:
            if verbose:
                print(f"  ✅ Valid after {attempt-1} correction(s)")
            return {
                "success": True,
                "original": original,
                "corrected": current,
                "attempts": attempt - 1,
                "changes_made": changes_made
            }
        
        if verbose:
            print(f"\n  Attempt {attempt}: {len(error_report['errors'])} error(s) found")
        
        # Step 2: Fix karo agar fixable hai
        if not error_report["fixable"]:
            if verbose:
                print(f"  ❌ Not fixable — unknown operations present")
            return {
                "success": False,
                "original": original,
                "corrected": current,
                "attempts": attempt,
                "changes_made": changes_made
            }
        
        # Step 3: Apply corrections
        prev = list(current)
        
        # Fix 1: Remove unknown operations
        known_ops = set(VALID_TRANSITIONS.keys()) - {"START"}
        current = [s for s in current if s in known_ops]
        if len(current) != len(prev):
            changes_made.append("Removed unknown operations")
        
        # Fix 2: Remove duplicates (keep first occurrence)
        seen = []
        deduped = []
        for s in current:
            if s not in seen:
                deduped.append(s)
                seen.append(s)
        if deduped != current:
            changes_made.append("Removed duplicate operations")
            current = deduped
        
        # Fix 3: FSM-based fix (Facing + Inspection add karo)
        current = fix_sequence(current)
        if current != prev:
            changes_made.append(f"FSM fix applied (attempt {attempt})")
        
        if verbose:
            print(f"  🔧 Fixed  : {' → '.join(current)}")
    
    # Final check
    final_check = detect_errors(current)
    if not final_check["has_errors"]:
        return {
            "success": True,
            "original": original,
            "corrected": current,
            "attempts": MAX_CORRECTION_ATTEMPTS,
            "changes_made": changes_made
        }
    
    return {
        "success": False,
        "original": original,
        "corrected": current,
        "attempts": MAX_CORRECTION_ATTEMPTS,
        "changes_made": changes_made
    }


def print_correction_result(result: dict):
    """Correction result print karo."""
    print(f"\n{'─'*55}")
    status = "✅ CORRECTED" if result["success"] else "❌ COULD NOT FIX"
    print(f"  Status    : {status}")
    print(f"  Original  : {' → '.join(result['original'])}")
    print(f"  Corrected : {' → '.join(result['corrected'])}")
    print(f"  Attempts  : {result['attempts']}")
    if result["changes_made"]:
        print(f"  Changes   :")
        for c in result["changes_made"]:
            print(f"    • {c}")


if __name__ == "__main__":
    print("=== Self-Correction Loop Tests ===")

    # Test 1: Missing Facing
    print("\n─── Test 1: Missing Facing ───")
    result1 = self_correct(["Drilling", "Reaming", "Inspection"])
    print_correction_result(result1)

    # Test 2: Missing Inspection
    print("\n─── Test 2: Missing Inspection ───")
    result2 = self_correct(["Facing", "Drilling", "Reaming"])
    print_correction_result(result2)

    # Test 3: Both missing
    print("\n─── Test 3: Both Missing ───")
    result3 = self_correct(["Drilling", "Reaming"])
    print_correction_result(result3)

    # Test 4: Duplicate operations
    print("\n─── Test 4: Duplicate Operations ───")
    result4 = self_correct(["Facing", "Drilling", "Drilling", "Inspection"])
    print_correction_result(result4)

    # Test 5: Unfixable (unknown operation)
    print("\n─── Test 5: Unfixable ───")
    result5 = self_correct(["Facing", "LaserCut", "Inspection"])
    print_correction_result(result5)