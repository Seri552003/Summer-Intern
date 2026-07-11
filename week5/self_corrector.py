# self_corrector.py
# Self-Correction Loop — Invalid plans automatically fix karo
# Week 5 | LLM-CAPP Project
# FIXED + UPGRADED:
#   1. Broken import fix (VALID_TRANSITIONS -> hata diya)
#   2. DESTRUCTIVE bug fix: "unknown op removal" 8-op list use karta tha,
#      isse naye operations (Tapping, Pocket Milling...) galti se DELETE
#      ho jaate the correction ke dauraan. Ab 41-op registry use karta hai.
#   3. NAYA PRIMARY METHOD: agar original `features` diye gaye hain, seedha
#      Route Builder se guaranteed-valid replacement route milta hai —
#      1 hi attempt me, order-violations bhi automatically theek.
#      Purana ad-hoc patching (Facing/Inspection/duplicates) ab sirf
#      FALLBACK hai jab features available na ho.

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week4")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week2")))

from fsm_validator import fix_sequence, fix_sequence_with_builder
from error_detector import detect_errors
from routes import ALL_OPERATIONS

MAX_CORRECTION_ATTEMPTS = 3
ALL_KNOWN_OPS = set(ALL_OPERATIONS)  # 41 canonical operations


def self_correct(steps: list, features: list = None, verbose: bool = True) -> dict:
    """
    Invalid process plan ko correct karo.

    features diya gaya (RECOMMENDED): Route Builder se seedha guaranteed-valid
    replacement route milta hai — 1 attempt, order-violations bhi fix ho jaate hain.

    features NAHI diya (FALLBACK): purana ad-hoc patching (Facing/Inspection add
    karna, duplicates hatana) — sirf structural issues fix karta hai, order-
    violations FIX NAHI kar sakta (usse detect zaroor karega).

    Returns:
    {
      "success": True/False,
      "original": [...],
      "corrected": [...],
      "attempts": 1,
      "changes_made": [...],
      "method": "route_builder" | "fallback_patch" | "none"
    }
    """
    original = list(steps)

    if verbose:
        print(f"\n  Original  : {' → '.join(original)}")

    error_report = detect_errors(original)
    if not error_report["has_errors"]:
        if verbose:
            print(f"  ✅ Already valid, koi correction nahi chahiye")
        return {
            "success": True, "original": original, "corrected": original,
            "attempts": 0, "changes_made": [], "method": "none"
        }

    # ═══════════════════════════════════════════════
    # PRIMARY METHOD: Route Builder se guaranteed-valid fix
    # ═══════════════════════════════════════════════
    if features:
        corrected = fix_sequence_with_builder(features)
        final_check = detect_errors(corrected)
        if verbose:
            print(f"  🔧 Route Builder fix: {' → '.join(corrected)}")
            print(f"  {'✅ VALID' if not final_check['has_errors'] else '❌ STILL INVALID (edge case)'}")
        return {
            "success": not final_check["has_errors"],
            "original": original,
            "corrected": corrected,
            "attempts": 1,
            "changes_made": ["Route Builder se naya guaranteed-valid route liya gaya"],
            "method": "route_builder"
        }

    # ═══════════════════════════════════════════════
    # FALLBACK METHOD: features nahi diye — ad-hoc patching (bug-fixed)
    # ═══════════════════════════════════════════════
    current = list(steps)
    changes_made = []

    for attempt in range(1, MAX_CORRECTION_ATTEMPTS + 1):
        error_report = detect_errors(current)

        if not error_report["has_errors"]:
            if verbose:
                print(f"  ✅ Valid after {attempt-1} correction(s) [fallback method]")
            return {
                "success": True, "original": original, "corrected": current,
                "attempts": attempt - 1, "changes_made": changes_made, "method": "fallback_patch"
            }

        if verbose:
            print(f"\n  Attempt {attempt}: {len(error_report['errors'])} error(s) found")

        if not error_report["fixable"]:
            if verbose:
                print(f"  ❌ Not fixable — unknown operations present, ya features nahi diye order-fix ke liye")
            return {
                "success": False, "original": original, "corrected": current,
                "attempts": attempt, "changes_made": changes_made, "method": "fallback_patch"
            }

        prev = list(current)

        # Fix 1: Remove unknown operations (ab 41-op registry se — genuinely unknown hi hatega)
        current = [s for s in current if s in ALL_KNOWN_OPS]
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

        # Fix 3: Structural fix (Facing + Inspection)
        current = fix_sequence(current)
        if current != prev:
            changes_made.append(f"Structural fix applied (attempt {attempt})")

        if verbose:
            print(f"  🔧 Fixed  : {' → '.join(current)}")

    final_check = detect_errors(current)
    return {
        "success": not final_check["has_errors"],
        "original": original, "corrected": current,
        "attempts": MAX_CORRECTION_ATTEMPTS, "changes_made": changes_made,
        "method": "fallback_patch"
    }


def print_correction_result(result: dict):
    """Correction result print karo."""
    print(f"\n{'─'*55}")
    status = "✅ CORRECTED" if result["success"] else "❌ COULD NOT FIX"
    print(f"  Status    : {status}  (method: {result['method']})")
    print(f"  Original  : {' → '.join(result['original'])}")
    print(f"  Corrected : {' → '.join(result['corrected'])}")
    print(f"  Attempts  : {result['attempts']}")
    if result["changes_made"]:
        print(f"  Changes   :")
        for c in result["changes_made"]:
            print(f"    • {c}")


if __name__ == "__main__":
    print("=== Self-Correction Loop Tests ===")

    print("\n─── Test 1: Missing Facing (fallback) ───")
    result1 = self_correct(["Drilling", "Reaming", "Inspection"])
    print_correction_result(result1)

    print("\n─── Test 2: Missing Inspection (fallback) ───")
    result2 = self_correct(["Facing", "Drilling", "Reaming"])
    print_correction_result(result2)

    print("\n─── Test 3: Duplicate Operations (fallback) ───")
    result3 = self_correct(["Facing", "Drilling", "Drilling", "Inspection"])
    print_correction_result(result3)

    print("\n─── Test 4: Genuinely Unfixable (unknown op) ───")
    result4 = self_correct(["Facing", "LaserCut", "Inspection"])
    print_correction_result(result4)

    print("\n─── Test 5: Order-violation WITHOUT features (fallback GAP) ───")
    result5 = self_correct(["Facing", "Reaming", "Drilling", "Inspection"])
    print_correction_result(result5)
    print("  ^ Fallback order-violations fix NAHI kar sakta — ye EXPECTED hai")

    print("\n─── Test 6: SAME order-violation WITH features (Route Builder fix) ───")
    result6 = self_correct(["Facing", "Reaming", "Drilling", "Inspection"], features=["Hole"])
    print_correction_result(result6)
    print("  ^ Ab fix ho gaya, kyunki features diye — Route Builder ne naya route banaya")

    print("\n─── Test 7: New operation (Tapping) — no longer wrongly deleted ───")
    result7 = self_correct(["Tapping", "Facing", "Drilling", "Inspection"])
    print_correction_result(result7)
    print("  ^ 'Tapping' delete NAHI hona chahiye (purane bug me ho jaata)")